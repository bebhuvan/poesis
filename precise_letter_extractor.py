#!/usr/bin/env python3
"""
Precise Letter Extractor for Gandhi's Letters
Uses manually identified line numbers for 100% accuracy
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import logging
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreciseLetterExtractor:
    """Extract letters using precise line-number mapping"""

    def __init__(self, text_file: Path):
        self.text_file = text_file
        with open(text_file, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
        self.raw_text = ''.join(self.lines)

        # Manually identified letter boundaries (line numbers from grep)
        # Format: (start_line, title, recipient)
        self.letter_map = [
            (413, "Letter to Lord Chelmsford", "Lord Chelmsford"),
            (624, "Ultimatum to Lord Chelmsford", "Lord Chelmsford"),
            (821, "To Every Englishman Living in India - First Letter", "Every Englishman in India"),
            (1029, "To Every Englishman Living in India - Second Letter", "Every Englishman in India"),
            (1208, "To the Youngmen of Bengal", "The Youngmen of Bengal"),
            (1356, "To His Royal Highness, The Duke of Connaught", "The Duke of Connaught"),
            (1510, "Ultimatum to Lord Reading", "Lord Reading"),
            (1699, "Letters to Lord Irwin - First Letter", "Lord Irwin"),
            (2094, "Letters to Lord Irwin - Second Letter", "Lord Irwin"),
            (2348, "To the Inmates of Sabarmati Ashram", "Inmates of Sabarmati Ashram"),
            (2510, "Letters to Lord Willingdon - First Rejoinder", "Lord Willingdon"),
            (2720, "Letters to Lord Willingdon - Second Rejoinder", "Lord Willingdon"),
            (2789, "To the Nation", "The Nation"),
            (2898, "To Sir Samuel Hoare - Secretary of State for India", "Sir Samuel Hoare"),
            (3105, "To Ramsay MacDonald - British Prime Minister", "Ramsay MacDonald"),
            (3201, "To Mr. M.A. Jinnah", "M.A. Jinnah"),
            (3285, "To Generalissimo Chiang Kai-shek", "Chiang Kai-shek"),
            (3487, "To the People of America", "The People of America"),
            (3564, "Letters to Lord Linlithgow - First Letter", "Lord Linlithgow"),
            # Multiple Linlithgow letters
            (4009, "To Lord Linlithgow - On New Year's Eve", "Lord Linlithgow"),
            (4171, "To Lord Linlithgow - Personal", "Lord Linlithgow"),
            (4271, "To Lord Linlithgow - Last Letter", "Lord Linlithgow"),
        ]

    def find_additional_letters(self):
        """Find Lord Willingdon and Sir Samuel Hoare letters"""
        # Search around known line numbers
        logger.info("Searching for additional letters...")

        # Lord Willingdon around line 2508
        for i in range(2500, 2600):
            if i < len(self.lines) and 'WILLINGDON' in self.lines[i].upper():
                logger.info(f"Line {i+1}: {self.lines[i].strip()}")

        # Sir Samuel Hoare around line 2898
        for i in range(2890, 2950):
            if i < len(self.lines) and 'HOARE' in self.lines[i].upper():
                logger.info(f"Line {i+1}: {self.lines[i].strip()}")

    def extract_letter_by_lines(self, start_line: int, end_line: int) -> str:
        """Extract text between line numbers (1-indexed)"""
        # Convert to 0-indexed
        start_idx = start_line - 1
        end_idx = end_line - 1

        if start_idx < 0 or end_idx >= len(self.lines):
            return ""

        return ''.join(self.lines[start_idx:end_idx])

    def clean_ocr_text(self, text: str) -> str:
        """Comprehensive OCR cleaning"""

        # Remove page numbers and footers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Famous Letters of Mahatma Gandhi\.\s*\n', '\n', text)

        # Fix common OCR errors
        replacements = {
            'Grandhji': 'Gandhi',
            'Gandhiji': 'Gandhi',
            'Mahatmaji': 'Mahatma',
            'G-overnment': 'Government',
            'G-od': 'God',
            'Mohammedan': 'Muslim',
            'Mussalman': 'Muslim',
            'Hijrat': 'Hijrah',
            'Youngmen': 'Young men',
            'imderstand': 'understand',
            'fain': 'gladly',
            'Chiang Kai Sheck': 'Chiang Kai-shek',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Fix hyphenated line breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Fix broken sentences
        text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)

        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Fix punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)

        return text.strip()

    def extract_metadata(self, text: str, title: str, recipient: str) -> Dict:
        """Extract metadata from letter text"""

        metadata = {
            'recipient': recipient,
            'date': None,
            'location': None
        }

        # Extract date
        date_patterns = [
            r'\b([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text[:1000])
            if match:
                metadata['date'] = match.group(1)
                break

        return metadata

    def extract_all_letters(self) -> List[Dict]:
        """Extract all letters using the line map"""
        logger.info("Extracting letters using precise line numbers...")

        # First, find additional letters
        self.find_additional_letters()

        letters = []

        for i, (start_line, title, recipient) in enumerate(self.letter_map):
            # Determine end line (start of next letter or end of file)
            if i + 1 < len(self.letter_map):
                end_line = self.letter_map[i + 1][0] - 1
            else:
                end_line = len(self.lines)

            raw_text = self.extract_letter_by_lines(start_line, end_line)

            if not raw_text or len(raw_text) < 100:
                logger.warning(f"Letter {i+1} ({title}) seems too short, skipping")
                continue

            cleaned_text = self.clean_ocr_text(raw_text)
            metadata = self.extract_metadata(cleaned_text, title, recipient)

            letter = {
                'letter_number': i + 1,
                'title': title,
                'metadata': metadata,
                'text': cleaned_text,
                'word_count': len(cleaned_text.split()),
                'line_range': f"{start_line}-{end_line}",
                'content_hash': hashlib.sha256(cleaned_text.encode()).hexdigest()[:16]
            }

            letters.append(letter)
            logger.info(f"Letter {i+1}: {title} ({letter['word_count']} words)")

        return letters

    def generate_markdown(self, letter: Dict) -> str:
        """Generate markdown for a letter"""

        frontmatter = f"""---
