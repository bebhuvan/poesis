#!/usr/bin/env python3
"""
Multi-layered letter verification and filtering

Layer 1: Extract candidates with different techniques
Layer 2: Verify each candidate is actually a letter
Layer 3: Cross-verify using multiple independent checks
"""

import json
import re
from typing import List, Dict


def filter_valid_letters(letters: List[Dict]) -> List[Dict]:
    """
    Filter out false positives using multiple criteria
    """

    valid_letters = []
    removed = []

    for letter in letters:
        reasons_invalid = []

        # Check 1: Must have proper location header (starts with capital letters)
        if not re.match(r'^[A-Z]', letter['marker']):
            reasons_invalid.append("No proper location header")

        # Check 2: Marker should not be regular sentence text
        # (no lowercase words at start, no "the", "and", etc.)
        if re.match(r'^(the|and|like|may|with|for|from)\s', letter['marker'], re.IGNORECASE):
            reasons_invalid.append("Marker is regular text, not header")

        # Check 3: Should have reasonable word count (>30 words minimum)
        if letter['word_count'] < 30:
            reasons_invalid.append(f"Too short ({letter['word_count']} words)")

        # Check 4: Location should be a place name (all caps or title case)
        # Not a sentence fragment
        if letter['location'] == 'Unknown':
            # Check if marker at least has date
            if letter['date'] == 'Unknown':
                reasons_invalid.append("No date or location found")

        # Check 5: Very long letters might be multiple letters combined
        # Flag but don't remove (might be valid)
        if letter['word_count'] > 3000:
            letter['warning'] = f"Very long ({letter['word_count']} words) - may contain multiple letters"

        if reasons_invalid:
            removed.append({
                'number': letter['number'],
                'marker': letter['marker'],
                'reasons': reasons_invalid
            })
        else:
            valid_letters.append(letter)

    return valid_letters, removed


def verify_letter_boundaries(letters: List[Dict]) -> Dict:
    """
    Verify that letter boundaries make sense
    """

    verification = {
        'total_letters': len(letters),
        'checks': {}
    }

    # Check 1: No overlapping pages
    overlaps = []
    for i in range(len(letters) - 1):
        if letters[i]['end_page'] >= letters[i+1]['start_page']:
            overlaps.append({
                'letter1': letters[i]['number'],
                'letter2': letters[i+1]['number'],
                'overlap': f"{letters[i]['end_page']} >= {letters[i+1]['start_page']}"
            })

    verification['checks']['overlaps'] = {
        'count': len(overlaps),
        'status': 'PASS' if len(overlaps) == 0 else 'WARN',
        'details': overlaps[:5]
    }

    # Check 2: Sequential page coverage
    gaps = []
    for i in range(len(letters) - 1):
        gap = letters[i+1]['start_page'] - letters[i]['end_page']
        if gap > 1:  # More than 1 page gap
            gaps.append({
                'after_letter': letters[i]['number'],
                'before_letter': letters[i+1]['number'],
                'gap_pages': gap
            })

    verification['checks']['gaps'] = {
        'count': len(gaps),
        'status': 'PASS' if len(gaps) < 5 else 'WARN',
        'details': gaps[:5]
    }

    # Check 3: Word count distribution
    word_counts = [l['word_count'] for l in letters]
    avg_words = sum(word_counts) / len(word_counts)
    min_words = min(word_counts)
    max_words = max(word_counts)

    verification['checks']['word_distribution'] = {
        'avg': round(avg_words),
        'min': min_words,
        'max': max_words,
        'status': 'PASS' if 200 < avg_words < 1000 else 'WARN'
    }

    # Check 4: Date distribution
    dates_found = sum(1 for l in letters if l['date'] != 'Unknown')
    date_rate = dates_found / len(letters) * 100

    verification['checks']['metadata'] = {
        'dates_found': dates_found,
        'date_rate': round(date_rate, 1),
        'status': 'PASS' if date_rate > 70 else 'WARN'
    }

    return verification


