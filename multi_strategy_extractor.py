#!/usr/bin/env python3
"""
Multi-Strategy Letter Extraction Framework
Implements multiple competing extraction strategies and compares results
"""

import re
import json
from typing import Dict, List, Tuple
from collections import Counter
from abc import ABC, abstractmethod


class ExtractionStrategy(ABC):
    """Base class for extraction strategies"""

    @abstractmethod
    def name(self) -> str:
        """Return strategy name"""
        pass

    @abstractmethod
    def extract_letters(self, ocr_text: Dict[int, str]) -> List[Dict]:
        """Extract letters from OCR text"""
        pass

    @abstractmethod
    def confidence_score(self, letter: Dict) -> float:
        """Calculate confidence score for extracted letter (0-1)"""
        pass


class RomanNumeralStrategy(ExtractionStrategy):
    """Extract letters based on Roman numeral markers"""

    def name(self) -> str:
        return "Roman Numeral Strategy"

    def extract_letters(self, ocr_text: Dict[int, str]) -> List[Dict]:
        """Find letters marked by Roman numerals"""
        boundaries = []

        # Roman numeral pattern (I, II, III, IV, etc.)
        roman_pattern = re.compile(r'^([IVXLCDM]{1,6})\s*\.?\s*$')

        for page_num in sorted(ocr_text.keys()):
            lines = ocr_text[page_num].split('\n')

            for line_num, line in enumerate(lines):
                line = line.strip()
                if roman_pattern.match(line):
                    boundaries.append({
                        'page': page_num,
                        'line': line_num,
                        'marker': line,
                        'type': 'roman_numeral'
                    })

        return self._extract_content(ocr_text, boundaries)

    def _extract_content(self, ocr_text, boundaries):
        """Extract content between boundaries"""
        letters = []

        for i, boundary in enumerate(boundaries):
            start_page = boundary['page']
            start_line = boundary['line']

            # Determine end
            if i + 1 < len(boundaries):
                end_page = boundaries[i + 1]['page']
                end_line = boundaries[i + 1]['line']
            else:
                end_page = max(ocr_text.keys())
                end_line = None

            # Extract text
            content = self._extract_between(ocr_text, start_page, start_line, end_page, end_line)

            # Extract metadata
            letter_data = {
                'number': i + 1,
                'marker': boundary['marker'],
                'start_page': start_page,
                'end_page': end_page,
                'content': content,
                'word_count': len(content.split()),
                'strategy': self.name()
            }

            # Try to extract date
            date_match = re.search(
                r'((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,.]?\s+\d{1,2}(?:st|nd|rd|th)?[,.]?\s+\d{4})',
                content,
                re.IGNORECASE
            )
            if date_match:
                letter_data['date'] = date_match.group(1)

            # Try to extract recipient
            recipient_match = re.search(r'(?:Dear|My dear)\s+([^,\n]{3,30})', content)
            if recipient_match:
                letter_data['recipient'] = recipient_match.group(1).strip()

            letters.append(letter_data)

        return letters

    def _extract_between(self, ocr_text, start_page, start_line, end_page, end_line):
        """Helper to extract text between boundaries"""
        text_parts = []

        for page_num in range(start_page, end_page + 1):
            if page_num not in ocr_text:
                continue

            lines = ocr_text[page_num].split('\n')

            if page_num == start_page and page_num == end_page:
                if end_line is not None:
                    text_parts.extend(lines[start_line:end_line])
                else:
                    text_parts.extend(lines[start_line:])
            elif page_num == start_page:
                text_parts.extend(lines[start_line:])
            elif page_num == end_page:
                if end_line is not None:
                    text_parts.extend(lines[:end_line])
                else:
                    text_parts.extend(lines)
            else:
                text_parts.extend(lines)

        return '\n'.join(text_parts).strip()

    def confidence_score(self, letter: Dict) -> float:
        """Calculate confidence based on letter characteristics"""
        score = 0.5  # Base score

        # Bonus for reasonable length
        if 100 < letter['word_count'] < 5000:
            score += 0.2

        # Bonus for having a valid Roman numeral marker
        if re.match(r'^[IVXLCDM]+$', letter['marker']):
            score += 0.2

        # Penalty for very short content
        if letter['word_count'] < 50:
            score -= 0.3

        return max(0.0, min(1.0, score))


class DateHeaderStrategy(ExtractionStrategy):
    """Extract letters based on date headers"""

    def name(self) -> str:
        return "Date Header Strategy"

    def extract_letters(self, ocr_text: Dict[int, str]) -> List[Dict]:
        """Find letters that start with date headers"""
        boundaries = []

        # Date patterns at start of letter
        date_patterns = [
            r'^(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,.]?\s+\d{1,2}(?:st|nd|rd|th)?[,.]?\s*\d{4}?',
            r'^\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,.]?\s*\d{4}?',
        ]

        for page_num in sorted(ocr_text.keys()):
            lines = ocr_text[page_num].split('\n')

            for line_num, line in enumerate(lines):
                line = line.strip()
                for pattern in date_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        boundaries.append({
                            'page': page_num,
                            'line': line_num,
                            'marker': line,
                            'type': 'date'
                        })
                        break

        return RomanNumeralStrategy()._extract_content(ocr_text, boundaries)

    def confidence_score(self, letter: Dict) -> float:
        """Calculate confidence score"""
        score = 0.5

        # Bonus for having a date in content
        if re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)', letter['content'], re.IGNORECASE):
            score += 0.3

        # Bonus for reasonable length
        if 100 < letter['word_count'] < 5000:
            score += 0.1

        return max(0.0, min(1.0, score))


