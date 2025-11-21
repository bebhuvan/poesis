#!/usr/bin/env python3
"""
Extract individual letters from the combined page text
Each letter is identified by a date header and saved separately
"""

import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class LetterExtractor:
    """Extract and separate individual letters from pages"""

    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.letters_dir = Path(output_dir) / "letters"
        self.letters_dir.mkdir(parents=True, exist_ok=True)

    def load_all_pages(self):
        """Load all page text files in order"""
        pages = []
        page_dirs = sorted(self.output_dir.glob("page_*"))

        for page_dir in page_dirs:
            text_file = page_dir / "text.txt"
            metadata_file = page_dir / "metadata.json"

            if text_file.exists():
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read()

                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                pages.append({
                    'number': metadata['page_number'],
                    'text': text,
                    'metadata': metadata
                })

        return pages

    def identify_letter_starts(self, pages):
        """Find pages where letters begin based on date patterns"""

        # Pattern to match letter headers like:
        # "RED SEA, May 24th, 1920"
        # "LONDON, June 10th, 1920"
        # "December 25th, 1914"
        date_pattern = re.compile(
            r'^([A-Z\s,]+,?\s+)?'  # Optional location (all caps)
            r'(January|February|March|April|May|June|July|August|September|October|November|December)'  # Month
            r'\s+\d{1,2}(st|nd|rd|th)?'  # Day
            r',?\s+\d{4}'  # Year
            r'\s*$',
            re.MULTILINE | re.IGNORECASE
        )

        letter_starts = []

        for page in pages:
            text = page['text']
            lines = text.split('\n')

            for i, line in enumerate(lines):
                line = line.strip()
                if date_pattern.match(line):
                    # Found a letter start
                    letter_starts.append({
                        'page_number': page['number'],
                        'line_number': i,
                        'date_header': line,
                        'text_position': text.find(line)
                    })
                    print(f"Found letter on page {page['number']}: {line}")

        return letter_starts

    def extract_letters(self, pages, letter_starts):
        """Extract individual letters based on identified starts"""

        if not letter_starts:
            print("No letters found!")
            return []

        # Build full text with page markers
        full_text = ""
        page_positions = {}

        for page in pages:
            page_positions[len(full_text)] = page['number']
            full_text += f"\n\n[PAGE {page['number']}]\n\n{page['text']}"

        letters = []

        for i, start in enumerate(letter_starts):
            # Find position in full text
            search_text = f"[PAGE {start['page_number']}]"
            page_pos = full_text.find(search_text)

            if page_pos == -1:
                continue

            # Find the actual letter start position
            letter_pos = full_text.find(start['date_header'], page_pos)

            if letter_pos == -1:
                continue

            # Determine end position (start of next letter or end of text)
            if i + 1 < len(letter_starts):
                next_start = letter_starts[i + 1]
                # Find the next letter header directly, starting after current one
                end_pos = full_text.find(next_start['date_header'], letter_pos + len(start['date_header']))

                if end_pos == -1:
                    # If not found, go to end
                    end_pos = len(full_text)
            else:
                # Last letter - go to end
                end_pos = len(full_text)

            # Extract letter text
            letter_text = full_text[letter_pos:end_pos]

            # Clean up page markers
            letter_text = re.sub(r'\[PAGE \d+\]', '', letter_text)
            letter_text = letter_text.strip()

            # Parse date and location
            date_match = re.match(
                r'^([A-Z\s,]+,)?\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(st|nd|rd|th)?,?\s+(\d{4})',
                start['date_header'],
                re.IGNORECASE
            )

            location = None
            date_str = start['date_header']

            if date_match:
                if date_match.group(1):
                    location = date_match.group(1).strip().rstrip(',')
                date_str = f"{date_match.group(2)} {date_match.group(3)}, {date_match.group(5)}"

            letters.append({
                'number': i + 1,
                'date_header': start['date_header'],
                'date': date_str,
                'location': location,
                'start_page': start['page_number'],
                'text': letter_text,
                'word_count': len(letter_text.split())
            })

        return letters

    def save_letters(self, letters):
        """Save each letter as a separate file"""

        for letter in letters:
            letter_num = letter['number']

            # Create letter directory
            letter_dir = self.letters_dir / f"letter_{letter_num:03d}"
            letter_dir.mkdir(exist_ok=True)

            # Save plain text
            text_file = letter_dir / "letter.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(letter['text'])

            # Save markdown with metadata
            md_file = letter_dir / "letter.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# Letter {letter_num}\n\n")
                f.write(f"**Date**: {letter['date']}\n\n")
                if letter['location']:
                    f.write(f"**Location**: {letter['location']}\n\n")
                f.write(f"**Start Page**: {letter['start_page']}\n\n")
                f.write(f"**Word Count**: {letter['word_count']}\n\n")
                f.write("---\n\n")
                f.write(letter['text'])
                f.write("\n")

            # Save metadata
            metadata_file = letter_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'letter_number': letter_num,
                    'date_header': letter['date_header'],
                    'date': letter['date'],
                    'location': letter['location'],
                    'start_page': letter['start_page'],
                    'word_count': letter['word_count'],
                    'extracted': datetime.utcnow().isoformat()
                }, f, indent=2)

            print(f"✓ Saved letter {letter_num}: {letter['date']}" +
                  (f" ({letter['location']})" if letter['location'] else ""))

        # Create index
        index_file = self.letters_dir / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_letters': len(letters),
                'letters': [
                    {
                        'number': l['number'],
                        'date': l['date'],
                        'location': l['location'],
                        'start_page': l['start_page'],
                        'word_count': l['word_count']
                    }
                    for l in letters
                ],
                'extracted': datetime.utcnow().isoformat()
            }, f, indent=2)

        print(f"\n✓ Created index: {index_file}")
        print(f"Total letters extracted: {len(letters)}")

        return letters


def main():
    extractor = LetterExtractor()

    print("Loading all pages...")
    pages = extractor.load_all_pages()
    print(f"Loaded {len(pages)} pages\n")

    print("Identifying letter starts...")
    letter_starts = extractor.identify_letter_starts(pages)
    print(f"\nFound {len(letter_starts)} letters\n")

    if letter_starts:
        print("Extracting letters...")
        letters = extractor.extract_letters(pages, letter_starts)

        print("\nSaving letters...")
        extractor.save_letters(letters)

        print(f"\n{'='*60}")
        print("LETTER EXTRACTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total letters: {len(letters)}")
        print(f"Output directory: {extractor.letters_dir}")
        print(f"{'='*60}")
    else:
        print("No letters found to extract!")


if __name__ == '__main__':
    main()
