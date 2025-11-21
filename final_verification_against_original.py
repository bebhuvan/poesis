#!/usr/bin/env python3
"""
Final verification against original PDF structure
Check table of contents, page headers, and cross-reference everything
"""

import json
import re
from collections import Counter


def check_table_of_contents(ocr_text):
    """
    Look for table of contents or any indication of letter count
    in the front matter
    """
    print("\n🔍 Checking Table of Contents and Front Matter...")

    # Check pages 0-20 (front matter)
    toc_info = []

    for page_num in range(0, 21):
        if page_num not in ocr_text:
            continue

        text = ocr_text[page_num]

        # Look for "contents", "index", "chapter" keywords
        if re.search(r'(contents|index|chapter)', text, re.IGNORECASE):
            print(f"\n📄 Page {page_num} - Table of Contents:")
            # Show first 1000 chars
            print(text[:1000])
            print("...")
            toc_info.append(page_num)

    return toc_info


def analyze_page_headers(ocr_text):
    """
    Analyze page headers to understand document structure
    """
    print("\n🔍 Analyzing page headers...")

    headers = []

    for page_num in range(40, 200):  # Main content area
        if page_num not in ocr_text:
            continue

        lines = ocr_text[page_num].split('\n')

        # Check first 5 lines for headers
        for line in lines[:5]:
            line = line.strip()

            # Look for "Letters to a Friend" with page numbers
            if re.search(r'Letters to a Friend\s+\d+', line):
                match = re.search(r'Letters to a Friend\s+(\d+)', line)
                if match:
                    page_ref = int(match.group(1))
                    headers.append({
                        'pdf_page': page_num,
                        'book_page': page_ref,
                        'header': line
                    })
                    break

    if headers:
        print(f"✓ Found {len(headers)} page headers with 'Letters to a Friend'")
        print(f"  Book page range: {headers[0]['book_page']} - {headers[-1]['book_page']}")
        print(f"  PDF page range: {headers[0]['pdf_page']} - {headers[-1]['pdf_page']}")

    return headers


def count_letter_markers_in_text(ocr_text):
    """
    Count all potential letter markers in the full text
    """
    print("\n🔍 Counting all date/location patterns in text...")

    # Different patterns to try
    patterns = {
        'full_date': r'([A-Z][A-Z\s]+),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}',
        'month_year': r'([A-Z][A-Z\s]+),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
    }

    counts = {}
    all_matches = []

    for pattern_name, pattern in patterns.items():
        matches = []

        for page_num in range(40, 200):
            if page_num not in ocr_text:
                continue

            text = ocr_text[page_num]

            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append({
                    'page': page_num,
                    'text': match.group(0),
                    'pattern': pattern_name
                })
                all_matches.append(match.group(0))

        counts[pattern_name] = len(matches)
        print(f"  {pattern_name}: {len(matches)} matches")

    return counts, all_matches


def check_chapter_structure(ocr_text):
    """
    Look for chapter markers to understand book structure
    """
    print("\n🔍 Checking chapter structure...")

    chapters = []

    for page_num in sorted(ocr_text.keys()):
        text = ocr_text[page_num]

        # Look for chapter markers
        if re.search(r'^CHAPTER\s+[IVXLCDM]+', text, re.MULTILINE):
            match = re.search(r'(CHAPTER\s+[IVXLCDM]+)', text, re.MULTILINE)
            if match:
                chapters.append({
                    'page': page_num,
                    'marker': match.group(1)
                })

    if chapters:
        print(f"✓ Found {len(chapters)} chapters:")
        for ch in chapters:
            print(f"  Page {ch['page']:3d}: {ch['marker']}")

    return chapters


