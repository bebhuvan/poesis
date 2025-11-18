# Famous Letters of Mahatma Gandhi

A meticulously extracted collection of 22 historic letters written by Mahatma Gandhi, compiled from the 1947 publication "Famous Letters Of Mahatma Gandhi" by R.L. Khipple, M.A.

## About This Collection

This collection represents some of the most significant correspondence from one of history's most influential leaders. These letters, written between the 1910s and 1940s, document Gandhi's political philosophy, his negotiations with British authorities, and his unwavering commitment to non-violent resistance.

### Source Information

- **Original Publication**: "Famous Letters Of Mahatma Gandhi"
- **Compiler**: R.L. Khipple, M.A.
- **Publisher**: The Indian Printing Works, Lahore
- **Year**: 1947
- **Archive.org ID**: [in.ernet.dli.2015.208999](https://archive.org/details/in.ernet.dli.2015.208999)
- **Public Domain Status**: Yes (Published 1947, author died 1948)

## Extraction Methodology

### Multi-Strategy OCR Approach

To ensure maximum accuracy, we employed multiple extraction and verification strategies:

1. **Archive.org DJVU Text Layer**: Primary OCR source (184KB, 27,656 words)
2. **PDF Text Extraction**: Secondary verification method
3. **Precise Line Mapping**: Manual identification of letter boundaries
4. **Automated OCR Cleanup**: Fixed common OCR errors
5. **Content Hashing**: SHA-256 hash for verification

### Quality Assurance

- ✅ Multiple OCR methods for cross-verification
- ✅ Precise line-number based extraction
- ✅ Automated cleanup of common OCR errors
- ✅ Preserved historical context notes
- ✅ Complete metadata for each letter
- ⚠️  Manual review recommended for critical research

## Letters in This Collection

### Correspondence Overview

1. **Letter to Lord Chelmsford** (1,502 words) - WWI War Conference
2. **Ultimatum to Lord Chelmsford** (1,233 words) - Non-cooperation movement
3. **To Every Englishman Living in India - First Letter** (1,306 words)
4. **To Every Englishman Living in India - Second Letter** (1,191 words)
5. **To the Youngmen of Bengal** (913 words) - Youth engagement
6. **To His Royal Highness, The Duke of Connaught** (974 words)
7. **Ultimatum to Lord Reading** (1,231 words) - Civil disobedience warning
8. **Letters to Lord Irwin - First Letter** (2,537 words) - Salt March precursor
9. **Letters to Lord Irwin - Second Letter** (1,546 words)
10. **To the Inmates of Sabarmati Ashram** (963 words) - Personal guidance
11. **Letters to Lord Willingdon - First Rejoinder** (1,457 words)
12. **Letters to Lord Willingdon - Second Rejoinder** (416 words)
13. **To the Nation** (669 words) - National appeal
14. **To Sir Samuel Hoare - Secretary of State for India** (1,307 words)
15. **To Ramsay MacDonald - British Prime Minister** (602 words)
16. **To Mr. M.A. Jinnah - President of the Muslim League** (535 words)
17. **To Generalissimo Chiang Kai-shek** (1,381 words) - International solidarity
18. **To the People of America** (498 words) - International appeal
19. **Letters to Lord Linlithgow - First Letter (1942)** (2,783 words)
20. **To Lord Linlithgow - On New Year's Eve** (885 words)
21. **To Lord Linlithgow - Personal** (634 words)
22. **To Lord Linlithgow - Last Letter** (1,231 words)

## File Format

Each letter is saved as a Markdown file with:

### YAML Frontmatter
```yaml
---
letter_number: 1
title: "Letter to Lord Chelmsford"
author: "Mahatma Gandhi"
recipient: "Lord Chelmsford"
word_count: 1502
content_hash: "62dcfb2219cb7e17"
source:
  archive_org_id: "in.ernet.dli.2015.208999"
  title: "Famous Letters Of Mahatma Gandhi"
  compiler: "R.L. Khipple, M.A."
  publisher: "The Indian Printing Works, Lahore"
  year: 1947
  line_range: "413-623"
public_domain:
  status: true
  reason: "Published 1947, author died 1948 (77 years ago)"
verification:
  extraction_method: "precise_line_mapping"
  ocr_cleaned: true
  manual_review_needed: true
extracted_at: "2025-11-18T03:18:32.879406"
---
```

### Letter Content
- Historical context notes (when available)
- Full letter text with OCR cleanup applied
- Preserved original formatting and structure

## OCR Cleanup Applied

The following automated corrections were made:

- Fixed hyphenated line breaks
- Corrected common OCR errors (e.g., "Gandhiji" → "Gandhi")
- Normalized spacing and punctuation
- Removed page numbers and headers
- Fixed broken sentences across lines
- Modernized archaic terminology where appropriate

## Directory Structure

```
letters/mahatma-gandhi/
├── README.md (this file)
├── individual-letters/
│   ├── 01-lord-chelmsford.md
│   ├── 02-lord-chelmsford.md
│   ├── ...
│   ├── 22-lord-linlithgow.md
│   └── collection-index.json
└── in.ernet.dli.2015.208999/
    ├── extraction_report.json
    ├── primary_text.txt
    ├── raw_txt.txt
    └── temp/ (download cache)
```

## Usage

### For Researchers

These letters are primary historical sources documenting:
- Gandhi's non-violent resistance philosophy
- British-Indian colonial negotiations
- The Indian independence movement
- Gandhi's personal relationships and guidance

### For Developers

- **Machine-readable format**: Markdown with YAML frontmatter
- **Content verification**: SHA-256 hashes provided
- **Source traceability**: Line ranges and extraction metadata
- **Public domain**: Free to use for any purpose

## Citation

If you use these letters in academic work, please cite:

```
Gandhi, Mahatma. Famous Letters Of Mahatma Gandhi.
Compiled by R.L. Khipple, M.A. Lahore: The Indian Printing Works, 1947.
Digital edition extracted from Archive.org (in.ernet.dli.2015.208999), 2025.
```

## Known Limitations

- Some letters may have minor OCR errors requiring manual review
- Original page layout and typography not preserved
- Table of contents lists 27 entries; 22 distinct letters extracted
- A few sub-letters (Home Member, Richards) not yet separately extracted

## Contributing

If you find OCR errors or have corrections, please:
1. Note the letter number and content hash
2. Provide the correction with line reference
3. Submit via issue or pull request

## License

**Public Domain** - These letters were published in 1947 and the author died in 1948, placing them firmly in the public domain worldwide.

## Acknowledgments

- **Archive.org** - For digitizing and preserving this historic text
- **Digital Library of India** - Original scanning project
- **R.L. Khipple, M.A.** - Original compilation and publication
- **Rashtrapati Bhavan Library** - Source institution

## Tools Used

- Archive.org DJVU OCR text layer
- PyPDF2 for PDF extraction
- Python 3.11 for extraction automation
- Multiple verification strategies for accuracy

---

**Extracted**: November 18, 2025
**For**: PaperLanterns.ink - Preserving historic letters for public access
**Contact**: Through GitHub repository
