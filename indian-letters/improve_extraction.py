#!/usr/bin/env python3
"""
Improved extraction with OCR error correction.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set


def fix_roman_numeral_ocr(text: str) -> str:
    """Fix common OCR errors in Roman numerals."""
    # Common OCR errors:
    # - 'l' (lowercase L) instead of 'I'
    # - 'O' or '0' instead of nothing
    # - Extra characters

    corrections = {
        # Specific known errors
        'Ill': 'III',
        'lll': 'III',
        'll': 'II',
        'lI': 'II',
        'Il': 'II',
        'XLVIXX': 'XLVIII',
        'CXXVIXI': 'CXXVIII',
        'CXXXVIX': 'CXXXVII',
        'CCLVXI': 'CCLVII',
        'CCLXXXVXI': 'CCLXXXVII',
    }

    if text in corrections:
        return corrections[text]

    # Pattern-based corrections
    # Replace lowercase 'l' with 'I' if surrounded by Roman numeral characters
    if re.match(r'^[IVXLCDMl]+$', text):
        corrected = text.replace('l', 'I')
        if corrected != text:
            print(f"  Auto-corrected: {text} -> {corrected}")
            return corrected

    return text


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer."""
    roman_values = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }

    # Clean and fix OCR errors
    roman = fix_roman_numeral_ocr(roman.strip().upper())

    total = 0
    prev_value = 0

    for char in reversed(roman):
        if char not in roman_values:
            return -1
        value = roman_values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value

    return total


def int_to_roman(num: int) -> str:
    """Convert integer to Roman numeral."""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num


def find_all_letter_markers(text_content: str) -> List[Dict]:
    """Find all potential letter markers in the text."""
    lines = text_content.split('\n')
    markers = []

    # Find where letters start
    letter_start_idx = 0
    for i, line in enumerate(lines):
        if 'LETTERS  TO' in line and i+2 < len(lines) and 'SARDAR  VALLABHBHAI  PATEL' in lines[i+2]:
            letter_start_idx = i + 3
            break

    print(f"Searching for letter markers starting at line {letter_start_idx}")

    for i in range(letter_start_idx, len(lines)):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            continue

        # Check for Roman numerals (including OCR errors)
        if re.match(r'^[IVXLCDMl]+$', line):
            corrected = fix_roman_numeral_ocr(line)
            value = roman_to_int(corrected)
            if value > 0:
                markers.append({
                    'line': i,
                    'original': line,
                    'corrected': corrected,
                    'value': value,
                    'type': 'roman'
                })
                continue

        # Check for Arabic numeral (only "1" in right context)
        if line == "1" and i > letter_start_idx:
            # Check next few lines for date patterns
            next_text = " ".join(lines[i+1:i+6])
            if re.search(r'(Bombay|July|1921)', next_text):
                markers.append({
                    'line': i,
                    'original': line,
                    'corrected': line,
                    'value': 1,
                    'type': 'arabic'
                })

    return markers


def analyze_markers(markers: List[Dict]) -> Dict:
    """Analyze markers to find gaps and issues."""
    print(f"\nFound {len(markers)} letter markers")

    # Sort by value
    markers_sorted = sorted(markers, key=lambda x: x['value'])

    # Find gaps
    expected = set(range(1, markers_sorted[-1]['value'] + 1))
    found = set(m['value'] for m in markers_sorted)
    missing = expected - found

    # Find duplicates
    values = [m['value'] for m in markers_sorted]
    duplicates = set([x for x in values if values.count(x) > 1])

    print(f"Expected range: 1 to {markers_sorted[-1]['value']}")
    print(f"Found: {len(found)} unique letters")
    print(f"Missing: {len(missing)} letters")

    if missing:
        print(f"Missing letter numbers: {sorted(missing)[:20]}...")  # Show first 20

    if duplicates:
        print(f"Duplicate values found: {duplicates}")

    return {
        'total_markers': len(markers),
        'unique_letters': len(found),
        'expected_count': markers_sorted[-1]['value'],
        'missing_count': len(missing),
        'missing_numbers': sorted(missing),
        'duplicates': sorted(duplicates)
    }


def search_for_missing(text_content: str, missing_numbers: List[int]) -> Dict[int, List[int]]:
    """Search for missing letter numbers in the text."""
    lines = text_content.split('\n')
    found_missing = {}

    print(f"\nSearching for {len(missing_numbers)} missing letters...")

    for num in missing_numbers[:50]:  # Search for first 50 missing
        roman = int_to_roman(num)
        pattern = re.compile(r'\b' + roman + r'\b')

        for i, line in enumerate(lines):
            if pattern.search(line):
                if num not in found_missing:
                    found_missing[num] = []
                found_missing[num].append(i)

        # Also search for common OCR variants
        variants = [
            roman.replace('I', 'l'),  # lowercase L
            roman.replace('II', 'll'),
            roman.replace('III', 'Ill'),
        ]

        for variant in variants:
            if variant != roman:
                for i, line in enumerate(lines):
                    if variant in line:
                        if num not in found_missing:
                            found_missing[num] = []
                        if i not in found_missing[num]:
                            found_missing[num].append(i)

    print(f"Found potential locations for {len(found_missing)} missing letters")
    return found_missing


def main():
    """Main analysis."""
    print("="*80)
    print("Improved Letter Extraction - OCR Error Analysis")
    print("="*80)

    # Read text file
    text_file = Path("gandhi-patel-letters.txt")
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all markers
    markers = find_all_letter_markers(content)

    # Save markers for inspection
    with open("letter_markers.json", 'w') as f:
        json.dump(markers, f, indent=2)

    print(f"Saved markers to letter_markers.json")

    # Analyze gaps
    analysis = analyze_markers(markers)

    # Search for missing letters
    if analysis['missing_numbers']:
        found_missing = search_for_missing(content, analysis['missing_numbers'])

        # Show some results
        print("\nSample missing letter locations:")
        for num in sorted(found_missing.keys())[:10]:
            print(f"  {int_to_roman(num)} (#{num}): found at lines {found_missing[num]}")

        # Save results
        with open("missing_letters_search.json", 'w') as f:
            json.dump({
                'analysis': analysis,
                'found_locations': {int_to_roman(k): v for k, v in found_missing.items()}
            }, f, indent=2)

        print("\nSaved analysis to missing_letters_search.json")


if __name__ == "__main__":
    main()
