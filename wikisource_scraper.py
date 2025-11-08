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
            skip_patterns = [
                r'/Index$',          # Index pages
                r'/Versions$',       # Version pages
                r'^Index:',          # Index namespace
                r'^Portal:',         # Portal pages
                r'^Category:',       # Category pages
            ]

            if 'query' in data and 'categorymembers' in data['query']:
                for item in data['query']['categorymembers']:
                    title = item['title']

                    # Skip obvious index/metadata pages
                    skip = False
                    for pattern in skip_patterns:
                        if re.search(pattern, title):
                            skip = True
                            logger.debug(f"Skipping index/meta page: {title}")
                            break

                    if not skip:
                        poems.append({
                            'title': title,
                            'pageid': item['pageid']
                        })

            logger.info(f"Found {len(poems)} poems in Wikisource (after filtering)")
            time.sleep(REQUEST_DELAY)
            return poems

        except Exception as e:
            logger.error(f"Error searching Wikisource: {str(e)}")
            return []

    def extract_author_from_path(self, title: str) -> Optional[str]:
        """
        Extract author from collection path like "The Complete Poems of Paul Laurence Dunbar/The Crisis".

        Args:
            title: Page title

        Returns:
            Author name if found in path
        """
        # Well-known poetry collections and their authors
        known_collections = {
            # Kipling
            "A Diversity of Creatures": "Rudyard Kipling",
            "Rudyard Kipling's Verse, Inclusive Edition, 1885-1918": "Rudyard Kipling",

            # Carroll
            "Alice in Wonderland": "Lewis Carroll",
            "Alice's Adventures in Wonderland": "Lewis Carroll",
            "Through the Looking-Glass": "Lewis Carroll",

            # Lear
            "Nonsense Songs, Stories, Botany, and Alphabets": "Edward Lear",
            "A Book of Nonsense": "Edward Lear",

            # Yeats
            "The Wanderings of Oisin and Other Poems": "William Butler Yeats",
            "The Wind Among the Reeds": "William Butler Yeats",
            "Crossways": "William Butler Yeats",

            # American poets
            "Sword Blades and Poppy Seed": "Amy Lowell",
            "Mountain Interval": "Robert Frost",
            "North of Boston": "Robert Frost",
            "A Boy's Will": "Robert Frost",
            "The Black Riders & Other Lines": "Stephen Crane",
            "The Black Riders and Other Lines": "Stephen Crane",
            "The Children of the Night": "Edwin Arlington Robinson",
            "The Inn of Dreams": "Zoe Akins",

            # British poets
            "The Temple: Sacred Poems and Private Ejaculations": "George Herbert",
            "The Bad Child's Book Of Beasts": "Hilaire Belloc",
            "The Ballad of St. Barbara and other verses": "G. K. Chesterton",
            "Bells and Pomegranates": "Robert Browning",
            "Bells and Pomegranates, First Series": "Robert Browning",
            "Bells and Pomegranates, Second Series": "Robert Browning",
            "Prometheus Bound, and other poems": "Elizabeth Barrett Browning",
            "Enamels and Cameos": "Théophile Gautier",

            # Medieval
            "The Book of the Duchess": "Geoffrey Chaucer",
            "The Canterbury Tales": "Geoffrey Chaucer",

            # Australian poets
            "In the Days When the World was Wide and Other Verses": "A. B. Paterson",

            # Blake - multiple notebooks and collections
            "Blake's Notebook": "William Blake",
            "Songs of Innocence and of Experience": "William Blake",
            "Songs of Innocence": "William Blake",
            "Songs of Experience": "William Blake",

            # Paul Laurence Dunbar
            "The Complete Poems of Paul Laurence Dunbar": "Paul Laurence Dunbar",
            "Lyrics of Lowly Life": "Paul Laurence Dunbar",
            "Lyrics of the Hearthside": "Paul Laurence Dunbar",
            "Lyrics of Love and Laughter": "Paul Laurence Dunbar",
            "Lyrics of Sunshine and Shadow": "Paul Laurence Dunbar",
        }

        # Check if title starts with a known collection
        for collection, author in known_collections.items():
            if title.startswith(collection + "/") or title == collection:
                return author

        # Common collection path patterns
        patterns = [
            r'^The Complete Poems of ([^/]+)/',
            r'^Poems \(([^)]+)\)/',
            r'^Works of ([^/]+)/',
            r'^The Poems of ([^/]+)/',
            r'^([^/]+)\'s Poems/',
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                author = match.group(1).strip()
                # Remove year ranges from collection names
                author = re.sub(r'\s*\d{4}(?:-\d{4})?\s*', '', author)
                return author

        return None

    def validate_author_name(self, author: str) -> bool:
        """
        Validate that an extracted author name is reasonable.

        Args:
            author: Potential author name

        Returns:
            True if name seems valid, False otherwise
        """
        if not author or len(author) < 2:
            return False

        # Reject obvious non-names
        invalid_patterns = [
            r'^\d+$',                           # Just numbers like "1", "2"
            r'^(1st|2nd|3rd|\d+th)\s+',        # Version indicators
            r'version',                         # Contains "version"
            r'^(here|there|i |we |you |he |she |it |they )',  # Starts like poem text
            r'buried|lies|died',                # Poem text
            r'^notebook$',                      # "Notebook" alone
            r'shorter|longer|revised',          # Editorial terms
        ]

        author_lower = author.lower()
        for pattern in invalid_patterns:
            if re.search(pattern, author_lower):
                logger.debug(f"Rejected invalid author name: {author}")
                return False

        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', author):
            return False

        # Reject if too long (likely first line of poem)
        if len(author) > 80:
            return False

        return True

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
                # Validate the name
                if self.validate_author_name(potential_author):
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

            # Remove Wikisource-specific navigation and metadata elements
            unwanted_selectors = [
                'script', 'style', 'table',
                '.mw-editsection',           # Edit links
                '.ws-noexport',              # Non-exportable content
                '.headertemplate',           # Header templates
                '.footertemplate',           # Footer templates
                '.navigation',               # Navigation boxes
                '.sister-wikipedia',         # Sister project links
                '.sister-projects',          # Sister project boxes
                '.portal',                   # Portal links
                '.noprint',                  # Non-printable elements
                '.printfooter',              # Print footer
                '.catlinks',                 # Category links
                '#toc',                      # Table of contents
            ]

            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()

            # Also remove elements by tag
            for element in soup.find_all(['script', 'style', 'table', 'sup']):
                element.decompose()

            # Try to find the poem content in specific containers
            # Wikisource often puts poems in divs with class "poem" or in the main content area
            poem_container = None

            # Strategy 1: Look for poem-specific containers
            for selector in ['.poem', '.mw-parser-output > p', '.mw-parser-output']:
                candidates = soup.select(selector)
                if candidates:
                    # Take the largest text block as the poem
                    poem_container = max(candidates, key=lambda x: len(x.get_text()))
                    if len(poem_container.get_text().strip()) > 100:  # Minimum length
                        break

            # Get text content from poem container or full soup
            if poem_container:
                text_content = poem_container.get_text()
            else:
                text_content = soup.get_text()

            # Clean up the text - remove common Wikisource artifacts
            lines = []
            skip_patterns = [
                r'^←.*→$',                      # Navigation arrows
                r'^For works with similar',    # Similar works notice
                r'^Versions of',                # Versions notice
                r'versions? of\s+\w+\s+include', # Version lists
                r'^\d+$',                       # Standalone numbers (page numbers)
                r'^This work',                  # Copyright notices at end
                r'^Public domain',              # Public domain notices
                r'^\s*false\s*$',               # Boolean artifacts
                r'^See also',                   # See also sections
                r'^\[edit\]$',                  # Edit links
                r'^Retrieved from',             # Source attribution
                r'^Categories?:',               # Category listings
                r'in\s+.+\s*\(\d{4}\)\s*$',    # Publication info like "in Poems (1830)"
            ]

            for line in text_content.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Skip lines matching unwanted patterns
                skip = False
                for pattern in skip_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        skip = True
                        break

                if not skip and len(line) > 1:  # Skip single characters
                    lines.append(line)

            poem_text = '\n'.join(lines)

            # If poem is suspiciously short, it might be an index page
            if len(poem_text) < 50:
                logger.warning(f"Poem text very short ({len(poem_text)} chars), might be index page: {title}")


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

            # Look for "Poetry by", "Poems by", "Verse by" patterns
            for pattern in ['Poetry by', 'Poems by', 'Verse by', 'Works of']:
                if pattern in cat_name:
                    author = cat_name.replace('Category:', '').replace(pattern, '').strip()
                    if author:
                        return author

            # Look for author categories with roles
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

        # Strategy 1: Extract from collection path (highest priority for anthology poems)
        author = self.extract_author_from_path(title)

        # Strategy 2: Extract from categories
        if not author:
            author_candidate = self.extract_author_from_categories(content['categories'])
            if author_candidate and self.validate_author_name(author_candidate):
                author = author_candidate

        # Strategy 3: Extract from title (e.g., "Poem Title (Author Name)")
        if not author:
            author = self.extract_author_from_title(title)

        # Strategy 4: Look for author in page properties (if available)
        if not author and 'properties' in content:
            # Some Wikisource pages have author properties
            for prop in content.get('properties', []):
                if 'author' in prop.get('name', '').lower():
                    author_candidate = prop.get('*')
                    if author_candidate and self.validate_author_name(author_candidate):
                        author = author_candidate
                        break

        # Special case handling for known patterns
        if author:
            # Fix "Blake's Notebook" → "William Blake"
            if 'blake' in author.lower() and 'notebook' in author.lower():
                author = "William Blake"
            # Remove trailing descriptors
            author = re.sub(r',\s*(Notebook|tr\.|trans\.).*$', '', author, flags=re.IGNORECASE)
            author = author.strip()

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
