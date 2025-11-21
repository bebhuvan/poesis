#!/usr/bin/env python3
"""
Final OCR cleanup pass - character-level corrections
Fixes remaining artifacts: ^, «, ., ', backslash patterns
"""

import re
from pathlib import Path

# Character-level OCR corrections
FINAL_OCR_FIXES = {
    # Character corruption patterns (most common)
    r'(\w)\.([a-z])': r'\1\2',  # Remove periods in middle of words
    r'(\w)\^([a-z])': r'\1\2',  # Remove ^ in middle of words
    r'(\w)«([a-z])': r'\1\2',  # Remove « in middle of words
    r"(\w)'([aeiou])": r'\1\2',  # Remove apostrophe before vowels in middle
    r'(\w)\\d(\w)': r'\1\2',  # Remove \d pattern
    r'(\w)\\([a-z])': r'\1\2',  # Remove backslash

    # Specific word fixes
    r'\bAf\^\'er\b': 'After',
    r'\.answer': 'answer',
    r'\.nswer': 'answer',
    r'population\.Jo': 'population to',
    r'idea\.«': 'ideas',
    r'againasked': 'again asked',
    r'stumblingupon': 'stumbling upon',
    r'guari\^\'an': 'guardian',
    r'pers-m': 'person',
    r'eiigine': 'engine',
    r'romis\^e': 'promise',
    r'maki\^xg': 'making',
    r'in\^a': 'in a',
    r'wji\^\*': 'when',
    r'Sepjetr\\ber': 'September',
    r'v\\ith': 'with',
    r'tir\.rdr': 'tiredness',
    r'that\.iats': 'that lasts',
    r'som\.e': 'some',
    r'ju\.st': 'just',
    r'of\.n': 'often',
    r'no\'ai': 'moral',
    r'itself\.i': 'itself',
    r'i\.ti': 'it',
    r'i\.and': 'and',
    r'harvest\.now': 'harvest now',
    r'dark\.folds': 'dark folds',
    r'but\.Ior': 'but for',
    r'ai\\d': 'and',
    r'agenc\.y': 'agency',
    r'a\.s': 'as',
    r'j\.n': 'in',

    # Spacing issues
    r'\s+\.': '.',  # Remove space before period
    r'\s+,': ',',  # Remove space before comma
    r'([a-z])\s*\.\s*([A-Z])': r'\1. \2',  # Normalize sentence endings

    # Hyphenation artifacts
    r'(\w+)-\s*\n\s*(\w+)': r'\1\2',  # Join hyphenated words across lines

    # Special characters at word boundaries
    r'\b\.(\w)': r'\1',  # Remove leading period
    r'(\w)\.\s+([a-z])': r'\1 \2',  # Period followed by lowercase (not sentence end)

    # Quote marks
    r'■': '',  # Remove filled square
    r'\^': '',  # Remove stray ^
}

def apply_final_ocr_fixes(text: str) -> str:
    """Apply final character-level OCR corrections"""
    cleaned = text

    for pattern, replacement in FINAL_OCR_FIXES.items():
        cleaned = re.sub(pattern, replacement, cleaned)

    # Clean up multiple spaces
    cleaned = re.sub(r'  +', ' ', cleaned)

    # Clean up multiple newlines (max 2)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned

def process_all_letters():
    """Process all 66 letters with final OCR cleanup"""

    input_dir = Path("/home/user/poesis/New tagore 2/tagore_letters_complete_66")

    files = sorted(input_dir.glob("tagore_*.md"))

    print(f"🔧 FINAL OCR CLEANUP PASS")
    print(f"=" * 70)
    print(f"Processing {len(files)} letters...")
    print()

    changes_made = 0

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()

        # Apply fixes
        cleaned = apply_final_ocr_fixes(original)

        # Check if anything changed
        if cleaned != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned)

            # Count changes
            changes = len([i for i in range(len(original)) if i < len(cleaned) and original[i:i+1] != cleaned[i:i+1]])

            if changes > 5:  # Only report significant changes
                changes_made += 1
                print(f"✓ {filepath.name}: ~{changes} character changes")

    print()
    print(f"=" * 70)
    print(f"✅ COMPLETE: {changes_made} files modified")
    print()

if __name__ == '__main__':
    process_all_letters()
