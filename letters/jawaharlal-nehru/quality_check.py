#!/usr/bin/env python3
"""
Comprehensive quality assurance checker for extracted letters.
Performs automated verification of completeness, accuracy, and formatting.
"""

import re
import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple


class QualityChecker:
    """Automated quality assurance for extracted letters"""

    def __init__(self, letters_dir: str):
        self.letters_dir = Path(letters_dir)
        self.issues = []
        self.warnings = []
        self.stats = {}

    def check_all(self):
        """Run all quality checks"""
        print("=" * 80)
        print("COMPREHENSIVE QUALITY ASSURANCE CHECK")
        print("=" * 80)

        self.check_file_completeness()
        self.check_sequential_numbering()
        self.check_metadata_consistency()
        self.check_ocr_artifacts()
        self.check_letter_lengths()
        self.check_paragraph_structure()
        self.check_common_words()
        self.check_suspicious_patterns()

        self.print_report()

    def check_file_completeness(self):
        """Verify all 31 letters are present"""
        print("\n[1/8] Checking file completeness...")

        expected_count = 31
        letter_files = sorted(self.letters_dir.glob("letter-*.md"))
        actual_count = len(letter_files)

        if actual_count == expected_count:
            print(f"  ✓ All {expected_count} letters present")
        else:
            self.issues.append(f"Expected {expected_count} letters, found {actual_count}")
            print(f"  ✗ ISSUE: Expected {expected_count}, found {actual_count}")

        self.stats['total_files'] = actual_count

    def check_sequential_numbering(self):
        """Verify letters are numbered 1-31 with no gaps"""
        print("\n[2/8] Checking sequential numbering...")

        letter_files = sorted(self.letters_dir.glob("letter-*.md"))
        numbers = []

        for file in letter_files:
            match = re.search(r'letter-(\d+)-', file.name)
            if match:
                numbers.append(int(match.group(1)))

        numbers.sort()
        expected = list(range(1, 32))

        if numbers == expected:
            print(f"  ✓ Sequential numbering 1-31 confirmed")
        else:
            missing = set(expected) - set(numbers)
            duplicates = [n for n in numbers if numbers.count(n) > 1]

            if missing:
                self.issues.append(f"Missing letter numbers: {missing}")
                print(f"  ✗ ISSUE: Missing {missing}")
            if duplicates:
                self.issues.append(f"Duplicate letter numbers: {duplicates}")
                print(f"  ✗ ISSUE: Duplicates {duplicates}")

    def check_metadata_consistency(self):
        """Check YAML frontmatter consistency"""
        print("\n[3/8] Checking metadata consistency...")

        required_fields = [
            'title', 'letter_number', 'author', 'recipient',
            'date_written', 'written_from', 'written_to', 'collection'
        ]

        issues_count = 0

        for letter_file in sorted(self.letters_dir.glob("letter-*.md")):
            content = letter_file.read_text(encoding='utf-8')

            # Extract YAML frontmatter
            yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
            if not yaml_match:
                self.issues.append(f"{letter_file.name}: No YAML frontmatter found")
                issues_count += 1
                continue

            yaml_content = yaml_match.group(1)

            # Check required fields
            for field in required_fields:
                if f'{field}:' not in yaml_content:
                    self.warnings.append(f"{letter_file.name}: Missing field '{field}'")
                    issues_count += 1

        if issues_count == 0:
            print(f"  ✓ All metadata fields present and consistent")
        else:
            print(f"  ⚠ {issues_count} metadata issues found")

    def check_ocr_artifacts(self):
        """Look for common OCR errors that slipped through"""
        print("\n[4/8] Checking for OCR artifacts...")

        ocr_patterns = [
            (r'\b[Il1]{3,}\b', 'Multiple I/l/1 characters'),
            (r'\b\w*[|]\w*\b', 'Pipe characters in words'),
            (r'\b\w*rn\w*\b', 'Potential rn→m confusion'),
            (r'\bvv\w+\b', 'vv instead of w'),
            (r'\b[A-Z]{10,}\b', 'Excessive capitals'),
            (r'\s{3,}', 'Multiple spaces'),
            (r'[^\x00-\x7F]{10,}', 'Long non-ASCII sequences'),
            (r'\b\d+[A-Za-z]+\d+\b', 'Mixed numbers/letters'),
        ]

        total_issues = 0
        issue_details = []

        for letter_file in sorted(self.letters_dir.glob("letter-*.md")):
            content = letter_file.read_text(encoding='utf-8')

            # Remove YAML frontmatter for checking
            content = re.sub(r'^---.*?^---', '', content, flags=re.DOTALL | re.MULTILINE)

            for pattern, description in ocr_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    unique_matches = set(matches[:5])  # First 5 unique
                    issue_details.append(f"  {letter_file.name}: {description} - {unique_matches}")
                    total_issues += len(matches)

        if total_issues == 0:
            print(f"  ✓ No obvious OCR artifacts detected")
        else:
            print(f"  ⚠ {total_issues} potential OCR artifacts found")
            for detail in issue_details[:10]:  # Show first 10
                print(detail)
            if len(issue_details) > 10:
                print(f"  ... and {len(issue_details) - 10} more")

    def check_letter_lengths(self):
        """Check letter lengths for anomalies"""
        print("\n[5/8] Checking letter lengths...")

        lengths = []

        for letter_file in sorted(self.letters_dir.glob("letter-*.md")):
            content = letter_file.read_text(encoding='utf-8')
            # Get content after frontmatter
            match = re.search(r'^---.*?^---\n\n(.+)', content, re.DOTALL | re.MULTILINE)
            if match:
                letter_content = match.group(1)
                lengths.append((letter_file.name, len(letter_content)))

        if not lengths:
            print(f"  ✗ No letter content found!")
            return

        avg_length = sum(l[1] for l in lengths) / len(lengths)
        min_length = min(lengths, key=lambda x: x[1])
        max_length = max(lengths, key=lambda x: x[1])

        print(f"  ✓ Average length: {avg_length:.0f} characters")
        print(f"    Shortest: {min_length[0]} ({min_length[1]} chars)")
        print(f"    Longest: {max_length[0]} ({max_length[1]} chars)")

        # Flag unusually short letters
        for name, length in lengths:
            if length < 1000:
                self.warnings.append(f"{name}: Unusually short ({length} chars)")
                print(f"  ⚠ {name}: Only {length} characters (possible truncation?)")

        self.stats['avg_length'] = avg_length
        self.stats['min_length'] = min_length
        self.stats['max_length'] = max_length

    def check_paragraph_structure(self):
        """Verify paragraph structure looks reasonable"""
        print("\n[6/8] Checking paragraph structure...")

        issues_count = 0

        for letter_file in sorted(self.letters_dir.glob("letter-*.md")):
            content = letter_file.read_text(encoding='utf-8')

            # Get main content
            match = re.search(r'^# Letter \d+:.*?\n\n(.+?)(?=\n---|\Z)', content, re.DOTALL | re.MULTILINE)
            if not match:
                continue

            letter_content = match.group(1)

            # Count paragraphs
            paragraphs = [p.strip() for p in letter_content.split('\n\n') if p.strip()]

            # Check for anomalies
            if len(paragraphs) < 2:
                self.warnings.append(f"{letter_file.name}: Only {len(paragraphs)} paragraph(s)")
                issues_count += 1

            # Check for overly long paragraphs (likely OCR issue)
            for i, para in enumerate(paragraphs):
                if len(para) > 5000:
                    self.warnings.append(f"{letter_file.name}: Very long paragraph #{i+1} ({len(para)} chars)")
                    issues_count += 1

        if issues_count == 0:
            print(f"  ✓ Paragraph structure looks reasonable")
        else:
            print(f"  ⚠ {issues_count} paragraph structure issues")

    def check_common_words(self):
        """Verify common English words appear correctly"""
        print("\n[7/8] Checking common word spelling...")

        # Common words that should appear correctly
        test_words = ['the', 'and', 'that', 'this', 'when', 'which', 'who', 'what', 'where']

        all_text = ""
        for letter_file in sorted(self.letters_dir.glob("letter-*.md")):
            content = letter_file.read_text(encoding='utf-8')
            all_text += content.lower()

        issues_count = 0
        for word in test_words:
            count = all_text.count(f' {word} ')
            if count < 10:  # Should appear many times
                self.warnings.append(f"Word '{word}' appears only {count} times (possible OCR issue)")
                issues_count += 1

        if issues_count == 0:
            print(f"  ✓ Common words present as expected")
        else:
            print(f"  ⚠ {issues_count} common word issues")

    def check_suspicious_patterns(self):
        """Look for suspicious patterns that indicate problems"""
        print("\n[8/8] Checking for suspicious patterns...")

        suspicious = []

        for letter_file in sorted(self.letters_dir.glob("letter-*.md")):
            content = letter_file.read_text(encoding='utf-8')

            # Check for repeated characters (OCR glitch indicator)
            if re.search(r'(.)\1{5,}', content):
                suspicious.append(f"{letter_file.name}: Repeated character pattern")

            # Check for missing spaces after punctuation
            missing_spaces = len(re.findall(r'[.!?,][A-Z]', content))
            if missing_spaces > 10:
                suspicious.append(f"{letter_file.name}: {missing_spaces} missing spaces after punctuation")

            # Check for incomplete words (common OCR issue)
            if re.search(r'\b[bcdfghjklmnpqrstvwxyz]{8,}\b', content, re.IGNORECASE):
                suspicious.append(f"{letter_file.name}: Unusually long consonant sequence")

        if not suspicious:
            print(f"  ✓ No suspicious patterns detected")
        else:
            print(f"  ⚠ {len(suspicious)} suspicious patterns found:")
            for s in suspicious[:10]:
                print(f"    - {s}")

    def print_report(self):
        """Print final quality report"""
        print("\n" + "=" * 80)
        print("QUALITY ASSURANCE SUMMARY")
        print("=" * 80)

        print(f"\n📊 Statistics:")
        print(f"  Total files: {self.stats.get('total_files', 0)}")
        if 'avg_length' in self.stats:
            print(f"  Average length: {self.stats['avg_length']:.0f} characters")

        print(f"\n🔴 Critical Issues: {len(self.issues)}")
        for issue in self.issues:
            print(f"  ✗ {issue}")

        print(f"\n🟡 Warnings: {len(self.warnings)}")
        for warning in self.warnings[:20]:  # Show first 20
            print(f"  ⚠ {warning}")
        if len(self.warnings) > 20:
            print(f"  ... and {len(self.warnings) - 20} more warnings")

        if len(self.issues) == 0 and len(self.warnings) < 10:
            print("\n✅ OVERALL: Quality check PASSED - Ready for publication")
        elif len(self.issues) == 0:
            print("\n⚠️  OVERALL: Quality check PASSED with minor warnings")
        else:
            print("\n❌ OVERALL: Critical issues found - needs attention")


def main():
    base_dir = Path(__file__).parent
    letters_dir = base_dir / "final_letters/jawaharlal_nehru_1929"

    if not letters_dir.exists():
        print(f"ERROR: Letters directory not found: {letters_dir}")
        return

    checker = QualityChecker(letters_dir)
    checker.check_all()

    # Save report
    report_file = letters_dir / "QUALITY_REPORT.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Quality Assurance Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Critical Issues: {len(checker.issues)}\n")
        for issue in checker.issues:
            f.write(f"  - {issue}\n")
        f.write(f"\nWarnings: {len(checker.warnings)}\n")
        for warning in checker.warnings:
            f.write(f"  - {warning}\n")

    print(f"\n📄 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
