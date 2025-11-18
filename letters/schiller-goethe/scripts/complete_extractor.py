#!/usr/bin/env python3
"""
COMPLETE Letter Extractor - Handles postscripts and all edge cases
"""

import re
import json
from pathlib import Path
from typing import List, Optional, Tuple
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
    postscript: str


class CompleteExtractor:
    """Final complete extractor with postscript handling"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []

    def extract_letters(self) -> List[Letter]:
        """Extract letters"""
        print("="*80)
        print("COMPLETE LETTER EXTRACTION WITH POSTSCRIPT HANDLING")
        print("="*80)

        # Load full text
        full_text_path = self.base_dir / 'raw_ocr/full_text.txt'
        text = full_text_path.read_text(encoding='utf-8')

        # Find start
        start_match = re.search(r'Respected\s+Sir\s*:', text)
        if not start_match:
            return []

        letters_section = text[start_match.start():]

        # Split into blocks
        letter_blocks = []

        # First letter
        second_match = re.search(r'\n\s*II\.\s*\n', letters_section)
        if second_match:
            letter_blocks.append(letters_section[:second_match.start()])

            remaining = letters_section[second_match.start():]
            roman_pattern = r'\n\s*([IVXLCDM]+)\.\s*\n'
            positions = [(m.start(), m.group(1)) for m in re.finditer(roman_pattern, remaining)]

            for i, (pos, roman) in enumerate(positions):
                if i < len(positions) - 1:
                    next_pos = positions[i + 1][0]
                    block = remaining[pos:next_pos]
                else:
                    block = remaining[pos:]

                letter_blocks.append(block)

        print(f"Found {len(letter_blocks)} letter blocks\n")

        # Parse each
        for num, block in enumerate(letter_blocks, 1):
            letter = self._parse_letter(block, num)
            if letter:
                self.letters.append(letter)
                if num <= 20:
                    ps = " + P.S." if letter.postscript else ""
                    print(f"Letter {num:3}: {letter.sender:8} → {letter.recipient:8}  |  {letter.date or 'No date':20}{ps}")

        print(f"\n✓ Extracted {len(self.letters)} letters")
        return self.letters

    def _parse_letter(self, text: str, number: int) -> Optional[Letter]:
        """Parse single letter with postscript detection"""

        # Clean
        text = text.strip()
        text = re.sub(r'^\s*[IVXLCDM]+\.\s*\n', '', text)

        lines = text.split('\n')

        # Filter page headers
        filtered_lines = []
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

            is_header = any(re.match(p, stripped, re.IGNORECASE) for p in headers)
            if not is_header:
                filtered_lines.append(stripped)

        if len(filtered_lines) < 2:
            return None

        # Find signature line (just a name, possibly with period/punctuation)
        # Signature patterns:
        # - "Schiller."
        # - "Fr. Schiller."
        # - "Goethe."
        # - "J. W. Goethe."

        signature_idx = -1
        sender = "Unknown"

        # Search from the end for a line that looks like a signature
        for idx in range(len(filtered_lines) - 1, max(0, len(filtered_lines) - 10), -1):
            line = filtered_lines[idx]

            # Check if this line is JUST a name (not a full sentence)
            # Signature characteristics:
            # - Short (< 30 chars)
            # - Contains Schiller or Goethe
            # - Ends with period or is just the name
            # - Not part of a sentence

            if len(line) > 30:
                continue

            line_lower = line.lower()

            if 'schiller' in line_lower:
                # Make sure it's not part of a sentence like "I wrote to Schiller"
                if not any(word in line_lower for word in ['to', 'from', 'with', 'and', 'the', 'of']):
                    sender = "Schiller"
                    signature_idx = idx
                    break

            if 'goethe' in line_lower:
                if not any(word in line_lower for word in ['to', 'from', 'with', 'and', 'the', 'of']):
                    sender = "Goethe"
                    signature_idx = idx
                    break

        if signature_idx == -1:
            # No signature found - try another approach
            # Look for date line, sender might be right after it
            for idx in range(len(filtered_lines) - 1, max(0, len(filtered_lines) - 10), -1):
                line = filtered_lines[idx]
                if ',' in line and ('179' in line or '180' in line):
                    # This is likely a date line
                    # Check next line (if exists)
                    if idx + 1 < len(filtered_lines):
                        next_line = filtered_lines[idx + 1]
                        if 'schiller' in next_line.lower() and len(next_line) < 30:
                            sender = "Schiller"
                            signature_idx = idx + 1
                            break
                        elif 'goethe' in next_line.lower() and len(next_line) < 30:
                            sender = "Goethe"
                            signature_idx = idx + 1
                            break

        # Find date/location (usually just before signature)
        date_str = ""
        location = ""
        date_idx = -1

        if signature_idx > 0:
            # Check line before signature
            for idx in range(signature_idx - 1, max(0, signature_idx - 3), -1):
                line = filtered_lines[idx]
                if ',' in line:
                    date_match = re.search(r'([A-Z][a-z]+),\s+([A-Z][a-z]+\s+\d+[a-z]*,\s+\d{4})', line)
                    if date_match:
                        location = date_match.group(1)
                        date_str = date_match.group(2)
                        date_idx = idx
                        break

        # Determine recipient
        recipient = "Goethe" if sender == "Schiller" else "Schiller" if sender == "Goethe" else "Unknown"

        # Extract content and postscript
        if signature_idx > 0:
            # Content is everything before date line (or signature if no date)
            content_end = date_idx if date_idx > 0 else signature_idx
            content_lines = filtered_lines[:content_end]

            # Postscript is everything after signature
            postscript_lines = filtered_lines[signature_idx + 1:]
            postscript = '\n\n'.join(postscript_lines) if postscript_lines else ""
        else:
            # No signature found - use all lines as content
            content_lines = filtered_lines
            postscript = ""

        content = '\n\n'.join(content_lines)
        content = self._clean_text(content)
        postscript = self._clean_text(postscript)

        return Letter(
            number=number,
            sender=sender,
            recipient=recipient,
            date=date_str,
            location=location,
            content=content,
            postscript=postscript
        )

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts"""
        text = text.replace('v^', 'w')
        text = text.replace(' v^', ' w')
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
            sender_slug = letter.sender.lower()
            recipient_slug = letter.recipient.lower()
            date_slug = re.sub(r'[^a-z0-9]+', '_', letter.date.lower()) if letter.date else 'undated'
            date_slug = date_slug.strip('_')

            filename = f"{letter.number:04d}_{sender_slug}_to_{recipient_slug}_{date_slug}.md"

            md = self._create_markdown(letter)
            (output_path / filename).write_text(md, encoding='utf-8')

            metadata.append({
                'number': letter.number,
                'filename': filename,
                'sender': letter.sender,
                'recipient': letter.recipient,
                'date': letter.date,
                'location': letter.location,
                'word_count': len(letter.content.split()),
                'has_postscript': bool(letter.postscript)
            })

        (output_path / 'index.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

        # Summary
        schiller = len([l for l in self.letters if l.sender == 'Schiller'])
        goethe = len([l for l in self.letters if l.sender == 'Goethe'])
        unknown = len([l for l in self.letters if l.sender == 'Unknown'])
        dated = len([l for l in self.letters if l.date])
        with_ps = len([l for l in self.letters if l.postscript])

        print(f"\n" + "="*80)
        print("FINAL EXTRACTION SUMMARY")
        print("="*80)
        print(f"Total letters: {len(self.letters)}")
        print(f"  - From Schiller: {schiller} ({schiller/len(self.letters)*100:.1f}%)")
        print(f"  - From Goethe: {goethe} ({goethe/len(self.letters)*100:.1f}%)")
        print(f"  - Unknown sender: {unknown} ({unknown/len(self.letters)*100:.1f}%)")
        print(f"  - With dates: {dated}")
        print(f"  - With postscripts: {with_ps}")

    def _create_markdown(self, letter: Letter) -> str:
        """Create markdown"""
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
    base_dir = '/home/user/poesis/letters/schiller-goethe'
    extractor = CompleteExtractor(base_dir)
    letters = extractor.extract_letters()

    if letters:
        output_dir = Path(base_dir) / 'final_letters_complete'
        extractor.save_letters(output_dir)
        print(f"\nSaved to: {output_dir}")
