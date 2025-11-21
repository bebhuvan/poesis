#!/usr/bin/env python3
"""
Image Preprocessing Pipeline for Historical Documents

Applies advanced image processing techniques to improve OCR accuracy
on degraded, aged, or poor-quality scans.

Techniques:
- Deskewing (rotation correction)
- Denoising (remove artifacts, stains, spots)
- Binarization (convert to clean black & white)
- Contrast enhancement (improve faded text visibility)
- Border removal (remove scan edges and binding shadows)
- Resolution enhancement (upscale if needed)

Critical for historical documents from Archive.org that may have:
- Yellowing, stains, water damage
- Uneven lighting
- Skewed scans
- Low contrast
- Background noise
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass
from PIL import Image
import time

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing pipeline."""

    # Deskewing
    enable_deskew: bool = True
    max_skew_angle: float = 10.0

    # Denoising
    enable_denoise: bool = True
    denoise_strength: int = 7  # Higher = more aggressive

    # Binarization
    enable_binarization: bool = True
    binarization_method: str = 'adaptive'  # 'adaptive', 'otsu', or 'sauvola'
    adaptive_block_size: int = 51
    adaptive_c: int = 10

    # Contrast enhancement
    enable_contrast: bool = True
    clip_limit: float = 2.0  # For CLAHE

    # Border removal
    enable_border_removal: bool = True
    border_threshold: int = 10  # Pixels

    # Resolution
    target_dpi: int = 300  # Minimum DPI for good OCR
    enable_upscaling: bool = True


@dataclass
class PreprocessingResult:
    """Result of preprocessing pipeline."""
    processed_image: np.ndarray
    original_size: Tuple[int, int]
    processed_size: Tuple[int, int]
    skew_angle: Optional[float]
    quality_score_before: float
    quality_score_after: float
    processing_time: float
    steps_applied: list


