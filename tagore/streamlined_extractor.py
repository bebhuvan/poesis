#!/usr/bin/env python3
"""
Streamlined Tagore Letters Extractor
Efficient processing using Tesseract with our preprocessing and post-processing
"""

import cv2
import numpy as np
from pathlib import Path
import pytesseract
import json
import logging
from datetime import datetime
from tqdm import tqdm
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamlinedExtractor:
    """Efficient extractor with preprocessing + Tesseract + post-processing"""

    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'pages_processed': 0,
            'pages_succeeded': 0,
            'pages_failed': 0,
            'total_characters': 0,
            'total_words': 0,
            'start_time': datetime.utcnow().isoformat()
        }

    def preprocess_image(self, image_path):
        """Apply image preprocessing"""
        # Load image
        img = cv2.imread(str(image_path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Binarize with Otsu
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def extract_text(self, image):
        """Run Tesseract OCR"""
        text = pytesseract.image_to_string(
            image,
            lang='eng',
            config='--psm 1'  # Automatic page segmentation with OSD
        )
        return text

    def postprocess_text(self, text):
        """Apply basic post-processing corrections"""
        corrections = []
        original_text = text

        # Fix common OCR errors
        replacements = {
            'ba ': 'be ',
            'vighis': 'rights',
            'Yeserved': 'reserved',
            'pais©': 'paise',
        }

        for wrong, correct in replacements.items():
            if wrong in text:
                text = text.replace(wrong, correct)
                corrections.append(f"{wrong} → {correct}")

        # Fix multiple spaces
        text = re.sub(r' +', ' ', text)

        # Fix line breaks within sentences
        text = re.sub(r'(?<=[a-z,])\n(?=[a-z])', ' ', text)

        # Normalize
        text = text.strip()

        return {
            'text': text,
            'original_text': original_text,
            'corrections': corrections
        }

    def process_page(self, image_path, page_number):
        """Process a single page"""
        try:
            # Preprocess
            preprocessed = self.preprocess_image(image_path)

            # Extract text
            raw_text = self.extract_text(preprocessed)

            # Post-process
            result = self.postprocess_text(raw_text)

            # Calculate stats
            char_count = len(result['text'])
            word_count = len(result['text'].split())

            # Save results
            page_dir = self.output_dir / f"page_{page_number:04d}"
            page_dir.mkdir(parents=True, exist_ok=True)

            # Save plain text
            with open(page_dir / "text.txt", 'w', encoding='utf-8') as f:
                f.write(result['text'])

            # Save metadata
            metadata = {
                'page_number': page_number,
                'image_path': str(image_path),
                'character_count': char_count,
                'word_count': word_count,
                'corrections': result['corrections'],
                'timestamp': datetime.utcnow().isoformat()
            }

            with open(page_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Update stats
            self.stats['pages_succeeded'] += 1
            self.stats['total_characters'] += char_count
            self.stats['total_words'] += word_count

            return {
                'success': True,
                'page': page_number,
                'chars': char_count,
                'words': word_count,
                'corrections': len(result['corrections'])
            }

        except Exception as e:
            logger.error(f"Failed to process page {page_number}: {e}")
            self.stats['pages_failed'] += 1
            return {
                'success': False,
                'page': page_number,
                'error': str(e)
            }
        finally:
            self.stats['pages_processed'] += 1

    def process_all(self, image_dir, page_range=None):
        """Process all pages in directory"""
        image_dir = Path(image_dir)

        # Find all images
        images = sorted(image_dir.glob("page_*.jpg"))

        if page_range:
            start, end = page_range
            images = images[start-1:end]

        logger.info(f"Processing {len(images)} pages...")

        results = []

        for image_path in tqdm(images, desc="Extracting text"):
            # Extract page number from filename
            page_num = int(image_path.stem.split('_')[1])

            result = self.process_page(image_path, page_num)
            results.append(result)

            if result['success']:
                tqdm.write(f"✓ Page {page_num}: {result['words']} words, {result['corrections']} corrections")

        # Save summary
        self.stats['end_time'] = datetime.utcnow().isoformat()

        with open(self.output_dir / "summary.json", 'w') as f:
            json.dump({
                'stats': self.stats,
                'results': results
            }, f, indent=2)

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("EXTRACTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Pages processed: {self.stats['pages_processed']}")
        logger.info(f"Success: {self.stats['pages_succeeded']}")
        logger.info(f"Failed: {self.stats['pages_failed']}")
        logger.info(f"Total words: {self.stats['total_words']:,}")
        logger.info(f"Total characters: {self.stats['total_characters']:,}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("="*60)

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Streamlined Tagore Letters Extractor')
    parser.add_argument('--image-dir', type=Path, default=Path('data/images'),
                       help='Directory containing page images')
    parser.add_argument('--output-dir', type=Path, default=Path('output'),
                       help='Output directory')
    parser.add_argument('--page-range', type=str,
                       help='Page range (e.g., "1-10")')
    parser.add_argument('--single-page', type=int,
                       help='Process single page')

    args = parser.parse_args()

    extractor = StreamlinedExtractor(output_dir=args.output_dir)

    if args.single_page:
        # Single page
        image_path = args.image_dir / f"page_{args.single_page:04d}.jpg"
        if image_path.exists():
            result = extractor.process_page(image_path, args.single_page)
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: Image not found: {image_path}")
    else:
        # All pages or range
        page_range = None
        if args.page_range:
            start, end = map(int, args.page_range.split('-'))
            page_range = (start, end)

        extractor.process_all(args.image_dir, page_range)


if __name__ == '__main__':
    main()
