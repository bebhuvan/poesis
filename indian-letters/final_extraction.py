#!/usr/bin/env python3
"""
Final comprehensive letter extraction with maximum accuracy.
Multi-pass approach to handle all OCR errors and edge cases.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


# OCR error corrections
ROMAN_OCR_FIXES = {
    'Ill': 'III',
    'lll': 'III',
    'll': 'II',
    'lI': 'II',
    'Il': 'II',
    'Cl': 'CI',
    'XLVIXX': 'XLVIII',
    'CXXVIXI': 'CXXVIII',
    'CXXXVIX': 'CXXXVII',
    'CCLVXI': 'CCLVII',
    'CCLXXXVXI': 'CCLXXXVII',
}


def fix_roman_ocr(text: str) -> str:
    """Fix OCR errors in Roman numerals."""
    text = text.strip()

    if text in ROMAN_OCR_FIXES:
        return ROMAN_OCR_FIXES[text]

    # Auto-fix lowercase 'l' to 'I' in Roman context
    if re.match(r'^[IVXLCDMl]+$', text):
        fixed = text.replace('l', 'I')
        if fixed != text:
            return fixed

    return text


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer, returning -1 for invalid."""
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    roman = fix_roman_ocr(roman.upper())

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
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num


def extract_roman_from_line(line: str) -> Optional[Tuple[str, int]]:
    """
    Extract Roman numeral from a line that may have OCR artifacts.
    Returns (roman_text, value) or None.
    """
    line = line.strip()

    # Try exact match first
    if re.match(r'^[IVXLCDMl]+$', line):
        val = roman_to_int(line)
        if val > 0:
            return (fix_roman_ocr(line.upper()), val)

    # Try with leading/trailing junk - match Roman in middle
    # Pattern: optional junk, then Roman numeral, then optional junk
    match = re.search(r'\b([IVXLCDMl]{1,10})\b', line)
    if match:
        roman_candidate = match.group(1)
        # Only accept if it's a plausible Roman numeral
        val = roman_to_int(roman_candidate)
        if val > 0 and val <= 300:  # Letters shouldn't exceed ~293
            return (fix_roman_ocr(roman_candidate.upper()), val)

    return None


def find_letter_boundaries(lines: List[str]) -> List[Dict]:
    """
    Find all letter boundaries with multiple detection strategies.
    """
    markers = []
    letter_start_line = 0

    # Find where letters start
    for i, line in enumerate(lines):
        if 'LETTERS  TO' in line and i+2 < len(lines) and 'SARDAR  VALLABHBHAI  PATEL' in lines[i+2]:
            letter_start_line = i + 3
            break

    print(f"Letters content starts at line {letter_start_line}")

    # Strategy 1: Find all Roman numeral patterns
    for i in range(letter_start_line, len(lines)):
        line = lines[i]

        # Try to extract Roman numeral
        result = extract_roman_from_line(line)
        if result:
            roman, value = result
            markers.append({
                'line_num': i,
                'original_line': line.strip(),
                'letter_number': roman,
                'letter_value': value,
                'confidence': 'high' if line.strip() == roman else 'medium'
            })

        # Also check for letter #1 (Arabic)
        if line.strip() == "1" and i == 284:  # Known position of first letter
            markers.append({
                'line_num': i,
                'original_line': line.strip(),
                'letter_number': '1',
                'letter_value': 1,
                'confidence': 'high'
            })

    # Remove duplicates (same line) and sort by line number
    seen_lines = set()
    unique_markers = []
    for m in markers:
        if m['line_num'] not in seen_lines:
            seen_lines.add(m['line_num'])
            unique_markers.append(m)

    unique_markers.sort(key=lambda x: x['line_num'])

    print(f"Found {len(unique_markers)} letter boundary markers")

    return unique_markers


