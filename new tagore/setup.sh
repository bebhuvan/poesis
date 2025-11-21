#!/bin/bash

# Setup script for Darwinian OCR Pipeline
# Installs dependencies and verifies setup

set -e

echo "===================================="
echo "Darwinian OCR Pipeline Setup"
echo "===================================="
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Check Tesseract installation
echo "[2/6] Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n1)
    echo "✓ $tesseract_version detected"
else
    echo "✗ Tesseract not found!"
    echo ""
    echo "Please install Tesseract:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
    exit 1
fi
echo ""

# Create virtual environment (optional)
echo "[3/6] Setting up Python environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "[4/6] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements_ocr.txt -q
echo "✓ Python packages installed"
echo ""

# Check NLTK data (needed for text processing)
echo "[5/6] Downloading NLTK data..."
python3 << EOF
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    print("✓ NLTK data downloaded")
except:
    print("⚠ NLTK download failed (optional)")
EOF
echo ""

# Verify GPU availability (for EasyOCR)
echo "[6/6] Checking GPU availability..."
python3 << EOF
try:
    import torch
    if torch.cuda.is_available():
        print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
        print("  EasyOCR will use GPU acceleration")
    else:
        print("⚠ No GPU detected - OCR will run on CPU (slower)")
        print("  Consider enabling GPU for faster processing")
except ImportError:
    print("⚠ PyTorch not installed correctly")
EOF
echo ""

# Create necessary directories
echo "Creating directory structure..."
mkdir -p raw_images ocr_outputs consensus final_text metadata logs
echo "✓ Directories created"
echo ""

echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test with sample pages:"
echo "   python ocr_pipeline.py --mode sample --sample-size 3"
echo ""
echo "2. Review outputs in final_text/ and metadata/"
echo ""
echo "3. Process full collection:"
echo "   python ocr_pipeline.py --mode all"
echo ""
echo "For help:"
echo "   python ocr_pipeline.py --help"
echo ""
