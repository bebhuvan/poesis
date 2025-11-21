#!/usr/bin/env python3
"""Inspect all EPUB items"""

import ebooklib
from ebooklib import epub
import sys

def inspect_epub_all(epub_path):
    print(f"Inspecting all items: {epub_path}\n")

    book = epub.read_epub(epub_path)

    # Get all items and group by type
    all_items = list(book.get_items())

    item_types = {}
    for item in all_items:
        item_type = item.get_type()
        if item_type not in item_types:
            item_types[item_type] = []
        item_types[item_type].append(item)

    print(f"Total items: {len(all_items)}\n")
    print("Items by type:")

    for item_type, items in sorted(item_types.items()):
        print(f"\n  Type {item_type}: {len(items)} items")

        # Show examples
        for item in items[:3]:
            print(f"    - {item.get_name()}")

    # Check if there's actual HTML content in non-DOCUMENT items
    print("\n\nChecking for HTML content in all items...")

    html_items = []
    for item in all_items:
        name = item.get_name()
        if name.endswith('.html') or name.endswith('.xhtml') or name.endswith('.htm'):
            html_items.append(item)

    print(f"\nFound {len(html_items)} items with HTML extension:")
    for item in html_items[:10]:
        print(f"  {item.get_name()} (type: {item.get_type()})")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python inspect_epub_all.py <epub_file>")
        sys.exit(1)

    inspect_epub_all(sys.argv[1])
