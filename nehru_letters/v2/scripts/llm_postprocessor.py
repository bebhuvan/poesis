#!/usr/bin/env python3
"""
LLM-based intelligent post-processing for OCR results.
Uses Claude to fix errors, clean artifacts, and improve quality.
"""

import anthropic
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
import json
import re


@dataclass
class PostProcessingResult:
    """Result of LLM post-processing."""
    original_text: str
    corrected_text: str
    changes_made: List[str]
    confidence_notes: List[str]
    artifacts_removed: List[str]
    error_corrections: Dict[str, str]


class LLMPostProcessor:
    """Use Claude to intelligently post-process OCR results."""

    def __init__(self, api_key: str = None):
        """
        Initialize LLM post-processor.

        Args:
            api_key: Anthropic API key (defaults to env var ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set ANTHROPIC_API_KEY environment variable.")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def process_page(
        self,
        ocr_text: str,
        page_number: int,
        context: str = "",
        fast_mode: bool = False
    ) -> PostProcessingResult:
        """
        Process a single page of OCR text with LLM.

        Args:
            ocr_text: Raw OCR output
            page_number: Page number for context
            context: Additional context about the document
            fast_mode: Use faster model for quicker processing

        Returns:
            PostProcessingResult with corrections
        """
        prompt = self._build_prompt(ocr_text, page_number, context)

        # Use Haiku for fast mode, Sonnet for quality
        model = "claude-haiku-4-5-20250929" if fast_mode else self.model

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text

            # Parse the response
            return self._parse_response(ocr_text, result_text)

        except Exception as e:
            print(f"LLM post-processing failed: {e}")
            # Return original text if processing fails
            return PostProcessingResult(
                original_text=ocr_text,
                corrected_text=ocr_text,
                changes_made=[],
                confidence_notes=[f"Processing failed: {str(e)}"],
                artifacts_removed=[],
                error_corrections={}
            )

    def _build_prompt(self, ocr_text: str, page_number: int, context: str) -> str:
        """Build prompt for LLM processing."""
        return f"""You are an expert OCR post-processor working on historical letters from Jawaharlal Nehru to his daughter Indira (1920s-1930s).

**Your task:** Clean and correct OCR errors while preserving the original meaning and style.

**Page {page_number} OCR Output:**
```
{ocr_text}
```

**Context:** {context if context else "Letters from a Father to His Daughter by Jawaharlal Nehru"}

**Instructions:**
1. Fix obvious OCR errors (e.g., "vesterday" → "yesterday", "tho" → "the")
2. Remove artifacts (page numbers, library stamps, single random characters)
3. Preserve historical spelling and style from the 1920s-1930s
4. Fix formatting (remove spurious line breaks, preserve paragraph structure)
5. Keep proper names, places, and historical terms exactly as written (unless clearly an OCR error)
6. Add subtle markers like [?] if uncertain about a correction
7. Preserve all actual letter content

**Output format (JSON):**
{{
  "corrected_text": "the fully corrected text",
  "changes_made": ["list of significant changes made"],
  "confidence_notes": ["list of uncertain areas marked with [?]"],
  "artifacts_removed": ["list of removed artifacts"],
  "error_corrections": {{"original": "corrected", ...}}
}}

Think carefully. Be conservative - only fix clear errors. When in doubt, preserve the original."""

    def _parse_response(self, original: str, response: str) -> PostProcessingResult:
        """Parse LLM response into structured result."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                return PostProcessingResult(
                    original_text=original,
                    corrected_text=data.get('corrected_text', original),
                    changes_made=data.get('changes_made', []),
                    confidence_notes=data.get('confidence_notes', []),
                    artifacts_removed=data.get('artifacts_removed', []),
                    error_corrections=data.get('error_corrections', {})
                )
            else:
                # If no JSON found, treat entire response as corrected text
                return PostProcessingResult(
                    original_text=original,
                    corrected_text=response,
                    changes_made=["LLM corrected text"],
                    confidence_notes=[],
                    artifacts_removed=[],
                    error_corrections={}
                )

        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return PostProcessingResult(
                original_text=original,
                corrected_text=original,
                changes_made=[],
                confidence_notes=[f"Parse error: {str(e)}"],
                artifacts_removed=[],
                error_corrections={}
            )

    def process_batch(
        self,
        texts: List[Tuple[str, int]],
        context: str = "",
        fast_mode: bool = False
    ) -> List[PostProcessingResult]:
        """
        Process multiple pages in batch.

        Args:
            texts: List of (ocr_text, page_number) tuples
            context: Document context
            fast_mode: Use faster processing

        Returns:
            List of PostProcessingResult objects
        """
        results = []

        for ocr_text, page_num in texts:
            print(f"  LLM processing page {page_num}...")
            result = self.process_page(ocr_text, page_num, context, fast_mode)
            results.append(result)

        return results


class SimplePostProcessor:
    """
    Fallback post-processor that doesn't use LLM.
    Uses regex and heuristics for basic cleanup.
    """

    def __init__(self):
        self.common_errors = {
            'vesterday': 'yesterday',
            'tho': 'the',
            'thoy': 'they',
            'wero': 'were',
            'whilo': 'while',
            'vory': 'very',
            'soo': 'see',
            'boen': 'been',
            'moro': 'more',
            'thore': 'there',
            'whon': 'when',
            'yoar': 'year',
            'yoars': 'years',
        }

    def process_page(self, ocr_text: str, page_number: int) -> PostProcessingResult:
        """Simple regex-based post-processing."""
        corrected = ocr_text
        changes = []
        errors_fixed = {}

        # Fix common OCR errors
        for wrong, right in self.common_errors.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, right)
                changes.append(f"Fixed '{wrong}' → '{right}'")
                errors_fixed[wrong] = right

        # Remove common artifacts
        artifacts = []

        # Remove standalone page numbers
        corrected = re.sub(r'^\s*\d+\s*$', '', corrected, flags=re.MULTILINE)
        if corrected != ocr_text:
            artifacts.append("page numbers")

        # Remove single character lines (often artifacts)
        lines_before = len(corrected.split('\n'))
        corrected = '\n'.join(
            line for line in corrected.split('\n')
            if len(line.strip()) != 1 or line.strip().isalpha()
        )
        lines_removed = lines_before - len(corrected.split('\n'))
        if lines_removed > 0:
            artifacts.append(f"{lines_removed} single-character lines")

        # Fix excessive whitespace
        corrected = re.sub(r'\n{4,}', '\n\n\n', corrected)
        corrected = re.sub(r' {3,}', ' ', corrected)

        return PostProcessingResult(
            original_text=ocr_text,
            corrected_text=corrected,
            changes_made=changes,
            confidence_notes=[],
            artifacts_removed=artifacts,
            error_corrections=errors_fixed
        )
