"""Markdown generator for poems with YAML front matter."""

import os
import yaml
import logging
import re
from typing import Dict, Optional
from datetime import datetime

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """Generates clean markdown files for poems with rich YAML front matter."""

    def __init__(self, output_dir: str = OUTPUT_DIR):
        """
        Initialize generator.

        Args:
            output_dir: Directory to save markdown files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def slugify(self, text: str) -> str:
        """
        Convert text to URL-friendly slug.

        Args:
            text: Text to slugify

        Returns:
            Slugified text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r'[^\w\s-]', '', text)

        # Replace spaces with hyphens
        text = re.sub(r'[\s_]+', '-', text)

        # Remove consecutive hyphens
        text = re.sub(r'-+', '-', text)

        # Remove leading/trailing hyphens
        text = text.strip('-')

        return text

    def generate_filename(self, title: str, author: str) -> str:
        """
        Generate a clean filename for the poem.

        Args:
            title: Poem title
            author: Author name

        Returns:
            Filename (with .md extension)
        """
        # Create slug from title
        title_slug = self.slugify(title)
        author_slug = self.slugify(author)

        # Combine author and title
        filename = f"{author_slug}_{title_slug}.md"

        # Truncate if too long
        if len(filename) > 200:
            filename = filename[:200] + ".md"

        return filename

    def create_front_matter(self, poem: Dict, verified_links: Optional[Dict] = None,
                           public_domain_info: Optional[Dict] = None) -> Dict:
        """
        Create YAML front matter dictionary.

        Args:
            poem: Poem dictionary with metadata
            verified_links: Dictionary of verified links
            public_domain_info: Public domain validation info

        Returns:
            Front matter dictionary
        """
        front_matter = {
            'title': poem.get('title', 'Untitled'),
            'author': poem.get('author', 'Unknown'),
        }

        # Add dates if available
        if poem.get('poet_birth_year'):
            front_matter['author_birth_year'] = poem['poet_birth_year']
        if poem.get('poet_death_year'):
            front_matter['author_death_year'] = poem['poet_death_year']

        # Add source information (CRITICAL: prevents hallucination)
        front_matter['source'] = {
            'url': poem.get('source_url'),
            'fetched_at': poem.get('fetched_at'),
            'content_hash': poem.get('content_hash')
        }

        # Add verified links
        if verified_links:
            links = {}
            for source, info in verified_links.items():
                if info.get('verified'):
                    links[source] = {
                        'url': info['url'],
                        'verified': True,
                        'verified_at': info['verified_at']
                    }
            if links:
                front_matter['links'] = links

        # Add public domain status
        if public_domain_info:
            front_matter['public_domain'] = {
                'status': public_domain_info.get('is_public_domain'),
                'confidence': public_domain_info.get('confidence'),
                'reason': public_domain_info.get('reason')
            }

        # Add metadata timestamp
        front_matter['generated_at'] = datetime.utcnow().isoformat()

        return front_matter

    def format_poem_text(self, text: str) -> str:
        """
        Format poem text for markdown.

        Args:
            text: Raw poem text

        Returns:
            Formatted poem text
        """
        # Clean up extra whitespace
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            # Preserve intentional indentation, but clean up
            cleaned = line.rstrip()
            formatted_lines.append(cleaned)

        # Join lines and ensure proper spacing
        formatted_text = '\n'.join(formatted_lines)

        # Remove excessive blank lines (more than 2 consecutive)
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)

        return formatted_text.strip()

    def generate_markdown(self, poem: Dict, verified_links: Optional[Dict] = None,
                         public_domain_info: Optional[Dict] = None) -> str:
        """
        Generate complete markdown content.

        Args:
            poem: Poem dictionary
            verified_links: Verified links dictionary
            public_domain_info: Public domain validation info

        Returns:
            Complete markdown content as string
        """
        # Create front matter
        front_matter = self.create_front_matter(poem, verified_links, public_domain_info)

        # Format poem text
        poem_text = self.format_poem_text(poem.get('text', ''))

        # Build markdown content
        markdown_parts = [
            '---',
            yaml.dump(front_matter, default_flow_style=False, allow_unicode=True, sort_keys=False).strip(),
            '---',
            '',
            poem_text,
            ''
        ]

        return '\n'.join(markdown_parts)

    def save_poem(self, poem: Dict, verified_links: Optional[Dict] = None,
                  public_domain_info: Optional[Dict] = None) -> Optional[str]:
        """
        Save poem as markdown file.

        Args:
            poem: Poem dictionary
            verified_links: Verified links dictionary
            public_domain_info: Public domain validation info

        Returns:
            Path to saved file, or None if error
        """
        try:
            # Generate filename
            filename = self.generate_filename(
                poem.get('title', 'untitled'),
                poem.get('author', 'unknown')
            )

            filepath = os.path.join(self.output_dir, filename)

            # Generate markdown content
            content = self.generate_markdown(poem, verified_links, public_domain_info)

            # Save file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"✓ Saved poem to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving poem {poem.get('title')}: {str(e)}")
            return None
