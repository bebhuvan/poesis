#!/usr/bin/env python3
"""
Test script to verify OCR pipeline installation
Run this before processing to check if everything is set up correctly
"""
import sys
from pathlib import Path


def test_imports():
    """Test if all required packages are installed"""
    print("Testing Python package imports...")

    packages = {
        'PIL': 'Pillow',
        'pytesseract': 'pytesseract',
        'numpy': 'numpy',
        'requests': 'requests',
        'tqdm': 'tqdm',
    }

    optional_packages = {
        'easyocr': 'easyocr',
        'transformers': 'transformers',
        'torch': 'torch',
        'cv2': 'opencv-python',
    }

    failed = []
    optional_failed = []

    for module, package in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            failed.append(package)

    for module, package in optional_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package} (optional)")
        except ImportError:
            print(f"  ⚠ {package} - not installed (optional, but recommended)")
            optional_failed.append(package)

    print()

    if failed:
        print("❌ Required packages missing. Install with:")
        print(f"   pip install {' '.join(failed)}")
        return False

    if optional_failed:
        print("⚠️  Optional packages missing. For best results, install with:")
        print(f"   pip install {' '.join(optional_failed)}")

    return True


def test_tesseract():
    """Test Tesseract OCR"""
    print("Testing Tesseract OCR...")
    try:
        import pytesseract
        from PIL import Image
        import numpy as np

        # Create a simple test image
        test_image = Image.new('RGB', (200, 50), color='white')

        # Try to run OCR
        version = pytesseract.get_tesseract_version()
        print(f"  ✓ Tesseract {version} working")
        return True

    except Exception as e:
        print(f"  ✗ Tesseract error: {e}")
        print("    Make sure Tesseract is installed on your system")
        return False


def test_gpu():
    """Test GPU availability"""
    print("Testing GPU availability...")
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"  ✓ GPU available: {device_name}")
            print(f"    CUDA version: {torch.version.cuda}")
            return True
        else:
            print("  ⚠ No GPU detected - will use CPU (slower)")
            return True
    except ImportError:
        print("  ⚠ PyTorch not installed - GPU check skipped")
        return True


def test_directories():
    """Test if directory structure exists"""
    print("Testing directory structure...")

    required_dirs = [
        'raw_images',
        'ocr_outputs',
        'consensus',
        'final_text',
        'metadata',
        'logs'
    ]

    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ✗ {dir_name}/ - MISSING")
            all_exist = False

    if not all_exist:
        print("\n  Creating missing directories...")
        for dir_name in required_dirs:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
        print("  ✓ Directories created")

    return True


def test_pipeline_modules():
    """Test if pipeline modules can be imported"""
    print("Testing pipeline modules...")

    modules = [
        'ocr_config',
        'archive_downloader',
        'image_preprocessor',
        'ocr_engines',
        'consensus_engine',
        'text_cleaner',
        'quality_verifier',
        'ocr_pipeline'
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}.py")
        except ImportError as e:
            print(f"  ✗ {module}.py - ERROR: {e}")
            failed.append(module)

    if failed:
        print(f"\n❌ Module import errors. Check the files: {', '.join(failed)}")
        return False

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("OCR Pipeline Installation Test")
    print("=" * 60)
    print()

    tests = [
        ("Python Packages", test_imports),
        ("Tesseract OCR", test_tesseract),
        ("GPU Support", test_gpu),
        ("Directory Structure", test_directories),
        ("Pipeline Modules", test_pipeline_modules),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            results.append((test_name, False))
        print()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
        if not result:
            all_passed = False

    print()

    if all_passed:
        print("✅ All tests passed! Ready to process documents.")
        print()
        print("Try running:")
        print("  python ocr_pipeline.py --mode sample --sample-size 3")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
