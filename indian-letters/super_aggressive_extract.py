#!/usr/bin/env python3
"""
Super aggressive extraction for the final 56 missing letters.
Uses multiple strategies including hOCR parsing and fuzzy matching.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer."""
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

    # Clean up
    roman = roman.strip().upper()
    roman = roman.replace('l', 'I')  # lowercase L to I

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


def find_letter_in_range(lines: List[str], target_num: int, start: int, end: int) -> Optional[Dict]:
    """
    Look for a specific letter number within a line range.
    This is useful when we know roughly where a letter should be.
    """
    target_roman = int_to_roman(target_num)

    # Look for the pattern in the specified range
    for i in range(start, min(end, len(lines))):
        line = lines[i].strip()

        # Check if this line contains the target Roman numeral
        # Allow for some OCR noise
        if target_roman in line or target_roman.lower() in line.lower():
            # Check if it's likely a letter marker
            context = ' '.join(lines[i+1:i+6]) if i+5 < len(lines) else ''

            # Look for date/location markers
            has_date = bool(re.search(r'\d{4}', context))
            has_location = bool(re.search(r'(Bombay|Delhi|Wardha|Sabarmati|London|Calcutta|Ahmedabad|Segaon|Poona)', context, re.I))

            if has_date or has_location:
                return {
                    'line': i,
                    'text': line,
                    'confidence': 8,
                    'method': 'range_search'
                }

    return None


def search_between_neighbors(lines: List[str], target_num: int, prev_num: int, next_num: int,
                              prev_line: int, next_line: int) -> Optional[Dict]:
    """
    Search for a letter between its neighbors.
    E.g., if letter 48 is missing but we have 47 and 50, search between them.
    """
    target_roman = int_to_roman(target_num)

    # Search in the range between previous and next letter
    search_start = prev_line + 10  # Skip some lines after previous letter
    search_end = next_line - 5     # Stop before next letter

    if search_start >= search_end:
        return None

    print(f"  Searching between letters {prev_num} (line {prev_line}) and {next_num} (line {next_line})")

    return find_letter_in_range(lines, target_num, search_start, search_end)


def fuzzy_search_letter(lines: List[str], target_num: int) -> List[Dict]:
    """
    Very fuzzy search - look for anything that might be this letter.
    """
    target_roman = int_to_roman(target_num)
    locations = []

    # Generate fuzzy patterns
    patterns = [
        target_roman,
        target_roman.replace('I', '[Il1]'),  # I could be l or 1
        target_roman.replace('V', '[Vv]'),
        target_roman.replace('X', '[Xx]'),
    ]

    # Also try with spaces
    spaced_roman = ' '.join(target_roman)
    patterns.append(spaced_roman)

    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line, re.I):
                # Found a match
                context = ' '.join(lines[i+1:i+6]) if i+5 < len(lines) else ''
                has_date = bool(re.search(r'\d{4}', context))

                locations.append({
                    'line': i,
                    'text': line.strip(),
                    'confidence': 5 + (3 if has_date else 0),
                    'method': 'fuzzy',
                    'pattern': pattern
                })
                break

    return locations


