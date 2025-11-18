#!/usr/bin/env python3
"""
Regenerate the complete static site with all extracted letters.
"""

import re
import json
from pathlib import Path
from datetime import datetime
import html as html_module


def clean_text(text: str) -> str:
    """Clean text formatting."""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('  ', ' ')
    return text.strip()


def generate_letter_html(letter: dict) -> str:
    """Generate HTML for a single letter."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letter {letter['number']} - Gandhi to Sardar Patel</title>
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
        <h1 class="letter-number">Letter {html_module.escape(letter['number'])}</h1>
        <div class="location">{html_module.escape(letter.get('location', ''))}</div>
        <div class="date">{html_module.escape(letter.get('date', ''))}</div>
    </div>

    {f'<div class="salutation">{html_module.escape(letter.get("salutation", ""))}</div>' if letter.get('salutation') else ''}

    <div class="body">
        {chr(10).join(f'<p>{html_module.escape(para)}</p>' for para in letter['body'].split(chr(10)*2) if para)}
    </div>

    {f'<div class="closing">{html_module.escape(letter.get("closing", ""))}</div>' if letter.get('closing') else ''}

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
    return html


def generate_letter_markdown(letter: dict) -> str:
    """Generate Markdown for a single letter."""
    md = f"# Letter {letter['number']}\n\n"

    if letter.get('location') or letter.get('date'):
        md += f"**{letter.get('location', '')}**" if letter.get('location') else ""
        if letter.get('location') and letter.get('date'):
            md += "  \n"
        md += f"_{letter.get('date', '')}_" if letter.get('date') else ""
        md += "\n\n"

    if letter.get('salutation'):
        md += f"_{letter['salutation']}_\n\n"

    md += letter['body'] + "\n\n"

    if letter.get('closing'):
        md += f"_{letter['closing']}_\n\n"

    md += f"\n---\n_Source: Letters to Sardar Vallabhbhai Patel by M.K. Gandhi_\n"

    return md


def generate_index_html(letters: list) -> str:
    """Generate main index page."""
    # Group by year
    by_year = {}
    for letter in letters:
        year_match = re.search(r'\d{4}', letter.get('date', ''))
        year = year_match.group() if year_match else "Unknown"
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(letter)

    # Sort letters within each year
    for year in by_year:
        by_year[year].sort(key=lambda l: l['value'])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letters from Gandhi to Sardar Vallabhbhai Patel</title>
    <meta name="description" content="A collection of {len(letters)} historical letters from Mahatma Gandhi to Sardar Vallabhbhai Patel (1921-1947)">
    <style>
        :root {{
            --primary-color: #8B4513;
            --secondary-color: #D2691E;
            --text-color: #333;
            --bg-color: #FFF8F0;
            --accent-color: #F4A460;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Georgia', serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }}

        .header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 3em 2em;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 0.3em;
            font-weight: normal;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.95;
            font-style: italic;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2em;
        }}

        .intro {{
            background: white;
            padding: 2em;
            margin: 2em 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-color);
        }}

        .stats {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin: 2em 0;
            gap: 1em;
        }}

        .stat-box {{
            background: white;
            padding: 1.5em;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 200px;
        }}

        .stat-box .number {{
            font-size: 2.5em;
            color: var(--primary-color);
            font-weight: bold;
        }}

        .stat-box .label {{
            color: #666;
            margin-top: 0.5em;
        }}

        .year-section {{
            background: white;
            margin: 2em 0;
            padding: 2em;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .year-section h2 {{
            color: var(--primary-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5em;
            margin-bottom: 1em;
            font-size: 1.8em;
        }}

        .letter-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1em;
            margin-top: 1em;
        }}

        .letter-card {{
            background: #FAFAFA;
            padding: 1.2em;
            border-radius: 6px;
            border-left: 3px solid var(--accent-color);
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
            display: block;
        }}

        .letter-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-left-color: var(--primary-color);
        }}

        .letter-number {{
            font-size: 1.3em;
            color: var(--primary-color);
            font-weight: bold;
            margin-bottom: 0.5em;
        }}

        .letter-meta {{
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }}

        .footer {{
            text-align: center;
            padding: 2em;
            margin-top: 3em;
            background: white;
            border-top: 2px solid var(--accent-color);
        }}

        .footer p {{
            color: #666;
            margin: 0.5em 0;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .letter-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Letters from Gandhi to Sardar Vallabhbhai Patel</h1>
        <p>A Historical Collection (1921-1947)</p>
    </div>

    <div class="container">
        <div class="intro">
            <h2>About This Collection</h2>
            <p>
                This collection contains {len(letters)} letters written by Mahatma Gandhi (1869-1948) to
                Sardar Vallabhbhai Patel (1875-1950), one of India's foremost freedom fighters
                and the first Deputy Prime Minister of independent India.
            </p>
            <p style="margin-top: 1em;">
                These letters span from 1921 to 1947, covering critical periods in India's
                independence movement including the Non-Cooperation Movement, the Salt March,
                the Quit India Movement, and the transition to independence.
            </p>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="number">{len(letters)}</div>
                <div class="label">Letters Extracted</div>
            </div>
            <div class="stat-box">
                <div class="number">{len(by_year)}</div>
                <div class="label">Years Covered</div>
            </div>
            <div class="stat-box">
                <div class="number">{round(len(letters)/293*100, 1)}%</div>
                <div class="label">Collection Coverage</div>
            </div>
        </div>
"""

    # Add letters by year
    for year in sorted(by_year.keys(), key=lambda y: y if y != "Unknown" else "9999"):
        year_letters = by_year[year]
        html += f"""
        <div class="year-section">
            <h2>{year} ({len(year_letters)} letters)</h2>
            <div class="letter-grid">
"""
        for letter in year_letters:
            location = letter.get('location', 'Unknown location')
            date = letter.get('date', year)

            html += f"""
                <a href="letter-{letter['value']:03d}.html" class="letter-card">
                    <div class="letter-number">Letter {letter['number']}</div>
                    <div class="letter-meta">
                        {html_module.escape(location)}<br>
                        {html_module.escape(date)}
                    </div>
                </a>
"""
        html += """
            </div>
        </div>
"""

    html += f"""
    </div>

    <div class="footer">
        <p><strong>Source:</strong> <em>Letters to Sardar Vallabhbhai Patel</em> by M.K. Gandhi</p>
        <p>Translated from Gujarati by Valji Govindji Desai and Sudarshan V. Desai</p>
        <p>Published by Navajivan Publishing House, Ahmedabad (1957)</p>
        <p style="margin-top: 1.5em; font-size: 0.9em;">
            Extracted from <a href="https://archive.org/details/letterstosardarv00gand" target="_blank">Archive.org</a><br>
            Part of the PaperLanterns.ink collection
        </p>
        <p style="margin-top: 1em; font-size: 0.85em; color: #999;">
            {len(letters)} of 293 letters ({round(len(letters)/293*100, 1)}% coverage) | Generated on {datetime.now().strftime('%B %d, %Y')}
        </p>
    </div>
</body>
</html>
"""

    return html


