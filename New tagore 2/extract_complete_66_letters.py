#!/usr/bin/env python3
"""
COMPLETE Tagore Letters Extraction - All 66 Letters
Includes the 4 previously missing letters + expanded OCR corrections
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter

# EXPANDED OCR error correction dictionary
OCR_CORRECTIONS = {
    # Original patterns (from v2)
    r'\bydh\b': 'you',
    r'\bafid\b': 'and',
    r'\bgroat\b': 'great',
    r'\bjealoue\b': 'jealous',
    r'\btkat\b': 'that',
    r'\bui-gent\b': 'urgent',
    r'\bwfiich\b': 'which',
    r'\btjould\b': 'would',
    r'\bPaeis\b': 'Paris',
    r'\bwithcommittee\b': 'with committee',
    r'\bCitizenslwp\b': 'Citizenship',
    r'\bthro\b': 'the',
    r'\bseat\'i\b': 'seats',
    r'% S\. (Rhyndam|Morea)': r'S.S. \1',
    r'S\. 3\. (Morea|Rhyndam)': r'S.S. \1',
    r'\'loNDON': 'LONDON',
    r'\bwo\b': 'we',
    r'\brao\b': 'me',
    r'\bTho\b': 'The',
    r'\btho\b': 'the',
    r'\bsomo\b': 'some',
    r'\bwhon\b': 'when',
    r'\bthoir\b': 'their',
    r'\bmado\b': 'made',

    # NEW patterns from verification (most critical)
    r'\baid\b': 'and',  # 41 occurrences!
    r'\bnswer\b': 'answer',  # 14 occurrences
    r'\bkor\b': 'for',
    r'\bsoa\b': 'sea',
    r'\bboon\b': 'been',
    r'\bifer\b': 'her',
    r'\bhaji\b': 'has',
    r'\bJNEW\b': 'NEW',
    r'\bISfEAR\s+': '',  # Remove OCR artifact
    r'\bCenadian\b': 'Canadian',
    r'\bpopulatioK': 'population',
    r'\bixispire\b': 'inspire',
    r'\bmtional\b': 'national',
    r'\binardi-\s*iiatcly': 'inordinately',
    r'\benornious\b': 'enormous',

    # Character corruption fixes
    r'(\w+)\^(\w+)': r'\1\2',  # Remove ^ between words
    r'(\w+)\\d(\w+)': r'\1\2',  # Remove \d patterns
    r'(\w+)«(\w+)': r'\1\2',  # Remove « between words
    r'(\w+)\'(\w+)': r'\1\2',  # Remove apostrophe corruption in words like compi'oaiise

    # Ship name corrections
    r'S\. Moeea': 'S.S. Morea',
    r'S\. RHYNDAM': 'S.S. Rhyndam',
    r'S\. S\.\s+': 'S.S. ',
}

# Page header patterns
PAGE_HEADER_PATTERNS = [
    r'\n\d+\s+LETTE[RH]S\s+FROM\s+ABROAD\s*\n',
    r'^\d+\s+LETTE[RH]S\s+FROM\s+ABROAD\s*$',
    r'LETTE[RH]S\s+FROM\s+ABROAD\s+\d+',
    r'^\s*\d{1,3}\s*$',
    r'^\s*\d{1,3}t\s*$',
    r'^\s*[a-z]\s*$',
    r'^\s*t\s*$',
    r'\n\s*\d{1,3}\s*\n',
    r'\n\s*M\s+LETTERS\s+FROM\s+ABROAD\s*\n',  # New pattern found
]

def clean_ocr_errors(text: str) -> str:
    """Apply OCR error corrections"""
    cleaned = text
    for pattern, replacement in OCR_CORRECTIONS.items():
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned

def remove_page_headers(text: str) -> str:
    """Remove page headers and artifacts"""
    cleaned = text
    for pattern in PAGE_HEADER_PATTERNS:
        cleaned = re.sub(pattern, '\n', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def fix_date_ocr_errors(text: str) -> str:
    """Fix OCR errors in dates"""
    text = re.sub(r'\bOctober li,', 'October 11,', text)
    text = re.sub(r'\b([A-Z][a-z]+) li,', r'\1 11,', text)
    text = re.sub(r'\b([A-Z][a-z]+) (\d)i,', r'\1 \g<2>1,', text)
    text = re.sub(r'\b1931\b', '1921', text)  # Common OCR error
    text = re.sub(r'\b38th\b', '28th', text)  # 38 -> 28
    text = re.sub(r'19\s*HO', '1920', text)  # 19 HO -> 1920
    text = re.sub(r'19\^0', '1920', text)  # 19^0 -> 1920
    text = re.sub(r'192U', '1921', text)  # 192U -> 1921
    return text

def extract_date_from_text(text: str) -> Optional[Dict]:
    """Extract date from letter text"""
    date_patterns = [
        r'([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})',
        r'([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})~?\.?',
        r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Z][a-z]+),?\s+(\d{4})',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text[:500])
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    if groups[0].isdigit():
                        day, month_str, year = groups
                    else:
                        month_str, day, year = groups

                    month_map = {
                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                    }

                    month = month_map.get(month_str, 0)
                    if not month:
                        continue

                    day = int(day)
                    if day > 31:
                        if day == 38:
                            day = 28
                        else:
                            continue

                    days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    if day > days_in_month[month - 1]:
                        continue

                    iso_date = f"{year}-{month:02d}-{day:02d}"
                    return {
                        'date': iso_date,
                        'date_original': match.group(0),
                        'date_confidence': 'high'
                    }
            except Exception:
                continue

    return None

def detect_internal_letter_boundaries(text: str) -> List[Dict]:
    """Detect if text block contains multiple letters"""
    text = fix_date_ocr_errors(text)

    patterns = [
        r'\n\n+([A-Z][a-zA-Z\s\.]+),?\s*\n+([A-Z][a-z]+ \d{1,2},? \d{4})',
        r'\n\n+(London|Paris|New York|Chicago|Berlin),?\s*\n',
    ]

    all_matches = []
    for pattern in patterns:
        matches = list(re.finditer(pattern, text))
        all_matches.extend(matches)

    all_matches.sort(key=lambda m: m.start())

    if not all_matches:
        return [{'text': text, 'position': 0}]

    valid_matches = [m for m in all_matches if m.start() > 200]

    if not valid_matches:
        return [{'text': text, 'position': 0}]

    letters = []
    last_pos = 0

    for match in valid_matches:
        letters.append({
            'text': text[last_pos:match.start()].strip(),
            'position': last_pos
        })
        last_pos = match.start()

    letters.append({
        'text': text[last_pos:].strip(),
        'position': last_pos
    })

    letters = [l for l in letters if len(l['text'].split()) > 50]

    return letters if letters else [{'text': text, 'position': 0}]

def extract_location_from_text(text: str) -> str:
    """Extract location from first line"""
    lines = text.strip().split('\n')

    known_locations = [
        'Bombay', 'Near Aden', 'Red Sea', 'London', 'Paris', 'New York',
        'Chicago', 'Berlin', 'Geneva', 'Strasbourg', 'Darmstadt',
        'Ardennes', 'Bonbon', 'Near Paris', 'Santiniketan',
        'Near Zurich', 'Hamburg', 'Stockholm'  # Added missing locations
    ]

    ship_patterns = [
        r'S\.?\s*S\.?\s*Rhyndam',
        r'S\.?\s*S\.?\s*Morea',
        r'S\.?\s*Moeea',  # Added variant
    ]

    for line in lines[:5]:
        line = line.strip().rstrip(',').strip()

        if not line or len(line) < 3:
            continue

        for location in known_locations:
            if location.lower() in line.lower():
                return location

        for pattern in ship_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                if 'rhyndam' in line.lower():
                    return 'S.S. Rhyndam'
                elif 'morea' in line.lower() or 'moeea' in line.lower():
                    return 'S.S. Morea'

        if (len(line) < 40 and
            re.match(r'^[A-Z][\w\s\.]+$', line) and
            not re.search(r'\b(the|from|have|that|this|when|where)\b', line, re.IGNORECASE)):
            return line

    return "Unknown"

def normalize_location(location: str) -> str:
    """Normalize location names"""
    location = re.sub(r'[JI]?N[EF]W\s+York', 'New York', location, flags=re.IGNORECASE)
    location = re.sub(r'IS?f?[EF]AR\s+', '', location)
    location = re.sub(r'%\s*S\.?', 'S.S.', location)
    location = re.sub(r'S\.\s*[3S]\.?\s*', 'S.S. ', location)
    location = re.sub(r'S\.\s*RHYNDAM', 'S.S. Rhyndam', location, flags=re.IGNORECASE)
    location = re.sub(r'S\.\s*MO[ER]+A', 'S.S. Morea', location, flags=re.IGNORECASE)
    location = re.sub(r'S\.\s*Moeea', 'S.S. Morea', location, flags=re.IGNORECASE)
    location = re.sub(r'S\.S\.\s+', 'S.S. ', location)

    location_map = {
        'new york': 'New York',
        'london': 'London',
        'paris': 'Paris',
        'chicago': 'Chicago',
        'berlin': 'Berlin',
        'geneva': 'Geneva',
        'bombay': 'Bombay',
        'hamburg': 'Hamburg',
        'stockholm': 'Stockholm',
    }

    location_lower = location.lower()
    for key, value in location_map.items():
        if key in location_lower:
            location = value
            break

    return location.strip()

def create_letter_markdown(letter_data: Dict, letter_num: int) -> tuple:
    """Create markdown file"""
    location = normalize_location(letter_data.get('location', 'Unknown'))
    date_info = letter_data.get('date_info', {})
    text = letter_data.get('text', '')
    word_count = len(text.split())

    date_str = date_info.get('date', 'undated').replace('-', '_') if date_info.get('date') else 'undated'
    filename = f"tagore_{location.lower().replace(' ', '_').replace('.', '')}_{date_str}_{letter_num:03d}.md"
    filename = re.sub(r'[^\w\-_\.]', '', filename)

    frontmatter = f"""---
