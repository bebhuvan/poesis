#!/usr/bin/env python3
"""
Quality scoring system for OCR results.
Evaluates and ranks different OCR strategies.
"""

from dataclasses import dataclass
from typing import List, Dict
import re
import math
from collections import Counter


@dataclass
class QualityScore:
    """Quality score for an OCR result."""
    ocr_confidence: float          # From OCR engine
    readability: float              # Language model perplexity
    artifact_score: float           # Fewer artifacts = higher score
    layout_score: float             # Better layout preservation
    length_score: float             # Reasonable length (not too short/long)
    total_score: float              # Weighted combination

    def __str__(self) -> str:
        return (f"Total: {self.total_score:.1f} "
                f"(OCR: {self.ocr_confidence:.1f}, "
                f"Read: {self.readability:.1f}, "
                f"Artifact: {self.artifact_score:.1f}, "
                f"Layout: {self.layout_score:.1f}, "
                f"Length: {self.length_score:.1f})")


class QualityScorer:
    """Score and rank OCR results."""

    # Scoring weights
    WEIGHTS = {
        'ocr_confidence': 0.25,
        'readability': 0.20,
        'artifact_score': 0.20,
        'layout_score': 0.20,
        'length_score': 0.15,
    }

    def score(self, text: str, ocr_confidence: float) -> QualityScore:
        """
        Calculate quality score for OCR text.

        Args:
            text: OCR output text
            ocr_confidence: Confidence from OCR engine (0-100)

        Returns:
            QualityScore object
        """
        readability = self._score_readability(text)
        artifact = self._score_artifacts(text)
        layout = self._score_layout(text)
        length = self._score_length(text)

        total = (
            ocr_confidence * self.WEIGHTS['ocr_confidence'] +
            readability * self.WEIGHTS['readability'] +
            artifact * self.WEIGHTS['artifact_score'] +
            layout * self.WEIGHTS['layout_score'] +
            length * self.WEIGHTS['length_score']
        )

        return QualityScore(
            ocr_confidence=ocr_confidence,
            readability=readability,
            artifact_score=artifact,
            layout_score=layout,
            length_score=length,
            total_score=total
        )

    def _score_readability(self, text: str) -> float:
        """
        Score text readability (0-100).
        Higher is better.
        """
        if not text or len(text.strip()) < 10:
            return 0.0

        words = text.split()
        if len(words) < 5:
            return 0.0

        score = 100.0

        # Penalize excessive non-alphabetic characters
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
        if alpha_ratio < 0.7:
            score -= (0.7 - alpha_ratio) * 100

        # Penalize words with too many repeated characters (like "oooo")
        weird_words = sum(1 for word in words if self._is_weird_word(word))
        weird_ratio = weird_words / len(words)
        score -= weird_ratio * 50

        # Penalize very short words ratio (single chars that aren't 'I' or 'a')
        short_words = sum(
            1 for word in words
            if len(word) == 1 and word.lower() not in ['i', 'a']
        )
        short_ratio = short_words / len(words)
        score -= short_ratio * 100

        # Reward reasonable average word length (English avg ~4.5-5 chars)
        avg_word_len = sum(len(w) for w in words) / len(words)
        if 3.5 <= avg_word_len <= 6.5:
            score += 10
        else:
            score -= abs(avg_word_len - 5) * 5

        return max(0.0, min(100.0, score))

    def _is_weird_word(self, word: str) -> bool:
        """Check if word looks like OCR garbage."""
        if len(word) < 2:
            return False

        # Check for excessive character repetition
        char_counts = Counter(word.lower())
        max_count = max(char_counts.values())
        if max_count / len(word) > 0.5:  # Same char appears >50% of time
            return True

        # Check for non-alphabetic characters in middle of word
        if len(word) > 2:
            middle = word[1:-1]
            if not middle.replace("'", "").replace("-", "").isalpha():
                return True

        return False

    def _score_artifacts(self, text: str) -> float:
        """
        Score artifact presence (0-100).
        Higher = fewer artifacts.
        """
        score = 100.0
        lines = text.split('\n')

        # Count various artifacts
        artifacts = 0

        # Single character lines (except meaningful ones)
        single_char_lines = sum(
            1 for line in lines
            if len(line.strip()) == 1 and line.strip() not in ['I', '!', '?']
        )
        artifacts += single_char_lines

        # Lines with just numbers (page numbers)
        number_lines = sum(1 for line in lines if line.strip().isdigit())
        artifacts += number_lines

        # Lines with excessive punctuation
        punct_lines = sum(
            1 for line in lines
            if len(line.strip()) > 0 and
            sum(c in '.,!?;:()[]{}|_-=' for c in line) / len(line) > 0.5
        )
        artifacts += punct_lines

        # Random short gibberish lines
        gibberish_lines = sum(
            1 for line in lines
            if 2 <= len(line.strip()) <= 4 and
            not line.strip().lower() in ['the', 'and', 'but', 'for', 'are', 'you', 'was', 'not']
        )
        artifacts += gibberish_lines

        # Penalize based on artifact density
        if len(lines) > 0:
            artifact_ratio = artifacts / len(lines)
            score -= artifact_ratio * 100

        return max(0.0, min(100.0, score))

    def _score_layout(self, text: str) -> float:
        """
        Score layout quality (0-100).
        Higher = better structure.
        """
        score = 100.0
        lines = text.split('\n')

        if len(lines) < 2:
            return 50.0  # Neutral for very short text

        # Check for reasonable paragraph structure
        blank_lines = sum(1 for line in lines if line.strip() == '')
        non_blank_lines = len(lines) - blank_lines

        if non_blank_lines > 0:
            blank_ratio = blank_lines / len(lines)

            # Ideal ratio: 10-30% blank lines for paragraph separation
            if 0.1 <= blank_ratio <= 0.3:
                score += 10
            elif blank_ratio > 0.5:  # Too many blank lines
                score -= 20
            elif blank_ratio < 0.05 and non_blank_lines > 10:  # Too few breaks
                score -= 10

        # Check for consistent line lengths (good layout has some variation)
        line_lengths = [len(line) for line in lines if line.strip()]
        if line_lengths:
            avg_len = sum(line_lengths) / len(line_lengths)
            variance = sum((l - avg_len) ** 2 for l in line_lengths) / len(line_lengths)
            std_dev = math.sqrt(variance)

            # Some variance is good (paragraphs), but not too much
            if 10 <= std_dev <= 40:
                score += 10
            elif std_dev > 60:  # Too chaotic
                score -= 10

        # Penalize excessive very short lines (fragmentation)
        very_short_lines = sum(1 for line in lines if 0 < len(line.strip()) < 10)
        if non_blank_lines > 0:
            short_ratio = very_short_lines / non_blank_lines
            if short_ratio > 0.4:  # >40% of lines are very short
                score -= 30

        return max(0.0, min(100.0, score))

    def _score_length(self, text: str) -> float:
        """
        Score text length (0-100).
        Penalize extremely short or long results.
        """
        char_count = len(text.strip())
        word_count = len(text.split())

        # Expected range for a book page: 100-2000 words, 500-10000 chars
        if char_count < 100:  # Too short
            return char_count / 100 * 50  # Scale from 0 to 50
        elif char_count > 15000:  # Suspiciously long (might be garbage)
            excess = char_count - 15000
            return max(0, 100 - (excess / 1000 * 10))
        else:
            # Optimal range
            return 100.0

    def rank_results(self, results: List[tuple]) -> List[tuple]:
        """
        Rank OCR results by quality score.

        Args:
            results: List of (name, text, ocr_confidence) tuples

        Returns:
            Sorted list of (name, text, score) tuples (best first)
        """
        scored_results = []

        for name, text, ocr_conf in results:
            score = self.score(text, ocr_conf)
            scored_results.append((name, text, score))

        # Sort by total score (descending)
        scored_results.sort(key=lambda x: x[2].total_score, reverse=True)

        return scored_results

    def find_best(self, results: List[tuple], min_margin: float = 10.0) -> tuple:
        """
        Find the best result, or None if no clear winner.

        Args:
            results: List of (name, text, ocr_confidence) tuples
            min_margin: Minimum score difference to be considered "clear winner"

        Returns:
            (name, text, score, is_clear_winner) tuple
        """
        ranked = self.rank_results(results)

        if not ranked:
            return None, None, None, False

        best = ranked[0]

        if len(ranked) == 1:
            return best[0], best[1], best[2], True

        # Check if there's a clear winner
        second_best = ranked[1]
        margin = best[2].total_score - second_best[2].total_score

        is_clear_winner = margin >= min_margin

        return best[0], best[1], best[2], is_clear_winner
