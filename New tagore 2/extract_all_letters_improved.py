#!/usr/bin/env python3
"""
Improved letter extraction - finds ALL letters properly
Handles multiple letters per section, removes page headers
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict


@dataclass
class LetterMetadata:
    """Letter metadata"""
    author: str = "Rabindranath Tagore"
    author_variants: List[str] = None
    recipient: str = "Unknown"
    date: str = ""
    date_original: str = ""
    date_confidence: str = "low"
    location: str = ""
    source_archive: str = "https://archive.org/details/in.ernet.dli.2015.97031"
    word_count: int = 0
    letter_num: int = 0

    def __post_init__(self):
        if self.author_variants is None:
            self.author_variants = ["Rabindranath Tagore", "R. Tagore", "Tagore"]


def remove_page_headers(text: str) -> str:
    """Remove page headers like 'LETTERS FROM ABROAD 3' and page numbers"""

    # Remove pattern like "2 LETTERS FROM ABROAD" or "LETTERS FROM ABROAD 3"
    text = re.sub(r'\n\d+\s+LETTERS? FROM ABROAD\s*\n', '\n', text)
    text = re.sub(r'\nLETTERS? FROM ABROAD\s+\d+\s*\n', '\n', text)
    text = re.sub(r'\nLETTERS? FROM ABROAD\s*\n', '\n', text)

    # Remove standalone page numbers at start of line
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    return text


def parse_date(date_str: str) -> Tuple[str, str]:
    """Parse date string to ISO format"""
    month_map = {
        'January': '01', 'February': '02', 'March': '03', 'April': '04',
        'May': '05', 'June': '06', 'July': '07', 'August': '08',
        'September': '09', 'October': '10', 'November': '11', 'December': '12',
        'Fehraary': '02',  # OCR error
        'Ikarch': '03',  # OCR error
        'jiLpril': '04',  # OCR error
    }

    # Clean and normalize
    date_str = date_str.strip().replace('.', '').replace('^', '').replace('HO', '20')
    date_str = re.sub(r'\s+', ' ', date_str)

    # Parse "Month Day, Year" format
    pattern = r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})'
    match = re.search(pattern, date_str)

    if match:
        month_name = match.group(1)
        day = match.group(2).zfill(2)
        year = match.group(3)

        month = month_map.get(month_name, None)
        if not month:
            # Try fuzzy match
            for m_name, m_num in month_map.items():
                if m_name.lower().startswith(month_name.lower()[:3]):
                    month = m_num
                    break

        if month:
            iso_date = f"{year}-{month}-{day}"
            return iso_date, "high"

    return "", "none"


def extract_all_letters(text_file: str, output_dir: str):
    """Extract all letters from text"""

    output_path = Path(output_dir)
    final_dir = output_path / "final_markdown"
    review_dir = output_path / "review_html"

    for d in [final_dir, review_dir]:
        d.mkdir(parents=True, exist_ok=True)

    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    print(f"📚 Loaded text: {len(full_text):,} characters\n")

    # Find where actual letters start (skip front matter)
    start_idx = full_text.find("Bombay,")
    if start_idx == -1:
        print("❌ Could not find start of letters")
        return

    letters_text = full_text[start_idx:]

    # Remove page headers first
    letters_text = remove_page_headers(letters_text)

    # Split into potential letter sections
    # Look for pattern: Location name followed by date
    # Pattern: Line starting with capital letter(s) + comma OR specific locations
    # Followed within 1-2 lines by a date pattern

    # More flexible pattern to catch all location/date combinations
    letter_pattern = r'''
        (?:^|\n)                          # Start of line
        ([A-Z][^\n,]{2,40}?),?\s*\n       # Location (capital letter start, up to comma/newline)
        \s*                               # Optional whitespace
        ([A-Z][a-z]+\s+\d{1,2},?\s+\d{4}[^\n]*)\s*\n  # Date line
    '''

    matches = list(re.finditer(letter_pattern, letters_text, re.VERBOSE | re.MULTILINE))

    print(f"🔍 Found {len(matches)} letter boundaries\n")

    letters = []

    for i, match in enumerate(matches):
        start = match.start()
        # End is start of next letter or end of text
        end = matches[i + 1].start() if i + 1 < len(matches) else len(letters_text)

        location_raw = match.group(1).strip()
        date_raw = match.group(2).strip()

        # Extract letter text
        letter_text = letters_text[start:end].strip()

        # Remove the location and date line from start
        letter_body_lines = letter_text.split('\n')[2:]  # Skip first 2 lines (location, date)
        letter_body = '\n'.join(letter_body_lines).strip()

        letters.append({
            'letter_num': i + 1,
            'location_raw': location_raw,
            'date_raw': date_raw,
            'text': letter_body
        })

    # Process each letter
    results = []

    for letter_data in letters:
        letter_num = letter_data['letter_num']

        # Parse metadata
        metadata = LetterMetadata()
        metadata.letter_num = letter_num
        metadata.location = letter_data['location_raw']
        metadata.date_original = letter_data['date_raw']

        iso_date, confidence = parse_date(letter_data['date_raw'])
        metadata.date = iso_date
        metadata.date_confidence = confidence

        metadata.word_count = len(letter_data['text'].split())

        # Generate filename
        date_str = metadata.date if metadata.date else "undated"
        filename = f"tagore_unknown_{date_str}_{letter_num:03d}.md"

        # Generate markdown
        markdown = f"""---
title: "Letter from {metadata.location}"
author: "{metadata.author}"
author_variants: {json.dumps(metadata.author_variants)}
recipient: "{metadata.recipient}"
date: "{metadata.date}"
date_confidence: "{metadata.date_confidence}"
date_original: "{metadata.date_original}"
location: "{metadata.location}"
source_archive: "{metadata.source_archive}"
word_count: {metadata.word_count}
letter_number: {metadata.letter_num}
extraction_method: "archive.org_pre_ocr_improved"
extraction_date: "2025-11-21"
quality: "high"
---

{metadata.location},

{metadata.date_original}

{letter_data['text']}

---

### Editorial Notes
- Extracted from Archive.org pre-OCR'd text
- Date: {metadata.date_original}
- Location: {metadata.location}
- Letter #{metadata.letter_num} from "Letters From Abroad" (1924)
- Page headers removed
- Source: {metadata.source_archive}
"""

        md_path = final_dir / filename
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        results.append({
            'num': letter_num,
            'location': metadata.location,
            'date': metadata.date,
            'words': metadata.word_count,
            'file': filename
        })

        print(f"✓ #{letter_num:3d}  {metadata.location[:25]:25s}  {metadata.date:12s}  {metadata.word_count:5d} words")

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Extracted {len(results)} letters")
    print(f"📊 Total words: {sum(r['words'] for r in results):,}")
    print(f"📁 Output: {final_dir}")
    print("=" * 70)


if __name__ == "__main__":
    text_file = "/home/user/poesis/New tagore 2/tagore_letters_preocr.txt"
    output_dir = "/home/user/poesis/New tagore 2/all_letters_final"

    print("=" * 70)
    print("COMPLETE LETTER EXTRACTION - ALL LETTERS")
    print("=" * 70 + "\n")

    extract_all_letters(text_file, output_dir)
