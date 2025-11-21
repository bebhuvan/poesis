#!/usr/bin/env python3
"""
Comprehensive Gandhi Letters OCR Extraction and Improvement Tool

This script extracts letters from OCR text, applies corrections,
and generates publication-ready markdown files with metadata.
"""

import re
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class OCRCorrector:
    """Handles OCR correction patterns and text cleaning."""

    def __init__(self):
        # Character-level OCR corrections
        self.char_corrections = {
            # Common character misreadings
            r'\bI\b(?=[a-z])': 'l',  # I -> l when followed by lowercase
            r'(?<=[a-z])I(?=[a-z])': 'l',  # I -> l in middle of words
            r'rn(?=[a-z])': 'm',  # rn -> m
            r'(?<=\w)IVI(?=\w)': 'M',  # IVI -> M
            r'(?<=\w)vv': 'w',  # vv -> w
            r'(?<=\w)VV': 'W',  # VV -> W
            r'\bII\b': 'H',  # II -> H
            r'0(?=[a-z])': 'o',  # 0 -> o before lowercase
            r'(?<=[A-Z])0(?=[a-z])': 'o',  # 0 -> o in words
            r'\bl\)': 'D',  # l) -> D
            r'\(\)': 'O',  # () -> O
        }

        # Common word corrections
        self.word_corrections = {
            # Names and proper nouns
            r'\bGrandhiji\b': 'Gandhiji',
            r'\bGrandhi\b': 'Gandhi',
            r'\bIVHabatma\b': 'Mahatma',
            r'\bIVEahatma\b': 'Mahatma',
            r'\bIVlahatma\b': 'Mahatma',
            r'\bMahatmaji\b': 'Mahatma',
            r'\bGanclhiji\b': 'Gandhiji',
            r'\bChclmsford\b': 'Chelmsford',
            r'\bChelrnsfcrrd\b': 'Chelmsford',
            r'\bChemlsford\b': 'Chelmsford',
            r'\bChelmsfcrrd\b': 'Chelmsford',
            r'\bLinlithgov\b': 'Linlithgow',
            r'\bLinlithow\b': 'Linlithgow',
            r'\bWillingclon\b': 'Willingdon',
            r'\bReacling\b': 'Reading',
            r'\bBcsant\b': 'Besant',
            r'\bTilalc\b': 'Tilak',
            r'\bJinnali\b': 'Jinnah',
            r'\bMacDonalcl\b': 'MacDonald',
            r'\bKasturba\b': 'Kasturba',
            r'\bSabarmati\b': 'Sabarmati',
            r'\bMiraBai\b': 'Mirabehn',

            # Common words
            r'\bIVIr\b': 'Mr',
            r'\bMrs\b\.': 'Mrs.',
            r'\bIVIrs\b': 'Mrs',
            r'\blt>e\b': 'be',
            r'\bIiave\b': 'have',
            r'\bI\)een\b': 'been',
            r'\bgoocl\b': 'good',
            r'\btlie\b': 'the',
            r'\bthat\b\.': 'that.',
            r'\bwhicli\b': 'which',
            r'\bwliich\b': 'which',
            r'\bwlio\b': 'who',
            r'\bwliom\b': 'whom',
            r'\bwhen\b\.': 'when.',
            r'\bwliere\b': 'where',
            r'\bYonr\b': 'Your',
            r'\bYour\s+Excellency\b': 'Your Excellency',
            r'\bHis\s+Excellency\b': 'His Excellency',
            r'\bGovernment\b': 'Government',
            r'\bGovemment\b': 'Government',
            r'\bG-overnment\b': 'Government',
            r'\bG-ovemment\b': 'Government',
            r'\bBritisli\b': 'British',
            r'\b^British\b': 'British',
            r'\bImpcrialisna\b': 'Imperialism',
            r'\bImperialisna\b': 'Imperialism',
            r'\bIndia\b': 'India',
            r'\bInclia\b': 'India',
            r'\blndian\b': 'Indian',
            r'\bConference\b': 'Conference',
            r'\bconference\b': 'conference',
            r'\bletters\b': 'letters',
            r'\binvaltiatole\b': 'invaluable',
            r'\bdocuixiezits\b': 'documents',
            r'\bcarefixlly\b': 'carefully',
            r'\bsocio-econo-mic\b': 'socio-economic',
            r'\bsignificant\b': 'significant',
            r'\brepresentatives\b': 'representatives',
            r'\btha\s+\^British\b': 'the British',
            r'\bdesires\b': 'desires',
            r'\bpermeates\b': 'permeates',

            # Special patterns
            r'Pack\s*$': 'Page',
            r'\bAathor\b': 'Author',
            r'\bBi\(\^;raphical\b': 'Biographical',
            r'\bI\'o\s+Every\b': 'To Every',
            r'\bYoungmen\b': 'Young Men',
            r'\bchUdren\b': 'children',
            r'\buntouchable\b': 'untouchable',
            r'\bdaugh-ter\b': 'daughter',
            r'\bSecond\s+Rejoin-der\b': 'Second Rejoinder',

            # Punctuation fixes
            r'\s+\.': '.',
            r'\s+,': ',',
            r'\s+;': ';',
            r'\s+:': ':',
            r'\s+\!': '!',
            r'\s+\?': '?',
            r'\.\.+': '.',
            r'\s+\)': ')',
            r'\(\s+': '(',
        }

        # Track corrections made
        self.corrections_made = defaultdict(int)

    def correct_text(self, text: str) -> str:
        """Apply all OCR corrections to text."""
        original_text = text

        # Apply character-level corrections
        for pattern, replacement in self.char_corrections.items():
            matches = len(re.findall(pattern, text))
            if matches > 0:
                text = re.sub(pattern, replacement, text)
                self.corrections_made[f"char: {pattern} -> {replacement}"] += matches

        # Apply word-level corrections
        for pattern, replacement in self.word_corrections.items():
            matches = len(re.findall(pattern, text))
            if matches > 0:
                text = re.sub(pattern, replacement, text)
                self.corrections_made[f"word: {pattern} -> {replacement}"] += matches

        # Remove special arrow characters from line starts
        text = re.sub(r'→', '', text)

        # Fix broken words with special characters
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Clean up multiple spaces
        text = re.sub(r'[ \t]+', ' ', text)

        # Clean up multiple newlines (but keep paragraph breaks)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        return text.strip()

    def get_corrections_report(self) -> str:
        """Generate a report of all corrections made."""
        report = "# OCR Corrections Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "## Summary\n\n"

        total_corrections = sum(self.corrections_made.values())
        report += f"Total corrections made: {total_corrections}\n\n"

        report += "## Detailed Corrections\n\n"

        # Group by type
        char_corrections = {k: v for k, v in self.corrections_made.items() if k.startswith('char:')}
        word_corrections = {k: v for k, v in self.corrections_made.items() if k.startswith('word:')}

        if char_corrections:
            report += "### Character-level Corrections\n\n"
            for correction, count in sorted(char_corrections.items(), key=lambda x: -x[1]):
                report += f"- {correction}: {count} instances\n"
            report += "\n"

        if word_corrections:
            report += "### Word-level Corrections\n\n"
            for correction, count in sorted(word_corrections.items(), key=lambda x: -x[1]):
                report += f"- {correction}: {count} instances\n"
            report += "\n"

        return report


