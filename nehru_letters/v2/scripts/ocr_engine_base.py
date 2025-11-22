#!/usr/bin/env python3
"""
Base classes for OCR engines and strategies.
All OCR implementations inherit from these.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import time
from PIL import Image


@dataclass
class OCRResult:
    """Result from a single OCR operation."""
    text: str
    confidence: float
    engine_name: str
    strategy_name: str
    processing_time: float
    metadata: Dict = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        """Combined engine and strategy name."""
        return f"{self.engine_name}_{self.strategy_name}"


@dataclass
class PageOCRResults:
    """Collection of OCR results for a single page."""
    page_number: int
    image_path: Path
    results: List[OCRResult] = field(default_factory=list)

    def add_result(self, result: OCRResult):
        """Add a new OCR result."""
        self.results.append(result)

    def get_best(self, metric: str = 'confidence') -> Optional[OCRResult]:
        """Get best result by specified metric."""
        if not self.results:
            return None

        if metric == 'confidence':
            return max(self.results, key=lambda r: r.confidence)
        elif metric == 'length':
            return max(self.results, key=lambda r: len(r.text))
        else:
            return self.results[0]

    def get_by_name(self, name: str) -> Optional[OCRResult]:
        """Get result by engine_strategy name."""
        for result in self.results:
            if result.full_name == name:
                return result
        return None


class ImagePreprocessor(ABC):
    """Base class for image preprocessing strategies."""

    @abstractmethod
    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image before OCR.

        Args:
            image: Input PIL Image

        Returns:
            Preprocessed PIL Image
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        pass


class OCREngine(ABC):
    """Base class for OCR engines."""

    def __init__(self, name: str):
        self.name = name
        self._initialized = False

    @abstractmethod
    def initialize(self):
        """Initialize the OCR engine (load models, etc.)."""
        pass

    @abstractmethod
    def extract_text(self, image: Image.Image, **kwargs) -> Tuple[str, float]:
        """
        Extract text from image.

        Args:
            image: PIL Image
            **kwargs: Engine-specific parameters

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        pass

    def process_with_strategy(
        self,
        image_path: Path,
        preprocessor: ImagePreprocessor,
        **ocr_kwargs
    ) -> OCRResult:
        """
        Process image with a specific preprocessing strategy.

        Args:
            image_path: Path to image file
            preprocessor: Preprocessing strategy
            **ocr_kwargs: Additional OCR parameters

        Returns:
            OCRResult object
        """
        if not self._initialized:
            self.initialize()
            self._initialized = True

        start_time = time.time()

        # Load image
        image = Image.open(image_path)

        # Preprocess
        preprocessed = preprocessor.preprocess(image)

        # OCR
        text, confidence = self.extract_text(preprocessed, **ocr_kwargs)

        processing_time = time.time() - start_time

        return OCRResult(
            text=text,
            confidence=confidence,
            engine_name=self.name,
            strategy_name=preprocessor.name,
            processing_time=processing_time,
            metadata={
                'image_path': str(image_path),
                'image_size': image.size,
                'ocr_kwargs': ocr_kwargs
            }
        )

    def cleanup(self):
        """Clean up resources."""
        pass


class OCRStrategy:
    """Combines an engine with a preprocessing strategy."""

    def __init__(self, engine: OCREngine, preprocessor: ImagePreprocessor, **ocr_kwargs):
        self.engine = engine
        self.preprocessor = preprocessor
        self.ocr_kwargs = ocr_kwargs

    @property
    def name(self) -> str:
        """Full strategy name."""
        return f"{self.engine.name}_{self.preprocessor.name}"

    def process(self, image_path: Path) -> OCRResult:
        """Process image with this strategy."""
        return self.engine.process_with_strategy(
            image_path,
            self.preprocessor,
            **self.ocr_kwargs
        )


class OCROrchestrator:
    """Coordinates multiple OCR strategies running in parallel."""

    def __init__(self, strategies: List[OCRStrategy]):
        self.strategies = strategies

    def process_page(self, page_number: int, image_path: Path) -> PageOCRResults:
        """
        Process a single page with all strategies.

        Args:
            page_number: Page number
            image_path: Path to page image

        Returns:
            PageOCRResults with all strategy results
        """
        page_results = PageOCRResults(page_number, image_path)

        for strategy in self.strategies:
            try:
                result = strategy.process(image_path)
                page_results.add_result(result)
                print(f"  ✓ {strategy.name}: {len(result.text)} chars, {result.confidence:.1f}% conf, {result.processing_time:.2f}s")
            except Exception as e:
                print(f"  ✗ {strategy.name} failed: {e}")

        return page_results

    def cleanup(self):
        """Clean up all engines."""
        unique_engines = {s.engine for s in self.strategies}
        for engine in unique_engines:
            engine.cleanup()
