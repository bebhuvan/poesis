"""
Archive.org Image Downloader
Downloads high-quality page images from Internet Archive
"""
import logging
import time
from pathlib import Path
from typing import List, Optional
import requests
from PIL import Image
from io import BytesIO
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ArchiveDownloader:
    """
    Download images from archive.org
    Handles rate limiting and retries
    """

    def __init__(self, item_id: str, output_dir: Path):
        self.item_id = item_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = f"https://iiif.archivelab.org/iiif/{item_id}"
        self.metadata_url = f"https://archive.org/metadata/{item_id}"

        # Rate limiting
        self.request_delay = 0.5  # seconds between requests

    def get_metadata(self) -> dict:
        """Fetch item metadata from archive.org"""
        logger.info(f"Fetching metadata for {self.item_id}")

        response = requests.get(self.metadata_url)
        response.raise_for_status()

        metadata = response.json()
        logger.info(f"Retrieved metadata for: {metadata.get('metadata', {}).get('title')}")

        return metadata

    def get_page_count(self, metadata: dict = None) -> int:
        """Get total number of pages"""
        if metadata is None:
            metadata = self.get_metadata()

        # Try to get from imagecount
        files = metadata.get('files', [])

        # Count JP2 files (original scans)
        jp2_files = [f for f in files if f.get('name', '').endswith('.jp2')]

        if jp2_files:
            return len(jp2_files)

        # Fallback: try to get from metadata
        image_count = metadata.get('metadata', {}).get('imagecount')
        if image_count:
            return int(image_count)

        logger.warning("Could not determine page count from metadata")
        return 0

    def download_page(self, page_number: int, size: str = "full") -> Optional[Image.Image]:
        """
        Download a single page as PIL Image

        Args:
            page_number: Page number (0-indexed)
            size: Image size - "full", "pct:50", "1200,", etc.
        """
        # Archive.org IIIF format:
        # https://iiif.archivelab.org/iiif/{item_id}${page}/${region}/${size}/${rotation}/{quality}.jpg

        # Build IIIF URL
        # Format: /{identifier}${page}/{region}/{size}/{rotation}/{quality}.{format}
        url = f"{self.base_url}${page_number}/full/{size}/0/default.jpg"

        try:
            logger.debug(f"Downloading page {page_number} from {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Open as PIL Image
            image = Image.open(BytesIO(response.content))

            # Rate limiting
            time.sleep(self.request_delay)

            return image

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download page {page_number}: {e}")
            return None

    def download_page_to_file(self, page_number: int, output_path: Path, size: str = "full") -> bool:
        """Download page and save to file"""
        image = self.download_page(page_number, size)

        if image is None:
            return False

        try:
            image.save(output_path)
            logger.info(f"Saved page {page_number} to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save page {page_number}: {e}")
            return False

    def download_range(self, start_page: int, end_page: int, size: str = "full") -> List[Path]:
        """
        Download a range of pages
        Returns list of paths to saved images
        """
        saved_files = []

        logger.info(f"Downloading pages {start_page} to {end_page}")

        for page_num in tqdm(range(start_page, end_page), desc="Downloading pages"):
            output_path = self.output_dir / f"page_{page_num:04d}.jpg"

            # Skip if already downloaded
            if output_path.exists():
                logger.debug(f"Page {page_num} already exists, skipping")
                saved_files.append(output_path)
                continue

            if self.download_page_to_file(page_num, output_path, size):
                saved_files.append(output_path)
            else:
                logger.warning(f"Failed to download page {page_num}")

        logger.info(f"Downloaded {len(saved_files)} pages")
        return saved_files

    def download_all(self, size: str = "full", max_pages: Optional[int] = None) -> List[Path]:
        """
        Download all pages from the item
        """
        metadata = self.get_metadata()
        page_count = self.get_page_count(metadata)

        if max_pages:
            page_count = min(page_count, max_pages)

        logger.info(f"Downloading {page_count} pages...")

        return self.download_range(0, page_count, size)

    def download_sample(self, num_pages: int = 5, size: str = "full") -> List[Path]:
        """
        Download a sample of pages (first few pages)
        Useful for testing the OCR pipeline
        """
        logger.info(f"Downloading {num_pages} sample pages...")
        return self.download_range(0, num_pages, size)
