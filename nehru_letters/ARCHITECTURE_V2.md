# Nehru Letters OCR Extraction - Architecture V2
## Multi-Strategy Parallel Processing System

### Design Philosophy
- **Redundancy**: Multiple OCR engines running in parallel
- **Intelligence**: LLM-guided post-processing and validation
- **Competition**: Strategies compete, best results selected per page
- **Verification**: Multi-layered quality control
- **Transparency**: Complete audit trail of all decisions

---

## Pipeline Architecture

### Stage 1: Parallel OCR Extraction
**Multiple engines running simultaneously:**

1. **Tesseract Strategy Suite** (6 variants)
   - Strategy A: Raw image, PSM 6
   - Strategy B: Grayscale + contrast enhancement, PSM 6
   - Strategy C: Binarization (Otsu), PSM 6
   - Strategy D: Denoising + sharpening, PSM 6
   - Strategy E: Deskew + binarization, PSM 1
   - Strategy F: High DPI (600) + binarization, PSM 6

2. **EasyOCR Strategy**
   - GPU-accelerated if available
   - English language model
   - Paragraph mode

3. **PaddleOCR Strategy**
   - State-of-art Chinese/English model
   - Layout analysis enabled

4. **Fallback: Pytesseract Legacy**
   - Different version/config
   - For comparison

**Output**: 8-10 different OCR results per page

---

### Stage 2: LLM-Based Intelligent Post-Processing

**For each OCR result:**

1. **Context-Aware Error Correction**
   - LLM identifies likely OCR errors (e.g., "vesterday" → "yesterday")
   - Fixes based on historical/contextual understanding
   - Preserves original if uncertain

2. **Artifact Removal**
   - LLM identifies non-content elements (page numbers, library stamps, etc.)
   - Smart removal vs. preservation decisions

3. **Layout Reconstruction**
   - Identify paragraph breaks, letter structure
   - Preserve formatting that matters
   - Remove spurious line breaks

4. **Confidence Annotation**
   - LLM marks uncertain passages for human review
   - Provides alternative interpretations

**Output**: Cleaned, intelligent version of each OCR result

---

### Stage 3: Multi-Method Quality Scoring

**Automated metrics:**
- OCR confidence scores
- Language model perplexity (how natural the text reads)
- Artifact count (fewer is better)
- Layout coherence score
- Character-level confidence

**LLM evaluation:**
- Readability assessment
- Coherence check
- Historical accuracy verification (does it make sense for 1920s letter?)

**Scoring weights:**
```
Final Score =
  25% OCR confidence +
  20% LLM readability +
  20% Artifact-free +
  20% Layout quality +
  15% Language perplexity
```

**Output**: Ranked results for each page

---

### Stage 4: Smart Strategy Selection

**Per-page winner selection:**
1. Automatic selection based on scores (if clear winner >10% margin)
2. LLM arbitration (if close scores)
3. Create ensemble version (combine best parts of top 3)

**Output**: Best-of-breed text for each page

---

### Stage 5: Intelligent Letter Boundary Detection

**Method 1: Table of Contents Parsing**
- Extract TOC from front matter
- Parse letter numbers and titles
- Map to page numbers

**Method 2: Pattern Recognition**
- Roman numerals
- Letter headers
- Date patterns
- Signature patterns

**Method 3: LLM Analysis**
- Feed entire document to LLM
- Ask it to identify letter boundaries
- Provide reasoning for each boundary

**Method 4: Content Flow Analysis**
- Detect topic shifts
- Identify greeting/closing patterns
- Track narrative continuity

**Consensus Algorithm:**
- Combine all 4 methods
- High-confidence boundaries (3+ methods agree)
- Medium-confidence (2 methods agree, manual review needed)
- LLM final arbitration for conflicts

**Output**: Accurately split letters with metadata

---

### Stage 6: Metadata Extraction

**For each letter:**

1. **Date Extraction**
   - Pattern matching for date formats
   - LLM context analysis (references to events, seasons)
   - Cross-reference with known historical timeline

2. **Title Extraction**
   - From TOC
   - From letter header
   - LLM-generated descriptive title if missing

3. **Recipient/Author Confirmation**
   - Parse letter opening/closing
   - Verify against known format

4. **Topic Tagging**
   - LLM-based topic identification
   - Keywords extraction
   - Thematic categorization

**Output**: Rich metadata for each letter

---

### Stage 7: Verification & Review Interface

**Multi-level review:**

1. **Comparison View**: Side-by-side all strategies
2. **Diff View**: Highlight differences between top strategies
3. **Confidence Heatmap**: Visual indication of uncertain text
4. **LLM Comments**: Inline notes on decisions made
5. **Original Scans**: Always accessible for human verification

**Interactive Features:**
- Click any paragraph to see all strategy versions
- Flag sections for human review
- Export specific strategy results
- Search across all versions

**Output**: HTML review interface + flagged issues list

---

### Stage 8: Final Quality Assurance

**Automated checks:**
- Spell check (with historical language awareness)
- Grammar check (1920s style)
- Completeness check (all pages processed)
- Continuity check (letters flow logically)

**LLM comprehensive review:**
- Read entire document
- Identify missing content
- Flag inconsistencies
- Verify letter boundaries make sense
- Check metadata accuracy

**Human review prompts:**
- High-priority issues list
- Medium-confidence decisions
- Statistics dashboard

**Output**: Final verified text + issue report

---

## Technology Stack

**OCR Engines:**
- Tesseract 5.3.4
- EasyOCR (Python)
- PaddleOCR (Python)

**Image Processing:**
- PIL/Pillow
- OpenCV
- scikit-image

**LLM Integration:**
- Claude API (for intelligent processing)
- Local embedding model for similarity

**Infrastructure:**
- Parallel processing (multiprocessing)
- Caching (avoid re-processing)
- Progress tracking
- Error recovery

---

## Success Metrics

**Target Quality:**
- 99.5%+ character accuracy
- 100% letter boundary accuracy
- 95%+ metadata completeness
- Zero missing content
- Human verification required only for flagged items

**Performance:**
- Process all 90 pages in < 30 minutes
- Full pipeline reproducible
- Clear audit trail

---

## Implementation Phases

**Phase 1**: Set up all OCR engines ✓ (pending)
**Phase 2**: Implement parallel extraction ✓ (pending)
**Phase 3**: Build LLM post-processing ✓ (pending)
**Phase 4**: Create scoring system ✓ (pending)
**Phase 5**: Implement letter detection ✓ (pending)
**Phase 6**: Build review interface ✓ (pending)
**Phase 7**: Run full pipeline ✓ (pending)
**Phase 8**: Final QA ✓ (pending)

---

Last updated: 2025-11-22
Status: Architecture design complete, ready for implementation
