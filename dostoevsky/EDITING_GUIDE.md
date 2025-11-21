# Guide to Editing and Improving the Dostoevsky Letters

## Overview

The letters have been extracted from OCR text, which means there may be errors, formatting issues, and typos that need correction. This guide explains how to edit and improve the letters.

## File Structure

```
dostoevsky/
├── letters_markdown/          # Individual letter markdown files
│   ├── 001_his_Father.md
│   ├── 003_his_Brother_Michael.md
│   └── ...
├── letters_final.json         # JSON file with all letters (used by website)
├── website/                   # Static website files
│   ├── letters.json          # Copy of letters_final.json
│   └── ...
└── tools/                     # Editing and improvement tools
    ├── fix_ocr_errors.py
    ├── rebuild_json.py
    └── ...
```

## Editing Workflow

### Step 1: Edit Markdown Files

The easiest way to improve the letters is to edit the markdown files directly:

```bash
# Edit a specific letter
nano letters_markdown/001_his_Father.md
# or use your preferred editor
code letters_markdown/001_his_Father.md
```

Each markdown file has this structure:

```markdown
---
letter_number: 1
author: Fyodor Dostoevsky
title: "Letter to his Father"
recipient: "his Father"
date: "May 10, 1838"
translator: Ethel Colburn Mayne
source: "Letters of Fyodor Michailovitch Dostoevsky (1917)"
source_url: "https://archive.org/details/lettersoffyodorm00dostiala"
has_footnotes: true
footnote_count: 3
public_domain: true
---

# Letter 1

## To his Father

**May 10, 1838**

---

[Letter body text here...]

---

### Footnotes

**[1]** Footnote text here...
```

### Step 2: Common OCR Issues to Fix

#### Issue 1: Double Spaces

The OCR often adds double spaces between words:

**Before:**
```
Can  you  really  think  that  your  son  is  asking
```

**Fix:**
```
Can you really think that your son is asking
```

**Tool:**
```bash
python3 tools/fix_ocr_errors.py letters_markdown/001_his_Father.md --fix-spaces
```

#### Issue 2: Line Breaks Mid-Sentence

The OCR breaks paragraphs incorrectly:

**Before:**
```
Can you really think that your son is asking

too much when he applies to you for an allowance?
```

**Fix:**
```
Can you really think that your son is asking too much when he applies to you for an allowance?
```

**Manual Fix:**
Join lines that belong together into proper paragraphs.

#### Issue 3: Common OCR Character Errors

| OCR Error | Should Be | Pattern |
|-----------|-----------|---------|
| rn | m | in middle of words |
| cl | d | in middle of words |
| vv | w | in middle of words |
| 1 | l | in words (not numbers) |
| 0 | O | in words |
| „ | " | quote marks |
| ,, | " | quote marks |

**Tool:**
```bash
python3 tools/fix_ocr_errors.py letters_markdown/*.md --fix-common
```

#### Issue 4: Incorrect Metadata

Sometimes the recipient or date is wrong:

**Before:**
```yaml
recipient: "know more, one must feel less, and vice versa"
```

**Fix:**
```yaml
recipient: "his Brother Michael"
```

**How to Find:** Check `EDITING_GUIDE.md` section on letter numbering, or compare with table of contents.

### Step 3: After Editing

Once you've edited markdown files, rebuild the JSON:

```bash
python3 tools/rebuild_json.py
```

This will:
1. Read all markdown files in `letters_markdown/`
2. Parse the frontmatter and content
3. Generate new `letters_final.json`
4. Copy to `website/letters.json`

### Step 4: Preview Changes

Refresh the website to see your changes:
```bash
# Website is running at http://localhost:8000
# Just refresh your browser
```

## Editing Tools

### 1. Automatic OCR Fixer

Fix common OCR errors automatically:

```bash
# Fix all letters
python3 tools/fix_ocr_errors.py letters_markdown/*.md --fix-all --backup

# Fix specific issues
python3 tools/fix_ocr_errors.py letters_markdown/*.md --fix-spaces --fix-common

# Dry run (see what would be changed)
python3 tools/fix_ocr_errors.py letters_markdown/*.md --fix-all --dry-run
```

### 2. Quality Checker

Check for issues in letters:

```bash
python3 tools/check_quality.py

# Output:
# Letter 5: Recipient looks suspicious: "know more, one must feel less..."
# Letter 7: No date found
# Letter 12: Very short body (< 100 chars)
```

### 3. Cross-Validator

Compare with the second edition (1923) to find discrepancies:

```bash
python3 tools/cross_validate.py --edition1917 letters_1917_raw.txt --edition1923 letters_1923_raw.txt
```

## Manual Editing Best Practices

1. **Always keep backups**: Tools create `.bak` files automatically

2. **Fix one letter at a time**: Start with important letters (to family, about major events)

3. **Verify dates and recipients**: Compare with the original table of contents

4. **Preserve translator's style**: Don't modernize spelling (e.g., keep "colour" not "color")

5. **Keep footnotes**: These provide crucial historical context

6. **Test after changes**: Always rebuild JSON and check website

## Common Editing Tasks

### Task: Fix Letter with Wrong Recipient

1. Open the letter: `nano letters_markdown/005_*.md`
2. Look at the original text to find correct recipient
3. Update the `recipient:` field in frontmatter
4. Update the `## To [recipient]` header
5. Save and rebuild: `python3 tools/rebuild_json.py`

### Task: Join Broken Paragraphs

1. Open letter in editor
2. Find paragraph breaks that should be joined
3. Remove extra newlines
4. Ensure paragraphs are separated by exactly one blank line
5. Save

### Task: Add Missing Footnotes

1. Check original text for footnotes
2. Add to end of letter:
```markdown
---

### Footnotes

**[1]** Text of footnote here...
```
3. Update `footnote_count:` in frontmatter
4. Rebuild JSON

## Batch Operations

### Fix All Double Spaces

```bash
for file in letters_markdown/*.md; do
    python3 tools/fix_ocr_errors.py "$file" --fix-spaces --no-backup
done
python3 tools/rebuild_json.py
```

### Re-extract Specific Letters

If a letter is completely broken, re-extract it:

```bash
# Edit parse_letters_simple.py to improve parsing
# Then re-run extraction
python3 parse_letters_simple.py letters_1917_raw.txt --output-md letters_markdown_new
# Compare and merge changes
```

## Quality Levels

Aim for these quality levels:

- **Level 1 (Basic)**: All letters extracted, basic metadata present
- **Level 2 (Clean)**: Fixed double spaces, joined paragraphs, corrected common OCR errors
- **Level 3 (Validated)**: Cross-checked with second edition, verified dates/recipients
- **Level 4 (Polished)**: All footnotes present, perfect formatting, proofread

## Getting Help

If stuck:
1. Check original text: `letters_1917_raw.txt`
2. Compare with 1923 edition: `letters_1923_raw.txt`
3. Search Internet Archive page for context
4. Refer to Wikipedia article: "List of letters from Fyodor Dostoevsky"

## Recommended Editing Order

1. Fix high-value letters first:
   - Letter 20 (December 22, 1849) - Written on day of death sentence
   - Letters to his brother Michael (most numerous)
   - Letters with many footnotes (historical context)

2. Fix all metadata issues (wrong recipients, missing dates)

3. Fix formatting (spaces, paragraphs)

4. Fix OCR character errors

5. Proofread important passages

---

**Remember**: This is a preservation project. The goal is to make these historical letters accessible and readable while preserving their authenticity.
