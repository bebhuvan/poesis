#!/usr/bin/env python3
"""
Intelligent post-processing for OCR text.
Cleans artifacts while preserving authorial intent.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class CleaningReport:
    """Report of cleaning operations performed."""
    original_lines: int
    cleaned_lines: int
    artifacts_removed: List[str]
    hyphenations_fixed: int
    formatting_preserved: List[str]


class OCRPostProcessor:
    """Intelligent post-processor for historical document OCR."""
    
    def __init__(self, aggressive=False):
        """
        Initialize post-processor.
        
        Args:
            aggressive: If True, apply more aggressive cleaning.
                       If False, preserve more original formatting.
        """
        self.aggressive = aggressive
        self.report = CleaningReport(
            original_lines=0,
            cleaned_lines=0,
            artifacts_removed=[],
            hyphenations_fixed=0,
            formatting_preserved=[]
        )
    
    def clean_text(self, text: str) -> Tuple[str, CleaningReport]:
        """
        Clean OCR text while preserving authorial intent.
        
        Returns:
            Tuple of (cleaned_text, cleaning_report)
        """
        lines = text.split('\n')
        self.report.original_lines = len(lines)
        
        # Step 1: Remove common OCR artifacts
        lines = self._remove_artifacts(lines)
        
        # Step 2: Handle underscores (from underlined text)
        lines = self._handle_underscores(lines)
        
        # Step 3: Fix hyphenation across lines
        text = '\n'.join(lines)
        text = self._fix_hyphenation(text)
        
        # Step 4: Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # Step 5: Fix common OCR errors
        text = self._fix_common_errors(text)
        
        # Step 6: Preserve paragraph structure
        text = self._normalize_paragraphs(text)
        
        self.report.cleaned_lines = len(text.split('\n'))
        
        return text, self.report
    
    def _remove_artifacts(self, lines: List[str]) -> List[str]:
        """Remove common OCR artifacts."""
        cleaned = []
        
        for line in lines:
            original = line
            
            # Remove page numbers (standalone numbers)
            if re.match(r'^\s*\d{1,3}\s*$', line):
                self.report.artifacts_removed.append(f"Page number: {line.strip()}")
                continue
            
            # Remove isolated single characters (likely artifacts)
            if self.aggressive and re.match(r'^\s*[a-zA-Z_\-\.]\s*$', line):
                self.report.artifacts_removed.append(f"Single char: {line.strip()}")
                continue
            
            # Keep the line
            cleaned.append(line)
        
        return cleaned
    
    def _handle_underscores(self, lines: List[str]) -> List[str]:
        """Handle underscores from underlined text."""
        cleaned = []
        
        for line in lines:
            # Pattern: "_ word" or "word _word" -> underlined text
            # We'll preserve this but could convert to markdown later
            
            # Remove leading underscores before words (Tesseract artifact)
            line = re.sub(r'_\s+(\w)', r'\1', line)
            
            # Remove trailing underscores after words
            line = re.sub(r'(\w)\s+_', r'\1', line)
            
            # Note preserved formatting
            if '_' in line:
                self.report.formatting_preserved.append(f"Underline: {line[:50]}")
            
            cleaned.append(line)
        
        return cleaned
    
    def _fix_hyphenation(self, text: str) -> str:
        """Fix hyphenation across line breaks."""
        # Pattern: "word-\n" should become "word"
        count = 0
        
        def replace_hyphen(match):
            nonlocal count
            count += 1
            return match.group(1)
        
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', replace_hyphen, text)
        
        self.report.hyphenations_fixed = count
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace while preserving structure."""
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        
        # Remove multiple spaces within lines (but preserve indentation)
        cleaned_lines = []
        for line in lines:
            # Preserve leading whitespace
            leading = len(line) - len(line.lstrip())
            content = line.lstrip()
            
            # Collapse multiple spaces in content
            content = re.sub(r' {2,}', ' ', content)
            
            cleaned_lines.append(' ' * leading + content)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_common_errors(self, text: str) -> str:
        """Fix common OCR errors."""
        # Common substitutions (be conservative!)
        fixes = {
            # Only fix obvious errors, not archaic spellings
        }
        
        for wrong, right in fixes.items():
            text = text.replace(wrong, right)
        
        return text
    
    def _normalize_paragraphs(self, text: str) -> str:
        """Normalize paragraph structure."""
        # Collapse multiple blank lines to double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure proper paragraph separation
        # (Groups of text separated by blank lines)
        
        return text.strip()


def process_file(input_path: str, output_path: str, aggressive: bool = False):
    """Process a single OCR file."""
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    processor = OCRPostProcessor(aggressive=aggressive)
    cleaned_text, report = processor.clean_text(text)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    return report


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 3:
        print("Usage: post_process.py <input_file> <output_file> [--aggressive]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    aggressive = '--aggressive' in sys.argv
    
    print(f"Post-processing {input_path}...")
    print(f"Aggressive mode: {aggressive}")
    
    report = process_file(input_path, output_path, aggressive)
    
    print(f"\n=== Cleaning Report ===")
    print(f"Original lines: {report.original_lines}")
    print(f"Cleaned lines: {report.cleaned_lines}")
    print(f"Artifacts removed: {len(report.artifacts_removed)}")
    print(f"Hyphenations fixed: {report.hyphenations_fixed}")
    print(f"Formatting preserved: {len(report.formatting_preserved)}")
    
    if report.artifacts_removed:
        print(f"\nArtifacts removed:")
        for artifact in report.artifacts_removed[:10]:
            print(f"  - {artifact}")
    
    print(f"\nCleaned text saved to: {output_path}")
