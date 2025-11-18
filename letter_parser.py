#!/usr/bin/env python3
"""
Letter Parser and Cleaner
Parses individual letters from bulk text and cleans OCR errors
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LetterParser:
    """Parse and clean individual letters from bulk extracted text"""

    def __init__(self, text: str, collection_name: str):
        self.raw_text = text
        self.collection_name = collection_name
        self.letters = []

    def identify_letter_boundaries(self) -> List[Dict]:
        """
        Identify individual letter boundaries in the text.
        Letters typically have:
        - A number or Roman numeral
        - Date
        - Salutation (Dear/My Dear/Respected...)
        - Body
        - Signature
        """
        logger.info("Identifying letter boundaries...")

        # Common patterns that indicate a new letter
        patterns = [
            # Letter numbers
            r'\n\s*(?:LETTER\s+)?(?:No\.|NUMBER|#)?\s*(\d+|[IVXLCDM]+)\s*\n',
            r'\n\s*(\d+)\.\s+TO\s+',
            r'\n\s*(\d+)\.\s+[A-Z]',
            # Dates at start
            r'\n\s*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
            # TO: patterns
            r'\n\s*TO[:]\s*([A-Z][A-Z\s\.]+)',
        ]

        # Find all potential boundaries
        boundaries = []
        for pattern in patterns:
            for match in re.finditer(pattern, self.raw_text):
                boundaries.append({
                    'position': match.start(),
                    'text': match.group(0),
                    'type': 'boundary'
                })

        # Sort by position
        boundaries.sort(key=lambda x: x['position'])

        logger.info(f"Found {len(boundaries)} potential letter boundaries")
        return boundaries

    def extract_letter_metadata(self, letter_text: str) -> Dict:
        """Extract metadata from a single letter"""
        metadata = {
            'date': None,
            'recipient': None,
            'location': None,
            'subject': None,
            'letter_number': None
        }

        # Extract letter number
        number_match = re.search(r'(?:LETTER\s+)?(?:No\.|NUMBER)?\s*(\d+|[IVXLCDM]+)', letter_text[:200])
        if number_match:
            metadata['letter_number'] = number_match.group(1)

        # Extract date (various formats)
        date_patterns = [
            r'([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',  # January 1, 1930
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',     # 1/1/1930
            r'([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',  # January 1st, 1930
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, letter_text[:500])
            if date_match:
                metadata['date'] = date_match.group(1)
                break

        # Extract recipient (TO: pattern)
        recipient_match = re.search(r'TO[:]\s*([A-Z][^\n]+)', letter_text[:300])
        if recipient_match:
            metadata['recipient'] = recipient_match.group(1).strip()

        # Extract location
        location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s*\n', letter_text[:300])
        if location_match:
            metadata['location'] = location_match.group(1)

        return metadata

    def clean_ocr_errors(self, text: str) -> str:
        """Clean common OCR errors"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Fix common OCR substitutions
        ocr_fixes = {
            r'\bGod\s+win\b': 'Godwin',
            r'\bGandlu\b': 'Gandhi',
            r'\bl\b': 'I',  # lowercase L mistaken for I
            r'\brn\b': 'm',
            r'(?<=[a-z])1(?=[a-z])': 'l',  # 1 for l in middle of words
            r'(?<=[a-z])0(?=[a-z])': 'o',  # 0 for o in middle of words
        }

        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', text)

        # Fix line breaks in middle of sentences
        text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)

        return text

    def split_into_letters(self) -> List[Dict]:
        """Split the raw text into individual letters"""
        logger.info("Splitting text into individual letters...")

        # Strategy: Look for clear letter markers
        # Pattern for Gandhi's letters: Usually "LETTER No. X" or numbered entries

        # Try to find letters using various patterns
        letter_pattern = r'(?:^|\n)(?:LETTER\s+)?(?:No\.|NUMBER)?\s*(\d+|[IVXLCDM]+)\.?\s*\n'

        splits = list(re.finditer(letter_pattern, self.raw_text, re.MULTILINE))

        if not splits:
            logger.warning("Could not find letter markers, attempting alternative split...")
            # Try splitting by "TO:" pattern
            splits = list(re.finditer(r'\n\s*TO[:]\s*[A-Z]', self.raw_text))

        if not splits:
            logger.error("Could not identify letter boundaries")
            return []

        letters = []
        for i, match in enumerate(splits):
            start = match.start()
            end = splits[i + 1].start() if i + 1 < len(splits) else len(self.raw_text)

            letter_text = self.raw_text[start:end].strip()

            if len(letter_text) > 50:  # Minimum length to be a valid letter
                metadata = self.extract_letter_metadata(letter_text)
                cleaned_text = self.clean_ocr_errors(letter_text)

                letters.append({
                    'metadata': metadata,
                    'raw_text': letter_text,
                    'cleaned_text': cleaned_text,
                    'word_count': len(cleaned_text.split()),
                    'extracted_at': datetime.now().isoformat()
                })

        logger.info(f"Extracted {len(letters)} letters")
        return letters

    def generate_markdown(self, letter: Dict, index: int) -> str:
        """Generate markdown for a single letter"""
        metadata = letter['metadata']

        # Create frontmatter
        frontmatter = f"""---
collection: "{self.collection_name}"
letter_number: {metadata.get('letter_number') or index}
"""

        if metadata.get('date'):
            frontmatter += f'date: "{metadata["date"]}"\n'
        if metadata.get('recipient'):
            frontmatter += f'recipient: "{metadata["recipient"]}"\n'
        if metadata.get('location'):
            frontmatter += f'location: "{metadata["location"]}"\n'

        frontmatter += f"""word_count: {letter['word_count']}
extracted_at: "{letter['extracted_at']}"
source:
  archive_org: "in.ernet.dli.2015.208999"
  title: "Famous Letters Of Mahatma Gandhi"
  compiler: "Khipple R.L."
  year: 1947
  publisher: "The Indian Printing Works, Lahore"
public_domain:
  status: true
  reason: "Published 1947, author died 1948 (77 years ago)"
---

"""

        # Add the letter text
        markdown = frontmatter + letter['cleaned_text']

        return markdown

    def save_letters(self, output_dir: Path):
        """Save each letter as a separate markdown file"""
        letters = self.split_into_letters()

        output_dir.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        for i, letter in enumerate(letters, 1):
            # Create filename
            letter_num = letter['metadata'].get('letter_number', i)
            recipient = letter['metadata'].get('recipient', 'unknown')
            recipient_slug = re.sub(r'[^a-z0-9]+', '-', recipient.lower()[:30])

            filename = f"letter-{letter_num:03d}-{recipient_slug}.md"
            filepath = output_dir / filename

            # Generate markdown
            markdown = self.generate_markdown(letter, i)

            # Save
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)

            logger.info(f"Saved: {filepath}")
            saved_count += 1

        logger.info(f"Saved {saved_count} letters to {output_dir}")

        # Save summary
        summary = {
            'total_letters': len(letters),
            'collection': self.collection_name,
            'processed_at': datetime.now().isoformat(),
            'letters': [
                {
                    'number': l['metadata'].get('letter_number'),
                    'recipient': l['metadata'].get('recipient'),
                    'date': l['metadata'].get('date'),
                    'word_count': l['word_count']
                }
                for l in letters
            ]
        }

        summary_path = output_dir / '_collection_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Saved summary to {summary_path}")

        return letters


def main():
    """Main parsing function"""
    # Read the primary text
    primary_text_path = Path("letters/mahatma-gandhi/in.ernet.dli.2015.208999/primary_text.txt")

    if not primary_text_path.exists():
        logger.error(f"Primary text not found at {primary_text_path}")
        logger.info("Please run archive_org_extractor.py first")
        return

    with open(primary_text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    logger.info(f"Loaded {len(text)} characters from {primary_text_path}")

    # Parse letters
    parser = LetterParser(text, "Mahatma Gandhi Letters")
    output_dir = Path("letters/mahatma-gandhi/individual-letters")
    letters = parser.save_letters(output_dir)

    logger.info("=" * 80)
    logger.info("PARSING COMPLETE")
    logger.info(f"Total letters extracted: {len(letters)}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
