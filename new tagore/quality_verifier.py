"""
Multi-Stage Quality Verification and Assurance
Periodic checks, uncertainty flagging, and self-diagnostics
"""
import re
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """Quality assessment report"""
    overall_score: float
    checks_passed: int
    checks_failed: int
    warnings: List[Dict]
    errors: List[Dict]
    uncertain_regions: List[Dict]
    recommendations: List[str]


class QualityVerifier:
    """
    Multi-layer quality verification system
    Catches errors that might slip through consensus
    """

    def __init__(self, min_confidence: float = 0.75):
        self.min_confidence = min_confidence
        self.checks = [
            self._check_text_length,
            self._check_character_distribution,
            self._check_word_validity,
            self._check_sentence_structure,
            self._check_formatting_consistency,
            self._check_special_characters,
            self._check_capitalization,
            self._check_number_patterns,
        ]

    def verify(self, text: str, metadata: Dict = None) -> QualityReport:
        """
        Run all quality checks on the text
        """
        metadata = metadata or {}
        warnings = []
        errors = []
        checks_passed = 0
        checks_failed = 0

        for check in self.checks:
            try:
                result = check(text, metadata)
                if result['status'] == 'pass':
                    checks_passed += 1
                elif result['status'] == 'warning':
                    warnings.append(result)
                    checks_passed += 1
                else:  # error
                    errors.append(result)
                    checks_failed += 1
            except Exception as e:
                logger.error(f"Check failed with exception: {e}")
                checks_failed += 1

        # Calculate overall score
        total_checks = checks_passed + checks_failed
        overall_score = checks_passed / max(1, total_checks)

        # Generate recommendations
        recommendations = self._generate_recommendations(warnings, errors)

        # Find uncertain regions
        uncertain_regions = self._find_uncertain_regions(text, metadata)

        return QualityReport(
            overall_score=overall_score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            errors=errors,
            uncertain_regions=uncertain_regions,
            recommendations=recommendations
        )

    def _check_text_length(self, text: str, metadata: Dict) -> Dict:
        """Check if text length is reasonable"""
        char_count = len(text)
        word_count = len(text.split())

        if char_count < 100:
            return {
                'check': 'text_length',
                'status': 'error',
                'message': f'Text too short: {char_count} characters',
                'data': {'char_count': char_count}
            }
        elif word_count < 20:
            return {
                'check': 'text_length',
                'status': 'warning',
                'message': f'Few words found: {word_count} words',
                'data': {'word_count': word_count}
            }

        return {
            'check': 'text_length',
            'status': 'pass',
            'data': {'char_count': char_count, 'word_count': word_count}
        }

    def _check_character_distribution(self, text: str, metadata: Dict) -> Dict:
        """Check character distribution for anomalies"""
        # Calculate character frequency
        char_freq = {}
        for char in text:
            char_freq[char] = char_freq.get(char, 0) + 1

        total_chars = len(text)

        # Check for suspicious patterns
        issues = []

        # Too many digits (might be OCR artifacts)
        digit_ratio = sum(1 for c in text if c.isdigit()) / max(1, total_chars)
        if digit_ratio > 0.3:
            issues.append(f'High digit ratio: {digit_ratio:.2%}')

        # Too many special characters
        special_ratio = sum(1 for c in text if not c.isalnum() and c not in ' \n.,;:!?\'"()-') / max(1, total_chars)
        if special_ratio > 0.1:
            issues.append(f'High special character ratio: {special_ratio:.2%}')

        # Check for repeated characters (OCR artifacts)
        repeated = re.findall(r'(.)\1{4,}', text)
        if repeated:
            issues.append(f'Found repeated characters: {repeated[:5]}')

        if issues:
            return {
                'check': 'character_distribution',
                'status': 'warning',
                'message': '; '.join(issues),
                'data': {'digit_ratio': digit_ratio, 'special_ratio': special_ratio}
            }

        return {'check': 'character_distribution', 'status': 'pass', 'data': {}}

    def _check_word_validity(self, text: str, metadata: Dict) -> Dict:
        """Check for valid word patterns"""
        words = re.findall(r'\b\w+\b', text)

        if not words:
            return {
                'check': 'word_validity',
                'status': 'error',
                'message': 'No valid words found'
            }

        # Check average word length
        avg_length = sum(len(w) for w in words) / len(words)

        if avg_length < 2:
            return {
                'check': 'word_validity',
                'status': 'error',
                'message': f'Average word length too short: {avg_length:.1f}',
                'data': {'avg_word_length': avg_length}
            }

        # Check for words that are all special characters (OCR noise)
        noisy_words = [w for w in words if not any(c.isalpha() for c in w)]
        noise_ratio = len(noisy_words) / len(words)

        if noise_ratio > 0.2:
            return {
                'check': 'word_validity',
                'status': 'warning',
                'message': f'High noise ratio: {noise_ratio:.2%}',
                'data': {'noise_ratio': noise_ratio, 'noisy_words': noisy_words[:10]}
            }

        return {
            'check': 'word_validity',
            'status': 'pass',
            'data': {'avg_word_length': avg_length, 'noise_ratio': noise_ratio}
        }

    def _check_sentence_structure(self, text: str, metadata: Dict) -> Dict:
        """Check sentence structure and punctuation"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return {
                'check': 'sentence_structure',
                'status': 'warning',
                'message': 'No sentences detected'
            }

        # Check average sentence length
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)

        issues = []

        if avg_length > 50:
            issues.append(f'Very long sentences (avg: {avg_length:.1f} words)')
        elif avg_length < 5:
            issues.append(f'Very short sentences (avg: {avg_length:.1f} words)')

        # Check capitalization
        capitalized = sum(1 for s in sentences if s and s[0].isupper())
        cap_ratio = capitalized / len(sentences)

        if cap_ratio < 0.5:
            issues.append(f'Low capitalization ratio: {cap_ratio:.2%}')

        if issues:
            return {
                'check': 'sentence_structure',
                'status': 'warning',
                'message': '; '.join(issues),
                'data': {'avg_sentence_length': avg_length, 'capitalization_ratio': cap_ratio}
            }

        return {
            'check': 'sentence_structure',
            'status': 'pass',
            'data': {'avg_sentence_length': avg_length}
        }

    def _check_formatting_consistency(self, text: str, metadata: Dict) -> Dict:
        """Check formatting consistency"""
        # Check line length consistency (for detecting layout issues)
        lines = text.split('\n')
        line_lengths = [len(line) for line in lines if line.strip()]

        if not line_lengths:
            return {'check': 'formatting_consistency', 'status': 'pass', 'data': {}}

        std_dev = np.std(line_lengths)
        mean_length = np.mean(line_lengths)

        # High variance might indicate layout issues
        coefficient_of_variation = std_dev / mean_length if mean_length > 0 else 0

        if coefficient_of_variation > 2.0:
            return {
                'check': 'formatting_consistency',
                'status': 'warning',
                'message': f'High line length variance (CV: {coefficient_of_variation:.2f})',
                'data': {'cv': coefficient_of_variation}
            }

        return {'check': 'formatting_consistency', 'status': 'pass', 'data': {}}

    def _check_special_characters(self, text: str, metadata: Dict) -> Dict:
        """Check for suspicious special characters"""
        # Look for characters that shouldn't appear in English text
        suspicious_chars = set()

        for char in text:
            code = ord(char)
            # Control characters (except newline, tab, carriage return)
            if code < 32 and char not in '\n\t\r':
                suspicious_chars.add(char)
            # Unusual Unicode ranges
            elif code > 127 and code < 160:
                suspicious_chars.add(char)

        if suspicious_chars:
            return {
                'check': 'special_characters',
                'status': 'warning',
                'message': f'Found suspicious characters: {suspicious_chars}',
                'data': {'suspicious_chars': list(suspicious_chars)}
            }

        return {'check': 'special_characters', 'status': 'pass', 'data': {}}

    def _check_capitalization(self, text: str, metadata: Dict) -> Dict:
        """Check capitalization patterns"""
        # Count all-caps words (might be OCR artifacts or headers)
        words = re.findall(r'\b[A-Z]{2,}\b', text)
        all_caps_count = len(words)

        total_words = len(text.split())
        caps_ratio = all_caps_count / max(1, total_words)

        if caps_ratio > 0.3:
            return {
                'check': 'capitalization',
                'status': 'warning',
                'message': f'High all-caps ratio: {caps_ratio:.2%}',
                'data': {'all_caps_ratio': caps_ratio, 'all_caps_words': words[:10]}
            }

        return {'check': 'capitalization', 'status': 'pass', 'data': {}}

    def _check_number_patterns(self, text: str, metadata: Dict) -> Dict:
        """Check for unusual number patterns"""
        # Find all numbers
        numbers = re.findall(r'\b\d+\b', text)

        if not numbers:
            return {'check': 'number_patterns', 'status': 'pass', 'data': {}}

        # Check for page numbers appearing in text
        # (Common OCR artifact)
        small_numbers = [n for n in numbers if int(n) < 1000]

        if len(small_numbers) > 20:
            return {
                'check': 'number_patterns',
                'status': 'warning',
                'message': f'Many small numbers found: {len(small_numbers)} (might be page numbers)',
                'data': {'small_number_count': len(small_numbers)}
            }

        return {'check': 'number_patterns', 'status': 'pass', 'data': {}}

    def _find_uncertain_regions(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Identify regions of text that might be uncertain
        These need manual review
        """
        uncertain = []

        # Look for patterns that suggest OCR uncertainty
        patterns = [
            (r'[^\w\s]{3,}', 'Multiple consecutive special characters'),
            (r'\b\w{20,}\b', 'Unusually long word'),
            (r'\b[A-Z]{5,}\b', 'Long all-caps sequence'),
            (r'\d[A-Za-z]\d', 'Mixed digit-letter-digit pattern'),
        ]

        for pattern, reason in patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start, end = match.span()
                context_start = max(0, start - 30)
                context_end = min(len(text), end + 30)

                uncertain.append({
                    'position': start,
                    'length': end - start,
                    'text': match.group(),
                    'context': text[context_start:context_end],
                    'reason': reason
                })

        return uncertain

    def _generate_recommendations(self, warnings: List[Dict], errors: List[Dict]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []

        if errors:
            recommendations.append("CRITICAL: Manual review required due to errors")

        for warning in warnings:
            check = warning.get('check')
            if check == 'character_distribution':
                recommendations.append("Review text for OCR artifacts and special characters")
            elif check == 'word_validity':
                recommendations.append("Check for noisy words and OCR errors")
            elif check == 'sentence_structure':
                recommendations.append("Verify sentence boundaries and capitalization")

        if not recommendations:
            recommendations.append("Quality checks passed - text looks good")

        return recommendations
