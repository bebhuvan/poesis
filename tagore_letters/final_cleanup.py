#!/usr/bin/env python3
"""
Final comprehensive cleanup - fix remaining issues found in manual review
"""

import re
from pathlib import Path

class FinalCleanup:
    """Final pass to fix all remaining issues"""

    def __init__(self):
        self.letters_dir = Path('extracted_letters_thorough')
        self.changes = []

        # Additional OCR errors found in manual review
        self.final_fixes = {
            # Common OCR errors
            'gerfnination': 'germination',
            'biith': 'birth',
            'lilce': 'like',
            'greatncss': 'greatness',
            'holdmg': 'holding',
            'Yobk': 'York',
            'intb': 'into',
            'mediasval': 'medieval',
            'ol ': 'of ',
            'remams': 'remains',
            'rmssion': 'mission',
            'drovmed': 'drowned',
            'cany': 'carry',
            'semce': 'service',
            'unreseivedly': 'unreservedly',
            'caiousal': 'carousal',
            'muimur': 'murmur',
            'wateis': 'waters',
            'tire ': 'the ',
            'rewairied': 'rewarded',
            'galhered': 'gathered',
            'uttei': 'utter',
            'spiing': 'spring',
            'fellowworkers': 'fellow-workers',
            'itself m ': 'itself in ',
            ' m ': ' in ',  # Common OCR error m→in

            # Apostrophe spacing
            'Haven *t': "Haven't",
            'don *t': "don't",
            'can *t': "can't",
            'won *t': "won't",
            'doesn *t': "doesn't",
            'isn *t': "isn't",
            'aren *t': "aren't",

            # Common character errors
            'you^': 'you',
            'Yori^': 'York',
            '^': '',  # Remove stray ^

            # Date OCR errors
            '2,othj': '20th,',
            'aisr': '21st',
            'zsih': '25th',
            'igzo': '1920',
            'igao': '1920',
        }

    def remove_page_artifacts(self, text):
        """Remove remaining page number and header artifacts"""

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip page artifacts
            if re.match(r'^\d+\s+Letters to a Friend', stripped):
                continue
            if re.match(r'^Letters to a Friend\s+\d+', stripped):
                continue
            if stripped == 'Letters to a Friend':
                continue
            if re.match(r'^\d{1,3}$', stripped) and len(stripped) <= 3:
                # Standalone page numbers
                continue
            if re.match(r'^[io]{1,3}$', stripped):  # OCR'd page numbers
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def fix_text(self, text):
        """Apply all final fixes"""

        # Apply OCR fixes
        for error, fix in self.final_fixes.items():
            if error in text:
                text = text.replace(error, fix)
                self.changes.append(f"Fixed: '{error}' → '{fix}'")

        # Remove page artifacts
        original = text
        text = self.remove_page_artifacts(text)
        if text != original:
            self.changes.append("Removed page artifacts")

        # Fix excessive blank lines
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        # Final spacing cleanup
        text = re.sub(r' +', ' ', text)

        return text

    def process_all(self):
        """Process all letters"""

        print("=" * 80)
        print("FINAL COMPREHENSIVE CLEANUP")
        print("=" * 80)
        print()

        letter_files = sorted(self.letters_dir.glob('letter_*.md'))
        modified_count = 0

        for letter_file in letter_files:
            self.changes = []

            with open(letter_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original = content
            content = self.fix_text(content)

            if content != original:
                with open(letter_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_count += 1
                print(f"✓ {letter_file.name}")
                for change in self.changes[:3]:
                    print(f"    {change}")
                if len(self.changes) > 3:
                    print(f"    ... and {len(self.changes)-3} more")

        print()
        print("=" * 80)
        print(f"COMPLETE: Modified {modified_count} letters")
        print("=" * 80)

        return modified_count


if __name__ == '__main__':
    cleanup = FinalCleanup()
    count = cleanup.process_all()
    print(f"\n✓ Final cleanup complete!")
