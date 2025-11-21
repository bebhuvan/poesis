"""
Image Preprocessing Pipeline
Prepares scanned images for optimal OCR performance
"""
import logging
from typing import Tuple
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    logger.warning("OpenCV not available - some preprocessing features disabled")
    HAS_CV2 = False


class ImagePreprocessor:
    """
    Multi-stage image preprocessing for OCR optimization
    Each stage improves different aspects of image quality
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.steps = self.config.get('PREPROCESSING_STEPS', [
            'grayscale',
            'denoise',
            'contrast_enhancement',
            'deskew',
            'binarization'
        ])

    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Apply all preprocessing steps sequentially
        """
        logger.info(f"Preprocessing image with steps: {self.steps}")

        processed = image.copy()

        for step in self.steps:
            try:
                if step == 'grayscale':
                    processed = self._to_grayscale(processed)
                elif step == 'denoise':
                    processed = self._denoise(processed)
                elif step == 'contrast_enhancement':
                    processed = self._enhance_contrast(processed)
                elif step == 'deskew':
                    processed = self._deskew(processed)
                elif step == 'binarization':
                    processed = self._binarize(processed)
                elif step == 'sharpen':
                    processed = self._sharpen(processed)
                else:
                    logger.warning(f"Unknown preprocessing step: {step}")
            except Exception as e:
                logger.error(f"Error in {step}: {e}")

        return processed

    def _to_grayscale(self, image: Image.Image) -> Image.Image:
        """Convert to grayscale if not already"""
        if image.mode != 'L':
            return image.convert('L')
        return image

    def _denoise(self, image: Image.Image) -> Image.Image:
        """Remove noise from the image"""
        if not HAS_CV2:
            # Fallback to PIL
            return image.filter(ImageFilter.MedianFilter(size=3))

        # Use OpenCV for better denoising
        img_array = np.array(image)
        denoised = cv2.fastNlMeansDenoising(img_array, h=10)
        return Image.fromarray(denoised)

    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance contrast for better OCR"""
        # Try adaptive histogram equalization if OpenCV available
        if HAS_CV2 and image.mode == 'L':
            img_array = np.array(image)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(img_array)
            return Image.fromarray(enhanced)

        # Fallback to PIL
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.5)

    def _deskew(self, image: Image.Image) -> Image.Image:
        """
        Detect and correct skew in the image
        Important for accurate line detection
        """
        if not HAS_CV2:
            logger.warning("Deskewing requires OpenCV - skipping")
            return image

        try:
            # Convert to numpy array
            img_array = np.array(image)

            # Detect edges
            edges = cv2.Canny(img_array, 50, 150, apertureSize=3)

            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is None:
                return image

            # Calculate average angle
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                angles.append(angle)

            median_angle = np.median(angles)

            # Only deskew if angle is significant
            if abs(median_angle) > 0.5:
                # Rotate image
                (h, w) = img_array.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(
                    img_array, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                logger.info(f"Deskewed by {median_angle:.2f} degrees")
                return Image.fromarray(rotated)

        except Exception as e:
            logger.error(f"Deskewing failed: {e}")

        return image

    def _binarize(self, image: Image.Image) -> Image.Image:
        """
        Convert to binary (black and white) using adaptive thresholding
        Best for old, degraded documents
        """
        if not HAS_CV2:
            # Simple thresholding with PIL
            return image.point(lambda x: 0 if x < 128 else 255, '1')

        # Adaptive thresholding with OpenCV (better for uneven lighting)
        img_array = np.array(image)

        # Ensure grayscale
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Adaptive threshold
        binary = cv2.adaptiveThreshold(
            img_array,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )

        return Image.fromarray(binary)

    def _sharpen(self, image: Image.Image) -> Image.Image:
        """Sharpen the image"""
        return image.filter(ImageFilter.SHARPEN)

    def create_variants(self, image: Image.Image) -> dict:
        """
        Create multiple preprocessed variants of the image
        Each OCR engine can choose the variant that works best
        """
        variants = {
            'original': image,
            'grayscale': self._to_grayscale(image),
            'enhanced': self._enhance_contrast(self._to_grayscale(image)),
            'binary': self._binarize(self._to_grayscale(image)),
        }

        # Full preprocessing
        variants['full_preprocess'] = self.preprocess(image)

        logger.info(f"Created {len(variants)} image variants")
        return variants
