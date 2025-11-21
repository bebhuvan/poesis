# Installation Guide - Archive.org OCR Extraction System

## Prerequisites

### System Requirements

- **Python 3.8+** (Python 3.9 or 3.10 recommended)
- **4GB RAM minimum** (8GB+ recommended for large documents)
- **GPU optional** (improves EasyOCR speed but not required)
- **Disk space:** ~2GB for dependencies, plus cache space for documents

### Operating System Support

- ✅ Linux (Ubuntu 20.04+, Debian, Fedora, etc.)
- ✅ macOS (10.15+)
- ✅ Windows 10/11 (with WSL2 recommended)

---

## Step 1: Install Tesseract OCR

Tesseract is a system-level dependency that must be installed separately.

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev

# Verify installation
tesseract --version
# Should output: tesseract 4.x or 5.x
```

### macOS

```bash
brew install tesseract

# Verify installation
tesseract --version
```

### Windows

**Option 1: WSL2 (Recommended)**
```bash
# Install WSL2 first, then:
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Option 2: Native Windows**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer and add to PATH
3. Verify in Command Prompt: `tesseract --version`

---

## Step 2: Install Python Dependencies

### Create Virtual Environment (Recommended)

```bash
# Navigate to project directory
cd poesis

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Install Required Packages

```bash
# Install all dependencies
pip install -r requirements.txt

# This will install:
# - OpenCV (image processing)
# - Tesseract Python bindings
# - EasyOCR
# - PaddleOCR (optional)
# - NLTK (natural language processing)
# - And other dependencies
```

### Download NLTK Data

```bash
# Download required NLTK datasets
python -c "import nltk; nltk.download('words')"
python -c "import nltk; nltk.download('punkt')"
```

---

## Step 3: Verify Installation

Run the verification script:

```bash
python -c "
import sys
print('Python:', sys.version)

try:
    import cv2
    print('✓ OpenCV:', cv2.__version__)
except:
    print('✗ OpenCV not installed')

try:
    import pytesseract
    print('✓ Tesseract bindings installed')
    version = pytesseract.get_tesseract_version()
    print('  Tesseract version:', version)
except:
    print('✗ Tesseract not available')

try:
    import easyocr
    print('✓ EasyOCR installed')
except:
    print('✗ EasyOCR not installed')

try:
    import nltk
    print('✓ NLTK installed')
except:
    print('✗ NLTK not installed')

print('\nInstallation check complete!')
"
```

Expected output:
```
Python: 3.9.x
✓ OpenCV: 4.8.x
✓ Tesseract bindings installed
  Tesseract version: 5.x.x
✓ EasyOCR installed
✓ NLTK installed

Installation check complete!
```

---

## Step 4: Test with Sample Document

```bash
# Test extraction on Gandhi letters
python extract_archive_item.py in.ernet.dli.2015.208999 --pages 1

# This will:
# 1. Download page 1 of the Gandhi letters
# 2. Preprocess the image
# 3. Run OCR with multiple engines
# 4. Verify text quality
# 5. Save results to extracted_documents/

# Expected output:
# ============================================================
# ARCHIVE.ORG EXTRACTION PIPELINE
# ============================================================
# Item: in.ernet.dli.2015.208999
# Target accuracy: 99.9%
# ...
# Extraction complete!
```

---

## Troubleshooting

### "tesseract not found"

**Problem:** Python can't find Tesseract executable

**Solution:**
```bash
# Linux/macOS: Install Tesseract
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
brew install tesseract              # macOS

# Windows: Add to PATH or specify location
# In Python:
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### "ImportError: libGL.so.1"

**Problem:** OpenCV missing system libraries (Linux)

**Solution:**
```bash
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
```

### "CUDA not available" warning

**Problem:** EasyOCR wants GPU but doesn't find it

**Solution:** This is just a warning. EasyOCR will use CPU (slower but works fine).

To enable GPU support:
```bash
# Install CUDA toolkit (NVIDIA GPUs only)
# Then install:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Slow EasyOCR performance

**Solution 1:** Use GPU (if available)

**Solution 2:** Disable EasyOCR for faster processing
```python
# Edit multi_engine_ocr.py
self.engines = [OCREngine.TESSERACT, OCREngine.ABBYY]
# Remove OCREngine.EASYOCR for faster (but less accurate) processing
```

### Memory errors on large documents

**Solution:** Process in batches
```bash
# Process pages 1-50
python extract_archive_item.py IDENTIFIER --pages $(seq 1 50)

# Process pages 51-100
python extract_archive_item.py IDENTIFIER --pages $(seq 51 100)
```

---

## Optional: AI-Enhanced Verification

For even better verification, you can enable Claude AI integration:

```bash
# Install Anthropic SDK (already in requirements.txt)
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Enable in code (text_verification.py):
verifier = TextVerifier(use_ai=True, ai_api_key=os.getenv('ANTHROPIC_API_KEY'))
```

---

## Performance Optimization

### For Maximum Speed

```bash
# Disable preprocessing and verification (faster but less accurate)
python extract_archive_item.py IDENTIFIER \
  --no-preprocessing \
  --no-verification
```

### For Maximum Accuracy

```bash
# Enable all features (slower but highest quality)
python extract_archive_item.py IDENTIFIER \
  --verbose

# Then manually review flagged pages in:
# extracted_documents/IDENTIFIER/review_queue.json
```

---

## Next Steps

1. **Read the documentation:**
   - `ARCHIVE_ORG_README.md` - Complete user guide
   - `ARCHIVE_ORG_OCR_STRATEGIES.md` - Technical details

2. **Extract your first document:**
   ```bash
   python extract_archive_item.py YOUR_IDENTIFIER
   ```

3. **Review the results:**
   - Check `extracted_documents/YOUR_IDENTIFIER/`
   - Review `extraction_summary.json`
   - Process `review_queue.json` for manual verification

---

## Getting Help

- **Check logs:** `extraction_IDENTIFIER_TIMESTAMP.log`
- **Common issues:** See "Troubleshooting" section above
- **System issues:** Verify installation with Step 3

---

**You're ready to extract historical documents with maximum accuracy! 🎉**
