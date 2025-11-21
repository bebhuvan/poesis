# Tagore Letters Extraction & Website Project

## Overview

This project extracts and showcases the letters of Rabindranath Tagore from a scanned PDF document ([Internet Archive source](https://archive.org/details/in.ernet.dli.2015.52214)).

The PDF presents significant challenges:
- **Image-based scanned pages** (not searchable text)
- **Inconsistent formatting** across pages
- **Missing dates** on many letters (e.g., SS Rhyndham correspondence)
- **Poor OCR quality** in original digitization

## Our Approach: Multi-Strategy Extraction with Verification

Instead of relying on a single extraction method, we implemented a **competitive multi-strategy framework** where different extraction approaches compete to find the best results.

### Extraction Strategies

1. **Roman Numeral Strategy**
   - Identifies letters by Roman numeral markers (I, II, III, IV, etc.)
   - Best for formally numbered sections

2. **Date Header Strategy**
   - Finds letters starting with date headers
   - Handles various date formats (Month DD, YYYY / DD Month YYYY)

3. **Chapter Break Strategy**
   - Uses structural breaks and chapter markers
   - Good for longer sections

4. **Hybrid Multi-Signal Strategy** ⭐
   - Combines all signals (Roman numerals, dates, page breaks, chapters)
   - Assigns confidence scores based on signal strength
   - Deduplicates boundaries intelligently
   - **Usually produces the best results**

### Verification Framework

We verify extraction quality using **7 independent methodologies**:

1. **Page Coverage Analysis**
   - Ensures all content pages are included in extracted letters
   - Identifies gaps in coverage

2. **Content Completeness Analysis**
   - Compares total words extracted vs. total words in OCR
   - Ensures we're not missing large sections

3. **Letter Structure Validation**
   - Checks for empty letters, very short letters, very long letters
   - Validates markers and boundaries

4. **Metadata Quality Assessment**
   - Measures date extraction success rate
   - Checks recipient extraction
   - Identifies metadata patterns

5. **Content Quality Assessment**
   - Detects common OCR errors (unusual characters, malformed words)
   - Flags letters with many errors for review

6. **Sequential Integrity Check**
   - Looks for gaps between consecutive letters
   - Detects overlapping letter boundaries

7. **Statistical Analysis**
   - Analyzes word count distributions
   - Checks page span distributions
   - Identifies outliers

## Project Structure

```
tagore_letters/
├── tagore_letters.pdf                  # Source PDF (6.1MB)
├── full_ocr_extraction.py              # OCR extraction (all 210 pages)
├── multi_strategy_extractor.py         # 4 competing extraction strategies
├── verification_framework.py           # 7 verification methodologies
├── website_generator.py                # Static website builder
│
├── tagore_full_ocr.json                # OCR text from all pages
├── strategy_comparison.json            # Results from all strategies
├── verification_report.json            # Comprehensive quality report
│
└── tagore_website/                     # Generated static website
    ├── index.html                      # Homepage with letter listing
    ├── about.html                      # About page
    ├── css/style.css                   # Beautiful typography
    └── letters/                        # Individual letter pages
        ├── letter_001.html
        ├── letter_002.html
        └── ...
```

## Usage

### 1. Run Full OCR Extraction

```bash
python full_ocr_extraction.py
```

- Processes all 210 pages
- Takes ~30-45 minutes
- Saves progress every 10 pages
- Output: `tagore_full_ocr.json`

### 2. Run Multi-Strategy Extraction

```bash
python multi_strategy_extractor.py
```

- Runs all 4 extraction strategies
- Compares results
- Identifies best strategy
- Output: `strategy_comparison.json`

### 3. Run Verification Framework

```bash
python verification_framework.py
```

- Runs all 7 verification checks
- Generates comprehensive quality report
- Output: `verification_report.json`

### 4. Generate Static Website

```bash
python website_generator.py
```

- Creates beautiful static website
- Elegant typography (Crimson Text font)
- Responsive design
- Output: `tagore_website/` directory

Then open `tagore_website/index.html` in your browser!

## Quality Assurance

Our multi-layered approach ensures:

✅ **Completeness**: All letters are extracted
✅ **Accuracy**: Multiple verification checks catch errors
✅ **Traceability**: Every letter includes source page numbers
✅ **Iterative Improvement**: Compare strategies, pick best, repeat

### Iterative Improvement Process

1. **Extract** with multiple strategies
2. **Compare** results quantitatively
3. **Verify** quality with 7 methodologies
4. **Identify** gaps or errors
5. **Refine** strategies based on findings
6. **Repeat** until quality target reached

## Website Features

The generated static website includes:

- 📚 **Letter Listing** - Beautiful grid layout with previews
- 📖 **Individual Letter Pages** - Full text with metadata
- 🎨 **Elegant Design** - Serif fonts, warm colors, clean layout
- 📱 **Responsive** - Works on mobile, tablet, desktop
- ⚡ **Fast** - Static HTML/CSS, no JavaScript needed
- 🔍 **SEO-Friendly** - Semantic HTML, proper headings

## Technical Details

### OCR Configuration

```python
tesseract --oem 3 --psm 6
```

- OEM 3: Default LSTM neural net mode
- PSM 6: Uniform block of text
- DPI: 300 (good balance of quality/speed)

### Dependencies

```bash
pip install PyPDF2 pdf2image pytesseract pdfplumber
apt-get install tesseract-ocr poppler-utils
```

## Challenges Overcome

1. **Image-based PDF**: Used Tesseract OCR with pdf2image
2. **Inconsistent formatting**: Multiple extraction strategies
3. **Missing dates**: Hybrid approach with multiple signals
4. **Poor quality scans**: Higher DPI, careful OCR configuration
5. **Verification**: 7 independent checks ensure quality

## Future Improvements

- [ ] Manual review of low-confidence letters
- [ ] OCR error correction using context
- [ ] Better date normalization
- [ ] Recipient name extraction improvements
- [ ] Full-text search on website
- [ ] Timeline visualization of letters
- [ ] Export to EPUB/PDF formats

## Credits

**Source**: "Rabindra Nath Tagore: Letters To A Friend"
- Edited by C. F. Andrews
- Published 1926 by George Allen & Unwin Ltd.
- Digitized by Digital Library of India
- Available at Internet Archive

**Extraction & Website**: Created with love for preserving Tagore's beautiful letters for the world to read.

## License

The letters themselves are in the **public domain** (Tagore died in 1941).

The extraction code and website are provided as-is for educational and preservation purposes.

---

*"Let me not pray to be sheltered from dangers, but to be fearless in facing them."* - Rabindranath Tagore