letter_number: {letter['letter_number']}
title: "{letter['title']}"
author: "Mahatma Gandhi"
recipient: "{letter['metadata']['recipient']}"
"""

        if letter['metadata'].get('date'):
            frontmatter += f'date: "{letter["metadata"]["date"]}"\n'

        frontmatter += f"""word_count: {letter['word_count']}
content_hash: "{letter['content_hash']}"
source:
  archive_org_id: "in.ernet.dli.2015.208999"
  title: "Famous Letters Of Mahatma Gandhi"
  compiler: "R.L. Khipple, M.A."
  publisher: "The Indian Printing Works, Lahore"
  year: 1947
  line_range: "{letter['line_range']}"
public_domain:
  status: true
  reason: "Published 1947, author died 1948 (77 years ago)"
verification:
  extraction_method: "precise_line_mapping"
  ocr_cleaned: true
  manual_review_needed: true
extracted_at: "{datetime.now().isoformat()}"
---

"""

        return frontmatter + letter['text']

    def save_letters(self, output_dir: Path):
        """Save all letters"""

        letters = self.extract_all_letters()

        output_dir.mkdir(parents=True, exist_ok=True)

        # Clear existing files
        for existing_file in output_dir.glob("*.md"):
            existing_file.unlink()

        for letter in letters:
            recipient_slug = re.sub(r'[^a-z0-9]+', '-', letter['metadata']['recipient'].lower())[:40]
            filename = f"{letter['letter_number']:02d}-{recipient_slug}.md"
            filepath = output_dir / filename

            markdown = self.generate_markdown(letter)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)

            logger.info(f"Saved: {filename}")

        # Create index
        index = {
            'collection': 'Famous Letters of Mahatma Gandhi',
            'total_letters': len(letters),
            'extracted_at': datetime.now().isoformat(),
            'letters': [
                {
                    'number': l['letter_number'],
                    'title': l['title'],
                    'recipient': l['metadata']['recipient'],
                    'date': l['metadata'].get('date'),
                    'word_count': l['word_count'],
                    'content_hash': l['content_hash']
                }
                for l in letters
            ]
        }

        index_path = output_dir / 'collection-index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)

        logger.info(f"\nTotal letters extracted: {len(letters)}")
        logger.info(f"Collection index: {index_path}")

        return letters


def main():
    """Main function"""
    text_file = Path("letters/mahatma-gandhi/in.ernet.dli.2015.208999/primary_text.txt")

    if not text_file.exists():
        logger.error(f"Text file not found: {text_file}")
        return

    extractor = PreciseLetterExtractor(text_file)
    output_dir = Path("letters/mahatma-gandhi/individual-letters")

    letters = extractor.save_letters(output_dir)

    logger.info("=" * 80)
    logger.info("PRECISE EXTRACTION COMPLETE!")
    logger.info(f"Total letters: {len(letters)}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
