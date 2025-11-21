#!/usr/bin/env python3
"""
Analyze what we extracted vs. what should be there.
Find patterns in the actual letter text to improve extraction.
"""

import json
import re

def analyze_current_extraction():
    """Analyze the current extraction"""
    with open('letters_final.json', 'r') as f:
        data = json.load(f)

    letters = data['letters']

    print(f"Current Extraction: {len(letters)} letters\n")
    print("="*80)

    # Find issues
    issues = {
        'no_recipient': [],
        'bad_recipient': [],
        'no_date': [],
        'short_body': [],
        'no_footnotes': []
    }

    for i, letter in enumerate(letters):
        num = letter.get('number', i+1)
        recipient = letter.get('recipient')
        date = letter.get('date')
        body = letter.get('body', '')
        footnotes = letter.get('footnotes', {})

        # Check for issues
        if not recipient:
            issues['no_recipient'].append(num)

        # Bad recipient (too long or looks like body text)
        if recipient and (len(recipient) > 60 or any(word in recipient.lower() for word in ['must', 'think', 'write', 'tell'])):
            issues['bad_recipient'].append((num, recipient))

        if not date:
            issues['no_date'].append(num)

        if len(body) < 100:
            issues['short_body'].append((num, len(body)))

        if not footnotes:
            issues['no_footnotes'].append(num)

    # Print issues
    print(f"\n📊 Issue Summary:")
    print(f"  No recipient: {len(issues['no_recipient'])}")
    print(f"  Bad recipient: {len(issues['bad_recipient'])}")
    print(f"  No date: {len(issues['no_date'])}")
    print(f"  Short body (<100 chars): {len(issues['short_body'])}")
    print(f"  No footnotes: {len(issues['no_footnotes'])}")

    # Show bad recipients
    if issues['bad_recipient']:
        print(f"\n❌ Bad Recipients:")
        for num, recipient in issues['bad_recipient'][:10]:
            print(f"  Letter {num}: {recipient[:70]}...")

    # Show short bodies
    if issues['short_body']:
        print(f"\n⚠️  Very Short Letters:")
        for num, length in issues['short_body'][:10]:
            print(f"  Letter {num}: {length} chars")

    # Show recipient distribution
    print(f"\n📨 Top Recipients:")
    recipient_counts = {}
    for letter in letters:
        rec = letter.get('recipient') or 'Unknown'
        recipient_counts[rec] = recipient_counts.get(rec, 0) + 1

    for rec, count in sorted(recipient_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {rec:<45} {count:2d} letters")

    return issues

def find_letter_patterns():
    """Find patterns in the source text to improve extraction"""
    with open('letters_1917_raw.txt', 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # Find letter start (after biography section)
    letters_start = text.find("MY  DEAR  GOOD  FATHER")
    if letters_start == -1:
        print("Could not find start of letters")
        return

    # Get letter section
    letters_section = text[letters_start-200:]

    # Find patterns like "To his Brother Michael"
    to_patterns = re.findall(r'(To\s+[^\n]{10,80})\s*\n', letters_section[:50000])

    print(f"\n🔍 Found 'To ...' Patterns (first 20):")
    for i, pattern in enumerate(to_patterns[:20], 1):
        pattern = re.sub(r'\s+', ' ', pattern)
        print(f"  {i:2d}. {pattern}")

    # Find patterns with Roman numerals
    roman_patterns = re.findall(r'\n([IVXL]+)\s*\n', letters_section[:50000])
    print(f"\n🔍 Found Roman Numerals: {len(set(roman_patterns))}")
    print(f"  {', '.join(sorted(set(roman_patterns[:30])))}")

def main():
    print("="*80)
    print("EXTRACTION ANALYSIS")
    print("="*80)

    issues = analyze_current_extraction()

    print("\n")
    find_letter_patterns()

    print("\n" + "="*80)
    print("\nRecommendations:")
    print("1. Re-extract using better letter boundary detection")
    print("2. Use TOC as guide for expected 77 letters")
    print("3. Cross-validate recipients with TOC")
    print("4. Extract dates more carefully (many are multi-line)")
    print("="*80)

if __name__ == '__main__':
    main()
