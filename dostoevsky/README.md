# Dostoevsky Letters Archive

A digital archive and website showcasing **88 letters** from Fyodor Dostoevsky to his family and friends (1838-1880).

## Features

- ✅ **88 letters extracted** from public domain sources
- ✅ **Clean markdown format** with metadata
- ✅ **Beautiful static website** for browsing and reading
- ✅ **Footnotes preserved** for historical context
- ✅ **Editing tools** for improving OCR quality
- ✅ **Multiple extraction strategies** documented
- ✅ **Public domain** - all content freely usable

## Quick Start

### View the Website

```bash
cd website
python3 -m http.server 8000
# Open http://localhost:8000
```

### Browse Letters

All letters are in `letters_markdown/` as individual markdown files:

```bash
ls letters_markdown/
# 001_his_Father.md
# 003_his_Brother_Michael.md
# ... etc
```

### Edit and Improve

```bash
# Fix OCR errors
python3 tools/fix_ocr_errors.py letters_markdown/*.md --fix-all --backup

# Rebuild website after editing
python3 tools/rebuild_json.py

# Refresh browser to see changes
```

## Project Structure

```
dostoevsky/
├── README.md                      # This file
├── EDITING_GUIDE.md               # How to edit and improve letters
├── EXTRACTION_STRATEGIES.md       # 7 strategies for text extraction
├── EXPERT_IMPLEMENTATION_PLAN.md  # Professional archiving approach
│
├── Source Materials (Internet Archive)
│   ├── letters_1917.epub          # Main source (77 letters)
│   ├── letters_1917_raw.txt       # OCR text
│   ├── letters_1923.epub          # Alternative edition
│   └── letters_1923_raw.txt       # OCR text
│
├── Extraction Scripts
│   ├── parse_letters_simple.py    # Main extraction script (WORKING)
│   ├── extract_letters.py         # EPUB-based extractor
│   ├── extract_from_pages.py      # Page-by-page extractor
│   └── inspect_epub.py            # EPUB structure analyzer
│
├── Output
│   ├── letters_markdown/          # 88 individual markdown files ⭐
│   ├── letters_final.json         # JSON with all letters
│   └── full_text_combined.txt     # All pages concatenated
│
├── Website (Static HTML/CSS/JS)
│   ├── index.html                 # Letter list page
│   ├── letter.html                # Individual letter view
│   ├── styles.css                 # Beautiful styling
│   ├── app.js                     # Main app logic
│   ├── letter.js                  # Letter display logic
│   └── letters.json               # Data file
│
└── Editing Tools
    ├── fix_ocr_errors.py          # Fix common OCR mistakes
    ├── rebuild_json.py            # Regenerate JSON from markdown
    └── (more tools can be added)
```

## Data Sources

### Primary Source (1917 Edition)
- **Title**: Letters of Fyodor Michailovitch Dostoevsky to his Family and Friends
- **Translator**: Ethel Colburn Mayne
- **Publisher**: Chatto & Windus, London
- **Year**: 1917
- **Letters**: 77 letters + recollections
- **Internet Archive**: https://archive.org/details/lettersoffyodorm00dostiala
- **Quality**: 98% OCR confidence

### Secondary Source (1923 Edition)
- **Title**: Dostoevsky: Letters and Reminiscences
- **Translators**: S. S. Koteliansky and J. Middleton Murry
- **Year**: 1923
- **Has**: Footnotes and reminiscences by his wife
- **Internet Archive**: https://archive.org/details/dostoevskyletter00dostuoft
- **Quality**: 96% OCR confidence

## Extraction Process

### What Worked: Simple Plain Text Parser

After testing 7 strategies (see `EXTRACTION_STRATEGIES.md`), the successful approach was:

1. **Downloaded** plain text OCR from Internet Archive (`.txt` files)
2. **Parsed** using regex patterns to find letter boundaries
3. **Extracted** metadata (recipient, date) from headers
4. **Separated** footnotes from body text
5. **Generated** markdown files with YAML frontmatter

