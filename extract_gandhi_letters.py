#!/usr/bin/env python3
"""
Quick extraction script for Gandhi letters.
Handles ABBYY XML namespace properly.
"""

import gzip
import json
import logging
from pathlib import Path
from xml.etree import ElementTree as ET

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def extract_abbyy_text(abbyy_gz_path):
    """Extract text from ABBYY OCR XML with proper namespace handling."""
    logger.info(f"Extracting text from: {abbyy_gz_path}")

    # Decompress gzip
    with gzip.open(abbyy_gz_path, 'rt', encoding='utf-8') as f:
        xml_content = f.read()

    # Parse XML
    root = ET.fromstring(xml_content)

    # Define namespace
    ns = {'abbyy': 'http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml'}

    # Find all pages using namespace
    pages = root.findall('.//abbyy:page', ns)
    logger.info(f"Found {len(pages)} pages")

    extracted_pages = {}

    for page_num, page in enumerate(pages, 1):
        logger.info(f"Processing page {page_num}/{len(pages)}...")

        page_data = {
            'page_number': page_num,
            'width': page.get('width'),
            'height': page.get('height'),
            'full_text': ''
        }

        # Extract all text from page
        text_lines = []

        # Find all formatting elements (they contain the actual text)
        for formatting in page.findall('.//abbyy:formatting', ns):
            # Get all charParams elements to extract characters
            chars = []
            for char_elem in formatting.findall('.//abbyy:charParams', ns):
                # The character is in the text content
                if char_elem.text:
                    chars.append(char_elem.text)

            if chars:
                text_lines.append(''.join(chars))

        # Also try extracting from text content directly
        for line in page.findall('.//abbyy:line', ns):
            for formatting in line.findall('.//abbyy:formatting', ns):
                if formatting.text:
                    text_lines.append(formatting.text)

        # Combine all text
        page_text = ' '.join(text_lines).strip()

        if page_text:
            page_data['full_text'] = page_text
            extracted_pages[page_num] = page_data
            logger.info(f"  Extracted {len(page_text)} characters")
        else:
            logger.warning(f"  No text extracted for page {page_num}")

    return extracted_pages


def main():
    """Extract all Gandhi letters."""
    logger.info("="*60)
    logger.info("GANDHI LETTERS EXTRACTION")
    logger.info("="*60)

    # Find ABBYY file
    abbyy_path = Path("archive_cache/in.ernet.dli.2015.208999/2015.208999.Famous-Letters_abbyy.gz")
    if not abbyy_path.exists():
        logger.error(f"ABBYY file not found: {abbyy_path}")
        return

    # Extract
    pages = extract_abbyy_text(abbyy_path)

    # Create output directory
    output_dir = Path("gandhi_letters_extracted")
    output_dir.mkdir(exist_ok=True)

    # Save each page
    logger.info(f"\nSaving {len(pages)} pages...")
    for page_num, page_data in pages.items():
        # Save text
        text_file = output_dir / f"page_{page_num:03d}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(page_data['full_text'])

        # Save metadata
        metadata_file = output_dir / f"page_{page_num:03d}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2)

    # Save combined text
    combined_file = output_dir / "all_letters_combined.txt"
    with open(combined_file, 'w', encoding='utf-8') as f:
        for page_num in sorted(pages.keys()):
            f.write(f"\n{'='*60}\n")
            f.write(f"PAGE {page_num}\n")
            f.write(f"{'='*60}\n\n")
            f.write(pages[page_num]['full_text'])
            f.write('\n')

    # Summary
    total_chars = sum(len(p['full_text']) for p in pages.values())
    logger.info(f"\n{'='*60}")
    logger.info("EXTRACTION COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Pages extracted: {len(pages)}")
    logger.info(f"Total characters: {total_chars:,}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Combined file: {combined_file}")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()
