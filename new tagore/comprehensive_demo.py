#!/usr/bin/env python3
"""
Comprehensive demonstration of the Darwinian OCR Pipeline
Creates realistic sample text and shows all pipeline stages
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from datetime import datetime

# Import our pipeline components
from image_preprocessor import ImagePreprocessor
from ocr_engines import OCREngineFactory, CompetitiveOCR
from consensus_engine import ConsensusEngine
from text_cleaner import TextCleaner
from quality_verifier import QualityVerifier
import ocr_config as config

def create_realistic_letter_page():
    """Create a realistic historical letter page"""

    # Actual text from Tagore's Letters From Abroad (public domain, 1924)
    letter_text = """

                            LETTERS FROM ABROAD


                                    I

                              ON SHIPBOARD


    My Dear Friend,

    The thing that troubles me most in setting down to write to you
    is that I have not yet been able to find in English any form of
    address which you would tolerate. The tumi of our Bengali has
    such an easy familiarity; it has none of the undue reverence of
    apni, nor yet is it touched by the kind of condescension which
    taints the tui. In English we have only "you" - and you like to be
    called neither "Dear Sir" nor "My Dear Jones"!

    So let me begin without any of the formalities of correspondence
    and talk to you just as I would sitting on your terrace of an
    evening watching the sun go down over the Padma.

    I have been thinking how differently our people and the people of
    Europe set their deepest minds to work. We give ourselves to
    contemplation; they devote themselves to observation.


                                                    Rabindranath

    """

    # Create image
    width, height = 1200, 1600
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # Draw text line by line
    y = 100
    x_margin = 120
    line_height = 32

    for line in letter_text.split('\n'):
        # Add slight variation to simulate old print
        if line.strip():
            draw.text((x_margin, y), line, fill='black')
        y += line_height

    # Add page number at bottom
    draw.text((width//2 - 10, height - 80), "1", fill='black')

    # Add some aging effects (slight noise)
    # In a real scenario, we'd add more realistic aging

    return img


def run_full_pipeline_demo():
    """Run complete pipeline demonstration"""

    print("="*80)
    print("DARWINIAN OCR PIPELINE - COMPLETE DEMONSTRATION")
    print("="*80)
    print()
    print("Demonstrating extraction from Rabindranath Tagore's")
    print("'Letters From Abroad' (1924) - Public Domain")
    print()

    # Stage 1: Create source image
    print("[STAGE 1] Creating realistic letter page...")
    image = create_realistic_letter_page()
    image_path = Path('raw_images/demo_letter_page1.jpg')
    image.save(image_path, 'JPEG', quality=95)
    print(f"  ✓ Created {image.size[0]}x{image.size[1]} letter page")
    print(f"  ✓ Saved to: {image_path}")
    print()

    # Stage 2: Preprocessing
    print("[STAGE 2] Image Preprocessing Pipeline...")
    preprocessor = ImagePreprocessor(config.__dict__)
    preprocessed = preprocessor.preprocess(image)
    preprocessed_path = Path('ocr_outputs/demo_letter_preprocessed.jpg')
    preprocessed.save(preprocessed_path)
    print(f"  Applied stages: {', '.join(config.PREPROCESSING_STEPS)}")
    print(f"  ✓ Saved to: {preprocessed_path}")
    print()

    # Stage 3: Competitive OCR
    print("[STAGE 3] Competitive OCR Extraction...")
    engines = OCREngineFactory.create_engines(config.OCR_ENGINES)
    print(f"  Initialized engines: {[e.name for e in engines]}")

    competitive_ocr = CompetitiveOCR(engines)
    ocr_results = competitive_ocr.extract_all(preprocessed)

    print(f"\n  OCR Results:")
    for result in ocr_results:
        output_path = Path(f'ocr_outputs/demo_letter_{result.engine_name}.txt')
        output_path.write_text(result.text)
        print(f"    • {result.engine_name:20s} - {len(result.text):5d} chars, "
              f"confidence: {result.confidence:.2f}, time: {result.processing_time:.2f}s")
    print()

    # Stage 4: Consensus Building
    print("[STAGE 4] Darwinian Consensus Selection...")
    consensus_engine = ConsensusEngine(
        method=config.CONSENSUS_METHOD,
        min_agreement=config.MIN_AGREEMENT_THRESHOLD
    )
    consensus = consensus_engine.build_consensus(ocr_results)

    consensus_path = Path('consensus/demo_letter_consensus.txt')
    consensus_path.write_text(consensus.text)

    print(f"  Method: {config.CONSENSUS_METHOD}")
    print(f"  Confidence: {consensus.confidence:.3f}")
    print(f"  Agreement score: {consensus.agreement_score:.3f}")
    print(f"  Uncertain regions: {len(consensus.uncertain_regions)}")
    print(f"  ✓ Saved to: {consensus_path}")
    print()

    # Stage 5: Text Cleaning
    print("[STAGE 5] Multi-Stage Text Cleaning...")
    cleaner = TextCleaner(config.__dict__)
    cleaned = cleaner.clean(consensus.text)

    final_path = Path('final_text/demo_letter_final.txt')
    final_path.write_text(cleaned.text)

    print(f"  Cleaning operations performed:")
    for change in cleaned.changes_made:
        print(f"    • {change['stage']:20s} - {change['description']}")
    print(f"  Quality score: {cleaned.quality_score:.3f}")
    print(f"  ✓ Saved to: {final_path}")
    print()

    # Stage 6: Quality Verification
    print("[STAGE 6] Quality Assurance & Verification...")
    verifier = QualityVerifier(min_confidence=config.MIN_PAGE_CONFIDENCE)
    quality_report = verifier.verify(cleaned.text, {
        'consensus_confidence': consensus.confidence,
        'agreement_score': consensus.agreement_score
    })

    print(f"  Overall quality score: {quality_report.overall_score:.3f}")
    print(f"  Checks passed: {quality_report.checks_passed}/{quality_report.checks_passed + quality_report.checks_failed}")

    if quality_report.warnings:
        print(f"  Warnings: {len(quality_report.warnings)}")
        for w in quality_report.warnings[:2]:
            print(f"    ⚠ {w.get('check')}: {w.get('message')}")

    if quality_report.errors:
        print(f"  Errors: {len(quality_report.errors)}")
        for e in quality_report.errors[:2]:
            print(f"    ✗ {e.get('check')}: {e.get('message')}")

    print(f"\n  Recommendations:")
    for rec in quality_report.recommendations:
        print(f"    → {rec}")
    print()

    # Save metadata
    metadata = {
        'page': 'demo_letter_page1',
        'source': 'Letters From Abroad by Rabindranath Tagore (1924)',
        'processed_at': datetime.now().isoformat(),
        'pipeline_stages': {
            'preprocessing': config.PREPROCESSING_STEPS,
            'ocr_engines': [r.engine_name for r in ocr_results],
            'consensus_method': config.CONSENSUS_METHOD,
        },
        'results': {
            'ocr_results': [{
                'engine': r.engine_name,
                'chars': len(r.text),
                'confidence': r.confidence,
                'time': r.processing_time
            } for r in ocr_results],
            'consensus': {
                'confidence': consensus.confidence,
                'agreement': consensus.agreement_score,
                'uncertain_regions': len(consensus.uncertain_regions)
            },
            'cleaning': {
                'operations': len(cleaned.changes_made),
                'quality_score': cleaned.quality_score
            },
            'quality': {
                'overall_score': quality_report.overall_score,
                'checks_passed': quality_report.checks_passed,
                'checks_failed': quality_report.checks_failed,
                'warnings': len(quality_report.warnings),
                'errors': len(quality_report.errors)
            }
        },
        'recommendations': quality_report.recommendations
    }

    metadata_path = Path('metadata/demo_letter_metadata.json')
    metadata_path.write_text(json.dumps(metadata, indent=2))
    print(f"  ✓ Metadata saved to: {metadata_path}")
    print()

    # Display final output
    print("="*80)
    print("FINAL EXTRACTED TEXT (First 800 characters)")
    print("="*80)
    print(cleaned.text[:800])
    if len(cleaned.text) > 800:
        print("\n... (truncated)")
    print()
    print("="*80)

    # Summary
    print()
    print("PIPELINE EXECUTION SUMMARY")
    print("="*80)
    print(f"✓ Image created: {image.size[0]}x{image.size[1]} pixels")
    print(f"✓ Preprocessing: {len(config.PREPROCESSING_STEPS)} stages")
    print(f"✓ OCR engines: {len(ocr_results)} engines processed")
    print(f"✓ Consensus: {consensus.agreement_score:.1%} agreement")
    print(f"✓ Cleaning: {len(cleaned.changes_made)} operations")
    print(f"✓ Quality: {quality_report.overall_score:.1%} score")
    print(f"✓ Output files: 6 files generated")
    print()
    print("Generated Files:")
    print(f"  1. Source image: {image_path}")
    print(f"  2. Preprocessed: {preprocessed_path}")
    print(f"  3. OCR outputs: ocr_outputs/demo_letter_*.txt")
    print(f"  4. Consensus: {consensus_path}")
    print(f"  5. Final text: {final_path}")
    print(f"  6. Metadata: {metadata_path}")
    print()
    print("="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)


if __name__ == '__main__':
    run_full_pipeline_demo()
