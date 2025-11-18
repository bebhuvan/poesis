#!/usr/bin/env python3
"""
THOROUGH Letter Extraction - catches ALL letter formats
Handles: full dates, partial dates, month-only, various OCR errors
"""

import re
from pathlib import Path
import json

class ThoroughLetterExtractor:
    """Extract every single letter, regardless of format variations"""

    def __init__(self):
        self.djvu_txt = Path('tagore_letters_raw.txt')

        # Massive OCR fixes dictionary
        self.ocr_fixes = {
            # Dates
            'i6i/z': '16th', 'iith^': '11th', 'iii/i': '11th', '$ihy': '5th',
            'loth^': '10th', 'I4i/?': '14th', 'iSthj': '18th', '7.1st': '21st',
            'zznd^': '22nd', '22rd': '22nd', '^th': 'th', 'ixth^': '11th',
            'sth^': '5th', 'iSi/z': '15th', '2,0th': '20th', 'zgtk': '29th',
            'Jizwwary': 'January', '30//z': '30th', 'irf/z': '10th',
            'i6//z': '16th', 'zgth': '29th', '^thy': '5th', 'izth': '12th',
            '2^th^': '25th', '20^/2': '20th', 'iii/z': '11th', '8^/2': '8th',
            '12th j': '12th', 'Jj/Zy 7 . 2 ndy': 'July 22nd', '13///': '13th',
            '2ijf': '21st', 'iSth': '18th', 'zSthf': '25th', 'zsth^': '25th',
            '^oth^': '30th', 'iphy': '10th', 'ipf/z': '19th', 'zznd^': '22nd',
            '8//z': '8th', '23^6?': '23rd', '2.nd^': '2nd', 'Sihy': '5th',
            'zdth': '20th', 'znd': '2nd', 'sth^': '5th', 'x^thy': '15th',
            'zxst': '21st', '(ith': '6th', 'z ^ th ^': '25th', '28//z': '28th',
            '()thy': '0th',

            # Months
            'Fehniary': 'February', 'Novemher': 'November', 'ywwe': 'June',

            # Locations
            'Santimketan': 'Santiniketan', 'SanTINIICETAN': 'Santiniketan',
            'Santiniicetan': 'Santiniketan', 'Lomdon': 'London',
            'SuiLEiDA': 'Shileida', "Ch'LCVTThy": 'Calcutta',
            'Parts': 'Paris', 'Ramgahh': 'Ramgarh', 'New Yoric': 'New York',
            'New Yomiy': 'New York', 'New Yomfi': 'New York',
            'New YoRiif^': 'New York', 'Ni:w York': 'New York',
            'Pai^is': 'Paris',

            # Text
            'j&nd': 'find', 'jom': 'join', 'caiiies': 'carries',
            'mateiials': 'materials', 'fiom': 'from', 'pais©': 'paise',
            'callected': 'collected', 'gieatly': 'greatly', 'woild': 'world',
            'miich': 'much', 'befoie': 'before', 'countiy': 'country',
            'stianded': 'stranded', 'stiuggle': 'struggle', 'tuimoil': 'turmoil',
            'nieet': 'meet', 'ignoied': 'ignored', 'seiwice': 'service',
            'Plospital': 'Hospital', 'tlie': 'the', 'mexely': 'merely',
            'teed': 'feed', 'file': 'fire',
        }

    def clean_text(self, text):
        """Apply all OCR fixes"""
        for error, fix in self.ocr_fixes.items():
            text = text.replace(error, fix)

        # Remove page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\s*\d+\s+Letters to a Friend\s+', ' ', text)
        text = re.sub(r'Letters to a Friend\s+\d+\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def extract_all_letters(self):
        """Extract using line-by-line analysis to catch everything"""

        print("Loading source text...")
        with open(self.djvu_txt, 'r', encoding='utf-8') as f:
            text = f.read()

        # Clean first
        text = self.clean_text(text)

        # Split into lines
        lines = text.split('\n')

        letters = []
        current_letter = None
        content_lines = []

        # Patterns for letter headers
        # Very flexible to catch all variations
        header_patterns = [
            # Full: "London, August 16th, 1913"
            r'^([A-Za-z][A-Za-z\s,\.]+?),\s+([A-Z][a-z]+\s+\d+[a-z]*,?\s+\d{4})\s*$',
            # Month-Year only: "Santiniketan, February 1914"
            r'^([A-Za-z][A-Za-z\s,\.]+?),\s+([A-Z][a-z]+\s+\d{4})\s*$',
            # Partial: "Calcutta, 10th, 1915"
            r'^([A-Za-z][A-Za-z\s,\.]+?),\s+(\d+[a-z]*,?\s+\d{4})\s*$',
            # No location: "January 20th, 1915"
            r'^([A-Z][a-z]+\s+\d+[a-z]*,?\s+\d{4})\s*$',
            # Just year: "Santiniketan, 1917"
            r'^([A-Za-z][A-Za-z\s,\.]+?),\s+(\d{4})\s*$',
        ]

        # Narrative lines to skip
        skip_patterns = [
            r'^He came back', r'^In the middle', r'^During this year',
            r'^Through the summer', r'^The journey', r'^The period',
            r'^After', r'^Later', r'^Some explanation', r'^These letters',
            r'CHAPTER', r'Letters to a Friend', r'^The next', r'^This',
        ]

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty or too short
            if not line or len(line) < 5:
                if current_letter:
                    content_lines.append(line)
                continue

            # Check if it's a skip pattern
            is_skip = any(re.match(pattern, line) for pattern in skip_patterns)
            if is_skip:
                if current_letter:
                    content_lines.append(line)
                continue

            # Check if it's a new letter header
            is_header = False
            location = None
            date = None

            for pattern in header_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        location, date = groups
                    elif len(groups) == 1:
                        # No location, just date
                        location = "[Unknown]"
                        date = groups[0]

                    # Validate it looks like a real header (has year)
                    if date and re.search(r'191[3-9]|192[0-3]', date):
                        is_header = True
                        break

            if is_header:
                # Save previous letter if exists
                if current_letter:
                    current_letter['content'] = '\n'.join(content_lines).strip()
                    if len(current_letter['content']) > 30:  # Only if has real content
                        letters.append(current_letter)

                # Start new letter
                current_letter = {
                    'location': location.strip() if location else "[Unknown]",
                    'date': date.strip() if date else line.strip(),
                    'raw_header': line
                }
                content_lines = []

            elif current_letter:
                # Accumulate content for current letter
                content_lines.append(line)

        # Save last letter
        if current_letter:
            current_letter['content'] = '\n'.join(content_lines).strip()
            if len(current_letter['content']) > 30:
                letters.append(current_letter)

        return letters

    def save_letters(self, letters):
        """Save all letters"""
        output_dir = Path('extracted_letters_thorough')
        output_dir.mkdir(exist_ok=True)

        print(f"\nSaving {len(letters)} letters...")

        for i, letter in enumerate(letters, 1):
            # Create safe filename
            loc_slug = re.sub(r'[^\w\s-]', '', letter['location'])
            loc_slug = re.sub(r'\s+', '-', loc_slug).lower()[:30]

            date_slug = re.sub(r'[^\w\s-]', '', letter['date'])
            date_slug = re.sub(r'\s+', '-', date_slug).lower()[:25]

            filename = f"letter_{i:03d}_{loc_slug}_{date_slug}.md"

            # Create markdown
            md = f"""---
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

            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md)

            print(f"  [{i:3d}] {letter['date'][:30]:<30} | {letter['location'][:20]:<20}")

        # Save combined
        combined = output_dir.parent / 'tagore_letters_thorough.md'
        with open(combined, 'w', encoding='utf-8') as f:
            f.write(f"# Rabindranath Tagore: Letters to a Friend\n\n")
            f.write(f"*{len(letters)} letters (complete extraction)*\n\n")
            f.write("---\n\n")

            for i, letter in enumerate(letters, 1):
                f.write(f"## Letter {i}: {letter['location']}, {letter['date']}\n\n")
                f.write(f"{letter['content']}\n\n")
                f.write("---\n\n")

        print(f"\nCombined: {combined}")

        # Save metadata
        metadata = {
            'total_letters': len(letters),
            'extraction_method': 'thorough_line_by_line',
            'date': '2025-11-18',
        }

        with open(output_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        return len(letters)

    def run(self):
        print("=" * 80)
        print("THOROUGH TAGORE LETTERS EXTRACTION")
        print("=" * 80)
        print()

        letters = self.extract_all_letters()
        print(f"\nFound {len(letters)} letters")

        if not letters:
            print("ERROR: No letters found!")
            return 0

        count = self.save_letters(letters)

        print()
        print("=" * 80)
        print(f"COMPLETE: {count} letters extracted")
        print("=" * 80)

        return count


if __name__ == '__main__':
    extractor = ThoroughLetterExtractor()
    count = extractor.run()
    print(f"\n✓ Extracted {count} letters")
