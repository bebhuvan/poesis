#!/usr/bin/env python3
"""
Combine all extracted pages into a single book file
"""

import json
from pathlib import Path
from datetime import datetime

def combine_pages(output_dir="output", format="txt"):
    """Combine all pages into a single file"""
    output_dir = Path(output_dir)

    # Find all page directories
    page_dirs = sorted(output_dir.glob("page_*"))

    if not page_dirs:
        print("No pages found to combine!")
        return None

    print(f"Found {len(page_dirs)} pages")

    # Collect all pages
    pages = []

    for page_dir in page_dirs:
        text_file = page_dir / "text.txt"
        metadata_file = page_dir / "metadata.json"

        if text_file.exists() and metadata_file.exists():
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            pages.append({
                'page_number': metadata['page_number'],
                'text': text,
                'word_count': metadata['word_count'],
                'corrections': len(metadata['corrections'])
            })

    pages = sorted(pages, key=lambda p: p['page_number'])

    print(f"Successfully loaded {len(pages)} pages")

    # Generate combined output
    if format == "txt":
        output = _generate_txt(pages)
        output_file = output_dir / "tagore_letters_complete.txt"
    elif format == "md":
        output = _generate_markdown(pages)
        output_file = output_dir / "tagore_letters_complete.md"
    else:
        print(f"Unknown format: {format}")
        return None

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\n✓ Combined book saved to: {output_file}")
    print(f"  Total pages: {len(pages)}")
    print(f"  Total words: {sum(p['word_count'] for p in pages):,}")
    print(f"  Total corrections: {sum(p['corrections'] for p in pages)}")

    return output_file

def _generate_txt(pages):
    """Generate plain text version"""
    output = []

    output.append("LETTERS TO A FRIEND")
    output.append("BY RABINDRANATH TAGORE")
    output.append("=" * 60)
    output.append(f"Digitally Preserved Edition - {datetime.now().year}")
    output.append(f"Extracted: {datetime.now().strftime('%Y-%m-%d')}")
    output.append("=" * 60)
    output.append("\n\n")

    for page in pages:
        output.append(f"\n{'='*60}\n")
        output.append(f"PAGE {page['page_number']}\n")
        output.append(f"{'='*60}\n\n")
        output.append(page['text'])
        output.append("\n\n")

    return ''.join(output)

def _generate_markdown(pages):
    """Generate Markdown version with metadata"""
    output = []

    output.append("# Letters to a Friend\n")
    output.append("## By Rabindranath Tagore\n\n")
    output.append("---\n\n")
    output.append("**Digitally Preserved Edition**\n\n")
    output.append(f"- Original Publication: 1926 (George Allen & Unwin Ltd)\n")
    output.append(f"- Digital Extraction: {datetime.now().strftime('%Y-%m-%d')}\n")
    output.append(f"- Source: [Internet Archive](https://archive.org/details/in.ernet.dli.2015.52214)\n")
    output.append(f"- Total Pages: {len(pages)}\n")
    output.append(f"- Total Words: {sum(p['word_count'] for p in pages):,}\n")
    output.append(f"- Extraction Method: Multi-strategy OCR with verification\n")
    output.append("\n---\n\n")

    for page in pages:
        output.append(f"\n\n## Page {page['page_number']}\n\n")
        output.append(page['text'])
        output.append("\n")

    output.append("\n\n---\n\n")
    output.append("*End of Book*\n")

    return ''.join(output)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Combine extracted pages into complete book')
    parser.add_argument('--output-dir', type=Path, default=Path('output'),
                       help='Output directory with extracted pages')
    parser.add_argument('--format', choices=['txt', 'md', 'both'], default='both',
                       help='Output format')

    args = parser.parse_args()

    if args.format in ['txt', 'both']:
        combine_pages(args.output_dir, 'txt')

    if args.format in ['md', 'both']:
        combine_pages(args.output_dir, 'md')
