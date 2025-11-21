"""
Main OCR Pipeline Orchestrator
Coordinates all stages: download -> preprocess -> OCR -> consensus -> clean -> verify
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
from PIL import Image

from archive_downloader import ArchiveDownloader
from image_preprocessor import ImagePreprocessor
from ocr_engines import OCREngineFactory, CompetitiveOCR
from consensus_engine import ConsensusEngine, EnsembleSelector
from text_cleaner import TextCleaner, SpellChecker
from quality_verifier import QualityVerifier
import ocr_config as config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OCRPipeline:
    """
    Complete OCR Pipeline - from raw images to clean text
    """

    def __init__(self, archive_item_id: str = None):
        self.archive_item_id = archive_item_id or config.ARCHIVE_ITEM_ID

        # Initialize components
        logger.info("Initializing OCR Pipeline...")

        self.downloader = ArchiveDownloader(
            self.archive_item_id,
            config.RAW_IMAGES_DIR
        )

        self.preprocessor = ImagePreprocessor(config.__dict__)

        # Create OCR engines
        logger.info("Initializing OCR engines...")
        engines = OCREngineFactory.create_engines(config.OCR_ENGINES)
        self.competitive_ocr = CompetitiveOCR(engines)

        # Consensus engine
        self.consensus_engine = EnsembleSelector()

        # Text cleaner
        self.text_cleaner = TextCleaner(config.__dict__)

        # Quality verifier
        self.quality_verifier = QualityVerifier(
            min_confidence=config.MIN_PAGE_CONFIDENCE
        )

        # Ensure directories exist
        for directory in [config.RAW_IMAGES_DIR, config.OCR_OUTPUTS_DIR,
                         config.CONSENSUS_DIR, config.FINAL_TEXT_DIR,
                         config.METADATA_DIR, config.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info("OCR Pipeline initialized successfully")

    def process_page(self, image_path: Path, page_number: int) -> Dict:
        """
        Process a single page through the complete pipeline
        Returns metadata about the processing
        """
        logger.info(f"Processing page {page_number}: {image_path}")

        try:
            # Load image
            image = Image.open(image_path)

            # Stage 1: Preprocess
            logger.info("Stage 1: Preprocessing image...")
            preprocessed = self.preprocessor.preprocess(image)

            # Save preprocessed image
            preprocessed_path = config.OCR_OUTPUTS_DIR / f"preprocessed_{page_number:04d}.jpg"
            preprocessed.save(preprocessed_path)

            # Stage 2: Competitive OCR
            logger.info("Stage 2: Running competitive OCR...")
            ocr_results = self.competitive_ocr.extract_all(preprocessed)

            # Save individual OCR results
            for result in ocr_results:
                output_path = config.OCR_OUTPUTS_DIR / f"page_{page_number:04d}_{result.engine_name}.txt"
                output_path.write_text(result.text)

            # Stage 3: Build consensus
            logger.info("Stage 3: Building consensus...")
            consensus = self.consensus_engine.select_best(ocr_results)

            # Save consensus
            consensus_path = config.CONSENSUS_DIR / f"page_{page_number:04d}.txt"
            consensus_path.write_text(consensus.text)

            # Stage 4: Clean text
            logger.info("Stage 4: Cleaning text...")
            cleaned = self.text_cleaner.clean(consensus.text)

            # Stage 5: Quality verification
            logger.info("Stage 5: Verifying quality...")
            quality_report = self.quality_verifier.verify(
                cleaned.text,
                metadata={
                    'page_number': page_number,
                    'consensus_confidence': consensus.confidence,
                    'agreement_score': consensus.agreement_score
                }
            )

            # Save final text
            final_path = config.FINAL_TEXT_DIR / f"page_{page_number:04d}.txt"
            final_path.write_text(cleaned.text)

            # Save metadata
            metadata = {
                'page_number': page_number,
                'image_path': str(image_path),
                'processed_at': datetime.now().isoformat(),
                'ocr_engines': [r.engine_name for r in ocr_results],
                'consensus': {
                    'confidence': consensus.confidence,
                    'agreement_score': consensus.agreement_score,
                    'method': consensus.metadata.get('method'),
                    'uncertain_regions_count': len(consensus.uncertain_regions)
                },
                'cleaning': {
                    'changes_made': len(cleaned.changes_made),
                    'quality_score': cleaned.quality_score
                },
                'quality_verification': {
                    'overall_score': quality_report.overall_score,
                    'checks_passed': quality_report.checks_passed,
                    'checks_failed': quality_report.checks_failed,
                    'warnings_count': len(quality_report.warnings),
                    'errors_count': len(quality_report.errors),
                    'uncertain_regions_count': len(quality_report.uncertain_regions)
                },
                'recommendations': quality_report.recommendations
            }

            metadata_path = config.METADATA_DIR / f"page_{page_number:04d}.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))

            logger.info(
                f"Page {page_number} processed successfully - "
                f"Quality: {quality_report.overall_score:.2f}, "
                f"Consensus: {consensus.confidence:.2f}"
            )

            return metadata

        except Exception as e:
            logger.error(f"Error processing page {page_number}: {e}", exc_info=True)
            return {
                'page_number': page_number,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }

    def process_sample(self, num_pages: int = 5) -> List[Dict]:
        """
        Process a sample of pages (for testing)
        """
        logger.info(f"Processing {num_pages} sample pages...")

        # Download sample pages
        image_paths = self.downloader.download_sample(num_pages)

        # Process each page
        results = []
        for i, image_path in enumerate(image_paths):
            result = self.process_page(image_path, i)
            results.append(result)

        # Generate summary report
        self._generate_summary_report(results, "sample_report.json")

        return results

    def process_all(self, start_page: int = 0, end_page: Optional[int] = None) -> List[Dict]:
        """
        Process all pages in the collection
        """
        # Get metadata
        metadata = self.downloader.get_metadata()
        total_pages = self.downloader.get_page_count(metadata)

        if end_page is None:
            end_page = total_pages

        logger.info(f"Processing pages {start_page} to {end_page} (total: {total_pages})")

        # Download all images (if not already downloaded)
        logger.info("Ensuring all images are downloaded...")
        image_paths = self.downloader.download_range(start_page, end_page)

        # Process each page
        results = []
        for page_num, image_path in enumerate(tqdm(image_paths, desc="Processing pages"), start=start_page):
            result = self.process_page(image_path, page_num)
            results.append(result)

            # Periodic checkpoint
            if (page_num + 1) % 10 == 0:
                self._generate_summary_report(results, f"checkpoint_{page_num+1}.json")

        # Generate final report
        self._generate_summary_report(results, "final_report.json")

        # Combine all pages into a single text file
        self._combine_pages()

        logger.info("Processing complete!")
        return results

    def _generate_summary_report(self, results: List[Dict], filename: str):
        """Generate summary report of processing"""
        report_path = config.LOGS_DIR / filename

        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_pages': len(results),
            'successful': sum(1 for r in results if 'error' not in r),
            'failed': sum(1 for r in results if 'error' in r),
            'archive_metadata': config.ARCHIVE_METADATA,
            'pages': results
        }

        # Calculate averages
        successful_results = [r for r in results if 'error' not in r]
        if successful_results:
            avg_quality = sum(
                r.get('quality_verification', {}).get('overall_score', 0)
                for r in successful_results
            ) / len(successful_results)

            avg_consensus = sum(
                r.get('consensus', {}).get('confidence', 0)
                for r in successful_results
            ) / len(successful_results)

            summary['averages'] = {
                'quality_score': avg_quality,
                'consensus_confidence': avg_consensus
            }

        report_path.write_text(json.dumps(summary, indent=2))
        logger.info(f"Summary report saved to {report_path}")

    def _combine_pages(self):
        """Combine all processed pages into a single document"""
        logger.info("Combining all pages into final document...")

        final_text_files = sorted(config.FINAL_TEXT_DIR.glob("page_*.txt"))

        combined_text = []
        for text_file in final_text_files:
            page_num = int(text_file.stem.split('_')[1])
            text = text_file.read_text()

            # Add page marker
            combined_text.append(f"\n\n--- Page {page_num} ---\n\n")
            combined_text.append(text)

        # Save combined document
        combined_path = config.BASE_DIR / "letters_from_abroad_complete.txt"
        combined_path.write_text(''.join(combined_text))

        logger.info(f"Combined document saved to {combined_path}")

        # Also save as markdown
        markdown_path = config.BASE_DIR / "letters_from_abroad_complete.md"
        markdown_content = self._format_as_markdown(''.join(combined_text))
        markdown_path.write_text(markdown_content)

        logger.info(f"Markdown version saved to {markdown_path}")

    def _format_as_markdown(self, text: str) -> str:
        """Format the combined text as clean markdown"""
        # Add front matter
        metadata = config.ARCHIVE_METADATA

        front_matter = f"""---