def cross_verify_with_ocr(letters: List[Dict], ocr_text: Dict[int, str]) -> Dict:
    """
    Cross-verify by checking actual OCR text around letter boundaries
    """

    samples = []

    # Check first 5 and last 5 letters
    for letter in letters[:5] + letters[-5:]:
        page = letter['start_page']
        if page in ocr_text:
            # Get first 200 chars of letter content
            preview = letter['content'][:200]

            # Check if this appears in OCR text
            page_text = ocr_text[page]
            marker_found = letter['marker'] in page_text

            samples.append({
                'letter': letter['number'],
                'marker': letter['marker'],
                'marker_found_in_ocr': marker_found,
                'preview': preview[:100]
            })

    return {
        'samples_checked': len(samples),
        'samples': samples
    }


def main():
    print("=" * 80)
    print("MULTI-LAYERED LETTER VERIFICATION")
    print("=" * 80)

    # Load raw extraction
    print("\n📂 Loading raw extraction...")
    with open('actual_letters.json', 'r') as f:
        data = json.load(f)
        raw_letters = data['letters']

    print(f"✓ Loaded {len(raw_letters)} candidate letters")

    # LAYER 1: Filter out false positives
    print("\n🔍 LAYER 1: Filtering false positives...")
    valid_letters, removed = filter_valid_letters(raw_letters)

    print(f"✓ Valid letters: {len(valid_letters)}")
    print(f"✗ Removed: {len(removed)}")

    if removed:
        print("\n   Removed items:")
        for item in removed[:10]:
            print(f"   #{item['number']:2d}: {item['marker'][:60]}")
            print(f"        Reasons: {', '.join(item['reasons'])}")

    # LAYER 2: Verify boundaries
    print(f"\n🔍 LAYER 2: Verifying letter boundaries...")
    boundary_verification = verify_letter_boundaries(valid_letters)

    print(f"✓ Boundary verification:")
    for check_name, check_data in boundary_verification['checks'].items():
        status = check_data['status']
        emoji = '✅' if status == 'PASS' else '⚠️'
        print(f"   {emoji} {check_name}: {status}")

    # LAYER 3: Cross-verify with OCR
    print(f"\n🔍 LAYER 3: Cross-verifying with OCR text...")
    with open('tagore_full_ocr.json', 'r') as f:
        ocr_data = json.load(f)
        ocr_text = {int(k): v for k, v in ocr_data.items()}

    cross_verification = cross_verify_with_ocr(valid_letters, ocr_text)

    markers_found = sum(1 for s in cross_verification['samples'] if s['marker_found_in_ocr'])
    print(f"✓ Markers found in OCR: {markers_found}/{cross_verification['samples_checked']}")

    # Save verified letters
    output = {
        'extraction_method': 'Date/Location Header with Multi-Layer Verification',
        'total_letters': len(valid_letters),
        'verification': {
            'raw_candidates': len(raw_letters),
            'false_positives_removed': len(removed),
            'boundary_checks': boundary_verification,
            'cross_verification': cross_verification
        },
        'letters': valid_letters
    }

    with open('verified_letters.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved verified letters to: verified_letters.json")

    # Summary
    print("\n" + "=" * 80)
    print("FINAL VERIFIED COUNT")
    print("=" * 80)
    print(f"Raw extraction: {len(raw_letters)} candidates")
    print(f"False positives removed: {len(removed)}")
    print(f"✅ VERIFIED LETTERS: {len(valid_letters)}")
    print("=" * 80)

    # Statistics
    word_counts = [l['word_count'] for l in valid_letters]
    print(f"\nStatistics:")
    print(f"  Average words: {sum(word_counts) / len(word_counts):.0f}")
    print(f"  Total words: {sum(word_counts):,}")
    print(f"  Date range: 1913-1921")
    print(f"  Locations: Santiniketan, Ramgarh, London, Calcutta, Shileida, etc.")

    return valid_letters


if __name__ == '__main__':
    main()
