"""Poets.org scraper for public domain poems."""

import requests
import logging
import time
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

from config import USER_AGENT, REQUEST_DELAY, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


class PoetsOrgScraper:
    """Scraper for Poets.org public domain poetry anthology."""

    def __init__(self):
        """Initialize scraper."""
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.base_url = "https://poets.org"

    def search_public_domain_poems(self, limit: int = 100, max_pages: int = 50, start_page: int = 0) -> List[Dict]:
        """
        Search for public domain poems on poets.org by browsing the poems section.

        Args:
            limit: Maximum number of poem links to collect
            max_pages: Maximum number of pages to browse
            start_page: Page number to start browsing from (default: 0)

        Returns:
            List of poem metadata dictionaries
        """
        logger.info(f"Searching poets.org poems section (limit: {limit}, max pages: {max_pages}, starting from page: {start_page})")

        poem_links = []

        # Browse the main poems section with pagination
        for page_num in range(start_page, start_page + max_pages):
            if len(poem_links) >= limit:
                break

            # poets.org uses ?page=N for pagination
            browse_url = f"{self.base_url}/poems?page={page_num}"

            try:
                logger.info(f"Browsing page {page_num + 1}/{start_page + max_pages}...")
                response = self.session.get(browse_url, timeout=HTTP_TIMEOUT)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Find all poem title links on this page
                page_links = []
                for link in soup.find_all('a', href=re.compile(r'^/poem/')):
                    poem_url = link.get('href')
                    title = link.get_text(strip=True)

                    # Skip if empty or already found
                    if not title or not poem_url:
                        continue

                    full_url = poem_url if poem_url.startswith('http') else f"{self.base_url}{poem_url}"

                    # Check if we already have this URL
                    if full_url not in [p['url'] for p in poem_links]:
                        page_links.append({
                            'title': title,
                            'url': full_url
                        })

                logger.info(f"  Found {len(page_links)} poem links on page {page_num + 1}")
                poem_links.extend(page_links)

                # Stop if we've reached the limit
                if len(poem_links) >= limit:
                    poem_links = poem_links[:limit]
                    break

                # If no poems found on this page, we've probably reached the end
                if not page_links:
                    logger.info(f"No poems found on page {page_num + 1} - stopping")
                    break

                time.sleep(REQUEST_DELAY)

            except Exception as e:
                logger.error(f"Error browsing page {page_num + 1}: {str(e)}")
                break

        logger.info(f"Collected {len(poem_links)} total poem links from poets.org")
        return poem_links

    def extract_lifespan(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """
        Extract birth and death years from text like "(1809–1849)" or "(1809-1849)".

        Args:
            text: Text potentially containing lifespan

        Returns:
            Tuple of (birth_year, death_year)
        """
        # Pattern for lifespan: (YYYY–YYYY) or (YYYY-YYYY)
        pattern = r'\((\d{4})\s*[–-]\s*(\d{4})\)'
        match = re.search(pattern, text)

        if match:
            birth_year = int(match.group(1))
            death_year = int(match.group(2))
            return birth_year, death_year

        return None, None

    def get_poem_content(self, poem_url: str) -> Optional[Dict]:
        """
        Fetch full poem content from poets.org.

        Args:
            poem_url: URL to poem page

        Returns:
            Dictionary with poem content and metadata
        """
        logger.info(f"Fetching poem from: {poem_url}")

        try:
            response = self.session.get(poem_url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title = None
            title_elem = soup.find('h1') or soup.find('h2', class_=re.compile(r'title|poem-title'))
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract author
            author = None
            author_elem = soup.find('a', href=re.compile(r'^/poet/')) or \
                         soup.find('span', class_=re.compile(r'author|poet'))
            if author_elem:
                author = author_elem.get_text(strip=True)
                # Sometimes includes lifespan in parentheses
                author = re.sub(r'\s*\(\d{4}.*?\)', '', author).strip()

            # Extract lifespan dates from author info
            author_info = soup.find('div', class_=re.compile(r'author-info|poet-info'))
            birth_year, death_year = None, None

            if author_info:
                info_text = author_info.get_text()
                birth_year, death_year = self.extract_lifespan(info_text)

            # Also check in byline or other author containers
            if not birth_year or not death_year:
                byline = soup.find('div', class_=re.compile(r'byline|author-byline'))
                if byline:
                    byline_text = byline.get_text()
                    birth_year, death_year = self.extract_lifespan(byline_text)

            # Extract poem text
            poem_text = None

            # Strategy 1: Look for specific poem content containers
            poem_body = soup.find('div', class_=re.compile(r'poem-body|poem-content|field-name-body'))

            if poem_body:
                # Remove any script, style, or navigation elements
                for unwanted in poem_body.find_all(['script', 'style', 'nav', 'aside', 'button', 'form']):
                    unwanted.decompose()

                # Remove specific unwanted elements by class
                for unwanted_class in ['anthology-add', 'share-buttons', 'social-share', 'add-to-anthology']:
                    for elem in poem_body.find_all(class_=re.compile(unwanted_class, re.IGNORECASE)):
                        elem.decompose()

                # Get text, preserving line breaks
                lines = []
                for elem in poem_body.find_all(['p', 'div', 'br']):
                    if elem.name == 'br':
                        continue
                    text = elem.get_text(separator='\n', strip=True)
                    # Skip empty lines, close buttons, and common artifacts
                    if text and not text.startswith('×') and text.lower() not in ['add to anthology']:
                        lines.append(text)

                poem_text = '\n'.join(lines)

                # Clean up common artifacts
                poem_text = re.sub(r'^Add to anthology\s*\n', '', poem_text, flags=re.MULTILINE | re.IGNORECASE)
                poem_text = re.sub(r'×\s*\n', '', poem_text)
                poem_text = re.sub(r'\n{3,}', '\n\n', poem_text)  # Remove excessive blank lines

            # Strategy 2: If no specific container, look for stanzas
            if not poem_text:
                stanzas = soup.find_all('div', class_=re.compile(r'stanza|verse'))
                if stanzas:
                    stanza_texts = []
                    for stanza in stanzas:
                        stanza_text = stanza.get_text(separator='\n', strip=True)
                        if stanza_text:
                            stanza_texts.append(stanza_text)
                    poem_text = '\n\n'.join(stanza_texts)

            # Check for public domain confirmation
            public_domain_confirmed = False
            page_text = soup.get_text()
            if "This poem is in the public domain" in page_text:
                public_domain_confirmed = True
                logger.info("✓ Found explicit 'This poem is in the public domain' text")

            # If we couldn't find the poem text, get main content
            if not poem_text:
                main_content = soup.find('main') or soup.find('article')
                if main_content:
                    # Remove navigation, footer, etc.
                    for unwanted in main_content.find_all(['nav', 'footer', 'aside', 'script', 'style']):
                        unwanted.decompose()
                    poem_text = main_content.get_text(separator='\n', strip=True)

            if not poem_text:
                logger.warning(f"Could not extract poem text from {poem_url}")
                return None

            # Generate content hash
            content_hash = hashlib.sha256(response.content).hexdigest()[:16]

            result = {
                'title': title or 'Untitled',
                'author': author or 'Unknown',
                'text': poem_text,
                'poet_birth_year': birth_year,
                'poet_death_year': death_year,
                'source_url': poem_url,
                'fetched_at': datetime.utcnow().isoformat(),
                'content_hash': content_hash,
                'public_domain_confirmed': public_domain_confirmed,
                'source': 'poets.org'
            }

            logger.info(f"✓ Successfully fetched: {title} by {author}")
            if birth_year and death_year:
                logger.info(f"  Author lifespan: {birth_year}–{death_year}")

            time.sleep(REQUEST_DELAY)
            return result

        except Exception as e:
            logger.error(f"Error fetching poem from {poem_url}: {str(e)}")
            return None

    def get_poems(self, limit: int = 50, max_browse_pages: int = 50, start_page: int = 0) -> List[Dict]:
        """
        Get a collection of public domain poems from poets.org.

        Args:
            limit: Maximum number of PUBLIC DOMAIN poems to collect
            max_browse_pages: Maximum pages to browse looking for PD poems
            start_page: Page number to start browsing from (default: 0)

        Returns:
            List of poem dictionaries with full content and metadata (only public domain)
        """
        # Step 1: Browse many pages to find poem links
        # We'll check way more than limit since most won't be public domain
        browse_limit = limit * 20  # Check 20x as many poems to find enough PD ones
        poem_links = self.search_public_domain_poems(limit=browse_limit, max_pages=max_browse_pages, start_page=start_page)

        if not poem_links:
            logger.warning("No poem links found on poets.org")
            return []

        logger.info(f"Found {len(poem_links)} poem links to check for public domain status")

        # Step 2: Fetch each poem and filter for public domain
        public_domain_poems = []
        checked_count = 0

        for i, link in enumerate(poem_links, 1):
            # Stop if we've found enough public domain poems
            if len(public_domain_poems) >= limit:
                logger.info(f"Reached target of {limit} public domain poems")
                break

            checked_count += 1
            logger.info(f"[{i}/{len(poem_links)}] Checking: {link['title']} (Found {len(public_domain_poems)} PD poems so far)")

            poem = self.get_poem_content(link['url'])

            if poem:
                # Only keep poems that are explicitly marked as public domain
                if poem.get('public_domain_confirmed'):
                    public_domain_poems.append(poem)
                    logger.info(f"  ✓ PUBLIC DOMAIN - Added to collection ({len(public_domain_poems)}/{limit})")
                else:
                    logger.info(f"  ✗ Not public domain - skipping")
            else:
                logger.warning(f"  Failed to fetch")

        logger.info(f"Successfully found {len(public_domain_poems)} public domain poems after checking {checked_count} poems")
        return public_domain_poems
