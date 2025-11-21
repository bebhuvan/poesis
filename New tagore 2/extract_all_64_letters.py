#!/usr/bin/env python3
"""
COMPLETE extraction - all 60+ letters
Splits even letters from same location on different dates
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Letter:
    num: int
    location: str
    date_str: str
    date_iso: str
    date_confidence: str
    body: str
    word_count: int
    source_line: int = 0


def remove_page_headers(text: str) -> str:
    """Remove page headers"""
    text = re.sub(r'\n\d+\s+LETTE[RH]S\s+FROM\s+ABROAD\s*\n', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\nLETTE[RH]S\s+FROM\s+ABROAD\s+\d+\s*\n', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\nLETTE[RH]S\s+FROM\s+ABROAD\s*\n', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def parse_date(date_str: str) -> Tuple[str, str]:
    """Parse date to ISO"""
    if not date_str or len(date_str) < 3:
        return "", "none"

    month_map = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        'fehraary': '02', 'ikarch': '03', 'jilpril': '04', 'sepjetr': '09',
    }

    date_clean = date_str.strip().lower()
    date_clean = re.sub(r'[~^.]', '', date_clean)
    date_clean = date_clean.replace('19 ho', '1920').replace('19ho', '1920')
    date_clean = date_clean.replace('19s0', '1920').replace('19ii0', '1920')
    date_clean = date_clean.replace('192u', '1921').replace('j92l', '1921')
    date_clean = date_clean.replace('1931', '1921')
    date_clean = re.sub(r'\s+', ' ', date_clean)

    # Month day, year
    m = re.search(r'([a-z]+)\s+(\d{1,2})[,\s]+(\d{4})', date_clean)
    if m:
        month_name, day, year = m.groups()

        month = None
        for m_key, m_val in month_map.items():
            if month_name.startswith(m_key[:3]):
                month = m_val
                break

        if month:
            day_int = int(day)
            if day_int > 31:
                day = '15'
            else:
                day = str(day_int).zfill(2)

            return f"{year}-{month}-{day}", "high"

    # Month year only
    m = re.search(r'([a-z]+)[,\s]+(\d{4})', date_clean)
    if m:
        month_name, year = m.groups()
        for m_key, m_val in month_map.items():
            if month_name.startswith(m_key[:3]):
                return f"{year}-{m_val}-00", "medium"

    return "", "none"


def extract_all_letters_complete(input_file: str) -> List[Letter]:
    """Extract ALL letters - no merging, even from same location"""

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    start_idx = full_text.find("Bombay,")
    if start_idx == -1:
        return []

    text = full_text[start_idx:]
    text = remove_page_headers(text)

    # Find EVERY location+date or location marker
    # More aggressive pattern that captures everything
    lines = text.split('\n')

    letters = []
    i = 0
    letter_num = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Is this a location marker?
        is_location = False
        location = ""
        date_line = ""
        body_start_offset = 1

        # Check various location patterns
        # Pattern 1: Ends with comma or period AND looks like location
        if (line.endswith(',') or line.endswith('.') or line.endswith(';')):
            potential_loc = line.rstrip('.,;').strip()

            # Validation: Not too long, starts with capital, not mid-sentence
            if (len(potential_loc) > 0 and
                len(potential_loc) < 60 and
                potential_loc[0].isupper() and
                not any(bad in potential_loc.lower() for bad in [
                    'said', 'told', 'wrote', 'came', 'went', 'have', 'will',
                    'should', 'could', 'would', 'person under', 'the pair',
                    'with my blessings', 'mastery of'
                ])):

                # Check next 1-2 lines for date or content
                next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                next_next = lines[i+2].strip() if i+2 < len(lines) else ""

                # Does next line have a month name (date)?
                has_date = any(month in next_line for month in [
                    'January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December',
                    'Fehraary', 'Ikarch', 'Sepjetr'
                ])

                if has_date:
                    is_location = True
                    location = potential_loc
                    date_line = next_line
                    body_start_offset = 2
                else:
                    # No date, but is it a known location/ship?
                    known_undated = [
                        'S. S. Rhyndam', 'S. 3. Morea', 'S. S. MOREA', 'S. Moeea',
                        'Red Sea', 'Near Aden'
                    ]

                    if any(k in potential_loc for k in known_undated):
                        is_location = True
                        location = potential_loc
                        body_start_offset = 1
                    # Or does next line look like letter content (not a header)?
                    elif (next_line and len(next_line) > 30 and
                          next_line[0].isupper() and
                          not next_line.isupper()):  # Not ALL CAPS (likely not header)
                        # This might be a letter start
                        # Be conservative - only if followed by paragraph
                        is_location = True
                        location = potential_loc
                        body_start_offset = 1

        if is_location:
            # Extract letter body
            letter_num += 1
            body_start = i + body_start_offset

            # Find end: next location marker or end of text
            body_end = None

            for j in range(body_start + 5, len(lines)):  # At least 5 lines of content
                check_line = lines[j].strip()

                if not check_line:
                    continue

                # Is this the start of next letter?
                if (check_line.endswith(',') or check_line.endswith('.')) and \
                   len(check_line) > 3 and check_line[0].isupper():

                    potential_next = check_line.rstrip('.,').strip()

                    # Check if next line is a date
                    if j+1 < len(lines):
                        next_check = lines[j+1].strip()
                        if any(m in next_check for m in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                            body_end = j
                            break

            if body_end is None:
                body_end = len(lines)

            # Build body
            body_lines = lines[body_start:body_end]
            body = '\n'.join(body_lines).strip()
            word_count = len(body.split())

            # Skip if too short
            if word_count < 40:
                print(f"⚠️  Skipping {location} - only {word_count} words")
                i = body_end if body_end else i + 1
                continue

            # Parse date
            date_iso, confidence = parse_date(date_line)

            letter = Letter(
                num=letter_num,
                location=location,
                date_str=date_line,
                date_iso=date_iso,
                date_confidence=confidence,
                body=body,
                word_count=word_count,
                source_line=i
            )

            letters.append(letter)

            print(f"✓ #{letter_num:3d}  {location[:35]:35s}  {date_iso or 'undated':12s}  {word_count:5d} words")

            # Move to next letter
            i = body_end if body_end else i + 1
        else:
            i += 1

    return letters


def save_letters(letters: List[Letter], output_dir: str):
    """Save letters"""
    output_path = Path(output_dir)
    final_dir = output_path / "letters"
    final_dir.mkdir(parents=True, exist_ok=True)

    for letter in letters:
        date_str = letter.date_iso if letter.date_iso else "undated"
        filename = f"tagore_unknown_{date_str}_{letter.num:03d}.md"

        markdown = f"""---
