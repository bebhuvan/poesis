#!/usr/bin/env python3
"""
Advanced quality analysis to identify remaining issues
Goal: 99%+ accuracy
"""

import re
from collections import Counter, defaultdict
from pathlib import Path
import json


class QualityAnalyzer:
    def __init__(self, text_file):
        with open(text_file, 'r', encoding='utf-8') as f:
            self.text = f.read()
        self.lines = self.text.split('\n')

    def find_suspicious_patterns(self):
        """Find patterns that often indicate OCR errors"""
        issues = defaultdict(list)

        # Pattern: Mixed case in middle of words
        mixed_case = re.finditer(r'\b[a-z]+[A-Z][a-z]+\b', self.text)
        for match in mixed_case:
            issues['mixed_case'].append({
                'text': match.group(),
                'context': self.get_context(match.start())
            })

        # Pattern: Standalone single letters that might be errors
        standalone = re.finditer(r'\b[a-z]\b(?! )', self.text)
        for match in standalone:
            char = match.group()
            if char not in ['a', 'I']:  # Valid standalone letters
                issues['standalone_letters'].append({
                    'text': char,
                    'context': self.get_context(match.start())
                })

        # Pattern: Double punctuation (except valid cases)
        double_punct = re.finditer(r'[,;:]{2,}|[.]{4,}', self.text)
        for match in double_punct:
            issues['double_punctuation'].append({
                'text': match.group(),
                'context': self.get_context(match.start())
            })

        # Pattern: Space before punctuation (except dashes)
        space_before = re.finditer(r'\s+[,;:.](?!\.)(?!-)', self.text)
        for match in space_before:
            issues['space_before_punct'].append({
                'text': match.group(),
                'context': self.get_context(match.start())
            })

        # Pattern: Common OCR confusions still present
        ocr_suspects = [
            (r'\bwas\s+bom\b', 'bom → born?'),
            (r'\bwas\s+a\s+bom\b', 'bom → born?'),
            (r'\btbe\b', 'tbe → the?'),
            (r'\btlie\b', 'tlie → the?'),
            (r'\bwitb\b', 'witb → with?'),
            (r'\byoung\s+man\s+nam\b', 'nam → named?'),
            (r'\bfrom\s+tbe\b', 'tbe → the?'),
            (r'\bI\s+bad\b', 'bad → had?'),
            (r'\bwbich\b', 'wbich → which?'),
            (r'\bwben\b', 'wben → when?'),
            (r'\btbis\b', 'tbis → this?'),
            (r'\btbat\b', 'tbat → that?'),
            (r'\btbey\b', 'tbey → they?'),
            (r'\btbere\b', 'tbere → there?'),
            (r'\btbe\s+first\b', 'tbe → the?'),
            (r'\bin\s+tbe\b', 'tbe → the?'),
        ]

        for pattern, suggestion in ocr_suspects:
            matches = re.finditer(pattern, self.text, re.IGNORECASE)
            for match in matches:
                issues['ocr_suspects'].append({
                    'text': match.group(),
                    'suggestion': suggestion,
                    'context': self.get_context(match.start())
                })

        # Pattern: Numbers that might be misread letters
        num_letters = re.finditer(r'\b[A-Za-z]+[0-9][A-Za-z]+\b', self.text)
        for match in num_letters:
            issues['numbers_in_words'].append({
                'text': match.group(),
                'context': self.get_context(match.start())
            })

        # Pattern: All caps words in middle of sentences (might be OCR errors)
        all_caps = re.finditer(r'(?<=[a-z]\s)[A-Z]{2,}(?=\s[a-z])', self.text)
        for match in all_caps:
            word = match.group()
            # Skip known acronyms
            if word not in ['AND', 'OR', 'THE', 'OF', 'TO', 'IN', 'A']:
                issues['unexpected_caps'].append({
                    'text': word,
                    'context': self.get_context(match.start())
                })

        return issues

    def check_spelling(self):
        """Check for potential spelling errors"""
        # Common misspellings in OCR
        misspellings = {
            'recieved': 'received',
            'beleive': 'believe',
            'acheive': 'achieve',
            'occured': 'occurred',
            'untill': 'until',
            'witb': 'with',
            'tbe': 'the',
            'wbich': 'which',
            'wben': 'when',
            'tbis': 'this',
            'tbat': 'that',
            'tbey': 'they',
            'tbere': 'there',
            'bave': 'have',
            'tlie': 'the',
            'whicli': 'which',
        }

        found = {}
        for wrong, correct in misspellings.items():
            matches = list(re.finditer(r'\b' + wrong + r'\b', self.text, re.IGNORECASE))
            if matches:
                found[wrong] = {
                    'correct': correct,
                    'count': len(matches),
                    'examples': [self.get_context(m.start()) for m in matches[:3]]
                }

        return found

    def check_proper_names(self):
        """Check consistency of proper names"""
        # Known names that should be consistent
        names = {
            'Toru': ['Toru'],
            'Dutt': ['Dutt'],
            'Martin': ['Martin'],
            'Aru': ['Aru'],
            'Mary': ['Mary'],
            'Calcutta': ['Calcutta'],
            'Govin': ['Govin', 'Govind'],
        }

        variations = defaultdict(list)

        for name, valid_forms in names.items():
            # Find similar words (case-insensitive, within edit distance)
            pattern = r'\b' + name[0] + r'[a-z]*\b'
            matches = re.finditer(pattern, self.text, re.IGNORECASE)

            for match in matches:
                word = match.group()
                if word not in valid_forms and word.lower() != name.lower():
                    variations[name].append({
                        'found': word,
                        'context': self.get_context(match.start())
                    })

        return variations

    def check_punctuation_consistency(self):
        """Check for inconsistent punctuation patterns"""
        issues = defaultdict(list)

        # Check quote marks
        single_quotes = self.text.count("'")
        double_quotes = self.text.count('"')
        open_quotes = self.text.count('"')
        close_quotes = self.text.count('"')

        # Check if quotes are balanced
        if double_quotes % 2 != 0:
            issues['unbalanced_quotes'].append(f'Unbalanced double quotes: {double_quotes} found')

        # Check for inconsistent dash usage
        dashes = {
            'hyphen': self.text.count('-'),
            'en_dash': self.text.count('–'),
            'em_dash': self.text.count('—'),
            'double_hyphen': self.text.count('--'),
        }
        issues['dash_usage'] = dashes

        # Check for multiple spaces
        multi_space = re.finditer(r'  +', self.text)
        multi_space_count = len(list(multi_space))
        if multi_space_count > 0:
            issues['multiple_spaces'].append(f'Found {multi_space_count} instances of multiple spaces')

        return issues

    def find_word_fragments(self):
        """Find potential word fragments from line breaks"""
        # Words that end with common syllables might be fragments
        fragments = []

        lines = self.text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if line ends with a partial word (no punctuation, lowercase end)
            if line and line[-1].islower() and not line.endswith((',', '.', ';', ':', '!', '?')):
                # Check if next line starts with lowercase
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and next_line[0].islower():
                        fragments.append({
                            'line_num': i,
                            'end': line[-20:],
                            'start': next_line[:20]
                        })

        return fragments

    def get_context(self, pos, window=60):
        """Get context around a position"""
        start = max(0, pos - window)
        end = min(len(self.text), pos + window)
        return self.text[start:end].replace('\n', ' ')

    def generate_report(self):
        """Generate comprehensive quality report"""
        print("=" * 70)
        print("ADVANCED QUALITY ANALYSIS REPORT")
        print("Goal: Identify path to 99%+ accuracy")
        print("=" * 70)

        # 1. Suspicious patterns
        print("\n1. SUSPICIOUS PATTERNS")
        print("-" * 70)
        suspicious = self.find_suspicious_patterns()

        total_suspicious = sum(len(v) for v in suspicious.values())
        print(f"Total suspicious patterns found: {total_suspicious}")

        for category, items in suspicious.items():
            if items:
                print(f"\n  {category.replace('_', ' ').title()}: {len(items)} found")
                for item in items[:3]:  # Show first 3
                    if 'suggestion' in item:
                        print(f"    • {item['text']} ({item['suggestion']})")
                    else:
                        print(f"    • {item['text']}")
                    print(f"      Context: ...{item['context']}...")
                if len(items) > 3:
                    print(f"    ... and {len(items) - 3} more")

        # 2. Spelling check
        print("\n\n2. POTENTIAL SPELLING ERRORS")
        print("-" * 70)
        spelling = self.check_spelling()

        if spelling:
            print(f"Found {len(spelling)} potential misspellings:")
            for wrong, info in spelling.items():
                print(f"\n  '{wrong}' → '{info['correct']}' ({info['count']} occurrences)")
                for example in info['examples']:
                    print(f"    ...{example}...")
        else:
            print("✓ No common misspellings found")

        # 3. Proper names
        print("\n\n3. PROPER NAME CONSISTENCY")
        print("-" * 70)
        names = self.check_proper_names()

        if any(names.values()):
            print("Potential name variations found:")
            for name, variations in names.items():
                if variations:
                    print(f"\n  '{name}' variations: {len(variations)}")
                    for var in variations[:3]:
                        print(f"    • {var['found']}")
                        print(f"      ...{var['context']}...")
        else:
            print("✓ No obvious name inconsistencies found")

        # 4. Punctuation
        print("\n\n4. PUNCTUATION CONSISTENCY")
        print("-" * 70)
        punct = self.check_punctuation_consistency()

        for category, issues in punct.items():
            if category == 'dash_usage':
                print(f"\n  Dash usage:")
                for dash_type, count in issues.items():
                    print(f"    {dash_type}: {count}")
            else:
                print(f"\n  {category.replace('_', ' ').title()}:")
                for issue in issues:
                    print(f"    {issue}")

        # 5. Word fragments
        print("\n\n5. POTENTIAL WORD FRAGMENTS")
        print("-" * 70)
        fragments = self.find_word_fragments()

        if fragments:
            print(f"Found {len(fragments)} potential word fragments:")
            for frag in fragments[:5]:
                print(f"\n  Line {frag['line_num']}:")
                print(f"    Ends: ...{frag['end']}")
                print(f"    Continues: {frag['start']}...")
            if len(fragments) > 5:
                print(f"\n  ... and {len(fragments) - 5} more")
        else:
            print("✓ No obvious word fragments found")

        # Summary
        print("\n\n" + "=" * 70)
        print("SUMMARY - ESTIMATED QUALITY LEVEL")
        print("=" * 70)

        total_issues = (
            total_suspicious +
            len(spelling) +
            sum(len(v) for v in names.values()) +
            len(fragments)
        )

        # Rough estimate based on text length
        word_count = len(self.text.split())
        error_rate = (total_issues / word_count) * 100 if word_count > 0 else 0
        estimated_quality = max(0, 100 - error_rate)

        print(f"\nTotal suspicious items: {total_issues}")
        print(f"Total words: ~{word_count:,}")
        print(f"Error rate: ~{error_rate:.3f}%")
        print(f"Estimated quality: ~{estimated_quality:.1f}%")

        if estimated_quality >= 99:
            print("\n✓ QUALITY LEVEL: EXCELLENT (99%+)")
            print("  Minor manual review recommended for perfection")
        elif estimated_quality >= 95:
            print("\n⚠ QUALITY LEVEL: VERY GOOD (95-99%)")
            print("  Automated fixes + spot checking recommended")
        elif estimated_quality >= 90:
            print("\n⚠ QUALITY LEVEL: GOOD (90-95%)")
            print("  Additional processing needed")
        else:
            print("\n✗ QUALITY LEVEL: NEEDS IMPROVEMENT (<90%)")
            print("  Significant additional work required")

        return {
            'suspicious_patterns': suspicious,
            'spelling_errors': spelling,
            'name_variations': names,
            'punctuation_issues': punct,
            'word_fragments': fragments,
            'total_issues': total_issues,
            'estimated_quality': estimated_quality
        }


def main():
    analyzer = QualityAnalyzer('/home/user/poesis/toru_dutt_output/toru_dutt_perfect.md')
    report = analyzer.generate_report()

    # Save detailed report
    output_dir = Path('/home/user/poesis/toru_dutt_output')
    with open(output_dir / 'quality_analysis.json', 'w', encoding='utf-8') as f:
        # Convert to JSON-serializable format
        json_report = {
            'total_issues': report['total_issues'],
            'estimated_quality': report['estimated_quality'],
            'suspicious_count': sum(len(v) for v in report['suspicious_patterns'].values()),
            'spelling_errors': len(report['spelling_errors']),
            'punctuation_issues': len(report['punctuation_issues']),
            'word_fragments': len(report['word_fragments']),
        }
        json.dump(json_report, f, indent=2)

    print(f"\n\nDetailed analysis saved to: quality_analysis.json")


if __name__ == '__main__':
    main()
