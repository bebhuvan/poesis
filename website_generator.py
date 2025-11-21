#!/usr/bin/env python3
"""
Static Website Generator for Tagore Letters
Creates a beautiful, minimal website to showcase the letters
"""

import os
import json
from pathlib import Path


class WebsiteGenerator:
    """Generate static website for Tagore letters"""

    def __init__(self, letters: List[Dict], output_dir: str = 'tagore_website'):
        self.letters = letters
        self.output_dir = output_dir

    def generate(self):
        """Generate complete website"""
        print("\n" + "=" * 80)
        print("GENERATING STATIC WEBSITE")
        print("=" * 80)

        # Create directory structure
        self.create_directories()

        # Generate pages
        self.generate_index()
        self.generate_letter_pages()
        self.generate_about_page()
        self.generate_css()

        print(f"\n✓ Website generated in: {self.output_dir}/")
        print(f"  Open {self.output_dir}/index.html in your browser")

    def create_directories(self):
        """Create website directory structure"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/letters", exist_ok=True)
        os.makedirs(f"{self.output_dir}/css", exist_ok=True)

    def generate_css(self):
        """Generate CSS stylesheet"""
        css = """
/* Tagore Letters - Elegant Typography */

:root {
    --primary-color: #2c3e50;
    --secondary-color: #8b7355;
    --text-color: #333;
    --bg-color: #faf8f5;
    --accent-color: #d4a574;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Crimson Text', 'Garamond', 'Georgia', serif;
    line-height: 1.8;
    color: var(--text-color);
    background: var(--bg-color);
    font-size: 18px;
}

header {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    color: white;
    padding: 3rem 2rem;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

header h1 {
    font-size: 2.5rem;
    font-weight: 400;
    margin-bottom: 0.5rem;
    letter-spacing: 2px;
}

header p {
    font-size: 1.1rem;
    opacity: 0.9;
    font-style: italic;
}

nav {
    background: white;
    padding: 1rem 2rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    position: sticky;
    top: 0;
    z-index: 100;
}

nav ul {
    list-style: none;
    display: flex;
    justify-content: center;
    gap: 2rem;
}

nav a {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

nav a:hover {
    color: var(--secondary-color);
}

main {
    max-width: 900px;
    margin: 2rem auto;
    padding: 0 2rem;
}

.letter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.letter-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1.5rem;
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
}

.letter-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
}

