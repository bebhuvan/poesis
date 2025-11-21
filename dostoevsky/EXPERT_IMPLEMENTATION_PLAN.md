# Expert Digital Text Preservation & Extraction Plan
## Dostoevsky Letters Archive Project

### Archivist's Assessment

From a digital preservation perspective, we have:
- **Primary Source**: Internet Archive scans (2 editions, different translations)
- **OCR Quality**: 96-98% confidence (IA's ABBYY FineReader)
- **Formats Available**: DjVu, PDF, EPUB, plain TXT, hOCR
- **Goal**: Create authoritative digital edition for web presentation

---

## Professional OCR & Text Extraction Toolkit

### Core Tools & Libraries

#### 1. OCR Quality Assessment
```python
# OCR-D Framework - German DFG project for OCR quality
# pip install ocrd-tesserocr ocrd-cis

from ocrd import Processor
from ocrd_cis import ocr_quality_assessment
```

#### 2. Post-OCR Correction Tools

**CorrectOCR** (Aarhus University)
```bash
# State-of-the-art OCR correction
pip install correctocr
```

**OCRevalUAtion** (PRImA Research Lab)
```bash
# Compare OCR outputs, measure accuracy
git clone https://github.com/impactcentre/ocrevalUAtion
```

**dinglehopper** (OCR quality comparison)
```bash
pip install dinglehopper
# Compares OCR with ground truth, generates detailed error reports
```

#### 3. Text Extraction Libraries

```python
# EPUB: ebooklib (industry standard)
pip install ebooklib beautifulsoup4 lxml

# PDF: Multiple extraction methods
pip install pdfplumber pymupdf pdfminer.six

# hOCR: Tesseract's structured OCR format
pip install hocr-tools

# Text processing
pip install ftfy  # Fix mojibake and encoding issues
pip install language-tool-python  # Grammar checking
pip install symspellpy  # Fast spell checking
```

---

## Strategy: Multi-Tiered Archival Extraction

### Tier 1: Extract from Best Available Structured Format (hOCR)

**Why hOCR?**
- Contains OCR confidence scores per word
- Preserves layout and formatting
- Machine-readable + human-readable
- Standard format for digital libraries

```python
#!/usr/bin/env python3
"""
hOCR-based extraction with confidence filtering
"""
from bs4 import BeautifulSoup
import statistics

def extract_from_hocr(hocr_file):
    """
    Parse hOCR, extract text with confidence scores.
    Filter out low-confidence words for review.
    """
    with open(hocr_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')

    letters = []
    current_letter = {
        'header': '',
        'body': [],
        'footnotes': [],
        'low_confidence_words': []
    }

    # hOCR structure: page > carea > paragraph > line > word
    for page in soup.find_all('div', class_='ocr_page'):
        for word in page.find_all('span', class_='ocrx_word'):
            # Extract confidence score
            title = word.get('title', '')
            confidence = parse_confidence(title)

            word_text = word.get_text()

            if confidence < 80:  # Flag for review
                current_letter['low_confidence_words'].append({
                    'word': word_text,
                    'confidence': confidence,
                    'context': get_context(word)
                })

    return letters

def parse_confidence(title_attr):
    """Extract x_wconf (word confidence) from hOCR title attribute"""
    import re
    match = re.search(r'x_wconf\s+(\d+)', title_attr)
    return int(match.group(1)) if match else 0
```

### Tier 2: PDF Text Extraction with Layout Awareness

```python
import pdfplumber
import re

def extract_with_layout_analysis(pdf_path):
    """
    Professional PDF extraction preserving structure.
    Distinguishes: headers, body, footnotes, page numbers
    """
    with pdfplumber.open(pdf_path) as pdf:
        letters = []

        for page in pdf.pages:
            # Get text with layout
            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3,
                keep_blank_chars=True
            )

            # Classify regions
            page_height = page.height
            header_threshold = page_height * 0.15  # Top 15%
            footer_threshold = page_height * 0.85  # Bottom 15%

            body_text = []
            footnotes = []
            headers = []

            for word in words:
                y_pos = word['top']
                text = word['text']
                fontsize = word.get('size', 12)

                # Classify by position and font size
                if y_pos < header_threshold:
                    headers.append(text)
                elif y_pos > footer_threshold and fontsize < 10:
                    footnotes.append(text)
                else:
                    body_text.append(text)

            # Reconstruct with structure
            letter = {
                'header': ' '.join(headers),
                'body': ' '.join(body_text),
                'footnotes': extract_footnote_structure(footnotes)
            }

            letters.append(letter)

    return letters

def extract_footnote_structure(footnote_words):
    """
    Parse footnotes: detect numbers, associate text
    Common patterns:
    - ¹ Text of footnote
    - [1] Text of footnote
    - 1. Text of footnote
    """
    footnotes = {}
    current_num = None
    current_text = []

    footnote_pattern = re.compile(r'^[¹²³⁴⁵⁶⁷⁸⁹⁰\[\(]?(\d+)[\]\)]?\.?\s*(.*)')

    for word in footnote_words:
        match = footnote_pattern.match(word)
        if match:
            # Save previous footnote
            if current_num:
                footnotes[current_num] = ' '.join(current_text)
            # Start new footnote
            current_num = match.group(1)
            current_text = [match.group(2)] if match.group(2) else []
        else:
            if current_num:
                current_text.append(word)

    # Save last footnote
    if current_num:
        footnotes[current_num] = ' '.join(current_text)

    return footnotes
```

### Tier 3: EPUB Extraction (Cleanest for Modern Web Display)

```python
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

def extract_from_epub_professional(epub_path):
    """
    Parse EPUB with semantic structure preservation.
    Handles: chapters, footnotes, emphasized text, dates
    """
    book = epub.read_epub(epub_path)
    letters = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')

        # Extract letter structure
        letter = {}

        # Find letter header (recipient, date)
        # Common patterns in 19th c. letters
        header = soup.find(['h1', 'h2', 'h3', 'div'], class_=re.compile('header|title'))
        if header:
            letter['header'] = extract_letter_metadata(header.get_text())

        # Extract body paragraphs
        paragraphs = soup.find_all('p')
        letter['paragraphs'] = []

        for p in paragraphs:
            # Check if footnote reference
            footnote_refs = p.find_all(['sup', 'a'], class_=re.compile('footnote|note'))

            para_text = p.get_text()
            para_footnotes = [ref.get_text() for ref in footnote_refs]

            letter['paragraphs'].append({
                'text': para_text,
                'footnote_refs': para_footnotes
            })

        # Extract actual footnotes
        letter['footnotes'] = {}

        # Footnotes can be in: <aside>, <div class="footnote">, <section class="notes">
        footnote_sections = soup.find_all(['aside', 'div', 'section'],
                                         class_=re.compile('footnote|endnote|note'))

        for section in footnote_sections:
            for note in section.find_all(['p', 'li']):
                note_num, note_text = parse_footnote(note.get_text())
                if note_num:
                    letter['footnotes'][note_num] = note_text

        letters.append(letter)

    return letters

def extract_letter_metadata(header_text):
    """
    Parse letter headers for structured metadata.

    Common formats:
    - "To Michael Dostoevsky, January 1, 1840"
    - "LETTER TO HIS BROTHER\nJanuary 1, 1840"
    - "38. To his Sister Vera: January 1, 1868"
    """
    metadata = {
        'recipient': None,
        'date': None,
        'location': None
    }

    # Extract date (various formats)
    date_patterns = [
        r'([A-Z][a-z]+ \d{1,2}(?:, \d{4})?)',  # January 1, 1840
        r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',     # 1 January 1840
        r'([A-Z][a-z]+, \d{4})',                 # January, 1840
    ]

    for pattern in date_patterns:
        match = re.search(pattern, header_text)
        if match:
            metadata['date'] = match.group(1)
            break

    # Extract recipient
    to_pattern = r'[Tt]o\s+([A-Z][^:,\n]+)'
    match = re.search(to_pattern, header_text)
    if match:
        metadata['recipient'] = match.group(1).strip()

    return metadata

def parse_footnote(text):
    """
    Extract footnote number and text.
    Returns: (number, text) or (None, None)
    """
    # Match patterns like: "1 Text here" or "1. Text here" or "[1] Text here"
    patterns = [
        r'^[¹²³⁴⁵⁶⁷⁸⁹⁰]+\s+(.*)',  # Superscript numbers
        r'^\[(\d+)\]\s+(.*)',        # [1] format
        r'^(\d+)\.\s+(.*)',          # 1. format
        r'^(\d+)\s+(.*)',            # 1 format
    ]

    for pattern in patterns:
        match = re.match(pattern, text.strip())
        if match:
            if len(match.groups()) == 2:
                return match.group(1), match.group(2)
            else:
                return '1', match.group(1)  # Unnumbered footnote

    return None, None
```

### Tier 4: Cross-Source Validation & Error Correction

```python
from difflib import SequenceMatcher, unified_diff
import ftfy

def cross_validate_editions(edition1_letters, edition2_letters):
    """
    Compare two editions, create authoritative text.

    Process:
    1. Align corresponding letters
    2. Compare word-by-word
    3. Flag discrepancies
    4. Apply OCR error correction
    5. Generate review report
    """
    validated = []

    for let1, let2 in align_letters(edition1_letters, edition2_letters):
        if not let2:  # Letter only in edition 1
            validated.append(let1)
            continue

        # Compare texts
        text1 = let1['body']
        text2 = let2['body']

        # Fix encoding issues first
        text1 = ftfy.fix_text(text1)
        text2 = ftfy.fix_text(text2)

        # Word-level comparison
        words1 = text1.split()
        words2 = text2.split()

        validated_words = []
        issues = []

        for i, (w1, w2) in enumerate(zip(words1, words2)):
            if w1 == w2:
                validated_words.append(w1)
            else:
                # Different words - decide which is correct
                choice, reason = choose_better_word(w1, w2, i, words1, words2)
                validated_words.append(choice)

                issues.append({
                    'position': i,
                    'edition1': w1,
                    'edition2': w2,
                    'chosen': choice,
                    'reason': reason
                })

        validated_letter = let1.copy()
        validated_letter['body'] = ' '.join(validated_words)
        validated_letter['validation_issues'] = issues
        validated_letter['sources'] = ['edition1', 'edition2']

        validated.append(validated_letter)

    return validated

def choose_better_word(word1, word2, position, context1, context2):
    """
    Decide which word is more likely correct.

    Criteria:
    1. Dictionary check (is it a valid English word?)
    2. OCR error patterns (rn vs m, cl vs d)
    3. Context (does it make sense in sentence?)
    4. Length (OCR often drops/adds chars)
    """
    import enchant
    en_dict = enchant.Dict("en_US")

    # Check if valid English words
    valid1 = en_dict.check(word1)
    valid2 = en_dict.check(word2)

    if valid1 and not valid2:
        return word1, "word1 in dictionary, word2 not"
    elif valid2 and not valid1:
        return word2, "word2 in dictionary, word1 not"

    # Both valid or both invalid - check OCR patterns
    ocr_score1 = count_ocr_artifacts(word1)
    ocr_score2 = count_ocr_artifacts(word2)

    if ocr_score1 < ocr_score2:
        return word1, "fewer OCR artifacts"
    elif ocr_score2 < ocr_score1:
        return word2, "fewer OCR artifacts"

    # Similar quality - use longer/more complete
    if len(word1) > len(word2):
        return word1, "more complete"
    else:
        return word2, "more complete"

def count_ocr_artifacts(word):
    """Count common OCR error patterns"""
    score = 0

    # Common OCR errors
    if 'rn' in word.lower():
        score += 1  # Might be 'm'
    if 'cl' in word.lower():
        score += 1  # Might be 'd'
    if 'vv' in word.lower():
        score += 1  # Might be 'w'
    if re.search(r'\d', word):
        score += 1  # Numbers in words (like 1 for l)

    return score

def align_letters(letters1, letters2):
    """
    Align corresponding letters from two editions.

    Uses:
    1. Date matching
    2. Recipient matching
    3. First sentence matching
    4. Fuzzy matching
    """
    aligned = []

    for let1 in letters1:
        best_match = None
        best_score = 0

        for let2 in letters2:
            score = 0

            # Match by date
            if let1.get('date') == let2.get('date'):
                score += 5

            # Match by recipient
            if let1.get('recipient') == let2.get('recipient'):
                score += 3

            # Match by content similarity
            text1 = let1.get('body', '')[:200]  # First 200 chars
            text2 = let2.get('body', '')[:200]
            similarity = SequenceMatcher(None, text1, text2).ratio()
            score += similarity * 10

            if score > best_score:
                best_score = score
                best_match = let2

        aligned.append((let1, best_match if best_score > 5 else None))

    return aligned
```

### Tier 5: Quality Assessment & Reporting

```python
def generate_quality_report(letters):
    """
    Generate detailed quality report for archival purposes.

    Metrics:
    - Completeness (all expected letters present)
    - OCR confidence scores
    - Footnote coverage
    - Validation issue count
    - Manual review requirements
    """
    report = {
        'total_letters': len(letters),
        'letters_with_footnotes': 0,
        'avg_confidence': 0,
        'needs_manual_review': [],
        'extraction_date': datetime.now().isoformat(),
        'sources': []
    }

    confidence_scores = []

    for i, letter in enumerate(letters):
        # Check footnotes
        if letter.get('footnotes'):
            report['letters_with_footnotes'] += 1

        # Check validation issues
        issues = letter.get('validation_issues', [])
        if len(issues) > 10:  # More than 10 discrepancies
            report['needs_manual_review'].append({
                'letter_number': i + 1,
                'recipient': letter.get('recipient'),
                'date': letter.get('date'),
                'issue_count': len(issues)
            })

        # Aggregate confidence scores
        if 'confidence' in letter:
            confidence_scores.append(letter['confidence'])

    if confidence_scores:
        report['avg_confidence'] = statistics.mean(confidence_scores)

    return report
```

---

## Implementation Workflow

```bash
#!/bin/bash
# Professional extraction pipeline

# Step 1: Download all available formats
python extract_dostoevsky.py --download-all

# Step 2: Extract from each source
python extract_dostoevsky.py --extract-hocr letters_1917
python extract_dostoevsky.py --extract-epub letters_1917
python extract_dostoevsky.py --extract-epub letters_1923

# Step 3: Cross-validate
python extract_dostoevsky.py --cross-validate \
    --source1 letters_1917.json \
    --source2 letters_1923.json \
    --output validated_letters.json

# Step 4: Generate quality report
python extract_dostoevsky.py --quality-report \
    --input validated_letters.json \
    --output quality_report.html

# Step 5: Export for web
python extract_dostoevsky.py --export-web \
    --input validated_letters.json \
    --output-dir ./website/letters/
```

---

## Output Format (JSON-LD for Semantic Web)

```json
{
  "@context": "http://schema.org",
  "@type": "Letter",
  "identifier": "dostoevsky-letter-001",
  "author": {
    "@type": "Person",
    "name": "Fyodor Dostoevsky",
    "birthDate": "1821-11-11",
    "deathDate": "1881-02-09"
  },
  "recipient": "Michael Dostoevsky",
  "dateSent": "1840-01-01",
  "text": {
    "body": "Full letter text here...",
    "footnotes": {
      "1": "Footnote text...",
      "2": "Another footnote..."
    }
  },
  "inLanguage": "en",
  "translationOf": {
    "@type": "Letter",
    "inLanguage": "ru"
  },
  "translator": "Ethel Colburn Mayne",
  "publicationYear": 1917,
  "isPartOf": {
    "@type": "Book",
    "name": "Letters of Fyodor Michailovitch Dostoevsky to his Family and Friends"
  },
  "provider": {
    "@type": "Organization",
    "name": "Internet Archive",
    "url": "https://archive.org/details/lettersoffyodorm00dostiala"
  },
  "quality": {
    "ocrConfidence": 98,
    "validationIssues": 3,
    "manualReviewCompleted": true
  }
}
```

---

## Tools Required

```bash
# Install all dependencies
pip install \
    ebooklib \
    beautifulsoup4 \
    lxml \
    pdfplumber \
    pymupdf \
    ftfy \
    pyenchant \
    language-tool-python \
    requests \
    tqdm

# Optional: OCR quality tools
pip install dinglehopper correctocr
```

This professional approach ensures archival-quality extraction suitable for long-term digital preservation and scholarly use.