class ChapterBreakStrategy(ExtractionStrategy):
    """Extract letters based on chapter breaks and page patterns"""

    def name(self) -> str:
        return "Chapter Break Strategy"

    def extract_letters(self, ocr_text: Dict[int, str]) -> List[Dict]:
        """Find letters based on structural breaks in the document"""
        boundaries = []

        for page_num in sorted(ocr_text.keys()):
            text = ocr_text[page_num]
            lines = text.split('\n')

            for line_num, line in enumerate(lines):
                line = line.strip()

                # Look for chapter markers
                if re.match(r'^CHAPTER\s+[IVXLCDM]+', line, re.IGNORECASE):
                    boundaries.append({
                        'page': page_num,
                        'line': line_num,
                        'marker': line,
                        'type': 'chapter'
                    })

                # Look for numbered sections
                elif re.match(r'^(?:LETTER\s+)?(?:\d+|[IVXLCDM]+)\s*$', line, re.IGNORECASE):
                    boundaries.append({
                        'page': page_num,
                        'line': line_num,
                        'marker': line,
                        'type': 'numbered_section'
                    })

        return RomanNumeralStrategy()._extract_content(ocr_text, boundaries)

    def confidence_score(self, letter: Dict) -> float:
        """Calculate confidence score"""
        score = 0.4

        # Bonus for chapter markers
        if 'CHAPTER' in letter.get('marker', '').upper():
            score += 0.3

        # Bonus for reasonable length
        if 500 < letter['word_count'] < 10000:
            score += 0.2

        return max(0.0, min(1.0, score))


class HybridStrategy(ExtractionStrategy):
    """Hybrid approach combining multiple signals"""

    def name(self) -> str:
        return "Hybrid Multi-Signal Strategy"

    def extract_letters(self, ocr_text: Dict[int, str]) -> List[Dict]:
        """Combine Roman numerals, dates, and structural breaks"""
        boundaries = []

        for page_num in sorted(ocr_text.keys()):
            text = ocr_text[page_num]
            lines = text.split('\n')

            for line_num, line in enumerate(lines):
                line = line.strip()
                score = 0
                marker_type = []

                # Check for Roman numeral
                if re.match(r'^([IVXLCDM]{1,6})\s*\.?\s*$', line):
                    score += 3
                    marker_type.append('roman')

                # Check for date
                if re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)', line, re.IGNORECASE):
                    score += 2
                    marker_type.append('date')

                # Check for chapter
                if re.match(r'^(?:CHAPTER|LETTER)', line, re.IGNORECASE):
                    score += 2
                    marker_type.append('chapter')

                # Check for page break patterns
                if line_num < 5 and len(line) < 50:  # Early in page, short text
                    score += 1
                    marker_type.append('page_break')

                # If strong enough signal, add as boundary
                if score >= 2:
                    boundaries.append({
                        'page': page_num,
                        'line': line_num,
                        'marker': line,
                        'type': '+'.join(marker_type),
                        'signal_strength': score
                    })

        # Sort by signal strength and remove duplicates/nearby boundaries
        boundaries = self._deduplicate_boundaries(boundaries)

        return RomanNumeralStrategy()._extract_content(ocr_text, boundaries)

    def _deduplicate_boundaries(self, boundaries):
        """Remove boundaries that are too close together"""
        if not boundaries:
            return []

        # Sort by page then line
        boundaries = sorted(boundaries, key=lambda x: (x['page'], x['line']))

        result = [boundaries[0]]

        for b in boundaries[1:]:
            last = result[-1]

            # If this boundary is within 2 pages of the last, keep the stronger one
            if b['page'] - last['page'] <= 2:
                if b.get('signal_strength', 0) > last.get('signal_strength', 0):
                    result[-1] = b
            else:
                result.append(b)

        return result

    def confidence_score(self, letter: Dict) -> float:
        """Calculate confidence score based on multiple factors"""
        score = 0.6  # Higher base for hybrid

        # Bonus for multiple signal types
        marker_type = letter.get('marker', '')
        if '+' in marker_type:
            score += 0.2

        # Bonus for good length
        if 200 < letter['word_count'] < 3000:
            score += 0.2

        return max(0.0, min(1.0, score))


