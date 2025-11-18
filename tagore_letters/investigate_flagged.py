#!/usr/bin/env python3
"""
Investigate flagged letters that couldn't be auto-verified
"""

import re
from pathlib import Path

def investigate_letter(letter_num):
    """Deep dive into why a letter couldn't be found"""

    # Load the extracted letter
    letter_files = sorted(Path('extracted_letters_thorough').glob('letter_*.md'))
    letter_file = letter_files[letter_num - 1]

    print("=" * 80)
    print(f"INVESTIGATING LETTER {letter_num}")
    print("=" * 80)
    print(f"File: {letter_file.name}\n")

    with open(letter_file, 'r') as f:
        content = f.read()

    # Extract metadata and content
    lines = content.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('**') and ',' in line:
            start_idx = i + 2
            break

    letter_content = '\n'.join(lines[start_idx:]).strip()

    print(f"Letter length: {len(letter_content)} chars")
    print(f"\nFirst 300 chars of extracted letter:")
    print("-" * 80)
    print(letter_content[:300])
    print("-" * 80)

    # Load source texts
    djvu_text = Path('tagore_letters_raw.txt').read_text()
    epub_text = Path('epub_extracted_text.txt').read_text()

    # Try to find variations
    print("\nSearching in DjVu source...")
    search_variations = [
        letter_content[:100],
        letter_content[:50],
        re.sub(r'\s+', ' ', letter_content[:100]),
        re.sub(r'[^\w\s]', '', letter_content[:100]),
    ]

    for i, variation in enumerate(search_variations, 1):
        clean_djvu = re.sub(r'\s+', ' ', djvu_text)
        clean_variation = re.sub(r'\s+', ' ', variation)

        pos = clean_djvu.find(clean_variation)
        if pos != -1:
            print(f"✓ Found using variation {i} at position {pos}")
            context = clean_djvu[max(0, pos-200):pos+500]
            print(f"\nContext:")
            print("-" * 80)
            print(context)
            print("-" * 80)
            return True

    print("✗ Not found in DjVu with any variation")

    print("\nSearching in EPUB source...")
    for i, variation in enumerate(search_variations, 1):
        clean_epub = re.sub(r'\s+', ' ', epub_text)
        clean_variation = re.sub(r'\s+', ' ', variation)

        pos = clean_epub.find(clean_variation)
        if pos != -1:
            print(f"✓ Found using variation {i} at position {pos}")
            context = clean_epub[max(0, pos-200):pos+500]
            print(f"\nContext:")
            print("-" * 80)
            print(context)
            print("-" * 80)
            return True

    print("✗ Not found in EPUB with any variation")

    # Try searching for key phrases
    print("\nSearching for key phrases...")
    words = letter_content.split()[:20]
    for phrase_len in [10, 7, 5, 3]:
        phrase = ' '.join(words[:phrase_len])
        clean_phrase = re.sub(r'\s+', ' ', phrase)

        if clean_phrase in re.sub(r'\s+', ' ', djvu_text):
            print(f"✓ Found {phrase_len}-word phrase in DjVu:")
            print(f"  '{clean_phrase[:80]}...'")
            break
        elif clean_phrase in re.sub(r'\s+', ' ', epub_text):
            print(f"✓ Found {phrase_len}-word phrase in EPUB:")
            print(f"  '{clean_phrase[:80]}...'")
            break
    else:
        print("✗ No key phrases found")

    return False


# Investigate all flagged letters
flagged = [1, 3, 4, 5, 11, 43, 61]

for letter_num in flagged:
    investigate_letter(letter_num)
    print("\n\n")