class LetterExtractor:
    """Extracts and processes letters from OCR text."""

    def __init__(self, ocr_file_path: str):
        self.ocr_file_path = ocr_file_path
        self.corrector = OCRCorrector()
        self.letters = []
        self.toc = []
        self.quality_issues = []

    def read_file(self) -> List[str]:
        """Read the OCR file and return lines."""
        with open(self.ocr_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Remove line numbers and arrows from each line
        cleaned_lines = []
        for line in lines:
            # Remove pattern like "  413→" at start of line
            line = re.sub(r'^\s*\d+→', '', line)
            cleaned_lines.append(line)
        return cleaned_lines

    def extract_toc(self, lines: List[str]) -> List[Dict]:
        """Extract Table of Contents."""
        toc = []
        in_toc = False

        for i, line in enumerate(lines):
            line = line.strip()

            if 'TABLE OF CONTENTS' in line or 'CONTENTS' in line:
                in_toc = True
                continue

            if in_toc:
                # End of TOC when we hit a major section
                if re.match(r'^MAHATMA GANDHI', line) or re.match(r'^LETTER TO', line):
                    break

                # Parse TOC entries
                # Look for patterns like: "3. Letter to Lord Chelmsford ... 13"
                match = re.match(r'^\s*(\d+)\.\s+(.+?)\s+\.+\s*(\d+)', line)
                if match:
                    toc.append({
                        'number': int(match.group(1)),
                        'title': match.group(2).strip(),
                        'page': int(match.group(3))
                    })
                # Also handle multi-line entries
                elif line and not line.startswith('Pack') and len(line) > 3:
                    # This might be a continuation or a title without page number yet
                    if toc and 'title' in toc[-1]:
                        # Check if this is a continuation
                        if not re.search(r'\d+$', toc[-1]['title']):
                            toc[-1]['title'] += ' ' + line

        return toc

    def identify_letter_boundaries(self, lines: List[str]) -> List[Tuple[int, str]]:
        """Identify where each letter starts."""
        boundaries = []
        seen_titles = set()  # Track to avoid duplicates

        for i, line in enumerate(lines):
            line_clean = line.strip()

            # Skip very early lines (likely in TOC or intro)
            if i < 400:
                continue

            # Skip if line is too short
            if len(line_clean) < 10:
                continue

            # Skip common page headers/footers
            if re.match(r'^(Famous Letters|Letter to|Ultimatum to|Letters to)\s+(Lord|the)\s+\w+\.\s*\d+$', line_clean):
                continue
            if re.match(r'^\d+$', line_clean):
                continue

            title = None

            # Main letter headers - all caps patterns (must be substantial)
            # LETTER TO patterns
            if re.match(r'^LETTER\s+TO\s+LORD\s+\w+', line_clean):
                title = line_clean
            # ULTIMATUM TO patterns
            elif re.match(r'^ULTIMATUM\s+TO\s+LORD\s+\w+', line_clean):
                title = line_clean
            # LETTERS TO patterns
            elif re.match(r'^LETTERS\s+TO\s+LORD\s+\w+', line_clean):
                title = line_clean
            elif re.match(r'^LETTERS\s+TO\s+THE\s+(INMATES|NATION)', line_clean):
                title = line_clean
            # TO THE patterns
            elif re.match(r'^TO\s+THE\s+(NATION|PEOPLE\s+OF\s+AMERICA|YOUNGMEN\s+OF\s+BENGAL|INMATES|HOME\s+MEMBER)', line_clean):
                title = line_clean
            # TO EVERY patterns
            elif re.match(r'^TO\s+EVERY\s+ENGLISHMAN', line_clean):
                title = line_clean
            # TO HIS/GENERALISSIMO/MARSHAL patterns
            elif re.match(r'^TO\s+(HIS\s+ROYAL\s+HIGHNESS|GENERALISSIMO|MARSHAL|RAMSAY\s+MACDONALD)', line_clean, re.IGNORECASE):
                title = line_clean
            # TO Sir/Mr patterns
            elif re.match(r'^TO\s+(Sir\s+Samuel|Sir\s+Richard|Mr\.\s+M\.\s*A\.\s+JINNAH)', line_clean, re.IGNORECASE):
                title = line_clean
            # TO LORD patterns (for Lord Linlithgow, etc.)
            elif re.match(r'^TO\s+LORD\s+\w+', line_clean):
                title = line_clean
            # LETTERS WRITTEN pattern
            elif re.match(r'^LETTERS\s+WRITTEN\s+BY\s+GANDHIJI\s+TO\s+THE', line_clean):
                title = line_clean

            if title:
                # Normalize title for comparison
                title_normalized = re.sub(r'\s+', ' ', title).strip().upper()
                # Remove common suffixes like page numbers for comparison
                title_for_comparison = re.sub(r'\.\s*\d+\s*$', '', title_normalized)

                # Check if we've seen a very similar title recently (within 100 lines)
                is_duplicate = False
                for prev_line, prev_title in boundaries:
                    prev_normalized = re.sub(r'\s+', ' ', prev_title).strip().upper()
                    prev_for_comparison = re.sub(r'\.\s*\d+\s*$', '', prev_normalized)

                    # Check for exact match or very similar titles
                    if abs(i - prev_line) < 100:
                        # Exact match
                        if title_for_comparison == prev_for_comparison:
                            is_duplicate = True
                            break
                        # Similar match (Levenshtein-like check for minor variations)
                        if len(title_for_comparison) > 15 and len(prev_for_comparison) > 15:
                            # Check if one is a substring of the other
                            if title_for_comparison in prev_for_comparison or prev_for_comparison in title_for_comparison:
                                is_duplicate = True
                                break

                if not is_duplicate:
                    boundaries.append((i, title))

        # Sort by line number
        boundaries.sort(key=lambda x: x[0])

        return boundaries

    def extract_metadata(self, title: str, content: str) -> Dict:
        """Extract metadata from letter title and content."""
        metadata = {
            'title': title,
            'recipient': None,
            'date': None,
            'subject': None,
            'letter_type': None
        }

        # Determine letter type
        if 'ULTIMATUM' in title.upper():
            metadata['letter_type'] = 'ultimatum'
        elif 'LETTER' in title.upper():
            metadata['letter_type'] = 'letter'
        else:
            metadata['letter_type'] = 'communication'

        # Extract recipient
        recipient_patterns = [
            r'(?:LETTER |ULTIMATUM |TO )+(.+?)(?:\.|$)',
            r'(?:LETTERS TO )(.+?)(?:\.|$)',
        ]

        for pattern in recipient_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                metadata['recipient'] = match.group(1).strip()
                # Clean up recipient name
                metadata['recipient'] = re.sub(r'\s+', ' ', metadata['recipient'])
                metadata['recipient'] = metadata['recipient'].strip('.')
                break

        # Extract date from content (look in first 100 lines)
        content_lines = content.split('\n')[:100]
        for line in content_lines:
            # Look for date patterns
            date_patterns = [
                # Full date with month name
                r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+\d{4})\b',
                r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?[,\s]+\d{4})\b',
                # Date in parentheses or with year
                r'\(([^)]*(?:19\d{2}|1[89]\d{2})[^)]*)\)',
                # Year with period mentioned
                r'\b((?:year|period|in)\s+(?:19\d{2}|1[89]\d{2}))\b',
                # Numeric dates
                r'\b(\d{1,2}[/-]\d{1,2}[/-](?:19\d{2}|1[89]\d{2}))\b',
            ]

            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    # Make sure it's not too long (likely not just a date)
                    if len(date_str) < 100:
                        metadata['date'] = date_str.strip()
                        break
            if metadata['date']:
                break

        # Extract subject from parenthetical notes
        subject_match = re.search(r'\(([^)]+)\)', content[:500])
        if subject_match:
            subject_text = subject_match.group(1)
            if len(subject_text) < 200:  # Reasonable subject length
                metadata['subject'] = subject_text.strip()

        return metadata

    def extract_letters(self):
        """Main extraction method."""
        print("Reading OCR file...")
        lines = self.read_file()

        print("Extracting Table of Contents...")
        self.toc = self.extract_toc(lines)
        print(f"Found {len(self.toc)} TOC entries")

        print("Identifying letter boundaries...")
        boundaries = self.identify_letter_boundaries(lines)
        print(f"Found {len(boundaries)} letter boundaries")

        print("Extracting and correcting letters...")
        for idx, (start_line, title) in enumerate(boundaries):
            # Determine end line (start of next letter or end of file)
            if idx < len(boundaries) - 1:
                end_line = boundaries[idx + 1][0]
            else:
                end_line = len(lines)

            # Extract raw content
            raw_content = ''.join(lines[start_line:end_line])

            # Apply OCR corrections
            corrected_content = self.corrector.correct_text(raw_content)

            # Extract metadata
            metadata = self.extract_metadata(title, corrected_content)

            # Quality checks
            issues = []
            if not metadata['date']:
                issues.append('No date found')
            if len(corrected_content) < 100:
                issues.append('Very short content')
            if not metadata['recipient']:
                issues.append('No recipient identified')

            # Create letter object
            letter = {
                'id': idx + 1,
                'metadata': metadata,
                'content': corrected_content,
                'raw_content': raw_content,
                'start_line': start_line,
                'end_line': end_line,
                'quality_issues': issues
            }

            self.letters.append(letter)

            if issues:
                self.quality_issues.extend([f"Letter {idx + 1} ({title}): {issue}" for issue in issues])

        print(f"Extracted {len(self.letters)} letters")

    def generate_markdown(self, letter: Dict) -> str:
        """Generate markdown file content for a letter."""
        md = "---\n"
        md += f"title: \"{letter['metadata']['title']}\"\n"
        md += f"letter_id: {letter['id']}\n"

        if letter['metadata']['recipient']:
            md += f"recipient: \"{letter['metadata']['recipient']}\"\n"

        if letter['metadata']['date']:
            md += f"date: \"{letter['metadata']['date']}\"\n"

        md += f"letter_type: \"{letter['metadata']['letter_type']}\"\n"

        if letter['metadata']['subject']:
            md += f"subject: \"{letter['metadata']['subject']}\"\n"

        md += "author: \"Mahatma Gandhi\"\n"
        md += "source: \"Famous Letters of Mahatma Gandhi (1947)\"\n"
        md += "ocr_corrected: true\n"

        if letter['quality_issues']:
            md += f"quality_notes:\n"
            for issue in letter['quality_issues']:
                md += f"  - \"{issue}\"\n"

        md += "---\n\n"
        md += f"# {letter['metadata']['title']}\n\n"
        md += letter['content']
        md += "\n"

        return md

    def save_letters(self, output_dir: str):
        """Save all letters as individual markdown files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving letters to {output_dir}...")

        for letter in self.letters:
            # Generate filename
            filename = f"letter_{letter['id']:03d}"

            # Add recipient to filename if available
            if letter['metadata']['recipient']:
                recipient_slug = re.sub(r'[^a-zA-Z0-9]+', '_', letter['metadata']['recipient'].lower())
                recipient_slug = recipient_slug.strip('_')[:50]
                filename += f"_{recipient_slug}"

            filename += ".md"

            # Generate and save markdown
            md_content = self.generate_markdown(letter)

            filepath = output_path / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"  Saved: {filename}")

    def generate_manifest(self, output_dir: str):
        """Generate manifest.json with metadata about all letters."""
        manifest = {
            'metadata': {
                'source': 'Famous Letters of Mahatma Gandhi',
                'compiler': 'R. L. KHIPPLE, M.A.',
                'publisher': 'THE INDIAN PRINTING WORKS',
                'publication_year': 1947,
                'publication_place': 'Lahore',
                'extraction_date': datetime.now().isoformat(),
                'total_letters': len(self.letters),
                'ocr_corrections_applied': True,
            },
            'table_of_contents': self.toc,
            'letters': []
        }

        for letter in self.letters:
            manifest['letters'].append({
                'id': letter['id'],
                'title': letter['metadata']['title'],
                'recipient': letter['metadata']['recipient'],
                'date': letter['metadata']['date'],
                'letter_type': letter['metadata']['letter_type'],
                'subject': letter['metadata']['subject'],
                'filename': self.get_filename(letter),
                'quality_issues': letter['quality_issues'],
                'word_count': len(letter['content'].split()),
                'character_count': len(letter['content'])
            })

        filepath = Path(output_dir) / 'manifest.json'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"\nManifest saved to: {filepath}")

    def get_filename(self, letter: Dict) -> str:
        """Generate filename for a letter."""
        filename = f"letter_{letter['id']:03d}"

        if letter['metadata']['recipient']:
            recipient_slug = re.sub(r'[^a-zA-Z0-9]+', '_', letter['metadata']['recipient'].lower())
            recipient_slug = recipient_slug.strip('_')[:50]
            filename += f"_{recipient_slug}"

        return filename + ".md"

    def generate_quality_report(self, output_dir: str):
        """Generate quality improvements report."""
        report = "# Gandhi Letters - Quality Improvements Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += "## Extraction Summary\n\n"
        report += f"- **Total Letters Extracted:** {len(self.letters)}\n"
        report += f"- **Source File:** {self.ocr_file_path}\n"
        report += f"- **Output Directory:** {output_dir}\n\n"

        report += "## OCR Corrections\n\n"
        report += self.corrector.get_corrections_report()

        report += "\n## Quality Assessment\n\n"

        # Count letters by type
        letter_types = defaultdict(int)
        letters_with_dates = 0
        letters_with_recipients = 0

        for letter in self.letters:
            letter_types[letter['metadata']['letter_type']] += 1
            if letter['metadata']['date']:
                letters_with_dates += 1
            if letter['metadata']['recipient']:
                letters_with_recipients += 1

        report += f"### Letter Distribution\n\n"
        for ltype, count in sorted(letter_types.items()):
            report += f"- {ltype.capitalize()}: {count}\n"
        report += "\n"

        report += f"### Metadata Completeness\n\n"
        if len(self.letters) > 0:
            report += f"- Letters with dates: {letters_with_dates}/{len(self.letters)} ({100*letters_with_dates/len(self.letters):.1f}%)\n"
            report += f"- Letters with recipients: {letters_with_recipients}/{len(self.letters)} ({100*letters_with_recipients/len(self.letters):.1f}%)\n\n"
        else:
            report += "- No letters extracted - check boundary detection\n\n"

        if self.quality_issues:
            report += "### Quality Issues Detected\n\n"
            for issue in self.quality_issues[:20]:  # Limit to first 20
                report += f"- {issue}\n"
            if len(self.quality_issues) > 20:
                report += f"\n... and {len(self.quality_issues) - 20} more issues\n"
            report += "\n"

        report += "## Publication Readiness Assessment\n\n"

        # Calculate readiness score
        readiness_score = 0
        max_score = 5

        # Check 1: Most letters extracted
        if len(self.letters) >= 20:
            readiness_score += 1
            report += "- ✓ Sufficient number of letters extracted\n"
        else:
            report += "- ✗ Low number of letters extracted\n"

        # Check 2: Good metadata coverage
        if letters_with_dates / len(self.letters) > 0.5:
            readiness_score += 1
            report += "- ✓ Good date coverage\n"
        else:
            report += "- ✗ Poor date coverage\n"

        # Check 3: Recipients identified
        if letters_with_recipients / len(self.letters) > 0.8:
            readiness_score += 1
            report += "- ✓ Most recipients identified\n"
        else:
            report += "- ✗ Many recipients missing\n"

        # Check 4: OCR corrections applied
        if sum(self.corrector.corrections_made.values()) > 100:
            readiness_score += 1
            report += "- ✓ Significant OCR corrections applied\n"
        else:
            report += "- ⚠ Limited OCR corrections needed\n"

        # Check 5: Quality issues manageable
        if len(self.quality_issues) < len(self.letters) * 2:
            readiness_score += 1
            report += "- ✓ Quality issues are manageable\n"
        else:
            report += "- ✗ Many quality issues detected\n"

        report += f"\n**Overall Readiness Score: {readiness_score}/{max_score}**\n\n"

        if readiness_score >= 4:
            report += "**Status: READY FOR PUBLICATION** - The extracted letters have been well-processed and are suitable for public showcase.\n"
        elif readiness_score >= 3:
            report += "**Status: MOSTLY READY** - The letters are in good shape but may benefit from manual review of quality issues.\n"
        else:
            report += "**Status: NEEDS WORK** - Additional processing and manual review recommended before publication.\n"

        report += "\n## Next Steps\n\n"
        report += "1. Review quality issues and manually correct if needed\n"
        report += "2. Verify metadata accuracy (dates, recipients)\n"
        report += "3. Check formatting of special characters and quotes\n"
        report += "4. Validate all file outputs\n"
        report += "5. Consider adding historical context or annotations\n"

        filepath = Path(output_dir) / 'quality_improvements.md'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\nQuality report saved to: {filepath}")

        return report


def main():
    """Main execution function."""
    # Configuration
    ocr_file = '/home/user/poesis/gandhi_letters/ocr_text.txt'
    output_dir = '/home/user/poesis/gandhi_letters/letters/'

    print("=" * 70)
    print("Gandhi Letters OCR Extraction and Improvement Tool")
    print("=" * 70)
    print()

    # Initialize extractor
    extractor = LetterExtractor(ocr_file)

    # Extract letters
    extractor.extract_letters()

    # Save outputs
    extractor.save_letters(output_dir)
    extractor.generate_manifest(output_dir)
    quality_report = extractor.generate_quality_report(output_dir)

    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print()
    print(f"Total letters extracted: {len(extractor.letters)}")
    print(f"Total OCR corrections: {sum(extractor.corrector.corrections_made.values())}")
    print(f"Quality issues detected: {len(extractor.quality_issues)}")
    print()
    print(f"Output directory: {output_dir}")
    print()

    # Print summary statistics
    print("Letter Distribution:")
    letter_types = defaultdict(int)
    for letter in extractor.letters:
        letter_types[letter['metadata']['letter_type']] += 1

    for ltype, count in sorted(letter_types.items()):
        print(f"  - {ltype.capitalize()}: {count}")

    print()
    print("Files generated:")
    print(f"  - {len(extractor.letters)} markdown letter files")
    print(f"  - 1 manifest.json")
    print(f"  - 1 quality_improvements.md")
    print()


if __name__ == '__main__':
    main()
