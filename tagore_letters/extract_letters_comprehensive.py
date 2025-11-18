#!/usr/bin/env python3
"""
Comprehensive letter extraction for Tagore's Letters to a Friend
Handles all date format variations
"""

import re
import os
from pathlib import Path
from html.parser import HTMLParser
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


class ComprehensiveLetterExtractor:
    """Extract Tagore's letters with all date format variations"""

    def __init__(self, base_dir='.'):
        self.base_dir = Path(base_dir)
        self.djvu_txt = self.base_dir / 'tagore_letters_raw.txt'

        # Comprehensive date patterns
        # Matches: "London, August 16th, 1913", "Ramgarh, May 1914", "Near Paris, August 1920" etc.
        # Location is max 4 words (handles "Near Paris", "Srinagar, Kashmir", etc.)
        self.letter_pattern = re.compile(
            r'^([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-z]+){0,3}(?:,\s+[A-Z][a-z]+)?),\s+([A-Z][a-z]+(?:\s+\d+[a-z/\^$\*]*,?)?\s+\d{4})\s*$',
            re.MULTILINE
        )

        # OCR error fixes
        self.ocr_fixes = {
            # Date errors
            'i6i/z': '16th',
            'iith^': '11th',
            'iii/i': '11th',
            '$ihy': '5th',
            'loth^': '10th',
            'i/f/': '1st',
            'znd': '2nd',
            'zrd': '3rd',
            'ist^': '1st',
            '^rdj': '3rd',
            'iSth': '18th',
            'I4i/?': '14th',
            'iSthj': '15th',
            '7.1st': '21st',
            'zznd^': '22nd',
            '22rd': '22nd',
            '^th': 'th',
            'ixth^': '11th',
            'sth^': '5th',
            'iSi/z': '15th',
            '2,0th': '20th',
            'zgtk': '29th',
            'Jizwwary': 'January',
            '30//z': '30th',
            'irf/z': '10th',
            'i6//z': '16th',
            'zgth': '29th',
            '^thy': '5th',
            'izth': '12th',
            '2^th^': '25th',
            '20^/2': '20th',
            'iii/z': '11th',
            '8^/2': '8th',
            '12th j': '12th',
            'Jj/Zy 7 . 2 ndy': 'July 22nd',
            '13///': '13th',
            '2ijf': '21st',
            'iSth': '18th',

            # Location errors
            'Santimketan': 'Santiniketan',
            'SanTINIICETAN': 'Santiniketan',
            'Santiniicetan': 'Santiniketan',
            'Lomdon': 'London',
            'SuiLEiDA': 'Shileida',
            "Ch'LCVTThy": 'Calcutta',
            'Parts': 'Paris',
            'Ramgahh': 'Ramgarh',
            'ywwe': 'June',

            # Text errors
            'j&nd': 'find',
            'jom': 'join',
            'caiiies': 'carries',
            'mateiials': 'materials',
            'fiom': 'from',
            'pais©': 'paise',
            'callected': 'collected',
            'gieatly': 'greatly',
            'woild': 'world',
            'miich': 'much',
            'gerfnination': 'germination',
            'befoie': 'before',
            'countiy': 'country',
            'stianded': 'stranded',
            'stiuggle': 'struggle',
            'tuimoil': 'turmoil',
            'nieet': 'meet',
            'ignoied': 'ignored',
            'seiwice': 'service',
            'Plospital': 'Hospital',
        }

    def extract_from_djvu(self):
        """Extract text from DjVuTXT file"""
        print("Loading DjVu text...")
        with open(self.djvu_txt, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"Loaded: {len(text)} characters")
        return text

    def clean_text(self, text):
        """Fix OCR errors and clean text"""
        print("Cleaning OCR errors...")

        # Fix OCR errors
        for error, fix in self.ocr_fixes.items():
            text = text.replace(error, fix)

        # Remove page numbers (standalone numbers on their own line)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        # Remove "Letters to a Friend" headers that appear mid-text
        text = re.sub(r'\s*\d+\s+Letters to a Friend\s+', ' ', text)
        text = re.sub(r'Letters to a Friend\s+\d+\s+', ' ', text)

        # Remove multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def extract_letters(self, text):
        """Extract individual letters from text"""
        print("Parsing letters...")

        # Find all letter headers
        matches = list(self.letter_pattern.finditer(text))
        letters = []

        for i, match in enumerate(matches):
            location = match.group(1).strip()
            date = match.group(2).strip()

            # Skip if this looks like a narrative line, not a letter header
            if any(phrase in location.lower() for phrase in [
                'in the middle of',
                'during this year',
                'through the summer',
                'we were',
                'he came back',
                'after',
                'we both returned'
            ]):
                continue

            start_pos = match.end()

            # Find the next letter header or end of text
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            # Extract content
            content = text[start_pos:end_pos].strip()

            # Skip if too short
            if len(content) < 30:
                continue

            # Clean up content
            # Remove footnotes
            content = re.sub(r'\*\s*Referring to.*?\n', '', content)
            # Remove remaining page artifacts
            content = re.sub(r'\s*\d+\s*$', '', content)

            letters.append({
                'location': location,
                'date': date,
                'content': content.strip(),
                'raw_header': match.group(0)
            })

        print(f"Found {len(letters)} letters")
        return letters

    def save_letters(self, letters, output_dir='extracted_letters_complete'):
        """Save each letter as a markdown file"""
        output_path = self.base_dir / output_dir
        output_path.mkdir(exist_ok=True)

        print(f"\nSaving {len(letters)} letters to {output_path}/")

        combined_path = self.base_dir / 'tagore_letters_complete.md'
        saved_files = []

        with open(combined_path, 'w', encoding='utf-8') as combined:
            combined.write("# Rabindranath Tagore: Letters to a Friend\n\n")
            combined.write("*Edited by C. F. Andrews (1926)*\n\n")
            combined.write(f"*{len(letters)} letters extracted and cleaned*\n\n")
            combined.write("---\n\n")

            for i, letter in enumerate(letters, 1):
                # Create clean filename
                location_slug = re.sub(r'[^\w\s-]', '', letter['location'])
                location_slug = re.sub(r'\s+', '-', location_slug).lower()

                date_slug = letter['date'].lower()
                date_slug = re.sub(r'[^\w\s-]', '', date_slug)
                date_slug = re.sub(r'\s+', '-', date_slug)
                date_slug = re.sub(r'(st|nd|rd|th)', '', date_slug)

                filename = f"letter_{i:03d}_{location_slug}_{date_slug}.md"
                filepath = output_path / filename

                # Create markdown
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

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                saved_files.append(str(filepath))

                # Add to combined
                combined.write(f"## Letter {i}: {letter['location']}, {letter['date']}\n\n")
                combined.write(f"{letter['content']}\n\n")
                combined.write("---\n\n")

                print(f"  [{i:3d}] {letter['date'][:30]:<30} | {filename}")

        print(f"\nCombined file: {combined_path}")

        # Save metadata
        metadata = {
            'total_letters': len(letters),
            'extraction_date': '2025-11-18',
            'source': 'Rabindranath Tagore: Letters to a Friend (1926)',
            'editor': 'C. F. Andrews',
            'archive_url': 'https://archive.org/details/in.ernet.dli.2015.52214',
            'files': saved_files
        }

        metadata_path = output_path / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        return saved_files

    def run(self):
        """Main extraction pipeline"""
        print("=" * 80)
        print("COMPREHENSIVE TAGORE LETTERS EXTRACTION")
        print("=" * 80)
        print()

        # Extract and clean
        text = self.extract_from_djvu()
        text = self.clean_text(text)

        # Extract letters
        letters = self.extract_letters(text)

        if not letters:
            print("\nERROR: No letters found!")
            return None

        # Save
        saved_files = self.save_letters(letters)

        print()
        print("=" * 80)
        print(f"EXTRACTION COMPLETE: {len(letters)} letters saved")
        print("=" * 80)

        return letters


if __name__ == '__main__':
    extractor = ComprehensiveLetterExtractor()
    letters = extractor.run()
