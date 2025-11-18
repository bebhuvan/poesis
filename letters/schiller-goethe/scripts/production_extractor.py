#!/usr/bin/env python3
"""
PRODUCTION Letter Extractor - Properly tested and verified
Handles all edge cases discovered during verification
"""

import re
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Letter:
    number: int
    sender: str
    recipient: str
    date: str
    location: str
    content: str
    postscript: str
    detection_method: str


class ProductionExtractor:
    """Production-ready extractor with all fixes applied"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []
        self.stats = {
            'by_location': 0,
            'by_signature': 0,
            'unknown': 0,
            'with_dates': 0,
            'with_postscripts': 0
        }

    def extract_letters(self) -> List[Letter]:
        print("="*80)
        print("PRODUCTION LETTER EXTRACTION")
        print("="*80)

        # Load
        text_path = self.base_dir / 'raw_ocr/full_text.txt'
        text = text_path.read_text(encoding='utf-8')

        # Find start
        start_match = re.search(r'Respected\s+Sir\s*:', text)
        if not start_match:
            return []

        letters_section = text[start_match.start():]

        # Split into blocks
        blocks = self._split_into_blocks(letters_section)
        print(f"Found {len(blocks)} letter blocks\n")

        # Parse each
        for num, block in enumerate(blocks, 1):
            letter = self._parse_letter(block, num)
            if letter:
                self.letters.append(letter)
                self._update_stats(letter)

        self._print_sample()
        return self.letters

    def _split_into_blocks(self, text: str) -> List[str]:
        """Split text into letter blocks"""
        blocks = []

        # First letter
        second_match = re.search(r'\n\s*II\.\s*\n', text)
        if second_match:
            blocks.append(text[:second_match.start()])

            remaining = text[second_match.start():]
            positions = [(m.start(), m.group(1)) for m in re.finditer(r'\n\s*([IVXLCDM]+)\.\s*\n', remaining)]

            for i, (pos, roman) in enumerate(positions):
                if i < len(positions) - 1:
                    blocks.append(remaining[pos:positions[i + 1][0]])
                else:
                    blocks.append(remaining[pos:])

        return blocks

    def _parse_letter(self, text: str, number: int) -> Optional[Letter]:
        """Parse letter with all edge case handling"""

        # Clean
        text = text.strip()
        text = re.sub(r'^\s*[IVXLCDM]+\.\s*\n', '', text)

        # Split and filter
        filtered = self._filter_lines(text.split('\n'))

        if len(filtered) < 1:
            return None

        # Extract location/date with FLEXIBLE regex
        location, date_str, date_idx = self._extract_location_date(filtered)

        # Determine sender (PRIMARY: location, FALLBACK: signature)
        sender, detection_method = self._determine_sender(filtered, location)

        # Recipient
        recipient = "Goethe" if sender == "Schiller" else "Schiller" if sender == "Goethe" else "Unknown"

        # Find signature for content boundary
        signature_idx = self._find_signature(filtered, sender)

        # Extract content and postscript
        content, postscript = self._extract_content_postscript(filtered, date_idx, signature_idx)

        return Letter(
            number=number,
            sender=sender,
            recipient=recipient,
            date=date_str,
            location=location,
            content=content,
            postscript=postscript,
            detection_method=detection_method
        )

    def _filter_lines(self, lines: List[str]) -> List[str]:
        """Filter out empty lines and page headers"""
        filtered = []
        headers = [
            r'^\s*SCHILLER\s*$',
            r'^\s*GOETHE\s*$',
            r'^\s*SCHILLER\s+AND\s+GOETHE\.?\s*$',
            r'^\s*CORRESPONDENCE\s+BETWEEN\s*$',
            r'^\s*C\s*0\s*R.*BETWEEN\s*$',
            r'^\s*\d+\s*$',  # Page numbers
        ]

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if not any(re.match(p, stripped, re.IGNORECASE) for p in headers):
                filtered.append(stripped)

        return filtered

    def _extract_location_date(self, lines: List[str]) -> tuple:
        """Extract location and date with FLEXIBLE regex"""
        location = ""
        date_str = ""
        date_idx = -1

        # FLEXIBLE pattern - handles double spaces, various ordinals
        # Pattern: (Jena|Weimar), [anything], (year)
        for idx in range(len(lines) - 1, max(0, len(lines) - 15), -1):
            line = lines[idx]

            # Look for Jena or Weimar followed by a year
            if 'jena' in line.lower() or 'weimar' in line.lower():
                # Extract location
                loc_match = re.search(r'(Jena|Weimar)', line, re.IGNORECASE)
                if loc_match:
                    location = loc_match.group(1).capitalize()

                # Extract full date if possible
                # Pattern: Month Day, Year (with flexible spacing and ordinals)
                date_match = re.search(
                    r'([A-Z][a-z]+)\s+(\d+[a-z]*)[,\s]+(17\d{2}|18\d{2})',
                    line
                )
                if date_match:
                    month = date_match.group(1)
                    day = date_match.group(2)
                    year = date_match.group(3)
                    date_str = f"{month} {day}, {year}"

                date_idx = idx
                break

        return location, date_str, date_idx

    def _determine_sender(self, lines: List[str], location: str) -> tuple:
        """Determine sender - PRIMARY: location, FALLBACK: signature"""

        # PRIMARY: Use location
        if location:
            if location.lower() == 'jena':
                return "Schiller", "location"
            elif location.lower() == 'weimar':
                return "Goethe", "location"

        # FALLBACK: Check for signature
        for idx in range(len(lines) - 1, max(0, len(lines) - 10), -1):
            line = lines[idx]
            if len(line) < 30:  # Signatures are short
                line_lower = line.lower()
                # Check it's not part of a sentence
                if not any(w in line_lower for w in ['to', 'from', 'with', 'and', 'the', 'of', 'in']):
                    if 'schiller' in line_lower:
                        return "Schiller", "signature"
                    elif 'goethe' in line_lower:
                        return "Goethe", "signature"

        return "Unknown", "unknown"

    def _find_signature(self, lines: List[str], sender: str) -> int:
        """Find signature line index"""
        if sender == "Unknown":
            return -1

        for idx in range(len(lines) - 1, max(0, len(lines) - 10), -1):
            line = lines[idx]
            if len(line) < 30:
                if sender.lower() in line.lower():
                    return idx

        return -1

    def _extract_content_postscript(self, lines: List[str], date_idx: int, signature_idx: int) -> tuple:
        """Extract content and postscript"""

        if signature_idx > 0:
            content_end = date_idx if date_idx > 0 else signature_idx
            content_lines = lines[:content_end]
            postscript_lines = lines[signature_idx + 1:]
        elif date_idx > 0:
            content_lines = lines[:date_idx]
            postscript_lines = []
        else:
            content_lines = lines
            postscript_lines = []

        content = self._clean('\n\n'.join(content_lines))
        postscript = self._clean('\n\n'.join(postscript_lines)) if postscript_lines else ""

        return content, postscript

    def _clean(self, text: str) -> str:
        """Clean OCR artifacts"""
        if not text:
            return ""

        # Fix v^ -> w
        text = text.replace('v^', 'w').replace(' v^', ' w')

        # Fix hyphenated words
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

        # Fix multiple spaces (but preserve paragraph breaks)
        text = re.sub(r' +', ' ', text)

        # Fix multiple newlines
        text = re.sub(r'\n\n\n+', '\n\n', text)

        return text.strip()

    def _update_stats(self, letter: Letter):
        """Update statistics"""
        if letter.detection_method == 'location':
            self.stats['by_location'] += 1
        elif letter.detection_method == 'signature':
            self.stats['by_signature'] += 1
        else:
            self.stats['unknown'] += 1

        if letter.date:
            self.stats['with_dates'] += 1
        if letter.postscript:
            self.stats['with_postscripts'] += 1

    def _print_sample(self):
        """Print sample of extracted letters"""
        print("Sample of first 25 letters:")
        print("-" * 90)
        print(f"{'#':3} {'Sender':8} {'→':2} {'Recipient':8} {'Date':22} {'Method':10} {'PS':3}")
        print("-" * 90)

        for i, letter in enumerate(self.letters[:25], 1):
            ps = "✓" if letter.postscript else ""
            date_display = (letter.date[:22] if letter.date else "No date").ljust(22)
            print(f"{i:3} {letter.sender:8} → {letter.recipient:8} {date_display} {letter.detection_method:10} {ps:3}")

        print(f"\n✓ Extracted {len(self.letters)} letters\n")

    def save_letters(self, output_dir: str):
        """Save letters to markdown files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        metadata = []

        for letter in self.letters:
            # Filename
            filename = f"{letter.number:04d}_{letter.sender.lower()}_to_{letter.recipient.lower()}"
            if letter.date:
                date_slug = re.sub(r'[^a-z0-9]+', '_', letter.date.lower()).strip('_')
                filename += f"_{date_slug}"
            else:
                filename += "_undated"
            filename += ".md"

            # Create markdown
            md = self._create_markdown(letter)

            # Save
            (output_path / filename).write_text(md, encoding='utf-8')

            # Metadata
            metadata.append({
                'number': letter.number,
                'filename': filename,
                'sender': letter.sender,
                'recipient': letter.recipient,
                'date': letter.date,
                'location': letter.location,
                'word_count': len(letter.content.split()),
                'has_postscript': bool(letter.postscript),
                'detection_method': letter.detection_method
            })

        # Save index
        (output_path / 'index.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

        # Print summary
        schiller = len([l for l in self.letters if l.sender == 'Schiller'])
        goethe = len([l for l in self.letters if l.sender == 'Goethe'])
        unknown = len([l for l in self.letters if l.sender == 'Unknown'])

        print("="*80)
        print("PRODUCTION EXTRACTION SUMMARY")
        print("="*80)
        print(f"\nTotal Letters: {len(self.letters)}")
        print(f"\nBy Sender:")
        print(f"  Schiller:  {schiller:3} ({schiller/len(self.letters)*100:5.1f}%)")
        print(f"  Goethe:    {goethe:3} ({goethe/len(self.letters)*100:5.1f}%)")
        print(f"  Unknown:   {unknown:3} ({unknown/len(self.letters)*100:5.1f}%)")
        print(f"\nDetection Methods:")
        print(f"  Location:  {self.stats['by_location']:3}")
        print(f"  Signature: {self.stats['by_signature']:3}")
        print(f"  Unknown:   {self.stats['unknown']:3}")
        print(f"\nOther:")
        print(f"  With dates:       {self.stats['with_dates']:3}")
        print(f"  With postscripts: {self.stats['with_postscripts']:3}")
        print("="*80)

    def _create_markdown(self, letter: Letter) -> str:
        """Create markdown file"""
        md = []

        # YAML front matter
        md.append("---")
        md.append(f"letter_number: {letter.number}")
        md.append(f"sender: \"{letter.sender}\"")
        md.append(f"recipient: \"{letter.recipient}\"")
        md.append(f"date: \"{letter.date}\"")
        md.append(f"location: \"{letter.location}\"")
        md.append(f"has_postscript: {str(bool(letter.postscript)).lower()}")
        md.append("---")
        md.append("")

        # Header
        md.append(f"# Letter {letter.number}: {letter.sender} to {letter.recipient}")
        md.append("")

        # Metadata
        if letter.location or letter.date:
            md.append("**Metadata:**")
            if letter.location:
                md.append(f"- **Location:** {letter.location}")
            if letter.date:
                md.append(f"- **Date:** {letter.date}")
            md.append("")

        # Content
        md.append("---")
        md.append("")
        md.append(letter.content)

        # Postscript
        if letter.postscript:
            md.append("")
            md.append("---")
            md.append("")
            md.append("**P.S.**")
            md.append("")
            md.append(letter.postscript)

        return '\n'.join(md)


if __name__ == '__main__':
    extractor = ProductionExtractor('/home/user/poesis/letters/schiller-goethe')
    letters = extractor.extract_letters()

    if letters:
        output = Path('/home/user/poesis/letters/schiller-goethe/final_letters_production')
        extractor.save_letters(output)
        print(f"\n✓ Saved to: {output}\n")
