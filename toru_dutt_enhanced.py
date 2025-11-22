#!/usr/bin/env python3
"""
Enhanced text processor with better OCR correction and chapter title extraction
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple


class EnhancedProcessor:
    def __init__(self, input_file: str):
        with open(input_file, 'r', encoding='utf-8') as f:
            self.raw_text = f.read()
        self.lines = self.raw_text.split('\n')

    def advanced_ocr_cleanup(self, text: str) -> str:
        """Advanced OCR error correction"""
        # First pass: character-level fixes
        replacements = [
            (r'Tennysoi[\^\.]+', 'Tennyson.'),
            (r'nothii\^?g', 'nothing'),
            (r'Torn\b', 'Toru'),
            (r'INDIAJ\^?', 'INDIAN'),
            (r'\bOP\b', 'OF'),
            (r'SUPPLEMENTAEY', 'SUPPLEMENTARY'),
            (r'herlove', 'her love'),
            (r"field'of", 'field of'),
            (r'\bho\b', 'he'),
            (r'\bwe\b(?! )', 'we '),
            # Remove stray characters
            (r'\^', ''),
            (r'¬\s*', ''),
            # Fix common word errors
            (r'EAELY', 'EARLY'),
            (r'EUEOPE', 'EUROPE'),
            (r'PEEPAEATION', 'PREPARATION'),
            (r'CAEEEE', 'CAREER'),
            (r'LETTEES', 'LETTERS'),
            (r'TOEU', 'TORU'),
            (r'FOEEWORD', 'FOREWORD'),
            (r'POREWOED', 'FOREWORD'),
            (r'\bwo\b', 'we'),
            (r'imited\b', 'united'),
            (r'attrac-?\s*tion', 'attraction'),
            (r'con-?\s*tained', 'contained'),
            (r'Ban+erjea', 'Banerjea'),
            (r'Dkcember', 'December'),
            (r'Dkcbmber', 'December'),
            (r'Refrence', 'Reference'),
            (r'6toit', 'était'),
            (r'6cu', 'écu'),
            (r'oik', 'où'),
            # Fix French accents
            (r'v6cu', 'vécu'),
            # Page numbering artifacts
            (r'\bviii\s+FOREWORD', 'FOREWORD'),
            (r'\d+\s+LIFE AND LETTERS', 'LIFE AND LETTERS'),
            # Normalize spaces
            (r' {2,}', ' '),
            (r'\t+', ' '),
        ]

        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE if pattern.isupper() else 0)

        return text

    def extract_chapter_title(self, start_line: int, max_lines: int = 10) -> str:
        """Extract chapter title that may span multiple lines"""
        title_lines = []

        for i in range(start_line + 1, min(start_line + max_lines, len(self.lines))):
            line = self.lines[i].strip()

            # Skip empty lines
            if not line:
                if title_lines:  # If we already have title content, stop
                    break
                continue

            # Stop at chapter content (lowercase text or long paragraphs)
            if line and not line.isupper() and len(line) > 50:
                break

            # Stop at dates
            if re.match(r'[A-Z][a-z]+ \d{4}', line):
                break

            # Add to title if it looks like a title (short, uppercase, or title case)
            if line.isupper() or (len(line) < 80 and line[0].isupper()):
                title_lines.append(line)
            else:
                break

        return ' '.join(title_lines)

    def get_chapter_info(self) -> List[Dict]:
        """Extract detailed chapter information"""
        chapters = []
        chapter_pattern = r'^CHAPTER\s+([IVXLCDM]+)\s*$'

        for i, line in enumerate(self.lines):
            match = re.match(chapter_pattern, line.strip())
            if match:
                chapter_num = match.group(1)
                title = self.extract_chapter_title(i)

                chapters.append({
                    'number': chapter_num,
                    'title': title,
                    'line_number': i
                })

        return chapters

    def create_clean_markdown(self, output_path: str):
        """Create a clean, well-formatted Markdown file"""
        # Apply OCR cleanup
        cleaned_text = self.advanced_ocr_cleanup(self.raw_text)
        lines = cleaned_text.split('\n')

        # Get chapter info
        chapters = self.get_chapter_info()

        # Create output
        md_lines = []

        # Title page
        md_lines.extend([
            '# Life and Letters of Toru Dutt',
            '',
            '**By Harihar Das**',
            '',
            '*With a Foreword by The Right Hon. H. A. L. Fisher, M.P.*',
            '',
            '**Oxford University Press, 1921**',
            '',
            '---',
            '',
        ])

        # Process content
        in_title_section = True
        skip_line_count = 0

        for i, line in enumerate(lines):
            # Skip library stamps at start and end
            if i < 30 or i > len(lines) - 100:
                if re.search(r'Lai Bahadur|MUSSOORIE|LIBRARY|Accession|Class No|Book No', line, re.IGNORECASE):
                    continue

            if skip_line_count > 0:
                skip_line_count -= 1
                continue

            stripped = line.strip()

            # Skip title pages after our custom title
            if in_title_section and i < 200:
                if re.search(r'PRINTED IN ENGLAND|HUMPHREY MILFORD|1921|BOMBAY CALCUTTA', stripped):
                    continue
                if stripped == 'LIFE AND LETTERS OF' or stripped == 'TORU DUTT' or stripped == 'BY' or stripped == 'HARIHAR DAS':
                    continue

            # Detect major sections
            if re.match(r'^(FOREWORD|CONTENTS|PREFACE)$', stripped, re.IGNORECASE):
                in_title_section = False
                md_lines.extend(['', '', f'## {stripped.title()}', '', ''])
                continue

            # Detect chapters
            chapter_match = re.match(r'^CHAPTER\s+([IVXLCDM]+)\s*$', stripped)
            if chapter_match:
                in_title_section = False
                ch_num = chapter_match.group(1)

                # Find chapter info
                ch_info = next((ch for ch in chapters if ch['number'] == ch_num), None)
                if ch_info and ch_info['title']:
                    md_lines.extend(['', '', f'## Chapter {ch_num}', '', f'### {ch_info["title"]}', '', ''])
                    # Calculate how many lines to skip for the title
                    title_line_count = len(ch_info['title'].split('\n'))
                    skip_line_count = max(3, title_line_count + 2)
                else:
                    md_lines.extend(['', '', f'## Chapter {ch_num}', '', ''])
                continue

            # Detect appendix
            if stripped.startswith('APPENDIX'):
                md_lines.extend(['', '', f'## {stripped}', '', ''])
                continue

            # Add regular content
            md_lines.append(line.rstrip())

        # Write output
        markdown_content = '\n'.join(md_lines)

        # Final cleanup: remove excessive blank lines
        markdown_content = re.sub(r'\n{4,}', '\n\n\n', markdown_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return markdown_content, chapters


def main():
    processor = EnhancedProcessor('/tmp/toru_dutt_raw.txt')

    output_dir = Path('/home/user/poesis/toru_dutt_output')
    output_dir.mkdir(exist_ok=True)

    # Create enhanced markdown
    md_content, chapters = processor.create_clean_markdown(output_dir / 'toru_dutt_enhanced.md')

    print(f"✓ Created enhanced Markdown: toru_dutt_enhanced.md")
    print(f"  Total length: {len(md_content):,} characters")
    print(f"\n✓ Found {len(chapters)} chapters:")
    for ch in chapters:
        title_preview = ch['title'][:70] + '...' if len(ch['title']) > 70 else ch['title']
        print(f"  Chapter {ch['number']:>3}: {title_preview}")

    # Save chapter info
    with open(output_dir / 'chapters.json', 'w', encoding='utf-8') as f:
        json.dump(chapters, f, indent=2)


if __name__ == '__main__':
    main()
