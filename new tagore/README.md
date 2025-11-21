# Darwinian OCR Pipeline for Historical Letters

A sophisticated, multi-layered text extraction system for historical documents that uses competitive OCR and evolutionary selection to produce the highest quality text from scanned images.

## 🎯 Project Vision

This is **not** a simple OCR tool. This is an **archival-grade competitive extraction system** where multiple OCR engines "compete" Darwinian-style for the best text extraction, with consensus voting, uncertainty flagging, and multi-stage verification.

Think of it as **survival of the fittest for text extraction**.

## 📚 Current Collection

**Letters From Abroad** by Rabindranath Tagore (1924)
- 168 pages
- Public Domain
- Source: Internet Archive (in.ernet.dli.2015.97031)

## 🏗️ Architecture

### The Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│  1. DOWNLOAD         Archive.org → High-res page images     │
├─────────────────────────────────────────────────────────────┤
│  2. PREPROCESS       Denoise, deskew, enhance, binarize     │
├─────────────────────────────────────────────────────────────┤
│  3. COMPETITIVE OCR  Run multiple engines in parallel:      │
│                      • Tesseract (legacy + LSTM)            │
│                      • EasyOCR (deep learning)              │
│                      • TrOCR (transformer-based)            │
│                      • [PaddleOCR - optional]               │
├─────────────────────────────────────────────────────────────┤
│  4. CONSENSUS        Darwinian selection:                   │
│                      • Weighted voting                      │
│                      • Character-level alignment            │
│                      • Confidence scoring                   │
│                      • Edit distance comparison             │
├─────────────────────────────────────────────────────────────┤
│  5. TEXT CLEANING    Multi-stage cleanup:                   │
│                      • Fix ligatures (ﬁ → fi)               │
│                      • Fix hyphenation artifacts            │
│                      • Fix character confusables (rn → m)   │
│                      • Fix spacing & punctuation            │
│                      • Remove OCR artifacts                 │
├─────────────────────────────────────────────────────────────┤
│  6. VERIFICATION     Quality assurance:                     │
│                      • Character distribution analysis      │
│                      • Word validity checks                 │
│                      • Sentence structure verification      │
│                      • Uncertainty region flagging          │
│                      • Overall quality scoring              │
├─────────────────────────────────────────────────────────────┤
│  7. OUTPUT           Clean, formatted, publication-ready    │
│                      text with metadata and audit trail     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "new tagore"

# Install Python dependencies
pip install -r requirements_ocr.txt

# Install Tesseract OCR (system dependency)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. Test with Sample Pages

Process just 3 pages to test the system:

```bash
python ocr_pipeline.py --mode sample --sample-size 3
```

### 3. Process Full Collection

Once you're satisfied with the sample results:

```bash
python ocr_pipeline.py --mode all
```

### 4. Process Specific Range

```bash
python ocr_pipeline.py --mode range --start-page 10 --end-page 20
```

## 📊 Output Structure

```
new tagore/
├── raw_images/              # Downloaded page images
│   ├── page_0000.jpg
│   ├── page_0001.jpg
│   └── ...
├── ocr_outputs/             # Individual OCR engine outputs
│   ├── page_0000_tesseract.txt
│   ├── page_0000_easyocr.txt
│   ├── page_0000_trocr.txt
│   └── preprocessed_0000.jpg
├── consensus/               # Consensus text from voting
│   ├── page_0000.txt
│   └── ...
├── final_text/              # Clean, verified final text
│   ├── page_0000.txt
│   └── ...
├── metadata/                # Processing metadata & quality reports
│   ├── page_0000.json
│   └── ...
├── logs/                    # Summary reports and logs
│   ├── sample_report.json
│   ├── final_report.json
│   └── checkpoint_*.json
├── letters_from_abroad_complete.txt      # Combined plain text
└── letters_from_abroad_complete.md       # Combined markdown
```

## 🔬 How It Works

### Competitive OCR

Each page is processed by **multiple OCR engines simultaneously**:

- **Tesseract LSTM**: Modern neural OCR
- **Tesseract Legacy**: Classical OCR (for comparison)
- **EasyOCR**: Deep learning with GPU support
- **TrOCR**: Transformer-based vision model

Each engine produces its own extraction with confidence scores.

### Darwinian Consensus

The outputs compete through:

1. **Character-level voting**: Each character position gets votes from all engines
2. **Weighted scoring**: High-confidence engines get more weight
3. **Edit distance alignment**: Texts are aligned using sequence matching
4. **Uncertainty flagging**: Low-agreement regions are marked for review

The "fittest" text survives.

### Multi-Stage Cleaning

The consensus text goes through 7 cleaning stages:

