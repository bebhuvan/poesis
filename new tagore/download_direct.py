#!/usr/bin/env python3
"""
Download actual pages from archive.org using direct file access
Bypasses IIIF endpoint issues
"""
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
import time

def download_page_images(item_id, num_pages=3):
    """Download actual JP2 images from archive.org"""

    # Get metadata
    metadata_url = f"https://archive.org/metadata/{item_id}"
    response = requests.get(metadata_url)
    metadata = response.json()

    # Find JP2 files
    files = metadata.get('files', [])
    jp2_files = [f for f in files if f.get('name', '').endswith('.jp2')]
    jp2_files = sorted(jp2_files, key=lambda x: x['name'])[:num_pages]

    print(f"Found {len(jp2_files)} JP2 files")

    # Download each file
    output_dir = Path('raw_images')
    output_dir.mkdir(exist_ok=True)

    downloaded = []

    for i, file_info in enumerate(jp2_files):
        filename = file_info['name']
        url = f"https://archive.org/download/{item_id}/{filename}"

        print(f"Downloading {filename}...")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save JP2 file
            jp2_path = output_dir / f"page_{i:04d}.jp2"
            jp2_path.write_bytes(response.content)

            # Convert to JPG for easier processing
            try:
                from PIL import Image
                img = Image.open(BytesIO(response.content))
                jpg_path = output_dir / f"page_{i:04d}.jpg"
                img.convert('RGB').save(jpg_path, 'JPEG', quality=95)
                downloaded.append(jpg_path)
                print(f"  ✓ Saved to {jpg_path}")
            except Exception as e:
                print(f"  ⚠ Could not convert to JPG: {e}")
                downloaded.append(jp2_path)

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  ✗ Error: {e}")

    return downloaded

if __name__ == '__main__':
    print("Downloading pages from archive.org...")
    print()

    item_id = "in.ernet.dli.2015.97031"
    pages = download_page_images(item_id, num_pages=3)

    print()
    print(f"Downloaded {len(pages)} pages")
    print("You can now run:")
    print("  python3 ocr_pipeline.py --mode range --start-page 0 --end-page 3")
