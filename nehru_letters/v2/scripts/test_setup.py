#!/usr/bin/env python3
"""
Test that all OCR engines and dependencies are properly installed.
"""

import sys

def test_imports():
    """Test all required imports."""
    print("Testing imports...")

    tests = [
        ("PIL (Pillow)", "from PIL import Image"),
        ("PyMuPDF (fitz)", "import fitz"),
        ("pytesseract", "import pytesseract"),
        ("numpy", "import numpy"),
        ("OpenCV", "import cv2"),
        ("EasyOCR", "import easyocr"),
        ("PaddleOCR", "from paddleocr import PaddleOCR"),
    ]

    results = []

    for name, import_statement in tests:
        try:
            exec(import_statement)
            print(f"  ✓ {name}")
            results.append((name, True, None))
        except Exception as e:
            print(f"  ✗ {name}: {str(e)}")
            results.append((name, False, str(e)))

    return results

def test_tesseract():
    """Test Tesseract functionality."""
    print("\nTesting Tesseract...")

    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"  ✓ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"  ✗ Tesseract test failed: {e}")
        return False

def test_opencv():
    """Test OpenCV functionality."""
    print("\nTesting OpenCV...")

    try:
        import cv2
        version = cv2.__version__
        print(f"  ✓ OpenCV version: {version}")

        # Test basic operation
        import numpy as np
        img = np.zeros((100, 100), dtype=np.uint8)
        _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
        print(f"  ✓ Basic operations work")
        return True
    except Exception as e:
        print(f"  ✗ OpenCV test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("OCR SETUP VERIFICATION")
    print("=" * 60 + "\n")

    import_results = test_imports()
    tesseract_ok = test_tesseract()
    opencv_ok = test_opencv()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_imports_ok = all(result[1] for result in import_results)

    if all_imports_ok and tesseract_ok and opencv_ok:
        print("✅ All systems operational!")
        print("   Ready to run OCR pipeline")
        return 0
    else:
        print("⚠️  Some components failed")
        print("\nFailed components:")
        for name, success, error in import_results:
            if not success:
                print(f"  - {name}: {error}")
        if not tesseract_ok:
            print(f"  - Tesseract functionality")
        if not opencv_ok:
            print(f"  - OpenCV functionality")
        return 1

if __name__ == "__main__":
    sys.exit(main())
