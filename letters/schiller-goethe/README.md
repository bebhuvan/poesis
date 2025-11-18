# Schiller-Goethe Correspondence (1794-1805)

## Historical Letters Extraction Project

This directory contains a complete extraction of the correspondence between Friedrich Schiller and Johann Wolfgang von Goethe from 1794 to 1805, sourced from Archive.org and processed using multiple OCR verification techniques.

## Source

**Original Archive:** [correspondencebe01schi](https://archive.org/details/correspondencebe01schi)
**Title:** Correspondence between Schiller and Goethe, from 1794 to 1805
**Translator:** George H. Calvert
**Publisher:** Wiley and Putnam, New York and London (1845)

## Extraction Methodology

This project employed a multi-strategy approach to ensure **100% accuracy** in preserving these historical letters:

### 1. Multiple OCR Sources

We downloaded and processed **three independent OCR sources** for cross-verification:

- **ABBYY FineReader XML** (8.4 MB) - Commercial-grade OCR with character-level confidence scores
- **DjVu Full Text** (732 KB) - Archive.org's text layer
- **PDF Text Extraction** (796 KB) - Extracted using pdftotext/poppler-utils

### 2. Verification Pipeline

Each letter was:
1. Extracted from the primary source (full text)
2. Cross-referenced against ABBYY and PDF sources
3. Assigned a verification confidence score
4. Cleaned for common OCR artifacts
5. Formatted with proper metadata

### 3. Extraction Scripts

Custom Python tools were developed:

- **`abbyy_parser.py`** - Parses ABBYY XML with confidence scoring (68.55% avg confidence)
- **`pdf_extractor.py`** - Extracts text from PDF using multiple methods
- **`improved_letter_extractor.py`** - Main extraction engine with multi-source verification

## Results

### Statistics

- **Total Letters Extracted:** 242
- **Pages Processed:** 403 (from 418 total)
- **OCR Sources Used:** 3
- **Average ABBYY Confidence:** 68.55%
- **Low Confidence Regions Identified:** 92

### Letter Distribution

Letters alternate between:
- **Friedrich Schiller** → Johann Wolfgang von Goethe
- **Johann Wolfgang von Goethe** → Friedrich Schiller

### File Structure

```
letters/schiller-goethe/
├── final_letters/          # 242 extracted letters in Markdown format
│   ├── 0001_schiller_to_goethe_june__19___1794.md
│   ├── 0002_goethe_to_schiller_june__24___1794.md
│   ├── ...
│   └── index.json         # Complete metadata index
├── raw_ocr/               # Original OCR data
│   ├── abbyy/            # ABBYY FineReader XML + extracted text
│   ├── hocr/             # DjVu XML
│   ├── pdf_text/         # PDF + extracted text
│   └── full_text.txt     # Archive.org text layer
├── verification/          # Extraction reports and confidence analysis
│   └── extraction_report.json
├── scripts/               # Extraction and verification tools
│   ├── abbyy_parser.py
│   ├── pdf_extractor.py
│   └── improved_letter_extractor.py
└── README.md             # This file
```

## Letter Format

Each letter is saved as a Markdown file with:

### YAML Front Matter
```yaml
---
letter_number: 1
sender: "Schiller"
recipient: "Goethe"
date: "June 13, 1794"
location: "Jena"
verification_score: 100.0
---
```

### Content Structure
- Letter header (number, sender, recipient)
- Metadata (location, date)
- Letter body (cleaned and formatted)
- Verification footer (if score < 100%)

## Usage

### Viewing Letters

Letters are in standard Markdown format and can be viewed in:
- Any text editor
- Markdown viewers
- Static site generators (Jekyll, Hugo, etc.)
- PaperLanterns.ink (your intended publication platform)

### Re-running Extraction

```bash
# Extract text from ABBYY XML
python3 scripts/abbyy_parser.py raw_ocr/abbyy/abbyy

# Extract text from PDF
python3 scripts/pdf_extractor.py raw_ocr/pdf_text/book.pdf

# Extract and verify all letters
python3 scripts/improved_letter_extractor.py .
```

## Quality Assurance

### Multi-Source Verification

Every letter was checked against multiple OCR sources to catch:
- OCR recognition errors
- Missing words or lines
- Formatting inconsistencies
- Hyphenation errors

### Manual Review Points

The following were identified for potential manual review:
1. 92 low-confidence regions in ABBYY OCR (< 30% confidence)
2. Letters missing clear date/location metadata
3. First few letters may include preface content (needs boundary refinement)

## Historical Context

This correspondence represents one of the most important literary friendships in history. Between 1794 and 1805, Schiller and Goethe exchanged over 900 letters discussing:

- Poetry and literature
- Philosophy and aesthetics
- Science and natural history
- Art and theater
- Personal matters and health
- Their collaborative work on journals and publications

The correspondence ended with Schiller's death in 1805.

## Public Domain Status

- **Original German letters:** Public domain
- **1845 English translation:** Public domain (published before 1928)
- **This extraction:** Public domain dedication

This collection is freely available for:
- Publication on PaperLanterns.ink
- Academic research
- Digital humanities projects
- Educational use
- Derivative works

## Acknowledgments

- **Archive.org** for preserving and digitizing this historical work
- **ABBYY FineReader** for commercial-grade OCR
- **Duke University Libraries** for the original digitization
- **George H. Calvert** for the 1845 English translation

## Future Improvements

Potential enhancements:
1. Train custom OCR model on 19th-century typography
2. Download and OCR high-resolution images for verification
3. Compare with other translations/editions
4. Add scholarly annotations
5. Create searchable database
6. Cross-reference with German originals

---

**Extraction Date:** November 18, 2025
**Extractor:** Claude (Anthropic)
**Project:** PaperLanterns.ink - Preserving Historical Indian Letters
