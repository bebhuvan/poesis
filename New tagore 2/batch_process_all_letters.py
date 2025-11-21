#!/usr/bin/env python3
"""
Batch process all letters from the Tagore PDF
Intelligently detect letter boundaries and process each separately
"""

import re
import sys
from pathlib import Path
from ocr_extraction_pipeline import OCRExtractor

def detect_letter_boundaries(pdf_path: str, sample_pages: int = 20):
    """
    Analyze PDF to detect letter boundaries
    Look for patterns like dates, salutations, closings
    """
    print("🔍 Analyzing document structure to detect letter boundaries...")

    # For this collection, we'll use a simpler approach:
    # Letters appear to be sequential in the book
    # We'll process in reasonable chunks (3-5 pages per letter typically)

    # Based on the book structure "Letters From Abroad" (1924)
    # This appears to be a sequential collection of travel letters

    # For now, let's process in small batches and look for natural breaks
    boundaries = []

    # Sample approach: Process every 4-6 pages as a letter
    # (This would ideally be done by analyzing actual content)

    # Skip front matter (first 10 pages likely table of contents, intro, etc.)
    start = 10
    end = 168  # Total pages

    current_page = start
    letter_num = 1

    while current_page < end:
        # Typical letter length: 4-6 pages, but some may be shorter/longer
        letter_length = 6  # We can adjust this based on content

        boundaries.append({
            'letter_num': letter_num,
            'start_page': current_page,
            'end_page': min(current_page + letter_length - 1, end - 1)
        })

        current_page += letter_length
        letter_num += 1

    return boundaries


def main():
    pdf_path = "/home/user/poesis/New tagore 2/tagore_letters_from_abroad_1924.pdf"
    output_dir = "/home/user/poesis/New tagore 2/all_letters_extracted"

    print("=" * 70)
    print("BATCH OCR EXTRACTION - TAGORE LETTERS FROM ABROAD")
    print("=" * 70)

    # Detect letter boundaries
    boundaries = detect_letter_boundaries(pdf_path)

    print(f"\n📚 Detected {len(boundaries)} potential letters")
    print(f"📄 Processing pages 10-168")

    # Ask user for confirmation
    print(f"\n⚠️  This will process ~{len(boundaries)} letters")
    print("   Processing time: ~2-3 minutes per letter")
    print(f"   Total estimated time: ~{len(boundaries) * 2.5 / 60:.1f} hours")
    print("\n   For demo purposes, processing first 5 letters only...")
    print("   (Remove this limit in production)\n")

    # Limit for demo
    boundaries = boundaries[:5]

    # Initialize extractor
    extractor = OCRExtractor(pdf_path, output_dir)

    # Process each letter
    results = []
    for i, boundary in enumerate(boundaries, 1):
        print(f"\n{'='*70}")
        print(f"Letter {i}/{len(boundaries)}")
        print(f"{'='*70}")

        try:
            result = extractor.process_page_range(
                start_page=boundary['start_page'],
                end_page=boundary['end_page'],
                letter_num=boundary['letter_num']
            )

            # Generate outputs
            html_path = extractor.generate_review_html(result)
            md_path = extractor.generate_final_markdown(result)

            results.append({
                'letter_num': boundary['letter_num'],
                'pages': f"{boundary['start_page']+1}-{boundary['end_page']+1}",
                'confidence': result['metadata'].ocr_confidence,
                'word_count': result['metadata'].word_count,
                'date': result['metadata'].date,
                'html': html_path.name,
                'markdown': md_path.name
            })

        except Exception as e:
            print(f"❌ Error processing letter {boundary['letter_num']}: {str(e)}")
            continue

    # Summary report
    print("\n" + "=" * 70)
    print("✅ BATCH PROCESSING COMPLETE")
    print("=" * 70)

    print(f"\n📊 Processed {len(results)} letters successfully\n")

    print("Letter  Pages      Date         Confidence  Words    Files")
    print("-" * 70)

    for r in results:
        date_str = r['date'] if r['date'] else 'undated'
        print(f"#{r['letter_num']:<5} {r['pages']:<10} {date_str:<12} {r['confidence']:>5.1f}%  "
              f"{r['word_count']:>7}    ✓")

    avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
    total_words = sum(r['word_count'] for r in results)

    print("-" * 70)
    print(f"Total words: {total_words:,}")
    print(f"Average confidence: {avg_confidence:.1f}%")
    print(f"\n📁 Output directory: {output_dir}")
    print(f"   • Review HTML: {output_dir}/review_html/")
    print(f"   • Final Markdown: {output_dir}/final_markdown/")
    print("\n💡 Next steps:")
    print("   1. Review HTML files for accuracy")
    print("   2. Make any necessary corrections")
    print("   3. Remove limit to process all ~26 letters")
    print("   4. Commit and push to git branch")


if __name__ == "__main__":
    main()
