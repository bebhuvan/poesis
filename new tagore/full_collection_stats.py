#!/usr/bin/env python3
"""
Complete Collection Statistics and Quality Analysis
"""
import json
from pathlib import Path
from collections import defaultdict

def analyze_full_collection():
    """Analyze all 168 pages"""

    print("=" * 80)
    print("COMPLETE COLLECTION ANALYSIS - All 168 Pages")
    print("=" * 80)
    print()

    # Read all metadata
    stats = {
        'total_pages': 0,
        'blank_pages': 0,
        'content_pages': 0,
        'total_chars': 0,
        'total_words': 0,
        'confidence_scores': [],
        'quality_scores': [],
        'high_quality': 0,
        'medium_quality': 0,
        'low_quality': 0
    }

    confidence_bins = defaultdict(int)
    pages_by_quality = {'high': [], 'medium': [], 'low': []}

    for page_num in range(168):
        try:
            # Read metadata
            with open(f'metadata/page_{page_num:04d}.json') as f:
                metadata = json.load(f)

            # Read text
            text = Path(f'final_text/page_{page_num:04d}.txt').read_text()

            stats['total_pages'] += 1

            # Content analysis
            char_count = len(text)
            word_count = len(text.split())

            stats['total_chars'] += char_count
            stats['total_words'] += word_count

            if char_count < 10:
                stats['blank_pages'] += 1
            else:
                stats['content_pages'] += 1

            # Quality metrics
            confidence = metadata['consensus']['confidence']
            quality = metadata['quality_verification']['overall_score']

            stats['confidence_scores'].append(confidence)
            stats['quality_scores'].append(quality)

            # Categorize
            if confidence > 0.8 and quality > 0.9:
                stats['high_quality'] += 1
                pages_by_quality['high'].append(page_num)
                confidence_bins['80-100%'] += 1
            elif confidence > 0.5 and quality > 0.75:
                stats['medium_quality'] += 1
                pages_by_quality['medium'].append(page_num)
                confidence_bins['50-80%'] += 1
            else:
                stats['low_quality'] += 1
                pages_by_quality['low'].append(page_num)
                if confidence > 0.2:
                    confidence_bins['20-50%'] += 1
                else:
                    confidence_bins['0-20%'] += 1

        except Exception as e:
            print(f"Error processing page {page_num}: {e}")

    # Calculate averages
    avg_confidence = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
    avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores'])

    # Display results
    print("OVERVIEW")
    print("-" * 80)
    print(f"Total Pages:        {stats['total_pages']}")
    print(f"Content Pages:      {stats['content_pages']} ({stats['content_pages']/stats['total_pages']*100:.1f}%)")
    print(f"Blank/Minimal:      {stats['blank_pages']} ({stats['blank_pages']/stats['total_pages']*100:.1f}%)")
    print()
    print(f"Total Characters:   {stats['total_chars']:,}")
    print(f"Total Words:        {stats['total_words']:,}")
    print(f"Avg Words/Page:     {stats['total_words']/stats['content_pages']:.0f} (content pages only)")
    print()

    print("QUALITY DISTRIBUTION")
    print("-" * 80)
    print(f"High Quality:       {stats['high_quality']:3d} pages ({stats['high_quality']/stats['total_pages']*100:.1f}%)")
    print(f"Medium Quality:     {stats['medium_quality']:3d} pages ({stats['medium_quality']/stats['total_pages']*100:.1f}%)")
    print(f"Low Quality:        {stats['low_quality']:3d} pages ({stats['low_quality']/stats['total_pages']*100:.1f}%)")
    print()

    print("CONFIDENCE DISTRIBUTION")
    print("-" * 80)
    for range_name, count in sorted(confidence_bins.items()):
        print(f"{range_name:12s}  {count:3d} pages ({count/stats['total_pages']*100:.1f}%)")
    print()

    print("AVERAGE SCORES")
    print("-" * 80)
    print(f"OCR Confidence:     {avg_confidence:.2%}")
    print(f"Quality Score:      {avg_quality:.2%}")
    print()

    # Best pages
    top_pages = sorted(
        [(i, c) for i, c in enumerate(stats['confidence_scores'])],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    print("TOP 10 PAGES (Highest Confidence)")
    print("-" * 80)
    for page, conf in top_pages:
        if conf > 0:
            words = len(Path(f'final_text/page_{page:04d}.txt').read_text().split())
            print(f"Page {page:3d}: {conf:.2%} confidence ({words:4d} words)")
    print()

    # Pages needing review
    review_pages = [
        i for i, c in enumerate(stats['confidence_scores'])
        if c < 0.7 and len(Path(f'final_text/page_{i:04d}.txt').read_text()) > 50
    ]

    if review_pages:
        print(f"CONTENT PAGES NEEDING REVIEW ({len(review_pages)})")
        print("-" * 80)
        for page in review_pages[:10]:
            conf = stats['confidence_scores'][page]
            words = len(Path(f'final_text/page_{page:04d}.txt').read_text().split())
            print(f"Page {page:3d}: {conf:.2%} confidence ({words:4d} words)")
        if len(review_pages) > 10:
            print(f"... and {len(review_pages) - 10} more")
        print()

    # Overall assessment
    print("=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)
    print()

    if avg_confidence > 0.85:
        print("✅ EXCELLENT - Extraction quality is very high")
    elif avg_confidence > 0.75:
        print("✓ GOOD - Extraction quality is solid")
    elif avg_confidence > 0.6:
        print("⚠ MODERATE - Some manual review recommended")
    else:
        print("⚠ LOW - Significant manual review needed")

    print()
    print("Ready for publication:")
    if stats['high_quality'] > stats['total_pages'] * 0.6:
        print("  ✅ YES - Majority of pages are high quality")
    elif stats['high_quality'] + stats['medium_quality'] > stats['total_pages'] * 0.75:
        print("  ✓ MOSTLY - Good overall quality with some cleanup")
    else:
        print("  ⚠ REVIEW - Manual review recommended before publication")

    print()
    print("=" * 80)

    return stats

if __name__ == '__main__':
    analyze_full_collection()
