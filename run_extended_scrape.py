#!/usr/bin/env python3
"""
Extended scraping run for poets.org starting from page 51.
This allows us to explore deeper into the poets.org collection.
"""

import sys
from poets_org_scraper import PoetsOrgScraper
from public_domain import PublicDomainValidator
from link_verifier import LinkVerifier
from markdown_generator import MarkdownGenerator
from curator import PoemCurator
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/poets_org_extended_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Run extended scraping starting from page 51.
    """
    logger.info("=" * 60)
    logger.info("POETS.ORG EXTENDED SCRAPER - Pages 51-200")
    logger.info("=" * 60)

    # Initialize components
    scraper = PoetsOrgScraper()
    verifier = LinkVerifier()
    pd_validator = PublicDomainValidator()
    md_generator = MarkdownGenerator()
    curator = PoemCurator()

    # Scrape pages 51-200 (150 pages)
    # Target: 100 PD poems, so fetch 2x for curation = 200 PD poems
    logger.info("Fetching poems from pages 51-200...")
    poems = scraper.get_poems(
        limit=200,  # Target 200 PD poems (will be curated down to ~100)
        max_browse_pages=150,  # Browse 150 pages (51-200)
        start_page=50  # Start from page 51 (0-indexed, so page 50)
    )

    logger.info(f"Fetched {len(poems)} public domain poems")

    if not poems:
        logger.warning("No poems found in this range")
        return

    # Validate public domain status
    logger.info("Validating public domain status...")
    public_domain_results = {}
    for poem in poems:
        pd_result = pd_validator.validate_poem(
            author=poem.get('author', 'Unknown'),
            death_year=poem.get('poet_death_year'),
            publication_year=None,
            source_url=poem.get('source_url'),
            explicit_pd_marker=poem.get('public_domain_confirmed', False)
        )
        public_domain_results[poem['title']] = pd_result

    # Curate for diversity
    logger.info("Curating for diversity...")
    curated_poems = curator.filter_and_rank(poems, public_domain_results, target_count=100)
    logger.info(f"Selected {len(curated_poems)} poems after curation")

    # Save poems
    logger.info("Saving poems as markdown files...")
    saved_count = 0
    for item in curated_poems:
        poem = item['poem']
        pd_status = item['public_domain']

        # Verify links
        verified_links = verifier.verify_poet_links(poem.get('author', ''))

        # Add poets.org source URL
        verified_links['poets_org'] = {
            'url': poem['source_url'],
            'verified': True,
            'verified_at': poem['fetched_at']
        }

        # Generate markdown
        md_generator.save_poem(
            poem,
            verified_links=verified_links,
            public_domain_info=pd_status
        )
        saved_count += 1

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Pages browsed: 51-200")
    logger.info(f"Poems fetched: {len(poems)}")
    logger.info(f"Poems selected: {len(curated_poems)}")
    logger.info(f"Poems saved: {saved_count}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