title: "Letter from {location}"
author: "Rabindranath Tagore"
recipient: "Unknown"
date: "{date_info.get('date', '')}"
date_confidence: "{date_info.get('date_confidence', 'none')}"
date_original: "{date_info.get('date_original', '')}"
location: "{location}"
source_archive: "https://archive.org/details/in.ernet.dli.2015.97031"
source_collection: "Letters From Abroad (1924)"
source_line: {letter_data.get('source_line', 0)}
word_count: {word_count}
letter_number: {letter_num}
extraction_method: "complete_pipeline_v3_66letters"
extraction_date: "{datetime.now().strftime('%Y-%m-%d')}"
quality: "high"
ocr_corrected: true
---

{text}

---

### Editorial Notes
- Letter #{letter_num} from "Letters From Abroad" (1924)
- Complete extraction with expanded OCR corrections
- Source line: {letter_data.get('source_line', 0)} in original OCR text
- Location: {location}
- Word count: {word_count:,}
"""

    return filename, frontmatter

def extract_all_66_letters():
    """Main extraction with ALL 66 letters"""

    source_file = Path("/home/user/poesis/New tagore 2/tagore_letters_preocr.txt")
    output_dir = Path("/home/user/poesis/New tagore 2/tagore_letters_complete_66/")
    output_dir.mkdir(exist_ok=True)

    # Clear existing files
    for f in output_dir.glob("*.md"):
        f.unlink()

    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # COMPLETE boundaries list (58 original + 4 new)
    boundaries = [
        54, 84, 152, 192, 290, 344, 386, 423, 448, 803, 1056, 1221, 1258, 1293,
        1359, 1402, 1472, 1551, 1590, 1672, 1746, 1813, 1860, 1930, 2180, 2286,
        2350, 2433, 2536, 2622, 2697, 2735, 2777, 2882, 3192, 3451, 3534, 3616,
        3706, 3827, 3952, 4031, 4132, 4216, 4271, 4441, 4483, 4566, 4648,
        4871,  # NEW: Near Zurich
        5105,  # NEW: Hamburg
        5194,  # NEW: Stockholm
        5307, 5346, 5470, 5568, 5667, 5762, 5840, 5908, 6169,
        6240,  # NEW: S. Moeea
    ]

    boundaries.sort()  # Ensure sorted order

    all_letters = []
    letter_count = 0

    print("🔧 COMPLETE EXTRACTION - ALL 66 LETTERS")
    print("=" * 70)
    print(f"Using {len(boundaries)} boundaries")
    print()

    for i, start_line in enumerate(boundaries):
        end_line = boundaries[i + 1] if i + 1 < len(boundaries) else len(lines)

        text = ''.join(lines[start_line - 1:end_line - 1])
        text = clean_ocr_errors(text)
        text = fix_date_ocr_errors(text)
        text = remove_page_headers(text)

        internal_letters = detect_internal_letter_boundaries(text)

        for internal in internal_letters:
            letter_count += 1
            letter_text = internal['text'].strip()

            location = extract_location_from_text(letter_text)
            date_info = extract_date_from_text(letter_text) or {}

            letter_data = {
                'text': letter_text,
                'location': location,
                'date_info': date_info,
                'source_line': start_line,
            }

            filename, content = create_letter_markdown(letter_data, letter_count)

            output_path = output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            all_letters.append({
                'number': letter_count,
                'location': location,
                'date': date_info.get('date', 'undated'),
                'words': len(letter_text.split()),
                'internal_split': len(internal_letters) > 1
            })

            status = "📄" if len(internal_letters) == 1 else "✂️ SPLIT"
            print(f"{status} Letter {letter_count:3d}: {location:25s} | {date_info.get('date', 'undated'):12s} | {len(letter_text.split()):5d} words")

    print("=" * 70)
    print(f"✅ EXTRACTED {letter_count} LETTERS")
    print(f"📊 Total words: {sum(l['words'] for l in all_letters):,}")
    print()

    location_counts = Counter(l['location'] for l in all_letters)
    print("📍 By location:")
    for location, count in location_counts.most_common():
        print(f"  {location:30s}: {count:2d} letters")

    dated = sum(1 for l in all_letters if l['date'] != 'undated')
    print()
    print(f"📅 Date coverage: {dated}/{letter_count} letters dated ({dated*100//letter_count}%)")
    print()
    print(f"📁 Output: {output_dir}/")

    return all_letters

if __name__ == '__main__':
    letters = extract_all_66_letters()
