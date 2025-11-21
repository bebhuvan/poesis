#!/usr/bin/env python3
"""
Fix common OCR errors in Dostoevsky letter markdown files.
"""

import re
import sys
import argparse
from pathlib import Path

class OCRFixer:
    def __init__(self):
        # Common OCR character substitutions
        self.char_fixes = {
            # These should only be applied in word contexts
            'rn': 'm',   # "rn" often misread as "m"
            'cl': 'd',   # "cl" often misread as "d"
            'vv': 'w',   # "vv" often misread as "w"
        }

    def fix_double_spaces(self, text):
        """Replace multiple spaces with single space"""
        # Fix 2+ spaces
        text = re.sub(r' {2,}', ' ', text)
        return text

    def fix_common_chars(self, text):
        """Fix common OCR character errors"""
        # These fixes are context-sensitive

        # Fix "rn" -> "m" in middle of words
        text = re.sub(r'\brn', 'm', text)  # Start of word
        text = re.sub(r'rn\b', 'm', text)  # End of word

        # Fix common punctuation
        text = text.replace('„', '"')
        text = text.replace('"', '"')
        text = text.replace('"', '"')

        return text

    def join_broken_lines(self, text):
        """Join lines that were incorrectly broken"""
        # This is tricky - we want to join lines that are part of same paragraph
        # but not join actual paragraph breaks

        # Split into lines
        lines = text.split('\n')

        result = []
        buffer = ''

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Empty line - paragraph break
            if not stripped:
                if buffer:
                    result.append(buffer)
                    buffer = ''
                result.append('')
                continue

            # Markdown special lines (headers, frontmatter, etc)
            if stripped.startswith('#') or stripped.startswith('**[') or \
               stripped.startswith('---') or stripped.endswith(':'):
                if buffer:
                    result.append(buffer)
                    buffer = ''
                result.append(line)
                continue

            # Regular text line
            if buffer:
                # Add space if previous line didn't end with space or hyphen
                if not buffer.endswith(' ') and not buffer.endswith('-'):
                    buffer += ' '
                buffer += stripped
            else:
                buffer = stripped

        if buffer:
            result.append(buffer)

        return '\n'.join(result)

    def fix_file(self, filepath, fix_spaces=True, fix_chars=True, join_lines=False):
        """Fix OCR errors in a file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Apply fixes
        if fix_spaces:
            content = self.fix_double_spaces(content)

        if fix_chars:
            content = self.fix_common_chars(content)

        if join_lines:
            content = self.join_broken_lines(content)

        return original, content

def main():
    parser = argparse.ArgumentParser(description='Fix OCR errors in letter markdown files')
    parser.add_argument('files', nargs='+', help='Markdown files to fix')
    parser.add_argument('--fix-spaces', action='store_true', help='Fix double spaces')
    parser.add_argument('--fix-common', action='store_true', help='Fix common OCR character errors')
    parser.add_argument('--join-lines', action='store_true', help='Join broken lines (experimental)')
    parser.add_argument('--fix-all', action='store_true', help='Apply all fixes')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
    parser.add_argument('--backup', action='store_true', help='Create .bak backup files')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup (use with caution!)')

    args = parser.parse_args()

    # Default to fix-all if no specific fixes selected
    if not (args.fix_spaces or args.fix_common or args.join_lines):
        args.fix_all = True

    if args.fix_all:
        args.fix_spaces = True
        args.fix_common = True
        # Don't auto-enable join_lines as it's experimental

    fixer = OCRFixer()

    total_files = 0
    changed_files = 0

    for pattern in args.files:
        # Expand glob patterns
        files = Path('.').glob(pattern) if '*' in pattern else [Path(pattern)]

        for filepath in files:
            if not filepath.is_file():
                continue

            total_files += 1

            original, fixed = fixer.fix_file(
                filepath,
                fix_spaces=args.fix_spaces,
                fix_chars=args.fix_common,
                join_lines=args.join_lines
            )

            if original != fixed:
                changed_files += 1

                if args.dry_run:
                    print(f"\n{'='*60}")
                    print(f"Would change: {filepath}")
                    print(f"{'='*60}")

                    # Show first few differences
                    orig_lines = original.split('\n')
                    fixed_lines = fixed.split('\n')

                    for i, (o, f) in enumerate(zip(orig_lines[:10], fixed_lines[:10])):
                        if o != f:
                            print(f"Line {i+1}:")
                            print(f"  OLD: {o[:80]}")
                            print(f"  NEW: {f[:80]}")

                else:
                    # Create backup if requested
                    if args.backup and not args.no_backup:
                        backup_path = str(filepath) + '.bak'
                        Path(backup_path).write_text(original, encoding='utf-8')

                    # Write fixed version
                    filepath.write_text(fixed, encoding='utf-8')
                    print(f"✓ Fixed: {filepath}")

    print(f"\n{'='*60}")
    print(f"Processed {total_files} files")
    print(f"Changed {changed_files} files")

    if args.dry_run:
        print("(DRY RUN - no changes were saved)")

    print(f"{'='*60}")

if __name__ == '__main__':
    main()
