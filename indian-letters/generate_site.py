#!/usr/bin/env python3
"""
Generate a complete, beautiful static site for the Gandhi-Patel letters.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def generate_index_html(letters):
    """Generate main index page."""
    # Group letters by year
    by_year = {}
    for letter in letters:
        year_match = re.search(r'\d{4}', letter['date'])
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
    <meta name="description" content="A collection of historical letters from Mahatma Gandhi to Sardar Vallabhbhai Patel (1921-1947)">
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
                This collection contains letters written by Mahatma Gandhi (1869-1948) to
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
                <div class="number">{min(l['value'] for l in letters)}-{max(l['value'] for l in letters)}</div>
                <div class="label">Letter Range</div>
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
            location = letter['location'] if letter['location'] else "Unknown location"
            date = letter['date'] if letter['date'] else year

            html += f"""
                <a href="letter-{letter['value']:03d}.html" class="letter-card">
                    <div class="letter-number">Letter {letter['number']}</div>
                    <div class="letter-meta">
                        {location}<br>
                        {date}
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
            Generated on {datetime.now().strftime('%B %d, %Y')}
        </p>
    </div>
</body>
</html>
"""

    return html


def main():
    """Generate the complete site."""
    print("Generating complete static site...")

    # Load letters
    with open("letters_production.json") as f:
        letters = json.load(f)

    print(f"Loaded {len(letters)} letters")

    # Generate index
    index_html = generate_index_html(letters)

    with open("output/index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)

    print("Generated index.html")

    # Copy letter HTML files (already generated by production_extract.py)
    print(f"\nStatic site ready in output/")
    print(f"  - index.html: Main index page")
    print(f"  - letter-*.html: {len(letters)} individual letter pages")
    print(f"  - letter-*.md: {len(letters)} Markdown versions")

    # Create README
    readme = f"""# Gandhi-Patel Letters Collection

A digital collection of letters written by Mahatma Gandhi to Sardar Vallabhbhai Patel (1921-1947).

## Statistics

- **Letters Extracted:** {len(letters)} out of 293 total
- **Coverage:** {len(letters)/293*100:.1f}%
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
└── extraction_report.json  # Technical extraction report
```

## Viewing the Collection

1. Open `output/index.html` in a web browser to browse all letters
2. Individual letters can be viewed in HTML or Markdown format
3. Deploy the `output/` directory to any static hosting service

## Missing Letters

Approximately 120 letters (41%) still need to be extracted due to OCR errors and formatting complexities in the source material. These can be added manually by:

1. Locating the letter in the source text (`gandhi-patel-letters.txt`)
2. Creating a new letter file following the existing format
3. Adding it to the index

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

## Contributing

To add missing letters or improve the collection:

1. Find the letter in the source material
2. Extract and format it consistently with existing letters
3. Add it to the collection
4. Update the index

---

*Part of the PaperLanterns.ink project - preserving important historical correspondence*
"""

    with open("output/README.md", 'w') as f:
        f.write(readme)

    print("\nGenerated README.md")

    print("\n" + "="*80)
    print("SITE GENERATION COMPLETE!")
    print("="*80)
    print(f"\nYour static site is ready in: output/")
    print(f"\nTo view locally:")
    print(f"  cd output && python3 -m http.server 8000")
    print(f"\nThen open: http://localhost:8000")
    print("\nTo deploy: Upload the entire output/ directory to your web host")


if __name__ == "__main__":
    main()
