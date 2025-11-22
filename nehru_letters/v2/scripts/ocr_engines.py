#!/usr/bin/env python3
"""
OCR engine implementations.
"""

import pytesseract
from PIL import Image
import numpy as np
from typing import Tuple
from ocr_engine_base import OCREngine


class TesseractEngine(OCREngine):
    """Tesseract OCR engine."""

    def __init__(self, psm_mode: int = 6, oem_mode: int = 3):
        super().__init__("tesseract")
        self.psm_mode = psm_mode
        self.oem_mode = oem_mode

    def initialize(self):
        """Initialize Tesseract."""
        # Test if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            print(f"  Tesseract initialized (PSM {self.psm_mode}, OEM {self.oem_mode})")
        except Exception as e:
            raise RuntimeError(f"Tesseract not available: {e}")

    def extract_text(self, image: Image.Image, **kwargs) -> Tuple[str, float]:
        """Extract text using Tesseract."""
        # Build config
        config = f'--psm {self.psm_mode} --oem {self.oem_mode}'

        # Get detailed data with confidence
        data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)

        # Calculate average confidence
        confidences = [float(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Get text
        text = pytesseract.image_to_string(image, config=config)

        return text, avg_confidence

    @property
    def full_name(self) -> str:
        return f"{self.name}_psm{self.psm_mode}"


class EasyOCREngine(OCREngine):
    """EasyOCR engine."""

    def __init__(self, use_gpu: bool = False):
        super().__init__("easyocr")
        self.use_gpu = use_gpu
        self.reader = None

    def initialize(self):
        """Initialize EasyOCR."""
        try:
            import easyocr
            self.reader = easyocr.Reader(['en'], gpu=self.use_gpu)
            print(f"  EasyOCR initialized (GPU: {self.use_gpu})")
        except ImportError:
            raise RuntimeError("EasyOCR not installed. Install with: pip install easyocr")
        except Exception as e:
            raise RuntimeError(f"EasyOCR initialization failed: {e}")

    def extract_text(self, image: Image.Image, **kwargs) -> Tuple[str, float]:
        """Extract text using EasyOCR."""
        if self.reader is None:
            self.initialize()

        # Convert PIL image to numpy array
        img_array = np.array(image)

        # Run OCR
        results = self.reader.readtext(img_array, paragraph=True)

        # Extract text and confidence
        if not results:
            return "", 0.0

        # Combine all text
        text_parts = []
        confidences = []

        for bbox, text, conf in results:
            text_parts.append(text)
            confidences.append(conf)

        full_text = '\n'.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) * 100 if confidences else 0.0

        return full_text, avg_confidence


class PaddleOCREngine(OCREngine):
    """PaddleOCR engine."""

    def __init__(self, use_gpu: bool = False, lang: str = 'en'):
        super().__init__("paddleocr")
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr = None

    def initialize(self):
        """Initialize PaddleOCR."""
        try:
            from paddleocr import PaddleOCR

            # Suppress PaddleOCR verbose logging
            import os
            os.environ['FLAGS_allocator_strategy'] = 'auto_growth'

            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False
            )
            print(f"  PaddleOCR initialized (GPU: {self.use_gpu}, Lang: {self.lang})")
        except ImportError:
            raise RuntimeError("PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr")
        except Exception as e:
            raise RuntimeError(f"PaddleOCR initialization failed: {e}")

    def extract_text(self, image: Image.Image, **kwargs) -> Tuple[str, float]:
        """Extract text using PaddleOCR."""
        if self.ocr is None:
            self.initialize()

        # Convert PIL image to numpy array
        img_array = np.array(image)

        # Run OCR
        result = self.ocr.ocr(img_array, cls=True)

        # Extract text and confidence
        if not result or not result[0]:
            return "", 0.0

        text_parts = []
        confidences = []

        for line in result[0]:
            text = line[1][0]
            conf = line[1][1]
            text_parts.append(text)
            confidences.append(conf)

        full_text = '\n'.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) * 100 if confidences else 0.0

        return full_text, avg_confidence


def create_tesseract_engines() -> list:
    """Create multiple Tesseract engines with different PSM modes."""
    return [
        TesseractEngine(psm_mode=6, oem_mode=3),  # Default - uniform block of text
        TesseractEngine(psm_mode=1, oem_mode=3),  # Auto page segmentation with OSD
        TesseractEngine(psm_mode=3, oem_mode=3),  # Fully automatic page segmentation
        TesseractEngine(psm_mode=4, oem_mode=3),  # Single column of text
    ]


def create_all_engines(use_gpu: bool = False) -> list:
    """Create all available OCR engines."""
    engines = create_tesseract_engines()

    try:
        engines.append(EasyOCREngine(use_gpu=use_gpu))
    except RuntimeError as e:
        print(f"Skipping EasyOCR: {e}")

    try:
        engines.append(PaddleOCREngine(use_gpu=use_gpu))
    except RuntimeError as e:
        print(f"Skipping PaddleOCR: {e}")

    return engines
