#!/usr/bin/env python3
"""
Debug script to understand letter structure
"""

import re
from pathlib import Path

# Load full text
text_path = Path('/home/user/poesis/letters/schiller-goethe/raw_ocr/full_text.txt')
text = text_path.read_text(encoding='utf-8')

# Find Letter II
match = re.search(r'\nII\.\s*\n(.*?)\n(?:III\.|SCHILLER)', text, re.DOTALL)

if match:
    letter_2 = match.group(0)

    print("="*80)
    print("LETTER II RAW TEXT")
    print("="*80)
    print(letter_2)
    print("\n" + "="*80)

    lines = letter_2.split('\n')
    print(f"\nTotal lines: {len(lines)}")
    print("\nLast 5 lines:")
    for i, line in enumerate(lines[-5:], start=len(lines)-5):
        print(f"  [{i}] '{line.strip()}'")

    # Check for signature
    for i in range(len(lines)-1, max(0, len(lines)-5), -1):
        line = lines[i].strip()
        print(f"\nChecking line {i}: '{line}'")
        if 'Schiller' in line or 'schiller' in line.lower():
            print(f"  -> Found Schiller!")
        if 'Goethe' in line or 'goethe' in line.lower():
            print(f"  -> Found Goethe!")
