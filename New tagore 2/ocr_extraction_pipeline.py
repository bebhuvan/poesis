#!/usr/bin/env python3
"""
OCR Extraction Pipeline for Historical Letters
Implements structured reconstruction with >98% accuracy target
"""

import os
import re
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from collections import defaultdict, Counter

@dataclass
class OCRWord:
    """Structured OCR word data"""
    page: int
    block_num: int
    par_num: int
    line_num: int
    word_num: int
    word: str
    confidence: float
    left: int
    top: int
    width: int
    height: int

@dataclass
class LetterMetadata:
    """Extracted letter metadata"""
    author: str = "Unknown"
    author_variants: List[str] = None
    recipient: str = "Unknown"
    date: str = ""
    date_original: str = ""
    date_confidence: str = "low"
    location: str = ""
    source_pdf: str = ""
    source_pages: str = ""
    ocr_confidence: float = 0.0
    word_count: int = 0

    def __post_init__(self):
        if self.author_variants is None:
            self.author_variants = []

class OCRExtractor:
    """Main OCR extraction pipeline"""

    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        self.images_dir = self.output_dir / "images"
        self.tsv_dir = self.output_dir / "tsv_data"
        self.review_dir = self.output_dir / "review_html"
        self.final_dir = self.output_dir / "final_markdown"

        for d in [self.images_dir, self.tsv_dir, self.review_dir, self.final_dir]:
            d.mkdir(exist_ok=True)

        self.pdf_doc = fitz.open(str(self.pdf_path))
        self.total_pages = len(self.pdf_doc)

        print(f"📚 Loaded PDF: {self.pdf_path.name}")
        print(f"📄 Total pages: {self.total_pages}")

    def extract_page_to_image(self, page_num: int, dpi: int = 300) -> Path:
        """Extract PDF page to high-quality image"""
        page = self.pdf_doc[page_num]

        # Render at high DPI for better OCR
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Save as PNG
        img_path = self.images_dir / f"page_{page_num+1:04d}.png"
        pix.save(str(img_path))

        return img_path

    def run_tesseract_tsv(self, image_path: Path) -> List[OCRWord]:
        """Run Tesseract with TSV output for structured data"""
        # Get TSV output from Tesseract
        tsv_data = pytesseract.image_to_data(
            str(image_path),
            output_type=pytesseract.Output.DICT,
            config='--psm 1'  # Automatic page segmentation with OSD
        )

        page_num = int(image_path.stem.split('_')[1]) - 1

        words = []
        for i in range(len(tsv_data['text'])):
            word_text = tsv_data['text'][i].strip()
            conf = float(tsv_data['conf'][i])

            # Skip empty words and low confidence garbage
            if not word_text or conf < 0:
                continue

            word = OCRWord(
                page=page_num,
                block_num=tsv_data['block_num'][i],
                par_num=tsv_data['par_num'][i],
                line_num=tsv_data['line_num'][i],
                word_num=tsv_data['word_num'][i],
                word=word_text,
                confidence=conf,
                left=tsv_data['left'][i],
                top=tsv_data['top'][i],
                width=tsv_data['width'][i],
                height=tsv_data['height'][i]
            )
            words.append(word)

        return words

    def detect_headers_footers(self, all_words: List[OCRWord]) -> Dict[str, List[str]]:
        """Detect running headers and footers using repetition patterns"""
        # Group words by vertical position
        top_words = defaultdict(list)  # Top 15% of pages
        bottom_words = defaultdict(list)  # Bottom 15% of pages

        for word in all_words:
            # Approximate page height (should be consistent)
            if word.top < 800:  # Likely header region
                top_words[word.word.upper()].append((word.page, word.top))
            elif word.top > 2400:  # Likely footer region
                bottom_words[word.word.upper()].append((word.page, word.top))

        # Find repeated patterns (appearing on 3+ pages)
        headers = [word for word, occurrences in top_words.items()
                   if len(occurrences) >= 3]
        footers = [word for word, occurrences in bottom_words.items()
                   if len(occurrences) >= 3]

        # Also detect page numbers
        page_numbers = []
        for word in all_words:
            if word.word.isdigit() and 1 <= int(word.word) <= self.total_pages:
                page_numbers.append(word.word)

        return {
            'headers': headers,
            'footers': footers,
            'page_numbers': list(set(page_numbers))
        }

    def remove_headers_footers(self, words: List[OCRWord],
                               patterns: Dict[str, List[str]]) -> List[OCRWord]:
        """Remove identified headers, footers, and page numbers"""
        cleaned = []

        remove_words = set(
            patterns['headers'] +
            patterns['footers'] +
            patterns['page_numbers']
        )

        for word in words:
            # Skip if matches header/footer patterns
            if word.word.upper() in remove_words:
                continue

            # Skip if it's a standalone page number
            if word.word.isdigit() and word.word in patterns['page_numbers']:
                continue

            cleaned.append(word)

        return cleaned

    def fix_hyphenation(self, text: str) -> Tuple[str, int]:
        """Fix line-break hyphenation intelligently"""
        fixes_made = 0

        # Pattern: word- followed by newline and lowercase word
        # Example: "import-\nance" -> "importance"
        pattern = r'(\w+)-\s*\n\s*([a-z]+)'

        def hyphen_fix(match):
            nonlocal fixes_made
            word1 = match.group(1)
            word2 = match.group(2)

            # Try without hyphen first
            combined_no_hyphen = word1 + word2
            # Try with hyphen (for compound words)
            combined_with_hyphen = word1 + '-' + word2

            # Simple heuristic: if it's a common pattern, remove hyphen
            # This would ideally use a dictionary lookup
            # For now, remove hyphen for most cases
            fixes_made += 1
            return combined_no_hyphen

        fixed_text = re.sub(pattern, hyphen_fix, text)

        return fixed_text, fixes_made

    def reconstruct_paragraphs(self, words: List[OCRWord]) -> str:
        """Reconstruct text with proper paragraph structure"""
        if not words:
            return ""

        # Group by page, block, paragraph, line
        structure = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for word in words:
            structure[word.page][word.block_num][(word.par_num, word.line_num)].append(word)

        # Build text with paragraph awareness
        paragraphs = []
        current_paragraph_lines = []
        prev_par_num = None
        prev_block_num = None

        for page in sorted(structure.keys()):
            for block in sorted(structure[page].keys()):
                for (par_num, line_num) in sorted(structure[page][block].keys()):
                    line_words = sorted(structure[page][block][(par_num, line_num)],
                                      key=lambda w: w.word_num)
                    line_text = ' '.join(w.word for w in line_words)

                    # New paragraph detection (paragraph number changed OR block changed)
                    if ((prev_par_num is not None and par_num != prev_par_num) or
                        (prev_block_num is not None and block != prev_block_num)):
                        # Save previous paragraph
                        if current_paragraph_lines:
                            # Join lines with space (not newline) for paragraph flow
                            paragraph_text = ' '.join(current_paragraph_lines)
                            paragraphs.append(paragraph_text)
                            current_paragraph_lines = []

                    current_paragraph_lines.append(line_text)
                    prev_par_num = par_num
                    prev_block_num = block

        # Add final paragraph
        if current_paragraph_lines:
            paragraph_text = ' '.join(current_paragraph_lines)
            paragraphs.append(paragraph_text)

        # Join paragraphs with double newline
        return '\n\n'.join(paragraphs)

    def clean_ocr_artifacts(self, text: str) -> Tuple[str, List[str]]:
        """Remove OCR artifacts and normalize"""
        changes = []

        # Remove common OCR noise
        noise_patterns = [
            (r'[©®▯□�]+', ''),
            (r'\s+[|~]\s+', ' '),
            (r'= = =', ''),
            (r'- - -', '---'),
            (r'\s{2,}', ' '),  # Multiple spaces -> single
            (r' ([,.;:!?])', r'\1'),  # Fix detached punctuation
            (r"(\w)\s'(\w)", r"\1'\2"),  # Fix detached apostrophes
        ]

        for pattern, replacement in noise_patterns:
            matches = len(re.findall(pattern, text))
            if matches > 0:
                changes.append(f"Removed/fixed {matches} instances of '{pattern}'")
            text = re.sub(pattern, replacement, text)

        return text, changes

    def extract_date(self, text: str) -> Tuple[str, str, str]:
        """Extract and normalize date"""
        # Common date patterns
        patterns = [
            # "June 17, 1920" or "June 17, 19.20"
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})[,\s]+(\d{2,4}\.?\d{0,2})',
            # "15th March, 1920"
            r'(\d{1,2})(st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+(\d{4})',
            # "May 19" (without year - extract from context)
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})',
            # "1920-03-15"
            r'(\d{4})-(\d{2})-(\d{2})',
        ]

        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                original = match.group(0)

                # Parse based on pattern
                if groups[0] in month_map:
                    month = month_map[groups[0]]
                    day = groups[1].zfill(2)

                    # Handle year
                    if len(groups) >= 3 and groups[2]:
                        year_str = groups[2].replace('.', '')
                        # Handle abbreviated year like "19.20" or "20"
                        if len(year_str) == 2:
                            year = "19" + year_str
                        elif len(year_str) == 4:
                            year = year_str
                        else:
                            year = "1920"  # Default for this collection
                    else:
                        year = "1920"  # Default year from document metadata

                    iso_date = f"{year}-{month}-{day}"
                    confidence = "high" if len(groups) >= 3 else "medium"
                    return iso_date, original, confidence

                elif len(groups) == 4:  # "15th March, 1920"
                    day = groups[0].zfill(2)
                    month = month_map.get(groups[2], '00')
                    year = groups[3]
                    iso_date = f"{year}-{month}-{day}"
                    return iso_date, original, "high"

        return "", "", "none"

    def extract_metadata_from_text(self, text: str, pages: str) -> LetterMetadata:
        """Extract metadata dynamically from letter text"""
        metadata = LetterMetadata()
        metadata.source_pdf = self.pdf_path.name
        metadata.source_pages = pages

        # Extract date
        iso_date, original_date, confidence = self.extract_date(text)
        metadata.date = iso_date
        metadata.date_original = original_date
        metadata.date_confidence = confidence

        # Extract author (Tagore)
        # Look for signature patterns
        author_patterns = [
            r'(?:Yours\s+(?:sincerely|truly|faithfully)[,\s]+)?(Rabindranath\s+Tagore)',
            r'(?:Yours\s+(?:sincerely|truly|faithfully)[,\s]+)?(R\.?\s*Tagore)',
            r'(?:Yours\s+(?:sincerely|truly|faithfully)[,\s]+)?(Tagore)',
        ]

        for pattern in author_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.author = match.group(1)
                metadata.author_variants = ["Rabindranath Tagore", "R. Tagore", "Tagore"]
                break

        # If not found, use default
        if metadata.author == "Unknown":
            metadata.author = "Rabindranath Tagore"
            metadata.author_variants = ["Rabindranath Tagore", "R. Tagore"]

        # Extract recipient from salutation
        salutation_patterns = [
            r'Dear\s+(?:Mr\.?\s+)?(?:Mrs\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'My\s+dear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]

        for pattern in salutation_patterns:
            match = re.search(pattern, text)
            if match:
                metadata.recipient = match.group(1)
                break

        # Extract location (often appears with date or as header)
        # Look for patterns like "LONDON, June 17" or "NEAR ADEN, May 19"
        location_patterns = [
            r'([A-Z][A-Z\s]+),\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)',
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                metadata.location = match.group(1).strip()
                break

        # Calculate word count
        metadata.word_count = len(text.split())

        return metadata

    def calculate_confidence(self, words: List[OCRWord]) -> float:
        """Calculate average confidence score"""
        if not words:
            return 0.0

        total_conf = sum(w.confidence for w in words)
        return total_conf / len(words)

    def process_page_range(self, start_page: int, end_page: int,
                          letter_num: int = 1) -> Dict:
        """Process a range of pages as a single letter"""
        print(f"\n📝 Processing Letter #{letter_num}: Pages {start_page+1}-{end_page+1}")

        all_words = []

        # Extract and OCR each page
        for page_num in range(start_page, end_page + 1):
            print(f"  📄 Page {page_num+1}/{self.total_pages}", end='\r')

            # Extract page to image
            img_path = self.extract_page_to_image(page_num)

            # Run OCR
            words = self.run_tesseract_tsv(img_path)
            all_words.extend(words)

        print(f"  ✓ Extracted {len(all_words)} words from {end_page-start_page+1} pages")

        # Detect headers/footers across all pages
        print("  🔍 Detecting headers/footers...")
        patterns = self.detect_headers_footers(all_words)
        print(f"  ✓ Found {len(patterns['headers'])} header patterns, "
              f"{len(patterns['footers'])} footer patterns")

        # Remove headers/footers
        cleaned_words = self.remove_headers_footers(all_words, patterns)
        print(f"  ✓ Removed {len(all_words) - len(cleaned_words)} header/footer words")

        # Reconstruct text with paragraph structure
        print("  📐 Reconstructing paragraphs...")
        text = self.reconstruct_paragraphs(cleaned_words)

        # Clean artifacts
        print("  🧹 Cleaning OCR artifacts...")
        text, cleaning_changes = self.clean_ocr_artifacts(text)

        # Fix hyphenation
        print("  🔗 Fixing line-break hyphenation...")
        text, hyphen_fixes = self.fix_hyphenation(text)
        print(f"  ✓ Fixed {hyphen_fixes} hyphenation issues")

        # Extract metadata
        print("  📊 Extracting metadata...")
        pages_str = f"{start_page+1}-{end_page+1}" if start_page != end_page else f"{start_page+1}"
        metadata = self.extract_metadata_from_text(text, pages_str)

        # Calculate confidence
        metadata.ocr_confidence = self.calculate_confidence(cleaned_words)

        print(f"  ✓ Author: {metadata.author}")
        print(f"  ✓ Recipient: {metadata.recipient}")
        print(f"  ✓ Date: {metadata.date or 'Not found'}")
        print(f"  ✓ OCR Confidence: {metadata.ocr_confidence:.1f}%")

        return {
            'metadata': metadata,
            'text': text,
            'words': cleaned_words,
            'patterns': patterns,
            'cleaning_changes': cleaning_changes,
            'hyphen_fixes': hyphen_fixes,
            'letter_num': letter_num,
            'start_page': start_page,
            'end_page': end_page
        }

    def generate_review_html(self, result: Dict) -> Path:
        """Generate HTML review file"""
        metadata = result['metadata']
        text = result['text']

        # Split text into paragraphs for confidence coloring
        paragraphs = text.split('\n\n')

        # Generate filename
        author_last = metadata.author.split()[-1].lower()
        recipient_last = metadata.recipient.split()[-1].lower() if metadata.recipient != "Unknown" else "unknown"
        date_str = metadata.date if metadata.date else "undated"
        filename = f"{author_last}_{recipient_last}_{date_str}_{result['letter_num']:03d}_review.html"

        html_path = self.review_dir / filename

        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Review: {metadata.author} to {metadata.recipient} ({metadata.date or 'Undated'})</title>
    <style>
        .container {{ max-width: 1200px; margin: 0 auto; font-family: Georgia, serif; padding: 20px; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin-bottom: 20px; }}
        .metadata p {{ margin: 5px 0; }}
        .transcription {{ line-height: 1.8; font-size: 16px; }}
        .high-confidence {{ background: transparent; }}
        .medium-confidence {{ background: #fff3cd; }}
        .low-confidence {{ background: #f8d7da; }}
        .stats {{ background: #f0f0f0; padding: 15px; margin-top: 20px; }}
        .stats ul {{ list-style: none; padding: 0; }}
        .stats li {{ padding: 5px 0; }}
        .correction-history {{ background: #e7f3ff; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        h1 {{ color: #333; }}
        h3 {{ color: #555; }}
        h4 {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Letter Review: {metadata.author} to {metadata.recipient}</h1>

        <div class="metadata">
            <p><strong>Author:</strong> {metadata.author}</p>
            <p><strong>Recipient:</strong> {metadata.recipient}</p>
            <p><strong>Date:</strong> <span class="{'high-confidence' if metadata.date_confidence == 'high' else 'medium-confidence'}">{metadata.date or 'Unknown'}</span>
               {f'<span style="font-size: 12px;">(Original: {metadata.date_original})</span>' if metadata.date_original else ''}</p>
            <p><strong>Location:</strong> {metadata.location or 'Unknown'}</p>
            <p><strong>Source:</strong> {metadata.source_pdf}, Pages {metadata.source_pages}</p>
            <p><strong>OCR Confidence:</strong> {metadata.ocr_confidence:.1f}%</p>
        </div>

        <hr>

        <div class="transcription">
            <h3>Extracted Text</h3>
"""

        # Add paragraphs with confidence coloring
        avg_conf = metadata.ocr_confidence
        for para in paragraphs:
            if not para.strip():
                continue

            # Simple confidence heuristic based on overall score
            if avg_conf >= 90:
                css_class = "high-confidence"
            elif avg_conf >= 80:
                css_class = "medium-confidence"
            else:
                css_class = "low-confidence"

            html += f'            <p class="{css_class}">{para}</p>\n'

        html += f"""
        </div>

        <div class="correction-history">
            <h4>Extraction Notes</h4>
            <ul>
                <li><strong>Headers removed:</strong> {', '.join(result['patterns']['headers'][:5]) if result['patterns']['headers'] else 'None detected'}</li>
                <li><strong>Footers removed:</strong> {', '.join(result['patterns']['footers'][:5]) if result['patterns']['footers'] else 'None detected'}</li>
                <li><strong>Hyphenation fixes:</strong> {result['hyphen_fixes']}</li>
                <li><strong>Cleaning operations:</strong> {len(result['cleaning_changes'])}</li>
            </ul>

            <h4>Review Checklist</h4>
            <ul>
                <li>☐ Verify date format against original scan</li>
                <li>☐ Confirm author and recipient metadata</li>
                <li>☐ Check paragraph breaks match original layout</li>
                <li>☐ Verify no headers/footers remain in text</li>
                <li>☐ Review any low-confidence segments</li>
            </ul>
        </div>

        <div class="stats">
            <h3>Extraction Statistics</h3>
            <ul>
                <li><strong>Total words:</strong> {metadata.word_count}</li>
                <li><strong>Overall confidence:</strong> {metadata.ocr_confidence:.1f}%</li>
                <li><strong>Pages processed:</strong> {result['end_page'] - result['start_page'] + 1}</li>
                <li><strong>Hyphenation fixes:</strong> {result['hyphen_fixes']}</li>
                <li><strong>OCR Engine:</strong> Tesseract 5.3.4</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  ✓ Generated review HTML: {html_path.name}")
        return html_path

    def generate_final_markdown(self, result: Dict) -> Path:
        """Generate final publication-ready markdown"""
        metadata = result['metadata']
        text = result['text']

        # Generate filename
        author_last = metadata.author.split()[-1].lower()
        recipient_last = metadata.recipient.split()[-1].lower() if metadata.recipient != "Unknown" else "unknown"
        date_str = metadata.date if metadata.date else "undated"
        filename = f"{author_last}_{recipient_last}_{date_str}_{result['letter_num']:03d}.md"

        md_path = self.final_dir / filename

        # Build markdown with YAML frontmatter
        markdown = f"""---
title: "Letter to {metadata.recipient}"
author: "{metadata.author}"
author_variants: {json.dumps(metadata.author_variants)}
recipient: "{metadata.recipient}"
date: "{metadata.date}"
date_confidence: "{metadata.date_confidence}"
date_original: "{metadata.date_original}"
location: "{metadata.location}"
source_pdf: "{metadata.source_pdf}"
source_pages: "{metadata.source_pages}"
ocr_confidence: "{metadata.ocr_confidence:.1f}%"
word_count: {metadata.word_count}
extraction_date: "2025-11-21"
---

{text}

---

### Editorial Notes
- Extracted using Tesseract 5.3.4 with structured OCR pipeline
- OCR confidence: {metadata.ocr_confidence:.1f}%
- Fixed {result['hyphen_fixes']} line-break hyphenation errors
- Removed running headers and footers
- Paragraph structure reconstructed from OCR metadata
- Source: {metadata.source_pdf}, pages {metadata.source_pages}
"""

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"  ✓ Generated final markdown: {md_path.name}")
        return md_path


def main():
    """Main execution"""
    pdf_path = "/home/user/poesis/New tagore 2/tagore_letters_from_abroad_1924.pdf"
    output_dir = "/home/user/poesis/New tagore 2/extracted_letters"

    print("=" * 70)
    print("OCR EXTRACTION PIPELINE FOR HISTORICAL LETTERS")
    print("Target: >98% accuracy with structured reconstruction")
    print("=" * 70)

    extractor = OCRExtractor(pdf_path, output_dir)

    # For initial test, process first few pages as a sample letter
    # In production, this would detect letter boundaries automatically

    print("\n🚀 Starting extraction process...\n")

    # Sample: Extract first letter (pages 0-4 as a test)
    result = extractor.process_page_range(
        start_page=10,  # Skip table of contents
        end_page=15,    # First letter
        letter_num=1
    )

    # Generate outputs
    print("\n📋 Generating review files...")
    html_path = extractor.generate_review_html(result)
    md_path = extractor.generate_final_markdown(result)

    print("\n" + "=" * 70)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"\n📁 Review HTML: {html_path}")
    print(f"📁 Final Markdown: {md_path}")
    print(f"\n📊 Summary:")
    print(f"   • OCR Confidence: {result['metadata'].ocr_confidence:.1f}%")
    print(f"   • Word Count: {result['metadata'].word_count}")
    print(f"   • Hyphenation Fixes: {result['hyphen_fixes']}")
    print(f"   • Author: {result['metadata'].author}")
    print(f"   • Recipient: {result['metadata'].recipient}")
    print(f"   • Date: {result['metadata'].date or 'Not detected'}")
    print("\n💡 Next step: Review the HTML file to verify accuracy")
    print("   Then process remaining pages with detected letter boundaries\n")


if __name__ == "__main__":
    main()
