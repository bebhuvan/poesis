"""
Multi-Stage Text Cleaning and Formatting Pipeline
Fixes OCR artifacts, hyphenation, ligatures, spacing, and formatting issues
"""
import re
import logging
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CleaningResult:
    """Result of text cleaning operations"""
    text: str
    changes_made: List[Dict]
    quality_score: float
    issues_found: List[str]


class TextCleaner:
    """
    Multi-stage text cleaning pipeline
    Each stage is a separate verification pass
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.ligature_map = self.config.get('LIGATURE_MAP', {
            'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff',
            'ﬃ': 'ffi', 'ﬄ': 'ffl', 'ﬆ': 'st',
        })
        self.changes_log = []

    def clean(self, text: str) -> CleaningResult:
        """
        Apply all cleaning stages sequentially
        """
        original_text = text
        self.changes_log = []
        issues_found = []

        # Stage 1: Fix ligatures
        text = self._fix_ligatures(text)

        # Stage 2: Fix hyphenation artifacts
        text = self._fix_hyphenation(text)

        # Stage 3: Fix character-level OCR errors
        text = self._fix_character_confusables(text)

        # Stage 4: Fix spacing issues
        text = self._fix_spacing(text)

        # Stage 5: Fix line breaks and paragraphs
        text = self._fix_line_breaks(text)

        # Stage 6: Fix punctuation
        text = self._fix_punctuation(text)

        # Stage 7: Remove artifacts
        text = self._remove_artifacts(text)

        # Calculate quality score
        quality_score = self._calculate_quality_score(text)

        return CleaningResult(
            text=text,
            changes_made=self.changes_log,
            quality_score=quality_score,
            issues_found=issues_found
        )

    def _fix_ligatures(self, text: str) -> str:
        """Replace ligatures with normal characters"""
        original = text
        for ligature, replacement in self.ligature_map.items():
            text = text.replace(ligature, replacement)

        if text != original:
            self.changes_log.append({
                'stage': 'ligature_fix',
                'description': f'Fixed {sum(original.count(lig) for lig in self.ligature_map)} ligatures'
            })

        return text

    def _fix_hyphenation(self, text: str) -> str:
        """
        Fix word breaks from end-of-line hyphenation
        Pattern: word- \n word -> wordword
        But preserve intentional hyphens (e.g., self-made)
        """
        original = text

        # Pattern: word followed by hyphen, newline, and continuation
        # This is the trickiest part - we need to be conservative
        pattern = r'(\w+)-\s*\n\s*(\w+)'

        def replace_hyphen(match):
            """Check if this is likely a line-break hyphen"""
            word1, word2 = match.groups()

            # If the combined word looks reasonable, merge it
            combined = word1 + word2

            # Heuristic: if word1 ends with common prefixes or word2 starts with common suffixes
            # it's likely a real hyphenation artifact
            common_prefixes = ['dis', 'pre', 'un', 'in', 'im', 'non', 're', 'anti']
            common_suffixes = ['ing', 'ed', 'tion', 'able', 'ible', 'ness', 'ment']

            # Check if this looks like a split word
            if (word1.lower() in common_prefixes or
                word2.lower() in common_suffixes or
                len(word2) < 4):  # Short continuation suggests artifact
                return combined
            else:
                # Preserve the hyphen but remove the line break
                return f"{word1}-{word2}"

        text = re.sub(pattern, replace_hyphen, text)

        if text != original:
            self.changes_log.append({
                'stage': 'hyphenation_fix',
                'description': 'Fixed line-break hyphenation'
            })

        return text

    def _fix_character_confusables(self, text: str) -> str:
        """
        Fix common OCR character confusion errors
        Based on visual similarity
        """
        original = text

        # Common confusables (context-dependent)
        # These are aggressive fixes - in production, use NLP context

        # Fix obvious errors in context
        # Example: "l" vs "I" in words
        # This requires sophisticated context analysis
        # For now, we'll do simple pattern-based fixes

        # Fix standalone "l" that should be "I"
        text = re.sub(r'\bl\b(?=\s+[a-z])', 'I', text)  # "l am" -> "I am"
        text = re.sub(r'\bl\'', "I'", text)  # "l'm" -> "I'm"

        # Fix "rn" that should be "m" in common words
        common_rn_errors = {
            'frorn': 'from',
            'rnake': 'make',
            'rnany': 'many',
            'rnore': 'more',
            'rnust': 'must',
            'tirne': 'time',
        }

        for error, correction in common_rn_errors.items():
            text = re.sub(r'\b' + error + r'\b', correction, text, flags=re.IGNORECASE)

        # Fix "vv" that should be "w"
        text = re.sub(r'\bvvith\b', 'with', text, flags=re.IGNORECASE)
        text = re.sub(r'\bvvhat\b', 'what', text, flags=re.IGNORECASE)
        text = re.sub(r'\bvvhen\b', 'when', text, flags=re.IGNORECASE)

        if text != original:
            self.changes_log.append({
                'stage': 'confusables_fix',
                'description': 'Fixed character confusables'
            })

        return text

    def _fix_spacing(self, text: str) -> str:
        """Fix spacing issues"""
        original = text

        # Remove multiple spaces
        text = re.sub(r' {2,}', ' ', text)

        # Fix missing space after punctuation
        text = re.sub(r'([.!?;:,])([A-Z])', r'\1 \2', text)

        # Remove space before punctuation
        text = re.sub(r'\s+([.!?;:,])', r'\1', text)

        # Fix space around quotes
        text = re.sub(r'\s+"', ' "', text)
        text = re.sub(r'"\s+', '" ', text)

        if text != original:
            self.changes_log.append({
                'stage': 'spacing_fix',
                'description': 'Fixed spacing issues'
            })

        return text

    def _fix_line_breaks(self, text: str) -> str:
        """
        Fix line breaks and paragraph structure
        Preserve intentional line breaks (poetry, letters)
        """
        original = text

        # Remove single line breaks within paragraphs
        # But preserve double line breaks (paragraph boundaries)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

        # Normalize paragraph breaks
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing/leading whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        if text != original:
            self.changes_log.append({
                'stage': 'line_breaks_fix',
                'description': 'Fixed line breaks and paragraphs'
            })

        return text

    def _fix_punctuation(self, text: str) -> str:
        """Fix punctuation issues"""
        original = text

        # Fix smart quotes that may have been OCR'd wrong
        text = text.replace('``', '"')
        text = text.replace("''", '"')

        # Fix ellipsis
        text = re.sub(r'\.{3,}', '...', text)

        # Fix em-dash spacing
        text = re.sub(r'\s*—\s*', '—', text)
        text = re.sub(r'\s*--\s*', '—', text)

        if text != original:
            self.changes_log.append({
                'stage': 'punctuation_fix',
                'description': 'Fixed punctuation'
            })

        return text

    def _remove_artifacts(self, text: str) -> str:
        """Remove OCR artifacts and noise"""
        original = text

        # Remove common OCR artifacts
        artifacts = [
            r'\f',  # Form feed
            r'\x00',  # Null characters
            r'[^\x00-\x7F]+',  # Non-ASCII artifacts (careful with this!)
        ]

        # For historical texts, we want to preserve some non-ASCII
        # So we'll be selective
        text = text.replace('\f', '')
        text = text.replace('\x00', '')

        # Remove page numbers if they appear alone on lines
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

        # Remove headers/footers (common patterns)
        # This is domain-specific and should be configured
        text = re.sub(r'^[-_=]{3,}$', '', text, flags=re.MULTILINE)

        if text != original:
            self.changes_log.append({
                'stage': 'artifact_removal',
                'description': 'Removed OCR artifacts'
            })

        return text

    def _calculate_quality_score(self, text: str) -> float:
        """
        Calculate text quality score based on various heuristics
        Returns score from 0.0 to 1.0
        """
        score = 1.0

        # Check for common issues
        total_chars = len(text)
        if total_chars == 0:
            return 0.0

        # Penalize excessive special characters
        special_chars = len(re.findall(r'[^\w\s.,;:!?\'"()-]', text))
        score -= min(0.3, special_chars / total_chars)

        # Penalize very short words (OCR artifacts)
        words = text.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            if avg_word_length < 3:
                score -= 0.2

        # Check for reasonable capitalization
        sentences = re.split(r'[.!?]\s+', text)
        capitalized = sum(1 for s in sentences if s and s[0].isupper())
        if sentences:
            cap_ratio = capitalized / len(sentences)
            if cap_ratio < 0.5:
                score -= 0.1

        # Check for reasonable punctuation
        punct_count = len(re.findall(r'[.!?]', text))
        words_per_punct = len(words) / max(1, punct_count)
        if words_per_punct > 100:  # Very long run-on
            score -= 0.15

        return max(0.0, min(1.0, score))


class SpellChecker:
    """
    Spell checking with support for historical/archaic words
    """

    def __init__(self, historical_dict: List[str] = None):
        self.historical_words = set(historical_dict or [])

        try:
            from spellchecker import SpellChecker
            self.spell = SpellChecker()
            # Add historical words to dictionary
            self.spell.word_frequency.load_words(self.historical_words)
        except ImportError:
            logger.warning("spellchecker not installed")
            self.spell = None

    def check(self, text: str) -> List[Dict]:
        """Check spelling and return potential errors"""
        if not self.spell:
            return []

        words = re.findall(r'\b\w+\b', text.lower())
        misspelled = self.spell.unknown(words)

        issues = []
        for word in misspelled:
            # Skip if in historical dictionary
            if word in self.historical_words:
                continue

            suggestions = self.spell.candidates(word)
            issues.append({
                'word': word,
                'suggestions': list(suggestions) if suggestions else []
            })

        return issues
