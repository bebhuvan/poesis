#!/usr/bin/env python3
"""
Enhanced letter extractor (v3) that handles missing Roman numerals.

Improvements over v2:
- Detects letters 50 and 53 which lack Roman numeral markers in source
- Better date extraction patterns
- More robust recipient parsing
- Improved boundary detection to exclude biography/appendix sections
"""

import re
import json
from pathlib import Path
from datetime import datetime

class EnhancedLetterExtractor:
    def __init__(self):
        self.roman_to_int = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
            'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20,
            'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25,
            'XXVI': 26, 'XXVII': 27, 'XXVIII': 28, 'XXIX': 29, 'XXX': 30,
            'XXXI': 31, 'XXXII': 32, 'XXXIII': 33, 'XXXIV': 34, 'XXXV': 35,
            'XXXVI': 36, 'XXXVII': 37, 'XXXVIII': 38, 'XXXIX': 39, 'XL': 40,
            'XLI': 41, 'XLII': 42, 'XLIII': 43, 'XLIV': 44, 'XLV': 45,
            'XLVI': 46, 'XLVII': 47, 'XLVIII': 48, 'XLIX': 49, 'L': 50,
            'LI': 51, 'LII': 52, 'LIII': 53, 'LIV': 54, 'LV': 55,
            'LVI': 56, 'LVII': 57, 'LVIII': 58, 'LIX': 59, 'LX': 60,
            'LXI': 61, 'LXII': 62, 'LXIII': 63, 'LXIV': 64, 'LXV': 65,
            'LXVI': 66, 'LXVII': 67, 'LXVIII': 68, 'LXIX': 69, 'LXX': 70,
            'LXXI': 71, 'LXXII': 72, 'LXXIII': 73, 'LXXIV': 74, 'LXXV': 75,
            'LXXVI': 76, 'LXXVII': 77
        }

    def extract(self, text_file):
        """Extract all letters using Roman numeral boundaries and special cases"""
        print(f"Reading {text_file}...")

        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # Find letters section boundaries
        letters_start = text.find("MY  DEAR  GOOD  FATHER")
        if letters_start == -1:
            print("Could not find start of letters!")
            return []

        # Back up to find first letter header
        header_start = text.rfind("To  his  Father", max(0, letters_start - 500), letters_start)
        if header_start == -1:
            header_start = letters_start

        # Find end of letters section (before appendix "RECOLLECTIONS OF DOSTOEVSKY")
        letters_end = text.find("RECOLLECTIONS  OF  DOSTOEVSKY", letters_start)
        if letters_end == -1:
            letters_end = len(text)

        letters_text = text[header_start:letters_end]

        # Split by Roman numerals
        pattern = r'\n\s*\n\s*([IVXL]+)\s*\n'
        matches = list(re.finditer(pattern, letters_text))
        parts = re.split(pattern, letters_text)

        print(f"Split into {len(parts)} parts")
        print(f"Found {len(matches)} Roman numeral markers")

        letters = []

        # Process first letter (no Roman numeral)
        if parts[0].strip():
            letter = self._parse_letter(parts[0], 1)
            if letter:
                letters.append(letter)

        # Process remaining letters (pairs of: roman_numeral, content)
        for i in range(1, len(parts), 2):
            if i + 1 >= len(parts):
                break

            roman = parts[i].strip()
            content = parts[i + 1]

            # Get letter number from Roman numeral
            letter_num = self.roman_to_int.get(roman, len(letters) + 1)

            letter = self._parse_letter(content, letter_num)
            if letter:
                letters.append(letter)

        # Extract special cases: letters 50 and 53 (missing Roman numerals)
        print("Extracting letters without Roman numeral markers...")

        letter_50 = self._extract_special_letter_50(text)
        if letter_50:
            letters.append(letter_50)
            print("  ✓ Letter 50 extracted (no 'L' marker in source)")

        letter_53 = self._extract_special_letter_53(text)
        if letter_53:
            letters.append(letter_53)
            print("  ✓ Letter 53 extracted (no 'LIII' marker in source)")

        # Sort letters by number
        letters.sort(key=lambda x: x['number'])

        print(f"Extracted {len(letters)} letters total")

        return letters

    def _extract_special_letter_50(self, full_text):
        """Extract letter 50 which exists between XLIX and LI without Roman numeral marker"""
        # Find XLIX and LI positions
        xlix_match = re.search(r'\n\s*\n\s*XLIX\s*\n', full_text)
        li_match = re.search(r'\n\s*\n\s*LI\s*\n', full_text)

        if not xlix_match or not li_match:
            return None

        # Get text between XLIX and LI
        gap = full_text[xlix_match.end():li_match.start()]

        # Find "To his Niece Sofia Alexandrovna" (start of letter 50)
        to_match = re.search(r'(To\s+his\s+Niece\s+Sofia\s+Alexandrovna.*)', gap, re.DOTALL)

        if to_match:
            content = to_match.group(1).strip()
            # Remove page headers
            content = re.sub(r'\d+\s+DOSTOEVSKY\'S\s+LETTERS\s+\[[IVXL]+\]?\s*\n', '\n', content)

            # Quality check
            if ('August  29' in content or 'September  10' in content) and len(content) > 2000:
                return self._parse_letter(content, 50)

        return None

    def _extract_special_letter_53(self, full_text):
        """Extract letter 53 which exists between LII and LIV without Roman numeral marker"""
        # Find LII and LIV positions
        lii_match = re.search(r'\n\s*\n\s*LII\s*\n', full_text)
        liv_match = re.search(r'\n\s*\n\s*LIV\s*\n', full_text)

        if not lii_match or not liv_match:
            return None

        # Get text between LII and LIV
        gap = full_text[lii_match.end():liv_match.start()]

        # Find all "To" patterns (first is letter 52, second is letter 53)
        to_patterns = list(re.finditer(r'To\s+([^\n]+)', gap))

        if len(to_patterns) >= 2:
            # Second "To" is letter 53
            second_to_start = to_patterns[1].start()
            content = gap[second_to_start:].strip()
            # Remove page headers
            content = re.sub(r'\d+\s+[A-Z\s\']+\[[IVXL]+\]?\s*\n', '\n', content)

            # Quality check: should be to Strachov, not Maikov
            if ('Strachov' in content[:100] and 'Maikov' not in content[:100] and
                ('February  26' in content or 'March  10' in content)):
                return self._parse_letter(content, 53)

        return None

    def _parse_letter(self, text, number):
        """Parse a single letter"""
        lines = text.strip().split('\n')

        letter = {
            'number': number,
            'recipient': None,
            'date': None,
            'location': None,
            'body': '',
            'paragraphs': [],
            'footnotes': {}
        }

        # Look for "To [recipient]" in first few lines
        body_start_line = 0
        for i, line in enumerate(lines[:15]):
            # More flexible "To" pattern
            to_match = re.search(r'^To\s+(.+?)(?:\s*$)', line.strip())
            if to_match:
                recipient = to_match.group(1).strip()
                # Clean up
                recipient = re.sub(r'\s+', ' ', recipient)
                # Remove trailing punctuation
                recipient = recipient.rstrip('.,;:')
                letter['recipient'] = recipient

                # Look for date/location in next few lines
                for j in range(i + 1, min(i + 8, len(lines))):
                    check_line = lines[j].strip()

                    if not check_line:
                        continue

                    # Try to extract date (improved pattern)
                    date = self._parse_date(check_line)
                    if date:
                        letter['date'] = date

                    # Check if it's a location (all caps, often ends with comma)
                    if check_line.isupper() and len(check_line) < 50:
                        if check_line.endswith(','):
                            letter['location'] = check_line.rstrip(',').strip()
                        # Sometimes location is on same line as date
                        elif not any(char.isdigit() for char in check_line):
                            letter['location'] = check_line.strip()

                    # If we see all caps salutation, body is starting
                    if check_line.isupper() and len(check_line.split()) > 3:
                        # Check if it's a salutation (contains words like DEAR, HONOURED, etc.)
                        if any(word in check_line for word in ['DEAR', 'HONOURED', 'ESTEEMED', 'BELOVED']):
                            body_start_line = j
                            break

                # If no body start found, guess based on what we have
                if body_start_line == 0:
                    if letter.get('date'):
                        # Find line with date, body starts after
                        for j in range(i + 1, len(lines)):
                            if self._parse_date(lines[j]):
                                body_start_line = j + 1
                                break
                    else:
                        body_start_line = i + 3

                body_lines = lines[body_start_line:]
                break
        else:
            # No "To [recipient]" found, use all lines
            body_lines = lines

        # Extract body and footnotes
        body_text = []
        footnote_lines = []
        in_footnotes = False

        for line in body_lines:
            line = line.strip()

            if not line:
                continue

            # Check for footnote markers (digit followed by space and capital letter)
            if re.match(r'^\d+\s+[A-Z]', line) and len(line) < 200:
                in_footnotes = True
                footnote_lines.append(line)
            elif in_footnotes:
                footnote_lines.append(line)
            else:
                body_text.append(line)

        letter['body'] = '\n\n'.join(body_text)
        letter['paragraphs'] = body_text

        # Parse footnotes
        if footnote_lines:
            letter['footnotes'] = self._parse_footnotes('\n'.join(footnote_lines))

        return letter

    def _parse_date(self, text):
        """Extract date from text with improved pattern matching"""
        # Pattern 1: Full date like "August 9, 1838" or "May  10,  1838" (double spaces)
        match = re.search(r'([A-Z][a-z]+\s+[0-9i]{1,2}(?:,\s*|\s+)\d{4})', text)
        if match:
            date = match.group(1).strip()
            # Clean up double spaces and fix OCR errors
            date = re.sub(r'\s+', ' ', date)
            # Fix common OCR: "i," -> "1,"
            date = re.sub(r'\bi\b', '1', date)
            return date

        # Pattern 2: Date with brackets like "August 29 [September 10], 1869"
        match = re.search(r'([A-Z][a-z]+\s+\d{1,2}\s*\[[A-Z][a-z]+\s+\d{1,2}\],\s*\d{4})', text)
        if match:
            date = match.group(1).strip()
            date = re.sub(r'\s+', ' ', date)
            return date

        # Pattern 3: Month and day only
        match = re.search(r'([A-Z][a-z]+\s+\d{1,2}(?:,|\s*$))', text)
        if match:
            date = match.group(1).strip()
            date = re.sub(r'\s+', ' ', date)
            # Only return if it looks like a standalone date
            if len(date) < 30:
                return date

        return None

    def _parse_footnotes(self, text):
        """Parse footnotes from text"""
        footnotes = {}

        # Split by footnote numbers
        parts = re.split(r'(\d+)\s+', text)

        current_num = None
        for part in parts:
            if part.strip().isdigit():
                current_num = part.strip()
            elif current_num and part.strip():
                footnotes[current_num] = part.strip()
                current_num = None

        return footnotes

    def save_json(self, letters, output_file):
        """Save as JSON"""
        data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_letters': len(letters),
                'extractor_version': 3,
                'source': 'Letters of Fyodor Michailovitch Dostoevsky (1917)',
                'translator': 'Ethel Colburn Mayne',
                'improvements': [
                    'Handles missing Roman numeral markers (letters 50, 53)',
                    'Improved date extraction with multiple patterns',
                    'Better boundary detection (excludes appendix)',
                    'Enhanced recipient parsing'
                ]
            },
            'letters': letters
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(letters)} letters to {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Extract Dostoevsky letters (v3)')
    parser.add_argument('text_file', help='Plain text file')
    parser.add_argument('--output', default='letters_v3.json', help='Output JSON file')

    args = parser.parse_args()

    extractor = EnhancedLetterExtractor()
    letters = extractor.extract(args.text_file)

    # Print summary
    print(f"\n{'='*80}")
    print("EXTRACTION SUMMARY (v3)")
    print(f"{'='*80}")
    print(f"Total letters: {len(letters)}")

    with_dates = sum(1 for l in letters if l.get('date'))
    with_recipients = sum(1 for l in letters if l.get('recipient'))
    with_locations = sum(1 for l in letters if l.get('location'))

    print(f"With dates: {with_dates}")
    print(f"With recipients: {with_recipients}")
    print(f"With locations: {with_locations}")

    # Check for gaps in numbering
    letter_nums = sorted([l['number'] for l in letters])
    print(f"\nLetter numbers: {letter_nums[0]} to {letter_nums[-1]}")

    # Find missing numbers
    all_expected = set(range(1, 78))
    found = set(letter_nums)
    missing = sorted(all_expected - found)
    if missing:
        print(f"Missing letter numbers: {missing}")
    else:
        print("No gaps in letter numbering (1-77)")

    # Show first 10
    print(f"\nFirst 10 letters:")
    for letter in letters[:10]:
        rec = (letter.get('recipient') or 'Unknown')[:40]
        date = (letter.get('date') or 'No date')[:25]
        print(f"  {letter['number']:2d}. To {rec:<42} {date}")

    print(f"{'='*80}")

    # Save
    extractor.save_json(letters, args.output)


if __name__ == '__main__':
    main()