def main():
    """Regenerate the complete site."""
    print("="*80)
    print("Regenerating Complete Static Site")
    print("="*80)

    # Load complete letter collection
    with open("letters_complete.json") as f:
        letters = json.load(f)

    print(f"\nLoaded {len(letters)} letters")

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Generate individual letter pages
    print("\nGenerating individual letter pages...")
    for letter in letters:
        # HTML
        html = generate_letter_html(letter)
        html_file = output_dir / f"letter-{letter['value']:03d}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)

        # Markdown
        md = generate_letter_markdown(letter)
        md_file = output_dir / f"letter-{letter['value']:03d}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md)

    print(f"Generated {len(letters)} letter pages (HTML + Markdown)")

    # Generate index
    print("\nGenerating index page...")
    index_html = generate_index_html(letters)
    with open(output_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)

    # Generate README
    print("Generating README...")

    missing_count = 293 - len(letters)
    coverage = round(len(letters)/293*100, 1)

    readme = f"""# Gandhi-Patel Letters Collection

A digital collection of {len(letters)} letters written by Mahatma Gandhi to Sardar Vallabhbhai Patel (1921-1947).

## Statistics

- **Letters Extracted:** {len(letters)} out of 293 total
- **Coverage:** {coverage}%
- **Years Covered:** 1921-1947
- **Source:** [Archive.org](https://archive.org/details/letterstosardarv00gand)

## Collection Overview

This collection contains historically significant correspondence between two of India's most important independence leaders:

- **M.K. Gandhi** (1869-1948): Leader of the Indian independence movement
- **Sardar Vallabhbhai Patel** (1875-1950): India's first Deputy Prime Minister and Home Minister, known as the "Iron Man of India"

The letters cover:
- The Non-Cooperation Movement (1921)
- The Bardoli Satyagraha (1928)
- The Salt March and Civil Disobedience (1930-31)
- The Quit India Movement (1942)
- Independence and Partition (1947)

## File Structure

```
output/
├── index.html              # Main index page
├── letter-001.html         # Letter 1 (HTML)
├── letter-001.md           # Letter 1 (Markdown)
├── letter-002.html         # Letter 2 (HTML)
├── letter-002.md           # Letter 2 (Markdown)
...
└── README.md               # This file
```

## Viewing the Collection

1. Open `output/index.html` in a web browser to browse all letters
2. Individual letters can be viewed in HTML or Markdown format
3. Deploy the `output/` directory to any static hosting service

## Missing Letters

Approximately {missing_count} letters ({100-coverage:.1f}%) remain to be extracted due to OCR errors and formatting complexities in the source material.

## Technical Details

- **Original Source:** "Letters to Sardar Vallabhbhai Patel" by M.K. Gandhi
- **Publisher:** Navajivan Publishing House, Ahmedabad (1957)
- **Translators:** Valji Govindji Desai and Sudarshan V. Desai
- **Original Language:** Gujarati
- **Extraction Method:** OCR text from Archive.org with automated parsing and cleanup
- **Format:** Static HTML/Markdown pages

## License

The original letters are in the public domain. This digital collection is provided for educational and historical purposes.

## Acknowledgments

- Navajivan Trust for preserving and publishing Gandhi's writings
- Archive.org for digitizing and providing open access
- The translators for their work in making these letters accessible in English

---

*Part of the PaperLanterns.ink project - preserving important historical correspondence*

Generated on {datetime.now().strftime('%B %d, %Y')}
"""

    with open(output_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme)

    # Generate extraction report
    extracted_values = sorted([l['value'] for l in letters])
    still_missing = sorted(set(range(1, 294)) - set(extracted_values))

    def int_to_roman(num):
        vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        result = ''
        for i, v in enumerate(vals):
            count, num = divmod(num, v)
            result += syms[i] * count
        return result

    report = {
        'total_extracted': len(letters),
        'expected_total': 293,
        'missing_letters': [int_to_roman(n) if n > 1 else '1' for n in still_missing],
        'coverage_percent': coverage,
        'generated_date': datetime.now().isoformat()
    }

    with open(output_dir / "extraction_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*80)
    print("SITE GENERATION COMPLETE!")
    print("="*80)
    print(f"\nTotal Letters: {len(letters)} of 293 ({coverage}% coverage)")
    print(f"Missing: {missing_count} letters")
    print(f"\nOutput directory: output/")
    print(f"  - index.html: Main index page")
    print(f"  - {len(letters)} letter pages (HTML + Markdown)")
    print(f"  - README.md: Documentation")
    print(f"  - extraction_report.json: Technical report")
    print("\nTo view locally:")
    print("  cd output && python3 -m http.server 8000")
    print("\nReady to deploy to PaperLanterns.ink!")


if __name__ == "__main__":
    main()
