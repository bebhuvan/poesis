#!/usr/bin/env python3
"""
Multi-Strategy Archive.org Letter Extractor
Extracts historical letters from Archive.org using multiple OCR methods for verification
"""

import requests
import os
import hashlib
import json
from datetime import datetime
from pathlib import Path
import time
import re
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArchiveOrgExtractor:
    """Extract text from Archive.org items using multiple strategies"""

    def __init__(self, identifier: str, output_dir: str = "letters"):
        self.identifier = identifier
        self.output_dir = Path(output_dir)
        self.base_url = f"https://archive.org/download/{identifier}"
        self.metadata_url = f"https://archive.org/metadata/{identifier}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Historical Letters Preservation Project)'
        })

    def get_metadata(self) -> Dict:
        """Fetch metadata about the Archive.org item"""
        logger.info(f"Fetching metadata for {self.identifier}")
        response = self.session.get(self.metadata_url, timeout=30)
        response.raise_for_status()
        return response.json()

    def download_file(self, filename: str, save_path: Path) -> bool:
        """Download a file from Archive.org"""
        url = f"{self.base_url}/{filename}"
        logger.info(f"Downloading {filename} from {url}")

        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded {filename} ({save_path.stat().st_size} bytes)")
            return True
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return False

    def extract_text_from_txt(self, txt_file: Path) -> Optional[str]:
        """Extract text from plain text file (Method 1)"""
        logger.info(f"Extracting text from TXT file: {txt_file}")
        try:
            with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to extract from TXT: {e}")
            return None

    def extract_text_from_pdf(self, pdf_file: Path) -> Optional[str]:
        """Extract text from PDF file (Method 2)"""
        logger.info(f"Extracting text from PDF file: {pdf_file}")
        try:
            import PyPDF2
            text = []
            with open(pdf_file, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                logger.info(f"PDF has {len(pdf_reader.pages)} pages")
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text.append(f"\n--- Page {page_num} ---\n{page_text}")
            return '\n'.join(text)
        except ImportError:
            logger.warning("PyPDF2 not installed, skipping PDF extraction")
            return None
        except Exception as e:
            logger.error(f"Failed to extract from PDF: {e}")
            return None

    def extract_text_from_djvu(self, djvu_file: Path) -> Optional[str]:
        """Extract text from DJVU file (Method 3)"""
        logger.info(f"Extracting text from DJVU file: {djvu_file}")
        try:
            # Use djvutxt command if available
            import subprocess
            result = subprocess.run(
                ['djvutxt', str(djvu_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"djvutxt failed: {result.stderr}")
                return None
        except FileNotFoundError:
            logger.warning("djvutxt not installed, skipping DJVU extraction")
            return None
        except Exception as e:
            logger.error(f"Failed to extract from DJVU: {e}")
            return None

    def calculate_hash(self, text: str) -> str:
        """Calculate SHA-256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def compare_extractions(self, extractions: Dict[str, str]) -> Dict:
        """Compare different extraction methods for verification"""
        logger.info("Comparing extraction methods...")

        results = {
            'methods': {},
            'agreement': None,
            'recommended': None
        }

        for method, text in extractions.items():
            if text:
                results['methods'][method] = {
                    'length': len(text),
                    'hash': self.calculate_hash(text),
                    'lines': len(text.split('\n')),
                    'words': len(text.split())
                }

        # Check if different methods produce similar results
        hashes = [info['hash'] for info in results['methods'].values()]
        if len(set(hashes)) == 1:
            results['agreement'] = 'perfect'
            results['recommended'] = list(extractions.keys())[0]
        else:
            # Recommend the method with most content
            recommended = max(
                results['methods'].items(),
                key=lambda x: x[1]['words']
            )
            results['recommended'] = recommended[0]
            results['agreement'] = 'divergent'
            logger.warning(f"Different methods produced different results. Recommended: {recommended[0]}")

        return results

    def extract_all_methods(self) -> Tuple[Dict[str, str], Dict]:
        """Extract text using all available methods"""
        metadata = self.get_metadata()

        # Find available files
        files = metadata.get('files', [])
        txt_files = [f['name'] for f in files if f['name'].endswith('_djvu.txt')]
        pdf_files = [f['name'] for f in files if f['name'].endswith('.pdf') and 'bw' not in f['name']]
        djvu_files = [f['name'] for f in files if f['name'].endswith('.djvu')]

        logger.info(f"Found files - TXT: {len(txt_files)}, PDF: {len(pdf_files)}, DJVU: {len(djvu_files)}")

        extractions = {}
        temp_dir = self.output_dir / self.identifier / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Method 1: TXT extraction
        if txt_files:
            txt_file = txt_files[0]
            txt_path = temp_dir / txt_file
            if self.download_file(txt_file, txt_path):
                text = self.extract_text_from_txt(txt_path)
                if text:
                    extractions['txt'] = text

        # Method 2: PDF extraction
        if pdf_files:
            pdf_file = pdf_files[0]
            pdf_path = temp_dir / pdf_file
            if self.download_file(pdf_file, pdf_path):
                text = self.extract_text_from_pdf(pdf_path)
                if text:
                    extractions['pdf'] = text

        # Method 3: DJVU extraction
        if djvu_files:
            djvu_file = djvu_files[0]
            djvu_path = temp_dir / djvu_file
            if self.download_file(djvu_file, djvu_path):
                text = self.extract_text_from_djvu(djvu_path)
                if text:
                    extractions['djvu'] = text

        # Compare extractions
        comparison = self.compare_extractions(extractions)

        return extractions, comparison

    def save_extraction_report(self, extractions: Dict[str, str], comparison: Dict, metadata: Dict):
        """Save detailed extraction report"""
        report_dir = self.output_dir / self.identifier
        report_dir.mkdir(parents=True, exist_ok=True)

        report = {
            'identifier': self.identifier,
            'extracted_at': datetime.now().isoformat(),
            'metadata': {
                'title': metadata.get('metadata', {}).get('title', 'Unknown'),
                'creator': metadata.get('metadata', {}).get('creator', 'Unknown'),
                'year': metadata.get('metadata', {}).get('year', 'Unknown'),
                'pages': metadata.get('metadata', {}).get('imagecount', 'Unknown')
            },
            'extraction_methods': list(extractions.keys()),
            'comparison': comparison,
            'files_available': [f['name'] for f in metadata.get('files', [])[:10]]
        }

        report_path = report_dir / 'extraction_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved extraction report to {report_path}")

        # Save each extraction method's output
        for method, text in extractions.items():
            output_path = report_dir / f'raw_{method}.txt'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Saved {method} extraction to {output_path}")

        return report


def main():
    """Main extraction function"""
    # Gandhi letters collection
    identifier = "in.ernet.dli.2015.208999"

    extractor = ArchiveOrgExtractor(identifier, output_dir="letters/mahatma-gandhi")

    logger.info(f"Starting extraction for {identifier}")
    extractions, comparison = extractor.extract_all_methods()

    if not extractions:
        logger.error("No extractions successful!")
        return

    # Get metadata
    metadata = extractor.get_metadata()

    # Save report
    report = extractor.save_extraction_report(extractions, comparison, metadata)

    logger.info("=" * 80)
    logger.info("EXTRACTION COMPLETE")
    logger.info(f"Methods used: {', '.join(extractions.keys())}")
    logger.info(f"Agreement: {comparison['agreement']}")
    logger.info(f"Recommended method: {comparison['recommended']}")
    logger.info("=" * 80)

    # Save the recommended extraction as the primary text
    recommended_text = extractions[comparison['recommended']]
    primary_path = extractor.output_dir / extractor.identifier / 'primary_text.txt'
    with open(primary_path, 'w', encoding='utf-8') as f:
        f.write(recommended_text)
    logger.info(f"Saved primary text to {primary_path}")


if __name__ == "__main__":
    main()
