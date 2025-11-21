#!/usr/bin/env python3
"""
Parse the table of contents to get the authoritative list of letters.
"""

import re
import json

def parse_toc(text_file):
    """Parse TOC from the text file"""
    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # Find TOC section
    toc_start = text.find("LETTERS")
    toc_end = text.find("RECOLLECTIONS  OF  DOSTOEVSKY")

    if toc_start == -1 or toc_end == -1:
        print("Could not find TOC section")
        return []

    toc_text = text[toc_start:toc_end]

    # Join lines that are continuations (no number at start)
    lines = toc_text.split('\n')
    joined_lines = []
    current_line = ''

    for line in lines:
        stripped = line.strip()

        # Check if line starts with a number (new entry)
        if re.match(r'^\d+[-.]', stripped):
            if current_line:
                joined_lines.append(current_line)
            current_line = stripped
        else:
            # Continuation of previous line
            if current_line and stripped:
                current_line += ' ' + stripped

    if current_line:
        joined_lines.append(current_line)

    letters = []
    current_recipient = None

    for line in joined_lines:
        # Clean up line
        line = re.sub(r'\s+', ' ', line.strip())

        # Extract letter number
        num_match = re.match(r'^(\d+)[-.]', line)
        if not num_match:
            continue

        num = int(num_match.group(1))

        # Pattern 1: New recipient "N. To [recipient]: [date]"
        match = re.search(r'To\s+([^:]+?):\s*(.+?)(?:\s+\.\s*\d+)?$', line)
        if match:
            recipient = match.group(1).strip()
            recipient = re.sub(r'\s+', ' ', recipient)
            date = match.group(2).strip()

            # Clean up date (remove page numbers at end)
            date = re.sub(r'\s*\.\s*\d+\s*$', '', date)
            date = re.sub(r'\s*\d+\s*$', '', date)
            date = date.strip('. ')

            letters.append({
                'number': num,
                'recipient': recipient,
                'date': date
            })
            current_recipient = recipient
            continue

        # Pattern 2: Ditto marks - same recipient
        # Matches: "6. „ :, March 24, 1845 . . 17"
        #          "18. .. ,, August 27, 1849 . . 46"
        match = re.search(r'[„.,:\s]+([A-Z][^.]+?)(?:\s+\.\s*\d+)?$', line)
        if match and current_recipient:
            date = match.group(1).strip()
            # Clean up date
            date = re.sub(r'\s*\.\s*\d+\s*$', '', date)
            date = re.sub(r'\s*\d+\s*$', '', date)
            date = date.strip('. ,')

            # Skip if date looks weird (too long or has "To ")
            if len(date) < 100 and 'To ' not in date and date:
                letters.append({
                    'number': num,
                    'recipient': current_recipient,
                    'date': date
                })

    return letters

def main():
    letters = parse_toc('letters_1917_raw.txt')

    print(f"\nParsed {len(letters)} letters from TOC\n")
    print("="*80)

    # Show first 10
    for letter in letters[:10]:
        print(f"{letter['number']:2d}. To {letter['recipient']:<40} {letter['date']}")

    print(f"\n... ({len(letters) - 20} more) ...\n")

    # Show last 10
    for letter in letters[-10:]:
        print(f"{letter['number']:2d}. To {letter['recipient']:<40} {letter['date']}")

    print("="*80)

    # Save to JSON
    with open('toc_letters.json', 'w', encoding='utf-8') as f:
        json.dump({'total': len(letters), 'letters': letters}, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to toc_letters.json")

    # Statistics
    recipients = {}
    for letter in letters:
        rec = letter['recipient']
        recipients[rec] = recipients.get(rec, 0) + 1

    print("\nRecipients:")
    for rec, count in sorted(recipients.items(), key=lambda x: -x[1])[:15]:
        print(f"  {rec:<45} {count:2d} letters")

if __name__ == '__main__':
    main()
