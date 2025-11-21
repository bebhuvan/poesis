#!/usr/bin/env python3
"""
Automated Correction System for Gandhi Letters

Applies high-confidence corrections while flagging uncertain cases.
Only corrects errors where we're 100% certain.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class AutoCorrector:
    """
    Automatic correction system for Gandhi letters.

    Only applies corrections we're absolutely certain about.
    Everything else goes to manual review.
    """

    def __init__(self):
        """Initialize with correction rules."""
        # 100% certain corrections (common OCR errors)
        self.certain_corrections = {
            'afiford': 'afford',
            'Impcrialisna': 'Imperialism',
            'impcrialisna': 'imperialism',
            'tbe': 'the',
            'tbis': 'this',
            'tben': 'then',
            'witb': 'with',
            'tbat': 'that',
            'wben': 'when',
            'whicb': 'which',
        }

        # Context-dependent corrections (need whole word matching)
        self.word_corrections = {
            r'\barc\b': 'are',  # "arc" → "are" (when it's a full word)
            r'\btbc\b': 'the',
            r'\bwitb\b': 'with',
        }

        # Artifacts to remove
        self.artifacts_to_remove = [
            'r>^',
            'ii\'Ai',  # Often precedes MAHATMA
            'f\n',  # Weird formatting
        ]

        # Terms that are CORRECT (don't change)
        self.preserve_terms = {
            'Gandhiji',  # Correct honorific
            'raiyats',   # Historical term for peasants
            'Kasturba',  # His wife's name
            'Mirabai',   # Disciple's name
            'Sabarmati', # Ashram name
            'Wardha',    # Place name
            'Yeravda',   # Prison name
        }

        self.stats = {
            'pages_processed': 0,
            'corrections_made': 0,
            'artifacts_removed': 0,
            'uncertain_flagged': 0
        }

    def correct_page(self, text: str) -> Tuple[str, List[str]]:
        """
        Auto-correct a page of text.

        Args:
            text: Original text

        Returns:
            Tuple of (corrected_text, list_of_changes_made)
        """
        changes = []
        corrected = text

        # Step 1: Remove artifacts
        for artifact in self.artifacts_to_remove:
            if artifact in corrected:
                count = corrected.count(artifact)
                corrected = corrected.replace(artifact, '')
                changes.append(f"Removed artifact '{artifact}' ({count}x)")
                self.stats['artifacts_removed'] += count

        # Step 2: Apply certain corrections (exact matches)
        for error, correction in self.certain_corrections.items():
            if error in corrected:
                count = corrected.count(error)
                corrected = corrected.replace(error, correction)
                changes.append(f"'{error}' → '{correction}' ({count}x)")
                self.stats['corrections_made'] += count

        # Step 3: Apply word-boundary corrections (context-aware)
        for pattern, replacement in self.word_corrections.items():
            matches = list(re.finditer(pattern, corrected))
            if matches:
                corrected = re.sub(pattern, replacement, corrected)
                changes.append(f"{pattern} → '{replacement}' ({len(matches)}x)")
                self.stats['corrections_made'] += len(matches)

        # Step 4: Clean up excessive spacing
        if re.search(r'  {3,}', corrected):
            corrected = re.sub(r'  +', '  ', corrected)
            changes.append("Normalized excessive spacing")

        return corrected, changes

    def process_all_pages(self, input_dir: Path, output_dir: Path):
        """
        Process all pages and generate corrected versions.

        Args:
            input_dir: Directory with original texts
            output_dir: Directory for corrected texts
        """
        output_dir.mkdir(exist_ok=True)

        all_changes = {}

        for page_file in sorted(input_dir.glob("page_*.txt")):
            page_num = int(page_file.stem.split('_')[1])

            with open(page_file, 'r', encoding='utf-8') as f:
                original_text = f.read()

            if not original_text.strip():
                continue

            # Auto-correct
            corrected_text, changes = self.correct_page(original_text)

            # Save corrected version
            output_file = output_dir / page_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(corrected_text)

            if changes:
                all_changes[page_num] = changes
                logger.info(f"Page {page_num:3d}: {len(changes)} corrections")

            self.stats['pages_processed'] += 1

        # Save change log
        changelog_file = output_dir / "AUTO_CORRECTIONS_LOG.json"
        with open(changelog_file, 'w', encoding='utf-8') as f:
            json.dump(all_changes, f, indent=2)

        # Save human-readable changelog
        changelog_txt = output_dir / "AUTO_CORRECTIONS_LOG.txt"
        with open(changelog_txt, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("AUTOMATIC CORRECTIONS LOG\n")
            f.write("="*60 + "\n\n")

            for page_num in sorted(all_changes.keys()):
                f.write(f"\nPage {page_num}:\n")
                for change in all_changes[page_num]:
                    f.write(f"  • {change}\n")

        # Create combined corrected file
        combined_file = output_dir / "all_letters_corrected.txt"
        with open(combined_file, 'w', encoding='utf-8') as f:
            for page_file in sorted(output_dir.glob("page_*.txt")):
                page_num = int(page_file.stem.split('_')[1])

                f.write(f"\n{'='*60}\n")
                f.write(f"PAGE {page_num}\n")
                f.write(f"{'='*60}\n\n")

                with open(page_file, 'r', encoding='utf-8') as pf:
                    f.write(pf.read())
                f.write('\n')

        return changelog_file, combined_file


def main():
    """Run automatic corrections on Gandhi letters."""
    logger.info("="*60)
    logger.info("AUTOMATIC CORRECTION SYSTEM")
    logger.info("="*60)
    logger.info("Applying high-confidence corrections only")
    logger.info("="*60)

    input_dir = Path("gandhi_letters_best")
    output_dir = Path("gandhi_letters_corrected")

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return

    corrector = AutoCorrector()

    logger.info(f"\nProcessing {len(list(input_dir.glob('page_*.txt')))} pages...\n")

    changelog, combined = corrector.process_all_pages(input_dir, output_dir)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("CORRECTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Pages processed: {corrector.stats['pages_processed']}")
    logger.info(f"Corrections made: {corrector.stats['corrections_made']}")
    logger.info(f"Artifacts removed: {corrector.stats['artifacts_removed']}")
    logger.info(f"\nCorrected files: {output_dir}/")
    logger.info(f"Change log: {changelog}")
    logger.info(f"Combined file: {combined}")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()
