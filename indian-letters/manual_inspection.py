#!/usr/bin/env python3
"""
Manual inspection helper for the final 18 missing letters.
Shows context around where each letter SHOULD be to help with manual extraction.
"""

import re
import json
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


def int_to_roman(num: int) -> str:
    """Convert integer to Roman numeral."""
    vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    result = ''
    for i, v in enumerate(vals):
        count, num = divmod(num, v)
        result += syms[i] * count
    return result


def find_letter_context(lines, target_num, existing_map):
    """Find the context around where a missing letter should be."""
    # Find neighbors
    prev_num = target_num - 1
    next_num = target_num + 1

    while prev_num > 0 and prev_num not in existing_map:
        prev_num -= 1
    while next_num <= 293 and next_num not in existing_map:
        next_num += 1

    result = {
        'target': target_num,
        'target_roman': int_to_roman(target_num),
        'prev_letter': None,
        'next_letter': None,
        'search_range': None,
        'context_preview': []
    }

    if prev_num in existing_map:
        prev_info = existing_map[prev_num]
        result['prev_letter'] = {
            'num': prev_num,
            'roman': int_to_roman(prev_num),
            'line_start': prev_info['source_lines'][0] if 'source_lines' in prev_info else None,
            'line_end': prev_info['source_lines'][1] if 'source_lines' in prev_info else None
        }

    if next_num in existing_map:
        next_info = existing_map[next_num]
        result['next_letter'] = {
            'num': next_num,
            'roman': int_to_roman(next_num),
            'line_start': next_info['source_lines'][0] if 'source_lines' in next_info else None,
            'line_end': next_info['source_lines'][1] if 'source_lines' in next_info else None
        }

    # Define search range
    if result['prev_letter'] and result['next_letter']:
        start_line = result['prev_letter']['line_end']
        end_line = result['next_letter']['line_start']
        result['search_range'] = (start_line, end_line)

        # Get preview of this range
        if start_line and end_line:
            for i in range(max(0, start_line - 5), min(len(lines), end_line + 5)):
                result['context_preview'].append({
                    'line_num': i,
                    'text': lines[i].strip()
                })

    return result


def manual_extract_letter(lines, start_line, target_num):
    """Manually extract a letter starting at a specific line."""
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
    max_lines = 400
    lines_read = 0

    while i < len(lines) and lines_read < max_lines:
        line = lines[i].strip()

        # Stop if clear next letter
        if re.match(r'^[IVXLCDM]+$', line):
            next_num = roman_to_int(line)
            if next_num > target_num:
                break

        # Skip headers/footers
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

    if not body or len(body) < 20:
        return None

    return {
        'number': int_to_roman(target_num),
        'value': target_num,
        'location': location,
        'date': date,
        'salutation': salutation,
        'body': body,
        'closing': closing,
        'source_lines': (start_line, i)
    }


def main():
    """Manual inspection and extraction of final 18 letters."""
    print("="*80)
    print("Manual Inspection - Final 18 Letters")
    print("="*80)

    # Load missing letters
    with open("indian-letters/output/extraction_report.json") as f:
        report = json.load(f)

    missing_romans = report['missing_letters']
    missing_numbers = [roman_to_int(r) for r in missing_romans]

    print(f"\nMissing: {len(missing_numbers)} letters")
    print(f"Numbers: {missing_numbers}")

    # Load source
    with open("indian-letters/gandhi-patel-letters.txt") as f:
        lines = f.readlines()

    # Load existing letters
    with open("indian-letters/letters_complete.json") as f:
        existing_letters = json.load(f)

    existing_map = {l['value']: l for l in existing_letters}

    # Analyze each missing letter
    print("\n" + "="*80)
    print("Analyzing each missing letter...")
    print("="*80)

    manual_extractions = []

    for target_num in missing_numbers:
        print(f"\n{'='*60}")
        print(f"Letter {int_to_roman(target_num)} (#{target_num})")
        print(f"{'='*60}")

        context = find_letter_context(lines, target_num, existing_map)

        if context['prev_letter']:
            print(f"Previous: Letter {context['prev_letter']['roman']} ends at line {context['prev_letter']['line_end']}")

        if context['next_letter']:
            print(f"Next: Letter {context['next_letter']['roman']} starts at line {context['next_letter']['line_start']}")

        if context['search_range']:
            start, end = context['search_range']
            if start is not None and end is not None:
                print(f"Search range: lines {start} to {end} ({end - start} lines)")
            else:
                print(f"Search range incomplete: {start} to {end}")

            # Show some context
            if start is not None and end is not None:
                print(f"\nContext preview (showing 20 lines around the gap):")
                relevant_lines = [c for c in context['context_preview'] if start - 10 <= c['line_num'] <= end + 10]
                for ctx in relevant_lines[:20]:
                    marker = " >>> " if start <= ctx['line_num'] <= end else "     "
                    print(f"{marker}{ctx['line_num']:5d}: {ctx['text'][:70]}")

            # Try to find ANY mention of the target Roman numeral
            target_roman = int_to_roman(target_num)
            print(f"\nSearching for '{target_roman}' in the text...")

            found_mentions = []
            search_start = (start - 50) if start is not None else 0
            search_end = (end + 50) if end is not None else len(lines)
            for i in range(max(0, search_start), min(len(lines), search_end)):
                if target_roman in lines[i]:
                    found_mentions.append((i, lines[i].strip()))

            if found_mentions:
                print(f"Found {len(found_mentions)} mentions:")
                for line_num, text in found_mentions[:5]:
                    print(f"  Line {line_num}: {text[:80]}")

                # Try extraction from first mention
                if found_mentions:
                    first_mention_line = found_mentions[0][0]
                    print(f"\nAttempting extraction from line {first_mention_line}...")
                    letter = manual_extract_letter(lines, first_mention_line, target_num)

                    if letter:
                        manual_extractions.append(letter)
                        print(f"✓ EXTRACTED! ({len(letter['body'])} chars)")
                        print(f"  Location: {letter['location']}")
                        print(f"  Date: {letter['date']}")
                    else:
                        print("✗ Extraction failed")
            else:
                print("✗ No mentions found")

        print()

    # Save any new extractions
    if manual_extractions:
        print("\n" + "="*80)
        print(f"Successfully extracted {len(manual_extractions)} more letters!")
        print("="*80)

        # Combine and save
        all_letters = existing_letters + manual_extractions
        all_letters.sort(key=lambda x: x['value'])

        with open("indian-letters/letters_complete.json", 'w', encoding='utf-8') as f:
            json.dump(all_letters, f, indent=2, ensure_ascii=False)

        with open("indian-letters/manual_extracted.json", 'w', encoding='utf-8') as f:
            json.dump(manual_extractions, f, indent=2, ensure_ascii=False)

        print(f"\nTotal letters: {len(all_letters)} of 293")
        print(f"Coverage: {len(all_letters)/293*100:.1f}%")

        # Show what we got
        for letter in manual_extractions:
            print(f"\n- {letter['number']}: {letter['location']} - {letter['date']}")
    else:
        print("\n" + "="*80)
        print("No new letters extracted via manual inspection")
        print("="*80)
        print("\nThese letters may require:")
        print("- Direct PDF inspection")
        print("- Contacting the archive for better scans")
        print("- Accepting they may be missing from the digitization")


if __name__ == "__main__":
    main()
