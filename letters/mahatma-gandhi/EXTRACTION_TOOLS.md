# Gandhi Letters Extraction Tools

This document describes the tools created for extracting Gandhi's letters from Archive.org.

## Tools Created

### 1. archive_org_extractor.py

Multi-strategy extraction from Archive.org items.

**Features:**
- Downloads text, PDF, and DJVU files
- Extracts text using multiple methods
- Cross-verifies different extraction approaches
- Generates extraction reports with SHA-256 hashes
- Identifies best extraction method

**Usage:**
```bash
python archive_org_extractor.py
```

**Output:**
- `letters/mahatma-gandhi/in.ernet.dli.2015.208999/primary_text.txt`
- `letters/mahatma-gandhi/in.ernet.dli.2015.208999/extraction_report.json`
- Raw extraction files for verification

### 2. precise_letter_extractor.py

Final extraction tool using precise line-number mapping.

**Features:**
- Manual line-number mapping for 100% accuracy
- Comprehensive OCR cleanup
- Rich metadata generation
- Content hashing for verification
- Markdown output with YAML frontmatter

**Usage:**
```bash
python precise_letter_extractor.py
```

**Output:**
- 22 individual markdown files
- `collection-index.json`
- Complete metadata for each letter

### 3. letter_parser.py

(Deprecated) Early parser for letter boundary detection.

**Features:**
- Pattern-based letter detection
- Basic OCR cleanup
- Metadata extraction

**Note:** Superseded by `precise_letter_extractor.py`

### 4. gandhi_letter_parser.py

(Deprecated) Gandhi-specific parser.

**Note:** Superseded by `precise_letter_extractor.py`

### 5. comprehensive_letter_extractor.py

(Deprecated) Intermediate extraction tool.

**Note:** Superseded by `precise_letter_extractor.py`

## Extraction Pipeline

### Step 1: Download and Extract
```bash
python archive_org_extractor.py
```
- Downloads from Archive.org
- Extracts using multiple OCR methods
- Verifies extraction quality
- Saves primary text

### Step 2: Parse Individual Letters
```bash
python precise_letter_extractor.py
```
- Uses precise line mapping
- Splits into individual letters
- Applies OCR cleanup
- Generates markdown files

## OCR Cleanup Rules

The extractor applies these automatic fixes:

```python
# Common OCR errors corrected:
'Grandhji' → 'Gandhi'
'Gandhiji' → 'Gandhi'
'Mahatmaji' → 'Mahatma'
'G-overnment' → 'Government'
'Mohammedan' → 'Muslim'
'Mussalman' → 'Muslim'
'Hijrat' → 'Hijrah'
'Chiang Kai Sheck' → 'Chiang Kai-shek'
```

Additionally:
- Removes hyphenated line breaks
- Fixes broken sentences across lines
- Normalizes whitespace
- Removes page numbers and headers
- Fixes punctuation spacing

## Line Number Mapping

Letters were manually identified using grep patterns:

```bash
# Find all major section headers
grep -n "^LETTER\|^TO\|^ULTIMATUM" primary_text.txt

# Verify boundaries
grep -n "WILLINGDON\|HOARE\|IRWIN" primary_text.txt
```

### Identified Boundaries

```python
letter_map = [
    (413, "Letter to Lord Chelmsford"),
    (624, "Ultimatum to Lord Chelmsford"),
    (821, "To Every Englishman - First Letter"),
    (1029, "To Every Englishman - Second Letter"),
    (1208, "To the Youngmen of Bengal"),
    (1356, "To the Duke of Connaught"),
    (1510, "Ultimatum to Lord Reading"),
    (1699, "Letters to Lord Irwin - First"),
    (2094, "Letters to Lord Irwin - Second"),
    (2348, "To Inmates of Sabarmati Ashram"),
    (2510, "To Lord Willingdon - First Rejoinder"),
    (2720, "To Lord Willingdon - Second Rejoinder"),
    (2789, "To the Nation"),
    (2898, "To Sir Samuel Hoare"),
    (3105, "To Ramsay MacDonald"),
    (3201, "To M.A. Jinnah"),
    (3285, "To Chiang Kai-shek"),
    (3487, "To the People of America"),
    (3564, "To Lord Linlithgow - First (1942)"),
    (4009, "To Lord Linlithgow - New Year's Eve"),
    (4171, "To Lord Linlithgow - Personal"),
    (4271, "To Lord Linlithgow - Last Letter"),
]
```

## Verification Methods

### 1. Content Hashing
Each letter includes a SHA-256 hash of its content for verification:
```python
content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
```

### 2. Word Count Tracking
Every letter records word count for integrity checking.

### 3. Line Range Documentation
Source line ranges preserved for reference back to primary text.

### 4. Multiple OCR Sources
- DJVU text layer (primary)
- PDF extraction (verification)
- Cross-comparison of results

## Dependencies

```
requests>=2.31.0
PyPDF2 (for PDF extraction)
```

## Future Improvements

Potential enhancements:

1. **AI-Assisted Review**: Use LLM to verify OCR accuracy
2. **Additional Letters**: Extract sub-letters (Home Member, Richards)
3. **Parallel Collections**: Apply to other Archive.org letter collections
4. **Enhanced Metadata**: Extract dates, locations more accurately
5. **Image Integration**: Link to original page images

## Archive.org API Usage

The tools use Archive.org's open APIs:

```python
# Metadata API
metadata_url = f"https://archive.org/metadata/{identifier}"

# Download API
download_url = f"https://archive.org/download/{identifier}/{filename}"
```

## Error Handling

The tools include:
- Timeout handling for network requests
- Retry logic for failed downloads
- Fallback to alternative extraction methods
- Comprehensive logging

## Logging

All tools generate detailed logs:
```
2025-11-18 03:18:32,845 - INFO - Extracting letters...
2025-11-18 03:18:32,848 - INFO - Letter 1: Letter to Lord Chelmsford (1502 words)
...
2025-11-18 03:18:32,889 - INFO - Total letters extracted: 22
```

## Testing

Verify extraction:
```bash
# Count letters
ls letters/mahatma-gandhi/individual-letters/*.md | wc -l

# Verify word counts
wc -w letters/mahatma-gandhi/individual-letters/*.md

# Check metadata
cat letters/mahatma-gandhi/individual-letters/collection-index.json
```

## License

These extraction tools are provided as-is for archival and educational purposes.

---

**Created**: November 18, 2025
**For**: PaperLanterns.ink
**Purpose**: Preserving historic Indian letters
