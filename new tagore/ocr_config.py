"""
Configuration for the Darwinian OCR Pipeline
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
RAW_IMAGES_DIR = BASE_DIR / "raw_images"
OCR_OUTPUTS_DIR = BASE_DIR / "ocr_outputs"
CONSENSUS_DIR = BASE_DIR / "consensus"
FINAL_TEXT_DIR = BASE_DIR / "final_text"
METADATA_DIR = BASE_DIR / "metadata"
LOGS_DIR = BASE_DIR / "logs"

# Archive.org settings
ARCHIVE_ITEM_ID = "in.ernet.dli.2015.97031"
IMAGE_FORMAT = "jp2"  # or "jpg", "png"
DOWNLOAD_ORIGINAL = True

# OCR Engine Configuration
OCR_ENGINES = {
    "tesseract": {
        "enabled": True,
        "lang": "eng",
        "config": "--psm 6 --oem 3",  # Page segmentation mode 6, LSTM OCR Engine Mode
        "weight": 1.0,
    },
    "tesseract_legacy": {
        "enabled": True,
        "lang": "eng",
        "config": "--psm 6 --oem 0",  # Legacy engine for comparison
        "weight": 0.8,
    },
    "easyocr": {
        "enabled": True,
        "languages": ["en"],
        "gpu": True,  # Set to False if no GPU available
        "weight": 1.2,
    },
    "trocr": {
        "enabled": True,
        "model": "microsoft/trocr-large-printed",  # Or "microsoft/trocr-base-printed"
        "weight": 1.3,
    },
    "paddleocr": {
        "enabled": False,  # Enable if you install PaddleOCR
        "lang": "en",
        "weight": 1.1,
    }
}

# Image Preprocessing
PREPROCESSING_STEPS = [
    "grayscale",
    "denoise",
    "contrast_enhancement",
    "deskew",
    "binarization"
]

# Consensus Configuration
CONSENSUS_METHOD = "weighted_voting"  # Options: "majority_voting", "weighted_voting", "confidence_voting"
MIN_AGREEMENT_THRESHOLD = 0.6  # Minimum agreement percentage to accept a character
CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to accept OCR output without verification

# Text Cleaning & Verification
ENABLE_SPELL_CHECK = True
ENABLE_GRAMMAR_CHECK = True
ENABLE_HISTORICAL_DICTIONARY = True  # For archaic words
HISTORICAL_DICTIONARIES = ["1920s_english.txt", "british_english_historical.txt"]

# Character confusables (common OCR errors)
CONFUSABLE_PAIRS = [
    ('l', 'I', '1', '|'),
    ('O', '0'),
    ('S', '5'),
    ('rn', 'm'),
    ('vv', 'w'),
    ('cl', 'd'),
    ('nn', 'u'),
]

# Hyphenation handling
FIX_HYPHENATION = True
PRESERVE_INTENTIONAL_HYPHENS = True

# Ligature fixing
LIGATURE_MAP = {
    'ﬁ': 'fi',
    'ﬂ': 'fl',
    'ﬀ': 'ff',
    'ﬃ': 'ffi',
    'ﬄ': 'ffl',
    'ﬆ': 'st',
}

# Quality Assurance
MIN_PAGE_CONFIDENCE = 0.75  # Pages below this trigger manual review
ENABLE_UNCERTAINTY_FLAGGING = True
UNCERTAINTY_MARKERS = ["[?]", "[uncertain]", "[unclear]"]

# Output formats
OUTPUT_FORMATS = ["markdown", "txt", "json"]
PRESERVE_LAYOUT = True
PRESERVE_FORMATTING = True

# Parallel processing
MAX_WORKERS = 4  # Number of parallel OCR processes
BATCH_SIZE = 10  # Number of pages to process in a batch

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
VERBOSE = True

# Archive settings
ARCHIVE_METADATA = {
    "title": "Letters From Abroad",
    "author": "Rabindranath Tagore",
    "year": 1924,
    "total_pages": 168,
    "language": "English",
    "genre": "Letters/Epistolary"
}
