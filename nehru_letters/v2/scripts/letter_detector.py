#!/usr/bin/env python3
"""
Smart letter boundary detection using multiple methods.
Combines pattern matching, TOC parsing, and LLM analysis.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import anthropic
import os


@dataclass
class LetterBoundary:
    """Represents a detected letter boundary."""
    letter_number: int
    title: str
    start_page: int
    end_page: int
    confidence: float  # 0-1
    detection_method: str
    date: Optional[str] = None
    recipient: Optional[str] = None


class TableOfContentsParser:
    """Extract letter information from table of contents."""

    def parse(self, toc_text: str) -> List[Dict]:
        """
        Parse TOC to extract letter information.

        Args:
            toc_text: Text of the table of contents pages

        Returns:
            List of {number, title, page} dicts
        """
        letters = []

        # Pattern: "NUMBER Title ... PAGE"
        # Example: "1 The Book of Nature ... 10"
        pattern = r'(\d+)\s+(.+?)\s+\.+\s+(\d+)'

        matches = re.finditer(pattern, toc_text)

        for match in matches:
            letter_num = int(match.group(1))
            title = match.group(2).strip()
            page = int(match.group(3))

            letters.append({
                'number': letter_num,
                'title': title,
                'page': page
            })

        return letters


class PatternBasedDetector:
    """Detect letter boundaries using regex patterns."""

    def detect(self, all_pages_text: List[Tuple[int, str]]) -> List[LetterBoundary]:
        """
        Detect boundaries using patterns.

        Args:
            all_pages_text: List of (page_num, page_text) tuples

        Returns:
            List of detected boundaries
        """
        boundaries = []

        for page_num, text in all_pages_text:
            lines = text.split('\n')

            for i, line in enumerate(lines):
                # Check for Roman numerals as letter numbers
                if re.match(r'^\s*([IVX]+)\s*$', line.strip()):
                    boundaries.append(LetterBoundary(
                        letter_number=self._roman_to_int(line.strip()),
                        title="",  # Will be filled in later
                        start_page=page_num,
                        end_page=page_num,  # Will be updated
                        confidence=0.8,
                        detection_method="pattern_roman_numeral"
                    ))

                # Check for "LETTER" keyword
                if re.search(r'\bLETTER\s+(\d+|[IVX]+)\b', line, re.IGNORECASE):
                    match = re.search(r'LETTER\s+(\d+|[IVX]+)', line, re.IGNORECASE)
                    num_str = match.group(1)
                    if num_str.isdigit():
                        letter_num = int(num_str)
                    else:
                        letter_num = self._roman_to_int(num_str)

                    boundaries.append(LetterBoundary(
                        letter_number=letter_num,
                        title=line.strip(),
                        start_page=page_num,
                        end_page=page_num,
                        confidence=0.9,
                        detection_method="pattern_letter_keyword"
                    ))

                # Check for all-caps titles (likely chapter/letter titles)
                if (re.match(r'^[A-Z\s]{10,}$', line.strip()) and
                    len(line.strip()) > 10 and
                    len(line.strip()) < 100):

                    boundaries.append(LetterBoundary(
                        letter_number=0,  # Unknown, will be inferred
                        title=line.strip(),
                        start_page=page_num,
                        end_page=page_num,
                        confidence=0.6,
                        detection_method="pattern_allcaps_title"
                    ))

        return boundaries

    def _roman_to_int(self, s: str) -> int:
        """Convert Roman numeral to integer."""
        roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        result = 0
        prev_value = 0

        for char in reversed(s.upper()):
            value = roman.get(char, 0)
            if value < prev_value:
                result -= value
            else:
                result += value
            prev_value = value

        return result


class LLMLetterDetector:
    """Use LLM to intelligently detect letter boundaries."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def detect(
        self,
        all_pages_text: List[Tuple[int, str]],
        toc_hints: Optional[List[Dict]] = None
    ) -> List[LetterBoundary]:
        """
        Use LLM to detect letter boundaries.

        Args:
            all_pages_text: List of (page_num, page_text) tuples
            toc_hints: Optional TOC information to guide detection

        Returns:
            List of detected boundaries
        """
        if not self.client:
            print("LLM detector not available (no API key)")
            return []

        # Combine all text with page markers
        full_text = ""
        for page_num, text in all_pages_text:
            full_text += f"\n{'='*60}\nPAGE {page_num}\n{'='*60}\n{text}\n"

        # Build prompt
        toc_context = ""
        if toc_hints:
            toc_context = "\n\nTable of Contents hints:\n"
            for hint in toc_hints:
                toc_context += f"  Letter {hint['number']}: {hint['title']} (around page {hint['page']})\n"

        prompt = f"""You are analyzing "Letters from a Father to His Daughter" by Jawaharlal Nehru.

**Task:** Identify the boundaries of each individual letter in this book.

{toc_context}

**Full book text:**
{full_text[:50000]}  {# Limit to avoid token limits #}

**Instructions:**
1. Identify where each letter begins (page number)
2. Identify where each letter ends (page number)
3. Extract the letter title or first few words
4. Note any dates you find
5. Ignore front matter (title pages, prefaces, table of contents)
6. The actual letters likely start after page 10

**Output format (JSON array):**
[
  {{
    "letter_number": 1,
    "title": "The Book of Nature",
    "start_page": 10,
    "end_page": 12,
    "date": "1928" or null,
    "confidence": 0.95
  }},
  ...
]

Provide ONLY the JSON array, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # Extract JSON
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                boundaries = []
                for item in data:
                    boundaries.append(LetterBoundary(
                        letter_number=item.get('letter_number', 0),
                        title=item.get('title', ''),
                        start_page=item.get('start_page', 0),
                        end_page=item.get('end_page', 0),
                        confidence=item.get('confidence', 0.5),
                        detection_method="llm_analysis",
                        date=item.get('date')
                    ))

                return boundaries

        except Exception as e:
            print(f"LLM detection failed: {e}")

        return []


class LetterBoundaryDetector:
    """
    Multi-method letter boundary detector.
    Combines TOC parsing, pattern matching, and LLM analysis.
    """

    def __init__(self, use_llm: bool = True):
        self.toc_parser = TableOfContentsParser()
        self.pattern_detector = PatternBasedDetector()
        self.llm_detector = LLMLetterDetector() if use_llm else None

    def detect_all(
        self,
        all_pages_text: List[Tuple[int, str]],
        toc_pages: Optional[List[int]] = None
    ) -> List[LetterBoundary]:
        """
        Detect letter boundaries using all methods and combine results.

        Args:
            all_pages_text: List of (page_num, page_text) tuples
            toc_pages: Optional list of page numbers that contain TOC

        Returns:
            List of final letter boundaries (consensus)
        """
        print("\n🔍 Detecting letter boundaries...")

        # Method 1: Parse TOC if provided
        toc_hints = []
        if toc_pages:
            toc_text = '\n\n'.join(
                text for page_num, text in all_pages_text
                if page_num in toc_pages
            )
            toc_hints = self.toc_parser.parse(toc_text)
            print(f"  TOC Parser: Found {len(toc_hints)} letters")

        # Method 2: Pattern-based detection
        pattern_boundaries = self.pattern_detector.detect(all_pages_text)
        print(f"  Pattern Detector: Found {len(pattern_boundaries)} boundaries")

        # Method 3: LLM analysis
        llm_boundaries = []
        if self.llm_detector:
            llm_boundaries = self.llm_detector.detect(all_pages_text, toc_hints)
            print(f"  LLM Detector: Found {len(llm_boundaries)} letters")

        # Combine results
        final_boundaries = self._combine_results(
            toc_hints,
            pattern_boundaries,
            llm_boundaries
        )

        print(f"  ✓ Final consensus: {len(final_boundaries)} letters detected")

        return final_boundaries

    def _combine_results(
        self,
        toc_hints: List[Dict],
        pattern_boundaries: List[LetterBoundary],
        llm_boundaries: List[LetterBoundary]
    ) -> List[LetterBoundary]:
        """Combine results from multiple detection methods."""

        # If LLM detected letters, use those as primary source
        if llm_boundaries:
            # Enhance with TOC titles if available
            if toc_hints:
                toc_by_num = {h['number']: h for h in toc_hints}
                for boundary in llm_boundaries:
                    if boundary.letter_number in toc_by_num:
                        toc_entry = toc_by_num[boundary.letter_number]
                        if not boundary.title:
                            boundary.title = toc_entry['title']
            return sorted(llm_boundaries, key=lambda b: b.start_page)

        # Otherwise, use TOC + pattern matching
        if toc_hints:
            boundaries = []
            for hint in toc_hints:
                # Find end page from next letter's start
                next_hint = next(
                    (h for h in toc_hints if h['number'] == hint['number'] + 1),
                    None
                )
                end_page = next_hint['page'] - 1 if next_hint else 999

                boundaries.append(LetterBoundary(
                    letter_number=hint['number'],
                    title=hint['title'],
                    start_page=hint['page'],
                    end_page=end_page,
                    confidence=0.85,
                    detection_method="toc_plus_inference"
                ))
            return boundaries

        # Fallback: just pattern boundaries
        return sorted(pattern_boundaries, key=lambda b: b.start_page)

    def save_boundaries(self, boundaries: List[LetterBoundary], output_path: Path):
        """Save detected boundaries to JSON file."""
        data = [
            {
                'letter_number': b.letter_number,
                'title': b.title,
                'start_page': b.start_page,
                'end_page': b.end_page,
                'confidence': b.confidence,
                'detection_method': b.detection_method,
                'date': b.date,
                'recipient': b.recipient
            }
            for b in boundaries
        ]

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved boundaries to {output_path}")
