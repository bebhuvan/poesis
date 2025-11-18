#!/usr/bin/env python3
"""
Improved Historical Letter Extractor with Multi-Source Verification
Specifically designed for Schiller-Goethe correspondence format
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from datetime import datetime


@dataclass
class Letter:
    """Individual letter metadata and content"""
    number: int
    sender: str
    recipient: str
    date: str
    location: str
    content: str
    sources: Dict[str, str]  # Text from each source
    verification_score: float  # Cross-source agreement score


class SchillerGoetheExtractor:
    """Extract Schiller-Goethe letters with multi-source verification"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []
        self.sources = {}
        self.load_sources()

    def load_sources(self):
        """Load text from all OCR sources"""
        print("Loading OCR sources...")

        sources_map = {
            'abbyy': 'raw_ocr/abbyy/abbyy_extracted.txt',
            'full_text': 'raw_ocr/full_text.txt',
            'pdf': 'raw_ocr/pdf_text/pdf_extracted.txt'
        }

        for name, path in sources_map.items():
            file_path = self.base_dir / path
            if file_path.exists():
                self.sources[name] = file_path.read_text(encoding='utf-8')
                print(f"  ✓ {name}: {len(self.sources[name]):,} characters")

        print(f"\nLoaded {len(self.sources)} sources\n")

    def extract_letters(self) -> List[Letter]:
        """Extract individual letters"""
        print("Extracting letters from Schiller-Goethe correspondence...")

        # Use full_text as primary (usually cleanest)
        primary_text = self.sources.get('full_text', list(self.sources.values())[0])

        # Find start of letters (after title page and preface)
        # Look for "CORRESPONDENCE\n\nBETWEEN\n\nSCHILLER AND GOETHE"
        start_match = re.search(r'CORRESPONDENCE.*?BETWEEN.*?SCHILLER\s+AND\s+GOETHE',
                               primary_text, re.DOTALL | re.MULTILINE)

        if not start_match:
            print("ERROR: Could not find start of correspondence")
            return []

        letters_text = primary_text[start_match.end():]

        # Split into individual letters
        # Letters are separated by Roman numerals (II., III., IV., etc.)
        # or by signatures (Schiller./Goethe.)
        letter_pattern = r'(?:^([IVXLCDM]+)\.\s*$)'

        # Find all letter boundaries
        letters_raw = []
        current_letter = []
        letter_num = 1  # First letter is unnumbered

        lines = letters_text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if this is a Roman numeral marker
            if re.match(r'^([IVXLCDM]+)\.$', line):
                # Save previous letter
                if current_letter:
                    letter_text = '\n'.join(current_letter)
                    parsed = self._parse_letter(letter_text, letter_num)
                    if parsed:
                        letters_raw.append(parsed)
                        letter_num += 1

                # Start new letter (skip the roman numeral line)
                current_letter = []
                i += 1
                continue

            current_letter.append(lines[i])
            i += 1

        # Save last letter
        if current_letter:
            letter_text = '\n'.join(current_letter)
            parsed = self._parse_letter(letter_text, letter_num)
            if parsed:
                letters_raw.append(parsed)

        # Cross-verify each letter
        print(f"\nCross-verifying {len(letters_raw)} letters...")
        for letter in letters_raw:
            self._verify_letter(letter)
            self.letters.append(letter)

        print(f"✓ Extracted {len(self.letters)} letters\n")
        return self.letters

    def _parse_letter(self, text: str, number: int) -> Optional[Letter]:
        """Parse a single letter"""
        if not text.strip():
            return None

        # Extract signature (last line with a name)
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        if len(lines) < 3:
            return None

        # Find sender (last line is usually the signature)
        sender = "Unknown"
        location = ""
        date_str = ""

        # Check last few lines for signature and date
        for i in range(len(lines)-1, max(len(lines)-5, 0), -1):
            line = lines[i]

            # Check for sender name
            if 'Schiller' in line or 'Goethe' in line:
                sender = "Schiller" if "Schiller" in line else "Goethe"

            # Check for date/location (pattern: "City, Month Day, Year")
            date_match = re.search(r'([A-Z][a-z]+),\s+([A-Z][a-z]+\s+\d+,\s+\d{4})', line)
            if date_match:
                location = date_match.group(1)
                date_str = date_match.group(2)

        # Determine recipient
        recipient = "Goethe" if sender == "Schiller" else "Schiller"

        # Extract content (everything except last 1-3 lines which are signature/date)
        content_lines = lines[:-3] if len(lines) > 3 else lines[:-1]
        content = '\n\n'.join(content_lines)

        # Clean up content
        content = self._clean_text(content)

        return Letter(
            number=number,
            sender=sender,
            recipient=recipient,
            date=date_str,
            location=location,
            content=content,
            sources={},
            verification_score=0.0
        )

    def _verify_letter(self, letter: Letter):
        """Cross-verify letter content across all sources"""
        # Take first 300 characters as fingerprint
        fingerprint = letter.content[:300].strip()
        fingerprint_words = re.sub(r'\s+', ' ', fingerprint).split()[:30]
        search_pattern = ' '.join(fingerprint_words)

        matches = 0
        for source_name, source_text in self.sources.items():
            # Try to find this letter in the source
            match = self._find_in_source(search_pattern, source_text)
            if match:
                letter.sources[source_name] = source_name
                matches += 1

        letter.verification_score = (matches / len(self.sources)) * 100

    def _find_in_source(self, pattern: str, source_text: str) -> bool:
        """Find pattern in source text (fuzzy match)"""
        # Clean pattern and source
        clean_pattern = re.sub(r'[^a-z0-9\s]', '', pattern.lower())
        clean_source = re.sub(r'[^a-z0-9\s]', '', source_text.lower())

        # Try exact match first
        if clean_pattern in clean_source:
            return True

        # Try fuzzy matching on chunks
        pattern_words = clean_pattern.split()[:15]
        search_str = ' '.join(pattern_words)

        return search_str in clean_source

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts and formatting issues"""
        # Fix common OCR errors
        text = text.replace('  ', ' ')  # Double spaces
        text = re.sub(r' +', ' ', text)  # Multiple spaces
        text = re.sub(r'\n\n\n+', '\n\n', text)  # Multiple blank lines

        # Fix hyphenated words at line breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Fix common OCR mistakes
        replacements = {
            ' v^': ' w',
            'v^': 'w',
            ' t ': ' ',
            '  ': ' ',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text.strip()

    def save_letters(self, output_dir: str):
        """Save individual letters to markdown files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Saving {len(self.letters)} letters...")

        metadata = []

        for letter in self.letters:
            # Create filename
            sender_slug = letter.sender.lower().replace(' ', '_')
            date_slug = re.sub(r'[^a-z0-9]', '_', letter.date.lower()) if letter.date else 'undated'
            filename = f"{letter.number:04d}_{sender_slug}_to_{letter.recipient.lower()}_{date_slug}.md"

            # Create markdown
            md_content = self._create_markdown(letter)

            # Save
            (output_path / filename).write_text(md_content, encoding='utf-8')

            # Metadata
            metadata.append({
                'number': letter.number,
                'filename': filename,
                'sender': letter.sender,
                'recipient': letter.recipient,
                'date': letter.date,
                'location': letter.location,
                'verification_score': letter.verification_score,
                'word_count': len(letter.content.split())
            })

        # Save index
        (output_path / 'index.json').write_text(
            json.dumps(metadata, indent=2),
            encoding='utf-8'
        )

        print(f"  ✓ Saved {len(self.letters)} letters")
        print(f"  ✓ Created index.json\n")

    def _create_markdown(self, letter: Letter) -> str:
        """Create markdown-formatted letter"""
        md = []

        # Front matter (YAML)
        md.append("---")
        md.append(f"letter_number: {letter.number}")
        md.append(f"sender: \"{letter.sender}\"")
        md.append(f"recipient: \"{letter.recipient}\"")
        md.append(f"date: \"{letter.date}\"")
        md.append(f"location: \"{letter.location}\"")
        md.append(f"verification_score: {letter.verification_score:.1f}")
        md.append("---")
        md.append("")

        # Header
        md.append(f"# Letter {letter.number}: {letter.sender} to {letter.recipient}")
        md.append("")

        # Metadata
        if letter.date or letter.location:
            md.append("**Metadata:**")
            if letter.location:
                md.append(f"- **Location:** {letter.location}")
            if letter.date:
                md.append(f"- **Date:** {letter.date}")
            md.append("")

        # Content
        md.append("---")
        md.append("")
        md.append(letter.content)
        md.append("")

        # Verification footer
        if letter.verification_score < 100:
            md.append("---")
            md.append("")
            md.append(f"*Verification: This letter has been cross-verified against {len(self.sources)} OCR sources. "
                     f"Match score: {letter.verification_score:.1f}%*")

        return '\n'.join(md)

    def create_report(self, output_file: str):
        """Create extraction and verification report"""
        report = {
            'extraction_date': datetime.now().isoformat(),
            'sources_used': list(self.sources.keys()),
            'total_letters': len(self.letters),
            'statistics': {
                'avg_verification_score': sum(l.verification_score for l in self.letters) / len(self.letters) if self.letters else 0,
                'perfect_matches': len([l for l in self.letters if l.verification_score == 100]),
                'needs_review': len([l for l in self.letters if l.verification_score < 80]),
                'by_sender': {
                    'Schiller': len([l for l in self.letters if l.sender == 'Schiller']),
                    'Goethe': len([l for l in self.letters if l.sender == 'Goethe'])
                }
            },
            'letters': [
                {
                    'number': l.number,
                    'sender': l.sender,
                    'recipient': l.recipient,
                    'date': l.date,
                    'location': l.location,
                    'verification_score': l.verification_score,
                    'word_count': len(l.content.split())
                }
                for l in self.letters
            ]
        }

        Path(output_file).write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f"✓ Saved extraction report\n")


if __name__ == '__main__':
    import sys

    base_dir = sys.argv[1] if len(sys.argv) > 1 else '/home/user/poesis/letters/schiller-goethe'

    extractor = SchillerGoetheExtractor(base_dir)
    extractor.extract_letters()

    # Save letters
    output_dir = Path(base_dir) / 'final_letters'
    extractor.save_letters(output_dir)

    # Create report
    verification_dir = Path(base_dir) / 'verification'
    verification_dir.mkdir(exist_ok=True)
    extractor.create_report(verification_dir / 'extraction_report.json')

    print("="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"Total letters: {len(extractor.letters)}")
    if extractor.letters:
        avg_score = sum(l.verification_score for l in extractor.letters) / len(extractor.letters)
        print(f"Average verification: {avg_score:.1f}%")
        print(f"Letters by Schiller: {len([l for l in extractor.letters if l.sender == 'Schiller'])}")
        print(f"Letters by Goethe: {len([l for l in extractor.letters if l.sender == 'Goethe'])}")
