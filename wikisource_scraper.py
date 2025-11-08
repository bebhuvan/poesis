"""Wikisource scraper using the MediaWiki API."""

import requests
import logging
import time
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

from config import WIKISOURCE_API_BASE, USER_AGENT, REQUEST_DELAY, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


class WikisourceScraper:
    """Scraper for Wikisource using MediaWiki API."""

    def __init__(self, api_base: str = WIKISOURCE_API_BASE):
        """
        Initialize scraper.

        Args:
            api_base: Base URL for Wikisource API
        """
        self.api_base = api_base
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})

    def search_poems(self, limit: int = 100) -> List[Dict]:
        """
        Search for poems in Wikisource.

        Args:
            limit: Maximum number of results

        Returns:
            List of poem metadata dictionaries
        """
        logger.info(f"Searching Wikisource for poems (limit: {limit})")

        # Search in Category:Poems to find poetry pages
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': 'Category:Poems',
            'cmlimit': limit,
            'format': 'json'
        }

        try:
            response = self.session.get(
                self.api_base,
                params=params,
                timeout=HTTP_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            poems = []
            if 'query' in data and 'categorymembers' in data['query']:
                for item in data['query']['categorymembers']:
                    poems.append({
                        'title': item['title'],
                        'pageid': item['pageid']
                    })

            logger.info(f"Found {len(poems)} poems in Wikisource")
            time.sleep(REQUEST_DELAY)
            return poems

        except Exception as e:
            logger.error(f"Error searching Wikisource: {str(e)}")
            return []

    def extract_author_from_title(self, title: str) -> Optional[str]:
        """
        Extract author from title if present in parentheses.

        Args:
            title: Page title (e.g., "Adeline (Tennyson)")

        Returns:
            Author name if found
        """
        # Look for author in parentheses at end of title
        match = re.search(r'\(([^)]+)\)\s*$', title)
        if match:
            potential_author = match.group(1)
            # Filter out things that aren't likely author names
            if not any(word in potential_author.lower() for word in ['poem', 'song', 'verse', 'excerpt']):
                return potential_author
        return None

    def get_page_content(self, title: str) -> Optional[Dict]:
        """
        Get the full content of a Wikisource page.

        Args:
            title: Page title

        Returns:
            Dictionary with page content and metadata, or None if error
        """
        logger.info(f"Fetching content for: {title}")

        params = {
            'action': 'parse',
            'page': title,
            'format': 'json',
            'prop': 'text|wikitext|categories|properties'
        }

        try:
            response = self.session.get(
                self.api_base,
                params=params,
                timeout=HTTP_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if 'parse' not in data:
                logger.warning(f"No parse data for {title}")
                return None

            parse_data = data['parse']

            # Extract clean text from HTML
            html_content = parse_data.get('text', {}).get('*', '')
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'table']):
                element.decompose()

            # Get text content
            text_content = soup.get_text()

            # Clean up the text
            lines = [line.strip() for line in text_content.split('\n')]
            clean_lines = [line for line in lines if line]
            poem_text = '\n'.join(clean_lines)

            # Get categories
            categories = [cat for cat in parse_data.get('categories', [])]

            # Get properties (if available)
            properties = parse_data.get('properties', [])

            # Create source URL
            source_url = f"https://en.wikisource.org/wiki/{title.replace(' ', '_')}"

            # Generate content hash for verification
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()[:16]

            result = {
                'title': title,
                'text': poem_text,
                'wikitext': parse_data.get('wikitext', {}).get('*', ''),
                'categories': categories,
                'properties': properties,
                'source_url': source_url,
                'fetched_at': datetime.utcnow().isoformat(),
                'content_hash': content_hash
            }

            logger.info(f"✓ Successfully fetched: {title}")
            time.sleep(REQUEST_DELAY)
            return result

        except Exception as e:
            logger.error(f"Error fetching {title}: {str(e)}")
            return None

    def extract_author_from_categories(self, categories: List) -> Optional[str]:
        """
        Extract author name from Wikisource categories.

        Args:
            categories: List of category dictionaries

        Returns:
            Author name if found, None otherwise
        """
        for cat in categories:
            cat_name = cat.get('*', '') if isinstance(cat, dict) else str(cat)

            # Look for patterns like "Category:Works by Author Name"
            if 'Works by' in cat_name:
                author = cat_name.replace('Category:', '').replace('Works by', '').strip()
                return author

            # Look for author categories
            if 'Category:' in cat_name and any(word in cat_name for word in ['Poet', 'Author', 'Writer']):
                author = cat_name.replace('Category:', '').strip()
                for word in ['Poet', 'Author', 'Writer']:
                    author = author.replace(word, '').strip()
                if author:
                    return author

        return None

    def get_poet_info_from_wikidata(self, poet_name: str) -> Optional[Dict]:
        """
        Get poet information from Wikidata (more reliable for dates).

        Args:
            poet_name: Name of the poet

        Returns:
            Dictionary with birth_year, death_year, wikidata_id
        """
        logger.info(f"Querying Wikidata for: {poet_name}")

        # Step 1: Search Wikidata for the entity
        search_url = "https://www.wikidata.org/w/api.php"
        search_params = {
            'action': 'wbsearchentities',
            'search': poet_name,
            'language': 'en',
            'format': 'json',
            'type': 'item',
            'limit': 5
        }

        try:
            response = self.session.get(search_url, params=search_params, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if 'search' not in data or not data['search']:
                logger.warning(f"No Wikidata results for {poet_name}")
                return None

            # Find the best match (prefer items with "poet" or "writer" in description)
            best_match = None
            for item in data['search']:
                description = item.get('description', '').lower()
                if any(word in description for word in ['poet', 'writer', 'author', 'playwright']):
                    best_match = item
                    break

            # If no poet found, just use first result
            if not best_match and data['search']:
                best_match = data['search'][0]

            if not best_match:
                return None

            entity_id = best_match['id']
            logger.info(f"Found Wikidata entity: {entity_id} - {best_match.get('label')}")

            # Step 2: Get entity data with birth/death dates
            entity_url = "https://www.wikidata.org/w/api.php"
            entity_params = {
                'action': 'wbgetentities',
                'ids': entity_id,
                'format': 'json',
                'props': 'claims'
            }

            time.sleep(REQUEST_DELAY)
            response = self.session.get(entity_url, params=entity_params, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            entity_data = response.json()

            if 'entities' not in entity_data or entity_id not in entity_data['entities']:
                return None

            claims = entity_data['entities'][entity_id].get('claims', {})

            # Extract birth date (P569) and death date (P570)
            birth_year = None
            death_year = None

            # Birth date
            if 'P569' in claims and claims['P569']:
                birth_claim = claims['P569'][0]
                birth_value = birth_claim.get('mainsnak', {}).get('datavalue', {}).get('value', {})
                if 'time' in birth_value:
                    # Format: +1795-00-00T00:00:00Z
                    birth_time = birth_value['time']
                    match = re.search(r'[+-](\d{4})', birth_time)
                    if match:
                        birth_year = int(match.group(1))

            # Death date
            if 'P570' in claims and claims['P570']:
                death_claim = claims['P570'][0]
                death_value = death_claim.get('mainsnak', {}).get('datavalue', {}).get('value', {})
                if 'time' in death_value:
                    death_time = death_value['time']
                    match = re.search(r'[+-](\d{4})', death_time)
                    if match:
                        death_year = int(match.group(1))

            if birth_year or death_year:
                logger.info(f"✓ Wikidata: {poet_name} ({birth_year}–{death_year})")

            result = {
                'name': poet_name,
                'birth_year': birth_year,
                'death_year': death_year,
                'wikidata_id': entity_id,
                'wikidata_label': best_match.get('label')
            }

            time.sleep(REQUEST_DELAY)
            return result

        except Exception as e:
            logger.error(f"Error fetching from Wikidata for {poet_name}: {str(e)}")
            return None

    def get_poet_info(self, poet_name: str) -> Optional[Dict]:
        """
        Get comprehensive poet information using Wikidata + Wikipedia.

        Args:
            poet_name: Name of the poet

        Returns:
            Dictionary with poet information including birth/death years
        """
        logger.info(f"Fetching poet info for: {poet_name}")

        # Primary: Get structured data from Wikidata
        wikidata_info = self.get_poet_info_from_wikidata(poet_name)

        # Secondary: Get bio text from Wikipedia
        wiki_api = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'titles': poet_name,
            'prop': 'extracts',
            'exintro': True,
            'explaintext': True,
            'format': 'json'
        }

        wikipedia_extract = None
        try:
            response = self.session.get(wiki_api, params=params, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            if pages:
                page = next(iter(pages.values()))
                if not page.get('missing'):
                    wikipedia_extract = page.get('extract', '')[:500]

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            logger.warning(f"Could not fetch Wikipedia bio for {poet_name}: {str(e)}")

        # Combine results
        if wikidata_info:
            result = {
                'name': poet_name,
                'birth_year': wikidata_info.get('birth_year'),
                'death_year': wikidata_info.get('death_year'),
                'wikidata_id': wikidata_info.get('wikidata_id'),
                'extract': wikipedia_extract,
                'wikipedia_url': f"https://en.wikipedia.org/wiki/{poet_name.replace(' ', '_')}"
            }
            return result
        elif wikipedia_extract:
            # Fallback: Try to extract dates from Wikipedia text
            date_pattern = r'\b(\d{4})\s*[–-]\s*(\d{4})\b'
            match = re.search(date_pattern, wikipedia_extract)

            birth_year = None
            death_year = None

            if match:
                birth_year = int(match.group(1))
                death_year = int(match.group(2))
                logger.info(f"Extracted dates from Wikipedia for {poet_name}: {birth_year}–{death_year}")

            return {
                'name': poet_name,
                'birth_year': birth_year,
                'death_year': death_year,
                'extract': wikipedia_extract,
                'wikipedia_url': f"https://en.wikipedia.org/wiki/{poet_name.replace(' ', '_')}"
            }

        logger.warning(f"Could not find poet info for {poet_name}")
        return None

    def get_poem_with_metadata(self, title: str) -> Optional[Dict]:
        """
        Get a complete poem with all metadata.

        Args:
            title: Poem title

        Returns:
            Complete poem dictionary with all metadata
        """
        # Get page content
        content = self.get_page_content(title)
        if not content:
            return None

        # Try multiple strategies to extract author
        author = None

        # Strategy 1: Extract from categories
        author = self.extract_author_from_categories(content['categories'])

        # Strategy 2: Extract from title (e.g., "Poem Title (Author Name)")
        if not author:
            author = self.extract_author_from_title(title)

        # Strategy 3: Look for author in page properties (if available)
        if not author and 'properties' in content:
            # Some Wikisource pages have author properties
            for prop in content.get('properties', []):
                if 'author' in prop.get('name', '').lower():
                    author = prop.get('*')
                    break

        # Get poet information
        poet_info = None
        if author:
            logger.info(f"Found author: {author}")
            poet_info = self.get_poet_info(author)

        # Combine everything
        poem = {
            'title': content['title'],
            'text': content['text'],
            'author': author or 'Unknown',
            'source_url': content['source_url'],
            'fetched_at': content['fetched_at'],
            'content_hash': content['content_hash'],
            'categories': content['categories']
        }

        # Add poet info if available
        if poet_info:
            poem['poet_birth_year'] = poet_info.get('birth_year')
            poem['poet_death_year'] = poet_info.get('death_year')
            poem['poet_bio'] = poet_info.get('extract')
            poem['wikipedia_url'] = poet_info.get('wikipedia_url')
            poem['wikidata_id'] = poet_info.get('wikidata_id')

        return poem
