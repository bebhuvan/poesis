#!/usr/bin/env python3
"""
Standalone demo using a generated test image
Shows the OCR pipeline working without needing archive.org
"""
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
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


def create_test_image():
    """Create a test image with sample text from a Tagore letter"""
    # Sample text from Tagore's writings
    sample_text = """
    My Dear Friend,

    I am writing to you from far away, where the
    mountains meet the sky and the rivers sing their
    ancient songs. The beauty of this place reminds
    me of the eternal truths we discussed in our
    last conversation.

    The world is vast, yet human hearts remain
    connected across distances through the bonds
    of friendship and shared understanding.

    With warm regards,
    Rabindranath Tagore
    """

    # Create a white image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Draw text (using default font)
    y_position = 50
    for line in sample_text.strip().split('\n'):
        draw.text((50, y_position), line.strip(), fill='black')
        y_position += 30

    return image


def main():
    """Run a quick demo with test image"""
    print("=" * 70)
    print("Darwinian OCR Pipeline - Standalone Demo")
    print("=" * 70)
    print()
    print("Note: Using generated test image (archive.org unavailable)")
    print()

    # Create test image
    print("[1/6] Creating test image...")
    image = create_test_image()
    image_path = config.RAW_IMAGES_DIR / "test_image.jpg"
    image.save(image_path)
    print(f"  ✓ Test image created: {image_path}")
    print(f"  Image size: {image.size}")
    print()

    # Preprocess
    print("[2/6] Preprocessing image...")
    preprocessor = ImagePreprocessor(config.__dict__)
    preprocessed = preprocessor.preprocess(image)

    preprocessed_path = config.OCR_OUTPUTS_DIR / "test_preprocessed.jpg"
    preprocessed.save(preprocessed_path)
    print(f"  ✓ Preprocessed image saved to {preprocessed_path}")
    print()

    # Run OCR
    print("[3/6] Running OCR engines...")
    print("  Available engines: Tesseract")
    print("  (Install easyocr, transformers, torch for more engines)")
    print()

    engines = OCREngineFactory.create_engines(config.OCR_ENGINES)
    competitive_ocr = CompetitiveOCR(engines)

    ocr_results = competitive_ocr.extract_all(preprocessed)

    for result in ocr_results:
        output_path = config.OCR_OUTPUTS_DIR / f"test_{result.engine_name}.txt"
        output_path.write_text(result.text)
        print(f"  ✓ {result.engine_name}:")
        print(f"      Characters: {len(result.text)}")
        print(f"      Confidence: {result.confidence:.2f}")
        print(f"      Time: {result.processing_time:.2f}s")
        print(f"      Saved to: {output_path.name}")
    print()

    # Build consensus
    print("[4/6] Building consensus...")
    consensus_engine = ConsensusEngine(
        method=config.CONSENSUS_METHOD,
        min_agreement=config.MIN_AGREEMENT_THRESHOLD
    )

    consensus = consensus_engine.build_consensus(ocr_results)
    consensus_path = config.CONSENSUS_DIR / "test_consensus.txt"
    consensus_path.write_text(consensus.text)

    print(f"  Method: {consensus.metadata.get('method')}")
    print(f"  Confidence: {consensus.confidence:.2f}")
    print(f"  Agreement score: {consensus.agreement_score:.2f}")
    print(f"  Contributing engines: {', '.join(consensus.contributing_engines)}")
    print(f"  ✓ Consensus saved to {consensus_path.name}")
    print()

    # Clean text
    print("[5/6] Cleaning text...")
    cleaner = TextCleaner(config.__dict__)
    cleaned = cleaner.clean(consensus.text)

    final_path = config.FINAL_TEXT_DIR / "test_final.txt"
    final_path.write_text(cleaned.text)

    print(f"  Cleaning stages applied:")
    for change in cleaned.changes_made:
        print(f"    - {change['stage']}: {change['description']}")

    print(f"  Quality score: {cleaned.quality_score:.2f}")
    print(f"  ✓ Final text saved to {final_path.name}")
    print()

    # Verify quality
    print("[6/6] Verifying quality...")
    verifier = QualityVerifier(min_confidence=config.MIN_PAGE_CONFIDENCE)
    quality_report = verifier.verify(cleaned.text, {
        'consensus_confidence': consensus.confidence,
        'agreement_score': consensus.agreement_score
    })

    print(f"  Overall quality score: {quality_report.overall_score:.2f}")
    print(f"  Checks passed: {quality_report.checks_passed}")
    print(f"  Checks failed: {quality_report.checks_failed}")
    print(f"  Warnings: {len(quality_report.warnings)}")
    print(f"  Errors: {len(quality_report.errors)}")

    if quality_report.warnings:
        print(f"\n  Warnings:")
        for warning in quality_report.warnings[:3]:
            print(f"    - {warning.get('message')}")

    print(f"\n  Recommendations:")
    for rec in quality_report.recommendations:
        print(f"    - {rec}")
    print()

    # Show final output
    print("=" * 70)
    print("Final Extracted Text:")
    print("=" * 70)
    print(cleaned.text)
    print("=" * 70)
    print()

    print("✅ Demo Complete!")
    print()
    print("File Outputs:")
    print(f"  - Original: {image_path}")
    print(f"  - Preprocessed: {preprocessed_path}")
    print(f"  - OCR results: {config.OCR_OUTPUTS_DIR}")
    print(f"  - Consensus: {consensus_path}")
    print(f"  - Final clean text: {final_path}")
    print()
    print("Pipeline Summary:")
    print(f"  ✓ Image preprocessing: {len(config.PREPROCESSING_STEPS)} stages")
    print(f"  ✓ OCR engines: {len(ocr_results)} engines")
    print(f"  ✓ Consensus method: {config.CONSENSUS_METHOD}")
    print(f"  ✓ Text cleaning: {len(cleaned.changes_made)} operations")
    print(f"  ✓ Quality checks: {quality_report.checks_passed + quality_report.checks_failed} checks")
    print()
    print("Next Steps:")
    print("  1. When archive.org is available, run:")
    print("     python ocr_pipeline.py --mode sample --sample-size 5")
    print()
    print("  2. Install advanced OCR engines:")
    print("     pip install easyocr transformers torch opencv-python")
    print()


if __name__ == '__main__':
    main()
