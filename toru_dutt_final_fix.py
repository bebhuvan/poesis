#!/usr/bin/env python3
"""
Final comprehensive fix for all OCR and formatting issues
"""

import re
import json
from pathlib import Path


class FinalProcessor:
    def __init__(self, input_file: str):
        with open(input_file, 'r', encoding='utf-8') as f:
            self.raw_text = f.read()
        self.lines = self.raw_text.split('\n')

    def comprehensive_ocr_fix(self, text: str) -> str:
        """Fix all known OCR errors"""
        # Dictionary of all OCR replacements
        replacements = {
            # Chapter title errors
            r'\bEAELY\b': 'EARLY',
            r'\bEUEOPE\b': 'EUROPE',
            r'\bPEEPAEATION\b': 'PREPARATION',
            r'\bFOE A\b': 'FOR A',
            r'\bCAEEEE\b': 'CAREER',
            r'\bLETTEBS\b': 'LETTERS',
            r'\bLETTEES\b': 'LETTERS',
            r'\bLETTEKS\b': 'LETTERS',
            r'\bLETTEB&\b': 'LETTERS',
            r'\bMAETIN\b': 'MARTIN',
            r'\bMABTIN\b': 'MARTIN',
            r'\bJANUAEY\b': 'JANUARY',
            r'\bJANUABY\b': 'JANUARY',
            r'\bDEGEMBEB\b': 'DECEMBER',
            r'\bDECEMBEE\b': 'DECEMBER',
            r'\bDkcember\b': 'December',
            r'\bOP TORU\b': 'OF TORU',
            r'\bOP\b(?= [A-Z])': 'OF',  # OP before capital letter
            r'\bOB THE\b': 'OR THE',
            r'\bABVEBS\b': 'ARVERS',
            r'\bSUPPLEMENTAEY\b': 'SUPPLEMENTARY',
            r'\bMe\. E\. J\.': 'Mr. E. J.',

            # Name errors
            r'\bTOBU\b': 'TORU',
            r'\bTOKU\b': 'TORU',
            r'\bTorn\b': 'Toru',
            r'\bDTJTT\b': 'DUTT',
            r'\bDtJTT\b': 'DUTT',
            r'\bDUTT\b(?=\.)': 'DUTT',

            # Common word errors
            r'\bANf\)': 'AND',
            r'\bwo\b': 'we',
            r'\bherlove\b': 'her love',
            r'\bimited\b': 'united',
            r'\bho\b(?= bare)': 'he',

            # Publisher/printer errors
            r'\bPREDERIOK\b': 'FREDERICK',
            r'\bFREDERIOK\b': 'FREDERICK',

            # Fix French accents
            r'\b6toit\b': 'était',
            r'\b6cu\b': 'écu',
            r'\bv6cu\b': 'vécu',
            r'\boik\b': 'où',

            # Punctuation and formatting
            r'field\'of': 'field of',
            r'con-?\s*tained': 'contained',
            r'attrac-?\s*tion': 'attraction',
            r'Ban+erjea': 'Banerjea',
            r'Tennysoi[\^\.]+': 'Tennyson.',
            r'nothii\^?g': 'nothing',
            r'INDIAJ\^?': 'INDIAN',

            # Remove artifacts
            r'\^': '',
            r'¬\s*': '',

            # Normalize spaces
            r' {2,}': ' ',
            r'\t+': ' ',
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        return text

    def remove_running_headers(self, lines: list) -> list:
        """Remove page headers and footers"""
        cleaned = []
        header_patterns = [
            r'^\d{1,3}\s+LIFE AND LETTERS',
            r'^LIFE AND LETTERS OF TO[BRK]U',
            r'^LETTERS TO MISS MA[BE]TIN',
            r'^LETTEBS TO MISS',
            r'^\d{1,3}\s*$',  # Standalone page numbers
            r'^[ivxlcdm]+\s+FOREWORD\s*$',  # Roman numeral + FOREWORD
            r'^FOREWORD\s+[ivxlcdm]+\s*$',
            r'^\s*\d{1,3}\s+$',
        ]

        for line in lines:
            stripped = line.strip()
            should_remove = False

            for pattern in header_patterns:
                if re.match(pattern, stripped, re.IGNORECASE):
                    should_remove = True
                    break

            if not should_remove:
                cleaned.append(line)

        return cleaned

    def remove_library_artifacts(self, lines: list) -> list:
        """Remove library stamps, catalog marks, and artifacts"""
        cleaned = []
        skip_patterns = [
            r'Lai Bahadur Shastri',
            r'LAL BAHADUR',
            r'MUSSOORIE',
            r'^LIBRARY\s*$',
            r'Accession',
            r'Class No',
            r'Book No',
            r'^Author\s*$',
            r'Books are Issued',
            r'over-due charge',
            r'Books may be renewed',
            r'Periodicals.*Rare',
            r'Books lost.*defaced',
            r'borrower',
            r'^moving\s*$',
            r'^3T\^?Tf',
            r'^\s*#[\^trT]+',
            r'^\.+stst',
            r'^\.+li2\.0T',
            r'^\.Tiuh',
            r'^\s*\.+\s*$',
            r'^320\.54092',
            r'44 4\^?47',
            r'^\d+\s*$',  # Lines with just a number (page/catalog)
            r'^[\.]{3,}',  # Lines with multiple dots
            r'AT THE OXFORD UNIVERSITY PRESS',
            r'BY FREDERICK HALL',
        ]

        for line in lines:
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_skip = True
                    break
            if not should_skip:
                cleaned.append(line)

        return cleaned

    def extract_chapter_titles(self) -> dict:
        """Extract proper chapter titles"""
        chapters = []
        chapter_pattern = r'^CHAPTER\s+([IVXLCDM]+)\s*$'

        for i, line in enumerate(self.lines):
            match = re.match(chapter_pattern, line.strip())
            if match:
                chapter_num = match.group(1)
                title_lines = []

                # Look ahead for title (next 10 lines)
                for j in range(1, 11):
                    if i + j >= len(self.lines):
                        break

                    next_line = self.lines[i + j].strip()

                    # Skip empty lines
                    if not next_line:
                        continue

                    # Stop at lowercase paragraph text
                    if next_line and not next_line[0].isupper():
                        break

                    # Stop at dates or obvious content
                    if re.match(r'[A-Z][a-z]+ \d{4}', next_line):
                        break
                    if re.match(r'^[A-Z][a-z]+.*was born', next_line):
                        break

                    # Check if it's a running header
                    if re.match(r'\d+\s+LIFE AND', next_line):
                        continue

                    # Add if it looks like a title
                    if next_line and (next_line.isupper() or len(next_line) < 100):
                        title_lines.append(next_line)
                    else:
                        break

                    # Stop after finding reasonable title
                    if len(' '.join(title_lines)) > 20:
                        break

                title = ' '.join(title_lines)
                chapters.append({
                    'number': chapter_num,
                    'title': self.comprehensive_ocr_fix(title),
                    'line_number': i
                })

        return chapters

    def create_clean_markdown(self) -> str:
        """Create final clean markdown"""
        # Remove headers and artifacts
        cleaned_lines = self.remove_running_headers(self.lines)
        cleaned_lines = self.remove_library_artifacts(cleaned_lines)

        # Join and apply OCR fixes
        text = '\n'.join(cleaned_lines)
        text = self.comprehensive_ocr_fix(text)

        # Split back into lines
        lines = text.split('\n')

        # Build final markdown
        md_lines = []
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

        # Track sections to avoid duplicates
        seen_sections = set()
        in_front_matter = True
        skip_until = 0

        for i, line in enumerate(lines):
            if i < skip_until:
                continue

            stripped = line.strip()

            # Skip initial title material (already added)
            if in_front_matter and i < 100:
                if re.search(r'LIFE AND LETTERS OF|TORU DUTT|HARIHAR DAS|OXFORD UNIVERSITY', stripped):
                    continue

            # Handle major sections (avoid duplicates)
            section_match = re.match(r'^(FOREWORD|CONTENTS|PREFACE)$', stripped, re.IGNORECASE)
            if section_match:
                section_name = section_match.group(1).lower()
                if section_name not in seen_sections:
                    in_front_matter = False
                    seen_sections.add(section_name)
                    md_lines.extend(['', '', f'## {stripped.title()}', '', ''])
                continue

            # Handle chapters
            chapter_match = re.match(r'^CHAPTER\s+([IVXLCDM]+)\s*$', stripped)
            if chapter_match:
                in_front_matter = False
                ch_num = chapter_match.group(1)

                # Find chapter title
                title = ''
                title_lines = []
                for j in range(1, 8):
                    if i + j < len(lines):
                        candidate = lines[i + j].strip()
                        if candidate and not re.match(r'^\d+|^[a-z]', candidate):
                            if candidate.isupper() or (len(candidate) < 100 and candidate[0].isupper()):
                                title_lines.append(candidate)
                                if len(' '.join(title_lines)) > 20:
                                    break
                        elif title_lines:
                            break

                title = ' '.join(title_lines)

                md_lines.extend(['', '', f'## Chapter {ch_num}', ''])
                if title:
                    md_lines.extend([f'### {title}', '', ''])
                    skip_until = i + len(title_lines) + 2
                continue

            # Handle appendices
            if stripped.startswith('APPENDIX'):
                md_lines.extend(['', '', f'## {stripped}', '', ''])
                continue

            # Skip garbage lines (non-printable or weird characters)
            if re.search(r'[«»€]+|[\^]{2,}', stripped):
                continue

            # Add regular content
            md_lines.append(line.rstrip())

        # Final cleanup
        result = '\n'.join(md_lines)
        result = re.sub(r'\n{4,}', '\n\n\n', result)  # Max 2 blank lines

        return result

    def save_outputs(self, output_dir: str):
        """Save all cleaned outputs"""
        output_path = Path(output_dir)

        # Get chapters
        chapters = self.extract_chapter_titles()

        # Create clean markdown
        clean_md = self.create_clean_markdown()

        # Save files
        with open(output_path / 'toru_dutt_final.md', 'w', encoding='utf-8') as f:
            f.write(clean_md)

        with open(output_path / 'chapters_final.json', 'w', encoding='utf-8') as f:
            json.dump(chapters, f, indent=2, ensure_ascii=False)

        print(f"✓ Created final cleaned version")
        print(f"  Markdown: {len(clean_md):,} characters")
        print(f"  Chapters: {len(chapters)}")
        print(f"\nChapter titles:")
        for ch in chapters:
            print(f"  Chapter {ch['number']:>3}: {ch['title']}")

        return clean_md, chapters


def main():
    processor = FinalProcessor('/tmp/toru_dutt_raw.txt')
    processor.save_outputs('/home/user/poesis/toru_dutt_output')


if __name__ == '__main__':
    main()
