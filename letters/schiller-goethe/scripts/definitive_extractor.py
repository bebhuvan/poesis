#!/usr/bin/env python3
"""
DEFINITIVE Letter Extractor - Uses location to determine sender
Jena = Schiller, Weimar = Goethe
"""

import re
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Letter:
    """Letter with metadata"""
    number: int
    sender: str
    recipient: str
    date: str
    location: str
    content: str
    postscript: str
    detection_method: str  # How sender was determined


class DefinitiveExtractor:
    """Location-based sender detection"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []

    def extract_letters(self) -> List[Letter]:
        print("="*80)
        print("DEFINITIVE EXTRACTION - Location-Based Sender Detection")
        print("="*80)

        # Load text
        text_path = self.base_dir / 'raw_ocr/full_text.txt'
        text = text_path.read_text(encoding='utf-8')

        # Find start
        start_match = re.search(r'Respected\s+Sir\s*:', text)
        if not start_match:
            return []

        letters_section = text[start_match.start():]

        # Split into blocks
        blocks = []
        second_match = re.search(r'\n\s*II\.\s*\n', letters_section)
        if second_match:
            blocks.append(letters_section[:second_match.start()])

            remaining = letters_section[second_match.start():]
            positions = [(m.start(), m.group(1)) for m in re.finditer(r'\n\s*([IVXLCDM]+)\.\s*\n', remaining)]

            for i, (pos, roman) in enumerate(positions):
                if i < len(positions) - 1:
                    next_pos = positions[i + 1][0]
                    blocks.append(remaining[pos:next_pos])
                else:
                    blocks.append(remaining[pos:])

        print(f"Found {len(blocks)} letter blocks\n")

        # Parse
        for num, block in enumerate(blocks, 1):
            letter = self._parse_letter(block, num)
            if letter:
                self.letters.append(letter)

        # Print sample
        print("Sample of first 25 letters:")
        print("-" * 80)
        for i, letter in enumerate(self.letters[:25], 1):
            method_str = f"[{letter.detection_method}]"
            date_str = letter.date[:20] if letter.date else "No date"
            ps = " +PS" if letter.postscript else ""
            print(f"{i:3}. {letter.sender:8} → {letter.recipient:8}  {date_str:20}  {method_str:12}{ps}")

        print(f"\n✓ Extracted {len(self.letters)} letters")
        return self.letters

    def _parse_letter(self, text: str, number: int) -> Optional[Letter]:
        """Parse with location-based sender detection"""

        text = text.strip()
        text = re.sub(r'^\s*[IVXLCDM]+\.\s*\n', '', text)

        lines = text.split('\n')

        # Filter headers
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

        if len(filtered) < 1:
            return None

        # STEP 1: Find location/date line
        location = ""
        date_str = ""
        date_idx = -1

        for idx in range(len(filtered) - 1, max(0, len(filtered) - 15), -1):
            line = filtered[idx]
            # Pattern: "City, Month Day, Year"
            if ',' in line and ('179' in line or '180' in line):
                match = re.search(r'([A-Z][a-z]+),\s+([A-Z][a-z]+\s+\d+[a-z]*,\s+\d{4})', line)
                if match:
                    location = match.group(1)
                    date_str = match.group(2)
                    date_idx = idx
                    break

        # STEP 2: Determine sender from LOCATION (primary method)
        sender = "Unknown"
        detection_method = "unknown"

        if location:
            if location.lower() == 'jena':
                sender = "Schiller"
                detection_method = "location"
            elif location.lower() == 'weimar':
                sender = "Goethe"
                detection_method = "location"

        # STEP 3: If no location, try signature
        if sender == "Unknown":
            for idx in range(len(filtered) - 1, max(0, len(filtered) - 10), -1):
                line = filtered[idx]
                if len(line) < 30:
                    line_lower = line.lower()
                    if 'schiller' in line_lower and not any(w in line_lower for w in ['to', 'from', 'with']):
                        sender = "Schiller"
                        detection_method = "signature"
                        break
                    elif 'goethe' in line_lower and not any(w in line_lower for w in ['to', 'from', 'with']):
                        sender = "Goethe"
                        detection_method = "signature"
                        break

        # Recipient
        recipient = "Goethe" if sender == "Schiller" else "Schiller" if sender == "Goethe" else "Unknown"

        # STEP 4: Find signature line for content boundary
        signature_idx = -1

        for idx in range(len(filtered) - 1, max(0, len(filtered) - 10), -1):
            line = filtered[idx]
            if len(line) < 30:
                if sender == "Schiller" and 'schiller' in line.lower():
                    signature_idx = idx
                    break
                elif sender == "Goethe" and 'goethe' in line.lower():
                    signature_idx = idx
                    break

        # STEP 5: Extract content and postscript
        if signature_idx > 0:
            content_end = date_idx if date_idx > 0 else signature_idx
            content_lines = filtered[:content_end]
            postscript_lines = filtered[signature_idx + 1:]
        elif date_idx > 0:
            content_lines = filtered[:date_idx]
            postscript_lines = []
        else:
            content_lines = filtered
            postscript_lines = []

        content = '\n\n'.join(content_lines)
        postscript = '\n\n'.join(postscript_lines) if postscript_lines else ""

        content = self._clean(content)
        postscript = self._clean(postscript)

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

    def _clean(self, text: str) -> str:
        """Clean text"""
        text = text.replace('v^', 'w').replace(' v^', ' w')
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\n\n+', '\n\n', text)
        return text.strip()

    def save_letters(self, output_dir: str):
        """Save letters"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        metadata = []

        for letter in self.letters:
            filename = f"{letter.number:04d}_{letter.sender.lower()}_to_{letter.recipient.lower()}"
            if letter.date:
                date_slug = re.sub(r'[^a-z0-9]+', '_', letter.date.lower()).strip('_')
                filename += f"_{date_slug}"
            else:
                filename += "_undated"
            filename += ".md"

            md = self._create_md(letter)
            (output_path / filename).write_text(md, encoding='utf-8')

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

        (output_path / 'index.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

        # Summary
        schiller = len([l for l in self.letters if l.sender == 'Schiller'])
        goethe = len([l for l in self.letters if l.sender == 'Goethe'])
        unknown = len([l for l in self.letters if l.sender == 'Unknown'])
        dated = len([l for l in self.letters if l.date])
        with_ps = len([l for l in self.letters if l.postscript])

        by_location = len([l for l in self.letters if l.detection_method == 'location'])
        by_signature = len([l for l in self.letters if l.detection_method == 'signature'])

        print(f"\n" + "="*80)
        print("DEFINITIVE EXTRACTION SUMMARY")
        print("="*80)
        print(f"Total letters: {len(self.letters)}")
        print(f"\nBy Sender:")
        print(f"  - Schiller: {schiller} ({schiller/len(self.letters)*100:.1f}%)")
        print(f"  - Goethe: {goethe} ({goethe/len(self.letters)*100:.1f}%)")
        print(f"  - Unknown: {unknown} ({unknown/len(self.letters)*100:.1f}%)")
        print(f"\nDetection Methods:")
        print(f"  - By location: {by_location}")
        print(f"  - By signature: {by_signature}")
        print(f"  - Unknown: {unknown}")
        print(f"\nOther Stats:")
        print(f"  - With dates: {dated}")
        print(f"  - With postscripts: {with_ps}")

    def _create_md(self, letter: Letter) -> str:
        md = []
        md.append("---")
        md.append(f"letter_number: {letter.number}")
        md.append(f"sender: \"{letter.sender}\"")
        md.append(f"recipient: \"{letter.recipient}\"")
        md.append(f"date: \"{letter.date}\"")
        md.append(f"location: \"{letter.location}\"")
        md.append(f"has_postscript: {str(bool(letter.postscript)).lower()}")
        md.append("---")
        md.append("")
        md.append(f"# Letter {letter.number}: {letter.sender} to {letter.recipient}")
        md.append("")

        if letter.location or letter.date:
            md.append("**Metadata:**")
            if letter.location:
                md.append(f"- **Location:** {letter.location}")
            if letter.date:
                md.append(f"- **Date:** {letter.date}")
            md.append("")

        md.append("---")
        md.append("")
        md.append(letter.content)

        if letter.postscript:
            md.append("")
            md.append("---")
            md.append("")
            md.append("**P.S.**")
            md.append("")
            md.append(letter.postscript)

        return '\n'.join(md)


if __name__ == '__main__':
    extractor = DefinitiveExtractor('/home/user/poesis/letters/schiller-goethe')
    letters = extractor.extract_letters()

    if letters:
        output = Path('/home/user/poesis/letters/schiller-goethe/final_letters_definitive')
        extractor.save_letters(output)
        print(f"\n✓ Saved to: {output}")
