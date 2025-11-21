#!/usr/bin/env python3
"""Inspect actual text extracted from PDF to understand formatting"""

import PyPDF2

def inspect_pdf():
    with open('tagore_letters.pdf', 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)

        print(f"Total pages: {total_pages}\n")

        # Sample pages to inspect
        sample_pages = [0, 1, 2, 10, 20, 50, 100]

        for page_num in sample_pages:
            if page_num >= total_pages:
                continue

            print("=" * 80)
            print(f"PAGE {page_num}")
            print("=" * 80)

            page = reader.pages[page_num]
            text = page.extract_text()

            print(f"Character count: {len(text)}")
            print(f"Line count: {len(text.split(chr(10)))}")
            print("\nFirst 500 characters:")
            print("-" * 80)
            print(repr(text[:500]))
            print("-" * 80)
            print("\nActual display:")
            print("-" * 80)
            print(text[:800])
            print("-" * 80)
            print()

if __name__ == '__main__':
    inspect_pdf()
