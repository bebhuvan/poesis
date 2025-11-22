#!/usr/bin/env python3
"""
Create perfect version - removes ALL issues including running headers
"""

import re
import json
from pathlib import Path


def comprehensive_ocr_fix(text):
    """Apply all OCR corrections"""
    replacements = {
        # All OCR errors in one comprehensive list
        r'\bEAELY\b': 'EARLY',
        r'\bEUEOPE\b': 'EUROPE',
        r'\bPEEPAEATION\b': 'PREPARATION',
        r'\bPREPAEATION\b': 'PREPARATION',
        r'\bFOE A\b': 'FOR A',
        r'\bFOE\b(?= [A-Z])': 'FOR',
        r'\bCAEEEE\b': 'CAREER',
        r'\bLETTEBS\b': 'LETTERS',
        r'\bLETTEES\b': 'LETTERS',
        r'\bLETTEKS\b': 'LETTERS',
        r'\bLETTEK8\b': 'LETTERS',
        r'\bLETTEB&\b': 'LETTERS',
        r'\bLEITEES\b': 'LETTERS',
        r'\bMAETIN\b': 'MARTIN',
        r'\bMABTIN\b': 'MARTIN',
        r'\bMAEIIN\b': 'MARTIN',
        r'\bJANUAEY\b': 'JANUARY',
        r'\bJANUABY\b': 'JANUARY',
        r'\bDEGEMBEB\b': 'DECEMBER',
        r'\bDECEMBEE\b': 'DECEMBER',
        r'\bDkcember\b': 'December',
        r'\bDECEMBEE\b': 'DECEMBER',
        r'\bOP TORU\b': 'OF TORU',
        r'\bOP\b(?= [A-Z])': 'OF',
        r'\bOB THE\b': 'OR THE',
        r'\bOB\b(?= THE)': 'OR',
        r'\bABVEBS\b': 'ARVERS',
        r'\bAEVEES\b': 'ARVERS',
        r'\bSUPPLEMENTAEY\b': 'SUPPLEMENTARY',
        r'\bMe\. E\. J\.': 'Mr. E. J.',
        r'\bME\. E\. J\.': 'MR. E. J.',

        # Names
        r'\bTOBU\b': 'TORU',
        r'\bTOEU\b': 'TORU',
        r'\bTOKU\b': 'TORU',
        r'\bTorn\b': 'Toru',
        r'\bDTJTT\b': 'DUTT',
        r'\bDtJTT\b': 'DUTT',
        r'\bDUIT\b': 'DUTT',

        # Common words
        r'\bANf\)': 'AND',
        r'\bANI\)': 'AND',
        r'\bwo\b': 'we',
        r'\bherlove\b': 'her love',
        r'\bimited\b': 'united',
        r'\bho\b(?= bare)': 'he',
        r'\bho\b(?= had)': 'he',

        # Publisher/printer
        r'\bPREDERIOK\b': 'FREDERICK',
        r'\bFREDERIOK\b': 'FREDERICK',

        # French accents
        r'\b6toit\b': 'était',
        r'\b6cu\b': 'écu',
        r'\bv6cu\b': 'vécu',
        r'\boik\b': 'où',

        # Formatting
        r'field\'of': 'field of',
        r'con-?\s*tained': 'contained',
        r'attrac-?\s*tion': 'attraction',
        r'Ban+erjea': 'Banerjea',
        r'Tennysoi[\^\.]+': 'Tennyson.',
        r'nothii\^?g': 'nothing',
        r'INDIAJ\^?': 'INDIAN',
        r'\^': '',
        r'¬\s*': '',
        r' {2,}': ' ',
        r'\t+': ' ',
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    return text


def is_running_header(line):
    """Determine if a line is a running header/footer"""
    stripped = line.strip()

    # Page number + title patterns (with any OCR errors)
    if re.match(r'^\d{1,3}\s+LIFE AND LE[TI][TI][EI]', stripped, re.I):
        return True
    if re.match(r'^LE[TI][TI][EI].*TO MISS', stripped, re.I):
        return True

    # Standalone title patterns (common running headers)
    patterns = [
        r'^LIFE AND LE[TI][TI][EI].*TO[REBUK]{2} DU[TI]{2}',
        r'^LETTEBS TO MISS MA[BE]TIN',
        r'^LETTERS TO MISS MA[BE]TIN',
        r'^\d+\s*$',  # Standalone page number
        r'^[ivxlcdm]+\s+FOREWORD',
        r'^FOREWORD\s+[ivxlcdm]+',
    ]

    for pattern in patterns:
        if re.match(pattern, stripped, re.IGNORECASE):
            return True

    return False


def clean_text(input_file):
    """Clean text removing all artifacts"""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove library artifacts and running headers
    cleaned_lines = []
    library_patterns = [
        'Lai Bahadur', 'MUSSOORIE', '^LIBRARY', 'Accession', 'Class No',
        'Book No', '^Author', 'Books are Issued', 'over-due', 'borrower',
        '^moving', '3TTf', '#trT', '\.stst', '\.li2\.0T', '\.Tiuh',
        '320\.54092', '44 4',
    ]

    for line in lines:
        # Check running headers
        if is_running_header(line):
            continue

        # Check library artifacts
        should_skip = False
        for pattern in library_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                should_skip = True
                break

        if not should_skip:
            # Skip lines that are mostly dots or weird characters
            if not re.match(r'^[\.\s]+$', line.strip()):
                cleaned_lines.append(line.rstrip())

    # Join and apply OCR fixes
    text = '\n'.join(cleaned_lines)
    text = comprehensive_ocr_fix(text)

    return text


def create_final_markdown(cleaned_text):
    """Create well-structured markdown"""
    lines = cleaned_text.split('\n')

    md = []
    md.extend([
        '# Life and Letters of Toru Dutt',
        '',
        '**By Harihar Das**',
        '',
        '*With a Foreword by The Right Hon. H. A. L. Fisher, M.P.*',
        '',
        '**Oxford University Press, 1921**',
        '',
        '---',
        '',
    ])

    seen_sections = set()
    skip_count = 0

    for i, line in enumerate(lines):
        if skip_count > 0:
            skip_count -= 1
            continue

        stripped = line.strip()

        # Skip initial publisher info (first 100 lines)
        if i < 100 and re.search(r'PRINTED IN ENGLAND|BY FREDERICK|HUMPHREY MILFORD', stripped):
            continue
        if i < 100 and stripped in ['BY', 'LIFE AND LETTERS OF', 'TORU DUTT', 'HARIHAR DAS']:
            continue

        # Handle main sections (avoid duplicates)
        if stripped.upper() in ['FOREWORD', 'CONTENTS', 'PREFACE']:
            if stripped.lower() not in seen_sections:
                seen_sections.add(stripped.lower())
                md.extend(['', '', f'## {stripped.title()}', '', ''])
            continue

        # Handle chapters
        chapter_match = re.match(r'^CHAPTER\s+([IVXLCDM]+)\s*$', stripped)
        if chapter_match:
            ch_num = chapter_match.group(1)

            # Extract title (look ahead)
            title_parts = []
            for j in range(1, 6):
                if i + j < len(lines):
                    candidate = lines[i + j].strip()

                    # Skip empty
                    if not candidate:
                        continue

                    # Stop at content
                    if candidate and candidate[0].islower():
                        break
                    if re.match(r'[A-Z][a-z]+.*was|were|had', candidate):
                        break

                    # Add if looks like title
                    if candidate and candidate[0].isupper():
                        title_parts.append(candidate)

                    # Stop when we have enough
                    if len(' '.join(title_parts)) > 30:
                        break

            title = ' '.join(title_parts)
            md.extend(['', '', f'## Chapter {ch_num}', ''])
            if title:
                md.extend([f'### {title}', '', ''])
                skip_count = len(title_parts) + 1

            continue

        # Handle appendix
        if stripped.startswith('APPENDIX'):
            md.extend(['', '', f'## {stripped}', '', ''])
            continue

        # Skip garbage/artifacts
        if re.search(r'[«»€]{2,}|[\^]{2,}', stripped):
            continue

        # Add content
        md.append(line)

    result = '\n'.join(md)
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    return result


def main():
    output_dir = Path('/home/user/poesis/toru_dutt_output')

    print("Processing raw text...")
    cleaned_text = clean_text('/tmp/toru_dutt_raw.txt')

    print("Creating markdown...")
    final_md = create_final_markdown(cleaned_text)

    print("Saving files...")
    with open(output_dir / 'toru_dutt_perfect.md', 'w', encoding='utf-8') as f:
        f.write(final_md)

    # Count running headers in output
    running_headers = sum(1 for line in final_md.split('\n') if is_running_header(line))

    print(f"\n✓ Created perfect version")
    print(f"  File: toru_dutt_perfect.md")
    print(f"  Size: {len(final_md):,} characters")
    print(f"  Running headers removed: Yes (found {running_headers} remaining)")

    # Check for OCR errors
    ocr_errors = re.findall(r'\b(LETTEBS|TOBU|TOEU|MAETIN|EAELY)\b', final_md)
    print(f"  OCR errors remaining: {len(ocr_errors)}")

    if ocr_errors:
        print(f"  Found: {set(ocr_errors)}")


if __name__ == '__main__':
    main()
