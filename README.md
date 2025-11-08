# Poesis: Poetry Scraper & Curation System

A comprehensive system for scraping, validating, and curating public domain poetry from the internet.

## Features

### 🔍 **Multi-Source Scraping**
- **Wikisource API** - Comprehensive poetry database (fully implemented)
- **Poets.org** - Public domain anthology with explicit PD markers (fully implemented)
- Poetry Foundation support (planned)
- Wikipedia and Wikidata for poet metadata

### ✅ **Link Verification**
- **Zero hallucination guarantee**: All URLs verified with actual HTTP requests
- Verified links to poet Wikipedia pages
- Verified links to Poetry Foundation profiles
- Source URL tracking with content hashes for audit trail

### 📜 **Public Domain Validation**
- Automatic validation based on author death dates
- Life + 70 years rule (configurable)
- Confidence scoring for each poem
- Manual review flagging for uncertain cases

### 🎨 **Diversity & Curation**
- Balanced representation across time periods (centuries)
- Author diversity (max poems per author)
- Quality scoring system
- Filtering for substantial poems (not fragments)

### 📝 **Clean Markdown Output**
- Individual `.md` file for each poem
- Rich YAML front matter with metadata
- Verified links (Wikipedia, Poetry Foundation, Wikisource)
- Source tracking (URL, fetch timestamp, content hash)
- Public domain status and reasoning

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd poesis

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Scraping from Poets.org (Recommended for Public Domain)

Poets.org explicitly marks poems with "This poem is in the public domain" - making it the most reliable source:

```bash
# Dry run to see what would be scraped
python main_poets_org.py --dry-run --target 10

# Collect 50 public domain poems from poets.org
python main_poets_org.py --target 50

# Collect with verbose logging
python main_poets_org.py --target 100 --verbose
```

### Scraping from Wikisource

Wikisource provides comprehensive coverage with metadata:

```bash
# Dry run (Test Mode)
python main.py --dry-run

# Collect 50 Poems
python main.py --target 50

# Collect 100 Poems with Verbose Logging
python main.py --target 100 --verbose
```

## Output Structure

### Markdown File Example

```markdown
---
title: "The Raven"
author: "Edgar Allan Poe"
author_birth_year: 1809
author_death_year: 1849
source:
  url: "https://en.wikisource.org/wiki/The_Raven"
  fetched_at: "2025-11-08T10:30:00Z"
  content_hash: "a3f8d9e2b1c4..."
links:
  wikipedia:
    url: "https://en.wikipedia.org/wiki/Edgar_Allan_Poe"
    verified: true
    verified_at: "2025-11-08T10:31:00Z"
  poetry_foundation:
    url: "https://www.poetryfoundation.org/poets/edgar-allan-poe"
    verified: true
    verified_at: "2025-11-08T10:31:15Z"
  wikisource:
    url: "https://en.wikisource.org/wiki/The_Raven"
    verified: true
    verified_at: "2025-11-08T10:31:30Z"
public_domain:
  status: true
  confidence: "high"
  reason: "Author died in 1849, 176 years ago (threshold: 70 years)"
generated_at: "2025-11-08T10:32:00Z"
---

Once upon a midnight dreary, while I pondered, weak and weary,
Over many a quaint and curious volume of forgotten lore—
...
```

## Directory Structure

```
poesis/
├── main.py                    # Main orchestrator for Wikisource
├── main_poets_org.py          # Main orchestrator for Poets.org
├── config.py                  # Configuration settings
├── wikisource_scraper.py      # Wikisource API scraper
├── poets_org_scraper.py       # Poets.org scraper (with explicit PD markers)
├── link_verifier.py           # Link verification with HTTP checks
├── public_domain.py           # Public domain validator
├── markdown_generator.py      # Markdown file generator
├── curator.py                 # Curation and diversity filters
├── requirements.txt           # Python dependencies
├── poems/                     # Generated markdown files (created on run)
└── logs/                      # Log files and audit trails (created on run)
```

## Anti-Hallucination Safeguards

This system has **multiple layers** to prevent hallucinated content:

1. **Source URL Required**: Every poem must have a `source_url` field
2. **HTTP Verification**: All links verified with actual GET requests
3. **Content Hashing**: SHA-256 hash of source page stored for audit
4. **Fetch Timestamps**: Record exactly when content was retrieved
5. **Audit Logs**: Complete JSON logs of all scraping operations
6. **No Manual Entry**: System only accepts scraped content, never manual input

## Configuration

Edit `config.py` to customize:

```python
# Target collection size
TARGET_POEMS = 50

# Public domain threshold (years after death)
PUBLIC_DOMAIN_THRESHOLD = 70

# Rate limiting (seconds between requests)
REQUEST_DELAY = 1.0

# HTTP timeout
HTTP_TIMEOUT = 10
```

## Logs & Audit Trail

Every run creates:
- **Log file**: `logs/scraper_YYYYMMDD_HHMMSS.log`
- **Audit JSON**: `logs/audit_scraper_YYYYMMDD_HHMMSS.json`

The audit JSON contains:
- All poems processed
- All poems saved with file paths
- Verification status for all links
- Error log
- Complete timestamp trail

## Phased Approach

### Phase 1: Initial Testing (50 poems)
```bash
python main.py --target 50
```
- Test scraper quality
- Manually review output
- Refine metadata structure

### Phase 2: First Collection (100-150 poems)
```bash
python main.py --target 150
```
- Expand with confidence
- Balance across cultures and time periods

### Phase 3: Full Collection (200-300 poems)
```bash
python main.py --target 300
```
- Complete curated collection
- Maximum diversity

## Manual Review

After running the scraper, review:

1. **Check the logs** in `logs/` directory
2. **Verify links** by clicking URLs in the markdown front matter
3. **Read sample poems** to ensure quality
4. **Check diversity** in the audit JSON file

## Extending the System

### Add New Sources

1. Create a new scraper class (e.g., `poetry_foundation_scraper.py`)
2. Implement the same interface as `WikisourceScraper`
3. Import and use in `main.py`

### Adjust Curation Criteria

Edit `curator.py`:
- Modify `score_poem()` for different quality metrics
- Adjust `max_per_author` and `max_per_century` limits
- Add new diversity dimensions (language, form, etc.)

## Command Line Options

```bash
python main.py --help

Options:
  --target N        Target number of poems to collect (default: 50)
  --dry-run         Show what would be done without saving files
  --verbose         Enable verbose logging
```

## Requirements

- Python 3.7+
- Internet connection
- Dependencies listed in `requirements.txt`

## License

This is a tool for collecting public domain poetry. All scraped poems are in the public domain. The scraper code itself is provided as-is for educational purposes.

## Contributing

This is a personal project for building a poetry collection. Feel free to fork and adapt for your own use.

## Roadmap

- [x] Add Poets.org scraper with explicit PD marker detection
- [ ] Add Poetry Foundation scraper
- [ ] Multi-language Wikisource support (French, Spanish, German, etc.)
- [ ] Improve poem text extraction (remove HTML artifacts)
- [ ] Enhanced author date extraction from poets.org
- [ ] Genre/form classification
- [ ] Emotional/thematic tagging
- [ ] Export to website-ready format
- [ ] Duplicate detection across sources
- [ ] Merge results from multiple sources into one curated collection

## Questions?

Check the logs in `logs/` for detailed information about what the scraper is doing.
