#!/usr/bin/env python3
"""Inspect specific pages to find where letters actually start"""

import json

# Load the OCR text
with open('tagore_ocr_sample.json', 'r', encoding='utf-8') as f:
    ocr_text = json.load(f)

# Check specific pages
for page_num in [15, 20, 25, 28, 29]:
    page_num_str = str(page_num)
    if page_num_str in ocr_text:
        print("=" * 80)
        print(f"PAGE {page_num}")
        print("=" * 80)
        text = ocr_text[page_num_str]
        print(text[:800])
        print("\n")
