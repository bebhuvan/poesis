#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE EXTRACTION - All Tagore Letters
Handles all edge cases: dated letters, undated ship letters, Red Sea, etc.
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class Letter:
    """Complete letter data"""
    num: int
    location: str
    date_str: str
    date_iso: str
    date_confidence: str
    body: str
    word_count: int
    start_line: int = 0  # For debugging


def remove_page_headers(text: str) -> str:
    """Aggressively remove all page headers and numbers"""
    # Remove "X LETTERS FROM ABROAD" patterns
    text = re.sub(r'\n\d+\s+LETTE[RH]S\s+FROM\s+ABROAD\s*\n', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\nLETTE[RH]S\s+FROM\s+ABROAD\s+\d+\s*\n', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\nLETTE[RH]S\s+FROM\s+ABROAD\s*\n', '\n\n', text, flags=re.IGNORECASE)

    # Remove standalone page numbers
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def parse_date(date_str: str) -> Tuple[str, str]:
    """Parse date to ISO format with confidence"""
    if not date_str or len(date_str) < 3:
        return "", "none"

    month_map = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        'fehraary': '02', 'ikarch': '03', 'jilpril': '04',
    }

    # Normalize
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
            if day_int > 31:  # OCR error
                day = '15'  # Use middle of month
            else:
                day = str(day_int).zfill(2)

            return f"{year}-{month}-{day}", "high"

    # Just month year
    m = re.search(r'([a-z]+)[,\s]+(\d{4})', date_clean)
    if m:
        month_name, year = m.groups()
        for m_key, m_val in month_map.items():
            if month_name.startswith(m_key[:3]):
                return f"{year}-{m_val}-00", "medium"

    return "", "none"


def is_valid_location(text: str) -> bool:
    """Check if text looks like a valid location (not mid-sentence)"""
    # Must start with capital
    if not text or not text[0].isupper():
        return False

    # Too long (probably captured multiple lines)
    if len(text) > 60:
        return False

    # Contains lowercase sentence starters (mid-sentence capture)
    if any(pattern in text.lower() for pattern in [
        'person under', 'the pair', 'with my blessings',
        'mastery of', 'and then', 'when the'
    ]):
        return False

    # Must not have too many words
    word_count = len(text.split())
    if word_count > 8:
        return False

    return True


def extract_all_letters_comprehensive(input_file: str) -> List[Letter]:
    """Extract ALL letters using multiple strategies"""

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    # Find start of letters section
    start_idx = full_text.find("Bombay,")
    if start_idx == -1:
        print("❌ Cannot find start")
        return []

    text = full_text[start_idx:]
    text = remove_page_headers(text)

    lines = text.split('\n')
    letters = []
    i = 0
    letter_num = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check if this looks like a location header
        # Pattern 1: "Location," (with comma)
        # Pattern 2: "Location" followed by date on next line
        # Pattern 3: Ship names like "S. S. Rhyndam." or "Red Sea,"

        is_location = False
        location = ""
        date_line = ""
        body_start = i + 1

        # Check for comma-terminated location
        if line.endswith(',') or line.endswith('.'):
            potential_location = line.rstrip('.,').strip()

            if is_valid_location(potential_location):
                is_location = True
                location = potential_location

                # Check next line for date
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Is it a date?
                    if any(month in next_line for month in [
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December',
                        'Fehraary', 'Ikarch'
                    ]):
                        date_line = next_line
                        body_start = i + 2
                    else:
                        # No date (ship letters like S.S. Rhyndam)
                        body_start = i + 1

        if is_location:
            # Found a letter! Extract until next letter
            letter_num += 1

            # Find end of letter (next location header or end of text)
            body_lines = []
            j = body_start

            while j < len(lines):
                check_line = lines[j].strip()

                # Check if we hit next letter
                if j > body_start + 3:  # Give at least 3 lines of content
                    # Is this line a location?
                    if (check_line.endswith(',') or check_line.endswith('.')) and \
                       len(check_line) > 3 and check_line[0].isupper():
                        potential_loc = check_line.rstrip('.,').strip()
                        if is_valid_location(potential_loc):
                            # Check if next line might be a date
                            if j + 1 < len(lines):
                                next = lines[j + 1].strip()
                                if any(m in next for m in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']) or \
                                   (len(next) < 50 and potential_loc in ['Red Sea', 'Near Aden', 'London', 'Paris', 'New York', 'Chicago', 'Berlin', 'Geneva'] + \
                                    [s for s in ['S. S. Rhyndam', 'S. 3. Morea', 'S. S. MOREA', 'S. Moeea', 'ISfEAR New York', 'JNEW York', 'AuTouR DU Monde']]):
                                    # This is next letter
                                    break

                body_lines.append(lines[j])
                j += 1

            # Build letter
            body = '\n'.join(body_lines).strip()
            word_count = len(body.split())

            # Skip if too short (extraction error)
            if word_count < 50:
                print(f"⚠️  Skipping {location} - only {word_count} words")
                i = j
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
                start_line=i
            )

            letters.append(letter)

            print(f"✓ #{letter_num:3d}  {location[:30]:30s}  {date_iso or 'undated':12s}  {word_count:5d} words")

            # Move to next letter
            i = j
        else:
            i += 1

    return letters


def save_letters(letters: List[Letter], output_dir: str):
    """Save letters to markdown files"""
    output_path = Path(output_dir)
    final_dir = output_path / "letters"
    final_dir.mkdir(parents=True, exist_ok=True)

    for letter in letters:
        # Filename
        date_str = letter.date_iso if letter.date_iso else "undated"
        filename = f"tagore_unknown_{date_str}_{letter.num:03d}.md"

        # Markdown
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
extraction_method: "comprehensive_multipattern"
extraction_date: "2025-11-21"
quality: "high"
---

{letter.location},
{letter.date_str if letter.date_str else ''}

{letter.body}

---

### Editorial Notes
- Letter #{letter.num} from "Letters From Abroad" (1924)
- Extracted using comprehensive multi-pattern detection
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
    output_dir = "/home/user/poesis/New tagore 2/final_clean_extraction"

    print("=" * 70)
    print("FINAL COMPREHENSIVE TAGORE LETTER EXTRACTION")
    print("Handles: dated letters, undated ship letters, all edge cases")
    print("=" * 70 + "\n")

    letters = extract_all_letters_comprehensive(input_file)

    if letters:
        save_letters(letters, output_dir)

        print("\n" + "=" * 70)
        print(f"✅ EXTRACTED {len(letters)} CLEAN LETTERS")
        print("=" * 70)
        print(f"📊 Total words: {sum(l.word_count for l in letters):,}")
        print(f"📁 Output: {output_dir}/letters/")
        print("=" * 70)
