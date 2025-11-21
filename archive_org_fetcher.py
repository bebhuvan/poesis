#!/usr/bin/env python3
"""
Archive.org Document Fetcher

Downloads historical documents from Archive.org in multiple formats:
- ABBYY OCR XML (pre-computed high-quality OCR)
- High-resolution images (JP2/JPEG)
- PDF with text layer
- DjVu with text layer
- Item metadata

Supports the complete extraction workflow for historical document preservation.
"""

import requests
import json
import gzip
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class ArchiveOrgFetcher:
    """Fetches documents from Archive.org with multi-format support."""

    def __init__(self, cache_dir: str = "archive_cache"):
        """
        Initialize fetcher.

        Args:
            cache_dir: Directory to cache downloaded files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.base_url = "https://archive.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HistoricalDocumentPreservation/1.0 (Educational use; mailto:your@email.com)'
        })

    def get_metadata(self, identifier: str) -> Dict:
        """
        Fetch metadata for an Archive.org item.

        Args:
            identifier: Archive.org item identifier (e.g., 'in.ernet.dli.2015.208999')

        Returns:
            Dictionary with item metadata
        """
        logger.info(f"Fetching metadata for: {identifier}")

        url = f"{self.base_url}/metadata/{identifier}"
        response = self.session.get(url)
        response.raise_for_status()

        metadata = response.json()

        # Extract useful information
        result = {
            'identifier': identifier,
            'title': metadata.get('metadata', {}).get('title', 'Unknown'),
            'creator': metadata.get('metadata', {}).get('creator', 'Unknown'),
            'date': metadata.get('metadata', {}).get('date'),
            'language': metadata.get('metadata', {}).get('language', []),
            'description': metadata.get('metadata', {}).get('description'),
            'page_count': metadata.get('metadata', {}).get('imagecount'),
            'files': self._parse_files(metadata.get('files', [])),
            'server': metadata.get('server'),
            'dir': metadata.get('dir')
        }

        logger.info(f"Title: {result['title']}")
        logger.info(f"Creator: {result['creator']}")
        logger.info(f"Pages: {result['page_count']}")
        logger.info(f"Files available: {len(result['files'])}")

        return result

    def _parse_files(self, files: List[Dict]) -> Dict:
        """
        Parse file list to categorize by type.

        Args:
            files: List of file dictionaries from metadata

        Returns:
            Dictionary categorized by file type
        """
        categorized = {
            'abbyy_gz': [],      # OCR XML files
            'images': [],        # JP2, JPEG, PNG
            'pdf': [],           # PDF files
            'djvu': [],          # DjVu files
            'text': [],          # Plain text files
            'other': []
        }

        for file_info in files:
            name = file_info.get('name', '')
            format_type = file_info.get('format', '').lower()

            if name.endswith('_abbyy.gz'):
                categorized['abbyy_gz'].append(file_info)
            elif format_type in ['jpeg', 'jpg', 'jp2', 'png']:
                categorized['images'].append(file_info)
            elif format_type == 'pdf' or name.endswith('.pdf'):
                categorized['pdf'].append(file_info)
            elif format_type == 'djvu' or name.endswith('.djvu'):
                categorized['djvu'].append(file_info)
            elif format_type == 'text' or name.endswith('.txt'):
                categorized['text'].append(file_info)
            else:
                categorized['other'].append(file_info)

        return categorized

    def download_file(self, identifier: str, filename: str,
                      force: bool = False) -> Optional[Path]:
        """
        Download a specific file from Archive.org item.

        Args:
            identifier: Archive.org item identifier
            filename: Name of file to download
            force: If True, re-download even if cached

        Returns:
            Path to downloaded file, or None if failed
        """
        # Check cache first
        cache_path = self.cache_dir / identifier / filename
        if cache_path.exists() and not force:
            logger.info(f"Using cached file: {cache_path}")
            return cache_path

        # Create directory structure
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Download
        url = f"{self.base_url}/download/{identifier}/{filename}"
        logger.info(f"Downloading: {url}")

        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            # Stream to file
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded to: {cache_path}")
            return cache_path

        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return None

    def download_abbyy_ocr(self, identifier: str) -> Optional[Path]:
        """
        Download ABBYY OCR file (compressed XML).

        Args:
            identifier: Archive.org item identifier

        Returns:
            Path to downloaded .gz file
        """
        metadata = self.get_metadata(identifier)
        abbyy_files = metadata['files']['abbyy_gz']

        if not abbyy_files:
            logger.warning(f"No ABBYY OCR file found for {identifier}")
            return None

        # Usually there's one ABBYY file per item
        abbyy_file = abbyy_files[0]
        filename = abbyy_file['name']

        return self.download_file(identifier, filename)

    def extract_abbyy_text(self, abbyy_gz_path: Path) -> Dict[int, Dict]:
        """
        Extract text from ABBYY OCR XML file.

        Args:
            abbyy_gz_path: Path to ABBYY .gz file

        Returns:
            Dictionary mapping page numbers to extracted data
        """
        logger.info(f"Extracting text from ABBYY OCR: {abbyy_gz_path}")

        # Decompress gzip
        with gzip.open(abbyy_gz_path, 'rt', encoding='utf-8') as f:
            xml_content = f.read()

        # Parse XML
        root = ET.fromstring(xml_content)

        pages = {}
        page_num = 0

        # ABBYY XML structure: <page> elements contain <block> → <line> → <formatting> → <charParams>
        for page in root.findall('.//page'):
            page_num += 1
            page_data = {
                'page_number': page_num,
                'width': page.get('width'),
                'height': page.get('height'),
                'blocks': [],
                'full_text': ''
            }

            full_text_lines = []

            # Extract text blocks
            for block in page.findall('.//block'):
                block_data = {
                    'block_type': block.get('blockType'),
                    'lines': []
                }

                for line in block.findall('.//line'):
                    line_text = self._extract_line_text(line)
                    block_data['lines'].append(line_text)
                    full_text_lines.append(line_text)

                page_data['blocks'].append(block_data)

            page_data['full_text'] = '\n'.join(full_text_lines)
            pages[page_num] = page_data

        logger.info(f"Extracted {len(pages)} pages from ABBYY OCR")
        return pages

    def _extract_line_text(self, line_element) -> str:
        """
        Extract text from a line element in ABBYY XML.

        Args:
            line_element: XML element representing a line

        Returns:
            Extracted text string
        """
        text_parts = []

        for formatting in line_element.findall('.//formatting'):
            # Get text content
            text = ''.join(formatting.itertext())
            text_parts.append(text)

        return ''.join(text_parts)

    def download_page_images(self, identifier: str,
                            pages: Optional[List[int]] = None,
                            format_pref: str = 'jp2') -> Dict[int, Path]:
        """
        Download high-resolution page images.

        Args:
            identifier: Archive.org item identifier
            pages: List of page numbers to download (None = all pages)
            format_pref: Preferred format ('jp2' or 'jpg')

        Returns:
            Dictionary mapping page numbers to image file paths
        """
        metadata = self.get_metadata(identifier)
        image_files = metadata['files']['images']

        # Filter by format preference
        preferred_images = [
            f for f in image_files
            if f['name'].endswith(f'.{format_pref}')
        ]

        if not preferred_images:
            logger.warning(f"No {format_pref} images found, trying JPEG...")
            preferred_images = [
                f for f in image_files
                if f['name'].endswith('.jpg') or f['name'].endswith('.jpeg')
            ]

        # Sort by filename to ensure page order
        preferred_images.sort(key=lambda x: x['name'])

        downloaded = {}

        for i, img_file in enumerate(preferred_images, 1):
            # Check if this page should be downloaded
            if pages and i not in pages:
                continue

            filename = img_file['name']
            path = self.download_file(identifier, filename)

            if path:
                downloaded[i] = path

        logger.info(f"Downloaded {len(downloaded)} page images")
        return downloaded

    def get_item_url(self, identifier: str, page: Optional[int] = None) -> str:
        """
        Get URL to view item on Archive.org.

        Args:
            identifier: Archive.org item identifier
            page: Specific page number (optional)

        Returns:
            URL string
        """
        if page:
            return f"{self.base_url}/details/{identifier}/page/n{page-1}"
        else:
            return f"{self.base_url}/details/{identifier}"

    def create_extraction_report(self, identifier: str, output_path: Path):
        """
        Create detailed report about available formats for an item.

        Args:
            identifier: Archive.org item identifier
            output_path: Where to save the report
        """
        metadata = self.get_metadata(identifier)

        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'identifier': identifier,
            'item_info': {
                'title': metadata['title'],
                'creator': metadata['creator'],
                'date': metadata['date'],
                'language': metadata['language'],
                'page_count': metadata['page_count']
            },
            'available_formats': {
                'abbyy_ocr': len(metadata['files']['abbyy_gz']),
                'images': len(metadata['files']['images']),
                'pdf': len(metadata['files']['pdf']),
                'djvu': len(metadata['files']['djvu']),
                'text': len(metadata['files']['text'])
            },
            'files': metadata['files'],
            'urls': {
                'item_page': self.get_item_url(identifier),
                'metadata_api': f"{self.base_url}/metadata/{identifier}",
                'download_base': f"{self.base_url}/download/{identifier}"
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Extraction report saved to: {output_path}")


def main():
    """Example usage of Archive.org fetcher."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example: Gandhi letters
    identifier = "in.ernet.dli.2015.208999"

    fetcher = ArchiveOrgFetcher()

    # Get metadata
    metadata = fetcher.get_metadata(identifier)
    print(f"\nTitle: {metadata['title']}")
    print(f"Creator: {metadata['creator']}")
    print(f"Pages: {metadata['page_count']}")

    # Download ABBYY OCR
    abbyy_path = fetcher.download_abbyy_ocr(identifier)
    if abbyy_path:
        print(f"\nABBYY OCR downloaded: {abbyy_path}")

        # Extract text
        pages = fetcher.extract_abbyy_text(abbyy_path)
        print(f"\nExtracted text from {len(pages)} pages")

        # Show first page sample
        if pages:
            first_page = pages[1]
            print(f"\n--- Page 1 Sample ---")
            print(first_page['full_text'][:500])
            print("...")

    # Download first 5 page images
    print("\nDownloading first 5 page images...")
    images = fetcher.download_page_images(identifier, pages=[1, 2, 3, 4, 5])
    print(f"Downloaded {len(images)} images")

    # Create extraction report
    report_path = Path("archive_cache") / identifier / "extraction_report.json"
    fetcher.create_extraction_report(identifier, report_path)
    print(f"\nExtraction report: {report_path}")


if __name__ == '__main__':
    main()