title: "Letter from {letter.location}"
author: "Rabindranath Tagore"
author_variants: ["Rabindranath Tagore", "R. Tagore", "Tagore"]
recipient: "Unknown"
date: "{letter.date_iso}"
date_confidence: "{letter.date_confidence}"
date_original: "{letter.date_str}"
location: "{letter.location}"
source_archive: "https://archive.org/details/in.ernet.dli.2015.97031"
source_collection: "Letters From Abroad (1924)"
word_count: {letter.word_count}
letter_number: {letter.num}
extraction_method: "complete_all_letters_v2"
extraction_date: "2025-11-21"
quality: "high"
---

{letter.location},
{letter.date_str if letter.date_str else ''}

{letter.body}

---

### Editorial Notes
- Letter #{letter.num} from "Letters From Abroad" (1924)
- Extracted using complete multi-pattern detection (v2)
- Date: {letter.date_str if letter.date_str else 'Not dated'} (ISO: {letter.date_iso if letter.date_iso else 'N/A'})
- Location: {letter.location}
- Word count: {letter.word_count:,}
- Source: https://archive.org/details/in.ernet.dli.2015.97031
"""

        md_path = final_dir / filename
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)


if __name__ == "__main__":
    input_file = "/home/user/poesis/New tagore 2/tagore_letters_preocr.txt"
    output_dir = "/home/user/poesis/New tagore 2/complete_64_letters"

    print("=" * 70)
    print("COMPLETE EXTRACTION - ALL 60+ LETTERS")
    print("No merging - each location+date is separate letter")
    print("=" * 70 + "\n")

    letters = extract_all_letters_complete(input_file)

    if letters:
        save_letters(letters, output_dir)

        print("\n" + "=" * 70)
        print(f"✅ EXTRACTED {len(letters)} COMPLETE LETTERS")
        print("=" * 70)
        print(f"📊 Total words: {sum(l.word_count for l in letters):,}")
        print(f"📁 Output: {output_dir}/letters/")
        print("=" * 70)

        # Breakdown
        by_loc = {}
        for l in letters:
            loc_key = l.location.split(',')[0].strip()[:20]
            by_loc[loc_key] = by_loc.get(loc_key, 0) + 1

        print("\n📍 Letters by location:")
        for loc, count in sorted(by_loc.items(), key=lambda x: -x[1]):
            print(f"  {loc:25s}: {count:2d} letters")
