#!/usr/bin/env python3
"""
Find missing letters through aggressive pattern matching and context analysis.
"""

import re
import json
from pathlib import Path


def int_to_roman(num):
    """Convert integer to Roman numeral."""
    vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    result = ''
    for i, v in enumerate(vals):
        count, num = divmod(num, v)
        result += syms[i] * count
    return result


def find_letter_aggressive(lines, letter_num, start_line=280, end_line=10635):
    """
    Aggressively search for a specific letter number.
    Returns list of potential line numbers.
    """
    roman = int_to_roman(letter_num)
    found_lines = []

    # Search patterns (in order of reliability)
    patterns = [
        # Exact match on own line
        (rf'^\s*{roman}\s*$', 10),
        # With slight OCR noise
        (rf'^\s*[\'\"]?{roman}[\'\"]?\s*$', 9),
        # Word boundary
        (rf'\b{roman}\b', 8),
        # Common OCR variants
        (rf'\b{roman.replace("I", "[Il]")}\b', 7),
    ]

    for i in range(start_line, min(end_line, len(lines))):
        line = lines[i]

        for pattern, confidence in patterns:
            if re.search(pattern, line):
                # Check context - should look like a letter start
                context_score = 0

                # Check next few lines for date/location indicators
                next_lines = ' '.join(lines[i+1:i+6]) if i+5 < len(lines) else ''

                if re.search(r'\d{4}', next_lines):  # Year
                    context_score += 3
                if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', next_lines):
                    context_score += 2
                if re.search(r'(Bombay|Delhi|Wardha|Sabarmati|London|Calcutta|Ahmedabad)', next_lines):
                    context_score += 2

                if context_score > 0 or confidence >= 9:
                    found_lines.append({
                        'line': i,
                        'text': line.strip(),
                        'confidence': confidence + context_score,
                        'context': next_lines[:100]
                    })
                    break

    # Sort by confidence and remove duplicates
    found_lines.sort(key=lambda x: -x['confidence'])

    # Remove duplicates (same line or very close lines)
    unique = []
    seen_lines = set()
    for item in found_lines:
        if item['line'] not in seen_lines:
            # Also skip if within 3 lines of an already found one
            if not any(abs(item['line'] - s) <= 3 for s in seen_lines):
                unique.append(item)
                seen_lines.add(item['line'])

    return unique


def main():
    """Find all missing letters."""
    print("="*80)
    print("Finding Missing Letters")
    print("="*80)

    # Load extraction report to see what's missing
    with open("output/extraction_report.json") as f:
        report = json.load(f)

    missing_romans = report['missing_letters']
    print(f"\nSearching for {len(missing_romans)} missing letters")

    # Convert to numbers
    def roman_to_int(r):
        if r == '1':
            return 1
        vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = prev = 0
        for char in reversed(r):
            val = vals[char]
            total += val if val >= prev else -val
            prev = val
        return total

    missing_nums = [roman_to_int(r) for r in missing_romans]

    # Load source text
    with open("gandhi-patel-letters.txt") as f:
        lines = f.readlines()

    # Search for each missing letter
    results = {}
    for num in missing_nums[:50]:  # Search first 50
        print(f"\nSearching for Letter {int_to_roman(num)} (#{num})...")
        found = find_letter_aggressive(lines, num)

        if found:
            print(f"  Found {len(found)} potential locations:")
            for item in found[:3]:  # Show top 3
                print(f"    Line {item['line']}: {item['text'][:50]} (confidence: {item['confidence']})")
                print(f"      Context: {item['context'][:80]}...")

            results[int_to_roman(num)] = found
        else:
            print(f"  NOT FOUND")

    # Save results
    with open("missing_letters_found.json", 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Found potential locations for {len(results)} missing letters")
    print(f"Saved to missing_letters_found.json")

    # Show summary
    print(f"\n{'='*80}")
    print("Summary:")
    print(f"{'='*80}")
    for letter_num, locations in sorted(results.items(), key=lambda x: roman_to_int(x[0]) if x[0] != '1' else 1)[:20]:
        if locations:
            best = locations[0]
            print(f"{letter_num:8s}: Line {best['line']:5d} - {best['text'][:40]:40s} (conf: {best['confidence']})")


if __name__ == "__main__":
    main()
