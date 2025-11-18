#!/usr/bin/env python3
"""
Specialized Parser for Gandhi's Letters
Handles the specific format of "Famous Letters of Mahatma Gandhi"
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


class GandhiLetterParser:
    """Parse Gandhi's letters from the Khipple compilation"""

    def __init__(self, text_file: Path):
        self.text_file = text_file
        with open(text_file, 'r', encoding='utf-8') as f:
            self.raw_text = f.read()
        self.letters = []

    def clean_ocr_text(self, text: str) -> str:
        """Clean OCR errors specific to this document"""

        # Common OCR errors in this document
        text = re.sub(r'\bGrandlii\b', 'Gandhi', text)
        text = re.sub(r'\bGandhiji?\b', 'Gandhi', text)  # Normalize Gandhiji to Gandhi
        text = re.sub(r'\bMahatmaji\b', 'Mahatma', text)
        text = re.sub(r'\bG-overnment\b', 'Government', text)
        text = re.sub(r'\bGod\s+win\b', 'Godwin', text)
        text = re.sub(r'\bMohammedan\b', 'Muslim', text)  # Modernize terminology

        # Fix hyphenated line breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Fix excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', text)

        # Fix broken sentences across lines
        text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)

        return text

    def extract_letters(self) -> List[Dict]:
        """Extract individual letters from the collection"""
        logger.info("Extracting letters from Gandhi collection...")

        # Find all letter boundaries - they start with "LETTER" or "LETTERS"
        letter_pattern = r'\n(LETTERS?\s+(?:TO|WRITTEN BY)[^\n]+)'

        matches = list(re.finditer(letter_pattern, self.raw_text, re.MULTILINE))
        logger.info(f"Found {len(matches)} letter sections")

        letters = []

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(self.raw_text)

            letter_section = self.raw_text[start:end]

            # Parse this letter section
            parsed = self.parse_letter_section(letter_section, i + 1)
            if parsed:
                letters.append(parsed)

        logger.info(f"Successfully parsed {len(letters)} letters")
        self.letters = letters
        return letters

    def parse_letter_section(self, text: str, section_num: int) -> Optional[Dict]:
        """Parse a single letter section"""

        # Extract the title (first line)
        title_match = re.match(r'^\s*(LETTERS?\s+[^\n]+)', text)
        if not title_match:
            return None

        title = title_match.group(1).strip()

        # Extract context note (text in parentheses at the start)
        context_match = re.search(r'\(([^)]{50,})\)', text[:1500])
        context = context_match.group(1).strip() if context_match else None

        # Extract recipient from title
        recipient_match = re.search(r'LETTERS?\s+(?:TO|WRITTEN BY)\s+(.+)', title)
        recipient = recipient_match.group(1).strip() if recipient_match else "Unknown"

        # Clean the recipient name
        recipient = re.sub(r'[.\s]+$', '', recipient)

        # Try to find date patterns in the letter
        date_patterns = [
            r'\b([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
        ]

        date = None
        for pattern in date_patterns:
            date_match = re.search(pattern, text[:2000])
            if date_match:
                date = date_match.group(1)
                break

        # Clean the text
        cleaned_text = self.clean_ocr_text(text)

        # Count words (excluding the header/context)
        body_start = context_match.end() if context_match else title_match.end()
        body_text = text[body_start:]
        word_count = len(body_text.split())

        return {
            'section_number': section_num,
            'title': title,
            'recipient': recipient,
            'date': date,
            'context': context,
            'full_text': cleaned_text,
            'word_count': word_count,
            'character_count': len(cleaned_text)
        }

    def generate_markdown(self, letter: Dict) -> str:
        """Generate clean markdown for a letter"""

        # Build frontmatter
        frontmatter_parts = [
            "---",
            f'title: "{letter["title"]}"',
            f'author: "Mahatma Gandhi"',
            f'recipient: "{letter["recipient"]}"',
        ]

        if letter.get('date'):
            frontmatter_parts.append(f'date: "{letter["date"]}"')

        frontmatter_parts.extend([
            f'word_count: {letter["word_count"]}',
            f'section_number: {letter["section_number"]}',
            'source:',
            '  archive_org_id: "in.ernet.dli.2015.208999"',
            '  title: "Famous Letters Of Mahatma Gandhi"',
            '  compiler: "R.L. Khipple, M.A."',
            '  publisher: "The Indian Printing Works, Lahore"',
            '  year: 1947',
            'public_domain:',
            '  status: true',
            '  reason: "Published 1947, author died 1948 (77 years ago)"',
            f'extracted_at: "{datetime.now().isoformat()}"',
            '---',
            ''
        ])

        frontmatter = '\n'.join(frontmatter_parts)

        # Add context note if available
        body_parts = []

        if letter.get('context'):
            body_parts.append(f"> **Historical Context:** {letter['context']}")
            body_parts.append("")

        # Add the letter text
        body_parts.append(letter['full_text'])

        return frontmatter + '\n'.join(body_parts)

    def save_letters(self, output_dir: Path):
        """Save letters as markdown files"""

        if not self.letters:
            self.extract_letters()

        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []

        for letter in self.letters:
            # Create filename
            recipient_slug = re.sub(r'[^a-z0-9]+', '-', letter['recipient'].lower())
            recipient_slug = recipient_slug[:50]  # Limit length
            filename = f"{letter['section_number']:02d}-{recipient_slug}.md"

            filepath = output_dir / filename

            # Generate and save markdown
            markdown = self.generate_markdown(letter)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)

            logger.info(f"Saved: {filename}")
            saved_files.append(str(filepath))

        # Create collection index
        index = {
            'collection': 'Famous Letters of Mahatma Gandhi',
            'compiler': 'R.L. Khipple, M.A.',
            'published': 1947,
            'total_letters': len(self.letters),
            'extracted_at': datetime.now().isoformat(),
            'letters': [
                {
                    'section': l['section_number'],
                    'recipient': l['recipient'],
                    'date': l.get('date'),
                    'title': l['title'],
                    'word_count': l['word_count']
                }
                for l in self.letters
            ]
        }

        index_path = output_dir / 'collection-index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)

        logger.info(f"\nSaved {len(saved_files)} letters to {output_dir}")
        logger.info(f"Collection index: {index_path}")

        return saved_files


def main():
    """Main function"""
    text_file = Path("letters/mahatma-gandhi/in.ernet.dli.2015.208999/primary_text.txt")

    if not text_file.exists():
        logger.error(f"Text file not found: {text_file}")
        logger.error("Please run archive_org_extractor.py first")
        return

    parser = GandhiLetterParser(text_file)
    output_dir = Path("letters/mahatma-gandhi/individual-letters")

    saved_files = parser.save_letters(output_dir)

    logger.info("=" * 80)
    logger.info("EXTRACTION COMPLETE!")
    logger.info(f"Total letters: {len(saved_files)}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
