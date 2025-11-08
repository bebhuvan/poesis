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

    def search_public_domain_poems(self, limit: int = 100) -> List[Dict]:
        """
        Search for public domain poems on poets.org.

        Args:
            limit: Maximum number of poems to fetch

        Returns:
            List of poem metadata dictionaries
        """
        logger.info(f"Searching poets.org for public domain poems (limit: {limit})")

        # The main public domain anthology page
        anthology_url = f"{self.base_url}/anthology/poems-public-domain"

        try:
            response = self.session.get(anthology_url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all poem entries
            # Poems are typically in article or div containers with specific classes
            poem_links = []

            # Strategy 1: Find poem title links
            for link in soup.find_all('a', href=re.compile(r'^/poem/')):
                poem_url = link.get('href')
                if poem_url and poem_url not in [p['url'] for p in poem_links]:
                    poem_links.append({
                        'title': link.get_text(strip=True),
                        'url': poem_url if poem_url.startswith('http') else f"{self.base_url}{poem_url}"
                    })

                    if len(poem_links) >= limit:
                        break

            logger.info(f"Found {len(poem_links)} poem links on poets.org")
            time.sleep(REQUEST_DELAY)
            return poem_links

        except Exception as e:
            logger.error(f"Error searching poets.org: {str(e)}")
            return []

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

    def get_poems(self, limit: int = 50) -> List[Dict]:
        """
        Get a collection of public domain poems from poets.org.

        Args:
            limit: Maximum number of poems to collect

        Returns:
            List of poem dictionaries with full content and metadata
        """
        # Step 1: Find poem links
        poem_links = self.search_public_domain_poems(limit=limit)

        if not poem_links:
            logger.warning("No poem links found on poets.org")
            return []

        # Step 2: Fetch each poem's content
        poems = []
        for i, link in enumerate(poem_links[:limit], 1):
            logger.info(f"[{i}/{min(len(poem_links), limit)}] Fetching: {link['title']}")

            poem = self.get_poem_content(link['url'])
            if poem:
                poems.append(poem)
            else:
                logger.warning(f"Failed to fetch: {link['title']}")

        logger.info(f"Successfully fetched {len(poems)} poems from poets.org")
        return poems
