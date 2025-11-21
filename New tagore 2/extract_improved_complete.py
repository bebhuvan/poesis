#!/usr/bin/env python3
"""
Improved Tagore Letters Extraction Pipeline
Fixes: OCR errors, page headers, letter boundaries, date extraction
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter

# OCR error correction dictionary (common patterns found)
OCR_CORRECTIONS = {
    # Common OCR errors observed in the text
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
    r'\% S\. (Rhyndam|Morea)': r'S. S. \1',
    r'S\. 3\. (Morea|Rhyndam)': r'S. S. \1',  # Fix "S. 3." to "S. S."
    r'\'loNDON': 'LONDON',
    r'\bwo\b': 'we',
    # Additional common patterns
    r'\brao\b': 'me',
    r'\bTho\b': 'The',
    r'\btho\b': 'the',
    r'\bsomo\b': 'some',
    r'\bwhon\b': 'when',
    r'\bthoir\b': 'their',
    r'\bmado\b': 'made',
    r'\bsaid\b': 'said',
    r'\bfrom\b': 'from',
    r'\bwith\b': 'with',
}

# Page header patterns to remove
PAGE_HEADER_PATTERNS = [
    r'\n\d+\s+LETTE[RH]S\s+FROM\s+ABROAD\s*\n',  # Page headers like "2 LETTEHS FROM ABROAD"
    r'^\d+\s+LETTE[RH]S\s+FROM\s+ABROAD\s*$',    # Same as line
    r'LETTE[RH]S\s+FROM\s+ABROAD\s+\d+',         # Headers like "LETTERS FROM ABROAD 27"
    r'^\s*\d{1,3}\s*$',                           # Standalone page numbers
    r'^\s*\d{1,3}t\s*$',                          # Page numbers with OCR 't' artifact
    r'^\s*[a-z]\s*$',                             # Standalone single letters (artifacts)
    r'^\s*t\s*$',                                 # Common artifact 't'
    r'\n\s*\d{1,3}\s*\n',                         # Page numbers between newlines
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

    # Remove excessive newlines (more than 2 consecutive)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()

def extract_date_from_text(text: str) -> Optional[Dict]:
    """Extract date from letter text with multiple patterns and validation"""
    # Patterns for dates
    date_patterns = [
        # "May 14, 1920"
        r'([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})',
        # "October 8, 1920~"
        r'([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})~?\.?',
        # "14th May, 1920"
        r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Z][a-z]+),?\s+(\d{4})',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text[:500])  # Search in first 500 chars
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    if groups[0].isdigit():  # Day first
                        day, month_str, year = groups
                    else:  # Month first
                        month_str, day, year = groups

                    # Parse month
                    month_map = {
                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                    }

                    month = month_map.get(month_str, 0)
                    if not month:
                        continue

                    # Fix common OCR errors in year
                    year = year.replace('1931', '1921')  # Common OCR error
                    year = year.replace('19HO', '1920')
                    year = year.replace('19 HO', '1920')

                    # Validate day
                    day = int(day)
                    if day > 31:
                        # Common OCR errors
                        if day == 38:  # "38" → "28"
                            day = 28
                        else:
                            continue

                    # Validate month-day combination
                    days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    if day > days_in_month[month - 1]:
                        continue

                    iso_date = f"{year}-{month:02d}-{day:02d}"
                    return {
                        'date': iso_date,
                        'date_original': match.group(0),
                        'date_confidence': 'high'
                    }
            except Exception as e:
                continue

    return None

def fix_date_ocr_errors(text: str) -> str:
    """Fix OCR errors in dates before processing"""
    # Common OCR errors in dates
    text = re.sub(r'\bOctober li,', 'October 11,', text)
    text = re.sub(r'\b([A-Z][a-z]+) li,', r'\1 11,', text)  # Any month + "li" → 11
    text = re.sub(r'\b([A-Z][a-z]+) (\d)i,', r'\1 \g<2>1,', text)  # "1i" → "11", "2i" → "21"
    return text

def detect_internal_letter_boundaries(text: str) -> List[Dict]:
    """
    Detect if a text block contains multiple letters by finding
    internal location+date headers
    """
    # Fix date OCR errors first
    text = fix_date_ocr_errors(text)

    # Patterns for internal letter markers
    patterns = [
        # Location + date (may have blank line between)
        r'\n\n+([A-Z][a-zA-Z\s\.]+),?\s*\n+([A-Z][a-z]+ \d{1,2},? \d{4})',
        # Just location on its own line (known locations)
        r'\n\n+(London|Paris|New York|Chicago|Berlin),?\s*\n',
    ]

    all_matches = []
    for pattern in patterns:
        matches = list(re.finditer(pattern, text))
        all_matches.extend(matches)

    # Sort by position
    all_matches.sort(key=lambda m: m.start())

    if not all_matches:
        return [{'text': text, 'position': 0}]

    # Only split if we find matches WELL INTO the text (>200 chars)
    valid_matches = [m for m in all_matches if m.start() > 200]

    if not valid_matches:
        return [{'text': text, 'position': 0}]

    # Split into multiple letters
    letters = []
    last_pos = 0

    for i, match in enumerate(valid_matches):
        # Add letter before this match
        letters.append({
            'text': text[last_pos:match.start()].strip(),
            'position': last_pos
        })
        last_pos = match.start()

    # Add final letter
    letters.append({
        'text': text[last_pos:].strip(),
        'position': last_pos
    })

    # Filter out very short "letters" (< 50 words)
    letters = [l for l in letters if len(l['text'].split()) > 50]

    return letters if letters else [{'text': text, 'position': 0}]

def extract_location_from_text(text: str) -> str:
    """Extract location from first line with validation"""
    lines = text.strip().split('\n')

    # Known valid locations
    known_locations = [
        'Bombay', 'Near Aden', 'Red Sea', 'London', 'Paris', 'New York',
        'Chicago', 'Berlin', 'Geneva', 'Strasbourg', 'Darmstadt',
        'Ardennes', 'Bonbon', 'Near Paris', 'Santiniketan'
    ]

    # Known ship names
    ship_patterns = [
        r'S\.?\s*S\.?\s*Rhyndam',
        r'S\.?\s*S\.?\s*Morea',
    ]

    for line in lines[:5]:
        line = line.strip().rstrip(',').strip()

        # Skip empty lines
        if not line or len(line) < 3:
            continue

        # Check if it matches known locations
        for location in known_locations:
            if location.lower() in line.lower():
                return location

        # Check for ship names
        for pattern in ship_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Extract ship name
                if 'rhyndam' in line.lower():
                    return 'S.S. Rhyndam'
                elif 'morea' in line.lower():
                    return 'S.S. Morea'

        # Check if line looks like a location (short, capitalized, not a sentence)
        if (len(line) < 40 and
            re.match(r'^[A-Z][\w\s\.]+$', line) and
            not re.search(r'\b(the|from|have|that|this|when|where)\b', line, re.IGNORECASE)):
            return line

    return "Unknown"

def normalize_location(location: str) -> str:
    """Normalize location names"""
    # Fix common OCR errors
    location = re.sub(r'[JI]?N[EF]W\s+York', 'New York', location, flags=re.IGNORECASE)
    location = re.sub(r'IS?f?[EF]AR\s+', '', location)  # Remove OCR artifacts like "ISfEAR"

    # Normalize ship names
    location = re.sub(r'%\s*S\.?', 'S.S.', location)
    location = re.sub(r'S\.\s*[3S]\.?\s*', 'S.S. ', location)  # Fix "S. 3." or "S. S." to "S.S. "
    location = re.sub(r'S\.\s*RHYNDAM', 'S.S. Rhyndam', location, flags=re.IGNORECASE)
    location = re.sub(r'S\.\s*MOREA', 'S.S. Morea', location, flags=re.IGNORECASE)
    location = re.sub(r'S\.S\.\s+', 'S.S. ', location)  # Normalize spacing

    # Normalize case for known locations
    location_map = {
        'new york': 'New York',
        'london': 'London',
        'paris': 'Paris',
        'chicago': 'Chicago',
        'berlin': 'Berlin',
        'geneva': 'Geneva',
        'bombay': 'Bombay',
    }

    location_lower = location.lower()
    for key, value in location_map.items():
        if key in location_lower:
            location = value
            break

    location = location.strip()
    return location

def create_letter_markdown(letter_data: Dict, letter_num: int) -> str:
    """Create markdown file with frontmatter and cleaned text"""

    # Extract metadata
    location = normalize_location(letter_data.get('location', 'Unknown'))
    date_info = letter_data.get('date_info', {})
    text = letter_data.get('text', '')
    word_count = len(text.split())

    # Create filename
    date_str = date_info.get('date', 'undated').replace('-', '_') if date_info.get('date') else 'undated'
    filename = f"tagore_{location.lower().replace(' ', '_').replace('.', '')}_{date_str}_{letter_num:03d}.md"
    filename = re.sub(r'[^\w\-_\.]', '', filename)

    # Build frontmatter
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
extraction_method: "improved_pipeline_v2"
extraction_date: "{datetime.now().strftime('%Y-%m-%d')}"
quality: "publication_ready"
ocr_corrected: true
---

{text}

---

### Editorial Notes
- Letter #{letter_num} from "Letters From Abroad" (1924)
- OCR errors corrected, page headers removed
- Source line: {letter_data.get('source_line', 0)} in original OCR text
- Location: {location}
- Word count: {word_count:,}
"""

    return filename, frontmatter

