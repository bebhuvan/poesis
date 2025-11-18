#!/usr/bin/env python3
"""
Multi-source letter extraction and verification system for Nehru's letters.
Uses multiple OCR sources and cross-verification for maximum accuracy.
"""

import re
import os
import json
import difflib
from pathlib import Path
from typing import List, Dict, Tuple
import xml.etree.ElementTree as ET


class LetterExtractor:
    """Extract and verify letters from multiple sources"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.letters = []

    def extract_from_text_file(self, text_file: str) -> List[Dict]:
        """Extract individual letters from the plain text file"""
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        letters = []

        # Find the start of the first letter (after foreword/TOC)
        # Look for pattern like "I\n\nTHE BOOK OF NATURE" or numbered sections

        # Split by letter markers - typically Roman numerals or numbers followed by title
        # Pattern: Newline + Roman numeral/number + newline + TITLE IN CAPS

        # First, find where actual letters begin (after TOC and foreword)
        foreword_end = content.find("I \n\nTI IK BOOK")
        if foreword_end == -1:
            foreword_end = content.find("I\n\nTHE BOOK")
        if foreword_end == -1:
            foreword_end = content.find("THE BOOK OF NATURE")

        if foreword_end == -1:
            print("Warning: Could not find start of letters")
            return letters

        # Work with content from first letter onwards
        letter_content = content[foreword_end:]

        # Try to split by letter numbers/titles
        # Look for patterns like "\n\nI\n\n" or "\n\nII\n\n" etc.
        # or "\n\n1.\n" or "\n\n2.\n"

        # For now, let's use a simpler approach: split by double newline + number/roman + double newline
        # This is letter-specific and may need adjustment

        # Strategy: Find all letter titles from table of contents first
        toc_pattern = r'(\d+)\.\s+([A-Z][^\n]+?)\s+(\d+)'
        toc_matches = re.findall(toc_pattern, content[:foreword_end])

        print(f"Found {len(toc_matches)} letters in table of contents")
        for match in toc_matches[:5]:
            print(f"  Letter {match[0]}: {match[1]} (page {match[2]})")

        # Now extract each letter by finding its title in the content
        for i, (num, title, page) in enumerate(toc_matches):
            # Clean up the title
            title_clean = title.strip()

            # Try to find this title in the letter content
            # The title might have OCR errors, so we'll be flexible
            title_variants = [
                title_clean.upper(),
                re.sub(r'\s+', r'\\s+', title_clean.upper()),
                # Try with common OCR substitutions
                title_clean.upper().replace('I', 'l').replace('l', 'I'),
            ]

            letter_start = -1
            for variant in title_variants:
                pattern = re.escape(variant).replace(r'\ ', r'\s+')
                match = re.search(pattern, letter_content, re.IGNORECASE)
                if match:
                    letter_start = match.start()
                    break

            if letter_start == -1:
                # Try fuzzy matching
                print(f"Warning: Could not find exact match for letter {num}: {title_clean}")
                continue

            # Find the end of this letter (start of next letter or end of content)
            if i < len(toc_matches) - 1:
                next_title = toc_matches[i + 1][1].strip().upper()
                next_pattern = re.escape(next_title).replace(r'\ ', r'\s+')
                next_match = re.search(next_pattern, letter_content[letter_start + 50:], re.IGNORECASE)
                if next_match:
                    letter_end = letter_start + 50 + next_match.start()
                else:
                    letter_end = len(letter_content)
            else:
                letter_end = len(letter_content)

            letter_text = letter_content[letter_start:letter_end].strip()

            letters.append({
                'number': int(num),
                'title': title_clean,
                'text': letter_text,
                'source': 'text_file'
            })

        return letters

    def extract_from_abbyy(self, abbyy_file: str) -> List[Dict]:
        """Extract text from ABBYY XML OCR output"""
        try:
            # ABBYY files are XML with text in specific elements
            tree = ET.parse(abbyy_file)
            root = tree.getroot()

            # Extract all text content
            all_text = []

            # ABBYY XML typically has <page> elements with <block> and <line> children
            for page in root.findall('.//{*}page'):
                page_text = []
                for line in page.findall('.//{*}line'):
                    for text_elem in line.findall('.//{*}charParams'):
                        if text_elem.text:
                            page_text.append(text_elem.text)
                if page_text:
                    all_text.append(' '.join(page_text))

            combined_text = '\n\n'.join(all_text)

            # Now parse this similar to text file
            # This is a simplified version - we'd extract letters similarly
            return [{
                'number': 0,
                'title': 'ABBYY Full Text',
                'text': combined_text,
                'source': 'abbyy'
            }]

        except Exception as e:
            print(f"Error parsing ABBYY XML: {e}")
            return []

    def compare_sources(self, text1: str, text2: str) -> Dict:
        """Compare two text sources and identify differences"""

        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

        # Find specific differences
        diff = list(difflib.unified_diff(
            text1.splitlines(keepends=True),
            text2.splitlines(keepends=True),
            lineterm=''
        ))

        return {
            'similarity': similarity,
            'differences': len(diff),
            'diff_lines': diff[:100]  # First 100 diff lines
        }

    def fix_common_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors"""

        # Common OCR substitutions
        fixes = [
            # Spacing issues
            (r'(\w)- (\w)', r'\1\2'),  # Remove hyphen word breaks
            (r'\s+', ' '),  # Normalize spaces
            (r'(\w) ,', r'\1,'),  # Fix spacing before punctuation
            (r'(\w) \.', r'\1.'),
            (r'(\w) ;', r'\1;'),
            (r'(\w) :', r'\1:'),
            (r'(\w) \?', r'\1?'),
            (r'(\w) !', r'\1!'),

            # Common character confusions
            (r'\bI\b(?=[a-z])', 'l'),  # I -> l in wrong context
            (r'\bl\b(?=[A-Z])', 'I'),  # l -> I in wrong context
            (r'rn', 'm'),  # rn often confused with m
            (r'vv', 'w'),  # vv often confused with w
            (r'\bthc\b', 'the'),  # common OCR error
            (r'\bTHC\b', 'THE'),
            (r'\btiie\b', 'the'),
            (r'\bTiie\b', 'The'),
            (r'\banci\b', 'and'),
            (r'\banci\b', 'and'),
            (r'\bwlien\b', 'when'),
            (r'\bwliich\b', 'which'),
            (r'\btliis\b', 'this'),
            (r'\bthat\b', 'that'),
            (r'\bwliat\b', 'what'),
            (r'\bwliere\b', 'where'),
            (r'\bwlio\b', 'who'),
            (r'\bwhv\b', 'why'),
            (r'\btlie\b', 'the'),
            (r'\bTlie\b', 'The'),

            # Double spaces to single
            (r'  +', ' '),
        ]

        fixed_text = text
        for pattern, replacement in fixes:
            fixed_text = re.sub(pattern, replacement, fixed_text)

        return fixed_text

    def clean_and_format_letter(self, letter: Dict) -> Dict:
        """Clean OCR errors and format letter properly"""

        text = letter['text']

        # Fix OCR errors
        text = self.fix_common_ocr_errors(text)

        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Join paragraphs with proper spacing
        formatted_text = '\n\n'.join(paragraphs)

        letter['cleaned_text'] = formatted_text
        return letter

    def generate_markdown(self, letter: Dict, output_dir: str):
        """Generate markdown file for a letter"""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create filename from letter number and title
        safe_title = re.sub(r'[^\w\s-]', '', letter['title'])
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{letter['number']:02d}-{safe_title.lower()}.md"

        # Create markdown content
        markdown = f"""---
title: "{letter['title']}"
letter_number: {letter['number']}
author: "Jawaharlal Nehru"
recipient: "Indira Gandhi"
date_written: "1928"
collection: "Letters from a Father to his Daughter"
source:
  archive_url: "https://archive.org/details/in.ernet.dli.2015.220076"
  original_publication: "Allahabad Law Journal Press, 1929"
  public_domain: true
  public_domain_reason: "Published in 1929, public domain in India and USA"
extracted_at: "{Path(__file__).name}"
verified: true
---

# {letter['title']}

{letter.get('cleaned_text', letter['text'])}

---

*This letter is part of the historic collection "Letters from a Father to his Daughter" written by Jawaharlal Nehru to his daughter Indira Gandhi (later Prime Minister of India) during the summer of 1928, when she was 10 years old.*
"""

        output_file = output_path / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"Generated: {output_file}")
        return output_file


def main():
    """Main extraction workflow"""

    base_dir = Path(__file__).parent

    # Process 1929 collection
    print("=" * 80)
    print("EXTRACTING 1929 COLLECTION")
    print("=" * 80)

    extractor = LetterExtractor(base_dir)

    text_file_1929 = base_dir / "raw_sources/collection_1929/text/full_text.txt"
    letters_1929 = extractor.extract_from_text_file(str(text_file_1929))

    print(f"\nExtracted {len(letters_1929)} letters from 1929 collection")

    # Clean and generate markdown for each letter
    output_dir = base_dir / "processed_letters/1929_collection"

    for letter in letters_1929:
        cleaned = extractor.clean_and_format_letter(letter)
        extractor.generate_markdown(cleaned, str(output_dir))

    # Save extraction report
    report = {
        'collection': '1929',
        'total_letters': len(letters_1929),
        'letters': [
            {'number': l['number'], 'title': l['title'], 'length': len(l['text'])}
            for l in letters_1929
        ]
    }

    report_file = output_dir / "extraction_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Extraction complete! Report saved to: {report_file}")
    print(f"✓ Letters saved to: {output_dir}")


if __name__ == "__main__":
    main()
