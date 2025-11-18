#!/usr/bin/env python3
"""
Comprehensive verification of the extracted letter collection.
Checks for duplicates, quality issues, and validates all 275 letters.
"""

import re
import json
from collections import Counter
from pathlib import Path


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer."""
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    roman = roman.strip().upper().replace('l', 'I')
    total = prev = 0
    for char in reversed(roman):
        if char not in vals:
            return -1
        val = vals[char]
        total += val if val >= prev else -val
        prev = val
    return total


def validate_letter(letter: dict, index: int) -> list:
    """Validate a single letter and return list of issues."""
    issues = []

    # Check required fields
    if not letter.get('number'):
        issues.append(f"Missing 'number' field")
    if not letter.get('value'):
        issues.append(f"Missing 'value' field")

    # Check if value matches number
    if letter.get('number') and letter.get('value'):
        expected_value = roman_to_int(letter['number']) if letter['number'] != '1' else 1
        if expected_value != letter['value']:
            issues.append(f"Value mismatch: number={letter['number']}, value={letter['value']}, expected={expected_value}")

    # Check body content quality
    body = letter.get('body', '')
    if not body:
        issues.append("Empty body")
    elif len(body) < 50:
        issues.append(f"Very short body ({len(body)} chars)")

    # Check for obvious OCR corruption markers
    corruption_markers = [
        r'\.{10,}',  # Many dots in a row
        r'\s{20,}',  # Excessive spaces
        r'[^a-zA-Z0-9\s\.,;:!?\-\'"()[\]\/]{5,}',  # Garbage characters
    ]

    for pattern in corruption_markers:
        if re.search(pattern, body):
            issues.append(f"Possible OCR corruption (pattern: {pattern})")
            break

    # Check date format
    date = letter.get('date', '')
    if date and not re.search(r'\d{4}', date):
        issues.append(f"Date without year: '{date}'")

    return issues


def main():
    """Verify the complete letter collection."""
    print("="*80)
    print("Comprehensive Collection Verification")
    print("="*80)

    # Load collection
    with open("indian-letters/letters_complete.json") as f:
        letters = json.load(f)

    print(f"\nLoaded {len(letters)} letters")

    # Check 1: Duplicate values
    print("\n" + "="*80)
    print("Check 1: Duplicate Letter Numbers")
    print("="*80)

    values = [l['value'] for l in letters]
    value_counts = Counter(values)
    duplicates = {v: count for v, count in value_counts.items() if count > 1}

    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate letter numbers!")
        for value, count in sorted(duplicates.items()):
            print(f"  Letter #{value} appears {count} times")

            # Show the duplicates
            dup_letters = [l for l in letters if l['value'] == value]
            for i, dup in enumerate(dup_letters):
                print(f"    [{i+1}] {dup.get('location', 'Unknown')[:30]} - {dup.get('date', 'Unknown')[:20]}")
                print(f"        Body preview: {dup.get('body', '')[:80]}...")
    else:
        print("✓ No duplicates found - all 275 letters are unique")

    # Check 2: Sequence gaps
    print("\n" + "="*80)
    print("Check 2: Sequence Verification")
    print("="*80)

    values_sorted = sorted(values)
    expected_all = set(range(1, 294))
    found_all = set(values)
    missing_all = sorted(expected_all - found_all)

    print(f"Expected range: 1-293")
    print(f"Found: {len(found_all)} letters")
    print(f"Missing: {len(missing_all)} letters")

    if missing_all:
        def int_to_roman(num):
            vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
            syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
            result = ''
            for i, v in enumerate(vals):
                count, num = divmod(num, v)
                result += syms[i] * count
            return result

        missing_romans = [int_to_roman(n) if n > 1 else '1' for n in missing_all]
        print(f"\nMissing letters: {', '.join(missing_romans)}")

    # Check 3: Individual letter quality
    print("\n" + "="*80)
    print("Check 3: Individual Letter Quality")
    print("="*80)

    all_issues = {}
    for i, letter in enumerate(letters):
        issues = validate_letter(letter, i)
        if issues:
            all_issues[letter.get('value', i)] = issues

    if all_issues:
        print(f"⚠ Found quality issues in {len(all_issues)} letters:")
        for value, issues in sorted(all_issues.items())[:20]:  # Show first 20
            letter_num = next((l['number'] for l in letters if l.get('value') == value), value)
            print(f"\n  Letter {letter_num} (#{value}):")
            for issue in issues:
                print(f"    - {issue}")
    else:
        print("✓ All letters pass quality checks")

    # Check 4: Content statistics
    print("\n" + "="*80)
    print("Check 4: Content Statistics")
    print("="*80)

    body_lengths = [len(l.get('body', '')) for l in letters]
    avg_length = sum(body_lengths) / len(body_lengths)
    min_length = min(body_lengths)
    max_length = max(body_lengths)

    print(f"Body length statistics:")
    print(f"  Average: {avg_length:.0f} characters")
    print(f"  Minimum: {min_length} characters")
    print(f"  Maximum: {max_length} characters")

    # Find suspiciously short letters
    short_letters = [(l['value'], l['number'], len(l.get('body', ''))) for l in letters if len(l.get('body', '')) < 100]
    if short_letters:
        print(f"\n  Suspiciously short letters ({len(short_letters)}):")
        for value, number, length in sorted(short_letters)[:10]:
            print(f"    Letter {number} (#{value}): {length} chars")

    # Find suspiciously long letters
    long_letters = [(l['value'], l['number'], len(l.get('body', ''))) for l in letters if len(l.get('body', '')) > 5000]
    if long_letters:
        print(f"\n  Suspiciously long letters ({len(long_letters)}):")
        for value, number, length in sorted(long_letters, key=lambda x: -x[2])[:10]:
            print(f"    Letter {number} (#{value}): {length} chars")

    # Check 5: Date distribution
    print("\n" + "="*80)
    print("Check 5: Temporal Distribution")
    print("="*80)

    years = []
    for letter in letters:
        year_match = re.search(r'\b(19\d{2})\b', letter.get('date', ''))
        if year_match:
            years.append(int(year_match.group(1)))

    if years:
        year_counts = Counter(years)
        print(f"Letters by year ({len(year_counts)} years):")
        for year in sorted(year_counts.keys()):
            count = year_counts[year]
            bar = '█' * (count // 2)
            print(f"  {year}: {count:3d} {bar}")

    # Final summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"Total letters: {len(letters)}")
    print(f"Unique values: {len(set(values))}")
    print(f"Duplicates: {len(duplicates)}")
    print(f"Quality issues: {len(all_issues)}")
    print(f"Coverage: {len(found_all)}/293 ({len(found_all)/293*100:.1f}%)")

    if not duplicates and len(all_issues) < 10:
        print("\n✓ Collection is in EXCELLENT condition")
    elif not duplicates and len(all_issues) < 30:
        print("\n✓ Collection is in GOOD condition")
    else:
        print("\n⚠ Collection needs review")

    # Save report
    report = {
        'total_letters': len(letters),
        'unique_letters': len(set(values)),
        'duplicates': list(duplicates.keys()) if duplicates else [],
        'missing': missing_all,
        'quality_issues': {str(k): v for k, v in all_issues.items()},
        'stats': {
            'avg_length': avg_length,
            'min_length': min_length,
            'max_length': max_length,
            'short_letters': short_letters,
            'long_letters': long_letters
        }
    }

    with open("indian-letters/verification_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to verification_report.json")


if __name__ == "__main__":
    main()
