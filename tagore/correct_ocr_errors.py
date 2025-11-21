#!/usr/bin/env python3
"""
Correct common OCR errors in extracted letters
"""

import re
import json
from pathlib import Path
from datetime import datetime

class OCRCorrector:
    """Fix common OCR errors in Tagore letters"""

    def __init__(self, letters_dir="output/letters"):
        self.letters_dir = Path(letters_dir)
        self.corrections_made = []

        # Common OCR error patterns
        self.corrections = {
            # Number/letter substitutions
            r'\b1s\b': 'is',
            r'\b1t\b': 'it',
            r'\b1n\b': 'in',
            r'\b1f\b': 'if',
            r'\b1([a-z])': r'i\1',  # 1mmense -> immense
            r'\bfo1\b': 'for',
            r'\bca1': 'car',  # ca1ousal -> carousal
            r'([a-z])1([a-z])': r'\1r\2',  # wa1k -> walk, ca1ry -> carry

            # Specific word corrections
            r'\bLetiers\b': 'Letters',
            r'\bTam\b': 'I am',
            r'\bmych\b': 'much',
            r'\bthiough\b': 'through',
            r'\bcarty\b': 'carry',
            r'\bwateis\b': 'waters',
            r'\bhampeting\b': 'hampering',
            r'\bgieat': 'great',
            r'\bmatetials\b': 'materials',
            r'\bcertaM': 'certain',
            r'\baliow\b': 'allow',
            r'\bmui mur\b': 'murmur',
            r'\bfur\b': 'for',  # context dependent, may need manual review
            r'\bHulls\b': 'Hills',
            r'\biecognize\b': 'recognize',
            r'\brecogmize\b': 'recognize',
            r'\bhoard:': 'board:',

            # Punctuation errors
            r'notice-hoard': 'notice-board',
            r'unnatural\]': 'unnatural',

            # Common hyphenation errors at line breaks
            r'hampet-ing': 'hampering',
            r'germni-\s*ation': 'germination',
            r'Santini-\s*ketan': 'Santiniketan',

            # Page number artifacts (remove)
            r'\n\n\d+\s+Letters to a Friend\n': '\n',
            r'\n\d+\s+Letiers to a Friend\n': '\n',
        }

        # Context-sensitive corrections (more complex)
        self.context_patterns = [
            # "1" at start of sentence should be "I"
            (r'(^|[.!?]\s+)1\s+', r'\1I '),
            # "1" before vowel often "I"
            (r'\b1([aeou])', r'I\1'),
        ]

    def correct_text(self, text):
        """Apply all corrections to text"""
        original = text
        corrections_log = []

        # Apply simple substitutions
        for pattern, replacement in self.corrections.items():
            matches = list(re.finditer(pattern, text))
            if matches:
                for match in matches:
                    corrections_log.append({
                        'pattern': pattern,
                        'matched': match.group(0),
                        'replacement': replacement,
                        'position': match.start()
                    })
                text = re.sub(pattern, replacement, text)

        # Apply context-sensitive corrections
        for pattern, replacement in self.context_patterns:
            text = re.sub(pattern, replacement, text)

        return text, corrections_log

    def process_letter(self, letter_num):
        """Process a single letter"""
        letter_dir = self.letters_dir / f"letter_{letter_num:03d}"

        if not letter_dir.exists():
            return None

        txt_file = letter_dir / "letter.txt"
        md_file = letter_dir / "letter.md"

        if not txt_file.exists():
            return None

        # Read original text
        with open(txt_file, 'r', encoding='utf-8') as f:
            original_txt = f.read()

        # Correct text
        corrected_txt, corrections = self.correct_text(original_txt)

        if corrected_txt == original_txt:
            return {'letter': letter_num, 'corrections': 0}

        # Save corrected text
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(corrected_txt)

        # Update markdown file
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # Extract metadata section
            parts = md_content.split('---\n', 2)
            if len(parts) == 3:
                header, meta, content = parts
                corrected_content, _ = self.correct_text(content)
                new_md = f"{header}---\n{meta}---\n{corrected_content}"

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_md)

        return {
            'letter': letter_num,
            'corrections': len(corrections),
            'details': corrections[:10]  # First 10 corrections
        }

    def process_all_letters(self):
        """Process all letters in the collection"""
        results = []
        total_corrections = 0

        letter_dirs = sorted(self.letters_dir.glob("letter_*"))

        for letter_dir in letter_dirs:
            letter_num = int(letter_dir.name.split('_')[1])
            result = self.process_letter(letter_num)

            if result:
                results.append(result)
                total_corrections += result['corrections']

                if result['corrections'] > 0:
                    print(f"✓ Letter {letter_num:03d}: {result['corrections']} corrections")

        return results, total_corrections

    def generate_report(self, results):
        """Generate correction report"""
        report_file = self.letters_dir / "ocr_corrections_report.json"

        report = {
            'total_letters_processed': len(results),
            'total_corrections': sum(r['corrections'] for r in results),
            'letters_with_errors': [r for r in results if r['corrections'] > 0],
            'timestamp': datetime.utcnow().isoformat()
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        return report


def main():
    print("OCR Error Correction Tool")
    print("=" * 60)

    corrector = OCRCorrector()

    print("\nProcessing all letters...")
    results, total = corrector.process_all_letters()

    print(f"\n{'=' * 60}")
    print("CORRECTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Letters processed: {len(results)}")
    print(f"Total corrections: {total}")
    print(f"Letters with errors: {sum(1 for r in results if r['corrections'] > 0)}")

    # Generate report
    report = corrector.generate_report(results)
    print(f"\nReport saved: {corrector.letters_dir}/ocr_corrections_report.json")

    # Show top errors
    letters_with_most_errors = sorted(
        [r for r in results if r['corrections'] > 0],
        key=lambda x: x['corrections'],
        reverse=True
    )[:10]

    if letters_with_most_errors:
        print("\nLetters with most corrections:")
        for r in letters_with_most_errors:
            print(f"  Letter {r['letter']:03d}: {r['corrections']} corrections")


if __name__ == '__main__':
    main()
