# Text Extraction Strategies for Dostoevsky Letters

## Goal
Extract high-quality, error-free, readable text from Dostoevsky's letters for a static showcase website, including all footnotes wherever possible.

## Available Sources

### Source 1: 1923 Collection (Koteliansky & Murry translation)
- **URL**: https://archive.org/details/dostoevskyletter00dostuoft
- **Content**: Letters + Reminiscences by his wife
- **Formats**: TXT (420KB), EPUB (2.8MB), PDF
- **OCR Quality**: 96% confidence
- **Footnotes**: YES (confirmed present)
- **Total Pages**: 314

### Source 2: 1917 Collection (Ethel Colburn Mayne translation)
- **URL**: https://archive.org/details/lettersoffyodorm00dostiala
- **Content**: 77 letters + Recollections
- **Formats**: TXT (665KB), EPUB (5.7MB), PDF
- **OCR Quality**: 98% confidence
- **More comprehensive**: YES (77 letters vs fewer in 1923)
- **Total Pages**: 384

---

## Strategy 1: Direct EPUB Parsing (CLEANEST)
**Approach**: EPUBs are structured HTML/XHTML - parse them programmatically

### Advantages
- ✅ Better formatting preservation than raw OCR
- ✅ Chapter/section structure already marked up
- ✅ Footnotes often properly tagged with semantic HTML
- ✅ Less OCR noise than plain text
- ✅ Can extract metadata (dates, recipients)

### Implementation
```python
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def extract_from_epub(epub_path):
    book = epub.read_epub(epub_path)
    letters = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')

        # Extract letter metadata
        # Extract body text
        # Extract footnotes (usually in <div class="footnote"> or <aside>)
        # Parse dates and recipients

    return letters
```

### Challenges
- Need to handle varying HTML structures between the two editions
- Footnotes might be at end of chapter vs inline

### Quality Score: ⭐⭐⭐⭐⭐

---

## Strategy 2: Multi-Source Cross-Validation
**Approach**: Compare text from both 1917 and 1923 editions to detect and fix OCR errors

### Advantages
- ✅ Two independent OCR sources (98% + 96% confidence)
- ✅ Different translators might handle difficult passages differently
- ✅ Errors unlikely to occur in same place in both
- ✅ Can choose cleaner version for each section

### Implementation
```python
from difflib import SequenceMatcher

def cross_validate_text(text1_1917, text2_1923):
    # Find common letters (both collections have them)
    # Compare text character-by-character
    # Where they differ, flag for manual review
    # Auto-fix obvious OCR errors (rn vs m, cl vs d, etc.)

    common_ocr_errors = {
        'rn': 'm',
        'cl': 'd',
        'vv': 'w',
        '1': 'l',  # in words
    }

    return validated_text
```

### Challenges
- Different translations might legitimately differ
- Need to align corresponding letters first
- Time-intensive

### Quality Score: ⭐⭐⭐⭐⭐

---

## Strategy 3: PDF Text Extraction with Layout Analysis
**Approach**: Use PDF libraries that preserve layout, then intelligently parse

### Advantages
- ✅ Can detect footnote positioning (bottom of page, smaller font)
- ✅ Can distinguish page numbers from body text
- ✅ Can detect letter headers/metadata
- ✅ Better than OCR plain text

### Implementation
```python
import pdfplumber
import re

def extract_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract text with layout info
            text = page.extract_text(layout=True)

            # Detect footnotes (smaller y-position, indented)
            # Detect page numbers (corners, specific positions)
            # Detect letter headers (dates, recipients)

            # Use regex to clean up
            cleaned = clean_ocr_artifacts(text)

    return letters_with_metadata
```

### Challenges
- PDFs can have inconsistent layouts
- Footnotes spanning multiple pages
- Need good heuristics for layout detection

### Quality Score: ⭐⭐⭐⭐

---

## Strategy 4: OCR Correction with Language Model
**Approach**: Use the existing text but run it through automated correction

### Advantages
- ✅ Can fix obvious OCR errors programmatically
- ✅ Works with existing TXT files (fastest to implement)
- ✅ Can use contextual spelling correction
- ✅ Leverage both sources for better accuracy

### Implementation
```python
import language_tool_python
from textblob import TextBlob

def correct_ocr_text(raw_text):
    # Common OCR error patterns
    fixes = {
        r'\brn\b': 'm',  # word boundary rn -> m
        r'\bcl\b': 'd',
        r'\.\.+': '.',   # multiple periods
        r'\s+': ' ',     # multiple spaces
    }

    for pattern, replacement in fixes.items():
        text = re.sub(pattern, replacement, text)

    # Use language tool for grammar/spelling
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)

    return corrected
```

