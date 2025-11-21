#!/usr/bin/env python3
"""
Simple, pragmatic letter parser for Dostoevsky letters.
Uses the plain text file from Internet Archive.
"""

import re
import json
from pathlib import Path
from datetime import datetime

class SimpleLetterParser:
    def __init__(self):
        self.letters = []

    def parse_text_file(self, filepath):
        """Parse the plain text file into letters"""
        print(f"Reading {filepath}...")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # Find the start of the actual letters (after table of contents)
        # The letters start after the biographical section
        # First letter starts with "To his Father" followed by the date "May 10, 1838"
        # and then "MY DEAR GOOD FATHER"

        letters_start = text.find("MY  DEAR  GOOD  FATHER")

        if letters_start == -1:
            print("Could not find start of letters!")
            return []

        # Back up to find the header
        # Search backwards for "To his Father"
        header_start = text.rfind("To  his  Father", max(0, letters_start - 200), letters_start)

        if header_start == -1:
            header_start = letters_start

        letters_text = text[header_start:]

        # Split by letter boundaries
        # In this OCR text, we have patterns like:
        # "To  his  Father" or "II\n\nTo  his  Brother" or numbered Roman numerals

        # Split by pattern: Roman numerals or "To  " at line start
        # Pattern matches: optional whitespace, optional Roman numeral,  newlines, then "To  "
        pattern = r'\n\s*(?=[IVXL]+\s*\n|To  )'

        parts = re.split(pattern, letters_text)

        print(f"Split into {len(parts)} potential letters")

        for i, part in enumerate(parts):
            letter = self._parse_letter(part, i + 1)
            if letter and len(letter['body']) > 50:  # Skip very short sections
                self.letters.append(letter)

        print(f"Extracted {len(self.letters)} letters")
        return self.letters

    def _parse_letter(self, text, number):
        """Parse a single letter from text"""
        lines = text.strip().split('\n')

        if not lines:
            return None

        letter = {
            'number': number,
            'recipient': None,
            'date': None,
            'header_text': '',
            'body': '',
            'paragraphs': [],
            'footnotes': {}
        }

        # First line is usually the header
        header_line = lines[0].strip()
        letter['header_text'] = header_line

        # Parse recipient and date from header
        # Format: "To  his  Father\n\nMay  10,  1838."
        # or "To  his  Brother  Michael\n\nAugust  9,  1838."
        # Note: OCR has double spaces

        # Extract recipient (after "To  " until newline or date)
        to_match = re.search(r'To\s+([^\n:]+)', header_line)
        if to_match:
            recipient = to_match.group(1).strip()
            # Clean up OCR double spaces
            recipient = re.sub(r'\s+', ' ', recipient)
            letter['recipient'] = recipient

        # Extract date - look in first few lines
        # Dates are on separate lines typically
        first_lines = '\n'.join(lines[:5])
        date_pattern = r'([A-Z][a-z]+\s+\d{1,2}(?:,\s+|\s+)\d{4})'
        date_match = re.search(date_pattern, first_lines)
        if date_match:
            letter['date'] = date_match.group(1).strip()

        # Rest is body (skip empty lines at start)
        body_lines = []
        footnote_lines = []
        in_footnotes = False

        for line in lines[1:]:
            line = line.strip()

            if not line:
                continue

            # Check if this is a footnote (usually starts with a number)
            # Footnotes are typically at the end and shorter
            if re.match(r'^\d+\s+[A-Z]', line) and len(line) < 150:
                in_footnotes = True
                footnote_lines.append(line)
            elif in_footnotes:
                footnote_lines.append(line)
            else:
                body_lines.append(line)

        letter['body'] = '\n\n'.join(body_lines)
        letter['paragraphs'] = body_lines

        # Parse footnotes
        if footnote_lines:
            letter['footnotes'] = self._parse_footnotes('\n'.join(footnote_lines))

        return letter

    def _parse_footnotes(self, footnote_text):
        """Parse footnotes from text"""
        footnotes = {}

        # Split by footnote numbers
        parts = re.split(r'(\d+)\s+', footnote_text)

        current_num = None
        for i, part in enumerate(parts):
            if part.strip().isdigit():
                current_num = part.strip()
            elif current_num and part.strip():
                footnotes[current_num] = part.strip()
                current_num = None

        return footnotes

    def save_as_markdown(self, output_dir):
        """Save each letter as markdown file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving {len(self.letters)} letters to {output_dir}...")

        for letter in self.letters:
            # Generate filename
            num = letter['number']
            recipient = letter.get('recipient') or 'Unknown'
            recipient = recipient.replace(' ', '_')
            recipient = re.sub(r'[^a-zA-Z0-9_-]', '', recipient)[:50]

            filename = f"{num:03d}_{recipient}.md"

            # Generate markdown
            md_content = self._letter_to_markdown(letter)

            # Save
            filepath = output_path / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)

        print(f"Saved {len(self.letters)} markdown files")

    def _letter_to_markdown(self, letter):
        """Convert letter to markdown with frontmatter"""
        lines = []

        # YAML frontmatter
        lines.append('---')
        lines.append(f'letter_number: {letter["number"]}')
        lines.append(f'author: Fyodor Dostoevsky')

        if letter.get('recipient'):
            title = f"Letter to {letter['recipient']}"
            lines.append(f'title: "{title}"')
            lines.append(f'recipient: "{letter["recipient"]}"')

        if letter.get('date'):
            lines.append(f'date: "{letter["date"]}"')

        lines.append('translator: Ethel Colburn Mayne')
        lines.append('source: "Letters of Fyodor Michailovitch Dostoevsky (1917)"')
        lines.append('source_url: "https://archive.org/details/lettersoffyodorm00dostiala"')

        if letter.get('footnotes'):
            lines.append(f'has_footnotes: true')
            lines.append(f'footnote_count: {len(letter["footnotes"])}')

        lines.append('public_domain: true')
        lines.append('---')
        lines.append('')

        # Header
        lines.append(f'# Letter {letter["number"]}')
        lines.append('')

        if letter.get('recipient'):
            lines.append(f'## To {letter["recipient"]}')
            lines.append('')

        if letter.get('date'):
            lines.append(f'**{letter["date"]}**')
            lines.append('')

        lines.append('---')
        lines.append('')

        # Body
        lines.append(letter.get('body', ''))
        lines.append('')

        # Footnotes
        if letter.get('footnotes'):
            lines.append('')
            lines.append('---')
            lines.append('')
            lines.append('### Footnotes')
            lines.append('')

            for num, text in sorted(letter['footnotes'].items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                lines.append(f'**[{num}]** {text}')
                lines.append('')

        return '\n'.join(lines)

    def save_as_json(self, filepath):
        """Save as JSON"""
        data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_letters': len(self.letters),
                'source': 'Letters of Fyodor Michailovitch Dostoevsky (1917)',
                'translator': 'Ethel Colburn Mayne'
            },
            'letters': self.letters
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved JSON to {filepath}")

    def print_summary(self):
        """Print summary of extracted letters"""
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total letters: {len(self.letters)}")

        with_dates = sum(1 for l in self.letters if l.get('date'))
        with_recipients = sum(1 for l in self.letters if l.get('recipient'))
        with_footnotes = sum(1 for l in self.letters if l.get('footnotes'))

        print(f"Letters with dates: {with_dates}")
        print(f"Letters with recipients: {with_recipients}")
        print(f"Letters with footnotes: {with_footnotes}")

        # Show first few
        print("\nFirst 5 letters:")
        for letter in self.letters[:5]:
            print(f"  {letter['number']}. To {letter.get('recipient', 'Unknown')} - {letter.get('date', 'No date')}")

        print("="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Parse Dostoevsky letters from plain text')
    parser.add_argument('text_file', help='Plain text file from Internet Archive')
    parser.add_argument('--output-md', default='letters_output', help='Output directory for markdown files')
    parser.add_argument('--output-json', default='letters.json', help='Output JSON file')

    args = parser.parse_args()

    # Parse
    extractor = SimpleLetterParser()
    extractor.parse_text_file(args.text_file)

    # Save
    extractor.save_as_markdown(args.output_md)
    extractor.save_as_json(args.output_json)

    # Summary
    extractor.print_summary()


if __name__ == '__main__':
    main()
