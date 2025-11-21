#!/usr/bin/env python3
"""Analyze existing OCR quality and extract statistics."""

import re
from collections import Counter

def analyze_ocr_quality(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Statistics
    total_lines = len(lines)
    non_empty_lines = len([l for l in lines if l.strip()])
    avg_line_length = sum(len(l) for l in lines) / max(1, total_lines)
    
    # Look for common OCR artifacts
    artifacts = {
        'mixed_case_words': len(re.findall(r'\b[a-z]+[A-Z]+[a-z]*\b|\b[A-Z]+[a-z]+[A-Z]+\b', content)),
        'single_chars': len(re.findall(r'\b[a-zA-Z]\b', content)),
        'numbers_in_words': len(re.findall(r'\b[a-zA-Z]+\d+[a-zA-Z]*\b|\b\d+[a-zA-Z]+\d*\b', content)),
        'special_chars': len(re.findall(r'[^\w\s\.,!?;:\-\'"()]', content)),
        'multiple_spaces': len(re.findall(r' {3,}', content)),
        'broken_words': len(re.findall(r'\b[a-z]+ [a-z]+\b', content))  # Approximate
    }
    
    # Find potential letter boundaries (common patterns)
    letter_patterns = [
        r'LETTER\s+\d+',
        r'Letter\s+\d+',
        r'^\d+$',  # Standalone numbers
        r'Dear\s+\w+',
        r'Yours\s+\w+',
    ]
    
    potential_letters = []
    for i, line in enumerate(lines):
        for pattern in letter_patterns:
            if re.search(pattern, line):
                potential_letters.append((i, line.strip()))
                break
    
    print("=== OCR Quality Analysis ===\n")
    print(f"Total lines: {total_lines}")
    print(f"Non-empty lines: {non_empty_lines}")
    print(f"Average line length: {avg_line_length:.1f} chars")
    print(f"\n=== OCR Artifacts ===")
    for artifact, count in artifacts.items():
        print(f"{artifact}: {count}")
    
    print(f"\n=== Potential Letter Boundaries ({len(potential_letters)}) ===")
    for line_num, content in potential_letters[:20]:  # Show first 20
        print(f"Line {line_num}: {content[:80]}")
    
    # Sample some actual content (middle section)
    print(f"\n=== Sample Content (lines 500-520) ===")
    for i, line in enumerate(lines[500:520], start=500):
        print(f"{i}: {line}")

if __name__ == "__main__":
    import sys
    analyze_ocr_quality(sys.argv[1] if len(sys.argv) > 1 else "../raw_scans/existing_ocr.txt")
