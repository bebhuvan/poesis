# Quick Start Guide

Get the OCR pipeline running in 5 minutes.

## 1. Install Dependencies (2 minutes)

```bash
cd "new tagore"

# Install system dependency (Tesseract)
sudo apt-get install tesseract-ocr  # Linux
# OR
brew install tesseract              # macOS

# Install Python packages
pip install -r requirements_ocr.txt
```

## 2. Test Installation (30 seconds)

```bash
python3 test_installation.py
```

You should see all tests pass ✓

## 3. Run Demo (1 minute)

```bash
python3 demo_standalone.py
```

This creates a test image and runs it through the entire pipeline.

## 4. Process Real Pages (when archive.org is available)

```bash
# Process 5 sample pages
python3 ocr_pipeline.py --mode sample --sample-size 5

# Check the results
ls final_text/
cat final_text/page_0000.txt
```

## 5. Review Quality

Check the quality reports:

```bash
# View metadata for a page
cat metadata/page_0000.json | python3 -m json.tool

# View logs
cat logs/sample_report.json | python3 -m json.tool
```

## Enhanced Processing (Optional)

For better OCR quality, install advanced engines:

```bash
pip install easyocr transformers torch opencv-python
```

Then re-run the pipeline. The system will automatically use all available engines.

## Troubleshooting

**Archive.org is unavailable:**
- Try again later (service is occasionally down)
- Use demo_standalone.py to test the pipeline with generated images

**Low OCR confidence:**
- Install additional OCR engines (easyocr, transformers)
- Adjust preprocessing steps in ocr_config.py
- Check the preprocessed images in ocr_outputs/

**Import errors:**
- Run: python3 test_installation.py
- Install missing packages as indicated

## What's Next?

1. Review the extracted text in `final_text/`
2. Check quality scores in `metadata/`
3. Process more pages with `--mode range --start-page 0 --end-page 20`
4. When satisfied, process the full collection with `--mode all`

See README.md for full documentation.
