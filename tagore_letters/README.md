# Rabindranath Tagore: Letters to a Friend

**Extracted and cleaned historical letters from Archive.org**

## About

This collection contains 48 letters written by Rabindranath Tagore to C. F. Andrews between 1913-1923, extracted from the book "Letters to a Friend" (1926).

### Source

- **Book**: Rabindranath Tagore: Letters to a Friend
- **Editor**: C. F. Andrews
- **Published**: 1926 by George Allen & Unwin Ltd, London
- **Archive**: https://archive.org/details/in.ernet.dli.2015.52214
- **Total Pages**: 211
- **OCR Quality**: Good (ABBYY FineReader 11.0 at 600 PPI)

## Extraction Process

### Multi-Source Verification

We used multiple extraction methods to ensure accuracy:

1. **DjVuTXT** - Plain text OCR layer (314KB)
2. **EPUB** - Formatted ebook version (126MB)
3. **Djvu XML** - Structured data with coordinates (3.1MB)
4. **Text PDF** - PDF with text layer (13MB)

### Extraction Pipeline

```
1. Download multiple formats from Archive.org
2. Extract text from DjVuTXT (primary source)
3. Clean OCR errors (100+ common patterns fixed)
4. Parse letter boundaries using date/location patterns
5. Remove page numbers, headers, and artifacts
6. Fix hyphenated line breaks
7. Generate markdown files with YAML frontmatter
8. Verify quality and fix remaining issues
```

### Scripts

- **`extract_letters_comprehensive.py`** - Main extraction script
- **`clean_and_verify.py`** - Post-processing and quality verification

## Collection Structure

### Individual Letters

All 48 letters are in `extracted_letters_complete/`:

```
letter_001_london_augu-16-1913.md
letter_002_calcutta_october-11-1913.md
letter_003_santiniketan_october-11-1913.md
...
letter_048_santiniketan_july-1923.md
```

Each letter includes:
- YAML frontmatter with metadata
- Clean, formatted letter content
- OCR errors corrected
- Page artifacts removed

### Combined File

**`tagore_letters_complete.md`** - All 48 letters in a single file for easy reading

### Example Letter Format

```markdown
---
title: "Letter from London"
author: "Rabindranath Tagore"
recipient: "C. F. Andrews"
date: "August 16th, 1913"
location: "London"
source: "Letters to a Friend (1926)"
letter_number: 1
---

# Letter 1

**London, August 16th, 1913**

I am so glad to know that you are now in Santiniketan...
```

## Letter Timeline

| Year | Count | Locations |
|------|-------|-----------|
| 1913 | 3 | London, Calcutta, Santiniketan |
| 1914 | 13 | Santiniketan, Ramgarh, Darjeeling, Calcutta, Agra, Allahabad |
| 1915 | 5 | Calcutta, Shileida, Santiniketan, Srinagar |
| 1916 | 2 | Shileida |
| 1917 | 2 | Santiniketan, Shileida |
| 1918 | 2 | Calcutta, Santiniketan |
| 1920 | 9 | Red Sea, London, Paris, Ardennes, Antwerp |
| 1921 | 10 | New York, Houston, Chicago, London, Strasbourg, Berlin |
| 1923 | 1 | Santiniketan |

**Total**: 48 letters across 11 years

## Known Issues

1. **Some letters may be partially merged** - Letters from the same location/month (e.g., multiple "Ramgarh, May 1914" letters) may have content mixed
2. **Minor OCR errors remain** - About 17 letters flagged with possible OCR patterns
3. **Date format variations** - Some dates have unusual OCR artifacts (e.g., "z2nd^" for "22nd")

## OCR Corrections Applied

Over 100+ common OCR errors were automatically fixed, including:

### Date Errors
- `i6i/z` → `16th`
- `iith^` → `11th`
- `$ihy` → `5th`
- `loth^` → `10th`
- And 40+ more patterns

### Text Errors
- `gerfni-nation` → `germination`
- `tlie` → `the`
- `mexely` → `merely`
- `stiuggle` → `struggle`
- `countiy` → `country`
- And 50+ more patterns

### Location Errors
- `Santimketan` → `Santiniketan`
- `Lomdon` → `London`
- And more

## Usage

### For Publishing

These letters are in the **public domain** (published 1926, copyright expired). They can be:

- Published on PaperLanterns.in
- Shared freely
- Used in research
- Republished in any format

### File Formats

All letters are in **Markdown** format with YAML frontmatter, making them:
- Easy to convert to HTML
- Compatible with static site generators (Jekyll, Hugo, 11ty)
- Readable as plain text
- Machine-parseable for analysis

## Historical Context

These letters document a crucial period in:

- **Indian Independence Movement** (references to Gandhi, South Africa)
- **World War I** (Tagore's premonitions in 1914 letters)
- **Bengal Renaissance** (cultural and spiritual awakening)
- **Santiniketan School** (Tagore's educational vision)

### Key Correspondents

- **Rabindranath Tagore** (1861-1941) - Nobel Prize-winning poet, writer, composer
- **C. F. Andrews** (1871-1940) - Anglican priest, close friend of Gandhi and Tagore

## Future Improvements

1. **Manual review** of merged letters
2. **Cross-verification** with physical book scans
3. **Additional OCR error correction**
4. **Add annotations** for historical context
5. **Extract more collections** from Archive.org

## Credits

- **Original Book**: C. F. Andrews (Editor), 1926
- **Digitization**: Digital Library of India
- **Archive**: Internet Archive (archive.org)
- **Extraction & Cleaning**: 2025-11-18

## License

The letters themselves are **public domain** (published 1926).

The extraction scripts and this README are provided for public use.

---

*"The time has come at last when I must leave England ; for I find that my work here in the West is getting the better of me."*
— Rabindranath Tagore, Letter 1, August 16, 1913
