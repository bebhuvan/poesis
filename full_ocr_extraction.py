#!/usr/bin/env python3
"""
Full OCR extraction of all 210 pages from Tagore letters PDF
Saves progress incrementally
"""

import os
import json
from pdf2image import convert_from_path
import pytesseract


def extract_all_pages_full():
    """Extract text from all 210 pages with progress saving"""

    pdf_path = 'tagore_letters.pdf'
    output_file = 'tagore_full_ocr.json'

    # Load existing progress if any
    ocr_text = {}
    if os.path.exists(output_file):
        print(f"📂 Loading existing OCR progress from {output_file}...")
        with open(output_file, 'r', encoding='utf-8') as f:
            ocr_text = json.load(f)
        print(f"   Already completed: {len(ocr_text)} pages")

    print("\n" + "=" * 80)
    print("FULL OCR EXTRACTION - ALL 210 PAGES")
    print("=" * 80)
    print("This will take approximately 30-45 minutes...")
    print("Progress is saved every 10 pages.\n")

    total_pages = 210
    batch_size = 10
    current_page = 0

    # Skip already processed pages
    if ocr_text:
        processed_pages = [int(k) for k in ocr_text.keys()]
        if processed_pages:
            current_page = max(processed_pages) + 1
            print(f"🔄 Resuming from page {current_page}...")

    while current_page < total_pages:
        batch_end = min(current_page + batch_size, total_pages)

        print(f"\n📄 Processing pages {current_page}-{batch_end-1}...")

        try:
            # Convert batch to images
            images = convert_from_path(
                pdf_path,
                first_page=current_page + 1,
                last_page=batch_end,
                dpi=300
            )

            # OCR each image
            for i, image in enumerate(images):
                page_num = current_page + i

                try:
                    custom_config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(image, config=custom_config)
                    ocr_text[page_num] = text

                    if (page_num + 1) % 5 == 0:
                        print(f"   ✓ {page_num + 1}/{total_pages} pages completed")

                except Exception as e:
                    print(f"   ⚠ Error on page {page_num}: {e}")
                    ocr_text[page_num] = ""

            # Save progress after each batch
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ocr_text, f, indent=2, ensure_ascii=False)

            print(f"   💾 Progress saved ({len(ocr_text)}/{total_pages} pages)")

        except Exception as e:
            print(f"   ⚠ Batch error: {e}")

        current_page = batch_end

    print("\n" + "=" * 80)
    print("✓ FULL OCR EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total pages extracted: {len(ocr_text)}")
    print(f"Output saved to: {output_file}")
    print("=" * 80)

    return ocr_text


if __name__ == '__main__':
    extract_all_pages_full()
