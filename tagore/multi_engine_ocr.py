"""
Multi-Engine OCR Ensemble - Strategy 1
Combines multiple OCR engines for maximum accuracy
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass, asdict
from collections import Counter
import numpy as np

from tagore_config import OCR_ENGINES_CONFIG, ENSEMBLE_CONFIG, MIN_ENGINES_FOR_CONSENSUS


@dataclass
class OCRResult:
    """Container for OCR engine output"""
    engine: str
    text: str
    confidence: float
    word_boxes: List[Dict] = None  # Bounding boxes for words
    char_confidences: List[float] = None  # Per-character confidence

    def to_dict(self):
        return asdict(self)


class MultiEngineOCR:
    """
    Orchestrates multiple OCR engines and combines results.
    Implements Strategy 1: Multi-Engine OCR Ensemble
    """

    def __init__(self, config: Dict = None):
        """
        Initialize OCR engines.

        Args:
            config: Engine configuration (defaults to OCR_ENGINES_CONFIG)
        """
        self.config = config or OCR_ENGINES_CONFIG
        self.logger = logging.getLogger(__name__)

        # Initialize available engines
        self.engines = {}
        self._init_engines()

    def _init_engines(self):
        """Initialize all enabled OCR engines."""

        # Tesseract
        if self.config['tesseract']['enabled']:
            try:
                import pytesseract
                self.engines['tesseract'] = self._ocr_tesseract
                self.logger.info("Tesseract OCR initialized")
            except ImportError:
                self.logger.warning("Tesseract not available (install: pip install pytesseract)")

        # EasyOCR
        if self.config['easyocr']['enabled']:
            try:
                import easyocr
                gpu = self.config['easyocr']['gpu']
                self.easyocr_reader = easyocr.Reader(
                    self.config['easyocr']['languages'],
                    gpu=gpu
                )
                self.engines['easyocr'] = self._ocr_easyocr
                self.logger.info(f"EasyOCR initialized (GPU: {gpu})")
            except ImportError:
                self.logger.warning("EasyOCR not available (install: pip install easyocr)")

        # PaddleOCR
        if self.config['paddleocr']['enabled']:
            try:
                from paddleocr import PaddleOCR
                self.paddleocr_engine = PaddleOCR(
                    lang=self.config['paddleocr']['lang'],
                    use_gpu=self.config['paddleocr']['use_gpu'],
                    use_angle_cls=self.config['paddleocr']['use_angle_cls'],
                    show_log=False
                )
                self.engines['paddleocr'] = self._ocr_paddleocr
                self.logger.info(f"PaddleOCR initialized (GPU: {self.config['paddleocr']['use_gpu']})")
            except ImportError:
                self.logger.warning("PaddleOCR not available (install: pip install paddleocr)")

        # ABBYY Baseline (extract from existing PDF)
        if self.config['abbyy_baseline']['enabled']:
            self.engines['abbyy_baseline'] = self._ocr_abbyy_baseline
            self.logger.info("ABBYY baseline extractor initialized")

        if len(self.engines) < MIN_ENGINES_FOR_CONSENSUS:
            self.logger.warning(
                f"Only {len(self.engines)} engines available. "
                f"Minimum {MIN_ENGINES_FOR_CONSENSUS} recommended for consensus."
            )

    def process_image(self, image_path: Path, page_number: Optional[int] = None) -> Dict:
        """
        Process image with all available OCR engines.

        Args:
            image_path: Path to image file
            page_number: Optional page number for ABBYY baseline extraction

        Returns:
            Dictionary containing results from all engines and consensus
        """
        self.logger.info(f"Processing {image_path.name} with {len(self.engines)} OCR engines")

        results = {}

        # Run each engine
        for engine_name, engine_func in self.engines.items():
            try:
                self.logger.debug(f"Running {engine_name}...")
                result = engine_func(image_path, page_number)
                results[engine_name] = result
                self.logger.info(f"{engine_name}: {len(result.text)} chars, confidence: {result.confidence:.2f}")
            except Exception as e:
                self.logger.error(f"{engine_name} failed: {e}", exc_info=True)
                results[engine_name] = OCRResult(engine_name, "", 0.0)

        # Generate consensus
        consensus = self._generate_consensus(results)

        return {
            'engine_results': {k: v.to_dict() for k, v in results.items()},
            'consensus': consensus,
            'metadata': {
                'image_path': str(image_path),
                'page_number': page_number,
                'engines_used': list(results.keys()),
                'engines_succeeded': len([r for r in results.values() if r.text]),
            }
        }

    def _ocr_tesseract(self, image_path: Path, page_number: Optional[int] = None) -> OCRResult:
        """Run Tesseract OCR."""
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)

        config = self.config['tesseract']
        custom_config = f"--psm {config['psm']} --oem {config['oem']} {config['config']}"

        # Get detailed data
        data = pytesseract.image_to_data(img, lang=config['language'],
                                        config=custom_config, output_type=pytesseract.Output.DICT)

        # Extract text
        text = pytesseract.image_to_string(img, lang=config['language'], config=custom_config)

        # Calculate average confidence
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0

        # Extract word boxes
        word_boxes = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 0:
                word_boxes.append({
                    'text': data['text'][i],
                    'confidence': int(data['conf'][i]) / 100.0,
                    'bbox': (data['left'][i], data['top'][i],
                            data['width'][i], data['height'][i])
                })

        return OCRResult(
            engine='tesseract',
            text=text.strip(),
            confidence=avg_confidence,
            word_boxes=word_boxes
        )

    def _ocr_easyocr(self, image_path: Path, page_number: Optional[int] = None) -> OCRResult:
        """Run EasyOCR."""
        import cv2

        img = cv2.imread(str(image_path))

        detail = self.config['easyocr']['detail']
        paragraph = self.config['easyocr']['paragraph']

        result = self.easyocr_reader.readtext(img, detail=detail, paragraph=paragraph)

        # Combine results
        text_parts = []
        confidences = []
        word_boxes = []

        for detection in result:
            bbox, text, conf = detection
            text_parts.append(text)
            confidences.append(conf)
            word_boxes.append({
                'text': text,
                'confidence': conf,
                'bbox': bbox
            })

        text = ' '.join(text_parts)
        avg_confidence = np.mean(confidences) if confidences else 0.0

        return OCRResult(
            engine='easyocr',
            text=text.strip(),
            confidence=avg_confidence,
            word_boxes=word_boxes
        )

    def _ocr_paddleocr(self, image_path: Path, page_number: Optional[int] = None) -> OCRResult:
        """Run PaddleOCR."""
        result = self.paddleocr_engine.ocr(str(image_path), cls=True)

        # Parse results
        text_parts = []
        confidences = []
        word_boxes = []

        if result and result[0]:
            for line in result[0]:
                bbox, (text, conf) = line
                text_parts.append(text)
                confidences.append(conf)
                word_boxes.append({
                    'text': text,
                    'confidence': conf,
                    'bbox': bbox
                })

        text = ' '.join(text_parts)
        avg_confidence = np.mean(confidences) if confidences else 0.0

        return OCRResult(
            engine='paddleocr',
            text=text.strip(),
            confidence=avg_confidence,
            word_boxes=word_boxes
        )

    def _ocr_abbyy_baseline(self, image_path: Path, page_number: Optional[int] = None) -> OCRResult:
        """
        Extract text from existing ABBYY OCR in PDF.
        This uses the baseline OCR that's already embedded in the Internet Archive PDF.
        """
        # This requires the PDF file and page number
        # For now, return placeholder - will be implemented when PDF is available

        if page_number is None:
            return OCRResult('abbyy_baseline', '', 0.0)

        try:
            # Try to extract from PDF using PyMuPDF
            import fitz  # PyMuPDF

            # Find PDF file (assume it's in same directory with .pdf extension)
            pdf_path = image_path.parent.parent / 'archive_pdf' / 'tagore_letters.pdf'

            if not pdf_path.exists():
                self.logger.debug(f"ABBYY PDF not found at {pdf_path}")
                return OCRResult('abbyy_baseline', '', 0.0)

            doc = fitz.open(pdf_path)
            if page_number <= len(doc):
                page = doc[page_number - 1]
                text = page.get_text()

                # ABBYY doesn't provide confidence scores in text layer
                # Assume high confidence since it's professional-grade
                confidence = 0.90

                return OCRResult('abbyy_baseline', text.strip(), confidence)

        except Exception as e:
            self.logger.debug(f"ABBYY baseline extraction failed: {e}")

        return OCRResult('abbyy_baseline', '', 0.0)

    def _generate_consensus(self, results: Dict[str, OCRResult]) -> Dict:
        """
        Generate consensus text from multiple OCR results.
        Uses voting and confidence weighting.
        """
        if not results:
            return {'text': '', 'confidence': 0.0, 'agreement_score': 0.0}

        # Filter out failed engines
        valid_results = {k: v for k, v in results.items() if v.text}

        if not valid_results:
            return {'text': '', 'confidence': 0.0, 'agreement_score': 0.0}

        # If only one engine succeeded, use it
        if len(valid_results) == 1:
            result = list(valid_results.values())[0]
            return {
                'text': result.text,
                'confidence': result.confidence,
                'agreement_score': 1.0,
                'method': 'single_engine'
            }

        # Character-level consensus
        if ENSEMBLE_CONFIG['character_level_voting']:
            consensus_text, agreement = self._character_level_consensus(valid_results)
        else:
            # Word-level consensus (fallback)
            consensus_text, agreement = self._word_level_consensus(valid_results)

        # Calculate weighted confidence
        weights = ENSEMBLE_CONFIG['confidence_weights']
        total_confidence = 0.0
        total_weight = 0.0

        for engine, result in valid_results.items():
            weight = weights.get(engine, 1.0)
            total_confidence += result.confidence * weight
            total_weight += weight

        avg_confidence = total_confidence / total_weight if total_weight > 0 else 0.0

        return {
            'text': consensus_text,
            'confidence': avg_confidence,
            'agreement_score': agreement,
            'method': 'ensemble',
            'engines_count': len(valid_results)
        }

    def _character_level_consensus(self, results: Dict[str, OCRResult]) -> Tuple[str, float]:
        """
        Character-level voting for maximum accuracy.
        Aligns texts and votes on each character position.
        """
        from difflib import SequenceMatcher

        texts = [r.text for r in results.values()]

        # Find longest text as reference
        reference = max(texts, key=len)

        # Align all texts to reference
        aligned_chars = [[] for _ in range(len(reference))]

        for text in texts:
            matcher = SequenceMatcher(None, reference, text)
            matches = matcher.get_opcodes()

            for tag, i1, i2, j1, j2 in matches:
                if tag == 'equal':
                    for i, j in zip(range(i1, i2), range(j1, j2)):
                        aligned_chars[i].append(text[j])
                elif tag == 'replace':
                    for i, j in zip(range(i1, i2), range(j1, j2)):
                        aligned_chars[i].append(text[j])
                elif tag == 'delete':
                    for i in range(i1, i2):
                        aligned_chars[i].append(reference[i])
                elif tag == 'insert':
                    pass  # Skip insertions for now

        # Vote on each character
        consensus_text = []
        agreements = []

        for chars in aligned_chars:
            if not chars:
                continue

            # Count votes
            counter = Counter(chars)
            most_common_char, count = counter.most_common(1)[0]

            consensus_text.append(most_common_char)
            agreements.append(count / len(chars))

        # Calculate overall agreement
        avg_agreement = np.mean(agreements) if agreements else 0.0

        return ''.join(consensus_text), avg_agreement

    def _word_level_consensus(self, results: Dict[str, OCRResult]) -> Tuple[str, float]:
        """
        Word-level voting (simpler, faster).
        Aligns texts and votes on each word.
        """
        texts = [r.text.split() for r in results.values()]

        # Use longest text as reference
        reference = max(texts, key=len)

        # Simple voting on word positions
        consensus_words = []
        agreements = []

        max_len = max(len(t) for t in texts)

        for i in range(max_len):
            words = [t[i] if i < len(t) else '' for t in texts]
            words = [w for w in words if w]  # Remove empty

            if not words:
                continue

            # Vote
            counter = Counter(words)
            most_common_word, count = counter.most_common(1)[0]

            consensus_words.append(most_common_word)
            agreements.append(count / len(words))

        avg_agreement = np.mean(agreements) if agreements else 0.0

        return ' '.join(consensus_words), avg_agreement


if __name__ == '__main__':
    # Test OCR
    logging.basicConfig(level=logging.DEBUG)

    ocr = MultiEngineOCR()

    # Example usage:
    # result = ocr.process_image(Path("data/processed/page001_enhanced.png"), page_number=1)
    # print(f"Consensus text: {result['consensus']['text'][:200]}...")
    # print(f"Confidence: {result['consensus']['confidence']:.2f}")
    # print(f"Agreement: {result['consensus']['agreement_score']:.2f}")
