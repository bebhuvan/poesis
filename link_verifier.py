"""Link verification system - ensures all URLs are real and not hallucinated."""

import requests
import logging
from datetime import datetime
from typing import Dict, Optional
import time

from config import HTTP_TIMEOUT, USER_AGENT, REQUEST_DELAY

logger = logging.getLogger(__name__)


class LinkVerifier:
    """Verifies URLs with actual HTTP requests to prevent hallucinated links."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.verified_cache = {}  # Cache to avoid re-verifying same URLs

    def verify_url(self, url: str, cache: bool = True) -> Dict:
        """
        Verify a URL with an actual HTTP request.

        Args:
            url: The URL to verify
            cache: Whether to use/update cache

        Returns:
            Dictionary with verification results:
            {
                'url': str,
                'verified': bool,
                'status_code': int or None,
                'verified_at': str (ISO format),
                'error': str (if any)
            }
        """
        # Check cache first
        if cache and url in self.verified_cache:
            logger.info(f"Using cached verification for {url}")
            return self.verified_cache[url]

        result = {
            'url': url,
            'verified': False,
            'status_code': None,
            'verified_at': datetime.utcnow().isoformat(),
            'error': None
        }

        try:
            logger.info(f"Verifying URL: {url}")
            response = self.session.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)

            result['status_code'] = response.status_code
            result['verified'] = response.status_code == 200

            if result['verified']:
                logger.info(f"✓ URL verified: {url} (status: {response.status_code})")
            else:
                logger.warning(f"✗ URL returned non-200 status: {url} (status: {response.status_code})")
                result['error'] = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"✗ URL verification timeout: {url}")
            result['error'] = "Timeout"

        except requests.exceptions.ConnectionError:
            logger.error(f"✗ URL connection error: {url}")
            result['error'] = "Connection error"

        except Exception as e:
            logger.error(f"✗ URL verification failed: {url} - {str(e)}")
            result['error'] = str(e)

        # Cache the result
        if cache:
            self.verified_cache[url] = result

        # Rate limiting
        time.sleep(REQUEST_DELAY)

        return result

    def verify_multiple(self, urls: list) -> Dict[str, Dict]:
        """
        Verify multiple URLs.

        Args:
            urls: List of URLs to verify

        Returns:
            Dictionary mapping URLs to verification results
        """
        results = {}
        for url in urls:
            if url:  # Skip None or empty strings
                results[url] = self.verify_url(url)
        return results

    def verify_poet_links(self, poet_name: str) -> Dict:
        """
        Verify common poet profile links (Wikipedia, Poetry Foundation).

        Args:
            poet_name: Name of the poet (e.g., "John Keats")

        Returns:
            Dictionary with verified links
        """
        # Generate potential URLs
        name_slug = poet_name.lower().replace(" ", "-")
        name_wiki = poet_name.replace(" ", "_")

        potential_urls = {
            'wikipedia': f"https://en.wikipedia.org/wiki/{name_wiki}",
            'poetry_foundation': f"https://www.poetryfoundation.org/poets/{name_slug}",
        }

        verified_links = {}
        for source, url in potential_urls.items():
            result = self.verify_url(url)
            if result['verified']:
                verified_links[source] = result
            else:
                logger.warning(f"Could not verify {source} link for {poet_name}: {url}")

        return verified_links
