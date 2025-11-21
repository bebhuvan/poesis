#!/usr/bin/env python3
"""
Quick demo of the OCR pipeline
Downloads and processes a single page to show the system working
"""
import logging
from pathlib import Path
from PIL import Image
from archive_downloader import ArchiveDownloader
from image_preprocessor import ImagePreprocessor
from ocr_engines import OCREngineFactory, CompetitiveOCR
from consensus_engine import ConsensusEngine
from text_cleaner import TextCleaner
from quality_verifier import QualityVerifier
import ocr_config as config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run a quick demo"""
    print("=" * 70)
    print("Darwinian OCR Pipeline - Quick Demo")
    print("=" * 70)
    print()

    # Download one sample page
    print("[1/6] Downloading sample page from archive.org...")
    downloader = ArchiveDownloader(
        config.ARCHIVE_ITEM_ID,
        config.RAW_IMAGES_DIR
    )

    # Download just the first page
    print(f"  Source: {config.ARCHIVE_METADATA['title']} by {config.ARCHIVE_METADATA['author']}")
    image_path = config.RAW_IMAGES_DIR / "demo_page_0000.jpg"

    if not image_path.exists():
        image = downloader.download_page(0, size="full")
        if image:
            image.save(image_path)
            print(f"  ✓ Downloaded page 0 to {image_path}")
        else:
            print("  ✗ Failed to download page")
            return
    else:
        print(f"  ✓ Using cached page: {image_path}")
    print()

    # Load and preprocess
    print("[2/6] Preprocessing image...")
    image = Image.open(image_path)
    print(f"  Image size: {image.size}")

    preprocessor = ImagePreprocessor(config.__dict__)
    preprocessed = preprocessor.preprocess(image)

    preprocessed_path = config.OCR_OUTPUTS_DIR / "demo_preprocessed.jpg"
    preprocessed.save(preprocessed_path)
    print(f"  ✓ Preprocessed image saved to {preprocessed_path}")
    print()

    # Run OCR with available engines
    print("[3/6] Running OCR engines...")
    print("  Note: Only Tesseract is installed. For best results, install EasyOCR and TrOCR.")
    print("  Install with: pip install easyocr transformers torch")
    print()

    engines = OCREngineFactory.create_engines(config.OCR_ENGINES)
    competitive_ocr = CompetitiveOCR(engines)

    ocr_results = competitive_ocr.extract_all(preprocessed)

    for result in ocr_results:
        output_path = config.OCR_OUTPUTS_DIR / f"demo_{result.engine_name}.txt"
        output_path.write_text(result.text)
        print(f"  ✓ {result.engine_name}: {len(result.text)} chars, confidence: {result.confidence:.2f}")
        print(f"    Saved to: {output_path}")
    print()

    # Build consensus
    print("[4/6] Building consensus...")
    consensus_engine = ConsensusEngine(
        method=config.CONSENSUS_METHOD,
        min_agreement=config.MIN_AGREEMENT_THRESHOLD
    )

    consensus = consensus_engine.build_consensus(ocr_results)
    consensus_path = config.CONSENSUS_DIR / "demo_consensus.txt"
    consensus_path.write_text(consensus.text)

    print(f"  Confidence: {consensus.confidence:.2f}")
    print(f"  Agreement score: {consensus.agreement_score:.2f}")
    print(f"  Uncertain regions: {len(consensus.uncertain_regions)}")
    print(f"  ✓ Consensus saved to {consensus_path}")
    print()

    # Clean text
    print("[5/6] Cleaning text...")
    cleaner = TextCleaner(config.__dict__)
    cleaned = cleaner.clean(consensus.text)

    final_path = config.FINAL_TEXT_DIR / "demo_final.txt"
    final_path.write_text(cleaned.text)

    print(f"  Changes made: {len(cleaned.changes_made)}")
    for change in cleaned.changes_made[:3]:  # Show first 3 changes
        print(f"    - {change['stage']}: {change['description']}")
    print(f"  Quality score: {cleaned.quality_score:.2f}")
    print(f"  ✓ Final text saved to {final_path}")
    print()

    # Verify quality
    print("[6/6] Verifying quality...")
    verifier = QualityVerifier(min_confidence=config.MIN_PAGE_CONFIDENCE)
    quality_report = verifier.verify(cleaned.text, {
        'consensus_confidence': consensus.confidence,
        'agreement_score': consensus.agreement_score
    })

    print(f"  Overall score: {quality_report.overall_score:.2f}")
    print(f"  Checks passed: {quality_report.checks_passed}/{quality_report.checks_passed + quality_report.checks_failed}")
    print(f"  Warnings: {len(quality_report.warnings)}")
    print(f"  Errors: {len(quality_report.errors)}")
    print()

    print("  Recommendations:")
    for rec in quality_report.recommendations:
        print(f"    - {rec}")
    print()

    # Show preview
    print("=" * 70)
    print("Final Extracted Text (first 500 characters):")
    print("=" * 70)
    print(cleaned.text[:500])
    if len(cleaned.text) > 500:
        print("\n... (truncated)")
    print()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review the extracted text in:", final_path)
    print("  2. Check preprocessed image in:", preprocessed_path)
    print("  3. Compare OCR outputs in:", config.OCR_OUTPUTS_DIR)
    print()
    print("To process more pages:")
    print("  python ocr_pipeline.py --mode sample --sample-size 5")
    print()
    print("To install additional OCR engines for better results:")
    print("  pip install easyocr transformers torch opencv-python")
    print()


if __name__ == '__main__':
    main()
