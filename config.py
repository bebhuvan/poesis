"""Configuration for poetry scraper system."""

import os

# Directories
OUTPUT_DIR = "poems"
LOGS_DIR = "logs"

# Rate limiting (seconds between requests)
REQUEST_DELAY = 1.0

# Verification settings
VERIFY_LINKS = True
HTTP_TIMEOUT = 10

# Public domain settings (years after author death)
PUBLIC_DOMAIN_THRESHOLD = 70

# Target collection size
TARGET_POEMS = 200  # Phase 2: Building substantial collection

# User agent for requests
USER_AGENT = "PoesisScraper/1.0 (Educational poetry collection; respecting robots.txt)"

# Wikisource settings
WIKISOURCE_API_BASE = "https://en.wikisource.org/w/api.php"
WIKISOURCE_LANGUAGES = ["en"]  # Can expand to: fr, es, de, it, etc.

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
