#!/usr/bin/env python3
"""
Extract ACTUAL individual letters by finding date/location headers
Pattern: LOCATION, Month Day, Year (e.g., "SANTINIKETAN, October 11th, 1913")
"""

import json
import re
from typing import List, Dict


def find_actual_letter_boundaries(ocr_text: Dict[int, str]) -> List[Dict]:
    """Find actual letter starts by date/location patterns"""

    # Pattern for letter headers: LOCATION, Date
    # Examples:
    # "SANTINIKETAN, October 11th, 1913"
    # "SANTINIKETAN, February 1914"
    # "BOLPUR, December 1913"

    patterns = [
        # Full date: Month Day, Year
        r'^([A-Z][A-Z\s]+),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}',
        # Short date: Month Year
        r'^([A-Z][A-Z\s]+),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        # With location only in caps
        r'^[A-Z]{2,}[A-Z\s]+,\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)',
    ]

    boundaries = []

    for page_num in sorted(ocr_text.keys()):
        if page_num < 35:  # Skip front matter
            continue

        text = ocr_text[page_num]
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            line = line.strip()

            # Check each pattern
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    boundaries.append({
                        'page': page_num,
                        'line': line_num,
                        'marker': line,
                        'type': 'date_location'
                    })
                    break

    return boundaries


def extract_letter_content(ocr_text: Dict[int, str], boundaries: List[Dict]) -> List[Dict]:
    """Extract content for each letter"""

    letters = []

    for i, boundary in enumerate(boundaries):
        start_page = boundary['page']
        start_line = boundary['line']

        # End is the next letter or end of document
        if i + 1 < len(boundaries):
            end_page = boundaries[i + 1]['page']
            end_line = boundaries[i + 1]['line']
        else:
            end_page = max(ocr_text.keys())
            end_line = None

        # Extract content
        content_parts = []

        for page_num in range(start_page, end_page + 1):
            if page_num not in ocr_text:
                continue

            page_text = ocr_text[page_num]
            lines = page_text.split('\n')

            if page_num == start_page and page_num == end_page:
                if end_line is not None:
                    content_parts.extend(lines[start_line:end_line])
                else:
                    content_parts.extend(lines[start_line:])
            elif page_num == start_page:
                content_parts.extend(lines[start_line:])
            elif page_num == end_page:
                if end_line is not None:
                    content_parts.extend(lines[:end_line])
                else:
                    content_parts.extend(lines)
            else:
                content_parts.extend(lines)

        content = '\n'.join(content_parts).strip()

        # Extract date from marker
        date_match = re.search(
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            boundary['marker'],
            re.IGNORECASE
        )
        date = date_match.group(1) if date_match else 'Unknown'

        # Extract location
        location_match = re.match(r'^([A-Z][A-Z\s]+?),', boundary['marker'])
        location = location_match.group(1).strip() if location_match else 'Unknown'

        letters.append({
            'number': i + 1,
            'marker': boundary['marker'],
            'date': date,
            'location': location,
            'start_page': start_page,
            'end_page': end_page,
            'content': content,
            'word_count': len(content.split()),
        })

    return letters


def main():
    print("=" * 80)
    print("EXTRACTING ACTUAL LETTERS BY DATE/LOCATION HEADERS")
    print("=" * 80)

    # Load OCR text
    print("\n📂 Loading OCR text...")
    with open('tagore_full_ocr.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        ocr_text = {int(k): v for k, v in data.items()}

    print(f"✓ Loaded {len(ocr_text)} pages")

    # Find boundaries
    print("\n🔍 Finding actual letter boundaries...")
    boundaries = find_actual_letter_boundaries(ocr_text)
    print(f"✓ Found {len(boundaries)} letters with date/location headers")

    if len(boundaries) == 0:
        print("\n⚠️  No letters found. Let me show sample text to debug...")
        # Show sample from page 40-50
        for page in range(40, 51):
            if page in ocr_text:
                print(f"\n--- PAGE {page} (first 500 chars) ---")
                print(ocr_text[page][:500])
        return

    # Show sample boundaries
    print("\n📋 Sample letter headers found:")
    for b in boundaries[:10]:
        print(f"  Page {b['page']:3d}: {b['marker']}")

    if len(boundaries) > 10:
        print(f"  ... and {len(boundaries) - 10} more")

    # Extract letters
    print("\n✂️  Extracting letter content...")
    letters = extract_letter_content(ocr_text, boundaries)

    # Stats
    total_words = sum(l['word_count'] for l in letters)
    avg_words = total_words / len(letters) if letters else 0

    print(f"\n📊 RESULTS:")
    print(f"  Total letters: {len(letters)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Avg words/letter: {avg_words:.0f}")

    # Save results
    output = {
        'extraction_method': 'Date/Location Header Pattern',
        'total_letters': len(letters),
        'letters': letters
    }

    with open('actual_letters.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved to: actual_letters.json")

    print("\n" + "=" * 80)
    print(f"✅ FOUND {len(letters)} ACTUAL LETTERS!")
    print("=" * 80)

    return letters


if __name__ == '__main__':
    main()
