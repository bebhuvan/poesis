#!/usr/bin/env python3
"""
Professional Letter Extraction Tool for Dostoevsky Archive
Author: Digital Archivist + Claude
Date: 2025-11-21

Extracts, validates, and preserves Dostoevsky's letters from multiple sources.
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import ftfy  # Fix text encoding issues

class LetterExtractor:
    """
    Professional-grade letter extraction with archival quality standards.
    """

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.stats = {
            'total_letters': 0,
            'letters_with_footnotes': 0,
            'letters_with_dates': 0,
            'letters_with_recipients': 0,
            'extraction_issues': []
        }

    def log(self, message, level='INFO'):
        """Log messages if verbose mode enabled"""
        if self.verbose:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {level}: {message}")

    def extract_from_epub(self, epub_path: str) -> List[Dict]:
        """
        Extract letters from EPUB with full structure preservation.

        Returns:
            List of letter dictionaries with metadata, body, footnotes
        """
        self.log(f"Opening EPUB: {epub_path}")

        book = epub.read_epub(epub_path)
        letters = []

        # Get all items - Internet Archive EPUBs use Type 0 for content pages
        all_items = list(book.get_items())
        # Filter for HTML content
        items = [item for item in all_items
                if item.get_name().endswith(('.html', '.xhtml', '.htm'))
                and not item.get_name().startswith('nav')]
        self.log(f"Found {len(items)} HTML pages in EPUB")

        for idx, item in enumerate(items):
            self.log(f"Processing section {idx+1}/{len(items)}: {item.get_name()}")

            try:
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')

                # Extract letters from this section
                section_letters = self._parse_section(soup, idx)
                letters.extend(section_letters)

            except Exception as e:
                self.log(f"Error processing section {idx}: {e}", 'WARNING')
                self.stats['extraction_issues'].append({
                    'section': idx,
                    'error': str(e)
                })

        self.stats['total_letters'] = len(letters)
        self.log(f"Extracted {len(letters)} letters total")

        return letters

    def _parse_section(self, soup: BeautifulSoup, section_idx: int) -> List[Dict]:
        """
        Parse a single EPUB section for letters.

        Detects:
        - Letter headers (dates, recipients)
        - Body paragraphs
        - Footnotes
        - Letter boundaries
        """
        letters = []

        # Strategy 1: Look for clear letter divisions (h1, h2, h3, hr, div.letter)
        # Strategy 2: If none found, treat whole section as one letter

        # Find potential letter headers
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])

        if headers:
            # Multiple letters in this section
            for i, header in enumerate(headers):
                letter = self._extract_letter_from_header(header, soup)
                if letter:
                    letter['section_index'] = section_idx
                    letter['letter_index_in_section'] = i
                    letters.append(letter)
        else:
            # Single letter or no clear structure - extract all content
            letter = self._extract_letter_from_soup(soup)
            if letter and letter.get('body'):  # Only if has content
                letter['section_index'] = section_idx
                letter['letter_index_in_section'] = 0
                letters.append(letter)

        return letters

    def _extract_letter_from_header(self, header, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract a letter starting from a header element.
        Continues until next header or end of document.
        """
        letter = {
            'header_text': header.get_text().strip(),
            'body': '',
            'paragraphs': [],
            'footnotes': {},
            'metadata': {}
        }

        # Parse header for metadata
        metadata = self._parse_letter_header(header.get_text())
        letter['metadata'] = metadata

        # Collect all content until next header
        current = header.find_next_sibling()
        paragraphs = []

        while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
            if current.name == 'p':
                para_text = self._clean_text(current.get_text())
                if para_text:
                    paragraphs.append(para_text)

                    # Check for footnote references in this paragraph
                    footnote_refs = current.find_all(['sup', 'a'], class_=re.compile('note|footnote'))
                    for ref in footnote_refs:
                        # Mark footnote locations
                        pass

            # Check for footnote sections
            if current.get('class') and any('note' in c.lower() or 'footnote' in c.lower() for c in current.get('class')):
                footnotes = self._extract_footnotes_from_element(current)
                letter['footnotes'].update(footnotes)

            current = current.find_next_sibling()

        letter['paragraphs'] = paragraphs
        letter['body'] = '\n\n'.join(paragraphs)

        return letter if letter['body'] else None

    def _extract_letter_from_soup(self, soup: BeautifulSoup) -> Dict:
        """
        Extract letter content from entire soup object.
        Used when no clear structure is found.
        """
        letter = {
            'header_text': '',
            'body': '',
            'paragraphs': [],
            'footnotes': {},
            'metadata': {}
        }

        # Get all paragraphs
        paragraphs = soup.find_all('p')
        para_texts = []

        for p in paragraphs:
            text = self._clean_text(p.get_text())
            if text:
                # Check if this looks like a header
                if self._is_likely_header(text):
                    if not letter['header_text']:
                        letter['header_text'] = text
                        letter['metadata'] = self._parse_letter_header(text)
                else:
                    para_texts.append(text)

        letter['paragraphs'] = para_texts
        letter['body'] = '\n\n'.join(para_texts)

        # Look for footnotes in aside, div.footnote, etc.
        footnote_sections = soup.find_all(['aside', 'div', 'section'],
                                         class_=re.compile('note|footnote|endnote'))
        for section in footnote_sections:
            footnotes = self._extract_footnotes_from_element(section)
            letter['footnotes'].update(footnotes)

        return letter

    def _parse_letter_header(self, header_text: str) -> Dict:
        """
        Extract structured metadata from letter header.

        Handles formats like:
        - "To Michael Dostoevsky, January 1, 1840"
        - "LETTER TO HIS BROTHER\nJanuary 1, 1840"
        - "38. To his Sister Vera: January 1 [13], 1868"
        """
        metadata = {
            'recipient': None,
            'date_original': None,
            'date_normalized': None,
            'location': None,
            'letter_number': None
        }

        # Extract letter number
        num_match = re.match(r'^(\d+)\.?\s+', header_text)
        if num_match:
            metadata['letter_number'] = int(num_match.group(1))

        # Extract recipient - various patterns
        recipient_patterns = [
            r'[Tt]o\s+([A-Z][^:,\n\d]+?)(?::|,|\d|\n)',  # "To Michael Dostoevsky:"
            r'LETTER\s+TO\s+([A-Z][^,\n]+)',               # "LETTER TO HIS BROTHER"
        ]

        for pattern in recipient_patterns:
            match = re.search(pattern, header_text)
            if match:
                metadata['recipient'] = match.group(1).strip()
                break

        # Extract date - multiple formats
        date_patterns = [
            r'([A-Z][a-z]+\s+\d{1,2}(?:,\s+\d{4})?)',       # January 1, 1840
            r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',              # 1 January 1840
            r'([A-Z][a-z]+,?\s+\d{4})',                      # January, 1840
            r'(\d{4})',                                       # 1840
        ]

        for pattern in date_patterns:
            match = re.search(pattern, header_text)
            if match:
                metadata['date_original'] = match.group(1).strip()
                # TODO: normalize to ISO format
                break

        # Extract location if present (Petersburg, Moscow, etc.)
        location_pattern = r'([A-Z][a-z]+(?:burg|grad|cow)),?\s+(?:\d{4}|[A-Z][a-z]+)'
        match = re.search(location_pattern, header_text)
        if match:
            metadata['location'] = match.group(1)

        return metadata

    def _is_likely_header(self, text: str) -> bool:
        """Check if text looks like a letter header"""
        # Short text mentioning "To" or containing dates
        if len(text) < 200:
            if re.search(r'\b[Tt]o\s+[A-Z]', text):
                return True
            if re.search(r'[A-Z][a-z]+\s+\d{1,2},\s+\d{4}', text):
                return True
        return False

    def _extract_footnotes_from_element(self, element) -> Dict[str, str]:
        """
        Extract footnotes from a container element.

        Returns:
            Dictionary mapping footnote numbers to text
        """
        footnotes = {}

        # Find all individual footnotes
        # They might be in <p>, <li>, or direct text
        note_elements = element.find_all(['p', 'li', 'div'])

        if not note_elements:
            # Direct text in the element
            note_elements = [element]

        for note_el in note_elements:
            text = self._clean_text(note_el.get_text())
            if text:
                num, note_text = self._parse_footnote(text)
                if num and note_text:
                    footnotes[num] = note_text

        return footnotes

    def _parse_footnote(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse footnote to extract number and text.

        Handles formats:
        - "¹ Text of footnote"
        - "[1] Text of footnote"
        - "1. Text of footnote"
        - "1 Text of footnote"
        """
        # Superscript numbers
        superscript_map = {'¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
                          '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0'}

        # Try superscript
        if text[0] in superscript_map:
            num = superscript_map[text[0]]
            note_text = text[1:].strip()
            return num, note_text

        # Try bracketed format
        match = re.match(r'^\[(\d+)\]\s+(.*)', text)
        if match:
            return match.group(1), match.group(2)

        # Try numbered format
        match = re.match(r'^(\d+)\.?\s+(.*)', text)
        if match:
            return match.group(1), match.group(2)

        return None, None

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        - Fix encoding issues
        - Normalize whitespace
        - Remove page numbers
        - Fix common OCR errors
        """
        # Fix encoding
        text = ftfy.fix_text(text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove standalone page numbers (just digits)
        text = re.sub(r'^\d+$', '', text)

        # Strip
        text = text.strip()

        return text

    def save_as_json(self, letters: List[Dict], output_path: str):
        """Save extracted letters as JSON"""
        self.log(f"Saving {len(letters)} letters to {output_path}")

        output_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_letters': len(letters),
                'statistics': self.stats
            },
            'letters': letters
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        self.log(f"Saved successfully")

    def save_as_markdown(self, letters: List[Dict], output_dir: str):
        """
        Save each letter as a separate markdown file.
        Suitable for static website generation.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.log(f"Saving {len(letters)} letters as markdown to {output_dir}")

        for i, letter in enumerate(letters, 1):
            # Generate filename
            metadata = letter['metadata']
            letter_num = metadata.get('letter_number', i)
            recipient = metadata.get('recipient', 'Unknown')
            # Sanitize for filename
            recipient_slug = re.sub(r'[^a-z0-9]+', '-', recipient.lower())[:50]
            filename = f"{letter_num:03d}_{recipient_slug}.md"

            # Create markdown content
            md_content = self._letter_to_markdown(letter, letter_num)

            # Save
            filepath = output_path / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)

        self.log(f"Saved {len(letters)} markdown files")

    def _letter_to_markdown(self, letter: Dict, number: int) -> str:
        """Convert letter dictionary to markdown with YAML frontmatter"""
        metadata = letter['metadata']

        # YAML frontmatter
        frontmatter = [
            '---',
            f'letter_number: {number}',
            f'title: "Letter to {metadata.get("recipient", "Unknown")}"',
            f'author: Fyodor Dostoevsky',
        ]

        if metadata.get('recipient'):
            frontmatter.append(f'recipient: "{metadata["recipient"]}"')

        if metadata.get('date_original'):
            frontmatter.append(f'date: "{metadata["date_original"]}"')

        if metadata.get('location'):
            frontmatter.append(f'location: "{metadata["location"]}"')

        frontmatter.append('translator: Ethel Colburn Mayne')  # or detect from source
        frontmatter.append('source: Letters of Fyodor Michailovitch Dostoevsky')

        if letter.get('footnotes'):
            frontmatter.append(f'has_footnotes: true')
            frontmatter.append(f'footnote_count: {len(letter["footnotes"])}')

        frontmatter.append('---')
        frontmatter.append('')

        # Body
        body = [
            f'# Letter {number}',
            '',
            f'## {metadata.get("recipient", "Unknown Recipient")}',
            ''
        ]

        if metadata.get('date_original'):
            body.append(f'**Date**: {metadata["date_original"]}')
            body.append('')

        if metadata.get('location'):
            body.append(f'**Location**: {metadata["location"]}')
            body.append('')

        body.append('---')
        body.append('')

        # Letter body
        body.append(letter.get('body', ''))
        body.append('')

        # Footnotes
        if letter.get('footnotes'):
            body.append('---')
            body.append('')
            body.append('## Footnotes')
            body.append('')

            for num, text in sorted(letter['footnotes'].items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                body.append(f'[^{num}]: {text}')
                body.append('')

        return '\n'.join(frontmatter + body)

    def print_stats(self):
        """Print extraction statistics"""
        print("\n" + "="*60)
        print("EXTRACTION STATISTICS")
        print("="*60)
        print(f"Total letters extracted: {self.stats['total_letters']}")
        print(f"Letters with footnotes: {self.stats['letters_with_footnotes']}")
        print(f"Letters with dates: {self.stats['letters_with_dates']}")
        print(f"Letters with recipients: {self.stats['letters_with_recipients']}")

        if self.stats['extraction_issues']:
            print(f"\nIssues encountered: {len(self.stats['extraction_issues'])}")
            for issue in self.stats['extraction_issues'][:5]:  # Show first 5
                print(f"  - {issue}")

        print("="*60)


def main():
    """Main extraction workflow"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract Dostoevsky letters from EPUB')
    parser.add_argument('epub_file', help='Path to EPUB file')
    parser.add_argument('--output-json', help='Output JSON file path')
    parser.add_argument('--output-md-dir', help='Output directory for markdown files')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')

    args = parser.parse_args()

    # Create extractor
    extractor = LetterExtractor(verbose=not args.quiet)

    # Extract letters
    letters = extractor.extract_from_epub(args.epub_file)

    # Save outputs
    if args.output_json:
        extractor.save_as_json(letters, args.output_json)

    if args.output_md_dir:
        extractor.save_as_markdown(letters, args.output_md_dir)

    # Print statistics
    extractor.print_stats()


if __name__ == '__main__':
    main()
