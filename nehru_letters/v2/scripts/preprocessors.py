#!/usr/bin/env python3
"""
Image preprocessing strategies for OCR.
Each strategy implements a different approach to prepare images.
"""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
from ocr_engine_base import ImagePreprocessor


class RawPreprocessor(ImagePreprocessor):
    """No preprocessing - use raw image."""

    def preprocess(self, image: Image.Image) -> Image.Image:
        return image

    @property
    def name(self) -> str:
        return "raw"


class GrayscalePreprocessor(ImagePreprocessor):
    """Convert to grayscale."""

    def preprocess(self, image: Image.Image) -> Image.Image:
        return image.convert('L')

    @property
    def name(self) -> str:
        return "grayscale"


class EnhancedPreprocessor(ImagePreprocessor):
    """Grayscale + contrast enhancement."""

    def __init__(self, contrast_factor: float = 2.0, sharpness_factor: float = 2.0):
        self.contrast_factor = contrast_factor
        self.sharpness_factor = sharpness_factor

    def preprocess(self, image: Image.Image) -> Image.Image:
        # Convert to grayscale
        img = image.convert('L')

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(self.contrast_factor)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(self.sharpness_factor)

        return img

    @property
    def name(self) -> str:
        return "enhanced"


class BinarizedPreprocessor(ImagePreprocessor):
    """Binarization using fixed threshold."""

    def __init__(self, threshold: int = 128):
        self.threshold = threshold

    def preprocess(self, image: Image.Image) -> Image.Image:
        # Convert to grayscale
        img = image.convert('L')

        # Binarize
        img = img.point(lambda p: 255 if p > self.threshold else 0)

        return img

    @property
    def name(self) -> str:
        return f"binary{self.threshold}"


class OtsuPreprocessor(ImagePreprocessor):
    """Binarization using Otsu's method (requires OpenCV)."""

    def preprocess(self, image: Image.Image) -> Image.Image:
        try:
            import cv2

            # Convert to grayscale numpy array
            img_array = np.array(image.convert('L'))

            # Otsu's binarization
            _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return Image.fromarray(binary)
        except ImportError:
            # Fallback to fixed threshold if OpenCV not available
            print("Warning: OpenCV not available, using fixed threshold")
            return BinarizedPreprocessor().preprocess(image)

    @property
    def name(self) -> str:
        return "otsu"


class DenoisedPreprocessor(ImagePreprocessor):
    """Denoising + sharpening."""

    def preprocess(self, image: Image.Image) -> Image.Image:
        # Convert to grayscale
        img = image.convert('L')

        # Denoise using median filter
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        return img

    @property
    def name(self) -> str:
        return "denoised"


class AdaptiveBinarizedPreprocessor(ImagePreprocessor):
    """Adaptive binarization using local threshold (requires OpenCV)."""

    def __init__(self, block_size: int = 11, c: int = 2):
        self.block_size = block_size
        self.c = c

    def preprocess(self, image: Image.Image) -> Image.Image:
        try:
            import cv2

            # Convert to grayscale numpy array
            img_array = np.array(image.convert('L'))

            # Adaptive threshold
            binary = cv2.adaptiveThreshold(
                img_array,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.block_size,
                self.c
            )

            return Image.fromarray(binary)
        except ImportError:
            # Fallback to Otsu
            print("Warning: OpenCV not available, using Otsu")
            return OtsuPreprocessor().preprocess(image)

    @property
    def name(self) -> str:
        return "adaptive"


class DeskewedPreprocessor(ImagePreprocessor):
    """Deskew + binarization (requires OpenCV)."""

    def preprocess(self, image: Image.Image) -> Image.Image:
        try:
            import cv2

            # Convert to grayscale numpy array
            img_array = np.array(image.convert('L'))

            # Threshold to get binary image
            _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Invert image (text should be white on black for deskewing)
            binary_inv = cv2.bitwise_not(binary)

            # Find all non-zero points
            coords = np.column_stack(np.where(binary_inv > 0))

            # Calculate angle
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]

                # Adjust angle
                if angle < -45:
                    angle = 90 + angle
                elif angle > 45:
                    angle = angle - 90

                # Only deskew if angle is significant
                if abs(angle) > 0.5:
                    # Get image dimensions
                    (h, w) = img_array.shape[:2]
                    center = (w // 2, h // 2)

                    # Perform rotation
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    rotated = cv2.warpAffine(
                        binary,
                        M,
                        (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )

                    return Image.fromarray(rotated)

            return Image.fromarray(binary)

        except ImportError:
            # Fallback to just binarization
            print("Warning: OpenCV not available, skipping deskew")
            return OtsuPreprocessor().preprocess(image)

    @property
    def name(self) -> str:
        return "deskewed"


class HighResolutionPreprocessor(ImagePreprocessor):
    """Upscale image for better OCR."""

    def __init__(self, scale_factor: float = 2.0, then_binarize: bool = True):
        self.scale_factor = scale_factor
        self.then_binarize = then_binarize

    def preprocess(self, image: Image.Image) -> Image.Image:
        # Convert to grayscale
        img = image.convert('L')

        # Upscale
        new_size = (
            int(img.width * self.scale_factor),
            int(img.height * self.scale_factor)
        )
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Optionally binarize
        if self.then_binarize:
            img = img.point(lambda p: 255 if p > 128 else 0)

        return img

    @property
    def name(self) -> str:
        suffix = "_binary" if self.then_binarize else ""
        return f"highres{self.scale_factor}x{suffix}"


# Factory function to get all preprocessors
def get_all_preprocessors() -> list:
    """Get all available preprocessors."""
    return [
        RawPreprocessor(),
        GrayscalePreprocessor(),
        EnhancedPreprocessor(),
        BinarizedPreprocessor(threshold=128),
        OtsuPreprocessor(),
        DenoisedPreprocessor(),
        AdaptiveBinarizedPreprocessor(),
        DeskewedPreprocessor(),
        HighResolutionPreprocessor(scale_factor=2.0),
    ]


def get_recommended_preprocessors() -> list:
    """Get recommended set of diverse preprocessors."""
    return [
        RawPreprocessor(),                          # Baseline
        EnhancedPreprocessor(),                     # General purpose
        OtsuPreprocessor(),                         # Good for clean scans
        AdaptiveBinarizedPreprocessor(),            # Good for varying quality
        DeskewedPreprocessor(),                     # For skewed pages
        HighResolutionPreprocessor(scale_factor=1.5),  # For small text
    ]
