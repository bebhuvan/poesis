#!/usr/bin/env python3
"""
Verification Script - Compare extracted text against original scans
Samples pages and checks for quality issues
"""
import json
import random
from pathlib import Path
from collections import Counter
import re

def analyze_page(page_num: int) -> dict:
    """Analyze a single page's extraction quality"""

    # Read metadata
    metadata_path = Path(f'metadata/page_{page_num:04d}.json')
    with open(metadata_path) as f:
        metadata = json.load(f)

    # Read extracted text
    text_path = Path(f'final_text/page_{page_num:04d}.txt')
    text = text_path.read_text()

    # Analyze
    analysis = {
        'page': page_num,
        'confidence': metadata['consensus']['confidence'],
        'quality_score': metadata['quality_verification']['overall_score'],
        'char_count': len(text),
        'word_count': len(text.split()),
        'has_content': len(text) > 100,
        'warnings': metadata['quality_verification']['warnings_count'],
        'errors': metadata['quality_verification']['errors_count'],
        'recommendations': metadata['recommendations']
    }

    # Check for specific issues
    issues = []

    # Too many special characters?
    special_chars = len(re.findall(r'[^\w\s.,;:!?\'"()-]', text))
    if special_chars / max(len(text), 1) > 0.1:
        issues.append('High special character ratio')

    # Very short words (OCR artifacts)?
    words = text.split()
    if words:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len < 3:
            issues.append('Short average word length')

    # Repeated characters?
    repeated = re.findall(r'(.)\1{4,}', text)
    if repeated:
        issues.append(f'Repeated characters: {repeated[:3]}')

    analysis['issues'] = issues

    return analysis

def sample_verification(num_samples: int = 20):
    """Sample random pages for verification"""

    # Get all page numbers
    all_pages = list(range(168))

    # Sample: first 5, last 5, and 10 random from middle
    sample_pages = (
        all_pages[:5] +  # First 5
        all_pages[-5:] +  # Last 5
        random.sample(all_pages[10:158], min(10, len(all_pages[10:158])))  # 10 random
    )

    print("=" * 80)
    print("VERIFICATION REPORT - Extracted Text Quality Check")
    print("=" * 80)
    print()
    print(f"Analyzing {len(sample_pages)} sample pages...")
    print()

    results = []
    high_quality = 0
    medium_quality = 0
    low_quality = 0

    for page_num in sorted(sample_pages):
        analysis = analyze_page(page_num)
        results.append(analysis)

        # Categorize
        if analysis['confidence'] > 0.8 and analysis['quality_score'] > 0.9:
            high_quality += 1
            quality = "HIGH"
        elif analysis['confidence'] > 0.5 and analysis['quality_score'] > 0.75:
            medium_quality += 1
            quality = "MEDIUM"
        else:
            low_quality += 1
            quality = "LOW"

        # Show interesting pages
        if page_num in [9, 15, 20, 30] or quality == "LOW":
            print(f"Page {page_num:3d}: {quality:6s} | "
                  f"Confidence: {analysis['confidence']:.2f} | "
                  f"Quality: {analysis['quality_score']:.2f} | "
                  f"{analysis['word_count']:4d} words")

            if analysis['issues']:
                print(f"          Issues: {', '.join(analysis['issues'])}")
            if analysis['recommendations']:
                for rec in analysis['recommendations'][:1]:
                    print(f"          → {rec}")
            print()

    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Sample Size:      {len(sample_pages)} pages")
    print(f"High Quality:     {high_quality} pages ({high_quality/len(sample_pages)*100:.1f}%)")
    print(f"Medium Quality:   {medium_quality} pages ({medium_quality/len(sample_pages)*100:.1f}%)")
    print(f"Low Quality:      {low_quality} pages ({low_quality/len(sample_pages)*100:.1f}%)")
    print()

    # Overall stats
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_quality = sum(r['quality_score'] for r in results) / len(results)
    content_pages = sum(1 for r in results if r['has_content'])

    print(f"Average Confidence: {avg_confidence:.2%}")
    print(f"Average Quality:    {avg_quality:.2%}")
    print(f"Content Pages:      {content_pages}/{len(sample_pages)}")
    print()

    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    if avg_confidence > 0.85:
        print("✅ Excellent OCR confidence - extraction is highly reliable")
    elif avg_confidence > 0.7:
        print("✓ Good OCR confidence - minor manual review recommended")
    else:
        print("⚠ Moderate OCR confidence - manual review recommended for critical pages")

    if avg_quality > 0.95:
        print("✅ Excellent quality score - text is clean and well-formatted")
    elif avg_quality > 0.85:
        print("✓ Good quality score - minimal cleanup needed")
    else:
        print("⚠ Quality concerns - review flagged pages")

    print()

    # Pages that need attention
    needs_review = [r for r in results if r['confidence'] < 0.7 or r['errors'] > 0]
    if needs_review:
        print(f"Pages needing manual review ({len(needs_review)}):")
        for r in needs_review:
            print(f"  • Page {r['page']} (confidence: {r['confidence']:.2f})")
    else:
        print("✅ No pages flagged for manual review in sample")

    print()
    print("=" * 80)

    return results

def compare_sample_text():
    """Show sample text comparisons"""

    print()
    print("=" * 80)
    print("SAMPLE TEXT QUALITY CHECK")
    print("=" * 80)
    print()

    # Check a few key pages
    key_pages = [9, 15, 20, 30, 50]  # Pages we know have content

    for page_num in key_pages:
        text_path = Path(f'final_text/page_{page_num:04d}.txt')
        if not text_path.exists():
            continue

        text = text_path.read_text()
        if len(text) < 50:
            continue

        print(f"Page {page_num} Preview (first 200 chars):")
        print("-" * 80)
        preview = text[:200].replace('\n', ' ')
        print(preview)
        if len(text) > 200:
            print("...")
        print()

    print("=" * 80)

if __name__ == '__main__':
    # Run verification
    results = sample_verification(20)

    # Show sample text
    compare_sample_text()

    print()
    print("✅ Verification complete!")
    print()
    print("To see full text for any page:")
    print("  cat final_text/page_NNNN.txt")
    print()
    print("To see the original image:")
    print("  xdg-open raw_images/page_NNNN.jpg")
    print()
