#!/usr/bin/env python3
"""
Process all 90 pages of Nehru's letters using the winning OCR strategy.
"""

import fitz  # PyMuPDF
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import sys
import json
from post_process import OCRPostProcessor

def extract_and_process_page(doc, page_num, output_dir, dpi=300):
    """Extract a page and process it with Tesseract binarized."""
    # Extract page as image
    page = doc[page_num]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_path = Path(tmp.name)
    
    pix.save(temp_path)
    
    # Binarize the image
    img = Image.open(temp_path)
    img = img.convert('L')
    threshold = 128
    img = img.point(lambda p: 255 if p > threshold else 0)
    
    # Save binarized image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp2:
        binarized_path = Path(tmp2.name)
    img.save(binarized_path)
    
    # Run Tesseract
    try:
        result = subprocess.run(
            ['tesseract', str(binarized_path), 'stdout', '--psm', '6'],
            capture_output=True,
            text=True,
            timeout=60
        )
        text = result.stdout
    except Exception as e:
        text = f"Error processing page {page_num}: {e}"
    
    # Clean up temp files
    temp_path.unlink()
    binarized_path.unlink()
    
    # Post-process the text
    processor = OCRPostProcessor(aggressive=False)
    cleaned_text, report = processor.clean_text(text)
    
    # Save cleaned text
    output_file = output_dir / f"page_{page_num:04d}.txt"
    output_file.write_text(cleaned_text)
    
    return cleaned_text, report


def process_all_pages(pdf_path, output_dir, start=0, end=None):
    """Process all pages in the PDF."""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    if end is None:
        end = total_pages
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing pages {start}-{end} of {total_pages}...")
    print(f"Output directory: {output_dir}")
    
    all_text = []
    all_reports = []
    
    for page_num in range(start, min(end, total_pages)):
        print(f"Processing page {page_num+1}/{end}...", end=' ')
        
        try:
            text, report = extract_and_process_page(doc, page_num, output_dir)
            all_text.append(f"\n{'='*60}\n")
            all_text.append(f"PAGE {page_num+1}\n")
            all_text.append(f"{'='*60}\n\n")
            all_text.append(text)
            all_reports.append({
                'page': page_num,
                'lines': report.cleaned_lines,
                'artifacts': len(report.artifacts_removed),
                'hyphenations': report.hyphenations_fixed
            })
            print(f"✓ ({report.cleaned_lines} lines, {report.hyphenations_fixed} fixes)")
        except Exception as e:
            print(f"✗ Error: {e}")
            all_reports.append({
                'page': page_num,
                'error': str(e)
            })
    
    doc.close()
    
    # Save combined text
    combined_file = output_dir / "all_pages_combined.txt"
    combined_file.write_text('\n'.join(all_text))
    
    # Save processing report
    report_file = output_dir / "processing_report.json"
    report_file.write_text(json.dumps(all_reports, indent=2))
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Combined text: {combined_file}")
    print(f"Report: {report_file}")
    print(f"{'='*60}")
    
    return combined_file


if __name__ == "__main__":
    pdf_path = "../raw_scans/nehru_letters.pdf"
    output_dir = "../ocr_outputs/final_processed"
    
    # Process all pages
    process_all_pages(pdf_path, output_dir)
