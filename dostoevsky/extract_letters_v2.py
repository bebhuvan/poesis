#!/usr/bin/env python3
"""
Improved letter extractor using Roman numerals as boundaries.

Structure observed:
- First letter has no Roman numeral
- Letters 2-N start with Roman numeral (II, III, IV, etc.)
- Format:
    [ROMAN]

    To [recipient]

    [Location], [Date]

    [Letter body]
"""

import re
import json
from pathlib import Path
from datetime import datetime

class ImprovedLetterExtractor:
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
        """Extract all letters using Roman numeral boundaries"""
        print(f"Reading {text_file}...")

        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # Find start of letters
        letters_start = text.find("MY  DEAR  GOOD  FATHER")
        if letters_start == -1:
            print("Could not find start of letters!")
            return []

        # Back up to find first letter header
        header_start = text.rfind("To  his  Father", max(0, letters_start - 500), letters_start)
        if header_start == -1:
            header_start = letters_start

        letters_text = text[header_start:]

        # Split by Roman numerals
        # Pattern: newline, optional whitespace, Roman numeral on its own line
        pattern = r'\n\s*\n\s*([IVXL]+)\s*\n'

        parts = re.split(pattern, letters_text)

        print(f"Split into {len(parts)} parts")

        # First part is Letter 1 (no Roman numeral)
        letters = []

        # Process first letter
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

        print(f"Extracted {len(letters)} letters")

        return letters

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
            to_match = re.search(r'^To\s+([^\n]+)', line.strip())
            if to_match:
                recipient = to_match.group(1).strip()
                # Clean up
                recipient = re.sub(r'\s+', ' ', recipient)
                letter['recipient'] = recipient

                # Look for date/location in next few lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    check_line = lines[j].strip()

                    if not check_line:
                        continue

                    # Try to extract date
                    date = self._parse_date(check_line)
                    if date:
                        letter['date'] = date

                    # Check if it's a location (all caps, ends with comma)
                    if check_line.isupper() and check_line.endswith(','):
                        letter['location'] = check_line.rstrip(',').strip()

                    # If we see all caps salutation, body is starting
                    if check_line.isupper() and len(check_line.split()) > 2:
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
                        body_start_line = i + 2

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

            # Check for footnote markers
            if re.match(r'^\d+\s+[A-Z]', line) and len(line) < 150:
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
        """Extract date from text"""
        # Pattern: "August  9,  1838." or "May  10,  1838" (note: double spaces in OCR)
        # Also handles formats like "i," for "1,"
        match = re.search(r'([A-Z][a-z]+\s+[0-9i]{1,2}(?:,\s+|\s+)\d{4})', text)
        if match:
            date = match.group(1).strip()
            # Clean up double spaces and fix OCR errors
            date = re.sub(r'\s+', ' ', date)
            # Fix common OCR: "i," -> "1,"
            date = re.sub(r'\bi\b', '1', date)
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
                'extractor_version': 2,
                'source': 'Letters of Fyodor Michailovitch Dostoevsky (1917)',
                'translator': 'Ethel Colburn Mayne'
            },
            'letters': letters
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(letters)} letters to {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Extract Dostoevsky letters (v2)')
    parser.add_argument('text_file', help='Plain text file')
    parser.add_argument('--output', default='letters_v2.json', help='Output JSON file')

    args = parser.parse_args()

    extractor = ImprovedLetterExtractor()
    letters = extractor.extract(args.text_file)

    # Print summary
    print(f"\n{'='*80}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*80}")
    print(f"Total letters: {len(letters)}")

    with_dates = sum(1 for l in letters if l.get('date'))
    with_recipients = sum(1 for l in letters if l.get('recipient'))
    with_locations = sum(1 for l in letters if l.get('location'))

    print(f"With dates: {with_dates}")
    print(f"With recipients: {with_recipients}")
    print(f"With locations: {with_locations}")

    # Show first few
    print(f"\nFirst 10 letters:")
    for letter in letters[:10]:
        rec = (letter.get('recipient') or 'Unknown')[:40]
        date = (letter.get('date') or 'No date')[:20]
        print(f"  {letter['number']:2d}. To {rec:<42} {date}")

    print(f"{'='*80}")

    # Save
    extractor.save_json(letters, args.output)


if __name__ == '__main__':
    main()
