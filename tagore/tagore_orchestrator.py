#!/usr/bin/env python3
"""
Tagore Letters OCR Orchestrator - Main Entry Point
Coordinates all strategies for high-quality historical text extraction
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys
from tqdm import tqdm

from tagore_config import (
    OUTPUT_DIR, LOGS_DIR, ARCHIVE_URL, ARCHIVE_ID,
    DOCUMENT_METADATA, QUALITY_TARGETS, OUTPUT_FORMATS
)

from image_preprocessor import ImagePreprocessor
from multi_engine_ocr import MultiEngineOCR
from layout_analyzer import LayoutAnalyzer
from text_postprocessor import TextPostProcessor
from verification_suite import VerificationSuite


class TagoreOrchestrator:
    """
    Main orchestrator coordinating all 5 extraction strategies
    and 6 verification strategies.
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize orchestrator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        self.logger = logging.getLogger(__name__)
        self.logger.info("="*60)
        self.logger.info("TAGORE LETTERS OCR SYSTEM")
        self.logger.info("="*60)

        # Initialize components
        self.logger.info("Initializing components...")

        self.preprocessor = ImagePreprocessor()
        self.ocr = MultiEngineOCR()
        self.layout_analyzer = LayoutAnalyzer()
        self.postprocessor = TextPostProcessor()
        self.verifier = VerificationSuite()

        self.logger.info("All components initialized successfully")

        # Statistics
        self.stats = {
            'pages_processed': 0,
            'pages_succeeded': 0,
            'pages_failed': 0,
            'total_corrections': 0,
            'total_flags': 0,
            'start_time': datetime.utcnow().isoformat()
        }

    def _setup_logging(self):
        """Setup logging configuration."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOGS_DIR / f"tagore_ocr_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.log_file = log_file

    def process_single_page(self, image_path: Path, page_number: int) -> Dict:
        """
        Process a single page through complete pipeline.

        Args:
            image_path: Path to page image
            page_number: Page number

        Returns:
            Complete processing result
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"PROCESSING PAGE {page_number}")
        self.logger.info(f"{'='*60}")

        result = {
            'page_number': page_number,
            'image_path': str(image_path),
            'timestamp': datetime.utcnow().isoformat(),
            'success': False
        }

        try:
            # Step 1: Preprocessing (Strategy 2)
            self.logger.info("Step 1/6: Image preprocessing...")
            processed_dir = self.output_dir / 'processed' / f'page_{page_number:04d}'
            preprocessed = self.preprocessor.preprocess(image_path, processed_dir)
            result['preprocessed'] = {k: str(v) for k, v in preprocessed.items() if v}

            # Step 2: Layout Analysis (Strategy 3)
            self.logger.info("Step 2/6: Layout analysis...")
            layout = self.layout_analyzer.analyze(
                preprocessed.get('enhanced') or preprocessed.get('grayscale') or image_path
            )
            result['layout'] = layout

            # Step 3: Multi-Engine OCR (Strategy 1)
            self.logger.info("Step 3/6: Multi-engine OCR...")

            # Use best preprocessed version for OCR
            ocr_image = preprocessed.get('binary_best') or preprocessed.get('enhanced') or image_path

            ocr_results = self.ocr.process_image(ocr_image, page_number)
            result['ocr'] = ocr_results

            # Step 4: Post-Processing (Strategy 4)
            self.logger.info("Step 4/6: Text post-processing...")
            consensus_text = ocr_results['consensus']['text']
            consensus_confidence = ocr_results['consensus'].get('confidence', 0.0)

            # Build confidence map from OCR results
            confidence_map = {}
            for engine, engine_result in ocr_results['engine_results'].items():
                if 'word_boxes' in engine_result and engine_result['word_boxes']:
                    for word_box in engine_result['word_boxes']:
                        word = word_box.get('text', '').lower()
                        conf = word_box.get('confidence', 0.0)
                        if word:
                            confidence_map[word] = max(confidence_map.get(word, 0.0), conf)

            postprocessed = self.postprocessor.process(consensus_text, confidence_map)
            result['postprocessed'] = postprocessed

            self.stats['total_corrections'] += postprocessed['correction_count']

            # Step 5: Comprehensive Verification (All 6 Strategies)
            self.logger.info("Step 5/6: Running verification suite...")
            verification = self.verifier.verify_all(ocr_results, image_path)
            result['verification'] = verification

            self.stats['total_flags'] += len(verification.get('flags', []))

            # Step 6: Export
            self.logger.info("Step 6/6: Exporting results...")
            export_paths = self._export_page(page_number, result)
            result['exports'] = export_paths

            # Success
            result['success'] = True
            self.stats['pages_succeeded'] += 1

            # Log summary
            self.logger.info(f"\n✓ Page {page_number} completed successfully")
            self.logger.info(f"  - Text length: {len(postprocessed['corrected_text'])} characters")
            self.logger.info(f"  - Corrections: {postprocessed['correction_count']}")
            self.logger.info(f"  - Quality: {verification['overall_quality']['quality']}")
            self.logger.info(f"  - Flags: {len(verification.get('flags', []))}")

        except Exception as e:
            self.logger.error(f"✗ Page {page_number} failed: {e}", exc_info=True)
            result['error'] = str(e)
            self.stats['pages_failed'] += 1

        finally:
            self.stats['pages_processed'] += 1

        return result

    def process_directory(self, image_dir: Path, page_range: Optional[tuple] = None) -> List[Dict]:
        """
        Process all images in a directory.

        Args:
            image_dir: Directory containing page images
            page_range: Optional (start, end) page numbers to process

        Returns:
            List of processing results
        """
        image_dir = Path(image_dir)

        # Find all images
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.jp2', '*.tif', '*.tiff']
        images = []

        for ext in image_extensions:
            images.extend(image_dir.glob(ext))

        images = sorted(images)

        # Apply page range filter
        if page_range:
            start, end = page_range
            images = images[start-1:end]

        self.logger.info(f"Found {len(images)} images to process")

        results = []

        # Process each page with progress bar
        for i, image_path in enumerate(tqdm(images, desc="Processing pages"), start=1):
            page_number = i if not page_range else page_range[0] + i - 1

            result = self.process_single_page(image_path, page_number)
            results.append(result)

        # Generate summary report
        self._generate_summary_report(results)

        return results

    def download_from_archive(self, output_path: Path = None) -> Path:
        """
        Download images from Internet Archive.

        Args:
            output_path: Directory to save images

        Returns:
            Path to downloaded images directory
        """
        if output_path is None:
            output_path = self.output_dir.parent / 'data' / 'images'

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Downloading from: {ARCHIVE_URL}")
        self.logger.info(f"Saving to: {output_path}")

        try:
            # Use internetarchive library
            from internetarchive import get_item

            item = get_item(ARCHIVE_ID)

            self.logger.info(f"Archive item: {item.metadata.get('title', 'Unknown')}")

            # Download all JP2 images
            files = [f for f in item.files if f['name'].endswith('.jp2')]

            self.logger.info(f"Found {len(files)} JP2 images")

            for file_info in tqdm(files, desc="Downloading"):
                file_name = file_info['name']
                file_path = output_path / Path(file_name).name

                if not file_path.exists():
                    item.download(
                        files=[file_name],
                        destdir=str(output_path),
                        silent=True
                    )

            self.logger.info(f"Download complete: {len(files)} files")

            return output_path

        except ImportError:
            self.logger.error("internetarchive library not installed")
            self.logger.error("Install with: pip install internetarchive")
            raise

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise

    def _export_page(self, page_number: int, result: Dict) -> Dict:
        """Export page results in multiple formats."""
        exports = {}

        page_dir = self.output_dir / 'pages' / f'page_{page_number:04d}'
        page_dir.mkdir(parents=True, exist_ok=True)

        # JSON (always)
        json_path = page_dir / 'result.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        exports['json'] = str(json_path)

        # Plain text
        if OUTPUT_FORMATS['txt']:
            txt_path = page_dir / 'text.txt'
            text = result['postprocessed']['corrected_text']
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            exports['txt'] = str(txt_path)

        # Markdown
        if OUTPUT_FORMATS['markdown']:
            md_path = page_dir / 'text.md'
            self._export_markdown(page_number, result, md_path)
            exports['md'] = str(md_path)

        return exports

    def _export_markdown(self, page_number: int, result: Dict, output_path: Path):
        """Export page as Markdown with metadata."""
        with open(output_path, 'w', encoding='utf-8') as f:
            # YAML frontmatter
            f.write("---\n")
            f.write(f"page_number: {page_number}\n")
            f.write(f"source_archive: {ARCHIVE_URL}\n")
            f.write(f"processed_at: {result['timestamp']}\n")
            f.write(f"quality: {result['verification']['overall_quality']['quality']}\n")
            f.write(f"confidence: {result['verification']['overall_quality']['overall_score']:.3f}\n")
            f.write(f"corrections_made: {result['postprocessed']['correction_count']}\n")
            f.write(f"flags: {len(result['verification'].get('flags', []))}\n")
            f.write("---\n\n")

            # Page content
            f.write(f"# Page {page_number}\n\n")
            f.write(result['postprocessed']['corrected_text'])
            f.write("\n\n")

            # Verification flags (if any)
            if result['verification'].get('flags'):
                f.write("## Verification Flags\n\n")
                for flag in result['verification']['flags']:
                    f.write(f"- **{flag['type']}** ({flag['severity']}): {flag['message']}\n")

    def _generate_summary_report(self, results: List[Dict]):
        """Generate comprehensive summary report."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info(f"{'='*60}")

        # Statistics
        self.stats['end_time'] = datetime.utcnow().isoformat()

        self.logger.info(f"Pages processed: {self.stats['pages_processed']}")
        self.logger.info(f"Pages succeeded: {self.stats['pages_succeeded']}")
        self.logger.info(f"Pages failed: {self.stats['pages_failed']}")
        self.logger.info(f"Total corrections: {self.stats['total_corrections']}")
        self.logger.info(f"Total flags: {self.stats['total_flags']}")

        # Quality metrics
        qualities = [r['verification']['overall_quality']['quality']
                    for r in results if r.get('success') and 'verification' in r]

        if qualities:
            quality_counts = {q: qualities.count(q) for q in set(qualities)}
            self.logger.info(f"\nQuality distribution:")
            for quality, count in sorted(quality_counts.items()):
                self.logger.info(f"  {quality}: {count} pages")

        # Save summary
        summary_path = self.output_dir / 'summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': self.stats,
                'quality_distribution': quality_counts if qualities else {},
                'quality_targets': QUALITY_TARGETS,
                'document_metadata': DOCUMENT_METADATA
            }, f, indent=2)

        self.logger.info(f"\nSummary saved to: {summary_path}")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"{'='*60}\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Tagore Letters Historical Text OCR System'
    )

    parser.add_argument(
        '--download',
        action='store_true',
        help='Download images from Internet Archive'
    )

    parser.add_argument(
        '--image-dir',
        type=Path,
        help='Directory containing page images to process'
    )

    parser.add_argument(
        '--page-range',
        type=str,
        help='Page range to process (e.g., "1-10" or "50-100")'
    )

    parser.add_argument(
        '--single-page',
        type=int,
        help='Process a single page number'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=OUTPUT_DIR,
        help='Output directory for results'
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = TagoreOrchestrator(output_dir=args.output_dir)

    try:
        # Download if requested
        if args.download:
            image_dir = orchestrator.download_from_archive()
        elif args.image_dir:
            image_dir = args.image_dir
        else:
            # Use default
            image_dir = OUTPUT_DIR.parent / 'data' / 'images'

        # Parse page range
        page_range = None
        if args.page_range:
            start, end = map(int, args.page_range.split('-'))
            page_range = (start, end)

        # Process
        if args.single_page:
            # Find image file for this page
            images = sorted(list(image_dir.glob('*.jp2')) + list(image_dir.glob('*.jpg')))
            if args.single_page <= len(images):
                image_path = images[args.single_page - 1]
                orchestrator.process_single_page(image_path, args.single_page)
            else:
                print(f"Error: Page {args.single_page} not found")

        else:
            # Process directory
            orchestrator.process_directory(image_dir, page_range)

        print("\n✓ Processing complete!")
        print(f"Output directory: {orchestrator.output_dir}")

    except KeyboardInterrupt:
        print("\n\nProcessing cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        logging.exception(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