class StrategyComparator:
    """Compare results from multiple extraction strategies"""

    def __init__(self):
        self.strategies = [
            RomanNumeralStrategy(),
            DateHeaderStrategy(),
            ChapterBreakStrategy(),
            HybridStrategy()
        ]
        self.results = {}

    def run_all_strategies(self, ocr_text: Dict[int, str]):
        """Run all strategies and collect results"""
        print("\n" + "=" * 80)
        print("MULTI-STRATEGY EXTRACTION COMPARISON")
        print("=" * 80)

        for strategy in self.strategies:
            print(f"\n🔄 Running: {strategy.name()}...")
            letters = strategy.extract_letters(ocr_text)

            # Calculate confidence scores
            for letter in letters:
                letter['confidence'] = strategy.confidence_score(letter)

            self.results[strategy.name()] = letters

            print(f"   ✓ Extracted {len(letters)} letters")
            if letters:
                avg_confidence = sum(l['confidence'] for l in letters) / len(letters)
                avg_words = sum(l['word_count'] for l in letters) / len(letters)
                print(f"   📊 Avg confidence: {avg_confidence:.2f}")
                print(f"   📊 Avg words/letter: {avg_words:.0f}")

    def compare_results(self):
        """Generate comparison report"""
        print("\n" + "=" * 80)
        print("STRATEGY COMPARISON REPORT")
        print("=" * 80)

        comparison = []

        for strategy_name, letters in self.results.items():
            if not letters:
                continue

            avg_confidence = sum(l['confidence'] for l in letters) / len(letters)
            avg_words = sum(l['word_count'] for l in letters) / len(letters)
            total_words = sum(l['word_count'] for l in letters)

            # Count letters in different quality tiers
            high_conf = sum(1 for l in letters if l['confidence'] >= 0.7)
            med_conf = sum(1 for l in letters if 0.4 <= l['confidence'] < 0.7)
            low_conf = sum(1 for l in letters if l['confidence'] < 0.4)

            comparison.append({
                'strategy': strategy_name,
                'total_letters': len(letters),
                'avg_confidence': avg_confidence,
                'avg_words': avg_words,
                'total_words': total_words,
                'high_confidence': high_conf,
                'medium_confidence': med_conf,
                'low_confidence': low_conf,
                'quality_score': avg_confidence * (len(letters) / 100)  # Combined metric
            })

        # Sort by quality score
        comparison = sorted(comparison, key=lambda x: x['quality_score'], reverse=True)

        print(f"\n{'Strategy':<35} {'Letters':<10} {'Avg Conf':<12} {'Quality':<10}")
        print("-" * 80)

        for c in comparison:
            print(f"{c['strategy']:<35} {c['total_letters']:<10} {c['avg_confidence']:<12.2f} {c['quality_score']:<10.2f}")

        print("\n🏆 WINNER: " + comparison[0]['strategy'])
        print(f"   Extracted: {comparison[0]['total_letters']} letters")
        print(f"   Avg Confidence: {comparison[0]['avg_confidence']:.2f}")
        print(f"   High confidence letters: {comparison[0]['high_confidence']}")

        return comparison

    def save_comparison(self, output_file: str = 'strategy_comparison.json'):
        """Save detailed comparison to JSON"""
        report = {
            'strategies': []
        }

        for strategy_name, letters in self.results.items():
            if not letters:
                continue

            avg_confidence = sum(l['confidence'] for l in letters) / len(letters)

            report['strategies'].append({
                'name': strategy_name,
                'letter_count': len(letters),
                'avg_confidence': avg_confidence,
                'letters': [
                    {
                        'number': l['number'],
                        'marker': l['marker'],
                        'pages': f"{l['start_page']}-{l['end_page']}",
                        'start_page': l['start_page'],
                        'end_page': l['end_page'],
                        'word_count': l['word_count'],
                        'confidence': l['confidence'],
                        'date': l.get('date', 'Unknown'),
                        'recipient': l.get('recipient', 'Unknown'),
                        'content': l['content'],  # Full content
                        'preview': l['content'][:200]
                    }
                    for l in letters
                ]
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Detailed comparison saved to: {output_file}")

    def get_best_extraction(self) -> Tuple[str, List[Dict]]:
        """Return the best extraction strategy and its results"""
        comparison = self.compare_results()
        best = comparison[0]
        return best['strategy'], self.results[best['strategy']]


def main():
    # Load OCR text
    import os

    ocr_file = 'tagore_full_ocr.json'
    if not os.path.exists(ocr_file):
        print(f"⚠ {ocr_file} not found. Waiting for full OCR extraction to complete...")
        return

    print("📂 Loading OCR text...")
    with open(ocr_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        ocr_text = {int(k): v for k, v in data.items()}

    print(f"✓ Loaded {len(ocr_text)} pages")

    # Run multi-strategy comparison
    comparator = StrategyComparator()
    comparator.run_all_strategies(ocr_text)
    comparator.compare_results()
    comparator.save_comparison()

    # Get best results
    best_strategy, best_letters = comparator.get_best_extraction()

    print(f"\n📝 Using best strategy: {best_strategy}")
    print(f"   Total letters: {len(best_letters)}")


if __name__ == '__main__':
    main()