def extract_letter_content(lines: List[str], start_line: int, letter_num: int) -> Optional[Dict]:
    """Extract letter content starting at a specific line."""
    i = start_line + 1

    # Extract location
    location = ""
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines):
        loc = lines[i].strip()
        if loc and not re.match(r'^\[?\d{4}\]?$', loc) and 'LETTERS TO SARDAR' not in loc:
            location = loc
            i += 1

    # Extract date
    date = ""
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines):
        date_text = lines[i].strip()
        if date_text and 'LETTERS TO SARDAR' not in date_text:
            date = date_text
            i += 1

    # Extract salutation
    salutation = ""
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines):
        sal = lines[i].strip()
        if sal and any(x in sal for x in ['Bhai', 'Chi.', 'Mani,']):
            salutation = sal
            i += 1

    # Extract body
    body_lines = []
    max_lines = 300
    lines_read = 0

    while i < len(lines) and lines_read < max_lines:
        line = lines[i].strip()

        # Stop if we hit a clear next letter marker
        if re.match(r'^[IVXLCDM]+$', line):
            next_num = roman_to_int(line)
            if next_num > 0 and next_num > letter_num:
                break

        # Skip headers/footers/page numbers
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

    # Extract closing
    closing = ""
    if body_lines:
        last = body_lines[-1]
        if any(x in last.lower() for x in ['bapu', 'mohandas', 'vande mataram', 'blessings']):
            closing = body_lines.pop()

    body = '\n\n'.join([line for line in body_lines if line])

    # Validate
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
    """Super aggressive extraction of final missing letters."""
    print("="*80)
    print("Super Aggressive Extraction - Final 56 Letters")
    print("="*80)

    # Load missing letters
    with open("indian-letters/output/extraction_report.json") as f:
        report = json.load(f)

    missing_romans = report['missing_letters']
    missing_numbers = [roman_to_int(r) for r in missing_romans]

    print(f"\nTargeting {len(missing_numbers)} missing letters")
    print(f"Numbers: {missing_numbers[:20]}...")

    # Load source text
    with open("indian-letters/gandhi-patel-letters.txt") as f:
        lines = f.readlines()

    # Load already extracted letters to find gaps
    with open("indian-letters/letters_complete.json") as f:
        existing_letters = json.load(f)

    # Build a map of existing letters
    existing_map = {l['value']: l['source_lines'] for l in existing_letters if 'source_lines' in l}

    # Try to extract missing letters
    newly_found = []

    for target_num in missing_numbers:
        print(f"\n{'='*60}")
        print(f"Searching for Letter {int_to_roman(target_num)} (#{target_num})")
        print(f"{'='*60}")

        # Strategy 1: Search between neighbors
        prev_num = target_num - 1
        next_num = target_num + 1

        # Find the closest existing letters before and after
        while prev_num > 0 and prev_num not in existing_map:
            prev_num -= 1
        while next_num <= 293 and next_num not in existing_map:
            next_num += 1

        if prev_num in existing_map and next_num in existing_map:
            prev_line = existing_map[prev_num][1]  # End line of previous letter
            next_line = existing_map[next_num][0]  # Start line of next letter

            result = search_between_neighbors(lines, target_num, prev_num, next_num, prev_line, next_line)

            if result:
                print(f"  ✓ Found via neighbor search at line {result['line']}")
                print(f"    Text: {result['text'][:60]}")

                # Try to extract
                letter = extract_letter_content(lines, result['line'], target_num)
                if letter:
                    newly_found.append(letter)
                    print(f"  ✓ EXTRACTED ({len(letter['body'])} chars)")
                    continue

        # Strategy 2: Fuzzy search
        print(f"  Trying fuzzy search...")
        fuzzy_results = fuzzy_search_letter(lines, target_num)

        if fuzzy_results:
            print(f"  Found {len(fuzzy_results)} fuzzy matches")
            # Try the best one
            best = fuzzy_results[0]
            print(f"    Best: line {best['line']} - {best['text'][:60]}")

            letter = extract_letter_content(lines, best['line'], target_num)
            if letter:
                newly_found.append(letter)
                print(f"  ✓ EXTRACTED via fuzzy ({len(letter['body'])} chars)")
                continue

        print(f"  ❌ Not found")

    print(f"\n{'='*80}")
    print(f"Super Aggressive Extraction Complete")
    print(f"{'='*80}")
    print(f"\nNewly found: {len(newly_found)} letters")

    if newly_found:
        # Combine with existing
        all_letters = existing_letters + newly_found
        all_letters.sort(key=lambda x: x['value'])

        # Save
        with open("indian-letters/letters_complete.json", 'w', encoding='utf-8') as f:
            json.dump(all_letters, f, indent=2, ensure_ascii=False)

        with open("indian-letters/super_aggressive_new.json", 'w', encoding='utf-8') as f:
            json.dump(newly_found, f, indent=2, ensure_ascii=False)

        print(f"\nTotal letters now: {len(all_letters)} of 293")
        print(f"Coverage: {len(all_letters)/293*100:.1f}%")
        print(f"\nStill missing: {293 - len(all_letters)} letters")

        # Show which ones we got
        print(f"\nNewly extracted letters:")
        for letter in newly_found[:20]:
            print(f"  - {letter['number']}: {letter['location']} ({letter['date']})")
    else:
        print("\nNo new letters found with super aggressive search")
        print("Remaining letters likely have severe OCR corruption or are genuinely missing from source")


if __name__ == "__main__":
    main()
