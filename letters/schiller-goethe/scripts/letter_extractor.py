#!/usr/bin/env python3
"""
Historical Letter Extractor with Multi-Source Verification
Extracts individual letters from OCR text with cross-verification
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
    subject: str
    content: str
    page_start: int
    page_end: int
    sources: Dict[str, str]  # Text from each source
    verification_score: float  # Cross-source agreement
    notes: List[str]


class LetterExtractor:
    """Extract and verify individual letters from multiple OCR sources"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters: List[Letter] = []

        # Load all OCR sources
        self.sources = {}
        self.load_sources()

    def load_sources(self):
        """Load text from all OCR sources"""
        print("Loading OCR sources...")

        # ABBYY
        abbyy_file = self.base_dir / 'raw_ocr/abbyy/abbyy_extracted.txt'
        if abbyy_file.exists():
            self.sources['abbyy'] = abbyy_file.read_text(encoding='utf-8')
            print(f"  ✓ ABBYY: {len(self.sources['abbyy'])} characters")

        # Full text
        full_text_file = self.base_dir / 'raw_ocr/full_text.txt'
        if full_text_file.exists():
            self.sources['full_text'] = full_text_file.read_text(encoding='utf-8')
            print(f"  ✓ Full Text: {len(self.sources['full_text'])} characters")

        # PDF
        pdf_file = self.base_dir / 'raw_ocr/pdf_text/pdf_extracted.txt'
        if pdf_file.exists():
            self.sources['pdf'] = pdf_file.read_text(encoding='utf-8')
            print(f"  ✓ PDF: {len(self.sources['pdf'])} characters")

        print(f"\nLoaded {len(self.sources)} sources for verification\n")

    def extract_letters(self) -> List[Letter]:
        """Extract individual letters from the text"""
        print("Extracting letters...")

        # Use the most complete source for initial extraction
        primary_source = self._get_primary_source()
        text = self.sources[primary_source]

        # Pattern to identify letter boundaries
        # Letters typically start with a Roman numeral (I., II., III., etc.)
        # followed by sender, recipient, location, date
        letter_pattern = r'([IVXLCDM]+\.)\s*'

        # Find the start of actual letters (after preface/intro)
        # Look for "LETTERS" or "I." (first letter)
        start_match = re.search(r'(?:^LETTERS|^I\.)', text, re.MULTILINE)
        if start_match:
            letters_section = text[start_match.start():]
        else:
            letters_section = text

        # Split into potential letter blocks
        # This is a simplified approach - we'll refine based on the actual structure
        blocks = re.split(r'\n\n+', letters_section)

        letter_num = 0
        current_letter_text = []
        in_letter = False

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Check if this starts a new letter
            if re.match(r'^[IVXLCDM]+\.$', block):
                # Save previous letter
                if current_letter_text:
                    letter = self._parse_letter_block('\n\n'.join(current_letter_text), letter_num)
                    if letter:
                        self.letters.append(letter)

                # Start new letter
                letter_num += 1
                current_letter_text = [block]
                in_letter = True
            elif in_letter:
                current_letter_text.append(block)

        # Save last letter
        if current_letter_text:
            letter = self._parse_letter_block('\n\n'.join(current_letter_text), letter_num)
            if letter:
                self.letters.append(letter)

        print(f"Extracted {len(self.letters)} letters\n")
        return self.letters

    def _parse_letter_block(self, text: str, number: int) -> Optional[Letter]:
        """Parse a single letter block"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        if len(lines) < 4:
            return None

        # Try to extract metadata
        # Typical format:
        # I.
        # SCHILLER TO GOETHE
        # Jena, June 13, 1794

        roman_num = lines[0] if re.match(r'^[IVXLCDM]+\.$', lines[0]) else str(number)

        # Find sender/recipient line
        sender, recipient = "Unknown", "Unknown"
        for i, line in enumerate(lines[1:3]):
            if ' TO ' in line.upper():
                parts = line.upper().split(' TO ')
                if len(parts) == 2:
                    sender = parts[0].strip().title()
                    recipient = parts[1].strip().title()
                    break

        # Find date/location line
        date_str = ""
        location = ""
        for line in lines[1:5]:
            # Look for date patterns: "City, Month Day, Year"
            date_match = re.search(r'([A-Z][a-z]+),\s+([A-Z][a-z]+\s+\d+,\s+\d{4})', line)
            if date_match:
                location = date_match.group(1)
                date_str = date_match.group(2)
                break

        # Rest is content
        content_start = 3
        content = '\n\n'.join(lines[content_start:])

        # Cross-verify this letter across sources
        sources_text = {}
        verification_score = 0.0

        for source_name, source_text in self.sources.items():
            # Find similar text in this source
            snippet = content[:200] if len(content) > 200 else content
            match = self._find_similar_text(snippet, source_text)
            if match:
                sources_text[source_name] = match
                verification_score += 1

        verification_score = (verification_score / len(self.sources)) * 100

        return Letter(
            number=number,
            sender=sender,
            recipient=recipient,
            date=date_str,
            location=location,
            subject="",  # Can be extracted later
            content=content,
            page_start=0,  # Will be filled from page markers
            page_end=0,
            sources=sources_text,
            verification_score=verification_score,
            notes=[]
        )

    def _find_similar_text(self, snippet: str, source_text: str, threshold: float = 0.7) -> Optional[str]:
        """Find similar text in another source"""
        # Clean snippet for matching
        clean_snippet = re.sub(r'\s+', ' ', snippet.strip())

        # Try exact match first
        if clean_snippet in source_text:
            return snippet

        # Try fuzzy matching
        words = clean_snippet.split()[:20]  # Use first 20 words
        search_text = ' '.join(words)

        # Search for similar text blocks
        for i in range(0, len(source_text) - len(search_text), 50):
            chunk = source_text[i:i+len(search_text)*2]
            similarity = SequenceMatcher(None, search_text.lower(), chunk.lower()).ratio()
            if similarity > threshold:
                return chunk

        return None

    def _get_primary_source(self) -> str:
        """Determine which source to use as primary"""
        # Prefer full_text as it's usually cleanest
        if 'full_text' in self.sources:
            return 'full_text'
        elif 'abbyy' in self.sources:
            return 'abbyy'
        elif 'pdf' in self.sources:
            return 'pdf'
        return list(self.sources.keys())[0]

    def save_letters(self, output_dir: str):
        """Save individual letters to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Saving {len(self.letters)} letters to {output_dir}...")

        # Save metadata index
        metadata = []

        for letter in self.letters:
            # Create filename
            sender_clean = re.sub(r'[^a-z0-9]+', '_', letter.sender.lower())
            recipient_clean = re.sub(r'[^a-z0-9]+', '_', letter.recipient.lower())
            date_clean = re.sub(r'[^a-z0-9]+', '_', letter.date.lower()) if letter.date else 'undated'

            filename = f"{letter.number:04d}_{sender_clean}_to_{recipient_clean}_{date_clean}.md"

            # Create markdown content
            md_content = self._create_markdown(letter)

            # Save letter file
            (output_path / filename).write_text(md_content, encoding='utf-8')

            # Add to metadata
            metadata.append({
                'number': letter.number,
                'filename': filename,
                'sender': letter.sender,
                'recipient': letter.recipient,
                'date': letter.date,
                'location': letter.location,
                'verification_score': letter.verification_score
            })

        # Save metadata index
        (output_path / 'index.json').write_text(
            json.dumps(metadata, indent=2),
            encoding='utf-8'
        )

        print(f"  ✓ Saved {len(self.letters)} letters")
        print(f"  ✓ Created index.json\n")

    def _create_markdown(self, letter: Letter) -> str:
        """Create markdown-formatted letter"""
        md = []

        # Front matter
        md.append("---")
        md.append(f"number: {letter.number}")
        md.append(f"sender: {letter.sender}")
        md.append(f"recipient: {letter.recipient}")
        md.append(f"date: {letter.date}")
        md.append(f"location: {letter.location}")
        md.append(f"verification_score: {letter.verification_score:.1f}")
        md.append("---")
        md.append("")

        # Header
        md.append(f"# Letter {letter.number}")
        md.append("")
        md.append(f"**From:** {letter.sender}  ")
        md.append(f"**To:** {letter.recipient}  ")
        if letter.date:
            md.append(f"**Date:** {letter.date}  ")
        if letter.location:
            md.append(f"**Location:** {letter.location}  ")
        md.append("")

        # Content
        md.append("---")
        md.append("")
        md.append(letter.content)
        md.append("")

        # Verification note
        if letter.verification_score < 100:
            md.append("---")
            md.append("")
            md.append("*Note: This letter has been verified against multiple OCR sources. "
                     f"Verification score: {letter.verification_score:.1f}%*")

        return '\n'.join(md)

    def create_verification_report(self, output_file: str):
        """Create detailed verification report"""
        report = {
            'extraction_date': datetime.now().isoformat(),
            'sources_used': list(self.sources.keys()),
            'total_letters': len(self.letters),
            'verification_stats': {
                'avg_score': sum(l.verification_score for l in self.letters) / len(self.letters) if self.letters else 0,
                'perfect_matches': len([l for l in self.letters if l.verification_score == 100]),
                'needs_review': len([l for l in self.letters if l.verification_score < 80])
            },
            'letters': [
                {
                    'number': l.number,
                    'sender': l.sender,
                    'recipient': l.recipient,
                    'date': l.date,
                    'verification_score': l.verification_score,
                    'length': len(l.content)
                }
                for l in self.letters
            ]
        }

        Path(output_file).write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f"Saved verification report to: {output_file}\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python letter_extractor.py <base_directory>")
        sys.exit(1)

    base_dir = sys.argv[1]
    extractor = LetterExtractor(base_dir)
    extractor.extract_letters()

    # Save letters
    extractor.save_letters(Path(base_dir) / 'final_letters')

    # Create verification report
    extractor.create_verification_report(Path(base_dir) / 'verification/letter_extraction_report.json')

    print("="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"Total letters extracted: {len(extractor.letters)}")
    if extractor.letters:
        print(f"Average verification score: {sum(l.verification_score for l in extractor.letters) / len(extractor.letters):.1f}%")
