#!/usr/bin/env python3
"""
ABBYY XML Parser for Historical Letters
Extracts text with confidence scores and formatting from ABBYY FineReader XML
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class CharacterData:
    """Individual character with OCR metadata"""
    char: str
    confidence: int
    left: int
    top: int
    right: int
    bottom: int
    font_family: str
    font_size: str
    word_start: bool
    from_dictionary: bool


@dataclass
class LineData:
    """Text line with characters and metadata"""
    text: str
    characters: List[CharacterData]
    baseline: int
    avg_confidence: float
    left: int
    top: int
    right: int
    bottom: int


@dataclass
class PageData:
    """Page with lines and metadata"""
    page_num: int
    lines: List[LineData]
    width: int
    height: int
    avg_confidence: float


class ABBYYParser:
    """Parser for ABBYY FineReader XML format"""

    def __init__(self, xml_path: str):
        self.xml_path = Path(xml_path)
        self.namespace = {'abbyy': 'http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml'}
        self.pages: List[PageData] = []

    def parse(self) -> List[PageData]:
        """Parse the ABBYY XML file"""
        print(f"Parsing ABBYY XML: {self.xml_path}")

        # Parse XML
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        # Get all pages (strip namespace from search)
        pages = [elem for elem in root if 'page' in elem.tag]
        print(f"Found {len(pages)} pages")

        for page_num, page_elem in enumerate(pages, 1):
            page_data = self._parse_page(page_elem, page_num)
            if page_data:
                self.pages.append(page_data)

            if page_num % 50 == 0:
                print(f"Processed {page_num}/{len(pages)} pages...")

        print(f"Parsing complete! Extracted {len(self.pages)} pages with text")
        return self.pages

    def _parse_page(self, page_elem, page_num: int) -> PageData:
        """Parse a single page"""
        width = int(page_elem.get('width', 0))
        height = int(page_elem.get('height', 0))

        lines = []

        # Find all text blocks (ignore namespace)
        for elem in page_elem.iter():
            if 'block' in elem.tag and elem.get('blockType') == 'Text':
                # Find all lines in this block
                for line_elem in elem.iter():
                    if 'line' in line_elem.tag:
                        line_data = self._parse_line(line_elem)
                        if line_data and line_data.text.strip():
                            lines.append(line_data)

        if not lines:
            return None

        # Calculate average confidence for the page
        avg_conf = sum(line.avg_confidence for line in lines) / len(lines)

        return PageData(
            page_num=page_num,
            lines=lines,
            width=width,
            height=height,
            avg_confidence=avg_conf
        )

    def _parse_line(self, line_elem) -> LineData:
        """Parse a single line"""
        baseline = int(line_elem.get('baseline', 0))
        left = int(line_elem.get('l', 0))
        top = int(line_elem.get('t', 0))
        right = int(line_elem.get('r', 0))
        bottom = int(line_elem.get('b', 0))

        characters = []
        text_parts = []

        # Find formatting elements (ignore namespace)
        for fmt_elem in line_elem.iter():
            if 'formatting' not in fmt_elem.tag:
                continue

            font_family = fmt_elem.get('ff', 'Unknown')
            font_size = fmt_elem.get('fs', '0')

            # Find all character params
            for char_elem in fmt_elem:
                if 'charParams' not in char_elem.tag:
                    continue

                char_text = char_elem.text if char_elem.text else ' '

                char_data = CharacterData(
                    char=char_text,
                    confidence=int(char_elem.get('charConfidence', 0)),
                    left=int(char_elem.get('l', 0)),
                    top=int(char_elem.get('t', 0)),
                    right=int(char_elem.get('r', 0)),
                    bottom=int(char_elem.get('b', 0)),
                    font_family=font_family,
                    font_size=font_size,
                    word_start=char_elem.get('wordStart', 'false') == 'true',
                    from_dictionary=char_elem.get('wordFromDictionary', 'false') == 'true'
                )

                characters.append(char_data)
                text_parts.append(char_text)

        if not characters:
            return None

        text = ''.join(text_parts)
        avg_conf = sum(c.confidence for c in characters) / len(characters)

        return LineData(
            text=text,
            characters=characters,
            baseline=baseline,
            avg_confidence=avg_conf,
            left=left,
            top=top,
            right=right,
            bottom=bottom
        )

    def extract_text(self, min_confidence: float = 0.0) -> str:
        """Extract plain text from all pages"""
        text_parts = []

        for page in self.pages:
            if page.avg_confidence >= min_confidence:
                text_parts.append(f"\n{'='*80}\n")
                text_parts.append(f"PAGE {page.page_num}\n")
                text_parts.append(f"{'='*80}\n\n")

                for line in page.lines:
                    if line.avg_confidence >= min_confidence:
                        text_parts.append(line.text + '\n')

                text_parts.append('\n')

        return ''.join(text_parts)

    def get_low_confidence_regions(self, threshold: float = 30.0) -> List[Dict]:
        """Find regions with low OCR confidence"""
        low_conf_regions = []

        for page in self.pages:
            for line in page.lines:
                if line.avg_confidence < threshold:
                    low_conf_regions.append({
                        'page': page.page_num,
                        'text': line.text,
                        'confidence': line.avg_confidence,
                        'position': f"({line.left}, {line.top})-({line.right}, {line.bottom})"
                    })

        return low_conf_regions

    def save_text(self, output_path: str, min_confidence: float = 0.0):
        """Save extracted text to file"""
        text = self.extract_text(min_confidence)
        Path(output_path).write_text(text, encoding='utf-8')
        print(f"Saved text to: {output_path}")

    def save_confidence_report(self, output_path: str):
        """Save confidence analysis report"""
        report = {
            'total_pages': len(self.pages),
            'avg_confidence': sum(p.avg_confidence for p in self.pages) / len(self.pages) if self.pages else 0,
            'low_confidence_regions': self.get_low_confidence_regions(),
            'page_stats': [
                {
                    'page': p.page_num,
                    'avg_confidence': p.avg_confidence,
                    'line_count': len(p.lines)
                }
                for p in self.pages
            ]
        }

        Path(output_path).write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f"Saved confidence report to: {output_path}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python abbyy_parser.py <abbyy_xml_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    parser = ABBYYParser(xml_file)
    parser.parse()

    # Save outputs
    output_dir = Path(xml_file).parent
    parser.save_text(output_dir / 'abbyy_extracted.txt')
    parser.save_confidence_report(output_dir / 'abbyy_confidence_report.json')

    print("\n" + "="*80)
    print("ABBYY EXTRACTION SUMMARY")
    print("="*80)
    print(f"Total pages: {len(parser.pages)}")
    if parser.pages:
        print(f"Average confidence: {sum(p.avg_confidence for p in parser.pages) / len(parser.pages):.2f}%")
        print(f"Low confidence regions: {len(parser.get_low_confidence_regions())}")
    else:
        print("No pages extracted")