def extract_letter_content(lines: List[str], start_marker: Dict, end_line: Optional[int]) -> Dict:
    """
    Extract the content of a letter between markers.
    """
    start_line = start_marker['line_num']
    if end_line is None:
        end_line = len(lines)

    # Skip the number line itself
    i = start_line + 1

    # Extract location (usually next 1-2 non-empty lines)
    location = ""
    date = ""

    while i < end_line and not lines[i].strip():
        i += 1

    if i < end_line:
        potential_loc = lines[i].strip()
        # Filter out obvious non-locations
        if potential_loc and not re.match(r'^\[?\d{4}\]?$', potential_loc):
            location = potential_loc
            i += 1

    while i < end_line and not lines[i].strip():
        i += 1

    if i < end_line:
        potential_date = lines[i].strip()
        if potential_date:
            date = potential_date
            i += 1

    # Skip empty lines
    while i < end_line and not lines[i].strip():
        i += 1

    # Extract salutation (if exists)
    salutation = ""
    if i < end_line:
        line = lines[i].strip()
        if 'Bhai' in line or 'Chi.' in line or (line and line.endswith(',')):
            salutation = line
            i += 1

    # Extract body until end marker
    body_lines = []
    while i < end_line:
        line = lines[i]
        stripped = line.strip()

        # Skip footnote markers (lines starting with *, †, etc.)
        if re.match(r'^[\*†‡§%]\s+', stripped):
            i += 1
            continue

        # Skip obvious page numbers and headers
        if stripped and not re.match(r'^\d+$', stripped) and 'LETTERS  TO  SARDAR' not in stripped:
            body_lines.append(stripped)

        i += 1

    # Find closing (usually last line)
    closing = ""
    if body_lines:
        last_line = body_lines[-1]
        if any(pattern in last_line.lower() for pattern in ['bapu', 'mohandas', 'vande mataram', 'blessings']):
            closing = body_lines.pop()
            # Remove trailing empty lines
            while body_lines and not body_lines[-1]:
                body_lines.pop()

    return {
        'number': start_marker['letter_number'],
        'value': start_marker['letter_value'],
        'location': location,
        'date': date,
        'salutation': salutation,
        'body': '\n\n'.join([line for line in body_lines if line]),  # Double newline for paragraphs
        'closing': closing,
        'line_start': start_line,
        'line_end': end_line,
        'confidence': start_marker['confidence']
    }


def main():
    """Main extraction."""
    print("="*80)
    print("Final Comprehensive Letter Extraction")
    print("="*80)

    # Read text
    with open("gandhi-patel-letters.txt", 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    print(f"Total lines: {len(lines)}")

    # Find letter boundaries
    print("\n" + "="*80)
    print("Finding letter boundaries...")
    print("="*80)
    markers = find_letter_boundaries(lines)

    # Show statistics
    values = [m['letter_value'] for m in markers]
    unique_values = sorted(set(values))
    print(f"\nUnique letter numbers found: {len(unique_values)}")
    print(f"Range: {min(values)} to {max(values)}")

    # Find missing
    expected = set(range(1, max(values) + 1))
    found = set(values)
    missing = sorted(expected - found)
    print(f"Missing {len(missing)} letters: {missing[:30]}...")

    # Find duplicates
    duplicates = [v for v in set(values) if values.count(v) > 1]
    if duplicates:
        print(f"\nWARNING: Duplicate letter numbers found: {sorted(duplicates)}")
        # Keep only first occurrence of duplicates
        seen_values = set()
        filtered_markers = []
        for m in markers:
            if m['letter_value'] not in seen_values:
                seen_values.add(m['letter_value'])
                filtered_markers.append(m)
            else:
                print(f"  Skipping duplicate {m['letter_number']} at line {m['line_num']}")
        markers = filtered_markers
        print(f"After removing duplicates: {len(markers)} markers")

    # Extract letter content
    print("\n" + "="*80)
    print("Extracting letter content...")
    print("="*80)

    letters = []
    for i, marker in enumerate(markers):
        end_line = markers[i+1]['line_num'] if i+1 < len(markers) else None
        letter = extract_letter_content(lines, marker, end_line)
        letters.append(letter)

        # Show progress
        if i % 50 == 0:
            print(f"Extracted {i} letters...")

    print(f"\nTotal letters extracted: {len(letters)}")

    # Save results
    output_file = "letters_final.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(letters, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {output_file}")

    # Show sample
    print("\n" + "="*80)
    print("Sample letters:")
    print("="*80)

    for letter in letters[:3]:
        print(f"\n--- Letter {letter['number']} ---")
        print(f"Location: {letter['location']}")
        print(f"Date: {letter['date']}")
        print(f"Body preview: {letter['body'][:150]}...")

    # Generate summary report
    report = {
        'total_extracted': len(letters),
        'expected_total': max(values),
        'missing_letters': missing,
        'year_distribution': {},
    }

    # Count by year
    for letter in letters:
        year_match = re.search(r'\d{4}', letter['date'])
        if year_match:
            year = year_match.group()
            report['year_distribution'][year] = report['year_distribution'].get(year, 0) + 1

    with open("extraction_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*80)
    print("Extraction Summary:")
    print("="*80)
    print(f"Extracted: {report['total_extracted']} letters")
    print(f"Expected: {report['expected_total']} letters")
    print(f"Missing: {len(missing)} letters")
    print(f"\nSaved report to extraction_report.json")


if __name__ == "__main__":
    main()