```bash
python3 parse_letters_simple.py letters_1917_raw.txt \
    --output-md letters_markdown \
    --output-json letters_final.json
```

**Results**:
- ✅ 88 letters extracted
- ✅ 86 with recipients identified
- ✅ 28 with dates extracted
- ✅ 80 with footnotes preserved

## Editing Workflow

### 1. Fix OCR Errors

```bash
# Preview changes
python3 tools/fix_ocr_errors.py letters_markdown/*.md --fix-all --dry-run

# Apply fixes (with backup)
python3 tools/fix_ocr_errors.py letters_markdown/*.md --fix-all --backup
```

Common issues fixed:
- Double spaces ("May  10" → "May 10")
- Character errors (rn → m, cl → d, vv → w)
- Punctuation („ → ")

### 2. Manual Editing

Edit any letter directly:

```bash
nano letters_markdown/001_his_Father.md
# or
code letters_markdown/001_his_Father.md
```

Fix:
- Incorrect recipients
- Missing dates
- Broken paragraphs
- Missing footnotes

### 3. Rebuild Website

```bash
python3 tools/rebuild_json.py
# Automatically updates website/letters.json
```

### 4. Preview

Refresh your browser at http://localhost:8000

## Statistics

- **Total Letters**: 88
- **Date Range**: 1838-1880 (42 years)
- **Primary Recipients**:
  - His Brother Michael: ~40 letters
  - Family members: ~20 letters
  - Literary friends: ~15 letters
  - Others: ~13 letters

- **Notable Letters**:
  - Letter 20: Written on day of death sentence (Dec 22, 1849)
  - Multiple letters from Siberian exile
  - Letters discussing his major works

## Quality Levels

Current state: **Level 1-2**

- ✅ Level 1: All letters extracted, basic metadata
- 🔄 Level 2: Fixed double spaces, common OCR errors
- ⏳ Level 3: Cross-validated, verified dates/recipients
- ⏳ Level 4: All footnotes, perfect formatting, proofread

## TODO / Future Improvements

- [ ] Cross-validate with 1923 edition
- [ ] Fix all recipient metadata
- [ ] Extract more dates
- [ ] Verify all footnotes
- [ ] Add letter summaries
- [ ] Add historical context
- [ ] Create chronological view
- [ ] Add search by topic
- [ ] Add translations comparison

## Technical Stack

- **Extraction**: Python 3 (re, json, pathlib)
- **Website**: Vanilla HTML/CSS/JavaScript
- **Data Format**: Markdown + YAML frontmatter, JSON
- **Hosting**: Static files (can deploy anywhere)

## How to Contribute

1. **Improve OCR**: Edit markdown files to fix errors
2. **Add Context**: Enhance footnotes with historical info
3. **Verify Metadata**: Check dates and recipients
4. **Cross-Reference**: Compare with other editions
5. **Proofread**: Read and correct important letters

See `EDITING_GUIDE.md` for detailed instructions.

## License & Copyright

- **Letters**: Public Domain (author died 1881, >70 years ago)
- **Translation**: Public Domain (published 1917, >95 years ago)
- **This Archive**: CC0 / Public Domain Dedication

Feel free to use, modify, and distribute this archive for any purpose.

## Credits

- **Author**: Fyodor Dostoevsky (1821-1881)
- **Translator**: Ethel Colburn Mayne (1917 edition)
- **Source**: Internet Archive
- **Digital Archive**: Created 2025
- **Tools**: Python, beautiful-soup, ebooklib, ftfy

## Links

- **Internet Archive (1917)**: https://archive.org/details/lettersoffyodorm00dostiala
- **Internet Archive (1923)**: https://archive.org/details/dostoevskyletter00dostuoft
- **Wikipedia**: https://en.wikipedia.org/wiki/List_of_letters_from_Fyodor_Dostoevsky
- **Dostoevsky on Wikipedia**: https://en.wikipedia.org/wiki/Fyodor_Dostoevsky

---

**"The Paradise-bird of poetry will never, never visit me again"**
— Dostoevsky, Letter to his Brother, October 31, 1838
