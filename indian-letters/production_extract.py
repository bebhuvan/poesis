#!/usr/bin/env python3
"""
Production letter extraction - generates clean, publishable output.
Focuses on quality over quantity with clear gap documentation.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import html


@dataclass
class Letter:
    number: str
    value: int
    location: str
    date: str
    salutation: str
    body: str
    closing: str
    source_lines: tuple  # (start, end)


# Known OCR corrections
ROMAN_FIXES = {
    'Ill': 'III', 'lll': 'III', 'll': 'II', 'lI': 'II', 'Il': 'II',
    'Cl': 'CI', 'XLVIXX': 'XLVIII', 'CXXVIXI': 'CXXVIII',
    'CXXXVIX': 'CXXXVII', 'CCLVXI': 'CCLVII', 'CCLXXXVXI': 'CCLXXXVII',
}


def fix_roman(text: str) -> str:
    """Fix OCR errors in Roman numerals."""
    text = text.strip()
    if text in ROMAN_FIXES:
        return ROMAN_FIXES[text]
    # Auto-fix 'l' to 'I'
    if re.match(r'^[IVXLCDMl]+$', text):
        return text.replace('l', 'I')
    return text


def roman_to_int(roman: str) -> int:
    """Convert Roman to integer."""
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    roman = fix_roman(roman.upper())
    total = prev = 0
    for char in reversed(roman):
        if char not in vals:
            return -1
        val = vals[char]
        total += val if val >= prev else -val
        prev = val
    return total


def int_to_roman(num: int) -> str:
    """Convert integer to Roman."""
    vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    result = ''
    for i, v in enumerate(vals):
        count, num = divmod(num, v)
        result += syms[i] * count
    return result


def clean_text(text: str) -> str:
    """Clean OCR artifacts from text."""
    # Fix common OCR issues
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to one
    text = text.replace('  ', ' ')
    # Fix common punctuation issues
    text = text.replace(' ,', ',')
    text = text.replace(' .', '.')
    text = text.replace('( ', '(')
    text = text.replace(' )', ')')
    return text.strip()


def extract_letters_strict(content: str) -> List[Letter]:
    """Extract letters with strict validation."""
    lines = content.splitlines()

    # Strict boundaries
    START_LINE = 280  # After title page "LETTERS TO / SARDAR VALLABHBHAI PATEL"
    END_LINE = 10635  # Before "APPENDIX"

    print(f"Scanning lines {START_LINE} to {END_LINE}")

    # Find all valid letter markers
    markers = []
    for i in range(START_LINE, min(END_LINE, len(lines))):
        line = lines[i].strip()

        # Clean Roman numeral pattern
        if re.match(r'^[IVXLCDMl]{1,8}$', line):
            fixed = fix_roman(line)
            val = roman_to_int(fixed)
            if 2 <= val <= 293:  # Valid letter range (letter 1 uses "1" not "I")
                markers.append({'line': i, 'num': fixed, 'val': val})

        # Special case: Letter 1
        elif line == "1" and i == 284:
            markers.append({'line': i, 'num': '1', 'val': 1})

    print(f"Found {len(markers)} potential markers")

    # Remove duplicates, keeping first occurrence
    seen = {}
    unique_markers = []
    for m in markers:
        if m['val'] not in seen:
            seen[m['val']] = m
            unique_markers.append(m)
        else:
            print(f"  Skipping duplicate {m['num']} at line {m['line']}")

    markers = sorted(unique_markers, key=lambda x: x['line'])
    print(f"After deduplication: {len(markers)} markers")

    # Extract letter content
    letters = []
    for i, marker in enumerate(markers):
        start_line = marker['line']
        end_line = markers[i+1]['line'] if i+1 < len(markers) else END_LINE

        # Parse letter
        letter = parse_letter(lines, marker, start_line, end_line)
        if letter:
            letters.append(letter)

    return letters


def parse_letter(lines: List[str], marker: Dict, start: int, end: int) -> Optional[Letter]:
    """Parse a single letter."""
    i = start + 1  # Skip marker line

    # Skip empty lines
    while i < end and not lines[i].strip():
        i += 1

    # Extract location
    location = ""
    if i < end:
        loc = lines[i].strip()
        if loc and not re.match(r'^\[?\d{4}\]?$', loc):
            location = clean_text(loc)
            i += 1

    # Skip empty lines
    while i < end and not lines[i].strip():
        i += 1

    # Extract date
    date = ""
    if i < end:
        date_text = lines[i].strip()
        if date_text:
            date = clean_text(date_text)
            i += 1

    # Skip empty lines
    while i < end and not lines[i].strip():
        i += 1

    # Extract salutation
    salutation = ""
    if i < end:
        sal = lines[i].strip()
        if sal and any(x in sal for x in ['Bhai', 'Chi.', ',Bhai', 'Mani,']):
            salutation = clean_text(sal)
            i += 1

    # Extract body
    body_lines = []
    while i < end:
        line = lines[i].strip()

        # Skip page numbers, headers, footnotes
        if (re.match(r'^\d+$', line) or
            'LETTERS  TO  SARDAR' in line or
            re.match(r'^[\*†‡§%]\s+', line)):
            i += 1
            continue

        if line:
            body_lines.append(line)

        i += 1

    # Find closing
    closing = ""
    if body_lines:
        last = body_lines[-1]
        if any(x in last.lower() for x in ['bapu', 'mohandas', 'vande mataram', 'blessings']):
            closing = body_lines.pop()

        # Remove trailing empty lines
        while body_lines and not body_lines[-1]:
            body_lines.pop()

    # Clean body
    body = '\n\n'.join([clean_text(line) for line in body_lines if line])

    return Letter(
        number=marker['num'],
        value=marker['val'],
        location=location,
        date=date,
        salutation=salutation,
        body=body,
        closing=closing,
        source_lines=(start, end)
    )


def generate_markdown(letter: Letter) -> str:
    """Generate Markdown for a letter."""
    md = f"# Letter {letter.number}\n\n"

    if letter.location or letter.date:
        md += f"**{letter.location}**" if letter.location else ""
        if letter.location and letter.date:
            md += "  \n"
        md += f"_{letter.date}_" if letter.date else ""
        md += "\n\n"

    if letter.salutation:
        md += f"_{letter.salutation}_\n\n"

    md += letter.body + "\n\n"

    if letter.closing:
        md += f"_{letter.closing}_\n\n"

    md += f"\n---\n_Source: Letters to Sardar Vallabhbhai Patel by M.K. Gandhi_\n"

    return md


def generate_html(letter: Letter) -> str:
    """Generate HTML for a letter."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letter {letter.number} - Gandhi to Sardar Patel</title>
    <style>
        body {{
            font-family: Georgia, serif;
            max-width: 700px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.8;
            color: #333;
        }}
        .letter-header {{
            text-align: center;
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 1px solid #ddd;
        }}
        .letter-number {{
            font-size: 2em;
            font-weight: normal;
            margin: 0;
        }}
        .location, .date {{
            font-style: italic;
            color: #666;
        }}
        .salutation {{
            font-style: italic;
            margin: 2em 0 1em 0;
        }}
        .body {{
            text-align: justify;
        }}
        .body p {{
            margin: 1em 0;
        }}
        .closing {{
            font-style: italic;
            text-align: right;
            margin: 2em 0;
        }}
        .footer {{
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
            text-align: center;
        }}
        .nav {{
            text-align: center;
            margin: 2em 0;
        }}
        .nav a {{
            margin: 0 1em;
            text-decoration: none;
            color: #0066cc;
        }}
    </style>
