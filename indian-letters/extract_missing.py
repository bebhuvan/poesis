#!/usr/bin/env python3
"""
Aggressive extraction of missing letters.
Searches for specific letter numbers and extracts them even with OCR errors.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer."""
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

    # OCR corrections
    ocr_fixes = {
        'Ill': 'III', 'lll': 'III', 'll': 'II', 'lI': 'II', 'Il': 'II',
        'Cl': 'CI', 'XLVIXX': 'XLVIII', 'CXXVIXI': 'CXXVIII',
        'CXXXVIX': 'CXXXVII', 'CCLVXI': 'CCLVII', 'CCLXXXVXI': 'CCLXXXVII',
    }

    roman = roman.strip().upper()
    if roman in ocr_fixes:
        roman = ocr_fixes[roman]

    # Auto-fix lowercase 'l' to 'I'
    if re.match(r'^[IVXLCDMl]+$', roman):
        roman = roman.replace('l', 'I')

    total = prev = 0
    for char in reversed(roman):
        if char not in vals:
            return -1
        val = vals[char]
        total += val if val >= prev else -val
        prev = val
    return total


def int_to_roman(num: int) -> str:
    """Convert integer to Roman numeral."""
    vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    result = ''
    for i, v in enumerate(vals):
        count, num = divmod(num, v)
        result += syms[i] * count
    return result


def find_letter_locations(lines: List[str], letter_num: int) -> List[Dict]:
    """Find all potential locations for a specific letter number."""
    roman = int_to_roman(letter_num)
    locations = []

    # Generate variations for OCR errors
    variations = [
        roman,
        "'" + roman,  # Leading quote
        roman + " ",  # Trailing space
        "'" + roman + " ",  # Both
    ]

    # Add variations with common OCR noise
    for var in list(variations):
        variations.append(var + " I")  # Roman followed by "I"
        variations.append(var + " II")

    # Search for letter markers
    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Exact match with variations
        for var in variations:
            if line_stripped == var or line_stripped.startswith(var):
                # Check context
                context = ' '.join(lines[i+1:i+6]) if i+5 < len(lines) else ''
                has_date = bool(re.search(r'\d{4}|January|February|March|April|May|June|July|August|September|October|November|December', context))
                has_location = bool(re.search(r'Bombay|Delhi|Wardha|Sabarmati|London|Calcutta|Ahmedabad|Segaon|Poona|Parnakuti', context, re.I))

                confidence = 0
                if line_stripped == roman:
                    confidence = 10
                elif var in line_stripped:
                    confidence = 8

                if has_date:
                    confidence += 3
                if has_location:
                    confidence += 2

                if confidence >= 8:
                    locations.append({
                        'line': i,
                        'text': line_stripped,
                        'confidence': confidence,
                        'context': context[:150]
                    })
                    break

        # Regex search for the pattern
        if roman in line:
            pattern = r'\b' + roman + r'\b'
            if re.search(pattern, line):
                context = ' '.join(lines[i+1:i+6]) if i+5 < len(lines) else ''
                has_date = bool(re.search(r'\d{4}', context))

                if has_date:
                    locations.append({
                        'line': i,
                        'text': line.strip(),
                        'confidence': 7,
                        'context': context[:150]
                    })

    # Sort by confidence and deduplicate
    locations.sort(key=lambda x: -x['confidence'])

    # Remove duplicates (lines close together)
    unique_locations = []
    seen_lines = set()
    for loc in locations:
        if not any(abs(loc['line'] - s) <= 2 for s in seen_lines):
            unique_locations.append(loc)
            seen_lines.add(loc['line'])

    return unique_locations