### Challenges
- Might "fix" legitimate 19th century spellings/grammar
- Can't fix all OCR errors automatically
- May need manual review

### Quality Score: ⭐⭐⭐⭐

---

## Strategy 5: Hybrid Manual Curation + Automation
**Approach**: Automated extraction + strategic manual fixes for critical sections

### Advantages
- ✅ Best possible quality for showcase website
- ✅ Can verify important letters manually
- ✅ Fix footnotes that are critical to understanding
- ✅ Reasonable time investment for 77 letters

### Implementation
```python
def hybrid_extraction():
    # 1. Auto-extract all letters using EPUB parser (Strategy 1)
    auto_letters = extract_from_epub('letters_1917.epub')

    # 2. Flag quality issues
    for letter in auto_letters:
        letter['quality_score'] = assess_quality(letter)
        letter['needs_review'] = letter['quality_score'] < 0.9

    # 3. Cross-validate flagged letters with 1923 edition
    # 4. Generate review checklist
    # 5. Manual review only for flagged sections

    return curated_letters
```

### Challenges
- Requires human time
- Subjective quality assessment

### Quality Score: ⭐⭐⭐⭐⭐

---

## Strategy 6: Internet Archive OCR API
**Approach**: Use Internet Archive's own cleaned up text versions

### Advantages
- ✅ IA often has multiple OCR passes
- ✅ Community corrections sometimes available
- ✅ HOCR format includes confidence scores
- ✅ Can download pre-processed versions

### Implementation
```python
def download_ia_cleaned_text(identifier):
    # Use Internet Archive API
    base_url = f'https://archive.org/download/{identifier}'

    # Try multiple formats in order of cleanliness:
    # 1. _djvu.txt (DjVu OCR - often cleanest)
    # 2. _hocr.html (HTML with OCR confidence)
    # 3. .txt (plain text)

    return best_available_text
```

### Challenges
- Limited control over quality
- Still has OCR errors

### Quality Score: ⭐⭐⭐

---

## Strategy 7: Segment-Based Quality Selection
**Approach**: Split into segments, choose best source for each segment

### Advantages
- ✅ Gets best of both 1917 and 1923 editions
- ✅ Can mix and match translations if needed
- ✅ Automated comparison per letter/paragraph
- ✅ Maximizes use of available data

### Implementation
```python
def segment_and_select(source1, source2):
    # Split both sources into letters
    letters1 = split_into_letters(source1)
    letters2 = split_into_letters(source2)

    # For each letter, compare quality
    best_letters = []
    for l1, l2 in zip(letters1, letters2):
        score1 = quality_metric(l1)
        score2 = quality_metric(l2)

        best = l1 if score1 > score2 else l2
        best_letters.append(best)

    return best_letters

def quality_metric(text):
    # Count OCR artifacts
    # Check for complete sentences
    # Verify proper capitalization
    # Check footnote integrity
    return score
```

### Challenges
- Complex alignment between different translations
- May lose consistency if mixing translations

### Quality Score: ⭐⭐⭐⭐

---

## Recommended Approach: Combined Strategy

### Phase 1: Automated Extraction (Strategy 1 + 7)
1. Parse EPUB from 1917 edition (more comprehensive - 77 letters)
2. Parse EPUB from 1923 edition (has good footnotes)
3. For letters in both editions, compare and select best version

### Phase 2: Cross-Validation (Strategy 2)
1. Compare overlapping letters between editions
2. Flag discrepancies for review
3. Auto-fix common OCR patterns

### Phase 3: Quality Assurance (Strategy 4 + 5)
1. Run OCR correction on final text
2. Manual review of:
   - First 3 letters (establish baseline)
   - Letters with footnotes (critical for context)
   - Letters with quality score < 90%
3. Spot-check random sample of 10%

### Expected Outcome
- **Quality**: 98%+ accuracy
- **Footnotes**: Preserved
- **Time**: 2-4 hours for automation + 2-3 hours manual review
- **Coverage**: All 77 letters from 1917 edition + extras from 1923

---

## Testing Plan

### Test Sample
Extract **3 letters** using each strategy to compare:
1. Letter 1 (First letter - establish baseline)
2. Letter with complex footnotes (test footnote extraction)
3. Letter with known OCR issues (test error correction)

### Metrics
- OCR error rate (manual count of errors per 1000 words)
- Footnote completeness (% of footnotes captured)
- Extraction time (automated vs manual components)
- Formatting quality (readability for website)

---

## Implementation Priority

1. **Start with Strategy 1** (EPUB parsing) - likely cleanest
2. **Add Strategy 7** (segment selection) - get best of both
3. **Apply Strategy 4** (OCR correction) - automated cleanup
4. **Use Strategy 5** (hybrid manual) - final polish for critical letters

This gives us 98%+ quality with reasonable time investment.
