#!/usr/bin/env python3
"""
Tagore Letters OCR Extractor
Uses OCR to extract text from scanned PDF pages
"""

import os
import re
import json
from typing import Dict, List
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


class TagoreOCRExtractor:
    """Extract letters from scanned PDF using OCR"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.ocr_text_by_page = {}
        self.letters = []

    def extract_page_text_ocr(self, page_num: int, image) -> str:
        """Extract text from a single page image using OCR"""
        try:
            # Use tesseract with better settings for old scanned documents
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=custom_config)
            return text
        except Exception as e:
            print(f"  ⚠ OCR error on page {page_num}: {e}")
            return ""

    def extract_all_pages(self, start_page: int = 0, end_page: int = None):
        """Extract text from all pages using OCR"""
        print(f"\n📄 Converting PDF to images and running OCR...")
        print(f"   This may take several minutes for 210 pages...")

        # Convert PDF to images (do in batches to save memory)
        batch_size = 10
        total_pages = 210  # We know this from earlier

        if end_page is None:
            end_page = total_pages

        current_page = start_page

        while current_page < end_page:
            batch_end = min(current_page + batch_size, end_page)

            print(f"\n  Processing pages {current_page}-{batch_end}...")

            try:
                # Convert this batch of pages to images
                images = convert_from_path(
                    self.pdf_path,
                    first_page=current_page + 1,  # pdf2image uses 1-based indexing
                    last_page=batch_end,
                    dpi=300  # Good balance of quality and speed
                )

                # OCR each image
                for i, image in enumerate(images):
                    page_num = current_page + i
                    text = self.extract_page_text_ocr(page_num, image)
                    self.ocr_text_by_page[page_num] = text

                    if (page_num + 1) % 5 == 0:
                        print(f"    OCR completed: {page_num + 1}/{end_page} pages")

            except Exception as e:
                print(f"  ⚠ Batch error for pages {current_page}-{batch_end}: {e}")

            current_page = batch_end

        print(f"\n✓ OCR completed for {len(self.ocr_text_by_page)} pages")

    def save_ocr_text(self, output_file: str = 'tagore_ocr_text.json'):
        """Save OCR text for later use"""
        print(f"\n💾 Saving OCR text to {output_file}...")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.ocr_text_by_page, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved OCR text for {len(self.ocr_text_by_page)} pages")

    def load_ocr_text(self, input_file: str = 'tagore_ocr_text.json'):
        """Load previously saved OCR text"""
        if os.path.exists(input_file):
            print(f"\n📂 Loading OCR text from {input_file}...")
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert string keys back to integers
                self.ocr_text_by_page = {int(k): v for k, v in data.items()}
            print(f"✓ Loaded OCR text for {len(self.ocr_text_by_page)} pages")
            return True
        return False

    def analyze_structure(self):
        """Analyze document structure from OCR text"""
        print("\n🔍 Analyzing document structure from OCR text...")

        # Look for Roman numerals (letter numbers)
        roman_numerals = []
        dates_found = []
        toc_pages = []

        for page_num, text in self.ocr_text_by_page.items():
            # Look for table of contents
            if re.search(r'contents|index', text, re.IGNORECASE):
                toc_pages.append(page_num)

            # Look for Roman numerals at start of lines (potential letter numbers)
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Match Roman numerals (I, II, III, IV, V, etc.)
                if re.match(r'^([IVXLCDM]{1,6})\s*\.?\s*$', line):
                    roman_numerals.append((page_num, line))

            # Look for dates
            date_patterns = [
                r'\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)',
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}',
            ]
            for pattern in date_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    dates_found.append(page_num)
                    break

        print(f"  Roman numerals found: {len(roman_numerals)}")
        print(f"  Pages with dates: {len(set(dates_found))}")
        print(f"  TOC pages: {toc_pages}")

        # Show sample Roman numerals
        if roman_numerals:
            print(f"\n  Sample Roman numerals found:")
            for page, numeral in roman_numerals[:10]:
                print(f"    Page {page}: {numeral}")

        return {
            'roman_numerals': roman_numerals,
            'dates_found': sorted(set(dates_found)),
            'toc_pages': toc_pages
        }

    def identify_letters(self):
        """Identify individual letters from OCR text"""
        print("\n📝 Identifying letter boundaries...")

        # Strategy: Look for Roman numerals which typically mark letter starts
        roman_pattern = re.compile(r'^([IVXLCDM]{1,6})\s*\.?\s*$', re.MULTILINE)

        letter_boundaries = []

        for page_num in sorted(self.ocr_text_by_page.keys()):
            text = self.ocr_text_by_page[page_num]
            lines = text.split('\n')

            for line_num, line in enumerate(lines):
                line = line.strip()

                # Check for Roman numeral
                if re.match(r'^([IVXLCDM]{1,6})\s*\.?\s*$', line):
                    letter_boundaries.append({
                        'page': page_num,
                        'line': line_num,
                        'marker': line,
                        'type': 'roman_numeral'
                    })

                # Also check for dates at start of letter (alternative pattern)
                elif re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}', line, re.IGNORECASE):
                    letter_boundaries.append({
                        'page': page_num,
                        'line': line_num,
                        'marker': line,
                        'type': 'date'
                    })

        print(f"  Found {len(letter_boundaries)} potential letter boundaries")

        # Sort by page and line
        letter_boundaries = sorted(letter_boundaries, key=lambda x: (x['page'], x['line']))

        return letter_boundaries

    def extract_letters_content(self, boundaries: List[Dict]):
        """Extract content for each letter"""
        print("\n✂️  Extracting letter content...")

        letters = []

        for i, boundary in enumerate(boundaries):
            start_page = boundary['page']
            start_line = boundary['line']

            # Determine end of this letter
            if i + 1 < len(boundaries):
                end_page = boundaries[i + 1]['page']
                end_line = boundaries[i + 1]['line']
            else:
                end_page = max(self.ocr_text_by_page.keys())
                end_line = None  # Will take all lines on last page

            # Extract content
            letter_text = []

            for page_num in range(start_page, end_page + 1):
                if page_num not in self.ocr_text_by_page:
                    continue

                page_text = self.ocr_text_by_page[page_num]
                lines = page_text.split('\n')

                if page_num == start_page and page_num == end_page:
                    # Same page
                    if end_line is not None:
                        letter_text.extend(lines[start_line:end_line])
                    else:
                        letter_text.extend(lines[start_line:])
                elif page_num == start_page:
                    # First page
                    letter_text.extend(lines[start_line:])
                elif page_num == end_page:
                    # Last page
                    if end_line is not None:
                        letter_text.extend(lines[:end_line])
                    else:
                        letter_text.extend(lines)
                else:
                    # Middle pages
                    letter_text.extend(lines)

            content = '\n'.join(letter_text).strip()

            # Extract metadata
            letter_data = {
                'number': i + 1,
                'marker': boundary['marker'],
                'marker_type': boundary['type'],
                'start_page': start_page,
                'end_page': end_page,
                'content': content,
                'word_count': len(content.split()),
                'char_count': len(content),
            }

            # Try to find date
            date_match = re.search(
                r'((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,.]?\s+\d{1,2}(?:st|nd|rd|th)?[,.]?\s+\d{4})',
                content,
                re.IGNORECASE
            )
            if date_match:
                letter_data['date'] = date_match.group(1)
            else:
                # Try simpler patterns
                date_match = re.search(
                    r'((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,.]?\s+\d{1,2}(?:st|nd|rd|th)?)',
                    content,
                    re.IGNORECASE
                )
                if date_match:
                    letter_data['date'] = date_match.group(1)

            # Try to find recipient
            recipient_patterns = [
                r'(?:Dear|My dear)\s+([^,\n]{3,30})',
                r'(?:To)\s+([A-Z][^,\n]{3,30})',
            ]
            for pattern in recipient_patterns:
                match = re.search(pattern, content)
                if match:
                    letter_data['recipient'] = match.group(1).strip()
                    break

            letters.append(letter_data)

        print(f"✓ Extracted {len(letters)} letters")
        self.letters = letters
        return letters

    def save_letters_as_markdown(self, output_dir: str = 'tagore_letters_ocr'):
        """Save letters as markdown files"""
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n💾 Saving {len(self.letters)} letters to {output_dir}/")

        for letter in self.letters:
            filename = f"letter_{letter['number']:03d}.md"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"letter_number: {letter['number']}\n")
                f.write(f"marker: \"{letter['marker']}\"\n")
                f.write(f"pages: {letter['start_page']}-{letter['end_page']}\n")

                if 'date' in letter:
                    f.write(f"date: \"{letter['date']}\"\n")

                if 'recipient' in letter:
                    f.write(f"recipient: \"{letter['recipient']}\"\n")

                f.write(f"word_count: {letter['word_count']}\n")
                f.write(f"---\n\n")

                f.write(f"# Letter {letter['number']}\n\n")
                f.write(letter['content'])

        print(f"✓ Saved {len(self.letters)} letters")


def main():
    print("=" * 80)
    print("TAGORE LETTERS - OCR EXTRACTION")
    print("=" * 80)

    extractor = TagoreOCRExtractor('tagore_letters.pdf')

    # Try to load previously saved OCR text
    if not extractor.load_ocr_text():
        # Run OCR on first 30 pages as a test
        print("\n⚠ No cached OCR text found. Running OCR on sample pages...")
        print("  (Full extraction will be done separately)")
        extractor.extract_all_pages(start_page=0, end_page=30)
        extractor.save_ocr_text('tagore_ocr_sample.json')

    # Analyze structure
    structure = extractor.analyze_structure()

    # Identify letters
    boundaries = extractor.identify_letters()

    # Extract letters
    if boundaries:
        letters = extractor.extract_letters_content(boundaries)

        # Save letters
        extractor.save_letters_as_markdown()

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Pages processed: {len(extractor.ocr_text_by_page)}")
        print(f"Letters extracted: {len(letters)}")
        if letters:
            print(f"Average words per letter: {sum(l['word_count'] for l in letters) / len(letters):.0f}")
            print(f"Letters with dates: {sum(1 for l in letters if 'date' in l)}")
            print(f"Letters with recipients: {sum(1 for l in letters if 'recipient' in l)}")
        print("=" * 80)
    else:
        print("\n⚠ No letter boundaries found. The OCR text may need manual review.")


if __name__ == '__main__':
    main()
