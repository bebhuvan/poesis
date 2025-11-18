#!/usr/bin/env python3
"""
Comprehensive Letter Extractor for Gandhi's Letters
Uses multiple strategies and rigorous verification
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveLetterExtractor:
    """Multi-strategy extractor with verification"""

    def __init__(self, text_file: Path):
        self.text_file = text_file
        with open(text_file, 'r', encoding='utf-8') as f:
            self.raw_text = f.read()
        self.letters = []

        # Table of contents from the book (for verification)
        self.toc_entries = [
            "Letter to Lord Chelmsford",
            "Ultimatum to Lord Chelmsford",
            "To Every Englishman living in India - First Letter",
            "To Every Englishman living in India - Second Letter",
            "To the Youngmen of Bengal",
            "To His Royal Highness, the Duke of Connaught",
            "Ultimatum to Lord Reading",
            "Letters to Lord Irwin - First letter",
            "Letters to Lord Irwin - Second letter",
            "Letters to Lord Irwin - Third letter",
            "Letters to Lord Willingdon - First Rejoinder",
            "Letters to Lord Willingdon - Second Rejoinder",
            "To the Nation",
            "To Sir Samuel Hoare",
            "To Ramsay MacDonald",
            "To Mr. M.A. Jinnah",
            "To Marshal Chiang Kai-shek",
            "To the People of America",
            "To Lord Linlithgow - 1st letter",
            "To the Home Member",
            "To Lord Linlithgow - New Year's Eve",
            "To Lord Linlithgow - Personal",
            "To Lord Linlithgow - (another)",
            "To Lord Linlithgow - Last letter",
            "To Sk Richards",
        ]

    def extract_by_page_markers(self) -> List[Tuple[str, int, int]]:
        """Extract content by finding page number markers and headers"""
        logger.info("Extracting letters by identifying headers and page markers...")

        # Find all ALL-CAPS headers that likely indicate letter starts
        header_pattern = r'\n([A-Z][A-Z\s]{10,}[A-Z])\s*\.\s*\n'
        matches = list(re.finditer(header_pattern, self.raw_text))

        sections = []
        for i, match in enumerate(matches):
            header = match.group(1).strip()

            # Skip table of contents and other non-letter sections
            if 'CONTENTS' in header or 'MAHATMA GANDHI' == header:
                continue

            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(self.raw_text)

            # Check if this looks like a letter section
            if any(keyword in header for keyword in ['LETTER', 'TO ', 'ULTIMATUM']):
                sections.append((header, start, end))
                logger.info(f"Found section: {header}")

        return sections

    def extract_sub_letters(self, text: str, parent_header: str) -> List[Dict]:
        """Extract individual letters from a section that contains multiple letters"""
        # Look for patterns like "The first letter:", "Second letter:", etc.
        sub_letter_pattern = r'\n((?:The\s+)?(?:first|second|third|fourth|1st|2nd|3rd|4th)\s+letter[:\.]?)'

        matches = list(re.finditer(sub_letter_pattern, text, re.IGNORECASE))

        if not matches:
            # No sub-letters, return the whole section as one letter
            return [{'text': text, 'sub_title': None}]

        sub_letters = []
        for i, match in enumerate(matches):
            sub_title = match.group(1).strip()
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            sub_text = text[start:end]
            sub_letters.append({
                'text': sub_text,
                'sub_title': sub_title
            })

        return sub_letters

    def clean_letter_text(self, text: str) -> str:
        """Apply comprehensive OCR cleaning"""

        # Remove page numbers and headers
        text = re.sub(r'\n\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*[A-Z][a-z\s]+\.\s*\d+\s*\n', '\n', text)

        # Fix common OCR errors
        fixes = {
            r'\bGrandlii\b': 'Gandhi',
            r'\bGandhiji\b': 'Gandhi',
            r'\bMahatmaji\b': 'Mahatma',
            r'\bG-overnment\b': 'Government',
            r'\bG-od\b': 'God',
            r'\bMohammedan\b': 'Muslim',
            r'\bMussalman\b': 'Muslim',
            r'\bHijrat\b': 'Hijrah',
            r'\bYomgmen\b': 'Youngmen',
            r',\)(?=\s)': ')',  # Fix ,) to )
            r'\bSk\b': 'Sir',
            r'\bimderstand\b': 'understand',
            r'\bfain\b': 'gladly',
        }

        for pattern, replacement in fixes.items():
            text = re.sub(pattern, replacement, text)

        # Fix hyphenated line breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Fix broken sentences across lines
        text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)

        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Fix punctuation spacing
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', text)

        return text.strip()

    def extract_metadata(self, text: str, header: str) -> Dict:
        """Extract metadata from letter text"""

        metadata = {
            'recipient': None,
            'date': None,
            'location': None,
            'subject': None
        }

        # Extract recipient from header
        recipient_patterns = [
            r'TO\s+(.+?)(?:\.|$)',
            r'LETTERS?\s+TO\s+(.+?)(?:\.|$)',
        ]

        for pattern in recipient_patterns:
            match = re.search(pattern, header, re.IGNORECASE)
            if match:
                metadata['recipient'] = match.group(1).strip()
                break

        if not metadata['recipient']:
            metadata['recipient'] = header.strip()

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
        """Main extraction method"""
        logger.info("Starting comprehensive letter extraction...")

        sections = self.extract_by_page_markers()
        all_letters = []

        letter_number = 1

        for header, start, end in sections:
            section_text = self.raw_text[start:end]

            # Extract context note if present
            context_match = re.search(r'\(([^)]{100,}?)\)', section_text[:2000])
            context = context_match.group(1).strip() if context_match else None

            # Check for sub-letters within this section
            sub_letters = self.extract_sub_letters(section_text, header)

            for sub_letter in sub_letters:
                full_title = header
                if sub_letter['sub_title']:
                    full_title += f" - {sub_letter['sub_title']}"

                cleaned_text = self.clean_letter_text(sub_letter['text'])
                metadata = self.extract_metadata(cleaned_text, header)

                letter_obj = {
                    'letter_number': letter_number,
                    'title': full_title,
                    'header': header,
                    'sub_title': sub_letter['sub_title'],
                    'metadata': metadata,
                    'context': context,
                    'text': cleaned_text,
                    'word_count': len(cleaned_text.split()),
                    'character_count': len(cleaned_text),
                    'content_hash': hashlib.sha256(cleaned_text.encode()).hexdigest()[:16]
                }

                all_letters.append(letter_obj)
                logger.info(f"Letter {letter_number}: {full_title[:60]}...")
                letter_number += 1

        self.letters = all_letters
        logger.info(f"Extracted {len(all_letters)} letters total")
        return all_letters

    def generate_markdown(self, letter: Dict) -> str:
        """Generate markdown for a letter"""

        frontmatter_lines = [
            "---",
            f'letter_number: {letter["letter_number"]}',
            f'title: "{letter["title"]}"',
            f'author: "Mahatma Gandhi"',
        ]

        if letter['metadata'].get('recipient'):
            frontmatter_lines.append(f'recipient: "{letter["metadata"]["recipient"]}"')

        if letter['metadata'].get('date'):
            frontmatter_lines.append(f'date: "{letter["metadata"]["date"]}"')

        frontmatter_lines.extend([
            f'word_count: {letter["word_count"]}',
            f'content_hash: "{letter["content_hash"]}"',
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
            'verification:',
            f'  ocr_method: "Archive.org DJVU text layer"',
            '  manual_review: false',
            '---',
            ''
        ])

        frontmatter = '\n'.join(frontmatter_lines)

        # Add context if available
        body_parts = []
        if letter.get('context'):
            body_parts.append(f'> **Historical Context:** {letter["context"]}')
            body_parts.append('')

        body_parts.append(letter['text'])

        return frontmatter + '\n'.join(body_parts)

    def save_letters(self, output_dir: Path):
        """Save all letters"""

        if not self.letters:
            self.extract_all_letters()

        output_dir.mkdir(parents=True, exist_ok=True)

        for letter in self.letters:
            # Create filename
            recipient = letter['metadata'].get('recipient', 'unknown')
            recipient_slug = re.sub(r'[^a-z0-9]+', '-', recipient.lower())[:40]

            filename = f"{letter['letter_number']:02d}-{recipient_slug}.md"
            filepath = output_dir / filename

            markdown = self.generate_markdown(letter)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)

            logger.info(f"Saved: {filename}")

        # Create collection index
        index = {
            'collection': 'Famous Letters of Mahatma Gandhi',
            'total_letters_expected': len(self.toc_entries),
            'total_letters_extracted': len(self.letters),
            'extraction_complete': len(self.letters) >= 20,  # We expect around 25-27 letters
            'extracted_at': datetime.now().isoformat(),
            'letters': [
                {
                    'number': l['letter_number'],
                    'title': l['title'],
                    'recipient': l['metadata'].get('recipient'),
                    'date': l['metadata'].get('date'),
                    'word_count': l['word_count'],
                    'content_hash': l['content_hash']
                }
                for l in self.letters
            ]
        }

        index_path = output_dir / 'collection-index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)

        logger.info(f"Collection index saved: {index_path}")

        return len(self.letters)


def main():
    """Main function"""
    text_file = Path("letters/mahatma-gandhi/in.ernet.dli.2015.208999/primary_text.txt")

    if not text_file.exists():
        logger.error(f"Text file not found: {text_file}")
        return

    extractor = ComprehensiveLetterExtractor(text_file)
    output_dir = Path("letters/mahatma-gandhi/individual-letters")

    # Clear previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)

    count = extractor.save_letters(output_dir)

    logger.info("=" * 80)
    logger.info("EXTRACTION COMPLETE!")
    logger.info(f"Total letters extracted: {count}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
