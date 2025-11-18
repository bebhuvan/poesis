#!/usr/bin/env python3
"""
Check for duplicate letters and verify uniqueness
"""

from pathlib import Path
import re
import hashlib

def analyze_letters():
    """Find duplicates and similar letters"""

    letters_dir = Path('extracted_letters_thorough')
    letters = []

    # Read all letters
    for filepath in sorted(letters_dir.glob('letter_*.md')):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata
        title_match = re.search(r'title: "(.*?)"', content)
        date_match = re.search(r'date: "(.*?)"', content)
        location_match = re.search(r'location: "(.*?)"', content)
        number_match = re.search(r'letter_number: (\d+)', content)

        # Extract main content (after the header)
        content_lines = content.split('\n')
        main_content = '\n'.join([l for l in content_lines if not l.startswith('#') and not l.startswith('**') and not l.startswith('---') and not l.startswith('title:') and not l.startswith('author:') and not l.startswith('recipient:') and not l.startswith('date:') and not l.startswith('location:') and not l.startswith('source:') and not l.startswith('letter_number:')])

        # Clean content for comparison
        clean_content = re.sub(r'\s+', ' ', main_content).strip()[:200]  # First 200 chars

        letters.append({
            'number': int(number_match.group(1)) if number_match else 0,
            'filepath': filepath,
            'location': location_match.group(1) if location_match else '',
            'date': date_match.group(1) if date_match else '',
            'content_hash': hashlib.md5(clean_content.encode()).hexdigest(),
            'content_preview': clean_content[:100],
            'full_length': len(main_content)
        })

    # Find duplicates by hash
    hashes = {}
    duplicates = []

    for letter in letters:
        h = letter['content_hash']
        if h in hashes:
            duplicates.append({
                'original': hashes[h],
                'duplicate': letter
            })
        else:
            hashes[h] = letter

    # Find same date/location pairs
    date_loc_pairs = {}
    multi_same_day = []

    for letter in letters:
        key = (letter['location'], letter['date'])
        if key not in date_loc_pairs:
            date_loc_pairs[key] = []
        date_loc_pairs[key].append(letter)

    for key, items in date_loc_pairs.items():
        if len(items) > 1:
            multi_same_day.append({
                'location': key[0],
                'date': key[1],
                'count': len(items),
                'letters': items
            })

    # Print report
    print("=" * 80)
    print("LETTER DEDUPLICATION ANALYSIS")
    print("=" * 80)
    print()
    print(f"Total letters: {len(letters)}")
    print(f"Unique content hashes: {len(hashes)}")
    print()

    if duplicates:
        print(f"\n⚠ Found {len(duplicates)} DUPLICATE(S):")
        for dup in duplicates:
            print(f"\n  Original: Letter {dup['original']['number']} - {dup['original']['date']}")
            print(f"  Duplicate: Letter {dup['duplicate']['number']} - {dup['duplicate']['date']}")
            print(f"  Preview: {dup['original']['content_preview']}")
    else:
        print("\n✓ No exact duplicates found")

    if multi_same_day:
        print(f"\n📅 Found {len(multi_same_day)} date/location pairs with multiple letters:")
        for group in multi_same_day:
            print(f"\n  {group['location']}, {group['date']} - {group['count']} letters:")
            for letter in group['letters']:
                print(f"    Letter {letter['number']:3d}: {letter['content_preview'][:60]}...")
                print(f"             Length: {letter['full_length']} chars")

    # Check for very short letters (might be over-extracted)
    short_letters = [l for l in letters if l['full_length'] < 100]
    if short_letters:
        print(f"\n⚠ Found {len(short_letters)} very short letters (< 100 chars):")
        for letter in short_letters:
            print(f"  Letter {letter['number']:3d}: {letter['location']}, {letter['date']}")
            print(f"           Length: {letter['full_length']} chars")
            print(f"           Content: {letter['content_preview'][:80]}...")

    print()
    print("=" * 80)
    print(f"UNIQUE LETTERS: {len(hashes)}")
    print("=" * 80)

    return len(hashes)


if __name__ == '__main__':
    count = analyze_letters()
    print(f"\n✓ Unique letter count: {count}")
