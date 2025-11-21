"""
Context-Aware Post-Processing & Error Correction - Strategy 4
Uses linguistic context and historical knowledge to fix OCR errors
"""

import re
import logging
from typing import Dict, List, Tuple, Set
from pathlib import Path
from collections import defaultdict

from tagore_config import (
    POSTPROCESSING_CONFIG,
    CUSTOM_VOCABULARY,
    KNOWN_CORRESPONDENTS,
    HISTORICAL_EVENTS
)


class TextPostProcessor:
    """
    Post-processes OCR text with context-aware corrections.
    Implements Strategy 4: Context-Aware Post-Processing & Error Correction
    """

    def __init__(self, config: Dict = None):
        """
        Initialize post-processor.

        Args:
            config: Post-processing configuration
        """
        self.config = config or POSTPROCESSING_CONFIG
        self.logger = logging.getLogger(__name__)

        # Initialize spell checker
        self.spell_checker = None
        if self.config['spell_check_enabled']:
            self._init_spell_checker()

        # Initialize language model
        self.language_model = None
        if self.config['language_model_enabled']:
            self._init_language_model()

        # Load custom dictionary
        self.custom_vocab = set(CUSTOM_VOCABULARY)
        self.known_names = set(KNOWN_CORRESPONDENTS)

        # Pattern corrections
        self.pattern_corrections = self.config['pattern_corrections']

    def _init_spell_checker(self):
        """Initialize spell checker with custom dictionary."""
        try:
            from spellchecker import SpellChecker

            self.spell_checker = SpellChecker(language=self.config['spell_check_language'])

            # Add custom vocabulary
            self.spell_checker.word_frequency.load_words(self.custom_vocab)
            self.spell_checker.word_frequency.load_words(self.known_names)

            self.logger.info("Spell checker initialized with custom dictionary")

        except ImportError:
            self.logger.warning("Spell checker not available (install: pip install pyspellchecker)")

    def _init_language_model(self):
        """Initialize language model for context-aware corrections."""
        try:
            from transformers import pipeline

            self.language_model = pipeline(
                'fill-mask',
                model=self.config['language_model_name']
            )

            self.logger.info(f"Language model initialized: {self.config['language_model_name']}")

        except ImportError:
            self.logger.warning("Transformers not available (install: pip install transformers)")
        except Exception as e:
            self.logger.warning(f"Failed to load language model: {e}")

    def process(self, text: str, confidence_scores: Dict[str, float] = None) -> Dict:
        """
        Post-process OCR text with corrections.

        Args:
            text: Raw OCR text
            confidence_scores: Optional per-word confidence scores

        Returns:
            Dictionary with corrected text and metadata
        """
        self.logger.info(f"Post-processing text ({len(text)} characters)")

        original_text = text
        corrections_made = []

        # Step 1: Pattern-based corrections
        text, pattern_corrections = self._apply_pattern_corrections(text)
        corrections_made.extend(pattern_corrections)

        # Step 2: Fix line breaks and hyphenation
        if self.config['fix_line_breaks']:
            text = self._fix_line_breaks(text)

        if self.config['resolve_hyphenation']:
            text = self._resolve_hyphenation(text)

        # Step 3: Spell checking
        if self.spell_checker:
            text, spell_corrections = self._spell_check(text, confidence_scores)
            corrections_made.extend(spell_corrections)

        # Step 4: Language model corrections (for low-confidence words)
        if self.language_model and confidence_scores:
            text, lm_corrections = self._language_model_correction(text, confidence_scores)
            corrections_made.extend(lm_corrections)

        # Step 5: Formatting
        if self.config['smart_quotes']:
            text = self._apply_smart_quotes(text)

        if self.config['normalize_whitespace']:
            text = self._normalize_whitespace(text)

        # Step 6: Proper noun capitalization
        text = self._fix_capitalization(text)

        return {
            'original_text': original_text,
            'corrected_text': text,
            'corrections': corrections_made,
            'correction_count': len(corrections_made),
            'confidence': self._calculate_final_confidence(text, corrections_made)
        }

    def _apply_pattern_corrections(self, text: str) -> Tuple[str, List[Dict]]:
        """Apply pattern-based OCR error corrections."""
        corrections = []

        for pattern, replacement in self.pattern_corrections.items():
            # Only replace in word contexts (not standalone)
            regex = r'\b(\w*' + re.escape(pattern) + r'\w*)\b'

            matches = list(re.finditer(regex, text))

            for match in matches:
                word = match.group(1)

                # Check if replacement makes sense
                if pattern in word:
                    corrected_word = word.replace(pattern, replacement)

                    # Verify it's a real word (if spell checker available)
                    if self.spell_checker:
                        if corrected_word.lower() in self.spell_checker or corrected_word in self.custom_vocab:
                            text = text.replace(word, corrected_word, 1)
                            corrections.append({
                                'type': 'pattern',
                                'original': word,
                                'corrected': corrected_word,
                                'pattern': f'{pattern}->{replacement}'
                            })

        return text, corrections

    def _fix_line_breaks(self, text: str) -> str:
        """Remove inappropriate line breaks within sentences."""
        # Replace single line breaks with spaces (except after punctuation)
        text = re.sub(r'(?<=[a-z,])\n(?=[a-z])', ' ', text)

        # Preserve paragraph breaks (double line breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def _resolve_hyphenation(self, text: str) -> str:
        """
        Resolve word breaks at line endings (hyphenation).
        Example: "exam-\nple" -> "example"
        """
        # Match word-\nword pattern
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        return text

    def _spell_check(self, text: str, confidence_scores: Dict[str, float] = None) -> Tuple[str, List[Dict]]:
        """
        Spell check with confidence-aware corrections.
        Only correct words below confidence threshold.
        """
        if not self.spell_checker:
            return text, []

        corrections = []
        words = text.split()

        corrected_words = []

        for i, word in enumerate(words):
            # Clean word for checking
            clean_word = re.sub(r'[^\w]', '', word)

            if not clean_word:
                corrected_words.append(word)
                continue

            # Check confidence (if available)
            word_confidence = confidence_scores.get(clean_word.lower(), 1.0) if confidence_scores else 1.0

            # Skip high-confidence words
            if word_confidence > 0.95:
                corrected_words.append(word)
                continue

            # Skip known vocabulary
            if clean_word in self.custom_vocab or clean_word in self.known_names:
                corrected_words.append(word)
                continue

            # Check spelling
            if clean_word.lower() not in self.spell_checker:
                # Get correction
                candidates = self.spell_checker.candidates(clean_word.lower())

                if candidates:
                    correction = list(candidates)[0]

                    # Preserve original capitalization
                    if clean_word[0].isupper():
                        correction = correction.capitalize()

                    # Replace in original word (preserve punctuation)
                    corrected_word = word.replace(clean_word, correction)

                    corrections.append({
                        'type': 'spelling',
                        'original': word,
                        'corrected': corrected_word,
                        'confidence': word_confidence
                    })

                    corrected_words.append(corrected_word)
                else:
                    # No correction found, flag for review
                    corrected_words.append(f"[?:{word}]")
                    corrections.append({
                        'type': 'uncertain',
                        'original': word,
                        'corrected': f"[?:{word}]",
                        'confidence': word_confidence
                    })
            else:
                corrected_words.append(word)

        return ' '.join(corrected_words), corrections

    def _language_model_correction(self, text: str, confidence_scores: Dict[str, float]) -> Tuple[str, List[Dict]]:
        """
        Use language model to correct low-confidence words.
        Uses BERT-style masked language modeling.
        """
        if not self.language_model:
            return text, []

        corrections = []

        # Find low-confidence words
        words = text.split()
        threshold = self.config['lm_confidence_threshold']

        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word)
            word_confidence = confidence_scores.get(clean_word.lower(), 1.0)

            if word_confidence < threshold:
                # Create masked sentence
                masked_sentence = ' '.join(words[:i] + ['[MASK]'] + words[i+1:])

                try:
                    # Get predictions
                    predictions = self.language_model(masked_sentence, top_k=3)

                    if predictions:
                        top_prediction = predictions[0]

                        # Only accept high-confidence predictions
                        if top_prediction['score'] > 0.5:
                            correction = top_prediction['token_str'].strip()

                            # Verify it's different and reasonable
                            if correction.lower() != clean_word.lower():
                                corrections.append({
                                    'type': 'language_model',
                                    'original': word,
                                    'corrected': correction,
                                    'lm_confidence': top_prediction['score'],
                                    'ocr_confidence': word_confidence
                                })

                                words[i] = correction

                except Exception as e:
                    self.logger.debug(f"LM correction failed for '{word}': {e}")

        return ' '.join(words), corrections

    def _apply_smart_quotes(self, text: str) -> str:
        """Convert straight quotes to smart quotes."""
        # Simple implementation
        text = re.sub(r'"([^"]*)"', r'"\1"', text)
        text = re.sub(r"'([^']*)'", r''\1'', text)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace (remove extra spaces, tabs, etc.)."""
        # Multiple spaces to single space
        text = re.sub(r' +', ' ', text)

        # Remove spaces before punctuation
        text = re.sub(r' +([.,;:!?])', r'\1', text)

        # Remove spaces after opening quotes/parentheses
        text = re.sub(r'(["\'(]) +', r'\1', text)

        # Remove spaces before closing quotes/parentheses
        text = re.sub(r' +(["\')\]])', r'\1', text)

        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _fix_capitalization(self, text: str) -> str:
        """Fix capitalization for proper nouns."""
        # Capitalize known names
        for name in self.known_names:
            # Case-insensitive replacement
            text = re.sub(r'\b' + re.escape(name) + r'\b', name, text, flags=re.IGNORECASE)

        # Capitalize sentence starts
        text = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)

        return text

    def _calculate_final_confidence(self, text: str, corrections: List[Dict]) -> float:
        """Calculate final confidence score after corrections."""
        if not corrections:
            return 1.0

        # Penalize based on number of corrections
        word_count = len(text.split())

        if word_count == 0:
            return 0.0

        correction_rate = len(corrections) / word_count

        # Confidence decreases with correction rate
        # 0% corrections = 100% confidence
        # 10% corrections = 90% confidence
        confidence = max(0.5, 1.0 - correction_rate)

        return confidence


if __name__ == '__main__':
    # Test post-processor
    logging.basicConfig(level=logging.DEBUG)

    processor = TextPostProcessor()

    # Example usage:
    test_text = """This is a sanple text with some OCR er-
rors that need to be fixed. Rabindranath tagore wrote many letters."""

    result = processor.process(test_text)

    print("Original:", result['original_text'])
    print("Corrected:", result['corrected_text'])
    print(f"Corrections: {result['correction_count']}")
    print(f"Confidence: {result['confidence']:.2f}")
