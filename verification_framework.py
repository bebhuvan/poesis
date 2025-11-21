#!/usr/bin/env python3
"""
Comprehensive Verification Framework for Tagore Letter Extraction
Multiple verification methodologies to ensure quality
"""

import re
import json
from typing import Dict, List
from collections import Counter


class VerificationFramework:
    """Multi-methodology verification of letter extraction quality"""

    def __init__(self, ocr_text: Dict[int, str], extracted_letters: List[Dict]):
        self.ocr_text = ocr_text
        self.letters = extracted_letters
        self.total_pages = len(ocr_text)
        self.verification_results = {}

    def run_all_verifications(self):
        """Run all verification checks"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE VERIFICATION FRAMEWORK")
        print("=" * 80)

        results = {}

        results['page_coverage'] = self.verify_page_coverage()
        results['content_completeness'] = self.verify_content_completeness()
        results['letter_structure'] = self.verify_letter_structure()
        results['metadata_quality'] = self.verify_metadata_quality()
        results['content_quality'] = self.verify_content_quality()
        results['sequential_integrity'] = self.verify_sequential_integrity()
        results['statistical_analysis'] = self.statistical_analysis()

        self.verification_results = results
        return results

    def verify_page_coverage(self):
        """Verification 1: Ensure all pages are covered by extracted letters"""
        print("\n🔍 Verification 1: Page Coverage Analysis")

        pages_covered = set()
        for letter in self.letters:
            for page in range(letter['start_page'], letter['end_page'] + 1):
                pages_covered.add(page)

        total_pages_set = set(range(self.total_pages))
        missing_pages = total_pages_set - pages_covered

        # Identify which missing pages likely contain content (not front matter)
        # Assume first 10 pages are front matter, last 5 might be appendix
        content_pages = set(range(10, self.total_pages - 5))
        missing_content_pages = content_pages - pages_covered

        coverage_pct = (len(pages_covered) / self.total_pages * 100) if self.total_pages else 0
        content_coverage_pct = (len(pages_covered & content_pages) / len(content_pages) * 100) if content_pages else 0

        result = {
            'total_pages': self.total_pages,
            'pages_covered': len(pages_covered),
            'pages_missing': len(missing_pages),
            'coverage_percentage': coverage_pct,
            'content_coverage_percentage': content_coverage_pct,
            'missing_pages': sorted(missing_content_pages)[:50],  # First 50
            'status': 'PASS' if content_coverage_pct > 80 else 'WARN' if content_coverage_pct > 50 else 'FAIL'
        }

        print(f"   Total pages: {self.total_pages}")
        print(f"   Pages covered: {len(pages_covered)} ({coverage_pct:.1f}%)")
        print(f"   Content coverage: {content_coverage_pct:.1f}%")
        print(f"   Status: {result['status']}")

        return result

    def verify_content_completeness(self):
        """Verification 2: Check if extracted content matches total document content"""
        print("\n🔍 Verification 2: Content Completeness Analysis")

        # Calculate total words in OCR text
        total_ocr_words = 0
        for text in self.ocr_text.values():
            total_ocr_words += len(text.split())

        # Calculate total words in extracted letters
        total_extracted_words = sum(l['word_count'] for l in self.letters)

        completeness_pct = (total_extracted_words / total_ocr_words * 100) if total_ocr_words else 0

        result = {
            'total_ocr_words': total_ocr_words,
            'total_extracted_words': total_extracted_words,
            'completeness_percentage': completeness_pct,
            'missing_words': total_ocr_words - total_extracted_words,
            'status': 'PASS' if completeness_pct > 70 else 'WARN' if completeness_pct > 40 else 'FAIL'
        }

        print(f"   Total OCR words: {total_ocr_words:,}")
        print(f"   Extracted words: {total_extracted_words:,}")
        print(f"   Completeness: {completeness_pct:.1f}%")
        print(f"   Status: {result['status']}")

        return result

    def verify_letter_structure(self):
        """Verification 3: Validate structure and formatting of each letter"""
        print("\n🔍 Verification 3: Letter Structure Validation")

        issues = []

        # Check for common structural problems
        empty_letters = []
        very_short_letters = []
        very_long_letters = []
        missing_markers = []

        for letter in self.letters:
            if letter['word_count'] == 0:
                empty_letters.append(letter['number'])

            if letter['word_count'] < 50:
                very_short_letters.append({
                    'number': letter['number'],
                    'words': letter['word_count']
                })

            if letter['word_count'] > 5000:
                very_long_letters.append({
                    'number': letter['number'],
                    'words': letter['word_count']
                })

            if not letter.get('marker'):
                missing_markers.append(letter['number'])

        result = {
            'total_letters': len(self.letters),
            'empty_letters': len(empty_letters),
            'very_short_letters': len(very_short_letters),
            'very_long_letters': len(very_long_letters),
            'missing_markers': len(missing_markers),
            'short_letter_details': very_short_letters[:10],
            'long_letter_details': very_long_letters[:10],
            'status': 'PASS' if len(empty_letters) == 0 and len(very_short_letters) < 5 else 'WARN'
        }

        print(f"   Total letters: {len(self.letters)}")
        print(f"   Empty letters: {len(empty_letters)}")
        print(f"   Very short (<50 words): {len(very_short_letters)}")
        print(f"   Very long (>5000 words): {len(very_long_letters)}")
        print(f"   Status: {result['status']}")

        return result

    def verify_metadata_quality(self):
        """Verification 4: Check quality of extracted metadata"""
        print("\n🔍 Verification 4: Metadata Quality Assessment")

        letters_with_dates = 0
        letters_with_recipients = 0
        date_formats = Counter()

        for letter in self.letters:
            # Check for date
            date_patterns = [
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)',
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
                r'\d{4}',  # Year
            ]

            for pattern in date_patterns:
                if re.search(pattern, letter['content'], re.IGNORECASE):
                    letters_with_dates += 1
                    break

            # Check for recipient
            recipient_patterns = [
                r'(?:Dear|My dear|To)\s+([A-Z][a-z]+)',
            ]

            for pattern in recipient_patterns:
                if re.search(pattern, letter['content']):
                    letters_with_recipients += 1
                    break

        date_rate = (letters_with_dates / len(self.letters) * 100) if self.letters else 0
        recipient_rate = (letters_with_recipients / len(self.letters) * 100) if self.letters else 0

        result = {
            'letters_with_dates': letters_with_dates,
            'letters_with_recipients': letters_with_recipients,
            'date_extraction_rate': date_rate,
            'recipient_extraction_rate': recipient_rate,
            'status': 'PASS' if date_rate > 30 else 'WARN'
        }

        print(f"   Letters with dates: {letters_with_dates}/{len(self.letters)} ({date_rate:.1f}%)")
        print(f"   Letters with recipients: {letters_with_recipients}/{len(self.letters)} ({recipient_rate:.1f}%)")
        print(f"   Status: {result['status']}")

        return result

    def verify_content_quality(self):
        """Verification 5: Assess OCR quality and content readability"""
        print("\n🔍 Verification 5: Content Quality Assessment")

        # Check for common OCR errors
        ocr_error_patterns = [
            (r'[^\w\s\.,;:!?\'\"-]', 'special_chars'),  # Unusual characters
            (r'\b\w{25,}\b', 'very_long_words'),  # Unrealistically long words
            (r'(?:^|\s)([A-Z]{5,})(?:\s|$)', 'all_caps_words'),  # Many all-caps words (OCR error)
        ]

        total_errors = Counter()
        letters_with_errors = []

        for letter in self.letters:
            letter_errors = Counter()

            for pattern, error_type in ocr_error_patterns:
                matches = re.findall(pattern, letter['content'])
                if matches:
                    letter_errors[error_type] = len(matches)
                    total_errors[error_type] += len(matches)

            if sum(letter_errors.values()) > 10:  # More than 10 errors
                letters_with_errors.append({
                    'number': letter['number'],
                    'errors': dict(letter_errors)
                })

        result = {
            'total_error_count': sum(total_errors.values()),
            'error_types': dict(total_errors),
            'letters_with_many_errors': len(letters_with_errors),
            'error_details': letters_with_errors[:10],
            'status': 'PASS' if len(letters_with_errors) < len(self.letters) * 0.2 else 'WARN'
        }

        print(f"   Total OCR errors detected: {sum(total_errors.values())}")
        print(f"   Letters with many errors: {len(letters_with_errors)}")
        print(f"   Status: {result['status']}")

        return result

    def verify_sequential_integrity(self):
        """Verification 6: Check for gaps or overlaps in sequential extraction"""
        print("\n🔍 Verification 6: Sequential Integrity Check")

        gaps = []
        overlaps = []

        for i in range(len(self.letters) - 1):
            current = self.letters[i]
            next_letter = self.letters[i + 1]

            # Check for gaps
            gap_size = next_letter['start_page'] - current['end_page']
            if gap_size > 2:  # More than 2 pages between letters
                gaps.append({
                    'after_letter': current['number'],
                    'before_letter': next_letter['number'],
                    'gap_pages': gap_size,
                    'pages': f"{current['end_page']}-{next_letter['start_page']}"
                })

            # Check for overlaps
            if next_letter['start_page'] <= current['end_page']:
                overlaps.append({
                    'letter1': current['number'],
                    'letter2': next_letter['number'],
                    'overlap_pages': current['end_page'] - next_letter['start_page'] + 1
                })

        result = {
            'total_gaps': len(gaps),
            'total_overlaps': len(overlaps),
            'gaps': gaps[:20],
            'overlaps': overlaps[:20],
            'status': 'PASS' if len(gaps) < 5 and len(overlaps) == 0 else 'WARN'
        }

        print(f"   Gaps between letters: {len(gaps)}")
        print(f"   Overlapping letters: {len(overlaps)}")
        print(f"   Status: {result['status']}")

        return result

    def statistical_analysis(self):
        """Verification 7: Statistical analysis of letter collection"""
        print("\n🔍 Verification 7: Statistical Analysis")

        if not self.letters:
            return {'status': 'FAIL', 'message': 'No letters to analyze'}

        word_counts = [l['word_count'] for l in self.letters]
        page_spans = [l['end_page'] - l['start_page'] + 1 for l in self.letters]

        result = {
            'total_letters': len(self.letters),
            'avg_words_per_letter': sum(word_counts) / len(word_counts),
            'min_words': min(word_counts),
            'max_words': max(word_counts),
            'avg_pages_per_letter': sum(page_spans) / len(page_spans),
            'min_pages': min(page_spans),
            'max_pages': max(page_spans),
            'status': 'PASS'
        }

        print(f"   Total letters: {len(self.letters)}")
        print(f"   Avg words/letter: {result['avg_words_per_letter']:.0f}")
        print(f"   Avg pages/letter: {result['avg_pages_per_letter']:.1f}")
        print(f"   Word count range: {result['min_words']}-{result['max_words']}")
        print(f"   Status: {result['status']}")

        return result

    def generate_report(self, output_file: str = 'verification_report.json'):
        """Generate comprehensive verification report"""
        report = {
            'summary': {
                'total_letters_extracted': len(self.letters),
                'total_pages': self.total_pages,
                'overall_status': self._calculate_overall_status()
            },
            'verifications': self.verification_results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Verification report saved to: {output_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Overall Status: {report['summary']['overall_status']}")
        print("\nIndividual Checks:")
        for check_name, check_result in self.verification_results.items():
            status = check_result.get('status', 'UNKNOWN')
            print(f"  {check_name:.<40} {status}")
        print("=" * 80)

        return report

    def _calculate_overall_status(self):
        """Calculate overall verification status"""
        if not self.verification_results:
            return 'UNKNOWN'

        statuses = [r.get('status', 'UNKNOWN') for r in self.verification_results.values()]

        if 'FAIL' in statuses:
            return 'FAIL'
        elif 'WARN' in statuses:
            return 'WARN'
        elif all(s == 'PASS' for s in statuses):
            return 'PASS'
        else:
            return 'UNKNOWN'


def main():
    import os

    # Load OCR text
    ocr_file = 'tagore_full_ocr.json'
    if not os.path.exists(ocr_file):
        print(f"⚠ {ocr_file} not found. Run full OCR extraction first.")
        return

    print("📂 Loading OCR text...")
    with open(ocr_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        ocr_text = {int(k): v for k, v in data.items()}

    # Load extracted letters (from best strategy)
    strategy_file = 'strategy_comparison.json'
    if not os.path.exists(strategy_file):
        print(f"⚠ {strategy_file} not found. Run multi-strategy extraction first.")
        return

    print("📂 Loading extracted letters...")
    with open(strategy_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Use first strategy's letters (assuming it's the best)
        letters = data['strategies'][0]['letters']

    print(f"✓ Loaded {len(ocr_text)} pages and {len(letters)} letters")

    # Run verification
    verifier = VerificationFramework(ocr_text, letters)
    verifier.run_all_verifications()
    verifier.generate_report()


if __name__ == '__main__':
    main()
