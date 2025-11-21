"""
Layout Analysis & Segmentation - Strategy 3
Intelligent page structure detection for proper text ordering
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

from tagore_config import LAYOUT_CONFIG


@dataclass
class TextRegion:
    """Represents a region of text on the page"""
    type: str  # 'header', 'footer', 'body', 'footnote', 'page_number', 'margin_note'
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    text: str = ""
    confidence: float = 1.0
    reading_order: int = 0

    def to_dict(self):
        return asdict(self)


class LayoutAnalyzer:
    """
    Analyzes page layout and structure.
    Implements Strategy 3: Intelligent Layout Analysis & Segmentation
    """

    def __init__(self, config: Dict = None):
        """
        Initialize layout analyzer.

        Args:
            config: Layout configuration (defaults to LAYOUT_CONFIG)
        """
        self.config = config or LAYOUT_CONFIG
        self.logger = logging.getLogger(__name__)

    def analyze(self, image_path: Path, ocr_word_boxes: List[Dict] = None) -> Dict:
        """
        Analyze page layout and detect regions.

        Args:
            image_path: Path to image file
            ocr_word_boxes: Optional word bounding boxes from OCR

        Returns:
            Dictionary containing detected regions and reading order
        """
        self.logger.info(f"Analyzing layout: {image_path.name}")

        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        regions = []

        # Step 1: Detect header region
        header_region = self._detect_header(gray, height, width)
        if header_region:
            regions.append(header_region)

        # Step 2: Detect footer region
        footer_region = self._detect_footer(gray, height, width)
        if footer_region:
            regions.append(footer_region)

        # Step 3: Detect page number
        page_number_region = self._detect_page_number(gray, height, width)
        if page_number_region:
            regions.append(page_number_region)

        # Step 4: Detect body text regions
        body_regions = self._detect_body_regions(gray, height, width, regions)
        regions.extend(body_regions)

        # Step 5: Detect footnotes
        footnote_regions = self._detect_footnotes(gray, height, width, regions)
        regions.extend(footnote_regions)

        # Step 6: Detect margin notes
        margin_regions = self._detect_margin_notes(gray, height, width, regions)
        regions.extend(margin_regions)

        # Step 7: Determine reading order
        regions = self._determine_reading_order(regions, width)

        # Step 8: Detect multi-column layout if enabled
        if self.config['multi_column_detection']:
            regions = self._detect_columns(regions, width)

        return {
            'regions': [r.to_dict() for r in regions],
            'page_type': self._classify_page_type(regions),
            'layout_metrics': self._calculate_layout_metrics(regions, height, width)
        }

    def _detect_header(self, image: np.ndarray, height: int, width: int) -> Optional[TextRegion]:
        """Detect header region (top portion of page)."""
        header_height = int(height * self.config['header_height_ratio'])

        # Check if there's significant text in header region
        header_roi = image[0:header_height, :]

        if self._has_text(header_roi):
            return TextRegion(
                type='header',
                bbox=(0, 0, width, header_height),
                reading_order=0
            )

        return None

    def _detect_footer(self, image: np.ndarray, height: int, width: int) -> Optional[TextRegion]:
        """Detect footer region (bottom portion of page)."""
        footer_height = int(height * self.config['footer_height_ratio'])
        footer_y = height - footer_height

        footer_roi = image[footer_y:height, :]

        if self._has_text(footer_roi):
            return TextRegion(
                type='footer',
                bbox=(0, footer_y, width, footer_height),
                reading_order=999  # Last in reading order
            )

        return None

    def _detect_page_number(self, image: np.ndarray, height: int, width: int) -> Optional[TextRegion]:
        """
        Detect page number (usually bottom center or top/bottom corners).
        """
        # Check bottom center
        margin = int(height * 0.05)
        center_width = int(width * 0.2)
        center_x = (width - center_width) // 2

        bottom_center = image[height-margin:height, center_x:center_x+center_width]

        # Simple heuristic: page numbers are small, isolated text
        if self._looks_like_page_number(bottom_center):
            return TextRegion(
                type='page_number',
                bbox=(center_x, height-margin, center_width, margin),
                reading_order=1000  # Don't include in reading order
            )

        return None

    def _detect_body_regions(self, image: np.ndarray, height: int, width: int,
                            existing_regions: List[TextRegion]) -> List[TextRegion]:
        """
        Detect main body text regions.
        Excludes areas already classified as header/footer/etc.
        """
        # Create mask of existing regions
        mask = np.ones_like(image, dtype=np.uint8) * 255

        for region in existing_regions:
            x, y, w, h = region.bbox
            mask[y:y+h, x:x+w] = 0

        # Apply mask
        masked_image = cv2.bitwise_and(image, mask)

        # Find text contours in remaining area
        _, binary = cv2.threshold(masked_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Morphological operations to connect text
        kernel = np.ones((5, 20), np.uint8)  # Horizontal kernel to connect words
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        body_regions = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Filter small regions
            if w < width * 0.1 or h < height * 0.02:
                continue

            # Filter regions that are too wide (likely noise)
            if w > width * 0.95:
                continue

            body_regions.append(TextRegion(
                type='body',
                bbox=(x, y, w, h),
                reading_order=0  # Will be set later
            ))

        return body_regions

    def _detect_footnotes(self, image: np.ndarray, height: int, width: int,
                         existing_regions: List[TextRegion]) -> List[TextRegion]:
        """
        Detect footnotes (usually bottom of page, smaller font).
        """
        # Footnotes are typically in bottom 20% of page
        footnote_area_start = int(height * 0.80)

        # Check if there's already a footer
        footer_exists = any(r.type == 'footer' for r in existing_regions)

        if footer_exists:
            # Adjust search area
            footer = next(r for r in existing_regions if r.type == 'footer')
            footnote_area_start = footer.bbox[1] - int(height * 0.15)

        footnote_roi = image[footnote_area_start:height, :]

        # Detect smaller text (footnotes typically have smaller font)
        # This is a simplified approach - could be enhanced with font size detection

        if self._has_text(footnote_roi):
            # Check if text is noticeably smaller than body text
            # (simplified check - would need more sophisticated analysis)

            return [TextRegion(
                type='footnote',
                bbox=(0, footnote_area_start, width, height - footnote_area_start),
                reading_order=998
            )]

        return []

    def _detect_margin_notes(self, image: np.ndarray, height: int, width: int,
                            existing_regions: List[TextRegion]) -> List[TextRegion]:
        """
        Detect margin notes (text in left/right margins).
        """
        margin_notes = []
        margin_width = int(width * 0.15)

        # Check left margin
        left_margin = image[:, 0:margin_width]
        if self._has_text(left_margin):
            margin_notes.append(TextRegion(
                type='margin_note',
                bbox=(0, 0, margin_width, height),
                reading_order=997
            ))

        # Check right margin
        right_margin = image[:, width-margin_width:width]
        if self._has_text(right_margin):
            margin_notes.append(TextRegion(
                type='margin_note',
                bbox=(width-margin_width, 0, margin_width, height),
                reading_order=997
            ))

        return margin_notes

    def _determine_reading_order(self, regions: List[TextRegion], page_width: int) -> List[TextRegion]:
        """
        Determine the correct reading order for regions.
        Uses XY-cut algorithm or topological sort.
        """
        # Separate regions by type
        body_regions = [r for r in regions if r.type == 'body']
        other_regions = [r for r in regions if r.type != 'body']

        # Sort body regions by reading order
        if self.config['reading_order_algorithm'] == 'xy_cut':
            body_regions = self._xy_cut_reading_order(body_regions)
        else:
            # Simple top-to-bottom, left-to-right
            body_regions = sorted(body_regions, key=lambda r: (r.bbox[1], r.bbox[0]))

        # Assign reading order numbers
        for i, region in enumerate(body_regions, start=1):
            region.reading_order = i

        return other_regions + body_regions

    def _xy_cut_reading_order(self, regions: List[TextRegion]) -> List[TextRegion]:
        """
        XY-cut algorithm for reading order.
        Handles multi-column layouts correctly.
        """
        if not regions:
            return []

        if len(regions) == 1:
            return regions

        # Find horizontal cut
        y_coords = sorted([(r.bbox[1], r.bbox[1] + r.bbox[3]) for r in regions])

        # Check if we can split horizontally
        max_gap = 0
        split_y = None

        for i in range(len(y_coords) - 1):
            gap = y_coords[i+1][0] - y_coords[i][1]
            if gap > max_gap:
                max_gap = gap
                split_y = (y_coords[i][1] + y_coords[i+1][0]) / 2

        # Split if gap is significant
        if max_gap > 20:  # Minimum gap threshold
            top_regions = [r for r in regions if r.bbox[1] + r.bbox[3] <= split_y]
            bottom_regions = [r for r in regions if r.bbox[1] >= split_y]

            return self._xy_cut_reading_order(top_regions) + self._xy_cut_reading_order(bottom_regions)

        # Otherwise split vertically
        x_coords = sorted([(r.bbox[0], r.bbox[0] + r.bbox[2]) for r in regions])

        max_gap = 0
        split_x = None

        for i in range(len(x_coords) - 1):
            gap = x_coords[i+1][0] - x_coords[i][1]
            if gap > max_gap:
                max_gap = gap
                split_x = (x_coords[i][1] + x_coords[i+1][0]) / 2

        if max_gap > 20:
            left_regions = [r for r in regions if r.bbox[0] + r.bbox[2] <= split_x]
            right_regions = [r for r in regions if r.bbox[0] >= split_x]

            return self._xy_cut_reading_order(left_regions) + self._xy_cut_reading_order(right_regions)

        # Can't split further, return sorted by position
        return sorted(regions, key=lambda r: (r.bbox[1], r.bbox[0]))

    def _detect_columns(self, regions: List[TextRegion], page_width: int) -> List[TextRegion]:
        """Detect if page has multiple columns."""
        body_regions = [r for r in regions if r.type == 'body']

        if len(body_regions) < 2:
            return regions

        # Check for vertical alignment patterns
        x_positions = [r.bbox[0] for r in body_regions]

        # If there are distinct clusters of x positions, likely multi-column
        # (Simplified detection - could use more sophisticated clustering)

        return regions

    def _classify_page_type(self, regions: List[TextRegion]) -> str:
        """Classify page type based on detected regions."""
        region_types = [r.type for r in regions]

        # Title page: has header, minimal body
        if 'header' in region_types and len([r for r in regions if r.type == 'body']) <= 1:
            return 'title_page'

        # Chapter start: large header
        if 'header' in region_types:
            header = next(r for r in regions if r.type == 'header')
            if header.bbox[3] > 100:  # Large header
                return 'chapter_start'

        # Regular body page
        if 'body' in region_types:
            return 'body_page'

        # Blank or unknown
        return 'unknown'

    def _calculate_layout_metrics(self, regions: List[TextRegion],
                                  height: int, width: int) -> Dict:
        """Calculate layout quality metrics."""
        total_area = height * width
        text_area = sum(r.bbox[2] * r.bbox[3] for r in regions if r.type == 'body')

        return {
            'text_coverage': text_area / total_area,
            'region_count': len(regions),
            'body_region_count': len([r for r in regions if r.type == 'body']),
            'has_header': any(r.type == 'header' for r in regions),
            'has_footer': any(r.type == 'footer' for r in regions),
        }

    def _has_text(self, roi: np.ndarray) -> bool:
        """Check if region of interest contains text."""
        # Simple threshold and contour detection
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Count white pixels (text)
        white_pixel_count = np.sum(binary == 255)
        total_pixels = roi.size

        # If more than 2% white pixels, likely has text
        return (white_pixel_count / total_pixels) > 0.02

    def _looks_like_page_number(self, roi: np.ndarray) -> bool:
        """Check if region looks like a page number."""
        # Page numbers: short, numeric, centered
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Should have very few contours (1-3 digits)
        return 1 <= len(contours) <= 4


if __name__ == '__main__':
    # Test layout analysis
    logging.basicConfig(level=logging.DEBUG)

    analyzer = LayoutAnalyzer()

    # Example usage:
    # result = analyzer.analyze(Path("data/processed/page001_enhanced.png"))
    # print(f"Page type: {result['page_type']}")
    # print(f"Regions detected: {result['layout_metrics']['region_count']}")
