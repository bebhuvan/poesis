#!/usr/bin/env python3
"""
Extract letters from page-by-page EPUB (Internet Archive format)
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import ftfy

class PageByPageExtractor:
    """
    Extract letters from Internet Archive style EPUB with one HTML file per page.
    """

    def __init__(self, verbose=True):
        self.verbose = verbose

    def log(self, message):
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def extract(self, epub_path: str) -> List[Dict]:
        """Extract all letters from page-based EPUB"""
        self.log(f"Opening EPUB: {epub_path}")

        book = epub.read_epub(epub_path)

        # Get all HTML pages
        all_items = list(book.get_items())
        pages = [item for item in all_items
                if item.get_name().endswith(('.html', '.xhtml'))
                and 'page_' in item.get_name()]

        # Sort by page number
        pages.sort(key=lambda x: self._extract_page_num(x.get_name()))

        self.log(f"Found {len(pages)} pages")

        # Extract text from all pages
        all_text = []
        for i, page in enumerate(pages):
            if i % 50 == 0:
                self.log(f"Processing page {i+1}/{len(pages)}")

            content = page.get_content()
            soup = BeautifulSoup(content, 'html.parser')
            page_text = soup.get_text()

            all_text.append({
                'page_num': self._extract_page_num(page.get_name()),
                'text': self._clean_text(page_text)
            })

        # Combine all pages into one text
        full_text = '\n\n[PAGE_BREAK]\n\n'.join(p['text'] for p in all_text)

        # Save full text for inspection
        with open('full_text_combined.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)

        self.log("Saved combined text to full_text_combined.txt")

        # Now split into letters
        letters = self._split_into_letters(full_text)

        self.log(f"Extracted {len(letters)} letters")

        return letters

    def _extract_page_num(self, filename: str) -> int:
        """Extract page number from filename like 'page_123.html'"""
        match = re.search(r'page_(\d+)', filename)
        return int(match.group(1)) if match else 0

    def _clean_text(self, text: str) -> str:
        """Clean OCR text"""
        # Fix encoding
        text = ftfy.fix_text(text)

        # Remove multiple spaces/newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Remove page numbers (standalone digits)
        lines = text.split('\n')
        lines = [line for line in lines if not re.match(r'^\d+$', line.strip())]

        return '\n'.join(lines).strip()

    def _split_into_letters(self, full_text: str) -> List[Dict]:
        """
        Split combined text into individual letters.

        Letter boundaries are detected by:
        1. Roman numerals (I., II., III., etc.)
        2. Numbers followed by "To" (1. To His Brother...)
        3. Headers like "LETTER TO..."
        4. Dates at start of sections
        """
        letters = []

        # Pattern for letter headers - very flexible
        # Matches things like:
        # "I.\n\nTo his Father: May 10, 1838"
        # "1. To his Brother Michael: August 9, 1838"
        # "LETTER TO HIS BROTHER"

        # Split by common patterns
        # This regex looks for numbered sections or clear letter headers
        letter_pattern = r'(?:^|\n\n+)(?:(?:[IVXLCDM]+\.|[0-9]+\.)\s*\n+|(?:LETTER\s+TO))'

        # Split text
        parts = re.split(letter_pattern, full_text, flags=re.MULTILINE)

        self.log(f"Split text into {len(parts)} potential sections")

        # Process each part
        for i, part in enumerate(parts):
            if len(part.strip()) < 100:  # Skip very short sections
                continue

            letter = self._parse_letter_text(part)
            if letter:
                letter['letter_number'] = len(letters) + 1
                letters.append(letter)

        return letters

    def _parse_letter_text(self, text: str) -> Dict:
        """Parse a letter section into structured data"""
        lines = text.strip().split('\n')

        letter = {
            'header': '',
            'recipient': None,
            'date': None,
            'body': '',
            'footnotes': {}
        }

        # First few lines are likely header
        header_lines = []
        body_start = 0

        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if self._is_header_line(line):
                header_lines.append(line)
                body_start = i + 1
            else:
                if header_lines:  # Already found header
                    break

        # Parse header
        header_text = '\n'.join(header_lines)
        letter['header'] = header_text

        # Extract metadata from header
        metadata = self._parse_header(header_text)
        letter['recipient'] = metadata.get('recipient')
        letter['date'] = metadata.get('date')

        # Rest is body
        body_lines = lines[body_start:]

        # Separate footnotes from body
        body_text = []
        footnotes = {}
        in_footnotes = False

        for line in body_lines:
            # Check if we've hit footnotes section
            if re.match(r'^\d+\s+[A-Z]', line) and len(line) < 100:
                # Looks like a footnote
                num, text = self._parse_footnote_line(line)
                if num:
                    footnotes[num] = text
                    in_footnotes = True
                    continue

            if in_footnotes:
                # Continue collecting footnote
                if footnotes:
                    last_num = list(footnotes.keys())[-1]
                    footnotes[last_num] += ' ' + line
            else:
                body_text.append(line)

        letter['body'] = '\n'.join(body_text).strip()
        letter['footnotes'] = footnotes

        return letter if letter['body'] else None

    def _is_header_line(self, line: str) -> bool:
        """Check if line looks like part of a letter header"""
        line = line.strip()

        if len(line) > 200:  # Too long for header
            return False

        # Contains "To " or recipient patterns
        if re.search(r'\bTo\s+[A-Z]', line):
            return True

        # Contains date pattern
        if re.search(r'[A-Z][a-z]+\s+\d{1,2}[,\s]+\d{4}', line):
            return True

        # Looks like "LETTER TO..."
        if re.match(r'^LETTER\s+TO', line, re.IGNORECASE):
            return True

        return False

    def _parse_header(self, header_text: str) -> Dict:
        """Extract recipient and date from header"""
        metadata = {}

        # Extract recipient
        to_pattern = r'[Tt]o\s+([A-Z][^:,\n\d]+?)(?::|,|\d)'
        match = re.search(to_pattern, header_text)
        if match:
            metadata['recipient'] = match.group(1).strip()

        # Extract date
        date_pattern = r'([A-Z][a-z]+\s+\d{1,2}(?:,\s+|\s+)\d{4})'
        match = re.search(date_pattern, header_text)
        if match:
            metadata['date'] = match.group(1).strip()

        return metadata

    def _parse_footnote_line(self, line: str):
        """Parse a footnote line"""
        match = re.match(r'^(\d+)\s+(.+)', line)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def save_json(self, letters: List[Dict], output_path: str):
        """Save as JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_date': datetime.now().isoformat(),
                'total_letters': len(letters),
                'letters': letters
            }, f, indent=2, ensure_ascii=False)

        self.log(f"Saved {len(letters)} letters to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('epub_file')
    parser.add_argument('--output', default='letters_extracted.json')

    args = parser.parse_args()

    extractor = PageByPageExtractor()
    letters = extractor.extract(args.epub_file)
    extractor.save_json(letters, args.output)

    # Show sample
    if letters:
        print("\n" + "="*60)
        print("SAMPLE LETTER:")
        print("="*60)
        sample = letters[0]
        print(f"Recipient: {sample.get('recipient')}")
        print(f"Date: {sample.get('date')}")
        print(f"Body preview: {sample.get('body')[:300]}...")
        print(f"Footnotes: {len(sample.get('footnotes', {}))}")


if __name__ == '__main__':
    main()