</head>
<body>
    <div class="letter-header">
        <h1 class="letter-number">Letter {html.escape(letter.number)}</h1>
        <div class="location">{html.escape(letter.location)}</div>
        <div class="date">{html.escape(letter.date)}</div>
    </div>

    {f'<div class="salutation">{html.escape(letter.salutation)}</div>' if letter.salutation else ''}

    <div class="body">
        {chr(10).join(f'<p>{html.escape(para)}</p>' for para in letter.body.split(chr(10)*2) if para)}
    </div>

    {f'<div class="closing">{html.escape(letter.closing)}</div>' if letter.closing else ''}

    <div class="footer">
        <p>From <em>Letters to Sardar Vallabhbhai Patel</em> by M.K. Gandhi</p>
        <p>Published by Navajivan Publishing House, Ahmedabad (1957)</p>
    </div>

    <div class="nav">
        <a href="index.html">← Back to Index</a>
    </div>
</body>
</html>
"""
    return html_content


def main():
    """Main extraction and generation."""
    print("="*80)
    print("Production Letter Extraction")
    print("="*80)

    # Read source
    with open("gandhi-patel-letters.txt", 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract
    letters = extract_letters_strict(content)

    print(f"\nExtracted {len(letters)} letters")

    # Analyze gaps
    values = sorted([l.value for l in letters])
    expected = set(range(1, max(values) + 1))
    found = set(values)
    missing = sorted(expected - found)

    print(f"Expected: {max(values)} letters")
    print(f"Found: {len(found)} letters")
    print(f"Missing: {len(missing)} letters")

    if missing:
        print(f"\nMissing letters: {', '.join(int_to_roman(n) if n > 1 else '1' for n in missing[:30])}...")

    # Save JSON
    letters_data = [{
        'number': l.number,
        'value': l.value,
        'location': l.location,
        'date': l.date,
        'salutation': l.salutation,
        'body': l.body,
        'closing': l.closing,
    } for l in letters]

    with open("letters_production.json", 'w', encoding='utf-8') as f:
        json.dump(letters_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to letters_production.json")

    # Generate output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Generate individual letter files
    for letter in letters:
        # Markdown
        md_file = output_dir / f"letter-{letter.value:03d}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(generate_markdown(letter))

        # HTML
        html_file = output_dir / f"letter-{letter.value:03d}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(generate_html(letter))

    print(f"Generated {len(letters)} letter pages in output/")

    # Generate index
    index_md = "# Letters from Gandhi to Sardar Vallabhbhai Patel\n\n"
    index_md += f"## Collection of {len(letters)} letters\n\n"

    # Group by year
    by_year = {}
    for letter in letters:
        year_match = re.search(r'\d{4}', letter.date)
        year = year_match.group() if year_match else "Unknown"
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(letter)

    for year in sorted(by_year.keys()):
        index_md += f"\n### {year}\n\n"
        for letter in sorted(by_year[year], key=lambda l: l.value):
            index_md += f"- [Letter {letter.number}](letter-{letter.value:03d}.html) - {letter.location} - {letter.date}\n"

    with open(output_dir / "index.md", 'w', encoding='utf-8') as f:
        f.write(index_md)

    print("Generated index.md")

    # Summary report
    report = {
        'total_extracted': len(letters),
        'expected_total': max(values),
        'missing_letters': [int_to_roman(n) if n > 1 else '1' for n in missing],
        'coverage_percent': round(len(found) / max(values) * 100, 1),
    }

    with open(output_dir / "extraction_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nCoverage: {report['coverage_percent']}%")
    print(f"\nAll output saved to output/")


if __name__ == "__main__":
    main()
