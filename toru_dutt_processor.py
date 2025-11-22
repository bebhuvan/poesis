#!/usr/bin/env python3
"""
Text processor for digitizing "Life and Letters of Toru Dutt" (1921)
Cleans OCR errors, formats text, and structures content for e-book publication
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple


class ToruDuttProcessor:
    def __init__(self, input_file: str):
        self.input_file = input_file
        with open(input_file, 'r', encoding='utf-8') as f:
            self.raw_text = f.read()
        self.lines = self.raw_text.split('\n')

    def clean_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors"""
        replacements = {
            # Common OCR character substitutions
            r'\^': '',  # Remove stray carets
            r'Torn\b': 'Toru',  # Common OCR error for Toru
            r'Tennysoi\^\.': 'Tennyson.',
            r'PREDERIOK': 'FREDERICK',
            r'EAELY': 'EARLY',
            r'EUEOPE': 'EUROPE',
            r'PEEPAEATION': 'PREPARATION',
            r'CAEEEE': 'CAREER',
            r'LETTEES': 'LETTERS',
            r'TOEU': 'TORU',
            r'FOEEWORD': 'FOREWORD',
            r'POREWOED': 'FOREWORD',
            r'wo\b': 'we',  # Common OCR error
            r'nothii\^g': 'nothing',
            r'imited': 'united',
            r'con¬\s*tained': 'contained',
            r'attrac¬\s*tion': 'attraction',
            r'Ban+erjea': 'Banerjea',
            r'Dkcember': 'December',
            r'Dkcbmber': 'December',
            r'Refrence': 'Reference',
            # Fix hyphenation across line breaks
            r'¬\s+': '',
            # Normalize multiple spaces
            r' {2,}': ' ',
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        return text

    def remove_library_stamps(self, lines: List[str]) -> List[str]:
        """Remove library stamps and administrative text"""
        cleaned_lines = []
        skip_patterns = [
            r'Lai Bahadur Shastri',
            r'LAL BAHADUR',
            r'MUSSOORIE',
            r'LIBRARY',
            r'Accession No',
            r'Class No',
            r'Book No',
            r'Author',
            r'Books are Issued',
            r'over-due charge',
            r'Books may be renewed',
            r'Periodicals.*Rare',
            r'Books lost.*defaced',
            r'borrower',
            r'moving',
            r'^\s*\d+\s*$',  # Lines with just numbers
            r'^\s*[\.]{2,}',  # Lines with just dots
            r'^3T\^Tf',  # Devanagari script artifacts
            r'^\s*#\^',  # More artifacts
            r'320\.54092',  # Catalog numbers
            r'44 4\^47',  # More catalog numbers
        ]

        for line in lines:
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_skip = True
                    break
            if not should_skip:
                cleaned_lines.append(line)

        return cleaned_lines

    def extract_structure(self) -> Dict:
        """Extract book structure (chapters, sections)"""
        structure = {
            'title': 'Life and Letters of Toru Dutt',
            'author': 'Harihar Das',
            'year': '1921',
            'foreword_author': 'H. A. L. Fisher',
            'chapters': [],
            'sections': []
        }

        chapter_pattern = r'^CHAPTER\s+([IVXLCDM]+)\s*$'

        for i, line in enumerate(self.lines):
            match = re.match(chapter_pattern, line.strip())
            if match:
                chapter_num = match.group(1)
                # Get chapter title (usually 2-3 lines after CHAPTER)
                title = ''
                for j in range(1, 6):
                    if i + j < len(self.lines):
                        potential_title = self.lines[i + j].strip()
                        if potential_title and not re.match(r'^[A-Z\s]+$', potential_title):
                            break
                        if potential_title and len(potential_title) > 3:
                            title = potential_title
                            break

                structure['chapters'].append({
                    'number': chapter_num,
                    'title': title,
                    'line_number': i
                })

        # Find key sections
        for i, line in enumerate(self.lines):
            line_upper = line.strip().upper()
            if line_upper == 'FOREWORD':
                structure['sections'].append({'type': 'foreword', 'line': i})
            elif line_upper == 'CONTENTS':
                structure['sections'].append({'type': 'contents', 'line': i})
            elif line_upper.startswith('APPENDIX'):
                structure['sections'].append({'type': 'appendix', 'line': i})

        return structure

    def format_text(self) -> str:
        """Format the cleaned text with proper structure"""
        # Clean lines
        cleaned_lines = self.remove_library_stamps(self.lines)

        # Join and clean text
        text = '\n'.join(cleaned_lines)
        text = self.clean_ocr_errors(text)

        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        # Ensure chapter headings have proper spacing
        text = re.sub(r'\n(CHAPTER [IVXLCDM]+)\n', r'\n\n\n\1\n\n', text)

        # Ensure section headings have proper spacing
        text = re.sub(r'\n(FOREWORD|CONTENTS|APPENDIX)\n', r'\n\n\n\1\n\n', text)

        return text

    def create_markdown(self) -> str:
        """Create a well-formatted Markdown version"""
        structure = self.extract_structure()
        formatted = self.format_text()
        lines = formatted.split('\n')

        markdown_lines = []
        markdown_lines.append('# Life and Letters of Toru Dutt')
        markdown_lines.append('')
        markdown_lines.append('**By Harihar Das**')
        markdown_lines.append('')
        markdown_lines.append('*With a Foreword by The Right Hon. H. A. L. Fisher, M.P.*')
        markdown_lines.append('')
        markdown_lines.append('---')
        markdown_lines.append('')
        markdown_lines.append('*Oxford University Press, 1921*')
        markdown_lines.append('')
        markdown_lines.append('---')
        markdown_lines.append('')

        # Process the rest of the content
        skip_until = 0
        for i, line in enumerate(lines):
            if i < skip_until:
                continue

            # Skip initial title pages (already added)
            if i < 100 and re.search(r'PRINTED IN ENGLAND|OXFORD UNIVERSITY PRESS|HUMPHREY MILFORD', line):
                continue

            # Convert chapter headings to Markdown
            if re.match(r'^CHAPTER\s+[IVXLCDM]+\s*$', line.strip()):
                markdown_lines.append('')
                markdown_lines.append(f'## {line.strip()}')
                markdown_lines.append('')
                skip_until = i + 1
                continue

            # Convert section headings
            line_upper = line.strip().upper()
            if line_upper in ['FOREWORD', 'CONTENTS', 'APPENDIX']:
                markdown_lines.append('')
                markdown_lines.append(f'## {line_upper.title()}')
                markdown_lines.append('')
                continue

            # Add regular lines
            markdown_lines.append(line)

        return '\n'.join(markdown_lines)

    def save_outputs(self, output_dir: str = '/home/user/poesis/toru_dutt_output'):
        """Save cleaned text in multiple formats"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save structure metadata
        structure = self.extract_structure()
        with open(output_path / 'structure.json', 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2)

        # Save cleaned plain text
        formatted_text = self.format_text()
        with open(output_path / 'toru_dutt_cleaned.txt', 'w', encoding='utf-8') as f:
            f.write(formatted_text)

        # Save Markdown version
        markdown = self.create_markdown()
        with open(output_path / 'toru_dutt.md', 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"✓ Processed and saved outputs to: {output_path}")
        print(f"  - structure.json: Book structure metadata")
        print(f"  - toru_dutt_cleaned.txt: Clean plain text ({len(formatted_text)} chars)")
        print(f"  - toru_dutt.md: Markdown format ({len(markdown)} chars)")
        print(f"\nFound {len(structure['chapters'])} chapters:")
        for ch in structure['chapters']:
            print(f"  Chapter {ch['number']}: {ch['title'][:60]}")


if __name__ == '__main__':
    processor = ToruDuttProcessor('/tmp/toru_dutt_raw.txt')
    processor.save_outputs()
