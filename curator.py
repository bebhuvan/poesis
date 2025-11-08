"""Curation and diversity filters for poem selection."""

import logging
from typing import List, Dict, Set, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class PoemCurator:
    """Curates poems to ensure diversity across multiple dimensions."""

    def __init__(self):
        """Initialize curator."""
        self.selected_authors = set()
        self.selected_centuries = defaultdict(int)
        self.stats = {
            'total_processed': 0,
            'total_selected': 0,
            'authors': set(),
            'centuries': defaultdict(int),
            'rejected_reasons': defaultdict(int)
        }

    def get_century(self, year: int) -> Optional[int]:
        """
        Get century from year.

        Args:
            year: Year (e.g., 1821)

        Returns:
            Century (e.g., 19 for 1821), or None if year is None
        """
        if year is None:
            return None
        return (year - 1) // 100 + 1

    def score_poem(self, poem: Dict, public_domain_info: Dict) -> Dict:
        """
        Score a poem for quality and curation value.

        Args:
            poem: Poem dictionary
            public_domain_info: Public domain validation info

        Returns:
            Dictionary with score and scoring details
        """
        score = 0
        details = []

        # Public domain status (critical)
        if not public_domain_info.get('is_public_domain'):
            return {
                'score': -1000,
                'details': ['NOT PUBLIC DOMAIN - REJECTED'],
                'reject': True
            }

        # Has author information
        if poem.get('author') and poem['author'] != 'Unknown':
            score += 20
            details.append('+20: Has author')
        else:
            details.append('0: No author information')

        # Has death year (helps with verification)
        if poem.get('poet_death_year'):
            score += 15
            details.append('+15: Has death year')

        # Has Wikipedia link
        if poem.get('wikipedia_url'):
            score += 10
            details.append('+10: Has Wikipedia link')

        # Text length (prefer substantial poems, not fragments or index pages)
        text_length = len(poem.get('text', ''))
        if text_length > 500:
            score += 15
            details.append('+15: Substantial length')
        elif text_length > 200:
            score += 10
            details.append('+10: Moderate length')
        elif text_length < 100:
            score -= 50
            details.append(f'-50: Too short ({text_length} chars - likely index page or fragment)')
        elif text_length < 150:
            score -= 10
            details.append('-10: Very short')

        # Source URL (critical for non-hallucination)
        if poem.get('source_url'):
            score += 25
            details.append('+25: Has verified source URL')
        else:
            score -= 100
            details.append('-100: NO SOURCE URL')

        return {
            'score': score,
            'details': details,
            'reject': score < 0
        }

    def should_select(self, poem: Dict, max_per_author: int = 3,
                     max_per_century: int = 20) -> Dict:
        """
        Determine if poem should be selected for collection.

        Args:
            poem: Poem dictionary
            max_per_author: Maximum poems per author
            max_per_century: Maximum poems per century

        Returns:
            Dictionary with decision and reason
        """
        author = poem.get('author', 'Unknown')
        death_year = poem.get('poet_death_year')
        century = self.get_century(death_year) if death_year else None

        reasons = []

        # Check author diversity
        author_count = sum(1 for a in self.selected_authors if a == author)
        if author_count >= max_per_author:
            return {
                'select': False,
                'reason': f'Already have {author_count} poems by {author} (max: {max_per_author})'
            }

        # Check century diversity
        if century:
            if self.selected_centuries[century] >= max_per_century:
                return {
                    'select': False,
                    'reason': f'Already have {self.selected_centuries[century]} poems from {century}th century (max: {max_per_century})'
                }
            reasons.append(f'Century {century}th: {self.selected_centuries[century]}/{max_per_century}')

        # Prefer new authors
        if author not in self.selected_authors:
            reasons.append('NEW AUTHOR - preferred')

        return {
            'select': True,
            'reason': '; '.join(reasons) if reasons else 'Meets diversity criteria'
        }

    def mark_selected(self, poem: Dict):
        """
        Mark a poem as selected (updates tracking).

        Args:
            poem: Poem dictionary
        """
        author = poem.get('author', 'Unknown')
        death_year = poem.get('poet_death_year')
        century = self.get_century(death_year) if death_year else None

        self.selected_authors.add(author)
        if century:
            self.selected_centuries[century] += 1

        # Update stats
        self.stats['total_selected'] += 1
        self.stats['authors'].add(author)
        if century:
            self.stats['centuries'][century] += 1

    def filter_and_rank(self, poems: List[Dict], public_domain_results: Dict[str, Dict],
                       target_count: int = 50) -> List[Dict]:
        """
        Filter and rank poems for final selection.

        Args:
            poems: List of poem dictionaries
            public_domain_results: Dictionary mapping poem titles to public domain info
            target_count: Target number of poems to select

        Returns:
            List of selected poems with scores
        """
        scored_poems = []

        for poem in poems:
            self.stats['total_processed'] += 1

            title = poem.get('title')
            pd_info = public_domain_results.get(title, {})

            # Score the poem
            score_result = self.score_poem(poem, pd_info)

            if score_result['reject']:
                reason = score_result['details'][0] if score_result['details'] else 'Low score'
                self.stats['rejected_reasons'][reason] += 1
                logger.debug(f"Rejected: {title} - {reason}")
                continue

            # Check diversity
            diversity_check = self.should_select(poem)

            if not diversity_check['select']:
                self.stats['rejected_reasons'][diversity_check['reason']] += 1
                logger.debug(f"Diversity filter: {title} - {diversity_check['reason']}")
                continue

            scored_poems.append({
                'poem': poem,
                'score': score_result['score'],
                'score_details': score_result['details'],
                'public_domain': pd_info
            })

        # Sort by score (highest first)
        scored_poems.sort(key=lambda x: x['score'], reverse=True)

        # Select top N
        selected = []
        for item in scored_poems:
            if len(selected) >= target_count:
                break

            # Final diversity check
            diversity_check = self.should_select(item['poem'])
            if diversity_check['select']:
                self.mark_selected(item['poem'])
                selected.append(item)
                logger.info(f"✓ SELECTED [{len(selected)}/{target_count}]: {item['poem']['title']} "
                          f"by {item['poem']['author']} (score: {item['score']})")

        return selected

    def print_stats(self):
        """Print curation statistics."""
        logger.info("=" * 60)
        logger.info("CURATION STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Total selected: {self.stats['total_selected']}")
        logger.info(f"Unique authors: {len(self.stats['authors'])}")
        logger.info(f"\nCenturies represented:")
        for century in sorted(self.stats['centuries'].keys()):
            logger.info(f"  {century}th century: {self.stats['centuries'][century]} poems")

        if self.stats['rejected_reasons']:
            logger.info(f"\nRejection reasons:")
            for reason, count in sorted(self.stats['rejected_reasons'].items(),
                                       key=lambda x: x[1], reverse=True):
                logger.info(f"  {reason}: {count}")
        logger.info("=" * 60)
