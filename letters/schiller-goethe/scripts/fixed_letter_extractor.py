#!/usr/bin/env python3
"""
FIXED Letter Extractor with Proper Signature and Date Parsing
Handles the actual Schiller-Goethe letter format correctly
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Letter:
    """Individual letter with metadata"""
    number: int
    sender: str
    recipient: str
    date: str
    location: str
    content: str
    raw_ending: str  # For verification


class RobustLetterExtractor:
    """Fixed extractor with proper signature parsing"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []

    def extract_letters(self) -> List[Letter]:
        """Extract letters with proper parsing"""
        print("="*80)
        print("FIXED LETTER EXTRACTION")
        print("="*80)

        # Load full text
        full_text_path = self.base_dir / 'raw_ocr/full_text.txt'
        text = full_text_path.read_text(encoding='utf-8')

        # Find start of letters (after preface)
        # Look for "Respected Sir :" which is the start of Letter I
        start_match = re.search(r'Respected\s+Sir\s*:', text)

        if not start_match:
            print("ERROR: Could not find start of letters")
            return []

        letters_section = text[start_match.start():]

        # Split into letter blocks
        # Pattern: Roman numeral followed by period and newline, OR start of text
        letter_blocks = []

        # First letter (starts with "Respected Sir")
        # Find where "II." appears
        second_letter_match = re.search(r'\n\s*II\.\s*\n', letters_section)

        if second_letter_match:
            first_letter_text = letters_section[:second_letter_match.start()]
            letter_blocks.append(('I', first_letter_text))

            # Now split the rest by Roman numerals
            remaining = letters_section[second_letter_match.start():]

            # Find all Roman numeral positions
            roman_pattern = r'\n\s*([IVXLCDM]+)\.\s*\n'
            positions = [(m.start(), m.group(1)) for m in re.finditer(roman_pattern, remaining)]

            for i, (pos, roman) in enumerate(positions):
                # Get text from this position to next position (or end)
                if i < len(positions) - 1:
                    next_pos = positions[i + 1][0]
                    block_text = remaining[pos:next_pos]
                else:
                    block_text = remaining[pos:]

                letter_blocks.append((roman, block_text))

        print(f"Found {len(letter_blocks)} letter blocks\n")

        # Parse each block
        for letter_num, (roman, block_text) in enumerate(letter_blocks, 1):
            letter = self._parse_letter_block(block_text, letter_num, roman)
            if letter:
                self.letters.append(letter)
                if letter_num <= 10:
                    print(f"Letter {letter_num}: {letter.sender} → {letter.recipient}, {letter.date}")

        print(f"\n✓ Extracted {len(self.letters)} letters")
        return self.letters

    def _parse_letter_block(self, text: str, number: int, roman_numeral: str) -> Optional[Letter]:
        """Parse a single letter block with robust signature detection"""

        # Clean the text
        text = text.strip()

        # Remove the Roman numeral if it's at the start
        text = re.sub(r'^\s*[IVXLCDM]+\.\s*\n', '', text)

        if not text:
            return None

        lines = text.split('\n')
        lines = [l.strip() for l in lines if l.strip()]

        if len(lines) < 2:
            return None

        # Extract signature (last line)
        signature_line = lines[-1]

        # Extract date/location (second-to-last or third-to-last line)
        date_str = ""
        location = ""
        date_line_idx = -2

        # Try to find date/location line
        for idx in range(len(lines) - 1, max(0, len(lines) - 4), -1):
            line = lines[idx]
            # Pattern: "City, Month Day, Year" or "City, Date"
            if ',' in line and any(month in line for month in [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]):
                date_line_idx = idx
                break

        if date_line_idx >= 0 and abs(date_line_idx) < len(lines):
            date_location_line = lines[date_line_idx]

            # Parse location and date
            # Format: "Jena, June 13, 1794" or "Weimar, June 24, 1794"
            date_match = re.search(r'([A-Z][a-z]+),\s+([A-Z][a-z]+\s+\d+[a-z]*,\s+\d{4})', date_location_line)
            if date_match:
                location = date_match.group(1)
                date_str = date_match.group(2)

        # Determine sender from signature
        sender = "Unknown"

        if 'Schiller' in signature_line or 'schiller' in signature_line.lower():
            sender = "Schiller"
        elif 'Goethe' in signature_line or 'goethe' in signature_line.lower():
            sender = "Goethe"

        # Determine recipient (opposite of sender)
        recipient = "Goethe" if sender == "Schiller" else "Schiller" if sender == "Goethe" else "Unknown"

        # Extract content (everything except last 2-3 lines)
        content_end_idx = date_line_idx if date_line_idx > 0 else -2
        content_lines = lines[:content_end_idx]

        # Clean content
        content = '\n\n'.join(content_lines)
        content = self._clean_text(content)

        # Store raw ending for verification
        raw_ending = '\n'.join(lines[content_end_idx:])

        return Letter(
            number=number,
            sender=sender,
            recipient=recipient,
            date=date_str,
            location=location,
            content=content,
            raw_ending=raw_ending
        )

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts"""
        # Fix common OCR errors
        text = text.replace('v^', 'w')
        text = text.replace(' v^', ' w')

        # Fix hyphenated words at line breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Fix multiple spaces
        text = re.sub(r' +', ' ', text)

        # Fix multiple blank lines
        text = re.sub(r'\n\n\n+', '\n\n', text)

        # Remove page numbers and headers if they slipped through
        text = re.sub(r'\n\d+\n', '\n', text)
        text = re.sub(r'\nSCHILLER\s+AND\s+GOETHE\.\n', '\n', text)
        text = re.sub(r'\nCORRESPONDENCE\s+BETWEEN\n', '\n', text)

        return text.strip()

    def save_letters(self, output_dir: str):
        """Save letters to markdown files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving {len(self.letters)} letters...")

        metadata = []

        for letter in self.letters:
            # Create filename
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

        print(f"  ✓ Saved {len(self.letters)} letters")
        print(f"  ✓ Created index.json")

        # Print summary
        schiller_count = len([l for l in self.letters if l.sender == 'Schiller'])
        goethe_count = len([l for l in self.letters if l.sender == 'Goethe'])
        unknown_count = len([l for l in self.letters if l.sender == 'Unknown'])
        dated_count = len([l for l in self.letters if l.date])

        print(f"\nSummary:")
        print(f"  - Schiller letters: {schiller_count}")
        print(f"  - Goethe letters: {goethe_count}")
        print(f"  - Unknown sender: {unknown_count}")
        print(f"  - With dates: {dated_count}")

    def _create_markdown(self, letter: Letter) -> str:
        """Create markdown formatted letter"""
        md = []

        # Front matter
        md.append("---")
        md.append(f"letter_number: {letter.number}")
        md.append(f"sender: \"{letter.sender}\"")
        md.append(f"recipient: \"{letter.recipient}\"")
        md.append(f"date: \"{letter.date}\"")
        md.append(f"location: \"{letter.location}\"")
        md.append("---")
        md.append("")

        # Header
        md.append(f"# Letter {letter.number}: {letter.sender} to {letter.recipient}")
        md.append("")

        # Metadata section
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

        return '\n'.join(md)


if __name__ == '__main__':
    import sys

    base_dir = sys.argv[1] if len(sys.argv) > 1 else '/home/user/poesis/letters/schiller-goethe'

    extractor = RobustLetterExtractor(base_dir)
    letters = extractor.extract_letters()

    if letters:
        # Save to new directory for comparison
        output_dir = Path(base_dir) / 'final_letters_fixed'
        extractor.save_letters(output_dir)

        print("\n" + "="*80)
        print("EXTRACTION COMPLETE")
        print("="*80)
        print(f"Output directory: {output_dir}")