1. **Ligature fixing**: ﬁ → fi, ﬂ → fl
2. **Hyphenation repair**: "word-\ncontinuation" → "wordcontinuation"
3. **Confusable characters**: rn → m, vv → w, l → I (context-aware)
4. **Spacing normalization**
5. **Line break handling**
6. **Punctuation fixing**
7. **Artifact removal**

### Quality Verification

Every page gets a quality report with:

- Overall quality score (0.0-1.0)
- Character distribution analysis
- Word validity checks
- Sentence structure verification
- Uncertain region flagging
- Actionable recommendations

## 📋 Metadata & Audit Trail

Each page generates a JSON metadata file with:

```json
{
  "page_number": 0,
  "processed_at": "2025-11-21T...",
  "ocr_engines": ["tesseract", "easyocr", "trocr"],
  "consensus": {
    "confidence": 0.87,
    "agreement_score": 0.92,
    "method": "weighted_voting",
    "uncertain_regions_count": 3
  },
  "cleaning": {
    "changes_made": 15,
    "quality_score": 0.94
  },
  "quality_verification": {
    "overall_score": 0.91,
    "checks_passed": 7,
    "checks_failed": 1,
    "warnings_count": 2
  },
  "recommendations": [
    "Review text for OCR artifacts",
    "Quality checks passed - text looks good"
  ]
}
```

## ⚙️ Configuration

Edit `ocr_config.py` to customize:

```python
# Which OCR engines to use
OCR_ENGINES = {
    "tesseract": {"enabled": True, "weight": 1.0},
    "easyocr": {"enabled": True, "weight": 1.2},
    "trocr": {"enabled": True, "weight": 1.3},
}

# Consensus method
CONSENSUS_METHOD = "weighted_voting"  # or "majority_voting", "confidence_voting"

# Quality thresholds
MIN_AGREEMENT_THRESHOLD = 0.6
CONFIDENCE_THRESHOLD = 0.7
MIN_PAGE_CONFIDENCE = 0.75

# Preprocessing steps
PREPROCESSING_STEPS = [
    "grayscale",
    "denoise",
    "contrast_enhancement",
    "deskew",
    "binarization"
]
```

## 🎓 Advanced Usage

### Adding New OCR Engines

1. Create a new engine class in `ocr_engines.py`:

```python
class MyCustomOCR(BaseOCREngine):
    def extract(self, image: Image.Image) -> OCRResult:
        # Your OCR logic here
        pass
```

2. Register it in `OCREngineFactory`

3. Enable it in `ocr_config.py`

### Custom Text Cleaning Rules

Add custom cleaning logic in `text_cleaner.py`:

```python
def _fix_custom_artifacts(self, text: str) -> str:
    # Your cleaning logic
    return text
```

### Historical Dictionary Support

Add archaic/historical words to avoid false spelling errors:

```python
HISTORICAL_DICTIONARIES = ["1920s_english.txt", "british_english_historical.txt"]
```

## 📈 Quality Metrics

The system provides multiple quality indicators:

- **Consensus Confidence**: How confident the OCR engines are
- **Agreement Score**: How much the engines agree with each other
- **Quality Score**: Overall text quality based on heuristics
- **Uncertain Regions**: Specific areas that need review

Pages with scores below thresholds are automatically flagged.

## 🐛 Troubleshooting

### OCR engines failing to initialize

Make sure you have the required dependencies:

```bash
# Tesseract
tesseract --version

# GPU support for EasyOCR (optional)
python -c "import torch; print(torch.cuda.is_available())"
```

### Low quality scores

- Check the preprocessed images in `ocr_outputs/`
- Adjust preprocessing steps in config
- Enable more OCR engines
- Lower quality thresholds

### Download failures

Archive.org might rate-limit. Adjust in `archive_downloader.py`:

```python
self.request_delay = 1.0  # Increase delay between requests
```

## 🎯 Next Steps

1. **Run sample processing** to validate the system
2. **Review sample outputs** in `final_text/` and `metadata/`
3. **Adjust configuration** based on results
4. **Process full collection** when satisfied
5. **Manual review** of uncertain regions
6. **Export** to your publishing platform

## 🏛️ Why This Approach?

Traditional OCR runs a single engine once and hopes for the best. This fails on:

- Degraded historical documents
- Archaic typography
- Irregular scanning quality
- Unusual layouts

**This system**:

✅ Runs multiple engines competitively
✅ Uses consensus to reduce errors
✅ Flags uncertainty automatically
✅ Provides audit trail for verification
✅ Produces publication-grade output

It's built for **archival reliability**, not convenience.

## 📜 License

This tool is for extracting public domain texts. All extracted texts retain their public domain status.

## 🙏 Acknowledgments

Built with:
- Tesseract OCR (Apache License)
- EasyOCR (Apache License)
- TrOCR (MIT License)
- Internet Archive (public service)

---

**Ready to extract the letters?**

```bash
python ocr_pipeline.py --mode sample --sample-size 5
```
