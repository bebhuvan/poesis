#!/usr/bin/env python3
"""
Comprehensive Verification System for Extracted Letters
Performs rigorous quality checks and identifies issues
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter


class LetterVerificationSystem:
    """Comprehensive verification for extracted letters"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters_dir = self.base_dir / 'final_letters'
        self.issues = []
        self.warnings = []
        self.stats = {}

    def run_all_checks(self):
        """Run all verification checks"""
        print("="*80)
        print("RUNNING COMPREHENSIVE VERIFICATION CHECKS")
        print("="*80)
        print()

        # Load index
        index_file = self.letters_dir / 'index.json'
        if not index_file.exists():
            self.issues.append("CRITICAL: index.json not found!")
            return

        with open(index_file) as f:
            self.index = json.load(f)

        # Run checks
        self.check_file_count()
        self.check_metadata_quality()
        self.check_sender_distribution()
        self.check_date_parsing()
        self.check_content_quality()
        self.check_verification_scores()
        self.check_letter_boundaries()
        self.check_for_preface_contamination()
        self.check_ocr_artifacts()
        self.check_source_files()
        self.check_duplicate_detection()

        # Print report
        self.print_report()

    def check_file_count(self):
        """Verify file count matches index"""
        print("✓ Checking file count...")

        md_files = list(self.letters_dir.glob('*.md'))
        index_count = len(self.index)
        file_count = len(md_files)

        if file_count != index_count:
            self.issues.append(f"File count mismatch: {file_count} files but {index_count} in index")
        else:
            print(f"  ✓ {file_count} files match index count")

        self.stats['total_files'] = file_count
        self.stats['index_entries'] = index_count

    def check_metadata_quality(self):
        """Check metadata completeness"""
        print("\n✓ Checking metadata quality...")

        missing_dates = 0
        missing_locations = 0
        unknown_senders = 0

        for entry in self.index:
            if not entry.get('date') or entry['date'] == '':
                missing_dates += 1
            if not entry.get('location') or entry['location'] == '':
                missing_locations += 1
            if entry.get('sender') == 'Unknown':
                unknown_senders += 1

        self.stats['missing_dates'] = missing_dates
        self.stats['missing_locations'] = missing_locations
        self.stats['unknown_senders'] = unknown_senders

        if missing_dates > 150:
            self.issues.append(f"Too many missing dates: {missing_dates}")
        else:
            print(f"  - Missing dates: {missing_dates}")

        if unknown_senders > 50:
            self.issues.append(f"CRITICAL: {unknown_senders} letters have unknown sender!")
        else:
            print(f"  - Unknown senders: {unknown_senders}")

        print(f"  - Missing locations: {missing_locations}")

    def check_sender_distribution(self):
        """Check sender distribution"""
        print("\n✓ Checking sender distribution...")

        senders = [entry['sender'] for entry in self.index]
        sender_counts = Counter(senders)

        print(f"  Sender breakdown:")
        for sender, count in sender_counts.most_common():
            print(f"    - {sender}: {count} letters")

        self.stats['sender_distribution'] = dict(sender_counts)

        # Expected: roughly equal between Schiller and Goethe
        schiller_count = sender_counts.get('Schiller', 0)
        goethe_count = sender_counts.get('Goethe', 0)
        unknown_count = sender_counts.get('Unknown', 0)

        if unknown_count > schiller_count or unknown_count > goethe_count:
            self.issues.append(f"CRITICAL: More Unknown ({unknown_count}) than identified senders")

    def check_date_parsing(self):
        """Check date parsing quality"""
        print("\n✓ Checking date parsing...")

        dated_letters = [e for e in self.index if e.get('date')]

        # Check date format
        date_pattern = r'[A-Z][a-z]+\s+\d+,\s+\d{4}'
        valid_dates = 0

        for entry in dated_letters:
            if re.match(date_pattern, entry['date']):
                valid_dates += 1

        print(f"  - Total dated letters: {len(dated_letters)}")
        print(f"  - Valid date format: {valid_dates}")

        if valid_dates < len(dated_letters) * 0.8:
            self.warnings.append("Many dates don't match expected format")

        self.stats['dated_letters'] = len(dated_letters)
        self.stats['valid_date_format'] = valid_dates

    def check_content_quality(self):
        """Check letter content quality"""
        print("\n✓ Checking content quality...")

        empty_letters = []
        very_short_letters = []
        very_long_letters = []

        for entry in self.index:
            word_count = entry.get('word_count', 0)

            if word_count == 0:
                empty_letters.append(entry['number'])
            elif word_count < 10:
                very_short_letters.append((entry['number'], word_count))
            elif word_count > 5000:
                very_long_letters.append((entry['number'], word_count))

        if empty_letters:
            self.issues.append(f"Empty letters found: {empty_letters}")

        if very_short_letters:
            self.warnings.append(f"Very short letters (< 10 words): {len(very_short_letters)}")
            print(f"  - Very short letters: {very_short_letters[:5]}...")

        if very_long_letters:
            self.warnings.append(f"Very long letters (> 5000 words): {len(very_long_letters)}")
            print(f"  - Very long letters: {very_long_letters[:5]}...")

        # Check word count distribution
        word_counts = [e.get('word_count', 0) for e in self.index]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

        print(f"  - Average letter length: {avg_words:.0f} words")
        print(f"  - Empty letters: {len(empty_letters)}")
        print(f"  - Very short (< 10 words): {len(very_short_letters)}")
        print(f"  - Very long (> 5000 words): {len(very_long_letters)}")

        self.stats['avg_word_count'] = avg_words
        self.stats['empty_letters'] = len(empty_letters)
        self.stats['very_short'] = len(very_short_letters)
        self.stats['very_long'] = len(very_long_letters)

    def check_verification_scores(self):
        """Check verification scores"""
        print("\n✓ Checking verification scores...")

        scores = [entry.get('verification_score', 0) for entry in self.index]
        avg_score = sum(scores) / len(scores) if scores else 0

        zero_scores = sum(1 for s in scores if s == 0)
        perfect_scores = sum(1 for s in scores if s == 100)

        print(f"  - Average verification score: {avg_score:.1f}%")
        print(f"  - Zero verification scores: {zero_scores}")
        print(f"  - Perfect scores (100%): {perfect_scores}")

        if zero_scores == len(scores):
            self.issues.append("CRITICAL: All letters have 0% verification score - verification failed!")
        elif zero_scores > len(scores) * 0.8:
            self.warnings.append(f"Most letters ({zero_scores}/{len(scores)}) have 0% verification")

        self.stats['avg_verification_score'] = avg_score
        self.stats['zero_verification'] = zero_scores

    def check_letter_boundaries(self):
        """Check if letter boundaries are correct"""
        print("\n✓ Checking letter boundaries...")

        # Read first 3 letters and check content
        issues_found = []

        for i in range(1, min(4, len(self.index) + 1)):
            filename = self.index[i-1]['filename']
            filepath = self.letters_dir / filename

            if filepath.exists():
                content = filepath.read_text()

                # Check for title page contamination
                if 'CORRESPONDENCE' in content and '1794 TO 1805' in content:
                    issues_found.append(f"Letter {i} contains title page content")

                # Check for preface contamination
                if 'PREFACE' in content or 'translator' in content.lower():
                    issues_found.append(f"Letter {i} contains preface content")

        if issues_found:
            for issue in issues_found:
                self.issues.append(issue)
            print(f"  ! Found {len(issues_found)} boundary issues")
        else:
            print(f"  ✓ First 3 letters appear clean")

    def check_for_preface_contamination(self):
        """Check for preface content in letters"""
        print("\n✓ Checking for preface contamination...")

        contaminated = []

        # Keywords that shouldn't appear in letters
        preface_keywords = [
            'translator', 'translation', 'preface', 'foreword',
            'Wiley and Putnam', 'published', 'volume contains'
        ]

        for entry in self.index[:10]:  # Check first 10 letters
            filename = entry['filename']
            filepath = self.letters_dir / filename

            if filepath.exists():
                content = filepath.read_text().lower()

                for keyword in preface_keywords:
                    if keyword.lower() in content:
                        contaminated.append((entry['number'], keyword))
                        break

        if contaminated:
            self.issues.append(f"Preface contamination in {len(contaminated)} letters: {contaminated[:3]}")
            print(f"  ! {len(contaminated)} letters may have preface content")
        else:
            print(f"  ✓ No preface contamination detected")

    def check_ocr_artifacts(self):
        """Check for common OCR artifacts"""
        print("\n✓ Checking for OCR artifacts...")

        artifacts_found = Counter()

        # Common OCR errors
        patterns = {
            'v^': r'v\^',  # v^ instead of w
            'misplaced_punctuation': r'\s+[,.]',
            'double_spaces': r'  +',
            'broken_words': r'\w-\s+\w',
        }

        for entry in self.index[:20]:  # Sample first 20
            filename = entry['filename']
            filepath = self.letters_dir / filename

            if filepath.exists():
                content = filepath.read_text()

                for artifact_name, pattern in patterns.items():
                    matches = len(re.findall(pattern, content))
                    if matches > 0:
                        artifacts_found[artifact_name] += matches

        if artifacts_found:
            print(f"  OCR artifacts detected (in first 20 letters):")
            for artifact, count in artifacts_found.most_common():
                print(f"    - {artifact}: {count} occurrences")

            if artifacts_found['v^'] > 10:
                self.warnings.append("High 'v^' artifact count - cleanup may be needed")
        else:
            print(f"  ✓ No major OCR artifacts in sample")

        self.stats['ocr_artifacts'] = dict(artifacts_found)

    def check_source_files(self):
        """Verify source files are present"""
        print("\n✓ Checking source files...")

        sources = {
            'ABBYY confidence report': 'raw_ocr/abbyy/abbyy_confidence_report.json',
            'Full text': 'raw_ocr/full_text.txt',
            'DjVu XML': 'raw_ocr/hocr/djvu.xml',
            'Extraction report': 'verification/extraction_report.json'
        }

        missing = []
        for name, path in sources.items():
            full_path = self.base_dir / path
            if not full_path.exists():
                missing.append(name)
            else:
                size = full_path.stat().st_size
                print(f"  ✓ {name}: {size:,} bytes")

        if missing:
            self.warnings.append(f"Missing source files: {missing}")

    def check_duplicate_detection(self):
        """Check for potential duplicate letters"""
        print("\n✓ Checking for duplicates...")

        # Check if multiple letters have identical word counts
        word_counts = Counter([e.get('word_count', 0) for e in self.index])

        suspicious_duplicates = [(wc, count) for wc, count in word_counts.items()
                                if count > 3 and wc > 0]

        if suspicious_duplicates:
            print(f"  ! Potential duplicates found:")
            for wc, count in suspicious_duplicates[:5]:
                print(f"    - {count} letters with {wc} words")
            self.warnings.append(f"{len(suspicious_duplicates)} groups of potentially duplicate letters")
        else:
            print(f"  ✓ No obvious duplicates detected")

    def print_report(self):
        """Print comprehensive verification report"""
        print("\n" + "="*80)
        print("VERIFICATION REPORT")
        print("="*80)

        print(f"\n📊 STATISTICS")
        print("-" * 80)
        for key, value in self.stats.items():
            print(f"  {key}: {value}")

        print(f"\n⚠️  WARNINGS ({len(self.warnings)})")
        print("-" * 80)
        if self.warnings:
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        else:
            print("  ✓ No warnings")

        print(f"\n🚨 ISSUES ({len(self.issues)})")
        print("-" * 80)
        if self.issues:
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("  ✓ No critical issues found")

        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT")
        print("-" * 80)

        if len(self.issues) == 0 and len(self.warnings) < 3:
            print("  ✅ EXCELLENT - Extraction quality is very good")
        elif len(self.issues) == 0:
            print("  ⚠️  GOOD - Some warnings but no critical issues")
        elif len(self.issues) < 3:
            print("  ⚠️  ACCEPTABLE - Some issues need attention")
        else:
            print("  ❌ NEEDS WORK - Multiple critical issues found")

        # Save report
        report_file = self.base_dir / 'verification' / 'verification_report.json'
        report_file.parent.mkdir(exist_ok=True)

        report_data = {
            'statistics': self.stats,
            'warnings': self.warnings,
            'issues': self.issues
        }

        report_file.write_text(json.dumps(report_data, indent=2))
        print(f"\n📄 Report saved to: {report_file}")


if __name__ == '__main__':
    import sys

    base_dir = sys.argv[1] if len(sys.argv) > 1 else '/home/user/poesis/letters/schiller-goethe'

    verifier = LetterVerificationSystem(base_dir)
    verifier.run_all_checks()