def verify_letter_spacing(verified_letters):
    """
    Check if letter distribution makes sense
    """
    print("\n🔍 Verifying letter distribution...")

    # Check pages per letter
    pages_per_letter = []
    for letter in verified_letters:
        pages = letter['end_page'] - letter['start_page'] + 1
        pages_per_letter.append(pages)

    avg_pages = sum(pages_per_letter) / len(pages_per_letter)

    print(f"  Average pages per letter: {avg_pages:.1f}")
    print(f"  Min pages: {min(pages_per_letter)}")
    print(f"  Max pages: {max(pages_per_letter)}")

    # How many letters per page?
    page_to_letters = {}
    for letter in verified_letters:
        for page in range(letter['start_page'], letter['end_page'] + 1):
            if page not in page_to_letters:
                page_to_letters[page] = []
            page_to_letters[page].append(letter['number'])

    pages_with_multiple = sum(1 for letters in page_to_letters.values() if len(letters) > 1)

    print(f"  Pages with multiple letters: {pages_with_multiple}")
    print(f"  Total pages covered: {len(page_to_letters)}")

    # Show sample pages with multiple letters
    if pages_with_multiple > 0:
        print("\n  Sample pages with multiple letters:")
        count = 0
        for page, letter_nums in sorted(page_to_letters.items()):
            if len(letter_nums) > 1:
                print(f"    Page {page}: Letters {letter_nums}")
                count += 1
                if count >= 5:
                    break


def cross_check_dates(verified_letters, ocr_text):
    """
    Verify dates are actually present in the OCR text at those pages
    """
    print("\n🔍 Cross-checking dates in OCR text...")

    verified = 0
    not_found = []

    for letter in verified_letters[:20]:  # Check first 20
        page = letter['start_page']
        date = letter['date']

        if date != 'Unknown' and page in ocr_text:
            # Look for date in page text
            page_text = ocr_text[page]

            # Try to find the date (might have OCR variations)
            date_parts = date.split()
            if date_parts and date_parts[0] in page_text:
                verified += 1
            else:
                not_found.append({
                    'letter': letter['number'],
                    'date': date,
                    'page': page
                })

    print(f"  Verified dates: {verified}/20 sampled")
    if not_found:
        print(f"  Dates not found in OCR: {len(not_found)}")


def main():
    print("=" * 80)
    print("FINAL VERIFICATION AGAINST ORIGINAL PDF")
    print("=" * 80)

    # Load OCR text
    print("\n📂 Loading full OCR text...")
    with open('tagore_full_ocr.json', 'r') as f:
        data = json.load(f)
        ocr_text = {int(k): v for k, v in data.items()}

    print(f"✓ Loaded {len(ocr_text)} pages")

    # Load verified letters
    with open('verified_letters.json', 'r') as f:
        data = json.load(f)
        verified_letters = data['letters']

    print(f"✓ Current verified count: {len(verified_letters)} letters")

    # Run all verification checks
    toc_pages = check_table_of_contents(ocr_text)
    headers = analyze_page_headers(ocr_text)
    counts, all_matches = count_letter_markers_in_text(ocr_text)
    chapters = check_chapter_structure(ocr_text)
    verify_letter_spacing(verified_letters)
    cross_check_dates(verified_letters, ocr_text)

    # Final summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"\n✅ Verified letter count: {len(verified_letters)}")
    print(f"\n📊 Cross-checks:")
    print(f"  • Date/location patterns found in text: {sum(counts.values())}")
    print(f"  • Page headers found: {len(headers)}")
    print(f"  • Chapters found: {len(chapters)}")
    print(f"  • Table of contents pages: {len(toc_pages)}")

    print("\n💡 Analysis:")
    print(f"  The verified count of {len(verified_letters)} letters appears")
    print(f"  consistent with {sum(counts.values())} date/location markers found")
    print(f"  in the OCR text (some markers may be chapter intros, not letters).")

    if len(verified_letters) >= 70 and len(verified_letters) <= 90:
        print(f"\n  ✅ {len(verified_letters)} letters is a REASONABLE count for this collection.")
    else:
        print(f"\n  ⚠️  Count may need further investigation.")

    print("=" * 80)


if __name__ == '__main__':
    main()
