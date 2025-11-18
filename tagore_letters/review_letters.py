#!/usr/bin/env python3
"""
Systematic letter review - find presentation and formatting issues
"""

import re
from pathlib import Path
from collections import defaultdict

class LetterReviewer:
    """Systematic review of all letters for quality issues"""

    def __init__(self):
        self.letters_dir = Path('extracted_letters_thorough')
        self.issues = defaultdict(list)

        # Common OCR errors that might have slipped through
        self.additional_fixes = {
            # Common OCR errors
            'tlie': 'the',
            'tbe': 'the',
            'tiie': 'the',
            'tne': 'the',
            'tliat': 'that',
            'wliich': 'which',
            'witli': 'with',
            'wlien': 'when',
            'wlio': 'who',
            'wliat': 'what',
            'whicli': 'which',
            'eveiy': 'every',
            'veiy': 'very',
            'theie': 'there',
            'wheie': 'where',
            'theil': 'their',
            'youi': 'your',
            'oui': 'our',
            'foi': 'for',
            'fiom': 'from',
            'foj': 'for',
            'aie': 'are',
            'anv': 'any',
            'onlv': 'only',
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
            'cairiage': 'carriage',

            # Spacing issues
            ' .': '.',
            ' ,': ',',
            ' ;': ';',
            ' :': ':',
            '  ': ' ',  # double spaces

            # Quote issues
            "' ": "'",
            " '": "'",
            '" ': '"',
            ' "': '"',
        }

        # Patterns that indicate problems
        self.problem_patterns = [
            (r'\b[a-z]{1,3}[^\w\s][a-z]{1,3}\b', 'Strange character in word'),
            (r'\d+[a-z]{2,3}[,\s]', 'Malformed date'),
            (r'[A-Z]{2,}[a-z]', 'Broken capitalization'),
            (r'\b[il1][a-z]{2,}', 'Likely OCR i/l/1 error'),
            (r'\w+[-—]\s*\n\s*\w+', 'Hyphenated word across lines'),
            (r'\s{3,}', 'Excessive spacing'),
            (r'^\s*\d+\s*$', 'Orphaned page number'),
            (r'[^\s]{60,}', 'Very long word (likely error)'),
        ]

    def check_letter(self, letter_file):
        """Check a single letter for issues"""

        with open(letter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        letter_num = int(re.search(r'letter_(\d+)', letter_file.name).group(1))
        issues = []

        # Check frontmatter
        if content.count('---') < 2:
            issues.append('Missing or incomplete frontmatter')

        # Extract content after frontmatter
        parts = content.split('---')
        if len(parts) >= 3:
            letter_content = '---'.join(parts[2:])
        else:
            letter_content = content

        # Check for problem patterns
        for pattern, description in self.problem_patterns:
            matches = re.finditer(pattern, letter_content, re.MULTILINE)
            for match in matches:
                issues.append(f"{description}: '{match.group()}'")

        # Check for unresolved OCR errors
        for error in self.additional_fixes.keys():
            if error in letter_content:
                issues.append(f"Unresolved OCR error: '{error}'")

        # Check letter length
        clean_content = re.sub(r'\s+', ' ', letter_content).strip()
        if len(clean_content) < 100:
            issues.append(f"Very short letter ({len(clean_content)} chars)")

        # Check for broken formatting
        lines = letter_content.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 200:
                issues.append(f"Very long line {i}: {len(line)} chars")

        return issues

    def review_all_letters(self):
        """Review all letters and collect issues"""

        print("=" * 80)
        print("SYSTEMATIC LETTER REVIEW")
        print("=" * 80)
        print()

        letter_files = sorted(self.letters_dir.glob('letter_*.md'))

        all_issues = {}

        for letter_file in letter_files:
            issues = self.check_letter(letter_file)
            if issues:
                all_issues[letter_file.name] = issues

        # Report findings
        print(f"Reviewed {len(letter_files)} letters\n")

        if all_issues:
            print(f"Found issues in {len(all_issues)} letters:\n")

            for filename, issues in sorted(all_issues.items())[:20]:  # Show first 20
                print(f"\n{filename}:")
                for issue in issues:
                    print(f"  ⚠ {issue}")
        else:
            print("✓ No obvious issues found!")

        return all_issues

    def generate_review_report(self, all_issues):
        """Generate detailed review report"""

        issue_types = defaultdict(int)

        for filename, issues in all_issues.items():
            for issue in issues:
                issue_type = issue.split(':')[0]
                issue_types[issue_type] += 1

        print("\n" + "=" * 80)
        print("ISSUE SUMMARY")
        print("=" * 80)
        print()

        for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            print(f"  {issue_type}: {count}")

        print(f"\nTotal letters with issues: {len(all_issues)}/65")

        return issue_types


if __name__ == '__main__':
    reviewer = LetterReviewer()
    issues = reviewer.review_all_letters()
    reviewer.generate_review_report(issues)
