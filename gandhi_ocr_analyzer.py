#!/usr/bin/env python3
"""
Gandhi Letters OCR Analyzer and Improver
Analyzes OCR quality, extracts letters, and fixes common errors
"""

import re
import json
from typing import List, Dict, Tuple
from collections import Counter

class GandhiLetterOCRAnalyzer:
    def __init__(self, ocr_file_path: str):
        self.ocr_file_path = ocr_file_path
        with open(ocr_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.raw_text = f.read()
        self.lines = self.raw_text.split('\n')

        # Common OCR errors specific to this document
        self.ocr_corrections = {
            # Common character substitutions
            'IVHabatma': 'Mahatma',
            'IVIahatma': 'Mahatma',
            'Grandlii': 'Gandhi',
            'Grandhiji': 'Gandhiji',
            'G-andhiji': 'Gandhiji',
            'G-andhijt': 'Gandhiji',
            'Sesidea': 'Besides',
            'Bi(^;raphical': 'Biographical',
            'docuixiezits': 'documents',
            'lt>e': 'be',
            'KHIPPLB': 'KHIPPLE',
            'KACZHERI': 'KACHERI',
            'KACZHBRI': 'KACHERI',
            'COMPIIED': 'COMPILED',
            'Dll ED': 'EDITED',
            'COPYBIGBTS': 'COPYRIGHTS',
            'PtiiOtd': 'Printed',
            'Pttiliskad': 'Published',
            'Z.akorS': 'Lahore',
            'Wmiu': 'Works',
            'Poadf': 'Road',
            'Karmn': 'Karman',
            'tha ': 'the ',
            "I'o ": 'To ',
            'Voungmen': 'Youngmen',
            'En^ishman': 'Englishman',
            'Linlithow': 'Linlithgow',
            'Chemlsford': 'Chelmsford',
            ' R& ': ' Rs ',
            'Aathor': 'Author',
            'Pack': 'Page',
            'chUdren': 'children',
            'Rejoindei': 'Rejoinder',
            'Highnes': 'Highness',
            ' Sk ': ' Sir ',
            ' tlie ': ' the ',
            ' llie ': ' the ',
            'invaltiatole': 'invaluable',
            ' hy ': ' by ',
            ' liave ': ' have ',
            'tlie': 'the',
            'llie': 'the',
        }

        # Patterns for letter boundaries
        self.letter_patterns = [
            r'^LETTER TO ',
            r'^Letter to ',
            r'^LETTERS TO ',
            r'^Letters to ',
            r'^To [A-Z]',
            r'^TO [A-Z]',
        ]

    def apply_corrections(self, text: str) -> str:
        """Apply OCR corrections to text"""
        corrected = text
        for wrong, right in self.ocr_corrections.items():
            corrected = corrected.replace(wrong, right)
        return corrected

    def find_letter_boundaries(self) -> List[Dict]:
        """Find all letter boundaries in the document"""
        letters = []
        current_letter = None

        for i, line in enumerate(self.lines):
            line_stripped = line.strip()

            # Check if this is a letter header
            is_letter_header = False
            for pattern in self.letter_patterns:
                if re.match(pattern, line_stripped):
                    is_letter_header = True
                    break

            if is_letter_header:
                # Save previous letter if exists
                if current_letter:
                    current_letter['end_line'] = i - 1
                    letters.append(current_letter)

                # Start new letter
                current_letter = {
                    'start_line': i,
                    'header': line_stripped,
                    'recipient': self._extract_recipient(line_stripped)
                }

        # Save last letter
        if current_letter:
            current_letter['end_line'] = len(self.lines) - 1
            letters.append(current_letter)

        return letters

    def _extract_recipient(self, header: str) -> str:
        """Extract recipient name from letter header"""
        # Remove "LETTER TO" or "TO" prefix
        recipient = re.sub(r'^(LETTER[S]? TO|TO)\s+', '', header, flags=re.IGNORECASE)
        return recipient.strip()

    def detect_ocr_errors(self) -> List[Dict]:
        """Detect potential OCR errors"""
        errors = []

        # Common OCR error patterns
        patterns = {
            'mixed_case': r'[a-z][A-Z]|[A-Z][a-z][A-Z]',  # Unusual case mixing
            'repeated_chars': r'(.)\1{3,}',  # Same character 4+ times
            'special_chars': r'[^a-zA-Z0-9\s\.\,\;\:\!\?\-\'\"\(\)\[\]\/]',  # Unusual special chars
            'broken_words': r'\b\w{1,2}\>\w+',  # Words with > or < breaking them
            'digit_in_word': r'[a-zA-Z]+\d+[a-zA-Z]+',  # Digits mixed in words
        }

        for i, line in enumerate(self.lines):
            for error_type, pattern in patterns.items():
                matches = re.finditer(pattern, line)
                for match in matches:
                    errors.append({
                        'line': i,
                        'type': error_type,
                        'text': match.group(),
                        'context': line.strip()
                    })

        return errors

    def analyze_completeness(self) -> Dict:
        """Analyze if all letters are present based on table of contents"""
        toc_entries = []
        in_toc = False

        for line in self.lines:
            if 'TABLE OF CONTENTS' in line:
                in_toc = True
                continue

            if in_toc:
                # Look for numbered entries
                match = re.match(r'^\d+\.\s+(.+)', line.strip())
                if match:
                    toc_entries.append(match.group(1).strip())
                elif line.strip() and not re.match(r'^\d+$', line.strip()) and 'Page' not in line:
                    # Check if it's a continuation of previous entry
                    if toc_entries and not re.match(r'^\d+\.', line.strip()):
                        toc_entries[-1] += ' ' + line.strip()

                # Stop at the end of TOC (usually indicated by blank lines or start of content)
                if in_toc and len(toc_entries) > 5 and line.strip() == '':
                    # Check if next non-empty line starts content
                    break

        # Find actual letters in document
        letters_found = self.find_letter_boundaries()

        return {
            'toc_count': len(toc_entries),
            'toc_entries': toc_entries,
            'letters_found': len(letters_found),
            'letters': [l['recipient'] for l in letters_found]
        }

    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 80)
        report.append("GANDHI LETTERS OCR ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Basic statistics
        report.append("## BASIC STATISTICS")
        report.append(f"Total lines: {len(self.lines)}")
        report.append(f"Total characters: {len(self.raw_text)}")
        report.append(f"Total words: {len(self.raw_text.split())}")
        report.append("")

        # Completeness analysis
        report.append("## COMPLETENESS ANALYSIS")
        completeness = self.analyze_completeness()
        report.append(f"Letters in Table of Contents: {completeness['toc_count']}")
        report.append(f"Letters found in document: {completeness['letters_found']}")
        report.append("")

        report.append("### Table of Contents Entries:")
        for i, entry in enumerate(completeness['toc_entries'], 1):
            report.append(f"  {i}. {entry}")
        report.append("")

        report.append("### Letters Found in Document:")
        letters = self.find_letter_boundaries()
        for i, letter in enumerate(letters, 1):
            report.append(f"  {i}. To: {letter['recipient']} (lines {letter['start_line']}-{letter['end_line']})")
        report.append("")

        # OCR errors
        report.append("## OCR ERRORS DETECTED")
        errors = self.detect_ocr_errors()
        error_counts = Counter([e['type'] for e in errors])
        report.append(f"Total potential errors: {len(errors)}")
        report.append("")
        for error_type, count in error_counts.most_common():
            report.append(f"  {error_type}: {count} occurrences")
        report.append("")

        # Sample errors
        report.append("### Sample OCR Errors (first 20):")
        for error in errors[:20]:
            report.append(f"  Line {error['line']}: [{error['type']}] '{error['text']}'")
            report.append(f"    Context: {error['context'][:80]}")
        report.append("")

        # Known corrections that will be applied
        report.append("## OCR CORRECTIONS TO BE APPLIED")
        report.append(f"Total known corrections: {len(self.ocr_corrections)}")
        report.append("")
        for wrong, right in list(self.ocr_corrections.items())[:30]:
            report.append(f"  '{wrong}' → '{right}'")
        report.append("")

        return "\n".join(report)

    def extract_and_save_letters(self, output_dir: str):
        """Extract individual letters and save them"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        letters = self.find_letter_boundaries()

        for i, letter in enumerate(letters, 1):
            # Extract letter content
            letter_lines = self.lines[letter['start_line']:letter['end_line']+1]
            letter_text = '\n'.join(letter_lines)

            # Apply corrections
            corrected_text = self.apply_corrections(letter_text)

            # Create filename
            recipient_slug = re.sub(r'[^a-z0-9]+', '_', letter['recipient'].lower())
            recipient_slug = recipient_slug.strip('_')[:50]
            filename = f"{i:02d}_{recipient_slug}.md"

            # Save letter
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"letter_number: {i}\n")
                f.write(f"recipient: \"{letter['recipient']}\"\n")
                f.write(f"source_lines: {letter['start_line']}-{letter['end_line']}\n")
                f.write(f"---\n\n")
                f.write(corrected_text)

        return len(letters)

    def save_corrected_full_text(self, output_file: str):
        """Save the fully corrected OCR text"""
        corrected_text = self.apply_corrections(self.raw_text)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(corrected_text)


def main():
    import sys
    import os

    # File paths
    ocr_file = '/home/user/poesis/gandhi_letters/ocr_text.txt'
    report_file = '/home/user/poesis/gandhi_letters/analysis_report.txt'
    corrected_file = '/home/user/poesis/gandhi_letters/corrected_full_text.txt'
    letters_dir = '/home/user/poesis/gandhi_letters/individual_letters'

    print("Initializing Gandhi Letters OCR Analyzer...")
    analyzer = GandhiLetterOCRAnalyzer(ocr_file)

    print("\nGenerating analysis report...")
    report = analyzer.generate_report()
    print(report)

    # Save report
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✓ Report saved to: {report_file}")

    # Save corrected full text
    print("\nApplying OCR corrections to full text...")
    analyzer.save_corrected_full_text(corrected_file)
    print(f"✓ Corrected text saved to: {corrected_file}")

    # Extract individual letters
    print("\nExtracting individual letters...")
    num_letters = analyzer.extract_and_save_letters(letters_dir)
    print(f"✓ Extracted {num_letters} letters to: {letters_dir}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
