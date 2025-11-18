#!/usr/bin/env python3
"""
ULTIMATE Letter Extractor - Maximum accuracy extraction
Handles all date format variations and edge cases
"""

import re
import json
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass


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
    date_confidence: str  # "high", "medium", "low"


class UltimateExtractor:
    """Ultimate extractor with maximum robustness"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []
        self.stats = {}

    def extract_letters(self) -> List[Letter]:
        print("="*80)
        print("ULTIMATE LETTER EXTRACTION - Maximum Accuracy Mode")
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

        self._print_results()
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
        """Parse letter with maximum robustness"""

        # Clean
        text = text.strip()
        text = re.sub(r'^\s*[IVXLCDM]+\.\s*\n', '', text)

        # Filter lines
        filtered = self._filter_lines(text.split('\n'))

        if len(filtered) < 1:
            return None

        # Extract location/date with ULTRA-FLEXIBLE regex
        location, date_str, date_idx, date_confidence = self._extract_location_date_robust(filtered)

        # Determine sender
        sender, detection_method = self._determine_sender(filtered, location)

        # Recipient
        recipient = "Goethe" if sender == "Schiller" else "Schiller" if sender == "Goethe" else "Unknown"

        # Find signature
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
            detection_method=detection_method,
            date_confidence=date_confidence
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
            r'^\s*\d+\s*$',
        ]

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if not any(re.match(p, stripped, re.IGNORECASE) for p in headers):
                filtered.append(stripped)

        return filtered

    def _extract_location_date_robust(self, lines: List[str]) -> Tuple[str, str, int, str]:
        """Extract location and date with MAXIMUM flexibility - handles all 3 date formats"""
        location = ""
        date_str = ""
        date_idx = -1
        confidence = "none"

        # Search entire letter for date (some letters have postscripts after date)
        for idx in range(len(lines) - 1, -1, -1):
            line = lines[idx]

            # Look for Jena or Weimar (case insensitive)
            if re.search(r'\b(jena|weimar)\b', line, re.IGNORECASE):

                # Extract location
                loc_match = re.search(r'\b(Jena|Weimar)\b', line, re.IGNORECASE)
                if loc_match:
                    location = loc_match.group(1).capitalize()

                # Try multiple date patterns (from most specific to least)

                # Format B: Day+ordinal Month Year
                # e.g., "Jena,  23d  August,  1794" or "31st  October,  1794"
                match = re.search(
                    r'(\d+)(?:st|nd|rd|th|d)\s+([A-Z][a-z]+)\s*,?\s*(17\d{2}|18\d{2})',
                    line,
                    re.IGNORECASE
                )
                if match:
                    day = match.group(1)
                    month = match.group(2)
                    year = match.group(3)
                    date_str = f"{month} {day}, {year}"
                    date_idx = idx
                    confidence = "high"
                    break

                # Format C: Month Day+ordinal Year
                # e.g., "Weimar,  November  27th,  1794"
                match = re.search(
                    r'([A-Z][a-z]{2,})\s+(\d+)(?:st|nd|rd|th|d)\s*,?\s*(17\d{2}|18\d{2})',
                    line,
                    re.IGNORECASE
                )
                if match:
                    month = match.group(1)
                    day = match.group(2)
                    year = match.group(3)
                    # Skip if month is "Jena" or "Weimar" (location, not month)
                    if month.lower() not in ['jena', 'weimar']:
                        date_str = f"{month} {day}, {year}"
                        date_idx = idx
                        confidence = "high"
                        break

                # Format A: Month Day Year (no ordinal)
                # e.g., "Jena,  June  19,  1794"
                match = re.search(
                    r'([A-Z][a-z]{2,})\s+(\d+)\s*,?\s*(17\d{2}|18\d{2})',
                    line,
                    re.IGNORECASE
                )
                if match:
                    month = match.group(1)
                    day = match.group(2)
                    year = match.group(3)
                    # Skip if month is "Jena" or "Weimar" (location, not month)
                    if month.lower() not in ['jena', 'weimar']:
                        date_str = f"{month} {day}, {year}"
                        date_idx = idx
                        confidence = "high"
                        break

                # Fallback: Month and year only
                # e.g., "Weimar, September 1794"
                match = re.search(
                    r'([A-Z][a-z]{2,})\s+(17\d{2}|18\d{2})',
                    line,
                    re.IGNORECASE
                )
                if match:
                    month = match.group(1)
                    year = match.group(2)
                    # Skip if month is "Jena" or "Weimar"
                    if month.lower() not in ['jena', 'weimar']:
                        date_str = f"{month} {year}"
                        date_idx = idx
                        confidence = "medium"
                        break

                # Fallback: Just year (very permissive)
                match = re.search(r'(17\d{2}|18\d{2})', line)
                if match:
                    year = match.group(1)
                    date_str = year
                    date_idx = idx
                    confidence = "low"
                    break

        return location, date_str, date_idx, confidence

    def _determine_sender(self, lines: List[str], location: str) -> Tuple[str, str]:
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
            if len(line) < 30:
                line_lower = line.lower()
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
            if len(line) < 30 and sender.lower() in line.lower():
                return idx

        return -1

    def _extract_content_postscript(self, lines: List[str], date_idx: int, signature_idx: int) -> Tuple[str, str]:
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

        text = text.replace('v^', 'w').replace(' v^', ' w')
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\n\n+', '\n\n', text)

        return text.strip()

    def _print_results(self):
        """Print extraction results"""

        # Count stats
        schiller = len([l for l in self.letters if l.sender == 'Schiller'])
        goethe = len([l for l in self.letters if l.sender == 'Goethe'])
        unknown = len([l for l in self.letters if l.sender == 'Unknown'])

        by_location = len([l for l in self.letters if l.detection_method == 'location'])
        by_signature = len([l for l in self.letters if l.detection_method == 'signature'])

        with_dates = len([l for l in self.letters if l.date])
        high_conf_dates = len([l for l in self.letters if l.date_confidence == 'high'])
        medium_conf_dates = len([l for l in self.letters if l.date_confidence == 'medium'])
        low_conf_dates = len([l for l in self.letters if l.date_confidence == 'low'])

        with_ps = len([l for l in self.letters if l.postscript])

        # Store stats
        self.stats = {
            'schiller': schiller,
            'goethe': goethe,
            'unknown': unknown,
            'by_location': by_location,
            'by_signature': by_signature,
            'with_dates': with_dates,
            'high_conf_dates': high_conf_dates,
            'medium_conf_dates': medium_conf_dates,
            'low_conf_dates': low_conf_dates,
            'with_postscripts': with_ps
        }

        # Print sample
        print("Sample of first 30 letters:")
        print("-" * 95)
        print(f"{'#':3} {'Sender':8} {'→':2} {'Recipient':8} {'Date':24} {'Method':10} {'Conf':4} {'PS':2}")
        print("-" * 95)

        for i, letter in enumerate(self.letters[:30], 1):
            ps = "✓" if letter.postscript else ""
            date_display = (letter.date[:24] if letter.date else "No date").ljust(24)
            conf = letter.date_confidence[:4] if letter.date else ""
            print(f"{i:3} {letter.sender:8} → {letter.recipient:8} {date_display} {letter.detection_method:10} {conf:4} {ps:2}")

        print(f"\n✓ Extracted {len(self.letters)} letters")

        # Print summary
        print("\n" + "="*80)
        print("ULTIMATE EXTRACTION RESULTS")
        print("="*80)
        print(f"\nTotal Letters: {len(self.letters)}")
        print(f"\nBy Sender:")
        print(f"  Schiller:  {schiller:3} ({schiller/len(self.letters)*100:5.1f}%)")
        print(f"  Goethe:    {goethe:3} ({goethe/len(self.letters)*100:5.1f}%)")
        print(f"  Unknown:   {unknown:3} ({unknown/len(self.letters)*100:5.1f}%)")
        print(f"\nDetection Methods:")
        print(f"  Location:  {by_location:3}")
        print(f"  Signature: {by_signature:3}")
        print(f"  Unknown:   {unknown:3}")
        print(f"\nDates:")
        print(f"  Total with dates:     {with_dates:3}")
        print(f"  High confidence:      {high_conf_dates:3}")
        print(f"  Medium confidence:    {medium_conf_dates:3}")
        print(f"  Low confidence:       {low_conf_dates:3}")
        print(f"  No date:              {len(self.letters) - with_dates:3}")
        print(f"\nOther:")
        print(f"  With postscripts:     {with_ps:3}")
        print("="*80)

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
                'detection_method': letter.detection_method,
                'date_confidence': letter.date_confidence
            })

        # Save index
        (output_path / 'index.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(f"\n✓ Saved to: {output_path}")

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
        md.append(f"detection_method: \"{letter.detection_method}\"")
        md.append(f"date_confidence: \"{letter.date_confidence}\"")
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
    extractor = UltimateExtractor('/home/user/poesis/letters/schiller-goethe')
    letters = extractor.extract_letters()

    if letters:
        output = Path('/home/user/poesis/letters/schiller-goethe/final_letters_ultimate')
        extractor.save_letters(output)
