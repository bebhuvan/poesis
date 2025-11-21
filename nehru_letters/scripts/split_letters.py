#!/usr/bin/env python3
"""
Split the combined book text into individual letters.
Detect letter boundaries intelligently.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
import json

@dataclass
class Letter:
    """Represents a single letter."""
    number: int
    title: str
    content: str
    start_page: int
    end_page: int
    date: str = ""
    recipient: str = "Indira"  # Default recipient
    author: str = "Jawaharlal Nehru"


class LetterSplitter:
    """Split book into individual letters."""
    
    def __init__(self):
        self.letters: List[Letter] = []
    
    def split(self, text: str, pages_text: Dict[int, str]) -> List[Letter]:
        """
        Split combined text into individual letters.
        
        Args:
            text: Combined text of all pages
            pages_text: Dict mapping page number to its text
        
        Returns:
            List of Letter objects
        """
        # Find letter boundaries
        boundaries = self._find_letter_boundaries(text)
        
        # Extract letters
        for i, (start, end, title) in enumerate(boundaries):
            # Get the letter content
            content = text[start:end].strip()
            
            # Find which pages this letter spans
            start_page, end_page = self._find_page_range(content, pages_text)
            
            # Try to extract date
            date = self._extract_date(content)
            
            letter = Letter(
                number=i + 1,
                title=title,
                content=content,
                start_page=start_page,
                end_page=end_page,
                date=date
            )
            
            self.letters.append(letter)
        
        return self.letters
    
    def _find_letter_boundaries(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Find boundaries of letters in the text.
        
        Returns list of (start_pos, end_pos, title) tuples.
        """
        boundaries = []
        
        # Look for letter numbers/titles
        # Patterns:
        # - "I" "II" "III" etc. at start of line
        # - Titles like "THE BOOK OF NATURE" in all caps
        # - Chapter-like breaks
        
        # Find potential boundaries
        lines = text.split('\n')
        positions = []
        
        for i, line in enumerate(lines):
            # Check for Roman numerals at start of line
            if re.match(r'^\s*[IVX]+\s*$', line.strip()):
                positions.append(i)
            
            # Check for all-caps titles (likely chapter/letter titles)
            elif re.match(r'^[A-Z\s]{10,}$', line.strip()) and len(line.strip()) > 10:
                positions.append(i)
            
            # Check for "LETTER" keyword
            elif re.search(r'\bLETTER\b', line, re.IGNORECASE):
                positions.append(i)
        
        # If we found very few boundaries, use a different strategy
        if len(positions) < 5:
            # Look for section breaks (multiple newlines)
            # This suggests chapters/letters separated by blank lines
            sections = re.split(r'\n{3,}', text)
            
            current_pos = 0
            for section in sections:
                if len(section.strip()) > 200:  # Meaningful content
                    # Extract title from first line
                    first_line = section.strip().split('\n')[0]
                    title = first_line[:50]
                    
                    boundaries.append((
                        current_pos,
                        current_pos + len(section),
                        title
                    ))
                
                current_pos += len(section) + 3  # +3 for the newlines
        else:
            # Use the found positions
            for i in range(len(positions)):
                start_line = positions[i]
                end_line = positions[i+1] if i+1 < len(positions) else len(lines)
                
                # Get char positions
                start_pos = sum(len(lines[j]) + 1 for j in range(start_line))
                end_pos = sum(len(lines[j]) + 1 for j in range(end_line))
                
                # Title is the boundary line itself
                title = lines[start_line].strip()
                
                boundaries.append((start_pos, end_pos, title))
        
        return boundaries
    
    def _find_page_range(self, content: str, pages_text: Dict[int, str]) -> Tuple[int, int]:
        """Find which pages a letter spans."""
        # Simple approach: find first and last page that contains content from this letter
        first_page = None
        last_page = None
        
        # Get first few words of content
        words = content.split()[:10]
        first_snippet = ' '.join(words)
        
        # Get last few words
        last_snippet = ' '.join(words[-10:])
        
        for page_num, page_text in sorted(pages_text.items()):
            if first_page is None and first_snippet[:30] in page_text:
                first_page = page_num
            
            if last_snippet[:30] in page_text:
                last_page = page_num
        
        return first_page or 0, last_page or 0
    
    def _extract_date(self, content: str) -> str:
        """Try to extract date from letter content."""
        # Look for date patterns
        date_patterns = [
            r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def save_letters(self, output_dir: Path):
        """Save individual letters to files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = []
        
        for letter in self.letters:
            # Create filename
            filename = f"letter_{letter.number:03d}_{letter.title[:30].replace(' ', '_').lower()}.md"
            filename = re.sub(r'[^\w\-_\.]', '', filename)
            
            # Create markdown with frontmatter
            md_content = f"""---
letter_number: {letter.number}
title: "{letter.title}"
author: "{letter.author}"
recipient: "{letter.recipient}"
date: "{letter.date}"
pages: [{letter.start_page}, {letter.end_page}]
---

# {letter.title}

{letter.content}
"""
            
            # Save file
            filepath = output_dir / filename
            filepath.write_text(md_content)
            
            # Add to metadata
            metadata.append({
                'number': letter.number,
                'title': letter.title,
                'filename': filename,
                'pages': [letter.start_page, letter.end_page],
                'date': letter.date,
                'word_count': len(letter.content.split())
            })
        
        # Save metadata index
        index_file = output_dir / "letters_index.json"
        index_file.write_text(json.dumps(metadata, indent=2))
        
        print(f"\nSaved {len(self.letters)} letters to {output_dir}")
        print(f"Index: {index_file}")


def main():
    """Main entry point."""
    # This will be called after all pages are processed
    print("Letter splitting will run after page processing completes")


if __name__ == "__main__":
    main()
