#!/usr/bin/env python3
"""Main orchestrator for poetry scraper system."""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path

from config import TARGET_POEMS, LOGS_DIR, OUTPUT_DIR
from wikisource_scraper import WikisourceScraper
from link_verifier import LinkVerifier
from public_domain import PublicDomainValidator
from markdown_generator import MarkdownGenerator
from curator import PoemCurator


def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration.

    Args:
        log_level: Logging level
    """
    # Create logs directory
    Path(LOGS_DIR).mkdir(exist_ok=True)

    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(LOGS_DIR) / f"scraper_{timestamp}.log"

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return log_file


def save_audit_log(audit_data: dict, log_file: Path):
    """
    Save audit log as JSON.

    Args:
        audit_data: Dictionary with audit information
        log_file: Path to save audit log
    """
    audit_file = log_file.parent / f"audit_{log_file.stem}.json"

    with open(audit_file, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2, default=str)

    logging.info(f"Audit log saved to: {audit_file}")


def main(target_count: int = TARGET_POEMS, dry_run: bool = False):
    """
    Main orchestrator function.

    Args:
        target_count: Target number of poems to collect
        dry_run: If True, shows what would be done without saving files
    """
    log_file = setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("POETRY SCRAPER SYSTEM")
    logger.info("=" * 60)
    logger.info(f"Target poems: {target_count}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Dry run: {dry_run}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    # Initialize components
    logger.info("Initializing components...")
    scraper = WikisourceScraper()
    verifier = LinkVerifier()
    pd_validator = PublicDomainValidator()
    md_generator = MarkdownGenerator()
    curator = PoemCurator()

    # Audit trail
    audit_data = {
        'started_at': datetime.utcnow().isoformat(),
        'target_count': target_count,
        'dry_run': dry_run,
        'poems_processed': [],
        'poems_saved': [],
        'errors': []
    }

    try:
        # Step 1: Search for poems
        logger.info(f"\n{'='*60}")
        logger.info("STEP 1: Searching Wikisource for poems...")
        logger.info(f"{'='*60}")

        # Search for more than target to account for filtering
        search_limit = target_count * 5
        poem_candidates = scraper.search_poems(limit=search_limit)

        logger.info(f"Found {len(poem_candidates)} poem candidates")

        # Step 2: Fetch poem content and metadata
        logger.info(f"\n{'='*60}")
        logger.info("STEP 2: Fetching poem content and metadata...")
        logger.info(f"{'='*60}")

        poems_with_metadata = []
        for i, candidate in enumerate(poem_candidates, 1):
            logger.info(f"\n[{i}/{len(poem_candidates)}] Fetching: {candidate['title']}")

            poem = scraper.get_poem_with_metadata(candidate['title'])

            if poem:
                poems_with_metadata.append(poem)
                audit_data['poems_processed'].append({
                    'title': poem['title'],
                    'author': poem.get('author'),
                    'source_url': poem.get('source_url')
                })
            else:
                error = f"Failed to fetch: {candidate['title']}"
                logger.warning(error)
                audit_data['errors'].append(error)

            # Stop if we have enough candidates
            if len(poems_with_metadata) >= target_count * 2:
                logger.info(f"Collected {len(poems_with_metadata)} poems, moving to validation...")
                break

        logger.info(f"\nSuccessfully fetched {len(poems_with_metadata)} poems")

        # Step 3: Validate public domain status
        logger.info(f"\n{'='*60}")
        logger.info("STEP 3: Validating public domain status...")
        logger.info(f"{'='*60}")

        public_domain_results = {}
        for poem in poems_with_metadata:
            pd_result = pd_validator.validate_poem(
                author=poem.get('author', 'Unknown'),
                death_year=poem.get('poet_death_year'),
                publication_year=None,  # Could extract from Wikisource if available
                source_url=poem.get('source_url')  # For Wikisource trust validation
            )
            public_domain_results[poem['title']] = pd_result

        # Step 4: Curate and select poems
        logger.info(f"\n{'='*60}")
        logger.info("STEP 4: Curating and selecting poems...")
        logger.info(f"{'='*60}")

        selected_poems = curator.filter_and_rank(
            poems_with_metadata,
            public_domain_results,
            target_count=target_count
        )

        logger.info(f"\nSelected {len(selected_poems)} poems for collection")

        # Step 5: Verify links and generate markdown
        logger.info(f"\n{'='*60}")
        logger.info("STEP 5: Verifying links and generating markdown...")
        logger.info(f"{'='*60}")

        saved_count = 0
        for i, item in enumerate(selected_poems, 1):
            poem = item['poem']
            logger.info(f"\n[{i}/{len(selected_poems)}] Processing: {poem['title']} by {poem.get('author')}")

            # Verify poet links
            verified_links = verifier.verify_poet_links(poem.get('author', ''))

            # Also verify source URL
            if poem.get('source_url'):
                source_verification = verifier.verify_url(poem['source_url'])
                verified_links['wikisource'] = source_verification

            if dry_run:
                logger.info("  [DRY RUN] Would save poem with:")
                logger.info(f"    Score: {item['score']}")
                logger.info(f"    Verified links: {len([v for v in verified_links.values() if v.get('verified')])}")
                logger.info(f"    Public domain: {item['public_domain'].get('is_public_domain')}")
            else:
                # Save poem as markdown
                saved_path = md_generator.save_poem(
                    poem,
                    verified_links=verified_links,
                    public_domain_info=item['public_domain']
                )

                if saved_path:
                    saved_count += 1
                    audit_data['poems_saved'].append({
                        'title': poem['title'],
                        'author': poem.get('author'),
                        'file_path': saved_path,
                        'score': item['score'],
                        'verified_links': {k: v['verified'] for k, v in verified_links.items()}
                    })

        # Print statistics
        logger.info(f"\n{'='*60}")
        curator.print_stats()

        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Poems searched: {len(poem_candidates)}")
        logger.info(f"Poems fetched: {len(poems_with_metadata)}")
        logger.info(f"Poems selected: {len(selected_poems)}")
        if not dry_run:
            logger.info(f"Poems saved: {saved_count}")
            logger.info(f"Output directory: {OUTPUT_DIR}")
        else:
            logger.info("[DRY RUN] No files were saved")
        logger.info(f"Log file: {log_file}")
        logger.info(f"{'='*60}")

        # Save audit log
        audit_data['completed_at'] = datetime.utcnow().isoformat()
        audit_data['summary'] = {
            'searched': len(poem_candidates),
            'fetched': len(poems_with_metadata),
            'selected': len(selected_poems),
            'saved': saved_count if not dry_run else 0
        }
        save_audit_log(audit_data, log_file)

        return True

    except KeyboardInterrupt:
        logger.warning("\n\nOperation cancelled by user")
        audit_data['status'] = 'cancelled'
        save_audit_log(audit_data, log_file)
        return False

    except Exception as e:
        logger.error(f"\n\nFATAL ERROR: {str(e)}", exc_info=True)
        audit_data['status'] = 'error'
        audit_data['error'] = str(e)
        save_audit_log(audit_data, log_file)
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Poetry scraper and curation system')
    parser.add_argument(
        '--target',
        type=int,
        default=TARGET_POEMS,
        help=f'Target number of poems to collect (default: {TARGET_POEMS})'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without saving files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set log level
    log_level = logging.DEBUG if args.verbose else logging.INFO

    # Run
    success = main(
        target_count=args.target,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)
