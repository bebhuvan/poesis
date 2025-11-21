#!/usr/bin/env python3
"""
Competitive Multi-Strategy OCR System for Historical Documents.

This system runs multiple OCR strategies in parallel and automatically
grades them to select the best output.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import difflib
import subprocess
import sys

@dataclass
class OCRResult:
    """Container for OCR results from a single strategy."""
    strategy_name: str
    text: str
    confidence: float
    word_count: int
    char_count: int
    artifacts_score: float  # Lower is better
    readability_score: float  # Higher is better
    layout_score: float  # Higher is better
    processing_time: float
    metadata: Dict = None
    
    def overall_score(self) -> float:
        """Calculate overall quality score (0-100, higher is better)."""
        # Weighted combination of metrics
        score = (
            self.confidence * 30 +
            (100 - self.artifacts_score) * 25 +
            self.readability_score * 25 +
            self.layout_score * 20
        ) / 100
        return score * 100

@dataclass
class CompetitionResult:
    """Results from comparing multiple OCR strategies."""
    winner: str
    scores: Dict[str, float]
    all_results: List[OCRResult]
    consensus_text: str
    improvement_over_baseline: float


class OCRStrategy:
    """Base class for OCR strategies."""
    
    def __init__(self, name: str):
        self.name = name
    
    def process(self, image_path: Path) -> OCRResult:
        """Process image and return OCR result."""
        raise NotImplementedError
    
    def calculate_artifacts_score(self, text: str) -> float:
        """Calculate artifact score (0-100, lower is better)."""
        artifacts = {
            'mixed_case': len(re.findall(r'\b[a-z]+[A-Z]+[a-z]*\b', text)),
            'single_chars': len(re.findall(r'\b[a-zA-Z]\b', text)),
            'numbers_in_words': len(re.findall(r'\b[a-zA-Z]+\d+\b', text)),
            'special_chars': len(re.findall(r'[^\w\s\.,!?;:\-\'\"()\[\]]', text)),
            'repeated_chars': len(re.findall(r'(.)\1{3,}', text)),
        }
        
        total_artifacts = sum(artifacts.values())
        words = len(text.split())
        
        if words == 0:
            return 100.0
        
        artifact_ratio = (total_artifacts / max(words, 1)) * 100
        return min(artifact_ratio * 10, 100.0)  # Normalize to 0-100
    
    def calculate_readability_score(self, text: str) -> float:
        """Calculate readability score (0-100, higher is better)."""
        words = text.split()
        if len(words) == 0:
            return 0.0
        
        # Average word length (optimal around 5-6 chars)
        avg_word_len = sum(len(w) for w in words) / len(words)
        word_len_score = max(0, 100 - abs(avg_word_len - 5.5) * 10)
        
        # Sentence structure (check for punctuation)
        sentences = len(re.findall(r'[.!?]', text))
        sentence_score = min((sentences / max(len(words) / 15, 1)) * 100, 100)
        
        # Dictionary word ratio (basic English check)
        common_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 
                       'I', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
                       'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
                       'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one',
                       'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out'}
        
        word_set = set(w.lower() for w in words if len(w) > 1)
        common_ratio = len(word_set & common_words) / max(len(word_set), 1)
        dict_score = common_ratio * 100
        
        return (word_len_score * 0.3 + sentence_score * 0.3 + dict_score * 0.4)
    
    def calculate_layout_score(self, text: str) -> float:
        """Calculate layout quality score (0-100, higher is better)."""
        lines = text.split('\n')
        non_empty = [l for l in lines if l.strip()]
        
        if len(non_empty) == 0:
            return 0.0
        
        # Paragraph structure (groups of lines separated by blanks)
        paragraphs = len(re.findall(r'\n\s*\n', text))
        para_score = min((paragraphs / max(len(non_empty) / 5, 1)) * 100, 100)
        
        # Line length variance (consistent lines are better)
        line_lengths = [len(l) for l in non_empty]
        if len(line_lengths) > 1:
            avg_len = sum(line_lengths) / len(line_lengths)
            variance = sum((l - avg_len) ** 2 for l in line_lengths) / len(line_lengths)
            std_dev = variance ** 0.5
            consistency_score = max(0, 100 - (std_dev / max(avg_len, 1)) * 100)
        else:
            consistency_score = 50
        
        # Indentation detection (better structured text)
        indented = len([l for l in non_empty if l.startswith((' ', '\t'))])
        indent_score = min((indented / max(len(non_empty), 1)) * 200, 100)
        
        return (para_score * 0.4 + consistency_score * 0.3 + indent_score * 0.3)


class TesseractStrategy(OCRStrategy):
    """Strategy using Tesseract OCR with various configurations."""
    
    def __init__(self, config: str = "default"):
        super().__init__(f"Tesseract_{config}")
        self.config = config
    
    def preprocess_image(self, image_path: Path, output_path: Path):
        """Preprocess image based on configuration."""
        from PIL import Image, ImageEnhance, ImageFilter
        
        img = Image.open(image_path)
        
        if self.config == "grayscale":
            img = img.convert('L')
        elif self.config == "enhanced":
            img = img.convert('L')
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
        elif self.config == "denoised":
            img = img.convert('L')
            img = img.filter(ImageFilter.MedianFilter(size=3))
        elif self.config == "binarized":
            img = img.convert('L')
            threshold = 128
            img = img.point(lambda p: 255 if p > threshold else 0)
        
        img.save(output_path)
        return output_path
    
    def process(self, image_path: Path) -> OCRResult:
        """Process image with Tesseract."""
        import time
        import tempfile
        
        start_time = time.time()
        
        # Preprocess if needed
        if self.config != "default":
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                processed_path = Path(tmp.name)
            self.preprocess_image(image_path, processed_path)
        else:
            processed_path = image_path
        
        # Run Tesseract
        try:
            result = subprocess.run(
                ['tesseract', str(processed_path), 'stdout', '--psm', '6'],
                capture_output=True,
                text=True,
                timeout=60
            )
            text = result.stdout
            
            # Try to get confidence from TSV output
            tsv_result = subprocess.run(
                ['tesseract', str(processed_path), 'stdout', '--psm', '6', 'tsv'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse confidence from TSV
            confidences = []
            for line in tsv_result.stdout.split('\n')[1:]:  # Skip header
                fields = line.split('\t')
                if len(fields) > 10 and fields[10].strip():
                    try:
                        conf = float(fields[10])
                        if conf >= 0:
                            confidences.append(conf)
                    except ValueError:
                        pass
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 50.0
            
        except subprocess.TimeoutExpired:
            text = ""
            avg_confidence = 0.0
        except Exception as e:
            text = f"Error: {e}"
            avg_confidence = 0.0
        
        # Clean up temp file
        if processed_path != image_path:
            processed_path.unlink()
        
        processing_time = time.time() - start_time
        
        return OCRResult(
            strategy_name=self.name,
            text=text,
            confidence=avg_confidence,
            word_count=len(text.split()),
            char_count=len(text),
            artifacts_score=self.calculate_artifacts_score(text),
            readability_score=self.calculate_readability_score(text),
            layout_score=self.calculate_layout_score(text),
            processing_time=processing_time,
            metadata={'config': self.config}
        )


class CompetitiveOCR:
    """Main competitive OCR system."""
    
    def __init__(self):
        self.strategies: List[OCRStrategy] = []
        self.results: Dict[str, List[OCRResult]] = {}
    
    def add_strategy(self, strategy: OCRStrategy):
        """Add a strategy to the competition."""
        self.strategies.append(strategy)
    
    def process_image(self, image_path: Path, baseline_text: str = None) -> CompetitionResult:
        """Process image with all strategies and compete."""
        results = []
        
        print(f"\nProcessing {image_path.name} with {len(self.strategies)} strategies...")
        
        for strategy in self.strategies:
            print(f"  Running {strategy.name}...", end=' ')
            result = strategy.process(image_path)
            results.append(result)
            print(f"Score: {result.overall_score():.1f}")
        
        # Sort by overall score
        results.sort(key=lambda r: r.overall_score(), reverse=True)
        
        # Calculate scores dict
        scores = {r.strategy_name: r.overall_score() for r in results}
        
        # Generate consensus text (use best result as base, could be enhanced)
        consensus_text = results[0].text
        
        # Calculate improvement over baseline if provided
        improvement = 0.0
        if baseline_text:
            baseline_score = self._score_text(baseline_text)
            winner_score = results[0].overall_score()
            improvement = ((winner_score - baseline_score) / max(baseline_score, 1)) * 100
        
        competition_result = CompetitionResult(
            winner=results[0].strategy_name,
            scores=scores,
            all_results=results,
            consensus_text=consensus_text,
            improvement_over_baseline=improvement
        )
        
        return competition_result
    
    def _score_text(self, text: str) -> float:
        """Score text using same metrics as strategies."""
        strategy = OCRStrategy("baseline")
        return (
            (100 - strategy.calculate_artifacts_score(text)) * 0.4 +
            strategy.calculate_readability_score(text) * 0.3 +
            strategy.calculate_layout_score(text) * 0.3
        )
    
    def save_results(self, competition_result: CompetitionResult, output_dir: Path, page_name: str):
        """Save competition results to files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save winner text
        winner_file = output_dir / f"{page_name}_winner.txt"
        winner_file.write_text(competition_result.consensus_text)
        
        # Save all results
        for result in competition_result.all_results:
            result_file = output_dir / f"{page_name}_{result.strategy_name}.txt"
            result_file.write_text(result.text)
        
        # Save competition report
        report = {
            'page': page_name,
            'winner': competition_result.winner,
            'scores': competition_result.scores,
            'improvement': competition_result.improvement_over_baseline,
            'details': [
                {
                    'strategy': r.strategy_name,
                    'overall_score': r.overall_score(),
                    'confidence': r.confidence,
                    'artifacts_score': r.artifacts_score,
                    'readability_score': r.readability_score,
                    'layout_score': r.layout_score,
                    'word_count': r.word_count,
                    'processing_time': r.processing_time
                }
                for r in competition_result.all_results
            ]
        }
        
        report_file = output_dir / f"{page_name}_report.json"
        report_file.write_text(json.dumps(report, indent=2))
        
        print(f"\nResults saved to {output_dir}/{page_name}_*")
        print(f"Winner: {competition_result.winner} (Score: {competition_result.scores[competition_result.winner]:.1f})")


