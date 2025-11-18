#!/usr/bin/env python3
"""
FINAL ROBUST Letter Extractor - Properly handles all edge cases
"""

import re
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Letter:
    """Individual letter with metadata"""
    number: int
    sender: str
    recipient: str
    date: str
    location: str
    content: str


class FinalRobustExtractor:
    """Properly debugged extractor"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []

    def extract_letters(self) -> List[Letter]:
        """Extract letters with proper parsing"""
        print("="*80)
        print("FINAL ROBUST LETTER EXTRACTION")
        print("="*80)

        # Load full text
        full_text_path = self.base_dir / 'raw_ocr/full_text.txt'
        text = full_text_path.read_text(encoding='utf-8')

        # Find start of letters
        start_match = re.search(r'Respected\s+Sir\s*:', text)
        if not start_match:
            print("ERROR: Could not find start of letters")
            return []

        letters_section = text[start_match.start():]

        # Split by Roman numerals
        letter_blocks = []

        # First letter
        second_letter_match = re.search(r'\n\s*II\.\s*\n', letters_section)
        if second_letter_match:
            first_letter_text = letters_section[:second_letter_match.start()]
            letter_blocks.append(first_letter_text)

            # Split remaining by Roman numerals
            remaining = letters_section[second_letter_match.start():]
            roman_pattern = r'\n\s*([IVXLCDM]+)\.\s*\n'
            positions = [(m.start(), m.group(1)) for m in re.finditer(roman_pattern, remaining)]

            for i, (pos, roman) in enumerate(positions):
                if i < len(positions) - 1:
                    next_pos = positions[i + 1][0]
                    block_text = remaining[pos:next_pos]
                else:
                    block_text = remaining[pos:]

                letter_blocks.append(block_text)

        print(f"Found {len(letter_blocks)} letter blocks\n")

        # Parse each block
        for letter_num, block_text in enumerate(letter_blocks, 1):
            letter = self._parse_letter_block(block_text, letter_num)
            if letter:
                self.letters.append(letter)
                if letter_num <= 15:
                    sender_display = f"{letter.sender:8}"
                    recip_display = f"{letter.recipient:8}"
                    date_display = letter.date if letter.date else "No date"
                    print(f"Letter {letter_num:3}: {sender_display} → {recip_display}  |  {date_display}")

        print(f"\n✓ Extracted {len(self.letters)} letters")
        return self.letters

    def _parse_letter_block(self, text: str, number: int) -> Optional[Letter]:
        """Parse letter with proper filtering"""

        # Clean and split into lines
        text = text.strip()
        text = re.sub(r'^\s*[IVXLCDM]+\.\s*\n', '', text)  # Remove Roman numeral

        lines = text.split('\n')

        # Filter out:
        # 1. Empty/whitespace lines
        # 2. Page headers (standalone "SCHILLER", "GOETHE", "CORRESPONDENCE BETWEEN", page numbers)
        # 3. Page footers

        filtered_lines = []
        page_header_patterns = [
            r'^\s*SCHILLER\s*$',
            r'^\s*GOETHE\s*$',
            r'^\s*SCHILLER\s+AND\s+GOETHE\.?\s*$',
            r'^\s*CORRESPONDENCE\s+BETWEEN\s*$',
            r'^\s*C\s*0\s*R.*E\s*X\s*C\s*E.*BETWEEN\s*$',  # OCR artifacts
            r'^\s*\d+\s*$',  # Page numbers
        ]

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Skip page headers
            is_header = False
            for pattern in page_header_patterns:
                if re.match(pattern, stripped, re.IGNORECASE):
                    is_header = True
                    break

            if not is_header:
                filtered_lines.append(stripped)

        if len(filtered_lines) < 2:
            return None

        # NOW extract signature (last non-empty line)
        signature_line = filtered_lines[-1]

        # Extract date/location (second-to-last or nearby)
        date_str = ""
        location = ""
        date_line_idx = -2

        # Search last 3 lines for date
        for idx in range(len(filtered_lines) - 1, max(0, len(filtered_lines) - 4), -1):
            line = filtered_lines[idx]
            # Pattern: "City, Month Day, Year"
            if ',' in line and ('17' in line or '18' in line):  # Has comma and looks like a year
                # Try to parse
                date_match = re.search(r'([A-Z][a-z]+),\s+([A-Z][a-z]+\s+\d+[a-z]*,\s+\d{4})', line)
                if date_match:
                    location = date_match.group(1)
                    date_str = date_match.group(2)
                    date_line_idx = idx
                    break

        # Determine sender from signature
        sender = "Unknown"
        signature_lower = signature_line.lower()

        if 'schiller' in signature_lower:
            sender = "Schiller"
        elif 'goethe' in signature_lower:
            sender = "Goethe"

        # Determine recipient
        recipient = "Goethe" if sender == "Schiller" else "Schiller" if sender == "Goethe" else "Unknown"

        # Extract content (exclude last 1-2 lines: signature + maybe date)
        if date_line_idx > 0:
            content_lines = filtered_lines[:date_line_idx]
        else:
            content_lines = filtered_lines[:-1]  # Just exclude signature

        content = '\n\n'.join(content_lines)
        content = self._clean_text(content)

        return Letter(
            number=number,
            sender=sender,
            recipient=recipient,
            date=date_str,
            location=location,
            content=content
        )

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts"""
        # Fix v^ -> w
        text = text.replace('v^', 'w')
        text = text.replace(' v^', ' w')

        # Fix hyphenated words
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

        # Fix spaces
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\n\n+', '\n\n', text)

        return text.strip()

    def save_letters(self, output_dir: str):
        """Save letters to markdown"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving {len(self.letters)} letters...")

        metadata = []

        for letter in self.letters:
            sender_slug = letter.sender.lower().replace(' ', '_')
            recipient_slug = letter.recipient.lower().replace(' ', '_')
            date_slug = re.sub(r'[^a-z0-9]+', '_', letter.date.lower()) if letter.date else 'undated'
            date_slug = date_slug.strip('_')

            filename = f"{letter.number:04d}_{sender_slug}_to_{recipient_slug}_{date_slug}.md"

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
                'word_count': len(letter.content.split())
            })

        # Save index
        (output_path / 'index.json').write_text(
            json.dumps(metadata, indent=2),
            encoding='utf-8'
        )

        # Print summary
        schiller_count = len([l for l in self.letters if l.sender == 'Schiller'])
        goethe_count = len([l for l in self.letters if l.sender == 'Goethe'])
        unknown_count = len([l for l in self.letters if l.sender == 'Unknown'])
        dated_count = len([l for l in self.letters if l.date])

        print(f"\n" + "="*80)
        print("EXTRACTION SUMMARY")
        print("="*80)
        print(f"Total letters: {len(self.letters)}")
        print(f"  - From Schiller: {schiller_count}")
        print(f"  - From Goethe: {goethe_count}")
        print(f"  - Unknown sender: {unknown_count}")
        print(f"  - With dates: {dated_count}")
        print(f"  - Missing dates: {len(self.letters) - dated_count}")

    def _create_markdown(self, letter: Letter) -> str:
        """Create markdown"""
        md = []

        md.append("---")
        md.append(f"letter_number: {letter.number}")
        md.append(f"sender: \"{letter.sender}\"")
        md.append(f"recipient: \"{letter.recipient}\"")
        md.append(f"date: \"{letter.date}\"")
        md.append(f"location: \"{letter.location}\"")
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

        return '\n'.join(md)


if __name__ == '__main__':
    import sys

    base_dir = sys.argv[1] if len(sys.argv) > 1 else '/home/user/poesis/letters/schiller-goethe'

    extractor = FinalRobustExtractor(base_dir)
    letters = extractor.extract_letters()

    if letters:
        output_dir = Path(base_dir) / 'final_letters_v2'
        extractor.save_letters(output_dir)

        print(f"\nOutput: {output_dir}")
        print("="*80)
