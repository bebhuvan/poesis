"""Public domain validation based on author death dates."""

import logging
from datetime import datetime
from typing import Optional, Dict

from config import PUBLIC_DOMAIN_THRESHOLD

logger = logging.getLogger(__name__)


class PublicDomainValidator:
    """Validates whether a work is in the public domain based on author death date."""

    def __init__(self, threshold_years: int = PUBLIC_DOMAIN_THRESHOLD):
        """
        Initialize validator.

        Args:
            threshold_years: Years after author death for public domain (default: 70)
        """
        self.threshold_years = threshold_years
        self.current_year = datetime.now().year

    def is_public_domain(self, death_year: Optional[int]) -> Dict:
        """
        Check if a work is in the public domain.

        Args:
            death_year: Year the author died

        Returns:
            Dictionary with validation results:
            {
                'is_public_domain': bool,
                'confidence': str ('high', 'medium', 'low', 'unknown'),
                'years_since_death': int or None,
                'reason': str
            }
        """
        if death_year is None:
            return {
                'is_public_domain': False,
                'confidence': 'unknown',
                'years_since_death': None,
                'reason': 'Author death date unknown - manual verification required'
            }

        years_since_death = self.current_year - death_year

        if years_since_death >= self.threshold_years:
            return {
                'is_public_domain': True,
                'confidence': 'high',
                'years_since_death': years_since_death,
                'reason': f'Author died in {death_year}, {years_since_death} years ago (threshold: {self.threshold_years} years)'
            }
        else:
            return {
                'is_public_domain': False,
                'confidence': 'high',
                'years_since_death': years_since_death,
                'reason': f'Author died in {death_year}, only {years_since_death} years ago (threshold: {self.threshold_years} years)'
            }

    def validate_poem(self, author: str, death_year: Optional[int],
                     publication_year: Optional[int] = None) -> Dict:
        """
        Comprehensive public domain validation for a poem.

        Args:
            author: Author name
            death_year: Year author died
            publication_year: Year poem was published (optional, for additional checks)

        Returns:
            Validation results dictionary
        """
        result = self.is_public_domain(death_year)
        result['author'] = author
        result['death_year'] = death_year
        result['publication_year'] = publication_year

        # Additional check: if publication date is very old, likely public domain
        if publication_year and publication_year < 1928:  # Pre-1928 works generally public domain in US
            result['additional_note'] = f'Published in {publication_year} (pre-1928) - likely public domain in US'

        # Log validation result
        if result['is_public_domain']:
            logger.info(f"✓ PUBLIC DOMAIN: {author} - {result['reason']}")
        else:
            logger.warning(f"✗ NOT PUBLIC DOMAIN: {author} - {result['reason']}")

        return result

    def get_safe_cutoff_year(self) -> int:
        """
        Get the latest death year that guarantees public domain.

        Returns:
            Year (e.g., 1955 for 70-year threshold in 2025)
        """
        return self.current_year - self.threshold_years
