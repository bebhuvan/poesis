#!/usr/bin/env python3
"""
Rebuild letters.json from markdown files.
Use this after editing markdown files to update the website.
"""

import re
import json
from pathlib import Path
from datetime import datetime
import yaml

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)

    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except:
        # Fallback to simple parsing
        frontmatter = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip().strip('"\'')

    return frontmatter, body

def extract_footnotes(body):
    """Extract footnotes from markdown body"""
    footnotes = {}

    # Find footnotes section
    footnote_section_match = re.search(r'### Footnotes\s*\n(.*?)$', body, re.DOTALL)

    if footnote_section_match:
        footnote_text = footnote_section_match.group(1)

        # Parse individual footnotes
        # Format: **[1]** Text here...
        for match in re.finditer(r'\*\*\[(\d+)\]\*\*\s+(.+?)(?=\n\*\*\[|\n\n|$)', footnote_text, re.DOTALL):
            num = match.group(1)
            text = match.group(2).strip()
            footnotes[num] = text

    return footnotes

def parse_letter_body(body):
    """Extract clean body text (without frontmatter and footnotes)"""
    # Remove everything from ### Footnotes onward
    body = re.sub(r'---\s*\n### Footnotes.*$', '', body, flags=re.DOTALL)

    # Remove header sections (# Letter X, ## To ..., etc.)
    body = re.sub(r'^#[^\n]*\n', '', body, flags=re.MULTILINE)

    # Remove horizontal rules
    body = re.sub(r'^---+\s*$', '', body, flags=re.MULTILINE)

    # Remove bold dates
    body = re.sub(r'^\*\*[^*]+\*\*\s*$', '', body, flags=re.MULTILINE)

    # Clean up extra newlines
    body = re.sub(r'\n{3,}', '\n\n', body)

    return body.strip()

def rebuild_json(markdown_dir, output_file):
    """Rebuild JSON from markdown files"""
    markdown_path = Path(markdown_dir)

    if not markdown_path.exists():
        print(f"Error: Directory {markdown_dir} not found")
        return False

    letters = []

    # Get all markdown files
    md_files = sorted(markdown_path.glob('*.md'))

    print(f"Found {len(md_files)} markdown files")

    for md_file in md_files:
        print(f"Processing: {md_file.name}")

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter and body
            frontmatter, body = parse_frontmatter(content)

            # Extract clean body
            clean_body = parse_letter_body(body)

            # Extract footnotes
            footnotes = extract_footnotes(body)

            # Build letter object
            letter = {
                'number': frontmatter.get('letter_number', 0),
                'recipient': frontmatter.get('recipient'),
                'date': frontmatter.get('date'),
                'header_text': frontmatter.get('title', ''),
                'body': clean_body,
                'paragraphs': [p.strip() for p in clean_body.split('\n\n') if p.strip()],
                'footnotes': footnotes,
                'metadata': {
                    'author': frontmatter.get('author', 'Fyodor Dostoevsky'),
                    'translator': frontmatter.get('translator', 'Ethel Colburn Mayne'),
                    'source': frontmatter.get('source'),
                    'source_url': frontmatter.get('source_url'),
                    'public_domain': frontmatter.get('public_domain', True),
                }
            }

            letters.append(letter)

        except Exception as e:
            print(f"  Error processing {md_file.name}: {e}")

    # Sort by letter number
    letters.sort(key=lambda x: x.get('number', 0))

    # Create output JSON
    output_data = {
        'metadata': {
            'extraction_date': datetime.now().isoformat(),
            'total_letters': len(letters),
            'source': 'Letters of Fyodor Michailovitch Dostoevsky (1917)',
            'translator': 'Ethel Colburn Mayne',
            'rebuilt_from': 'markdown files'
        },
        'letters': letters
    }

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Rebuilt JSON with {len(letters)} letters")
    print(f"✓ Saved to: {output_file}")

    # Also copy to website if it exists
    website_json = Path('website/letters.json')
    if website_json.parent.exists():
        with open(website_json, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Copied to: {website_json}")

    return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Rebuild letters.json from markdown files')
    parser.add_argument('--input-dir', default='letters_markdown', help='Directory with markdown files')
    parser.add_argument('--output', default='letters_final.json', help='Output JSON file')

    args = parser.parse_args()

    rebuild_json(args.input_dir, args.output)

if __name__ == '__main__':
    main()
