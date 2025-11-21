#!/usr/bin/env python3
"""
Comprehensive letter counting using multiple detection methods
Cross-validates different approaches to find true letter count
"""

import re
from collections import defaultdict

def method1_location_date_pairs(text):
    """Method 1: Location + Date pattern (original approach)"""
    pattern = r'(?:^|\n)([A-Z][^\n]{2,60}?),?\s*\n\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[^\n]{0,40})'
    matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
    return matches

def method2_location_only(text):
    """Method 2: Just location headers (for undated letters)"""
    # Common locations + ship names
    locations = [
        'Bombay', 'Near Aden', 'Red Sea', 'London', 'LONDON', 'Paris', 'Near Paris',
        'Ardennes', 'Santiniketan', 'Bonbon', 'New York', 'NEW York', 'JNEW York',
        'ISfEAR New York', 'Chicago', 'CHICAGO', 'Berlin', 'Geneva', 'Strasbourg',
        'Darmstadt', 'Wellesley, Mass', 'Houston, Texas',
        'S. S. Rhyndam', 'S. 3. Morea', 'S. S. MOREA', 'S. Moeea',
        'AUTOUR DU Monde', 'AuTouR DU Monde', 'Autour, DU Monde'
    ]

    found = []
    for loc in locations:
        # Find all occurrences
        pattern = rf'(?:^|\n)({re.escape(loc)})[,.\s]*\n'
        matches = re.findall(pattern, text, re.MULTILINE)
        for m in matches:
            found.append(m)

    return found

def method3_page_analysis(text):
    """Method 3: Analyze page structure and find letter starts"""
    # Look for patterns that indicate new letter start:
    # - Location name at start of line
    # - Followed by date OR by letter content
    # - After clear letter ending (signature, closing)

    lines = text.split('\n')
    potential_starts = []

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Check if line looks like location header
        if line and line[0].isupper() and (line.endswith(',') or line.endswith('.')):
            # Check what follows
            next_line = lines[i+1].strip() if i+1 < len(lines) else ""

            # Is next line a date?
            has_date = any(month in next_line for month in [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ])

            # Or is it the start of letter content?
            is_content = next_line and next_line[0].isupper() and len(next_line) > 20

            if has_date or is_content:
                potential_starts.append((i, line, next_line))

    return potential_starts

def method4_manual_markers(text):
    """Method 4: Known specific markers from manual review"""
    # List specific known letter start markers
    markers = [
        'Bombay,',
        'Near Aden,',
        'Red Sea,',
        'London,',
        'Paris,',
        'Near Paris,',
        'Ardennes,',
        'Santiniketan,',
        'Bonbon,',
        'Paeis,',
        'New York,',
        'Wellesley, Mass',
        'Houston, Texas',
        'Chicago,',
        'Berlin,',
        'Geneva,',
        'Strasbourg,',
        'Darmstadt,',
        'S. S. Rhyndam',
        'S. 3. Morea',
        'S. S. MOREA',
        'S. Moeea',
        'AUTOUR DU Monde',
        'AuTouR DU Monde',
    ]

    found = defaultdict(int)
    for marker in markers:
        count = len(re.findall(re.escape(marker), text))
        if count > 0:
            found[marker] = count

    return found

def main():
    with open('tagore_letters_preocr.txt', 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    # Find letter section
    start_idx = full_text.find("Bombay,")
    text = full_text[start_idx:] if start_idx != -1 else full_text

    print("=" * 70)
    print("COMPREHENSIVE LETTER COUNT ANALYSIS")
    print("=" * 70)

    # Method 1: Location + Date
    print("\n📍 Method 1: Location + Date Pattern")
    m1 = method1_location_date_pairs(text)
    print(f"Found: {len(m1)} letter markers")
    for i, (loc, date) in enumerate(m1[:10], 1):
        print(f"  {i}. {loc[:30]:30s} | {date[:30]}")
    if len(m1) > 10:
        print(f"  ... and {len(m1)-10} more")

    # Method 2: Location only
    print("\n📍 Method 2: Known Locations (all occurrences)")
    m2 = method2_location_only(text)
    print(f"Found: {len(m2)} location markers")
    print(f"Unique locations: {len(set(m2))}")

    # Method 3: Page structure
    print("\n📍 Method 3: Page Structure Analysis")
    m3 = method3_page_analysis(text)
    print(f"Found: {len(m3)} potential letter starts")

    # Method 4: Manual markers
    print("\n📍 Method 4: Specific Known Markers")
    m4 = method4_manual_markers(text)
    print(f"Found {len(m4)} unique marker types:")
    total_m4 = sum(m4.values())
    for marker, count in sorted(m4.items(), key=lambda x: -x[1]):
        print(f"  {marker:30s}: {count:2d} occurrences")
    print(f"Total marker occurrences: {total_m4}")

    # Cross-analysis
    print("\n" + "=" * 70)
    print("CROSS-VALIDATION")
    print("=" * 70)
    print(f"Method 1 (Loc+Date):        {len(m1)} letters")
    print(f"Method 2 (Known Locs):      {len(m2)} markers")
    print(f"Method 3 (Page Structure):  {len(m3)} starts")
    print(f"Method 4 (Manual Count):    {total_m4} markers")

    # Best estimate
    print("\n🎯 ESTIMATED LETTER COUNT")

    # Group Method 4 by unique letters (some markers appear multiple times)
    # Count unique location-date combinations
    unique_letters = set()

    # From Method 1 (most reliable for dated letters)
    for loc, date in m1:
        unique_letters.add((loc.strip(), date.strip()[:20]))

    # Add undated ship letters manually
    ship_variants = ['S. S. Rhyndam', 'S. 3. Morea', 'S. S. MOREA', 'S. Moeea']
    for ship in ship_variants:
        if ship in m4:
            # Each occurrence is likely a separate letter
            for i in range(m4[ship]):
                unique_letters.add((ship, f"undated_{i}"))

    # Add other known undated letters
    undated_locs = ['Red Sea', 'Near Aden']
    for loc in undated_locs:
        marker = loc + ','
        if marker in m4:
            for i in range(m4[marker]):
                unique_letters.add((loc, f"undated_{i}"))

    print(f"Estimated unique letters: {len(unique_letters)}")

    # Detailed breakdown
    print("\n📊 BREAKDOWN BY LOCATION TYPE")
    locations_with_dates = len([l for l, d in unique_letters if not d.startswith('undated')])
    locations_undated = len([l for l, d in unique_letters if d.startswith('undated')])
    print(f"  Letters with dates: {locations_with_dates}")
    print(f"  Undated letters:    {locations_undated}")
    print(f"  TOTAL:              {len(unique_letters)}")

    # Compare with our extraction
    print("\n🔍 COMPARISON WITH EXTRACTION")
    print(f"  Current extraction: 49 letters")
    print(f"  Method 1 count:     {len(m1)} letters")
    print(f"  Estimated total:    {len(unique_letters)} letters")
    print(f"  Difference:         {abs(49 - len(unique_letters))} letters")

    if len(unique_letters) > 49:
        print(f"\n⚠️  Potentially missing {len(unique_letters) - 49} letters!")
    elif len(unique_letters) < 49:
        print(f"\n⚠️  May have over-counted by {49 - len(unique_letters)} letters")
    else:
        print(f"\n✅ Count matches extraction!")

if __name__ == "__main__":
    main()
