#!/usr/bin/env python3
"""Extract pages from PDF as high-quality images for OCR processing."""

import fitz  # PyMuPDF
from pathlib import Path
import sys

def extract_pages(pdf_path, output_dir, start_page=0, end_page=None, dpi=300):
    """Extract pages from PDF as images.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save images
        start_page: First page to extract (0-indexed)
        end_page: Last page to extract (None = all pages)
        dpi: Resolution for extraction
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    if end_page is None:
        end_page = total_pages
    
    print(f"Extracting pages {start_page}-{end_page} from {total_pages} total pages")
    
    zoom = dpi / 72  # PDF is 72 DPI by default
    mat = fitz.Matrix(zoom, zoom)
    
    for page_num in range(start_page, min(end_page, total_pages)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        
        output_file = output_dir / f"page_{page_num:04d}.png"
        pix.save(output_file)
        
        if (page_num - start_page) % 10 == 0:
            print(f"Extracted page {page_num}/{end_page}")
    
    doc.close()
    print(f"Extraction complete. Saved to {output_dir}")

if __name__ == "__main__":
    pdf_path = "../raw_scans/nehru_letters.pdf"
    
    # Extract sample pages for testing (pages 10-20, which should have actual content)
    extract_pages(pdf_path, "../raw_scans/sample_pages", start_page=10, end_page=20, dpi=300)
    
    print("\nSample extraction complete!")
