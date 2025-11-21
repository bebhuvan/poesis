#!/usr/bin/env python3
"""
Archive.org Item Extraction Orchestrator

Main workflow script that coordinates:
1. Archive.org download (all formats)
2. Image preprocessing
3. Multi-engine OCR
4. Consensus voting
5. Text verification
6. Quality reporting

Designed for 100% accurate extraction of historical documents.

Example usage:
    python extract_archive_item.py in.ernet.dli.2015.208999
"""

import argparse
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import asdict

from archive_org_fetcher import ArchiveOrgFetcher
from image_preprocessing import ImagePreprocessor, PreprocessingConfig
from multi_engine_ocr import MultiEngineOCR, OCREngine
from text_verification import TextVerifier, VerificationStatus


logger = logging.getLogger(__name__)


class ArchiveItemExtractor:
    """
    Complete extraction pipeline for Archive.org items.

    Implements all 6 extraction strategies and 6 verification strategies
    for maximum accuracy.
    """

    def __init__(
        self,
        identifier: str,
        output_dir: str = "extracted_documents",
        cache_dir: str = "archive_cache",
        enable_preprocessing: bool = True,
        enable_multi_engine: bool = True,
        enable_verification: bool = True
    ):
        """
        Initialize extractor.

        Args:
            identifier: Archive.org item identifier
            output_dir: Where to save extracted text
            cache_dir: Cache for downloaded files
            enable_preprocessing: Enable image preprocessing
            enable_multi_engine: Use multiple OCR engines
            enable_verification: Run verification suite
        """
        self.identifier = identifier
        self.output_dir = Path(output_dir) / identifier
        self.cache_dir = cache_dir

        self.enable_preprocessing = enable_preprocessing
        self.enable_multi_engine = enable_multi_engine
        self.enable_verification = enable_verification

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.fetcher = ArchiveOrgFetcher(cache_dir=cache_dir)

        if enable_preprocessing:
            self.preprocessor = ImagePreprocessor(PreprocessingConfig())

        if enable_multi_engine:
            self.ocr = MultiEngineOCR([
                OCREngine.TESSERACT,
                OCREngine.EASYOCR
            ])

        if enable_verification:
            self.verifier = TextVerifier(use_ai=False)

        # Statistics
        self.stats = {
            'started_at': datetime.utcnow().isoformat(),
            'pages_processed': 0,
            'pages_successful': 0,
            'pages_failed': 0,
            'pages_need_review': 0,
            'total_issues': 0,
            'average_confidence': 0.0,
            'processing_times': {}
        }

    def extract_full(
        self,
        pages: Optional[List[int]] = None,
        target_accuracy: float = 0.999,
        save_intermediate: bool = True
    ) -> Dict:
        """
        Run complete extraction pipeline.

        Args:
            pages: List of page numbers to process (None = all)
            target_accuracy: Target accuracy (0-1)
            save_intermediate: Save intermediate results

        Returns:
            Dictionary with extraction results and statistics
        """
        logger.info(f"{'='*60}")
        logger.info(f"ARCHIVE.ORG EXTRACTION PIPELINE")
        logger.info(f"{'='*60}")
        logger.info(f"Item: {self.identifier}")
        logger.info(f"Target accuracy: {target_accuracy:.1%}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"{'='*60}\n")

        # Phase 1: Download
        logger.info("PHASE 1: Downloading from Archive.org...")
        metadata = self._download_item()

        # Phase 2: Extract ABBYY baseline
        logger.info("\nPHASE 2: Extracting ABBYY OCR baseline...")
        abbyy_pages = self._extract_abbyy_ocr()

        # Phase 3: Download page images
        logger.info("\nPHASE 3: Downloading page images...")
        page_images = self._download_images(pages)

        # Phase 4: Process each page
        logger.info(f"\nPHASE 4: Processing {len(page_images)} pages...")
        extracted_pages = self._process_pages(page_images, abbyy_pages)

        # Phase 5: Generate reports
        logger.info("\nPHASE 5: Generating reports...")
        self._generate_reports(extracted_pages, metadata)

        # Final summary
        self._print_summary()

        return {
            'metadata': metadata,
            'pages': extracted_pages,
            'statistics': self.stats
        }

    def _download_item(self) -> Dict:
        """Download item metadata and files."""
        metadata = self.fetcher.get_metadata(self.identifier)

        logger.info(f"Title: {metadata['title']}")
        logger.info(f"Creator: {metadata['creator']}")
        logger.info(f"Pages: {metadata['page_count']}")

        return metadata

    def _extract_abbyy_ocr(self) -> Dict:
        """Extract ABBYY OCR baseline from Archive.org."""
        abbyy_path = self.fetcher.download_abbyy_ocr(self.identifier)

        if not abbyy_path:
            logger.warning("No ABBYY OCR available, will rely on custom OCR")
            return {}

        pages = self.fetcher.extract_abbyy_text(abbyy_path)
        logger.info(f"Extracted ABBYY baseline for {len(pages)} pages")

        return pages

    def _download_images(self, pages: Optional[List[int]] = None) -> Dict[int, Path]:
        """Download high-resolution page images."""
        images = self.fetcher.download_page_images(
            self.identifier,
            pages=pages,
            format_pref='jp2'
        )

        logger.info(f"Downloaded {len(images)} page images")
        return images

    def _process_pages(
        self,
        page_images: Dict[int, Path],
        abbyy_pages: Dict[int, Dict]
    ) -> List[Dict]:
        """
        Process all pages through extraction pipeline.

        Args:
            page_images: Dictionary mapping page numbers to image paths
            abbyy_pages: ABBYY OCR results

        Returns:
            List of extracted page data
        """
        extracted = []

        for page_num, image_path in sorted(page_images.items()):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing Page {page_num}")
            logger.info(f"{'='*60}")

            try:
                page_data = self._process_single_page(
                    page_num,
                    image_path,
                    abbyy_pages.get(page_num)
                )

                extracted.append(page_data)
                self.stats['pages_successful'] += 1

            except Exception as e:
                logger.error(f"Failed to process page {page_num}: {e}", exc_info=True)
                self.stats['pages_failed'] += 1

            self.stats['pages_processed'] += 1

        return extracted

    def _process_single_page(
        self,
        page_num: int,
        image_path: Path,
        abbyy_data: Optional[Dict]
    ) -> Dict:
        """
        Process a single page through the complete pipeline.

        Args:
            page_num: Page number
            image_path: Path to page image
            abbyy_data: ABBYY OCR data for this page

        Returns:
            Dictionary with extracted data and metadata
        """
        page_data = {
            'page_number': page_num,
            'image_path': str(image_path),
            'preprocessing': None,
            'ocr_results': [],
            'consensus': None,
            'verification': None,
            'final_text': '',
            'status': 'pending'
        }

        # Step 1: Preprocessing
        if self.enable_preprocessing:
            logger.info("  1. Preprocessing image...")
            processed_path = self.output_dir / f"processed_page_{page_num:03d}.png"
            preprocess_result = self.preprocessor.preprocess(image_path, processed_path)

            page_data['preprocessing'] = {
                'quality_before': preprocess_result.quality_score_before,
                'quality_after': preprocess_result.quality_score_after,
                'quality_gain': preprocess_result.quality_score_after - preprocess_result.quality_score_before,
                'skew_angle': preprocess_result.skew_angle,
                'steps_applied': preprocess_result.steps_applied,
                'processing_time': preprocess_result.processing_time
            }

            logger.info(f"     Quality: {preprocess_result.quality_score_before:.1f} → {preprocess_result.quality_score_after:.1f} (+{page_data['preprocessing']['quality_gain']:.1f})")

            # Use preprocessed image for OCR
            ocr_image = processed_path
        else:
            ocr_image = image_path

        # Step 2: Multi-engine OCR
        logger.info("  2. Running multi-engine OCR...")

        abbyy_text = abbyy_data['full_text'] if abbyy_data else None
        ocr_results = self.ocr.process_image(ocr_image, abbyy_text=abbyy_text)

        for result in ocr_results:
            if not result.error:
                logger.info(f"     {result.engine.value}: {result.confidence:.1%} confidence, {len(result.text)} chars")
                page_data['ocr_results'].append({
                    'engine': result.engine.value,
                    'confidence': result.confidence,
                    'text_length': len(result.text),
                    'processing_time': result.processing_time
                })

        # Step 3: Consensus
        logger.info("  3. Computing consensus...")
        consensus = self.ocr.compute_consensus(ocr_results)

        page_data['consensus'] = {
            'confidence': consensus.overall_confidence,
            'text_length': len(consensus.consensus_text),
            'discrepancies': len(consensus.discrepancies),
            'requires_review': consensus.requires_review
        }

        logger.info(f"     Consensus: {consensus.overall_confidence:.1%} confidence, {len(consensus.discrepancies)} discrepancies")

        page_data['final_text'] = consensus.consensus_text

        # Step 4: Verification
        if self.enable_verification:
            logger.info("  4. Verifying text quality...")
            verification = self.verifier.verify(
                consensus.consensus_text,
                ocr_results=ocr_results
            )

            page_data['verification'] = {
                'status': verification.overall_status.value,
                'confidence': verification.overall_confidence,
                'consensus_score': verification.consensus_score,
                'dictionary_score': verification.dictionary_score,
                'perplexity_score': verification.perplexity_score,
                'statistical_score': verification.statistical_score,
                'historical_score': verification.historical_score,
                'issues_found': len(verification.issues),
                'critical_issues': verification.critical_issues,
                'high_priority_issues': verification.high_priority_issues,
                'requires_review': verification.requires_manual_review,
                'review_priority': verification.review_priority
            }

            logger.info(f"     Verification: {verification.overall_status.value} ({verification.overall_confidence:.1%})")
            logger.info(f"     Issues: {len(verification.issues)} total, {verification.critical_issues} critical")

            if verification.requires_manual_review:
                self.stats['pages_need_review'] += 1
                page_data['status'] = 'needs_review'
            else:
                page_data['status'] = 'verified'

            self.stats['total_issues'] += len(verification.issues)

        # Save page text
        page_file = self.output_dir / f"page_{page_num:03d}.txt"
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(page_data['final_text'])

        # Save page metadata
        metadata_file = self.output_dir / f"page_{page_num:03d}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, default=str)

        return page_data

    def _generate_reports(self, extracted_pages: List[Dict], metadata: Dict):
        """Generate comprehensive reports."""
        # Summary report
        summary = {
            'item': {
                'identifier': self.identifier,
                'title': metadata['title'],
                'creator': metadata['creator'],
                'total_pages': metadata['page_count']
            },
            'extraction': {
                'pages_processed': self.stats['pages_processed'],
                'pages_successful': self.stats['pages_successful'],
                'pages_failed': self.stats['pages_failed'],
                'pages_need_review': self.stats['pages_need_review']
            },
            'quality': {
                'total_issues': self.stats['total_issues'],
                'average_confidence': self._calculate_average_confidence(extracted_pages)
            },
            'pages': extracted_pages
        }

        # Save summary
        summary_file = self.output_dir / "extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Summary saved to: {summary_file}")

        # Generate review queue
        review_pages = [
            p for p in extracted_pages
            if p.get('verification', {}).get('requires_review', False)
        ]

        if review_pages:
            review_file = self.output_dir / "review_queue.json"
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump(review_pages, f, indent=2, default=str)

            logger.info(f"Review queue saved to: {review_file}")
            logger.info(f"{len(review_pages)} pages require manual review")

    def _calculate_average_confidence(self, pages: List[Dict]) -> float:
        """Calculate average confidence across all pages."""
        confidences = [
            p.get('verification', {}).get('confidence', 0)
            for p in pages
            if p.get('verification')
        ]

        return sum(confidences) / len(confidences) if confidences else 0.0

    def _print_summary(self):
        """Print extraction summary."""
        logger.info(f"\n{'='*60}")
        logger.info("EXTRACTION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Pages processed: {self.stats['pages_processed']}")
        logger.info(f"Pages successful: {self.stats['pages_successful']}")
        logger.info(f"Pages failed: {self.stats['pages_failed']}")
        logger.info(f"Pages need review: {self.stats['pages_need_review']}")
        logger.info(f"Total issues found: {self.stats['total_issues']}")
        logger.info(f"\nOutput directory: {self.output_dir}")
        logger.info(f"{'='*60}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract historical documents from Archive.org with maximum accuracy'
    )
    parser.add_argument(
        'identifier',
        help='Archive.org item identifier (e.g., in.ernet.dli.2015.208999)'
    )
    parser.add_argument(
        '--output',
        default='extracted_documents',
        help='Output directory (default: extracted_documents)'
    )
    parser.add_argument(
        '--pages',
        type=int,
        nargs='+',
        help='Specific pages to process (default: all)'
    )
    parser.add_argument(
        '--no-preprocessing',
        action='store_true',
        help='Disable image preprocessing'
    )
    parser.add_argument(
        '--no-verification',
        action='store_true',
        help='Disable text verification'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"extraction_{args.identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
        ]
    )

    # Create extractor
    extractor = ArchiveItemExtractor(
        identifier=args.identifier,
        output_dir=args.output,
        enable_preprocessing=not args.no_preprocessing,
        enable_verification=not args.no_verification
    )

    # Extract
    try:
        results = extractor.extract_full(pages=args.pages)
        return 0
    except KeyboardInterrupt:
        logger.warning("\nExtraction cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"\nExtraction failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