.letter-card h3 {
    color: var(--secondary-color);
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.letter-meta {
    color: #666;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.letter-preview {
    color: var(--text-color);
    font-size: 0.95rem;
    line-height: 1.6;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
}

.letter-content {
    background: white;
    padding: 3rem;
    margin-top: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}

.letter-content h1 {
    color: var(--secondary-color);
    font-size: 2rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid var(--accent-color);
    padding-bottom: 0.5rem;
}

.letter-metadata {
    background: #f5f5f5;
    padding: 1rem;
    border-left: 4px solid var(--secondary-color);
    margin-bottom: 2rem;
    font-size: 0.95rem;
}

.letter-text {
    font-size: 1.1rem;
    line-height: 1.9;
    text-align: justify;
    white-space: pre-wrap;
}

.letter-text p {
    margin-bottom: 1.5rem;
}

.letter-navigation {
    display: flex;
    justify-content: space-between;
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid #e0e0e0;
}

.nav-button {
    background: var(--secondary-color);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    text-decoration: none;
    transition: background 0.3s;
}

.nav-button:hover {
    background: var(--primary-color);
}

.about-content {
    background: white;
    padding: 3rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    line-height: 1.9;
}

.about-content h2 {
    color: var(--secondary-color);
    margin-top: 2rem;
    margin-bottom: 1rem;
}

.about-content p {
    margin-bottom: 1rem;
}

footer {
    text-align: center;
    padding: 2rem;
    margin-top: 4rem;
    background: var(--primary-color);
    color: white;
}

footer p {
    opacity: 0.9;
}

@media (max-width: 768px) {
    header h1 {
        font-size: 1.8rem;
    }

    .letter-grid {
        grid-template-columns: 1fr;
    }

    .letter-content {
        padding: 1.5rem;
    }
}
"""

        with open(f"{self.output_dir}/css/style.css", 'w', encoding='utf-8') as f:
            f.write(css)

    def generate_index(self):
        """Generate index page with letter listing"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letters of Rabindranath Tagore</title>
    <link rel="stylesheet" href="css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body>
    <header>
        <h1>LETTERS OF RABINDRANATH TAGORE</h1>
        <p>A Collection of Personal Correspondence</p>
    </header>

    <nav>
        <ul>
            <li><a href="index.html">All Letters</a></li>
            <li><a href="about.html">About This Collection</a></li>
        </ul>
    </nav>

    <main>
        <div class="letter-grid">
"""

        # Add letter cards
        for letter in self.letters:
            preview = letter.get('content', '')[:200].replace('\n', ' ').strip() + '...'

            # Extract metadata
            date = letter.get('date', 'Date unknown')
            marker = letter.get('marker', '')
            pages = f"Pages {letter.get('start_page', '?')}-{letter.get('end_page', '?')}"

            html += f"""
            <div class="letter-card" onclick="window.location='letters/letter_{letter['number']:03d}.html'">
                <h3>Letter {letter['number']}</h3>
                <div class="letter-meta">
                    <div><strong>Marker:</strong> {marker}</div>
                    <div><strong>Date:</strong> {date}</div>
                    <div>{pages} • {letter.get('word_count', 0)} words</div>
                </div>
                <div class="letter-preview">{preview}</div>
            </div>
"""

        html += """
        </div>
    </main>

    <footer>
        <p>These letters are in the public domain.</p>
        <p>Rabindranath Tagore (1861-1941) - Nobel Prize in Literature, 1913</p>
    </footer>
</body>
</html>
"""

        with open(f"{self.output_dir}/index.html", 'w', encoding='utf-8') as f:
            f.write(html)

    def generate_letter_pages(self):
        """Generate individual page for each letter"""
        for i, letter in enumerate(self.letters):
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letter {letter['number']} - Rabindranath Tagore</title>
    <link rel="stylesheet" href="../css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body>
    <header>
        <h1>LETTERS OF RABINDRANATH TAGORE</h1>
        <p>Letter {letter['number']}</p>
    </header>

    <nav>
        <ul>
            <li><a href="../index.html">All Letters</a></li>
            <li><a href="../about.html">About</a></li>
        </ul>
    </nav>

    <main>
        <div class="letter-content">
            <h1>Letter {letter['number']}</h1>

            <div class="letter-metadata">
                <p><strong>Marker:</strong> {letter.get('marker', 'Unknown')}</p>
                <p><strong>Date:</strong> {letter.get('date', 'Date unknown')}</p>
                <p><strong>Pages:</strong> {letter.get('start_page', '?')}-{letter.get('end_page', '?')}</p>
                <p><strong>Word Count:</strong> {letter.get('word_count', 0)}</p>
            </div>

            <div class="letter-text">
{letter.get('content', '').strip()}
            </div>

            <div class="letter-navigation">
"""

            # Previous/Next navigation
            if i > 0:
                html += f'                <a href="letter_{self.letters[i-1]["number"]:03d}.html" class="nav-button">← Previous Letter</a>\n'
            else:
                html += '                <span></span>\n'

            if i < len(self.letters) - 1:
                html += f'                <a href="letter_{self.letters[i+1]["number"]:03d}.html" class="nav-button">Next Letter →</a>\n'
            else:
                html += '                <span></span>\n'

            html += """
            </div>
        </div>
    </main>

    <footer>
        <p>These letters are in the public domain.</p>
    </footer>
</body>
</html>
"""

            with open(f"{self.output_dir}/letters/letter_{letter['number']:03d}.html", 'w', encoding='utf-8') as f:
                f.write(html)

    def generate_about_page(self):
        """Generate about page"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About - Rabindranath Tagore Letters</title>
    <link rel="stylesheet" href="css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body>
    <header>
        <h1>LETTERS OF RABINDRANATH TAGORE</h1>
        <p>About This Collection</p>
    </header>

    <nav>
        <ul>
            <li><a href="index.html">All Letters</a></li>
            <li><a href="about.html">About This Collection</a></li>
        </ul>
    </nav>

    <main>
        <div class="about-content">
            <h2>About Rabindranath Tagore</h2>
            <p>
                Rabindranath Tagore (1861-1941) was a Bengali polymath who worked as a poet, writer,
                playwright, composer, philosopher, social reformer and painter. He reshaped Bengali
                literature and music as well as Indian art with Contextual Modernism in the late
                19th and early 20th centuries.
            </p>
            <p>
                Tagore became the first non-European to receive the Nobel Prize in Literature in 1913.
                His poetry was viewed as spiritual and mercurial, and his words continue to inspire
                readers around the world.
            </p>

            <h2>About These Letters</h2>
            <p>
                This collection contains personal correspondence from Rabindranath Tagore, offering
                intimate glimpses into his thoughts, philosophy, and daily life. These letters reveal
                the personal side of one of the 20th century's most influential literary figures.
            </p>
            <p>
                The letters were originally compiled and published as "Rabindra Nath Tagore: Letters
                To A Friend" edited by C. F. Andrews in 1926, and published by George Allen & Unwin Ltd.
            </p>

            <h2>Public Domain</h2>
            <p>
                These letters are in the public domain. Rabindranath Tagore passed away in 1941,
                and these works are now freely available for all to read, study, and share.
            </p>

            <h2>Source</h2>
            <p>
                The text was extracted from a digitized version available at the Internet Archive
                (Digital Library of India project). The extraction used OCR technology and multiple
                verification methodologies to ensure accuracy.
            </p>

            <h2>Acknowledgments</h2>
            <p>
                This website was created to preserve and share these beautiful letters with the world.
                We believe that Tagore's words should be freely accessible to anyone who wishes to
                read them.
            </p>
        </div>
    </main>

    <footer>
        <p>These letters are in the public domain.</p>
        <p>Rabindranath Tagore (1861-1941) - Nobel Prize in Literature, 1913</p>
    </footer>
</body>
</html>
"""

        with open(f"{self.output_dir}/about.html", 'w', encoding='utf-8') as f:
            f.write(html)


def main():
    import sys

    # Load letters from strategy comparison
    strategy_file = 'strategy_comparison.json'
    if not os.path.exists(strategy_file):
        print(f"⚠ {strategy_file} not found. Run multi-strategy extraction first.")
        return

    print("📂 Loading extracted letters...")
    with open(strategy_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Use first strategy's letters
        letters = data['strategies'][0]['letters']

    print(f"✓ Loaded {len(letters)} letters")

    # Generate website
    generator = WebsiteGenerator(letters)
    generator.generate()


if __name__ == '__main__':
    from typing import Dict, List
    main()
