#!/usr/bin/env python3
"""
Clean up the collection by removing false positives and verifying quality.
"""

import json


def is_false_positive(letter):
    """Determine if a letter is a false positive extraction."""
    # Check if source lines are from front matter (before line 280)
    if 'source_lines' in letter:
        start_line = letter['source_lines'][0]
        if start_line < 280:  # Before actual letters start
            return True

    # Check for TOC-like content in location/date
    location = letter.get('location', '')
    date = letter.get('date', '')

    toc_markers = [
        'Village Industries Association',
        'Borsad plague',
        'nature cure in',
        'Goa in',
        'Noakhali',
        'Bihar disturbances',
        'LETTERS TO SARDAR',
        'in GXLVII',
        'et seq',
    ]

    for marker in toc_markers:
        if marker in location or marker in date:
            return True

    # Check for extremely corrupted body content
    body = letter.get('body', '')
    if 'LETTERS TO SARDAR PATEL' in body[:500]:
        return True

    return False


def main():
    """Clean up the collection."""
    print("="*80)
    print("Collection Cleanup")
    print("="*80)

    # Load collection
    with open("indian-letters/letters_complete.json") as f:
        letters = json.load(f)

    print(f"\nOriginal: {len(letters)} letters")

    # Identify false positives
    false_positives = []
    clean_letters = []

    for letter in letters:
        if is_false_positive(letter):
            false_positives.append(letter)
            print(f"  Removing Letter {letter['number']} (#{letter['value']}) - False positive")
            print(f"    Location: {letter.get('location', '')[:60]}")
            print(f"    Source lines: {letter.get('source_lines', 'Unknown')}")
        else:
            clean_letters.append(letter)

    print(f"\nRemoved: {len(false_positives)} false positives")
    print(f"Remaining: {len(clean_letters)} letters")

    # Sort by value
    clean_letters.sort(key=lambda x: x['value'])

    # Save cleaned collection
    with open("indian-letters/letters_complete.json", 'w', encoding='utf-8') as f:
        json.dump(clean_letters, f, indent=2, ensure_ascii=False)

    # Save false positives for reference
    if false_positives:
        with open("indian-letters/false_positives.json", 'w', encoding='utf-8') as f:
            json.dump(false_positives, f, indent=2, ensure_ascii=False)

    # Update extraction report
    values = [l['value'] for l in clean_letters]
    all_nums = set(range(1, 294))
    found = set(values)
    missing = sorted(all_nums - found)

    def int_to_roman(num):
        vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        result = ''
        for i, v in enumerate(vals):
            count, num = divmod(num, v)
            result += syms[i] * count
        return result

    print(f"\nFinal statistics:")
    print(f"  Total: {len(clean_letters)} letters")
    print(f"  Coverage: {len(found)}/293 ({len(found)/293*100:.1f}%)")
    print(f"  Missing: {len(missing)} letters")

    if missing:
        missing_romans = [int_to_roman(n) if n > 1 else '1' for n in missing]
        print(f"\nMissing letters: {', '.join(missing_romans[:30])}")
        if len(missing) > 30:
            print(f"  ... and {len(missing) - 30} more")

    print("\n✓ Collection cleaned and saved")


if __name__ == "__main__":
    main()
