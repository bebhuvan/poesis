#!/usr/bin/env python3
"""
Tagore Letters PDF Analyzer
Comprehensive analysis and verification of letter extraction from PDF
"""

import re
import json
from typing import Dict, List, Tuple
from collections import Counter
import PyPDF2


class TagorePDFAnalyzer:
    """Analyze and extract letters from Tagore PDF with verification"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_reader = None
        self.total_pages = 0
        self.raw_text_by_page = {}
        self.letters = []
        self.verification_report = {}

    def open_pdf(self):
        """Open and initialize PDF reader"""
        with open(self.pdf_path, 'rb') as file:
            self.pdf_reader = PyPDF2.PdfReader(file)
            self.total_pages = len(self.pdf_reader.pages)
            print(f"✓ PDF opened: {self.total_pages} pages")

    def extract_all_text(self):
        """Extract text from all pages"""
        print(f"\n📄 Extracting text from {self.total_pages} pages...")

        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            for page_num in range(len(reader.pages)):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    self.raw_text_by_page[page_num] = text

                    if (page_num + 1) % 20 == 0:
                        print(f"  Processed {page_num + 1}/{self.total_pages} pages...")
                except Exception as e:
                    print(f"  ⚠ Error on page {page_num}: {e}")
                    self.raw_text_by_page[page_num] = ""

        print(f"✓ Extracted text from {len(self.raw_text_by_page)} pages")

    def analyze_document_structure(self):
        """Analyze the structure of the document"""
        print("\n🔍 Analyzing document structure...")

        # Find table of contents
        toc_pages = []
        letter_markers = []
        page_numbers_found = []

        for page_num, text in self.raw_text_by_page.items():
            # Look for TOC indicators
            if re.search(r'contents|table of contents', text, re.IGNORECASE):
                toc_pages.append(page_num)

            # Look for letter markers (common patterns)
            # Roman numerals: I, II, III, etc.
            roman_matches = re.findall(r'\b([IVXLCDM]+)\b', text)
            if roman_matches:
                letter_markers.extend([(page_num, m) for m in roman_matches[:3]])

            # Look for dates (various formats)
            date_patterns = [
                r'\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)',
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?',
                r'\d{4}',  # Year
            ]
            for pattern in date_patterns:
                if re.search(pattern, text):
                    page_numbers_found.append(page_num)
                    break

        print(f"  TOC pages: {toc_pages}")
        print(f"  Pages with dates: {len(set(page_numbers_found))}")
        print(f"  Letter markers found: {len(letter_markers)}")

        return {
            'toc_pages': toc_pages,
            'pages_with_dates': sorted(set(page_numbers_found)),
            'letter_markers': letter_markers[:20]  # Sample
        }

    def identify_letter_boundaries(self):
        """Identify where each letter starts and ends"""
        print("\n📝 Identifying letter boundaries...")

        # Strategy 1: Look for Roman numerals (I, II, III, etc.)
        # Strategy 2: Look for page breaks combined with dates
        # Strategy 3: Look for "Dear" or recipient names

        letter_starts = []

        for page_num, text in self.raw_text_by_page.items():
            lines = text.split('\n')

            for i, line in enumerate(lines):
                line_stripped = line.strip()

                # Roman numeral at start of line
                if re.match(r'^([IVXLCDM]+)\s*$', line_stripped):
                    letter_starts.append({
                        'page': page_num,
                        'line': i,
                        'marker': line_stripped,
                        'type': 'roman_numeral'
                    })

                # Date patterns at start of letter
                if re.match(r'^(?:January|February|March|April|May|June|July|August|September|October|November|December)', line_stripped):
                    letter_starts.append({
                        'page': page_num,
                        'line': i,
                        'marker': line_stripped,
                        'type': 'date'
                    })

                # "Dear" or recipient patterns
                if re.match(r'^(?:Dear|My dear|To)\s+[A-Z]', line_stripped):
                    letter_starts.append({
                        'page': page_num,
                        'line': i,
                        'marker': line_stripped,
                        'type': 'salutation'
                    })

        print(f"  Found {len(letter_starts)} potential letter boundaries")
        print(f"    Roman numerals: {sum(1 for x in letter_starts if x['type'] == 'roman_numeral')}")
        print(f"    Dates: {sum(1 for x in letter_starts if x['type'] == 'date')}")
        print(f"    Salutations: {sum(1 for x in letter_starts if x['type'] == 'salutation')}")

        return letter_starts

    def extract_letters(self, letter_boundaries: List[Dict]):
        """Extract individual letters based on identified boundaries"""
        print("\n✂️  Extracting individual letters...")

        # Sort boundaries by page and line
        boundaries = sorted(letter_boundaries, key=lambda x: (x['page'], x['line']))

        letters = []

        for i, boundary in enumerate(boundaries):
            # Determine where this letter ends (start of next letter or end of document)
            start_page = boundary['page']
            start_line = boundary['line']

            if i + 1 < len(boundaries):
                end_page = boundaries[i + 1]['page']
                end_line = boundaries[i + 1]['line']
            else:
                end_page = max(self.raw_text_by_page.keys())
                end_line = float('inf')

            # Extract text for this letter
            letter_text = []

            for page_num in range(start_page, end_page + 1):
                if page_num not in self.raw_text_by_page:
                    continue

                lines = self.raw_text_by_page[page_num].split('\n')

                if page_num == start_page and page_num == end_page:
                    # Letter starts and ends on same page
                    letter_text.extend(lines[start_line:end_line])
                elif page_num == start_page:
                    # First page of letter
                    letter_text.extend(lines[start_line:])
                elif page_num == end_page:
                    # Last page of letter
                    letter_text.extend(lines[:end_line])
                else:
                    # Middle pages
                    letter_text.extend(lines)

            letter_content = '\n'.join(letter_text).strip()

            # Extract metadata
            letter_data = {
                'letter_number': i + 1,
                'marker': boundary['marker'],
                'marker_type': boundary['type'],
                'start_page': start_page,
                'end_page': end_page,
                'content': letter_content,
                'word_count': len(letter_content.split()),
                'char_count': len(letter_content),
            }

            # Try to extract date
            date_match = re.search(
                r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)',
                letter_content
            )
            if date_match:
                letter_data['date'] = date_match.group(1)

            # Try to extract recipient
            recipient_match = re.search(r'(?:Dear|My dear|To)\s+([^,\n]+)', letter_content)
            if recipient_match:
                letter_data['recipient'] = recipient_match.group(1).strip()

            letters.append(letter_data)

        print(f"✓ Extracted {len(letters)} letters")
        self.letters = letters
        return letters

    def verify_extraction_quality(self):
        """Run multiple verification checks"""
        print("\n🔬 Running verification checks...")

        verification = {
            'total_pages': self.total_pages,
            'total_letters_extracted': len(self.letters),
            'checks': {}
        }

        # Check 1: Page coverage
        pages_covered = set()
        for letter in self.letters:
            for page in range(letter['start_page'], letter['end_page'] + 1):
                pages_covered.add(page)

        # Exclude front matter (usually first 10 pages)
        content_pages = set(range(10, self.total_pages))
        missing_pages = content_pages - pages_covered

        verification['checks']['page_coverage'] = {
            'pages_with_content': len(content_pages),
            'pages_covered': len(pages_covered),
            'coverage_percentage': (len(pages_covered & content_pages) / len(content_pages) * 100) if content_pages else 0,
            'missing_pages': sorted(missing_pages)[:20]  # Show first 20
        }

        print(f"  ✓ Page coverage: {verification['checks']['page_coverage']['coverage_percentage']:.1f}%")
        print(f"    Missing pages: {len(missing_pages)}")

        # Check 2: Letter completeness
        short_letters = [l for l in self.letters if l['word_count'] < 50]
        empty_letters = [l for l in self.letters if l['word_count'] == 0]

        verification['checks']['letter_completeness'] = {
            'total_letters': len(self.letters),
            'short_letters': len(short_letters),
            'empty_letters': len(empty_letters),
            'avg_words_per_letter': sum(l['word_count'] for l in self.letters) / len(self.letters) if self.letters else 0
        }

        print(f"  ✓ Letter quality:")
        print(f"    Average words per letter: {verification['checks']['letter_completeness']['avg_words_per_letter']:.0f}")
        print(f"    Short letters (<50 words): {len(short_letters)}")
        print(f"    Empty letters: {len(empty_letters)}")

        # Check 3: Metadata extraction
        letters_with_dates = sum(1 for l in self.letters if 'date' in l)
        letters_with_recipients = sum(1 for l in self.letters if 'recipient' in l)

        verification['checks']['metadata_extraction'] = {
            'letters_with_dates': letters_with_dates,
            'letters_with_recipients': letters_with_recipients,
            'date_extraction_rate': (letters_with_dates / len(self.letters) * 100) if self.letters else 0,
            'recipient_extraction_rate': (letters_with_recipients / len(self.letters) * 100) if self.letters else 0
        }

        print(f"  ✓ Metadata extraction:")
        print(f"    Dates extracted: {letters_with_dates}/{len(self.letters)} ({verification['checks']['metadata_extraction']['date_extraction_rate']:.1f}%)")
        print(f"    Recipients extracted: {letters_with_recipients}/{len(self.letters)} ({verification['checks']['metadata_extraction']['recipient_extraction_rate']:.1f}%)")

        # Check 4: Sequential numbering
        if self.letters:
            gaps = []
            for i in range(len(self.letters) - 1):
                page_gap = self.letters[i + 1]['start_page'] - self.letters[i]['end_page']
                if page_gap > 2:  # Allow for page breaks
                    gaps.append({
                        'after_letter': i + 1,
                        'page_gap': page_gap
                    })

            verification['checks']['sequential_gaps'] = {
                'total_gaps': len(gaps),
                'gaps': gaps[:10]  # Show first 10
            }

            print(f"  ✓ Sequential analysis:")
            print(f"    Large gaps between letters: {len(gaps)}")

        self.verification_report = verification
        return verification

    def generate_report(self, output_file: str = 'tagore_extraction_report.json'):
        """Generate comprehensive report"""
        report = {
            'pdf_path': self.pdf_path,
            'total_pages': self.total_pages,
            'letters_extracted': len(self.letters),
            'verification': self.verification_report,
            'letters_summary': [
                {
                    'letter_number': l['letter_number'],
                    'marker': l['marker'],
                    'start_page': l['start_page'],
                    'end_page': l['end_page'],
                    'word_count': l['word_count'],
                    'date': l.get('date', 'NOT_FOUND'),
                    'recipient': l.get('recipient', 'NOT_FOUND'),
                    'preview': l['content'][:200] + '...' if len(l['content']) > 200 else l['content']
                }
                for l in self.letters
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📊 Report saved to: {output_file}")
        return report

    def save_letters(self, output_dir: str = 'tagore_letters'):
        """Save each letter as a separate file"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n💾 Saving letters to {output_dir}/")

        for letter in self.letters:
            filename = f"letter_{letter['letter_number']:03d}.md"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Letter {letter['letter_number']}\n\n")
                f.write(f"**Marker:** {letter['marker']}\n\n")
                f.write(f"**Pages:** {letter['start_page']}-{letter['end_page']}\n\n")

                if 'date' in letter:
                    f.write(f"**Date:** {letter['date']}\n\n")

                if 'recipient' in letter:
                    f.write(f"**Recipient:** {letter['recipient']}\n\n")

                f.write(f"**Word Count:** {letter['word_count']}\n\n")
                f.write("---\n\n")
                f.write(letter['content'])

        print(f"✓ Saved {len(self.letters)} letters")


def main():
    print("=" * 60)
    print("TAGORE LETTERS - PDF ANALYSIS & EXTRACTION")
    print("=" * 60)

    analyzer = TagorePDFAnalyzer('tagore_letters.pdf')

    # Step 1: Open PDF
    analyzer.open_pdf()

    # Step 2: Extract all text
    analyzer.extract_all_text()

    # Step 3: Analyze structure
    structure = analyzer.analyze_document_structure()

    # Step 4: Identify letter boundaries
    boundaries = analyzer.identify_letter_boundaries()

    # Step 5: Extract letters
    letters = analyzer.extract_letters(boundaries)

    # Step 6: Verify quality
    verification = analyzer.verify_extraction_quality()

    # Step 7: Generate report
    report = analyzer.generate_report()

    # Step 8: Save letters
    analyzer.save_letters()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Pages: {analyzer.total_pages}")
    print(f"Letters Extracted: {len(letters)}")
    print(f"Page Coverage: {verification['checks']['page_coverage']['coverage_percentage']:.1f}%")
    print(f"Avg Words/Letter: {verification['checks']['letter_completeness']['avg_words_per_letter']:.0f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
