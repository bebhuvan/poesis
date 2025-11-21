"""
Configuration for Tagore Letters OCR System
Centralized settings for all OCR strategies and verification methods
"""

from pathlib import Path

# ==================== PROJECT INFO ====================
PROJECT_NAME = "Tagore Letters Digital Preservation"
ARCHIVE_URL = "https://archive.org/details/in.ernet.dli.2015.52214"
ARCHIVE_ID = "in.ernet.dli.2015.52214"

# ==================== DIRECTORIES ====================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"

# Create directories if they don't exist
for directory in [DATA_DIR, IMAGES_DIR, PROCESSED_DIR, OUTPUT_DIR, LOGS_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== DOWNLOAD SETTINGS ====================
DOWNLOAD_FORMAT = "jp2"  # High quality JPEG 2000
DOWNLOAD_DPI = 600  # Target DPI
MAX_CONCURRENT_DOWNLOADS = 3
REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# ==================== IMAGE PREPROCESSING (Strategy 2) ====================
PREPROCESSING_CONFIG = {
    # Deskewing
    'deskew_enabled': True,
    'deskew_angle_threshold': 0.5,  # degrees

    # Binarization methods (will try all and select best)
    'binarization_methods': ['otsu', 'sauvola', 'wolf'],
    'sauvola_window_size': 25,
    'sauvola_k': 0.2,

    # Noise removal
    'denoise_enabled': True,
    'denoise_kernel_size': (3, 3),
    'bilateral_filter_d': 9,
    'bilateral_filter_sigma_color': 75,
    'bilateral_filter_sigma_space': 75,

    # Contrast enhancement
    'clahe_enabled': True,
    'clahe_clip_limit': 2.0,
    'clahe_tile_grid_size': (8, 8),
    'gamma_correction': 1.2,

    # Border removal
    'remove_borders': True,
    'border_threshold': 0.02,  # % of image to remove

    # Super-resolution (optional, for low DPI images)
    'super_resolution_enabled': False,
    'super_resolution_scale': 2,
}

# ==================== OCR ENGINES (Strategy 1) ====================
OCR_ENGINES_CONFIG = {
    'tesseract': {
        'enabled': True,
        'language': 'eng',
        'psm': 1,  # Automatic page segmentation with OSD
        'oem': 3,  # Default, based on what is available
        'config': '--dpi 600',
    },
    'easyocr': {
        'enabled': True,
        'languages': ['en'],
        'gpu': True,
        'detail': 1,  # Get detailed output with confidence
        'paragraph': False,
    },
    'paddleocr': {
        'enabled': True,
        'lang': 'en',
        'use_gpu': True,
        'use_angle_cls': True,  # Detect text direction
        'det': True,  # Enable text detection
        'rec': True,  # Enable text recognition
    },
    'abbyy_baseline': {
        'enabled': True,
        'source': 'embedded_pdf',  # Extract from existing PDF OCR
    },
}

# Minimum engines required for consensus
MIN_ENGINES_FOR_CONSENSUS = 3

# ==================== ENSEMBLE & CONSENSUS ====================
ENSEMBLE_CONFIG = {
    'voting_method': 'weighted',  # 'majority' or 'weighted'
    'min_agreement': 0.6,  # 60% agreement required
    'confidence_weights': {
        'tesseract': 1.0,
        'easyocr': 1.1,  # Slightly prefer EasyOCR
        'paddleocr': 1.0,
        'abbyy_baseline': 0.9,  # Baseline, slightly lower weight
    },
    'character_level_voting': True,
    'word_level_fallback': True,
}

# ==================== LAYOUT ANALYSIS (Strategy 3) ====================
LAYOUT_CONFIG = {
    'detect_regions': True,
    'region_types': ['header', 'footer', 'body', 'footnote', 'page_number', 'margin_note'],

    # Page structure
    'header_height_ratio': 0.1,  # Top 10% of page
    'footer_height_ratio': 0.05,  # Bottom 5% of page

    # Typography
    'detect_font_sizes': True,
    'title_font_threshold': 1.5,  # 1.5x larger than body

    # Reading order
    'multi_column_detection': True,
    'reading_order_algorithm': 'xy_cut',  # or 'topological_sort'
}

# ==================== POST-PROCESSING (Strategy 4) ====================
POSTPROCESSING_CONFIG = {
    # Spell checking
    'spell_check_enabled': True,
    'spell_check_language': 'en',
    'custom_dictionary_path': BASE_DIR / 'dictionaries' / 'tagore_custom.txt',

    # Language model correction
    'language_model_enabled': True,
    'language_model_name': 'bert-base-uncased',
    'lm_confidence_threshold': 0.7,  # Only correct if LM confidence > 70%

    # Pattern-based corrections
    'pattern_corrections': {
        # Common OCR errors
        'rn': 'm',
        'cl': 'd',
        'vv': 'w',
        '0': 'O',  # Zero to capital O in words
        '1': 'I',  # One to capital I in words
    },

    # Formatting
    'fix_line_breaks': True,
    'resolve_hyphenation': True,
    'smart_quotes': True,
    'normalize_whitespace': True,
}

# ==================== VERIFICATION (Strategies V1-V6) ====================

# V1: Cross-Engine Consensus
CONSENSUS_VERIFICATION_CONFIG = {
    'enabled': True,
    'agreement_threshold': 0.8,  # 80% agreement
    'generate_heatmap': True,
    'export_disagreements': True,
}

# V2: Confidence Score Tracking
CONFIDENCE_VERIFICATION_CONFIG = {
    'enabled': True,
    'thresholds': {
        'excellent': 0.95,
        'good': 0.80,
        'uncertain': 0.60,
        'poor': 0.0,
    },
    'generate_heatmap': True,
    'flag_below_threshold': 0.80,
}

# V3: Language Model Validation
LANGUAGE_MODEL_VERIFICATION_CONFIG = {
    'enabled': True,
    'model_name': 'gpt2',  # or 'bert-base-uncased'
    'perplexity_threshold': 100,  # Flag sentences with perplexity > 100
    'use_ner': True,  # Named Entity Recognition
    'grammar_check': True,
}

# V4: Historical & Contextual Validation
HISTORICAL_VERIFICATION_CONFIG = {
    'enabled': True,
    'check_biographical': True,
    'check_dates': True,
    'check_places': True,
    'check_vocabulary': True,
    'wikidata_api': True,
    'date_range': (1861, 1941),  # Tagore's lifetime
}

# V5: Manual Sampling & QA
MANUAL_VERIFICATION_CONFIG = {
    'enabled': True,
    'random_sample_percentage': 0.10,  # 10% of pages
    'always_review_pages': [1, 2, 3, -1, -2, -3],  # First and last 3 pages
    'review_flagged_regions': True,
    'target_cer': 0.005,  # Character Error Rate < 0.5%
    'target_wer': 0.010,  # Word Error Rate < 1%
}

# V6: Diff Visualization
DIFF_VISUALIZATION_CONFIG = {
    'enabled': True,
    'generate_html': True,
    'side_by_side': True,
    'highlight_differences': True,
    'confidence_overlay': True,
    'interactive_review': True,
}

# ==================== QUALITY METRICS ====================
QUALITY_TARGETS = {
    'character_error_rate': 0.005,  # <0.5%
    'word_error_rate': 0.010,  # <1%
    'consensus_rate': 0.90,  # >90%
    'average_confidence': 0.95,  # >95%
    'coverage': 1.0,  # 100%
}

# ==================== OUTPUT FORMATS ====================
OUTPUT_FORMATS = {
    'json': True,  # Per-page JSON with all metadata
    'txt': True,  # Plain text
    'markdown': True,  # Markdown with YAML frontmatter
    'html': True,  # HTML with styling
    'epub': False,  # EPUB e-book (requires pandoc)
    'latex': False,  # LaTeX for academic publication
    'tei': False,  # TEI XML for scholarly editions
}

# ==================== METADATA ====================
DOCUMENT_METADATA = {
    'title': 'Letters to a Friend',
    'author': 'Rabindranath Tagore',
    'author_birth_year': 1861,
    'author_death_year': 1941,
    'original_publication_year': 1926,
    'publisher': 'George Allen & Unwin Ltd',
    'language': 'English',
    'total_pages': 211,
    'public_domain': True,
    'license': 'Public Domain (author died 1941, >70 years ago)',
}

# ==================== LOGGING ====================
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_logging': True,
    'console_logging': True,
    'log_file': LOGS_DIR / 'tagore_ocr.log',
}

# ==================== PARALLELIZATION ====================
PARALLEL_CONFIG = {
    'max_workers': 4,  # For parallel OCR processing
    'batch_size': 10,  # Process N pages at a time
    'gpu_memory_fraction': 0.8,  # % of GPU memory to use
}

# ==================== CUSTOM DICTIONARIES ====================
# Words to add to spell checker (proper nouns, historical terms)
CUSTOM_VOCABULARY = [
    # Names
    'Rabindranath', 'Tagore', 'Santiniketan', 'Visva-Bharati',

    # Places (1920s spelling)
    'Calcutta', 'Bolpur',

    # Historical terms
    'Brahmo', 'Samaj',

    # Common Bengali words in English text
    'Gurudev', 'Shantiniketan',
]

# Known people in Tagore's circle
KNOWN_CORRESPONDENTS = [
    'C. F. Andrews',
    'William Rothenstein',
    'Romain Rolland',
    'Ezra Pound',
    'W. B. Yeats',
]

# Historical events for validation
HISTORICAL_EVENTS = {
    1913: 'Nobel Prize in Literature',
    1915: 'Knighthood from King George V',
    1919: 'Renounced knighthood (Jallianwala Bagh)',
    1921: 'Visva-Bharati founded',
}
