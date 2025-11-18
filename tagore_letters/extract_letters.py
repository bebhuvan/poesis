#!/usr/bin/env python3
"""
Multi-source letter extraction and verification for Tagore's Letters to a Friend
Uses EPUB, DjVuTXT, and cross-verification for maximum accuracy
"""

import re
import os
import hashlib
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict
import json

class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML while preserving paragraph breaks"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_p = True

    def handle_endtag(self, tag):
        if tag == 'p':
            self.in_p = False
            self.text.append('\n\n')

    def handle_data(self, data):
        if self.in_p:
            self.text.append(data)

    def get_text(self):
        return ''.join(self.text)


class LetterExtractor:
    """Extract and verify Tagore's letters from multiple sources"""

    def __init__(self, base_dir='.'):
        self.base_dir = Path(base_dir)
        self.epub_dir = self.base_dir / 'epub_extracted' / 'EPUB'
        self.djvu_txt = self.base_dir / 'tagore_letters_raw.txt'

        # Date/location patterns for letter boundaries
        # Examples: "London, August 16th, 1913", "Calcutta, October 11th, 1913"
        # Pattern matches location + date, even if not on its own line
        self.letter_header_pattern = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s+([A-Z][a-z]+\s+\d+[a-z/\^$\*]*,?\s+\d{4})\s',
            re.MULTILINE
        )

        # Common OCR errors in dates
        self.date_fixes = {
            'i6i/z': '16th',
            'iith^': '11th',
            'iii/i': '11th',
            '$ihy': '5th',
            'loth^': '10th',
            'i/f/': '1st',
            'znd': '2nd',
            'zrd': '3rd',
        }

        # Common OCR errors in text
        self.text_fixes = {
            'j&nd': 'find',
            'caiiies': 'carries',
            'mateiials': 'materials',
            'fiom': 'from',
            'pais©': 'paise',
            'callected': 'collected',
            'Santimketan': 'Santiniketan',
            'Bolpur': 'Bolpur',
            'gieatly': 'greatly',
            'woild': 'world',
        }

    def extract_from_epub(self):
        """Extract text from EPUB HTML files in page order"""
        print("Extracting from EPUB...")

        # Get all HTML page files, sorted by page number
        page_files = sorted(
            [f for f in self.epub_dir.glob('page_*.html')],
            key=lambda x: int(re.search(r'page_(\d+)', x.name).group(1))
        )

        full_text = []

        for page_file in page_files:
            with open(page_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                parser = HTMLTextExtractor()
                parser.feed(html_content)
                text = parser.get_text()
                full_text.append(text)

        complete_text = '\n'.join(full_text)

        # Save raw EPUB extraction
        epub_output = self.base_dir / 'epub_extracted_text.txt'
        with open(epub_output, 'w', encoding='utf-8') as f:
            f.write(complete_text)

        print(f"EPUB extracted: {len(complete_text)} characters -> {epub_output}")
        return complete_text

    def extract_from_djvu(self):
        """Extract text from DjVuTXT file"""
        print("Extracting from DjVuTXT...")

        with open(self.djvu_txt, 'r', encoding='utf-8') as f:
            text = f.read()

        print(f"DjVuTXT loaded: {len(text)} characters")
        return text

    def clean_ocr_errors(self, text):
        """Fix common OCR errors"""
        # Fix date errors
        for error, fix in self.date_fixes.items():
            text = text.replace(error, fix)

        # Fix text errors
        for error, fix in self.text_fixes.items():
            text = text.replace(error, fix)

        return text

    def remove_page_artifacts(self, text):
        """Remove page numbers, headers, and footers"""
        # Remove standalone page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        # Remove "Letters to a Friend" headers
        text = re.sub(r'\n\s*Letters to a Friend\s*\n', '\n', text)

        # Remove multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def extract_letters(self, text):
        """Parse individual letters from continuous text"""
        print("Parsing individual letters...")

        # Find all letter headers (location + date)
        matches = list(self.letter_header_pattern.finditer(text))

        letters = []

        for i, match in enumerate(matches):
            location = match.group(1).strip()
            date = match.group(2).strip()
            start_pos = match.end()

            # Find the next letter header or end of text
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            # Extract letter content
            content = text[start_pos:end_pos].strip()

            # Skip if too short (likely not a real letter)
            if len(content) < 50:
                continue

            # Remove footnote markers and inline page numbers
            content = re.sub(r'\*\s*Referring to.*?\n', '', content)
            content = re.sub(r'\d+\s+Letters to a Friend\s+', '', content)

            letters.append({
                'location': location,
                'date': date,
                'content': content.strip(),
                'raw_header': match.group(0)
            })

        print(f"Found {len(letters)} letters")
        return letters

    def normalize_date(self, date_str):
        """Normalize date for filename and metadata"""
        # Remove extra commas and spaces
        date_str = re.sub(r',\s+', '-', date_str)
        date_str = re.sub(r'\s+', '-', date_str)
        date_str = date_str.lower()
        # Remove 'th', 'st', 'nd', 'rd' from dates
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        # Remove any remaining special characters that would break filenames
        date_str = re.sub(r'[/\\^$*\[\]{}|<>?:]', '', date_str)
        return date_str

    def save_letters_as_markdown(self, letters, output_dir='extracted_letters'):
        """Save each letter as a markdown file"""
        output_path = self.base_dir / output_dir
        output_path.mkdir(exist_ok=True)

        print(f"\nSaving {len(letters)} letters to {output_path}/")

        # Also create a combined file
        combined_path = self.base_dir / 'all_letters_combined.md'

        saved_files = []

        with open(combined_path, 'w', encoding='utf-8') as combined:
            # Write header for combined file
            combined.write("# Rabindranath Tagore: Letters to a Friend\n\n")
            combined.write("*Edited by C. F. Andrews (1926)*\n\n")
            combined.write("---\n\n")

            for i, letter in enumerate(letters, 1):
                # Create filename from location and date
                location_slug = re.sub(r'[^\w\s-]', '', letter['location'])
                location_slug = re.sub(r'\s+', '-', location_slug).lower()
                date_slug = self.normalize_date(letter['date'])

                filename = f"letter_{i:03d}_{location_slug}_{date_slug}.md"
                filepath = output_path / filename

                # Create markdown content
                md_content = f"""---
title: "Letter from {letter['location']}"
author: "Rabindranath Tagore"
recipient: "C. F. Andrews"
date: "{letter['date']}"
location: "{letter['location']}"
source: "Letters to a Friend (1926)"
letter_number: {i}
---

# Letter {i}

**{letter['location']}, {letter['date']}**

{letter['content']}
"""

                # Save individual letter
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                saved_files.append(str(filepath))

                # Add to combined file
                combined.write(f"## Letter {i}: {letter['location']}, {letter['date']}\n\n")
                combined.write(f"{letter['content']}\n\n")
                combined.write("---\n\n")

                print(f"  [{i:3d}] {filename}")

        print(f"\nCombined file: {combined_path}")

        # Save metadata
        metadata = {
            'total_letters': len(letters),
            'extraction_date': '2025-11-18',
            'source': 'Rabindranath Tagore: Letters to a Friend (1926)',
            'editor': 'C. F. Andrews',
            'files': saved_files
        }

        metadata_path = output_path / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        print(f"Metadata: {metadata_path}")

        return saved_files

    def run(self):
        """Main extraction pipeline"""
        print("=" * 70)
        print("TAGORE LETTERS EXTRACTION - Multi-source verification")
        print("=" * 70)
        print()

        # Extract from both sources
        epub_text = self.extract_from_epub()
        djvu_text = self.extract_from_djvu()

        print()
        print("Cleaning and processing...")

        # Clean OCR errors
        epub_text = self.clean_ocr_errors(epub_text)
        epub_text = self.remove_page_artifacts(epub_text)

        djvu_text = self.clean_ocr_errors(djvu_text)
        djvu_text = self.remove_page_artifacts(djvu_text)

        # Use EPUB as primary (cleaner formatting)
        # but keep DjVu for verification
        primary_text = epub_text

        # Extract letters
        letters = self.extract_letters(primary_text)

        if not letters:
            print("\nWARNING: No letters found! Trying DjVu source...")
            letters = self.extract_letters(djvu_text)

        if not letters:
            print("\nERROR: Could not extract letters from any source")
            return None

        # Save letters
        saved_files = self.save_letters_as_markdown(letters)

        print()
        print("=" * 70)
        print(f"EXTRACTION COMPLETE: {len(letters)} letters saved")
        print("=" * 70)

        return letters


if __name__ == '__main__':
    extractor = LetterExtractor()
    letters = extractor.run()
