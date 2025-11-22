#!/usr/bin/env python3
"""
Main OCR pipeline orchestrator.
Runs all strategies in parallel and produces final output.
"""

import sys
from pathlib import Path
import json
from typing import List, Dict
import time
from multiprocessing import Pool, cpu_count
import fitz  # PyMuPDF
from PIL import Image

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ocr_engine_base import OCRStrategy, OCROrchestrator, PageOCRResults
from ocr_engines import create_tesseract_engines, create_all_engines
from preprocessors import get_recommended_preprocessors, get_all_preprocessors
from quality_scorer import QualityScorer
from llm_postprocessor import LLMPostProcessor, SimplePostProcessor


class NehruLettersPipeline:
    """
    Complete pipeline for extracting Nehru's letters with multiple OCR strategies.
    """

    def __init__(
        self,
        pdf_path: Path,
        output_dir: Path,
        use_llm: bool = True,
        use_gpu: bool = False,
        num_strategies: str = "recommended"  # "recommended", "all", or "tesseract_only"
    ):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.use_llm = use_llm
        self.use_gpu = use_gpu
        self.num_strategies = num_strategies

        # Create output directories
        self.pages_dir = self.output_dir / "pages"
        self.ocr_dir = self.output_dir / "ocr_results"
        self.processed_dir = self.output_dir / "processed"
        self.reviews_dir = self.output_dir / "reviews"
        self.final_dir = self.output_dir / "final"

        for directory in [self.pages_dir, self.ocr_dir, self.processed_dir,
                         self.reviews_dir, self.final_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.scorer = QualityScorer()
        self.postprocessor = None
        if use_llm:
            try:
                self.postprocessor = LLMPostProcessor()
                print("✓ LLM post-processor initialized")
            except Exception as e:
                print(f"⚠ LLM post-processor unavailable: {e}")
                print("  Using simple post-processor instead")
                self.postprocessor = SimplePostProcessor()
        else:
            self.postprocessor = SimplePostProcessor()

        # Build strategies
        self.strategies = self._build_strategies()
        print(f"✓ Created {len(self.strategies)} OCR strategies")

    def _build_strategies(self) -> List[OCRStrategy]:
        """Build all OCR strategies."""
        strategies = []

        # Get engines
        if self.num_strategies == "tesseract_only":
            engines = create_tesseract_engines()
            preprocessors = get_recommended_preprocessors()
        elif self.num_strategies == "all":
            engines = create_all_engines(use_gpu=self.use_gpu)
            preprocessors = get_all_preprocessors()
        else:  # recommended
            engines = create_all_engines(use_gpu=self.use_gpu)
            preprocessors = get_recommended_preprocessors()

        # Create strategy combinations
        # For Tesseract, use all preprocessors
        tesseract_engines = [e for e in engines if e.name.startswith("tesseract")]
        other_engines = [e for e in engines if not e.name.startswith("tesseract")]

        # Tesseract + all preprocessors
        for engine in tesseract_engines:
            for prep in preprocessors:
                strategies.append(OCRStrategy(engine, prep))

        # Other engines + just a few best preprocessors
        best_preps = preprocessors[:3]  # Top 3 preprocessors
        for engine in other_engines:
            for prep in best_preps:
                strategies.append(OCRStrategy(engine, prep))

        return strategies

    def extract_pages(self, dpi: int = 300) -> List[Path]:
        """
        Extract all pages from PDF as images.

        Args:
            dpi: DPI for extraction

        Returns:
            List of paths to extracted page images
        """
        print(f"\n📄 Extracting pages from PDF at {dpi} DPI...")

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        doc = fitz.open(self.pdf_path)
        page_paths = []

        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)

            # Save as PNG
            output_path = self.pages_dir / f"page_{page_num:03d}.png"
            pix.save(str(output_path))
            page_paths.append(output_path)

            if (page_num + 1) % 10 == 0:
                print(f"  Extracted {page_num + 1}/{len(doc)} pages...")

        doc.close()
        print(f"✓ Extracted {len(page_paths)} pages to {self.pages_dir}")

        return page_paths

    def process_page(self, page_num: int, image_path: Path) -> Dict:
        """
        Process a single page with all strategies.

        Args:
            page_num: Page number
            image_path: Path to page image

        Returns:
            Dict with results
        """
        print(f"\n📖 Processing Page {page_num}...")
        print(f"   Running {len(self.strategies)} OCR strategies...")

        orchestrator = OCROrchestrator(self.strategies)
        page_results = orchestrator.process_page(page_num, image_path)

        # Score all results
        print(f"   Scoring results...")
        scored = []
        for result in page_results.results:
            score = self.scorer.score(result.text, result.confidence)
            scored.append((result.full_name, result.text, result.confidence, score))

        # Sort by score
        scored.sort(key=lambda x: x[3].total_score, reverse=True)

        # Get top 3
        top_3 = scored[:3]

        print(f"\n   🏆 Top 3 Results:")
        for i, (name, text, conf, score) in enumerate(top_3, 1):
            print(f"   {i}. {name}: {score}")

        # Apply LLM post-processing to best result
        best_name, best_text, best_conf, best_score = top_3[0]

        print(f"\n   🤖 Applying post-processing...")
        if isinstance(self.postprocessor, LLMPostProcessor):
            pp_result = self.postprocessor.process_page(
                best_text,
                page_num,
                context="Letters from a Father to His Daughter by Jawaharlal Nehru",
                fast_mode=False
            )
            final_text = pp_result.corrected_text
            print(f"   ✓ LLM made {len(pp_result.changes_made)} changes")
        else:
            pp_result = self.postprocessor.process_page(best_text, page_num)
            final_text = pp_result.corrected_text
            print(f"   ✓ Simple processing complete")

        # Save results
        page_result = {
            'page_number': page_num,
            'image_path': str(image_path),
            'all_strategies': [
                {
                    'name': name,
                    'confidence': conf,
                    'score': {
                        'total': score.total_score,
                        'ocr_confidence': score.ocr_confidence,
                        'readability': score.readability,
                        'artifact_score': score.artifact_score,
                        'layout_score': score.layout_score,
                    },
                    'text_length': len(text)
                }
                for name, text, conf, score in scored
            ],
            'best_strategy': best_name,
            'best_score': best_score.total_score,
            'postprocessing': {
                'changes_made': pp_result.changes_made,
                'artifacts_removed': pp_result.artifacts_removed,
                'confidence_notes': pp_result.confidence_notes
            },
            'final_text': final_text
        }

        # Save to file
        result_file = self.ocr_dir / f"page_{page_num:03d}.json"
        with open(result_file, 'w') as f:
            json.dump(page_result, f, indent=2)

        # Save final text
        text_file = self.processed_dir / f"page_{page_num:03d}.txt"
        text_file.write_text(final_text)

        orchestrator.cleanup()

        return page_result

    def process_all_pages(self, page_paths: List[Path], parallel: bool = False) -> List[Dict]:
        """
        Process all pages.

        Args:
            page_paths: List of page image paths
            parallel: Use multiprocessing (experimental)

        Returns:
            List of page results
        """
        print(f"\n🚀 Processing {len(page_paths)} pages...")
        print(f"   Parallel: {parallel}")

        results = []

        if parallel:
            # Multiprocessing (might have issues with some OCR engines)
            with Pool(processes=min(4, cpu_count())) as pool:
                args = [(i, path) for i, path in enumerate(page_paths)]
                results = pool.starmap(self.process_page, args)
        else:
            # Sequential processing (more reliable)
            for i, path in enumerate(page_paths):
                result = self.process_page(i, path)
                results.append(result)

        print(f"\n✓ Processed all {len(results)} pages")
        return results

    def generate_summary_report(self, results: List[Dict]) -> Path:
        """Generate summary report of entire processing run."""
        print("\n📊 Generating summary report...")

        report = {
            'total_pages': len(results),
            'strategies_used': len(self.strategies),
            'strategy_names': [s.name for s in self.strategies],
            'postprocessing': 'LLM' if isinstance(self.postprocessor, LLMPostProcessor) else 'Simple',
            'page_summaries': []
        }

        # Collect stats
        strategy_wins = {}
        total_score = 0
        total_changes = 0

        for result in results:
            best_strat = result['best_strategy']
            strategy_wins[best_strat] = strategy_wins.get(best_strat, 0) + 1
            total_score += result['best_score']
            total_changes += len(result['postprocessing']['changes_made'])

            report['page_summaries'].append({
                'page': result['page_number'],
                'best_strategy': best_strat,
                'score': result['best_score'],
                'changes': len(result['postprocessing']['changes_made'])
            })

        report['strategy_wins'] = strategy_wins
        report['average_score'] = total_score / len(results) if results else 0
        report['total_postprocessing_changes'] = total_changes

        # Save report
        report_path = self.output_dir / "PROCESSING_SUMMARY.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Summary saved to {report_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Pages processed: {report['total_pages']}")
        print(f"Strategies used: {report['strategies_used']}")
        print(f"Average score: {report['average_score']:.1f}/100")
        print(f"Post-processing changes: {total_changes}")
        print(f"\nStrategy wins:")
        for strat, wins in sorted(strategy_wins.items(), key=lambda x: x[1], reverse=True):
            print(f"  {strat}: {wins} pages")
        print("=" * 60)

        return report_path

    def combine_final_text(self, results: List[Dict]) -> Path:
        """Combine all pages into single text file."""
        print("\n📝 Combining final text...")

        combined_text = []

        for result in sorted(results, key=lambda x: x['page_number']):
            page_num = result['page_number']
            text = result['final_text']

            combined_text.append(f"\n{'=' * 60}")
            combined_text.append(f"PAGE {page_num}")
            combined_text.append(f"{'=' * 60}\n")
            combined_text.append(text)

        final_path = self.final_dir / "all_pages_combined.txt"
        final_path.write_text('\n'.join(combined_text))

        print(f"✓ Combined text saved to {final_path}")
        return final_path


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Nehru Letters OCR Pipeline")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM post-processing")
    parser.add_argument("--gpu", action="store_true", help="Use GPU for OCR engines")
    parser.add_argument("--strategies", choices=["recommended", "all", "tesseract_only"],
                       default="recommended", help="Number of strategies to use")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for page extraction")
    parser.add_argument("--pages", help="Page range (e.g., '0-10' or '5,7,9')")

    args = parser.parse_args()

    # Create pipeline
    pipeline = NehruLettersPipeline(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        use_llm=not args.no_llm,
        use_gpu=args.gpu,
        num_strategies=args.strategies
    )

    # Extract pages
    page_paths = pipeline.extract_pages(dpi=args.dpi)

    # Filter pages if range specified
    if args.pages:
        if '-' in args.pages:
            start, end = map(int, args.pages.split('-'))
            page_paths = page_paths[start:end+1]
        else:
            indices = [int(x) for x in args.pages.split(',')]
            page_paths = [page_paths[i] for i in indices]

    # Process pages
    start_time = time.time()
    results = pipeline.process_all_pages(page_paths, parallel=False)
    elapsed = time.time() - start_time

    # Generate reports
    pipeline.generate_summary_report(results)
    pipeline.combine_final_text(results)

    print(f"\n✅ Pipeline complete in {elapsed:.1f} seconds ({elapsed/len(results):.1f}s per page)")
    print(f"📁 Output directory: {pipeline.output_dir}")


if __name__ == "__main__":
    main()
