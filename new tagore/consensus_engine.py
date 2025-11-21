"""
Darwinian Consensus Engine - Survival of the Fittest Text
Combines outputs from multiple OCR engines using voting, confidence, and edit distance
"""
import logging
from typing import List, Dict, Tuple
from collections import Counter
import difflib
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

try:
    from Levenshtein import distance as levenshtein_distance
except ImportError:
    logger.warning("python-Levenshtein not available, using difflib")
    levenshtein_distance = None


@dataclass
class ConsensusResult:
    """Result of consensus building"""
    text: str
    confidence: float
    agreement_score: float
    contributing_engines: List[str]
    uncertain_regions: List[Dict]
    metadata: Dict


class ConsensusEngine:
    """
    Combines multiple OCR results using competitive selection
    Think of it as natural selection for text extraction
    """

    def __init__(self, method: str = "weighted_voting", min_agreement: float = 0.6):
        self.method = method
        self.min_agreement = min_agreement

    def build_consensus(self, ocr_results: List) -> ConsensusResult:
        """
        Build consensus from multiple OCR results
        Uses character-level and word-level voting
        """
        if not ocr_results:
            raise ValueError("No OCR results to build consensus from")

        if len(ocr_results) == 1:
            # Only one engine, use it directly
            result = ocr_results[0]
            return ConsensusResult(
                text=result.text,
                confidence=result.confidence,
                agreement_score=1.0,
                contributing_engines=[result.engine_name],
                uncertain_regions=[],
                metadata={'method': 'single_engine'}
            )

        # Choose consensus method
        if self.method == "weighted_voting":
            return self._weighted_voting_consensus(ocr_results)
        elif self.method == "majority_voting":
            return self._majority_voting_consensus(ocr_results)
        elif self.method == "confidence_voting":
            return self._confidence_voting_consensus(ocr_results)
        else:
            raise ValueError(f"Unknown consensus method: {self.method}")

    def _weighted_voting_consensus(self, ocr_results: List) -> ConsensusResult:
        """
        Weighted voting based on engine weights and confidence
        More sophisticated than simple majority voting
        """
        # Extract texts and weights
        texts = [r.text for r in ocr_results]
        weights = [r.confidence * getattr(r, 'weight', 1.0) for r in ocr_results]
        engine_names = [r.engine_name for r in ocr_results]

        # Align texts using sequence matching
        aligned_texts = self._align_texts(texts)

        # Perform character-by-character weighted voting
        consensus_text = []
        uncertain_regions = []
        char_position = 0

        for char_options in aligned_texts:
            # char_options is a list of (char, weight) tuples
            if not char_options:
                continue

            # Vote for each character
            char_votes = Counter()
            total_weight = 0

            for i, (text, weight) in enumerate(zip(texts, weights)):
                if char_position < len(text):
                    char = text[char_position]
                    char_votes[char] += weight
                    total_weight += weight

            if not char_votes:
                char_position += 1
                continue

            # Get the winning character
            winner, winner_weight = char_votes.most_common(1)[0]
            agreement = winner_weight / total_weight if total_weight > 0 else 0

            consensus_text.append(winner)

            # Flag uncertain regions
            if agreement < self.min_agreement:
                uncertain_regions.append({
                    'position': char_position,
                    'character': winner,
                    'alternatives': dict(char_votes),
                    'agreement': agreement
                })

            char_position += 1

        # Calculate overall metrics
        final_text = ''.join(consensus_text)
        avg_confidence = np.mean([r.confidence for r in ocr_results])
        agreement_score = 1.0 - (len(uncertain_regions) / max(len(final_text), 1))

        return ConsensusResult(
            text=final_text,
            confidence=avg_confidence,
            agreement_score=agreement_score,
            contributing_engines=engine_names,
            uncertain_regions=uncertain_regions,
            metadata={
                'method': 'weighted_voting',
                'total_engines': len(ocr_results),
                'uncertain_count': len(uncertain_regions)
            }
        )

    def _majority_voting_consensus(self, ocr_results: List) -> ConsensusResult:
        """Simple majority voting - democratic approach"""
        texts = [r.text for r in ocr_results]

        # Use the most common text as baseline
        text_counter = Counter(texts)
        most_common_text, count = text_counter.most_common(1)[0]

        agreement_score = count / len(texts)
        avg_confidence = np.mean([r.confidence for r in ocr_results])

        return ConsensusResult(
            text=most_common_text,
            confidence=avg_confidence,
            agreement_score=agreement_score,
            contributing_engines=[r.engine_name for r in ocr_results],
            uncertain_regions=[],
            metadata={'method': 'majority_voting', 'votes': count}
        )

    def _confidence_voting_consensus(self, ocr_results: List) -> ConsensusResult:
        """Select based on highest confidence - meritocratic approach"""
        # Sort by confidence
        sorted_results = sorted(ocr_results, key=lambda r: r.confidence, reverse=True)
        best_result = sorted_results[0]

        return ConsensusResult(
            text=best_result.text,
            confidence=best_result.confidence,
            agreement_score=1.0,
            contributing_engines=[best_result.engine_name],
            uncertain_regions=[],
            metadata={'method': 'confidence_voting', 'winner': best_result.engine_name}
        )

    def _align_texts(self, texts: List[str]) -> List[List[Tuple[str, int]]]:
        """
        Align multiple texts character-by-character using sequence alignment
        Returns aligned positions
        """
        if len(texts) < 2:
            return [[(char, 0)] for char in texts[0]] if texts else []

        # Use the longest text as reference
        reference = max(texts, key=len)

        # For now, simple approach - return character positions
        # In production, use proper sequence alignment (e.g., multiple sequence alignment)
        aligned = []
        max_len = max(len(t) for t in texts)

        for i in range(max_len):
            chars_at_pos = []
            for text in texts:
                if i < len(text):
                    chars_at_pos.append((text[i], i))
            aligned.append(chars_at_pos)

        return aligned

    def compare_texts(self, text1: str, text2: str) -> Dict:
        """Compare two texts and return similarity metrics"""
        # Calculate edit distance
        if levenshtein_distance:
            edit_dist = levenshtein_distance(text1, text2)
        else:
            # Fallback to difflib
            edit_dist = sum(1 for a, b in zip(text1, text2) if a != b)
            edit_dist += abs(len(text1) - len(text2))

        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

        # Get diff
        diff = list(difflib.unified_diff(
            text1.splitlines(keepends=True),
            text2.splitlines(keepends=True),
            lineterm=''
        ))

        return {
            'edit_distance': edit_dist,
            'similarity': similarity,
            'diff': diff,
            'length_diff': abs(len(text1) - len(text2))
        }


class EnsembleSelector:
    """
    Advanced selection using multiple strategies
    Combines different consensus methods for robustness
    """

    def __init__(self):
        self.methods = [
            ConsensusEngine(method="weighted_voting"),
            ConsensusEngine(method="majority_voting"),
            ConsensusEngine(method="confidence_voting")
        ]

    def select_best(self, ocr_results: List) -> ConsensusResult:
        """
        Run multiple consensus methods and select the best result
        Meta-consensus: consensus about consensus
        """
        consensus_results = []

        for engine in self.methods:
            try:
                result = engine.build_consensus(ocr_results)
                consensus_results.append(result)
            except Exception as e:
                logger.error(f"Consensus method {engine.method} failed: {e}")

        if not consensus_results:
            raise ValueError("All consensus methods failed")

        # Select best based on combined score
        best_result = max(
            consensus_results,
            key=lambda r: r.confidence * r.agreement_score
        )

        logger.info(
            f"Selected consensus from {best_result.metadata.get('method')} "
            f"(confidence: {best_result.confidence:.2f}, "
            f"agreement: {best_result.agreement_score:.2f})"
        )

        return best_result