def main():
    """Run competitive OCR on sample pages."""
    print("=== Competitive Multi-Strategy OCR System ===\n")
    
    # Initialize system
    ocr = CompetitiveOCR()
    
    # Add strategies
    print("Initializing strategies...")
    ocr.add_strategy(TesseractStrategy("default"))
    ocr.add_strategy(TesseractStrategy("grayscale"))
    ocr.add_strategy(TesseractStrategy("enhanced"))
    ocr.add_strategy(TesseractStrategy("denoised"))
    ocr.add_strategy(TesseractStrategy("binarized"))
    
    print(f"Loaded {len(ocr.strategies)} strategies")
    
    # Process sample pages
    sample_dir = Path("../raw_scans/sample_pages")
    output_base = Path("../ocr_outputs")
    
    pages = sorted(sample_dir.glob("page_*.png"))[:5]  # Process first 5 for speed
    
    all_competitions = []
    
    for page_path in pages:
        page_name = page_path.stem
        
        # Run competition
        competition = ocr.process_image(page_path)
        all_competitions.append(competition)
        
        # Save results for each strategy
        for result in competition.all_results:
            strategy_dir = output_base / f"strategy_{result.strategy_name.lower().replace(' ', '_')}"
            strategy_dir.mkdir(parents=True, exist_ok=True)
            (strategy_dir / f"{page_name}.txt").write_text(result.text)
        
        # Save competition results
        ocr.save_results(competition, output_base / "competition_reports", page_name)
    
    # Overall summary
    print("\n" + "="*60)
    print("=== OVERALL COMPETITION SUMMARY ===")
    print("="*60)
    
    # Count wins by strategy
    win_counts = {}
    for comp in all_competitions:
        win_counts[comp.winner] = win_counts.get(comp.winner, 0) + 1
    
    print("\nStrategy Win Counts:")
    for strategy, wins in sorted(win_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {strategy}: {wins} wins")
    
    # Average scores
    all_scores = {}
    for comp in all_competitions:
        for strategy, score in comp.scores.items():
            if strategy not in all_scores:
                all_scores[strategy] = []
            all_scores[strategy].append(score)
    
    print("\nAverage Scores:")
    for strategy, scores in sorted(all_scores.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True):
        avg = sum(scores) / len(scores)
        print(f"  {strategy}: {avg:.1f}")
    
    # Recommendation
    best_strategy = max(win_counts.items(), key=lambda x: x[1])[0]
    print(f"\n🏆 RECOMMENDED STRATEGY: {best_strategy}")
    print(f"   Won {win_counts[best_strategy]}/{len(all_competitions)} competitions")


if __name__ == "__main__":
    main()
