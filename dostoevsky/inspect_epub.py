#!/usr/bin/env python3
"""Inspect EPUB structure"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import sys

def inspect_epub(epub_path):
    print(f"Inspecting: {epub_path}\n")

    book = epub.read_epub(epub_path)

    # Get all items
    all_items = list(book.get_items())
    print(f"Total items: {len(all_items)}\n")

    # Get document items
    doc_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    print(f"Document items: {len(doc_items)}\n")

    for idx, item in enumerate(doc_items):
        print(f"\n{'='*60}")
        print(f"Document {idx+1}: {item.get_name()}")
        print(f"ID: {item.get_id()}")
        print(f"Type: {item.get_type()}")
        print(f"{'='*60}")

        # Parse HTML
        content = item.get_content()
        soup = BeautifulSoup(content, 'html.parser')

        # Show structure
        print(f"\nHTML Structure:")
        print(f"  Headers: {len(soup.find_all(['h1', 'h2', 'h3', 'h4']))}")
        print(f"  Paragraphs: {len(soup.find_all('p'))}")
        print(f"  Divs: {len(soup.find_all('div'))}")

        # Show first few headers
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])[:5]
        if headers:
            print(f"\n  First headers:")
            for h in headers:
                print(f"    {h.name}: {h.get_text()[:80]}")

        # Show first paragraph
        first_p = soup.find('p')
        if first_p:
            print(f"\n  First paragraph:")
            print(f"    {first_p.get_text()[:200]}")

        # Show text length
        all_text = soup.get_text()
        print(f"\n  Total text length: {len(all_text)} characters")

        # Check for footnotes
        footnote_elements = soup.find_all(class_=lambda x: x and ('note' in x.lower() or 'footnote' in x.lower()))
        print(f"  Elements with footnote-related classes: {len(footnote_elements)}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python inspect_epub.py <epub_file>")
        sys.exit(1)

    inspect_epub(sys.argv[1])
