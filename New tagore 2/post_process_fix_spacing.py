#!/usr/bin/env python3
"""
Post-processing to fix concatenated words using dictionary lookups
Addresses issues like "insome" -> "in some", "writeyoua" -> "write you a"
"""

import re
from typing import List, Tuple


class WordSpacingFixer:
    """Fix concatenated words using heuristics and dictionary lookups"""

    def __init__(self):
        # Common English words for quick lookup
        # In production, use a full dictionary file
        self.common_words = set([
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
            'can', 'shall', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us',
            'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these',
            'those', 'which', 'who', 'whom', 'whose', 'what', 'when', 'where', 'why', 'how',
            'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 'then', 'here',
            'there', 'up', 'down', 'out', 'over', 'under', 'again', 'once', 'any', 'every',
            'write', 'writing', 'letter', 'letters', 'wish', 'wished', 'wishing', 'am', 'give',
            'gave', 'given', 'go', 'going', 'went', 'gone', 'see', 'seeing', 'saw', 'seen',
            'get', 'getting', 'got', 'gotten', 'make', 'making', 'made', 'think', 'thinking',
            'thought', 'take', 'taking', 'took', 'taken', 'come', 'coming', 'came', 'know',
            'knowing', 'knew', 'known', 'find', 'finding', 'found', 'feel', 'feeling', 'felt',
            'tell', 'telling', 'told', 'ask', 'asking', 'asked', 'work', 'working', 'worked',
            'seem', 'seeming', 'seemed', 'try', 'trying', 'tried', 'leave', 'leaving', 'left',
            'call', 'calling', 'called', 'put', 'putting', 'keep', 'keeping', 'kept', 'let',
            'letting', 'begin', 'beginning', 'began', 'begun', 'show', 'showing', 'showed',
            'shown', 'hear', 'hearing', 'heard', 'play', 'playing', 'played', 'run', 'running',
            'ran', 'move', 'moving', 'moved', 'live', 'living', 'lived', 'believe', 'believing',
            'believed', 'bring', 'bringing', 'brought', 'happen', 'happening', 'happened',
            'place', 'chair', 'deck', 'wish', 'could', 'great', 'sea', 'sky', 'trunk', 'label',
            'required', 'plans', 'feeling', 'guess', 'time', 'heat', 'mind', 'back', 'own',
            'almost', 'certain', 'stay', 'voyage', 'journey', 'happy', 'reach', 'week', 'mistake',
            'lessons', 'shall', 'evening', 'already', 'beginning', 'grow', 'cold', 'world',
            'hearts', 'region', 'atmosphere', 'looks', 'people', 'want', 'fight', 'battles',
            'supply', 'materials', 'standing', 'outside', 'doors', 'notice', 'board', 'asia',
            'prosecuted', 'thoughts', 'shiver', 'corner', 'today', 'monday', 'next', 'sunday',
            'morning', 'steamer', 'counting', 'days', 'return', 'sight', 'bare', 'rocks',
            'thrill', 'delight', 'heart', 'pointing', 'lifted', 'fingers', 'way', 'india',
            'london', 'june', 'scarce', 'sugar', 'butter', 'quiet', 'gather', 'recognise',
            'myself', 'expect', 'anything', 'else', 'fury', 'social', 'engagements', 'thing',
            'cannot', 'compose', 'ode', 'west', 'wind', 'allow', 'poet', 'exchange', 'wealth',
            'mole', 'cheek', 'beloved', 'maiden', 'away', 'mine', 'dispose', 'neither', 'persian',
            'extravagance', 'cost', 'help', 'oxford', 'tomorrow', 'knocking', 'different',
            'places', 'moment', 'starting', 'tea', 'party', 'honour', 'absent', 'pretext',
            'unless', 'manage', 'motor', 'car', 'street', 'matter', 'eternal', 'wonder',
            'happen', 'four', 'times', 'scarcity', 'note', 'paper', 'hastily', 'bid', 'farewell',
            'july', 'every', 'day', 'flesh', 'weak', 'become', 'solid', 'cannon', 'balls',
            'heavy', 'true', 'leisure', 'unfortunately', 'utilise', 'interrupted', 'whatever',
            'therefore', 'intervals', 'lost', 'nothing', 'sure', 'better', 'anybody', 'burden',
            'hard', 'bear', 'look', 'exterior', 'trace', 'damage', 'health', 'absurdly', 'good',
            'hope', 'regularly', 'furnishing', 'news', 'very', 'imagine', 'arduous',
            'responsibility', 'looking', 'after', 'suits', 'wonderfully', 'well', 'picture',
            'whole', 'dreams', 'felicitous', 'instance', 'last', 'night', 'dreamt', 'buying',
            'strawberries', 'large', 'gourds', 'proves', 'magnificent', 'vitality', 'vacation',
            'over', 'boys', 'school', 'resounding', 'laughter', 'songs', 'advent', 'rains',
            'contributing', 'portion', 'rejoicing', 'wings', 'love', 'children', 'blessings'
        ])

    def split_concatenated_word(self, word: str) -> str:
        """Attempt to split a concatenated word"""
        if len(word) < 5:  # Don't split short words
            return word

        # Try splitting at each position
        best_split = word
        best_score = 0

        for i in range(2, len(word) - 1):
            left = word[:i].lower()
            right = word[i:].lower()

            # Score based on dictionary matches
            score = 0
            if left in self.common_words:
                score += 2
            if right in self.common_words:
                score += 2

            # Bonus for common patterns
            if left in ['i', 'to', 'in', 'on', 'at', 'by', 'for', 'the', 'a', 'an']:
                score += 1

            if score > best_score:
                best_score = score
                # Preserve original capitalization
                if word[0].isupper():
                    best_split = word[:i].capitalize() + ' ' + word[i:]
                else:
                    best_split = word[:i] + ' ' + word[i:]

        # Only split if we found a good match
        if best_score >= 3:
            return best_split

        return word

    def fix_text(self, text: str) -> Tuple[str, int]:
        """Fix concatenated words in text"""
        fixes_made = 0
        words = text.split()
        fixed_words = []

        for word in words:
            # Clean punctuation for analysis
            cleaned = re.sub(r'[^\w]', '', word)

            if len(cleaned) > 6:  # Only check longer words
                # Check if word is likely concatenated
                # Heuristic: Contains multiple common word parts

                fixed = self.split_concatenated_word(cleaned)

                if fixed != cleaned:
                    # Preserve original punctuation
                    original_punct = word[len(cleaned):]
                    fixed_words.append(fixed + original_punct)
                    fixes_made += 1
                else:
                    fixed_words.append(word)
            else:
                fixed_words.append(word)

        return ' '.join(fixed_words), fixes_made

    def apply_manual_fixes(self, text: str) -> Tuple[str, List[str]]:
        """Apply known manual fixes for common OCR errors"""
        changes = []

        # Common concatenation patterns
        patterns = [
            (r'\binsome\b', 'in some'),
            (r'\bwriteyou\b', 'write you'),
            (r'\bwriteyoua\b', 'write you a'),
            (r'\bwishI\b', 'wish I'),
            (r'\bIam\b', 'I am'),
            (r'\binthe\b', 'in the'),
            (r'\btothe\b', 'to the'),
            (r'\bofthe\b', 'of the'),
            (r'\bonthe\b', 'on the'),
            (r'\batthe\b', 'at the'),
            (r'\bforthe\b', 'for the'),
            (r'\bwiththe\b', 'with the'),
            (r'\bifthey\b', 'if they'),
            (r'\bthatI\b', 'that I'),
            (r'\bthatwe\b', 'that we'),
            (r'\bcanbe\b', 'can be'),
            (r'\bwillbe\b', 'will be'),
            (r'\bhasbeen\b', 'has been'),
            (r'\bhavebeen\b', 'have been'),
            (r'\bdoesnot\b', 'does not'),
            (r'\bdonot\b', 'do not'),
            (r'\bcannot\b', 'cannot'),  # This one is actually correct as one word
            (r'\bofus\b', 'of us'),
            (r'\btous\b', 'to us'),
            (r'\bforus\b', 'for us'),
        ]

        for pattern, replacement in patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                changes.append(f"Fixed {matches} instances of '{pattern}' -> '{replacement}'")
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Fix common OCR character confusions
        ocr_fixes = [
            (r'\brn\b', 'm'),  # 'rn' often mistaken for 'm'
            (r'\bcl\b', 'd'),  # 'cl' often mistaken for 'd'
        ]

        for pattern, replacement in ocr_fixes:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text, changes


def fix_markdown_file(input_path: str, output_path: str = None):
    """Fix spacing issues in a markdown file"""
    if output_path is None:
        output_path = input_path.replace('.md', '_fixed.md')

    fixer = WordSpacingFixer()

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into frontmatter and body
    parts = content.split('---\n')
    if len(parts) >= 3:
        frontmatter = parts[1]
        body = '---\n'.join(parts[2:])

        # Fix body text
        fixed_body, auto_fixes = fixer.fix_text(body)
        fixed_body, manual_changes = fixer.apply_manual_fixes(fixed_body)

        # Reconstruct
        fixed_content = f"---\n{frontmatter}---\n{fixed_body}"

        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print(f"✓ Fixed {input_path}")
        print(f"  Auto fixes: {auto_fixes}")
        print(f"  Manual fixes: {len(manual_changes)}")
        for change in manual_changes[:5]:  # Show first 5
            print(f"    - {change}")

    else:
        print(f"✗ Could not parse {input_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        fix_markdown_file(sys.argv[1])
    else:
        print("Usage: python3 post_process_fix_spacing.py <markdown_file>")