title: "{metadata['title']}"
author: "{metadata['author']}"
year: {metadata['year']}
language: {metadata['language']}
genre: {metadata['genre']}
source: "Internet Archive (in.ernet.dli.2015.97031)"
extracted_at: "{datetime.now().isoformat()}"
extraction_method: "Multi-Model Competitive OCR Pipeline"
---

# {metadata['title']}

**by {metadata['author']}** ({metadata['year']})

---

"""
        return front_matter + text


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Darwinian OCR Pipeline for Historical Letters"
    )
    parser.add_argument(
        '--mode',
        choices=['sample', 'all', 'range'],
        default='sample',
        help='Processing mode'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=5,
        help='Number of sample pages to process'
    )
    parser.add_argument(
        '--start-page',
        type=int,
        default=0,
        help='Start page for range mode'
    )
    parser.add_argument(
        '--end-page',
        type=int,
        default=None,
        help='End page for range mode'
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = OCRPipeline()

    # Run based on mode
    if args.mode == 'sample':
        logger.info(f"Running in SAMPLE mode ({args.sample_size} pages)")
        pipeline.process_sample(args.sample_size)

    elif args.mode == 'all':
        logger.info("Running in FULL mode (all pages)")
        pipeline.process_all()

    elif args.mode == 'range':
        logger.info(f"Running in RANGE mode (pages {args.start_page}-{args.end_page})")
        pipeline.process_all(args.start_page, args.end_page)


if __name__ == '__main__':
    main()
