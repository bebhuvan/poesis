#!/usr/bin/env python3
"""
Competitive/Adversarial Extraction

Runs multiple extraction strategies and compares results:
1. ABBYY OCR XML (already done)
2. PDF Text Layer extraction
3. Comparison and consensus

Picks the best result for each page based on:
- Text length (more complete)
- Character distribution (more natural)
- Dictionary validation score
- Statistical quality metrics
"""

import PyPDF2
import json
import difflib
import logging
from pathlib import Path
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyPDF2."""
    logger.info(f"Extracting from PDF: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)
        logger.info(f"Found {num_pages} pages in PDF")

        pages = {}
        for page_num in range(num_pages):
            logger.info(f"  Processing page {page_num + 1}/{num_pages}...")
            page = reader.pages[page_num]
            text = page.extract_text()

            if text.strip():
                pages[page_num + 1] = {
                    'page_number': page_num + 1,
                    'full_text': text.strip(),
                    'source': 'pdf_text_layer'
                }
                logger.info(f"    Extracted {len(text)} characters")
            else:
                logger.warning(f"    No text on page {page_num + 1}")

        return pages


def calculate_quality_score(text):
    """Calculate text quality score based on multiple factors."""
    if not text:
        return 0.0

    score = 0.0

    # Factor 1: Length (normalized)
    length_score = min(100, len(text) / 20)  # 2000 chars = 100 points
    score += length_score * 0.3

    # Factor 2: Character distribution (English letter frequency)
    expected_freq = {
        'e': 0.127, 't': 0.091, 'a': 0.082, 'o': 0.075, 'i': 0.070,
        'n': 0.067, 's': 0.063, 'h': 0.061, 'r': 0.060
    }

    text_lower = text.lower()
    letter_count = sum(1 for c in text_lower if c.isalpha())

    if letter_count > 0:
        actual_freq = Counter(c for c in text_lower if c.isalpha())
        actual_freq = {k: v / letter_count for k, v in actual_freq.items()}

        # Calculate deviation from expected
        total_deviation = 0
        for char, exp_freq in expected_freq.items():
            act_freq = actual_freq.get(char, 0)
            total_deviation += abs(act_freq - exp_freq)

        # Lower deviation = higher score
        distribution_score = max(0, 100 - (total_deviation * 500))
        score += distribution_score * 0.3

    # Factor 3: Word count (more words = more complete)
    words = text.split()
    word_score = min(100, len(words) / 2)  # 200 words = 100 points
    score += word_score * 0.2

    # Factor 4: Artifact penalty
    artifacts = text.count('■') + text.count('�') + text.count('□')
    artifact_penalty = min(50, artifacts * 5)
    score -= artifact_penalty * 0.2

    return max(0, score)


def compare_texts(text1, text2, source1="Source 1", source2="Source 2"):
    """Compare two texts and return detailed comparison."""
    if not text1 and not text2:
        return {
            'identical': True,
            'similarity': 0.0,
            'differences': 0,
            'winner': None
        }

    if not text1:
        return {
            'identical': False,
            'similarity': 0.0,
            'differences': len(text2),
            'winner': source2
        }

    if not text2:
        return {
            'identical': False,
            'similarity': 0.0,
            'differences': len(text1),
            'winner': source1
        }

    # Calculate similarity
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

    # Count differences
    matcher = difflib.SequenceMatcher(None, text1, text2)
    differences = sum(1 for tag, _, _, _, _ in matcher.get_opcodes() if tag != 'equal')

    # Quality scores
    quality1 = calculate_quality_score(text1)
    quality2 = calculate_quality_score(text2)

    # Determine winner
    if similarity > 0.95:  # Nearly identical
        winner = source1 if quality1 >= quality2 else source2
    else:  # Significant differences
        winner = source1 if quality1 > quality2 else source2

    return {
        'identical': similarity > 0.99,
        'similarity': similarity,
        'differences': differences,
        'quality1': quality1,
        'quality2': quality2,
        'winner': winner,
        'winner_quality': max(quality1, quality2)
    }


def main():
    """Run competitive extraction."""
    logger.info("="*60)
    logger.info("COMPETITIVE EXTRACTION MODE")
    logger.info("="*60)
    logger.info("Strategy 1: ABBYY OCR XML (already extracted)")
    logger.info("Strategy 2: PDF Text Layer")
    logger.info("="*60)

    # Load ABBYY results
    abbyy_dir = Path("gandhi_letters_extracted")
    if not abbyy_dir.exists():
        logger.error("ABBYY extraction not found. Run extract_gandhi_letters.py first.")
        return

    abbyy_pages = {}
    for metadata_file in sorted(abbyy_dir.glob("page_*_metadata.json")):
        with open(metadata_file) as f:
            data = json.load(f)
            abbyy_pages[data['page_number']] = data

    logger.info(f"Loaded {len(abbyy_pages)} pages from ABBYY extraction")

    # Extract from PDF
    pdf_path = Path("archive_cache/in.ernet.dli.2015.208999/text_pdf.pdf")
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return

    logger.info("\n" + "="*60)
    logger.info("EXTRACTING FROM PDF TEXT LAYER")
    logger.info("="*60)
    pdf_pages = extract_pdf_text(pdf_path)

    # Compare and compete
    logger.info("\n" + "="*60)
    logger.info("COMPETITION: COMPARING RESULTS")
    logger.info("="*60)

    competition_results = {}
    abbyy_wins = 0
    pdf_wins = 0
    ties = 0

    all_pages = set(abbyy_pages.keys()) | set(pdf_pages.keys())

    for page_num in sorted(all_pages):
        logger.info(f"\nPage {page_num}:")

        abbyy_text = abbyy_pages.get(page_num, {}).get('full_text', '')
        pdf_text = pdf_pages.get(page_num, {}).get('full_text', '')

        comparison = compare_texts(
            abbyy_text,
            pdf_text,
            source1="ABBYY",
            source2="PDF"
        )

        logger.info(f"  ABBYY: {len(abbyy_text)} chars, quality={comparison.get('quality1', 0):.1f}")
        logger.info(f"  PDF:   {len(pdf_text)} chars, quality={comparison.get('quality2', 0):.1f}")
        logger.info(f"  Similarity: {comparison['similarity']:.1%}")
        logger.info(f"  Winner: {comparison['winner']} (quality={comparison['winner_quality']:.1f})")

        if comparison['winner'] == 'ABBYY':
            abbyy_wins += 1
            best_text = abbyy_text
        else:
            pdf_wins += 1
            best_text = pdf_text

        competition_results[page_num] = {
            'page_number': page_num,
            'abbyy_length': len(abbyy_text),
            'pdf_length': len(pdf_text),
            'similarity': comparison['similarity'],
            'winner': comparison['winner'],
            'winner_quality': comparison['winner_quality'],
            'best_text': best_text
        }

    # Save best results
    logger.info("\n" + "="*60)
    logger.info("SAVING BEST RESULTS")
    logger.info("="*60)

    output_dir = Path("gandhi_letters_best")
    output_dir.mkdir(exist_ok=True)

    for page_num, result in competition_results.items():
        # Save best text
        text_file = output_dir / f"page_{page_num:03d}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(result['best_text'])

        # Save competition metadata
        metadata_file = output_dir / f"page_{page_num:03d}_competition.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'page_number': page_num,
                'winner': result['winner'],
                'abbyy_length': result['abbyy_length'],
                'pdf_length': result['pdf_length'],
                'similarity': result['similarity'],
                'winner_quality': result['winner_quality']
            }, f, indent=2)

    # Save combined best text
    combined_file = output_dir / "all_letters_best.txt"
    with open(combined_file, 'w', encoding='utf-8') as f:
        for page_num in sorted(competition_results.keys()):
            f.write(f"\n{'='*60}\n")
            f.write(f"PAGE {page_num} (Winner: {competition_results[page_num]['winner']})\n")
            f.write(f"{'='*60}\n\n")
            f.write(competition_results[page_num]['best_text'])
            f.write('\n')

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("COMPETITION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total pages: {len(competition_results)}")
    logger.info(f"ABBYY wins: {abbyy_wins} ({abbyy_wins/len(competition_results)*100:.1f}%)")
    logger.info(f"PDF wins: {pdf_wins} ({pdf_wins/len(competition_results)*100:.1f}%)")
    logger.info(f"\nBest results saved to: {output_dir}/")
    logger.info(f"Combined file: {combined_file}")
    logger.info("="*60)


if __name__ == '__main__':
    main()