def extract_letter_at_line(lines: List[str], start_line: int, letter_num: int, end_line: Optional[int] = None) -> Optional[Dict]:
    """Extract letter content starting at a specific line."""
    if end_line is None:
        end_line = len(lines)

    i = start_line + 1  # Skip the marker line

    # Extract location
    location = ""
    while i < end_line and not lines[i].strip():
        i += 1
    if i < end_line:
        loc = lines[i].strip()
        if loc and not re.match(r'^\[?\d{4}\]?$', loc) and 'LETTERS TO SARDAR' not in loc:
            location = loc
            i += 1

    # Extract date
    date = ""
    while i < end_line and not lines[i].strip():
        i += 1
    if i < end_line:
        date_text = lines[i].strip()
        if date_text and 'LETTERS TO SARDAR' not in date_text:
            date = date_text
            i += 1

    # Extract salutation
    salutation = ""
    while i < end_line and not lines[i].strip():
        i += 1
    if i < end_line:
        sal = lines[i].strip()
        if sal and any(x in sal for x in ['Bhai', 'Chi.', 'Mani,']):
            salutation = sal
            i += 1

    # Extract body
    body_lines = []
    lines_read = 0
    max_lines = 200  # Safety limit

    while i < end_line and lines_read < max_lines:
        line = lines[i].strip()

        # Stop if we hit another letter marker (Roman numeral on its own line)
        if re.match(r'^[IVXLCDM]+$', line) and roman_to_int(line) > 0:
            next_num = roman_to_int(line)
            if next_num == letter_num + 1 or (next_num > letter_num and next_num < letter_num + 5):
                break

        # Skip page numbers, headers, footnotes
        if (re.match(r'^\d+$', line) or
            'LETTERS TO SARDAR' in line or
            re.match(r'^[\*†‡§%]\s+', line)):
            i += 1
            lines_read += 1
            continue

        if line:
            body_lines.append(line)

        i += 1
        lines_read += 1

    # Find closing
    closing = ""
    if body_lines:
        last = body_lines[-1]
        if any(x in last.lower() for x in ['bapu', 'mohandas', 'vande mataram', 'blessings']):
            closing = body_lines.pop()

    # Clean up body
    body = '\n\n'.join([line for line in body_lines if line])

    # Validate we got something reasonable
    if not body or len(body) < 20:
        return None

    return {
        'number': int_to_roman(letter_num),
        'value': letter_num,
        'location': location,
        'date': date,
        'salutation': salutation,
        'body': body,
        'closing': closing,
        'source_lines': (start_line, i)
    }


def main():
    """Extract all missing letters."""
    print("="*80)
    print("Extracting Missing Letters")
    print("="*80)

    # Load missing letters list
    with open("output/extraction_report.json") as f:
        report = json.load(f)

    missing_romans = report['missing_letters']
    missing_numbers = [roman_to_int(r) for r in missing_romans]

    print(f"\nSearching for {len(missing_numbers)} missing letters...")

    # Load source text
    with open("gandhi-patel-letters.txt") as f:
        lines = f.readlines()

    # Load already extracted letters
    with open("letters_production.json") as f:
        existing_letters = json.load(f)

    existing_values = set(l['value'] for l in existing_letters)

    # Extract missing letters
    newly_extracted = []

    for num in missing_numbers:
        print(f"\nSearching for Letter {int_to_roman(num)} (#{num})...")

        # Find potential locations
        locations = find_letter_locations(lines, num)

        if not locations:
            print(f"  ❌ Not found")
            continue

        print(f"  Found {len(locations)} potential location(s)")

        # Try to extract from the best location
        best_location = locations[0]
        print(f"  Best match at line {best_location['line']} (confidence: {best_location['confidence']})")
        print(f"  Context: {best_location['context'][:80]}...")

        # Try extraction
        letter = extract_letter_at_line(lines, best_location['line'], num)

        if letter:
            newly_extracted.append(letter)
            print(f"  ✓ Extracted successfully ({len(letter['body'])} chars)")
        else:
            print(f"  ⚠ Found but extraction failed")

    print(f"\n{'='*80}")
    print(f"Successfully extracted {len(newly_extracted)} new letters!")
    print(f"{'='*80}")

    # Combine with existing letters
    all_letters = existing_letters + newly_extracted
    all_letters.sort(key=lambda x: x['value'])

    # Save combined collection
    with open("letters_complete.json", 'w', encoding='utf-8') as f:
        json.dump(all_letters, f, indent=2, ensure_ascii=False)

    print(f"\nTotal letters: {len(all_letters)} of 293")
    print(f"Coverage: {len(all_letters)/293*100:.1f}%")

    # Show what's still missing
    extracted_values = set(l['value'] for l in all_letters)
    still_missing = sorted(set(range(1, 294)) - extracted_values)

    if still_missing:
        print(f"\nStill missing {len(still_missing)} letters:")
        print(f"  {', '.join(int_to_roman(n) for n in still_missing[:20])}...")
    else:
        print("\n🎉 ALL LETTERS EXTRACTED!")

    # Save newly extracted letters separately for review
    with open("newly_extracted.json", 'w', encoding='utf-8') as f:
        json.dump(newly_extracted, f, indent=2, ensure_ascii=False)

    print(f"\nSaved:")
    print(f"  - letters_complete.json ({len(all_letters)} letters)")
    print(f"  - newly_extracted.json ({len(newly_extracted)} new letters)")


if __name__ == "__main__":
    main()