class ImagePreprocessor:
    """
    Advanced image preprocessing for historical documents.

    Designed to handle the specific challenges of Archive.org scans:
    aging, degradation, and varying scan quality.
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """
        Initialize preprocessor.

        Args:
            config: Preprocessing configuration (uses defaults if None)
        """
        self.config = config or PreprocessingConfig()

    def preprocess(self, image_path: Path, save_path: Optional[Path] = None) -> PreprocessingResult:
        """
        Run complete preprocessing pipeline on image.

        Args:
            image_path: Path to input image
            save_path: Optional path to save processed image

        Returns:
            PreprocessingResult with processed image and metadata
        """
        logger.info(f"Preprocessing: {image_path}")
        start_time = time.time()

        # Load image
        img = self._load_image(image_path)
        original_size = img.shape[:2]

        # Calculate initial quality score
        quality_before = self._calculate_quality_score(img)
        logger.info(f"Initial quality score: {quality_before:.2f}")

        steps_applied = []

        # Step 1: Deskew
        if self.config.enable_deskew:
            img, skew_angle = self._deskew(img)
            if skew_angle != 0:
                steps_applied.append(f"deskew ({skew_angle:.2f}°)")
                logger.info(f"Deskewed by {skew_angle:.2f} degrees")
        else:
            skew_angle = None

        # Step 2: Convert to grayscale if needed
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            steps_applied.append("grayscale conversion")

        # Step 3: Denoise
        if self.config.enable_denoise:
            img = self._denoise(img)
            steps_applied.append("denoising")
            logger.info("Applied denoising")

        # Step 4: Contrast enhancement
        if self.config.enable_contrast:
            img = self._enhance_contrast(img)
            steps_applied.append("contrast enhancement")
            logger.info("Enhanced contrast")

        # Step 5: Binarization
        if self.config.enable_binarization:
            img = self._binarize(img)
            steps_applied.append(f"binarization ({self.config.binarization_method})")
            logger.info(f"Applied {self.config.binarization_method} binarization")

        # Step 6: Remove borders
        if self.config.enable_border_removal:
            img = self._remove_borders(img)
            steps_applied.append("border removal")
            logger.info("Removed borders")

        # Step 7: Upscale if needed
        if self.config.enable_upscaling:
            img = self._ensure_resolution(img, image_path)
            steps_applied.append("resolution check")

        # Calculate final quality score
        quality_after = self._calculate_quality_score(img)
        logger.info(f"Final quality score: {quality_after:.2f}")

        processed_size = img.shape[:2]
        processing_time = time.time() - start_time

        # Save if requested
        if save_path:
            self._save_image(img, save_path)
            logger.info(f"Saved processed image to: {save_path}")

        result = PreprocessingResult(
            processed_image=img,
            original_size=original_size,
            processed_size=processed_size,
            skew_angle=skew_angle,
            quality_score_before=quality_before,
            quality_score_after=quality_after,
            processing_time=processing_time,
            steps_applied=steps_applied
        )

        logger.info(f"Preprocessing complete in {processing_time:.2f}s")
        logger.info(f"Quality improvement: {quality_after - quality_before:.2f}")

        return result

    def _load_image(self, image_path: Path) -> np.ndarray:
        """
        Load image file.

        Args:
            image_path: Path to image

        Returns:
            Image as numpy array
        """
        # Handle different formats
        if image_path.suffix.lower() in ['.jp2', '.j2k']:
            # JPEG2000 format (common in Archive.org)
            img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        else:
            img = cv2.imread(str(image_path))

        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        return img

    def _save_image(self, img: np.ndarray, save_path: Path):
        """
        Save processed image.

        Args:
            img: Image array
            save_path: Where to save
        """
        save_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(save_path), img)

    def _deskew(self, img: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Correct image rotation (deskew).

        Uses Hough transform to detect text lines and calculate skew angle.

        Args:
            img: Input image

        Returns:
            Tuple of (deskewed image, skew angle in degrees)
        """
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough line detection
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None:
            return img, 0.0

        # Calculate angles
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            if abs(angle) < self.config.max_skew_angle:
                angles.append(angle)

        if not angles:
            return img, 0.0

        # Median angle (robust to outliers)
        skew_angle = np.median(angles)

        # Only rotate if angle is significant
        if abs(skew_angle) < 0.5:
            return img, 0.0

        # Rotate image
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h),
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)

        return rotated, skew_angle

    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """
        Remove noise from image.

        Uses Non-local Means Denoising for high quality.

        Args:
            img: Input image

        Returns:
            Denoised image
        """
        # Non-local means denoising
        denoised = cv2.fastNlMeansDenoising(
            img,
            None,
            h=self.config.denoise_strength,
            templateWindowSize=7,
            searchWindowSize=21
        )

        return denoised

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE.

        CLAHE (Contrast Limited Adaptive Histogram Equalization) is
        excellent for improving faded text visibility.

        Args:
            img: Input image

        Returns:
            Contrast-enhanced image
        """
        # Create CLAHE object
        clahe = cv2.createCLAHE(
            clipLimit=self.config.clip_limit,
            tileGridSize=(8, 8)
        )

        enhanced = clahe.apply(img)

        return enhanced

    def _binarize(self, img: np.ndarray) -> np.ndarray:
        """
        Convert to black and white (binarization).

        Args:
            img: Input grayscale image

        Returns:
            Binary image (black text on white background)
        """
        if self.config.binarization_method == 'otsu':
            # Otsu's method (global thresholding)
            _, binary = cv2.threshold(
                img, 0, 255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

        elif self.config.binarization_method == 'adaptive':
            # Adaptive thresholding (handles varying lighting)
            binary = cv2.adaptiveThreshold(
                img, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.config.adaptive_block_size,
                self.config.adaptive_c
            )

        elif self.config.binarization_method == 'sauvola':
            # Sauvola binarization (excellent for degraded documents)
            binary = self._sauvola_binarization(img)

        else:
            raise ValueError(f"Unknown binarization method: {self.config.binarization_method}")

        return binary

    def _sauvola_binarization(self, img: np.ndarray, window_size: int = 25, k: float = 0.2, r: float = 128) -> np.ndarray:
        """
        Sauvola binarization method.

        Excellent for historical documents with uneven lighting.

        Args:
            img: Input image
            window_size: Local window size
            k: Parameter (0.2-0.5)
            r: Dynamic range (default 128)

        Returns:
            Binary image
        """
        # Convert to float
        img_float = img.astype(np.float64)

        # Calculate local mean and std
        mean = cv2.boxFilter(img_float, -1, (window_size, window_size))
        mean_sq = cv2.boxFilter(img_float ** 2, -1, (window_size, window_size))
        std = np.sqrt(mean_sq - mean ** 2)

        # Sauvola threshold
        threshold = mean * (1 + k * ((std / r) - 1))

        # Apply threshold
        binary = np.where(img_float > threshold, 255, 0).astype(np.uint8)

        return binary

    def _remove_borders(self, img: np.ndarray) -> np.ndarray:
        """
        Remove scan borders and binding shadows.

        Args:
            img: Input image

        Returns:
            Image with borders removed
        """
        # Find content bounding box
        # Assume borders are lighter/darker than content

        # Threshold to find content
        if len(img.shape) == 2:
            thresh = img
        else:
            thresh = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find contours
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return img

        # Find largest contour (content area)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Add small margin
        margin = self.config.border_threshold
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(img.shape[1] - x, w + 2 * margin)
        h = min(img.shape[0] - y, h + 2 * margin)

        # Crop
        cropped = img[y:y+h, x:x+w]

        return cropped

    def _ensure_resolution(self, img: np.ndarray, original_path: Path) -> np.ndarray:
        """
        Ensure image meets minimum DPI requirement.

        Args:
            img: Input image
            original_path: Path to original file (for DPI detection)

        Returns:
            Image scaled to appropriate resolution
        """
        try:
            # Try to get DPI from image metadata
            with Image.open(original_path) as pil_img:
                dpi = pil_img.info.get('dpi', (72, 72))
                if isinstance(dpi, tuple):
                    dpi = dpi[0]
        except:
            # Assume 150 DPI if unknown
            dpi = 150

        if dpi < self.config.target_dpi:
            # Upscale
            scale_factor = self.config.target_dpi / dpi
            new_width = int(img.shape[1] * scale_factor)
            new_height = int(img.shape[0] * scale_factor)

            logger.info(f"Upscaling from {dpi} DPI to {self.config.target_dpi} DPI")
            upscaled = cv2.resize(
                img,
                (new_width, new_height),
                interpolation=cv2.INTER_CUBIC
            )
            return upscaled

        return img

    def _calculate_quality_score(self, img: np.ndarray) -> float:
        """
        Calculate image quality score (0-100).

        Uses multiple metrics:
        - Sharpness (Laplacian variance)
        - Contrast (standard deviation)
        - SNR (Signal-to-Noise Ratio)

        Args:
            img: Input image

        Returns:
            Quality score (0-100)
        """
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()

        # Contrast (standard deviation)
        contrast = gray.std()

        # Normalize and combine
        # These are empirical values that work well
        sharpness_score = min(100, sharpness / 100)
        contrast_score = min(100, contrast / 2)

        quality = (sharpness_score + contrast_score) / 2

        return quality


def main():
    """Example usage of image preprocessor."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example: Preprocess a page
    image_path = Path("archive_cache/in.ernet.dli.2015.208999/page_001.jp2")

    if not image_path.exists():
        print(f"Sample image not found: {image_path}")
        print("Please run archive_org_fetcher.py first to download images")
        return

    # Create preprocessor with custom config
    config = PreprocessingConfig(
        enable_deskew=True,
        enable_denoise=True,
        enable_binarization=True,
        binarization_method='adaptive',
        enable_contrast=True,
        enable_border_removal=True,
        target_dpi=300
    )

    preprocessor = ImagePreprocessor(config)

    # Process image
    save_path = image_path.parent / f"processed_{image_path.stem}.png"
    result = preprocessor.preprocess(image_path, save_path)

    # Print results
    print(f"\n{'='*60}")
    print("PREPROCESSING RESULTS")
    print(f"{'='*60}")
    print(f"Original size: {result.original_size}")
    print(f"Processed size: {result.processed_size}")
    print(f"Skew angle: {result.skew_angle:.2f}° (if deskewed)" if result.skew_angle else "No skew detected")
    print(f"Quality before: {result.quality_score_before:.2f}")
    print(f"Quality after: {result.quality_score_after:.2f}")
    print(f"Quality improvement: {result.quality_score_after - result.quality_score_before:.2f}")
    print(f"Processing time: {result.processing_time:.2f}s")
    print(f"\nSteps applied: {', '.join(result.steps_applied)}")
    print(f"\nProcessed image saved to: {save_path}")


if __name__ == '__main__':
    main()
