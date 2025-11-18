#!/usr/bin/env python3
"""
Manual fixes for all letters - presentation and formatting
"""

import re
from pathlib import Path

class LetterFixer:
    """Apply manual fixes to all letters"""

    def __init__(self):
        self.letters_dir = Path('extracted_letters_thorough')
        self.changes_log = []

        # Real OCR errors to fix
        self.ocr_fixes = {
            # Spacing around punctuation
            ' ;': ';',
            ' :': ':',
            ' ,': ',',
            ' .': '.',
            '  ': ' ',

            # Real OCR errors
            'tlie': 'the',
            'tiie': 'the',
            'tliat': 'that',
            'wliich': 'which',
            'witli': 'with',
            'wlien': 'when',
            'wlio': 'who',
            'wliat': 'what',
            'whicli': 'which',
            'theie': 'there',
            'wheie': 'where',
            'theil': 'their',
            'youi': 'your',
            'oui': 'our',
            'foi': 'for',
            'fiom': 'from',
            'aie': 'are',
            'woik': 'work',
            'yeai': 'year',
            'moie': 'more',
            'heie': 'here',
            'theii': 'their',
            'fiiend': 'friend',
            'thiough': 'through',
            'tlirough': 'through',
            'thioats': 'throats',
            'leally': 'really',
            'icalize': 'realize',
            'lealized': 'realized',
            'piesent': 'present',
            'letteis': 'letters',
            'diiect': 'direct',
            'difticult': 'difficult',
            'evei': 'ever',
            'ovei': 'over',
            'valu•able': 'valuable',
            'elsewheie': 'elsewhere',
            'fieedom': 'freedom',
            'fi om': 'from',
            'befoie': 'before',
            'stiuggle': 'struggle',
            'countiy': 'country',
            'stianded': 'stranded',
            'tuimoil': 'turmoil',
            'nieet': 'meet',
            'ignoied': 'ignored',
            'seiwice': 'service',
            'Plospital': 'Hospital',
            'mateiials': 'materials',
            'gieatly': 'greatly',
            'woild': 'world',
            'miich': 'much',
            'veiy': 'very',
            'eveiy': 'every',
        }

    def fix_hyphenation(self, text):
        """Fix words hyphenated across line breaks"""

        # Pattern: word- followed by newline(s) and whitespace, then word
        fixed = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        if fixed != text:
            self.changes_log.append("Fixed hyphenated words across line breaks")

        return fixed

    def fix_spacing(self, text):
        """Fix spacing and punctuation issues"""

        original = text

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)

        # Fix multiple spaces
        text = re.sub(r'  +', ' ', text)

        # Fix space at start of lines (but preserve intentional indentation)
        lines = text.split('\n')
        fixed_lines = []
        for line in lines:
            # Don't strip YAML frontmatter or markdown headers
            if line.startswith('---') or line.startswith('#') or line.startswith('title:') or line.startswith('author:') or line.startswith('date:') or line.startswith('location:') or line.startswith('source:') or line.startswith('letter_number:') or line.startswith('recipient:') or line.startswith('**'):
                fixed_lines.append(line)
            else:
                # Strip leading/trailing whitespace from content lines
                fixed_lines.append(line.strip())

        text = '\n'.join(fixed_lines)

        # Remove excessive blank lines (more than 2 in a row)
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        if text != original:
            self.changes_log.append("Fixed spacing and punctuation")

        return text

    def fix_ocr_errors(self, text):
        """Fix remaining OCR errors"""

        original = text

        for error, fix in self.ocr_fixes.items():
            if error in text:
                text = text.replace(error, fix)
                self.changes_log.append(f"Fixed OCR error: '{error}' → '{fix}'")

        return text

    def fix_letter(self, letter_file):
        """Apply all fixes to a single letter"""

        self.changes_log = []  # Reset for this letter

        with open(letter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply fixes in order
        content = self.fix_hyphenation(content)
        content = self.fix_ocr_errors(content)
        content = self.fix_spacing(content)

        # Only write if changed
        if content != original_content:
            with open(letter_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, self.changes_log
        else:
            return False, []

    def fix_all_letters(self):
        """Fix all letters"""

        print("=" * 80)
        print("MANUAL LETTER FIXES")
        print("=" * 80)
        print()

        letter_files = sorted(self.letters_dir.glob('letter_*.md'))

        total_changed = 0
        all_changes = {}

        for i, letter_file in enumerate(letter_files, 1):
            changed, changes = self.fix_letter(letter_file)

            if changed:
                total_changed += 1
                all_changes[letter_file.name] = changes
                print(f"✓ Fixed {letter_file.name}")
                for change in changes[:3]:  # Show first 3 changes
                    print(f"    - {change}")
                if len(changes) > 3:
                    print(f"    ... and {len(changes) - 3} more")

            if (i % 10 == 0):
                print(f"  Processed {i}/{len(letter_files)}...")

        print()
        print("=" * 80)
        print(f"COMPLETE: Fixed {total_changed} letters")
        print("=" * 80)

        return all_changes


if __name__ == '__main__':
    fixer = LetterFixer()
    changes = fixer.fix_all_letters()

    if changes:
        print(f"\nTotal letters modified: {len(changes)}")
    else:
        print("\n✓ No fixes needed - all letters are clean!")