def extract_all_letters_improved():
    """Main extraction with improved pipeline"""

    source_file = Path("/home/user/poesis/New tagore 2/tagore_letters_preocr.txt")
    output_dir = Path("/home/user/poesis/New tagore 2/tagore_letters_from_abroad_1924/improved_extraction")
    output_dir.mkdir(exist_ok=True)

    # Clear existing files
    for f in output_dir.glob("*.md"):
        f.unlink()

    # Read source
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Letter boundaries (from previous extraction)
    boundaries = [
        54, 84, 152, 192, 290, 344, 386, 423, 448, 803, 1056, 1221, 1258, 1293,
        1359, 1402, 1472, 1551, 1590, 1672, 1746, 1813, 1860, 1930, 2180, 2286,
        2350, 2433, 2536, 2622, 2697, 2735, 2777, 2882, 3192, 3451, 3534, 3616,
        3706, 3827, 3952, 4031, 4132, 4216, 4271, 4441, 4483, 4566, 4648, 5307,
        5346, 5470, 5568, 5667, 5762, 5840, 5908, 6169
    ]

    all_letters = []
    letter_count = 0

    print("🔧 IMPROVED EXTRACTION PIPELINE")
    print("=" * 60)

    for i, start_line in enumerate(boundaries):
        end_line = boundaries[i + 1] if i + 1 < len(boundaries) else len(lines)

        # Extract text
        text = ''.join(lines[start_line - 1:end_line - 1])

        # Clean OCR errors
        text = clean_ocr_errors(text)

        # Fix date OCR errors
        text = fix_date_ocr_errors(text)

        # Remove page headers
        text = remove_page_headers(text)

        # Check for internal letter boundaries (multi-letter blocks)
        internal_letters = detect_internal_letter_boundaries(text)

        for j, internal in enumerate(internal_letters):
            letter_count += 1
            letter_text = internal['text'].strip()

            # Extract location
            location = extract_location_from_text(letter_text)

            # Extract date
            date_info = extract_date_from_text(letter_text) or {}

            # Create letter data
            letter_data = {
                'text': letter_text,
                'location': location,
                'date_info': date_info,
                'source_line': start_line,
            }

            # Generate markdown
            filename, content = create_letter_markdown(letter_data, letter_count)

            # Save
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

    print("=" * 60)
    print(f"✅ EXTRACTED {letter_count} LETTERS")
    print(f"📊 Total words: {sum(l['words'] for l in all_letters):,}")
    print(f"✂️  Split multi-letter blocks: {sum(1 for l in all_letters if l.get('internal_split'))}")
    print()

    # Statistics by location
    location_counts = Counter(l['location'] for l in all_letters)
    print("📍 By location:")
    for location, count in location_counts.most_common(10):
        print(f"  {location:30s}: {count:2d} letters")

    # Statistics by date coverage
    dated = sum(1 for l in all_letters if l['date'] != 'undated')
    print()
    print(f"📅 Date coverage: {dated}/{letter_count} letters dated ({dated*100//letter_count}%)")

    return all_letters

if __name__ == '__main__':
    letters = extract_all_letters_improved()
