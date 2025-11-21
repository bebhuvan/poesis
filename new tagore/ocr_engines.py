"""
OCR Engine Wrappers - Competitive extraction from multiple models
Each engine is a "species" competing for the best extraction
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Standardized OCR result from any engine"""
    text: str
    confidence: float
    engine_name: str
    word_boxes: List[Dict]  # Bounding boxes with word-level confidence
    processing_time: float
    metadata: Dict


class BaseOCREngine(ABC):
    """Base class for all OCR engines"""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.total_processed = 0
        self.avg_confidence = 0.0

    @abstractmethod
    def extract(self, image: Image.Image) -> OCRResult:
        """Extract text from image"""
        pass

    def update_stats(self, result: OCRResult):
        """Update engine statistics (for adaptive weighting)"""
        self.total_processed += 1
        # Running average of confidence
        self.avg_confidence = (
            (self.avg_confidence * (self.total_processed - 1) + result.confidence)
            / self.total_processed
        )


class TesseractEngine(BaseOCREngine):
    """Tesseract OCR Engine"""

    def __init__(self, config: Dict):
        super().__init__("tesseract", config.get("weight", 1.0))
        self.lang = config.get("lang", "eng")
        self.config_str = config.get("config", "--psm 6")

        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            raise ImportError("pytesseract not installed. Run: pip install pytesseract")

    def extract(self, image: Image.Image) -> OCRResult:
        """Extract text using Tesseract"""
        start_time = time.time()

        # Get detailed data with bounding boxes and confidence
        data = self.pytesseract.image_to_data(
            image,
            lang=self.lang,
            config=self.config_str,
            output_type=self.pytesseract.Output.DICT
        )

        # Extract text
        text = self.pytesseract.image_to_string(
            image,
            lang=self.lang,
            config=self.config_str
        )

        # Calculate average confidence
        confidences = [
            float(conf) for conf in data['conf']
            if conf != '-1' and str(conf).replace('.','').isdigit()
        ]
        avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0

        # Build word boxes
        word_boxes = []
        for i, word in enumerate(data['text']):
            if word.strip():
                word_boxes.append({
                    'text': word,
                    'confidence': float(data['conf'][i]) / 100.0 if data['conf'][i] != '-1' else 0.0,
                    'box': (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                })

        processing_time = time.time() - start_time

        result = OCRResult(
            text=text,
            confidence=avg_confidence,
            engine_name=self.name,
            word_boxes=word_boxes,
            processing_time=processing_time,
            metadata={'config': self.config_str, 'lang': self.lang}
        )

        self.update_stats(result)
        return result


class EasyOCREngine(BaseOCREngine):
    """EasyOCR Engine - Deep learning based"""

    def __init__(self, config: Dict):
        super().__init__("easyocr", config.get("weight", 1.0))
        self.languages = config.get("languages", ["en"])
        self.gpu = config.get("gpu", True)

        try:
            import easyocr
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu)
        except ImportError:
            raise ImportError("easyocr not installed. Run: pip install easyocr")

    def extract(self, image: Image.Image) -> OCRResult:
        """Extract text using EasyOCR"""
        start_time = time.time()

        # Convert PIL to numpy array
        image_np = np.array(image)

        # Run OCR with detail
        results = self.reader.readtext(image_np, detail=1)

        # Combine all text
        text_parts = []
        word_boxes = []
        confidences = []

        for (bbox, text, conf) in results:
            text_parts.append(text)
            confidences.append(conf)

            # Convert bbox to our format
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            box = (min(x_coords), min(y_coords),
                   max(x_coords) - min(x_coords),
                   max(y_coords) - min(y_coords))

            word_boxes.append({
                'text': text,
                'confidence': conf,
                'box': box
            })

        text = ' '.join(text_parts)
        avg_confidence = np.mean(confidences) if confidences else 0.0
        processing_time = time.time() - start_time

        result = OCRResult(
            text=text,
            confidence=avg_confidence,
            engine_name=self.name,
            word_boxes=word_boxes,
            processing_time=processing_time,
            metadata={'languages': self.languages, 'gpu': self.gpu}
        )

        self.update_stats(result)
        return result


class TrOCREngine(BaseOCREngine):
    """TrOCR Engine - Transformer-based OCR"""

    def __init__(self, config: Dict):
        super().__init__("trocr", config.get("weight", 1.0))
        self.model_name = config.get("model", "microsoft/trocr-large-printed")

        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import torch

            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.torch = torch
        except ImportError:
            raise ImportError("transformers or torch not installed")

    def extract(self, image: Image.Image) -> OCRResult:
        """Extract text using TrOCR (line-by-line processing)"""
        start_time = time.time()

        # For TrOCR, we need to process line-by-line
        # First, detect lines (simplified - use the whole image for now)
        # In production, you'd segment into lines first

        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)

        generated_ids = self.model.generate(pixel_values)
        text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # TrOCR doesn't provide confidence scores directly
        # We'll use a heuristic based on sequence probability
        confidence = 0.85  # Placeholder - could compute from logits

        processing_time = time.time() - start_time

        result = OCRResult(
            text=text,
            confidence=confidence,
            engine_name=self.name,
            word_boxes=[],  # TrOCR doesn't provide bounding boxes easily
            processing_time=processing_time,
            metadata={'model': self.model_name}
        )

        self.update_stats(result)
        return result


class OCREngineFactory:
    """Factory to create OCR engines based on configuration"""

    @staticmethod
    def create_engines(config: Dict) -> List[BaseOCREngine]:
        """Create all enabled OCR engines"""
        engines = []

        for engine_name, engine_config in config.items():
            if not engine_config.get("enabled", False):
                continue

            try:
                if engine_name.startswith("tesseract"):
                    engines.append(TesseractEngine(engine_config))
                elif engine_name == "easyocr":
                    engines.append(EasyOCREngine(engine_config))
                elif engine_name == "trocr":
                    engines.append(TrOCREngine(engine_config))
                # Add more engines here as needed

                logger.info(f"Initialized {engine_name} engine")
            except Exception as e:
                logger.warning(f"Failed to initialize {engine_name}: {e}")

        return engines


class CompetitiveOCR:
    """Run multiple OCR engines competitively on the same image"""

    def __init__(self, engines: List[BaseOCREngine]):
        self.engines = engines
        logger.info(f"Competitive OCR initialized with {len(engines)} engines")

    def extract_all(self, image: Image.Image) -> List[OCRResult]:
        """Run all OCR engines on the image"""
        results = []

        for engine in self.engines:
            try:
                logger.info(f"Running {engine.name}...")
                result = engine.extract(image)
                results.append(result)
                logger.info(
                    f"{engine.name}: {len(result.text)} chars, "
                    f"confidence: {result.confidence:.2f}, "
                    f"time: {result.processing_time:.2f}s"
                )
            except Exception as e:
                logger.error(f"Error in {engine.name}: {e}")

        return results
