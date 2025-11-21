# Tagore Letters Historical OCR System

## 🎯 Project Overview

A **state-of-the-art digital preservation system** for extracting clean, high-quality text from Rabindranath Tagore's historical letters (1926). This system implements **5 extraction strategies** and **6 verification strategies** to achieve near-perfect accuracy in OCR of 100-year-old printed documents.

**Source**: [Internet Archive - Letters to a Friend](https://archive.org/details/in.ernet.dli.2015.52214/)
- 211 pages of printed English text
- 600 DPI scans
- Original publication: 1926 (George Allen & Unwin Ltd)

---

## ✨ Key Features

### 🔍 **5 Extraction Strategies**

1. **Multi-Engine OCR Ensemble** - Combines Tesseract, EasyOCR, PaddleOCR, and ABBYY baseline
2. **Adaptive Image Pre-processing** - Deskewing, denoising, binarization, contrast enhancement
3. **Intelligent Layout Analysis** - Detects headers, footers, body text, footnotes, reading order
4. **Context-Aware Post-Processing** - Spell checking, language models, pattern corrections
5. **Human-in-the-Loop Workflow** - Smart flagging and review interface

### ✅ **6 Verification Strategies**

1. **Cross-Engine Consensus Analysis** - Compare outputs, find disagreements
2. **Confidence Score Tracking** - Per-word/character confidence monitoring
3. **Language Model Validation** - Perplexity analysis, NER, grammar checking
4. **Historical & Contextual Validation** - Verify dates, names, events against known facts
5. **Manual Sampling & QA** - Statistical quality control with random sampling
6. **Diff Visualization** - Interactive comparison and review tools

### 🎯 **Quality Targets**

- **Character Error Rate (CER)**: < 0.5% (99.5% accuracy)
- **Word Error Rate (WER)**: < 1% (99% accuracy)
- **OCR Engine Consensus**: > 90% agreement
- **Average Confidence**: > 95%

---

## 📦 Installation

### System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0  # OpenCV
sudo apt-get install -y poppler-utils  # PDF processing
```

#### macOS:
```bash
brew install tesseract
brew install poppler
```

### Python Dependencies

```bash
cd tagore
pip install -r requirements_tagore.txt

# Download SpaCy language model
python -m spacy download en_core_web_sm
```

### GPU Support (Optional, for faster processing)

```bash
# For CUDA 11.8:
pip install torch --index-url https://download.pytorch.org/whl/cu118
pip install paddlepaddle-gpu
```

---

## 🚀 Quick Start

### 1. Download Images from Internet Archive

```bash
python tagore_orchestrator.py --download
```

This downloads all 211 pages as high-quality JP2 images.

### 2. Process a Single Page (Test)

```bash
python tagore_orchestrator.py --single-page 52 --image-dir data/images
```

### 3. Process a Page Range

```bash
python tagore_orchestrator.py --page-range 1-10 --image-dir data/images
```

### 4. Process Entire Document

```bash
python tagore_orchestrator.py --image-dir data/images
```

---

## 📂 Output Structure

```
tagore/
├── output/
│   ├── pages/
│   │   ├── page_0001/
│   │   │   ├── result.json          # Complete processing data
│   │   │   ├── text.txt             # Plain text output
│   │   │   └── text.md              # Markdown with metadata
│   │   ├── page_0002/
│   │   └── ...
│   ├── processed/
│   │   ├── page_0001/
│   │   │   ├── page_0001_binary_best.png
│   │   │   ├── page_0001_enhanced.png
│   │   │   └── ...
│   │   └── ...
│   └── summary.json                 # Overall statistics
├── logs/
│   └── tagore_ocr_YYYYMMDD_HHMMSS.log
└── data/
    └── images/                      # Downloaded images
```

---

## 📊 Output Formats

### Per-Page JSON (`result.json`)

Complete processing metadata including:
- All OCR engine outputs
- Consensus text
- Preprocessing variants used
- Layout analysis results
- Post-processing corrections
- Verification scores and flags
- Quality metrics

### Plain Text (`text.txt`)

Clean, corrected text ready for reading or further processing.

### Markdown (`text.md`)

Text with YAML frontmatter containing:
```yaml
---
page_number: 52
source_archive: https://archive.org/details/in.ernet.dli.2015.52214
quality: excellent
confidence: 0.967
corrections_made: 3
flags: 0
---
```

---

## 🔧 Configuration

Edit `tagore_config.py` to customize:

```python
# OCR engines to use
OCR_ENGINES_CONFIG = {
    'tesseract': {'enabled': True, ...},
    'easyocr': {'enabled': True, ...},
    'paddleocr': {'enabled': True, ...},
}

# Quality thresholds
QUALITY_TARGETS = {
    'character_error_rate': 0.005,
    'word_error_rate': 0.010,
    ...
}

# Preprocessing parameters
PREPROCESSING_CONFIG = {
    'deskew_enabled': True,
    'clahe_enabled': True,
    ...
}
```

---

## 📈 Quality Metrics

After processing, check `output/summary.json` for:

```json
{
  "stats": {
    "pages_processed": 211,
    "pages_succeeded": 210,
    "total_corrections": 1250,
    "total_flags": 15
  },
  "quality_distribution": {
    "excellent": 185,
    "good": 22,
    "acceptable": 3,
    "needs_improvement": 1
  }
}
```

---

## 🔍 Verification & Review

### Automatic Verification

Every page is automatically verified using 6 strategies:
- Cross-engine consensus
- Confidence tracking
- Language model validation
- Historical fact checking
- Statistical sampling plan
- Diff visualization

### Manual Review

Pages flagged for review will appear in logs with:
- **Type**: low_consensus, low_confidence, high_perplexity, etc.
- **Severity**: high, medium, low
- **Recommendations**: Specific actions to take

Example:
```
[WARNING] Page 52: low_confidence (medium severity)
  - 12 low-confidence words detected
  - Recommendation: Manual review recommended
```

---

## 🧪 Testing

```bash
# Run unit tests
pytest tagore/

# Test single component
python image_preprocessor.py
python multi_engine_ocr.py
python verification_suite.py
```

---

## 📚 Documentation

- **[STRATEGIES.md](STRATEGIES.md)** - Complete technical documentation of all 10 strategies
- **[tagore_config.py](tagore_config.py)** - Configuration reference
- Inline code documentation in each module

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  tagore_orchestrator.py                      │
│                   (Main Coordinator)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
│ Image        │  │ Multi-Engine    │  │ Layout       │
│ Preprocessor │→ │ OCR             │→ │ Analyzer     │
│ (Strategy 2) │  │ (Strategy 1)    │  │ (Strategy 3) │
└──────────────┘  └─────────────────┘  └──────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
│ Text         │  │ Verification    │  │ Export       │
│ Postprocess  │→ │ Suite           │→ │ (Multiple    │
│ (Strategy 4) │  │ (Strategies     │  │  Formats)    │
│              │  │  V1-V6)         │  │              │
└──────────────┘  └─────────────────┘  └──────────────┘
```

---

## 🤝 Contributing

This is a specialized historical preservation project. Contributions welcome for:
- Additional OCR engines
- Improved error correction patterns
- Historical validation data
- Testing and QA

---

## 📄 License

This tool is provided for historical document preservation and educational purposes.

- **Software**: MIT License (open source tools used)
- **Source Material**: Rabindranath Tagore's letters are in the Public Domain (author died 1941, >70 years ago)
- **Output**: Extracted text retains Public Domain status

---

## 🙏 Acknowledgments

- **Rabindranath Tagore** (1861-1941) - Nobel Laureate in Literature
- **Internet Archive** - Digitization and public access
- **Open Source OCR Community** - Tesseract, EasyOCR, PaddleOCR teams
- **Digital Humanities** - Preservation best practices

---

## 📞 Support & Issues

For issues, questions, or contributions:
1. Check the [STRATEGIES.md](STRATEGIES.md) documentation
2. Review configuration in `tagore_config.py`
3. Check logs in `logs/` directory
4. Open an issue with:
   - Page number
   - Error message
   - Log file excerpt
   - Expected vs actual output

---

## 🎯 Next Steps

After successful processing:

1. **Review Summary** - Check `output/summary.json` for quality metrics
2. **Manual QA** - Review flagged pages (listed in logs)
3. **Sampling** - Manually verify 10% of pages (as per sampling plan)
4. **Export** - Combine pages into final document format
5. **Publish** - Share extracted text with scholarly community

---

**This is not just OCR—it's digital literary archaeology done right.** 🏛️✨

---

*Last Updated: 2025-11-21*
*Version: 1.0*
