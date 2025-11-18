#!/usr/bin/env python3
"""
PDF Text Extractor for Historical Letters
Extracts text from PDF using multiple methods for comparison
"""

import sys
from pathlib import Path
from typing import List, Dict
import subprocess


class PDFExtractor:
    """Extract text from PDF using multiple tools"""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.text = ""

    def extract_with_pdftotext(self) -> str:
        """Extract using pdftotext (poppler-utils)"""
        print("Extracting with pdftotext...")
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', str(self.pdf_path), '-'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"pdftotext failed: {e}")
            return ""
        except FileNotFoundError:
            print("pdftotext not found. Installing poppler-utils...")
            try:
                subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
                subprocess.run(['apt-get', 'install', '-y', 'poppler-utils'], check=True, capture_output=True)
                # Retry
                result = subprocess.run(
                    ['pdftotext', '-layout', str(self.pdf_path), '-'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout
            except Exception as e2:
                print(f"Failed to install/use pdftotext: {e2}")
                return ""

    def extract_with_pdfplumber(self) -> str:
        """Extract using pdfplumber library"""
        try:
            import pdfplumber
            print("Extracting with pdfplumber...")

            pages_text = []
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        pages_text.append(f"\n{'='*80}\n")
                        pages_text.append(f"PAGE {i}\n")
                        pages_text.append(f"{'='*80}\n\n")
                        pages_text.append(text)
                        pages_text.append('\n')

                    if i % 50 == 0:
                        print(f"Processed {i}/{len(pdf.pages)} pages...")

            return ''.join(pages_text)

        except ImportError:
            print("pdfplumber not available. Installing...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'pdfplumber'], check=True)
                import pdfplumber
                # Retry extraction
                pages_text = []
                with pdfplumber.open(self.pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if text:
                            pages_text.append(f"\n{'='*80}\n")
                            pages_text.append(f"PAGE {i}\n")
                            pages_text.append(f"{'='*80}\n\n")
                            pages_text.append(text)
                            pages_text.append('\n')
                return ''.join(pages_text)
            except Exception as e:
                print(f"Failed to install/use pdfplumber: {e}")
                return ""
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            return ""

    def extract(self) -> str:
        """Extract text using best available method"""
        # Try pdftotext first (usually better for scanned documents)
        text = self.extract_with_pdftotext()

        if not text or len(text.strip()) < 1000:
            # Fallback to pdfplumber
            text = self.extract_with_pdfplumber()

        self.text = text
        return text

    def save(self, output_path: str):
        """Save extracted text"""
        Path(output_path).write_text(self.text, encoding='utf-8')
        print(f"Saved PDF text to: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    extractor = PDFExtractor(pdf_file)
    text = extractor.extract()

    output_file = Path(pdf_file).parent / 'pdf_extracted.txt'
    extractor.save(output_file)

    print(f"\nExtracted {len(text)} characters from PDF")
