#!/usr/bin/env python3
"""
Post-processing to clean up extracted letters
Fixes hyphenation, OCR errors, and formatting issues
"""

import re
from pathlib import Path
import json

class LetterCleaner:
    """Clean and verify extracted letters"""

    def __init__(self, letters_dir='extracted_letters_complete'):
        self.letters_dir = Path(letters_dir)

        # Additional OCR errors not caught in first pass
        self.ocr_fixes = {
            'gerfni-\nnation': 'germination',
            'gerfnination': 'germination',
            'tlie': 'the',
            'mexely': 'merely',
            'teed': 'feed',
            'stiuggle': 'struggle',
            'countiy': 'country',
            'stianded': 'stranded',
            'fiom': 'from',
            'valu•able': 'valuable',
            'theie': 'there',
            'diiect': 'direct',
            'difticult': 'difficult',
            'woik': 'work',
            'foi': 'for',
            'heie': 'here',
            'aie': 'are',
            'lealized': 'realized',
            'icalize': 'realize',
            'piesent': 'present',
            'letteis': 'letters',
            'youi': 'your',
            'tliat': 'that',
            'thiough': 'through',
            'thioats': 'throats',
            'moie': 'more',
            'ovei': 'over',
            'veiy': 'very',
            'evei': 'ever',
            'leally': 'really',
            'theii': 'their',
            'whele': 'where',
            'sciiptures': 'scriptures',
            'chaiacter': 'character',
            'wliich': 'which',
            'vaiious': 'various',
        }

        # Patterns for embedded letter headers that shouldn't be there
        self.header_pattern = re.compile(
            r'(Letters to a Friend\s+)?([A-Z][a-z]+(?:,\s+[A-Z][a-z]+)?),?\s+([A-Z][a-z]+\s+\d+[a-z/\^$\*]*,?\s+\d{4})',
            re.MULTILINE
        )

    def fix_hyphenation(self, text):
        """Fix words broken across lines with hyphens"""
        # Match word-\nword and rejoin
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        return text

    def fix_ocr_errors(self, text):
        """Fix common OCR errors"""
        for error, fix in self.ocr_fixes.items():
            text = text.replace(error, fix)
        return text

    def remove_embedded_headers(self, text):
        """Remove letter headers that appear mid-letter"""
        lines = text.split('\n')
        cleaned_lines = []
        in_frontmatter = False
        frontmatter_count = 0

        for i, line in enumerate(lines):
            # Track frontmatter (between ---  markers)
            if line.strip() == '---':
                frontmatter_count += 1
                in_frontmatter = frontmatter_count < 2
                cleaned_lines.append(line)
                continue

            # Skip "Letters to a Friend" page headers
            if 'Letters to a Friend' in line and not in_frontmatter:
                continue

            # Check if this looks like an embedded letter header
            # But preserve the actual letter header in the markdown
            if not in_frontmatter and i > 20:  # After frontmatter and main header
                match = self.header_pattern.search(line)
                if match:
                    # This looks like another letter's header embedded in the text
                    # Skip it
                    continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def clean_letter(self, filepath):
        """Clean a single letter file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Apply fixes
        content = self.fix_hyphenation(content)
        content = self.fix_ocr_errors(content)
        content = self.remove_embedded_headers(content)

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def clean_all(self):
        """Clean all letter files"""
        letter_files = sorted(self.letters_dir.glob('letter_*.md'))

        print(f"Cleaning {len(letter_files)} letters...")

        for i, filepath in enumerate(letter_files, 1):
            self.clean_letter(filepath)
            if i % 10 == 0:
                print(f"  Cleaned {i}/{len(letter_files)}...")

        print(f"✓ All {len(letter_files)} letters cleaned")

        return len(letter_files)

    def verify_quality(self):
        """Check for remaining issues"""
        letter_files = sorted(self.letters_dir.glob('letter_*.md'))

        print("\nVerifying quality...")
        issues = []

        for filepath in letter_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for common problems
            if content.count('---') < 2:
                issues.append(f"{filepath.name}: Missing frontmatter")

            if len(content) < 100:
                issues.append(f"{filepath.name}: Suspiciously short ({len(content)} chars)")

            # Check for remaining OCR patterns
            if re.search(r'\w{1,3}[/\^$\*]{1,2}\w', content):
                issues.append(f"{filepath.name}: Possible OCR errors remaining")

        if issues:
            print(f"\n⚠ Found {len(issues)} potential issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"  - {issue}")
        else:
            print("✓ No obvious issues found")

        return issues


def main():
    print("=" * 80)
    print("LETTER CLEANING AND VERIFICATION")
    print("=" * 80)
    print()

    cleaner = LetterCleaner()
    count = cleaner.clean_all()
    issues = cleaner.verify_quality()

    print()
    print("=" * 80)
    print(f"CLEANING COMPLETE: {count} letters processed")
    if not issues:
        print("✓ All letters appear clean and well-formatted")
    print("=" * 80)


if __name__ == '__main__':
    main()
