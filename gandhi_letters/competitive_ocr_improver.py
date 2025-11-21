#!/usr/bin/env python3
"""
Competitive OCR Improvement System for Gandhi Letters
Uses multiple OCR strategies and pits them against each other to find the best version
"""

import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from difflib import SequenceMatcher

class CompetitiveOCRImprover:
    def __init__(self):
        self.strategies = {}
        self.letter_boundaries = []
        self.comparison_results = defaultdict(list)

    def load_strategy(self, name: str, file_path: str, parser_func):
        """Load an OCR strategy"""
        print(f"Loading Strategy: {name}...")
        text, confidence_map = parser_func(file_path)
        self.strategies[name] = {
            'text': text,
            'confidence_map': confidence_map,
            'name': name,
            'file': file_path
        }
        print(f"  ✓ Loaded {len(text)} characters")

    def parse_djvu_txt(self, file_path: str) -> Tuple[str, Dict]:
        """Parse DjVu text file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        # No confidence data available
        return text, {}

    def parse_abbyy_xml(self, file_path: str) -> Tuple[str, Dict]:
        """Parse ABBYY FineReader XML with confidence scores"""
        print("  Parsing ABBYY XML (this may take a moment)...")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception as e:
            print(f"  Warning: Could not parse XML: {e}")
            return "", {}

        # ABBYY XML uses namespace
        ns = {'abbyy': 'http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml'}

        text_parts = []
        confidence_map = {}
        char_position = 0

        # Find all charParams elements with namespace
        for page in root.findall('.//abbyy:page', ns):
            for block in page.findall('.//abbyy:block', ns):
                for par in block.findall('.//abbyy:par', ns):
                    for line in par.findall('.//abbyy:line', ns):
                        line_text = []
                        for charparams in line.findall('.//abbyy:charParams', ns):
                            char = charparams.text if charparams.text else ''
                            char_conf = charparams.get('charConfidence', '50')

                            if char and char not in [' ', '\t']:  # Skip pure whitespace
                                line_text.append(char)
                                try:
                                    conf_val = int(char_conf) if char_conf else 50
                                    confidence_map[char_position] = max(0, conf_val)  # Handle -1 values
                                except:
                                    confidence_map[char_position] = 50
                                char_position += 1
                            elif char == ' ':
                                line_text.append(' ')
                                char_position += 1

                        if line_text:
                            text_parts.append(''.join(line_text))
                            text_parts.append('\n')
                            char_position += 1

                    # Paragraph break
                    text_parts.append('\n')
                    char_position += 1

        full_text = ''.join(text_parts)
        print(f"  ✓ Extracted {len(full_text)} characters with confidence scores")

        return full_text, confidence_map

    def compare_strategies_word_level(self) -> Dict:
        """Compare strategies at word level"""
        print("\n" + "="*80)
        print("WORD-LEVEL STRATEGY COMPARISON")
        print("="*80)

        # Get all words from each strategy
        strategy_words = {}
        for name, data in self.strategies.items():
            words = re.findall(r'\b\w+\b', data['text'])
            strategy_words[name] = Counter(words)

        # Find disagreements
        disagreements = []
        all_words = set()
        for words_counter in strategy_words.values():
            all_words.update(words_counter.keys())

        # Analyze each word
        word_analysis = {}
        for word in all_words:
            versions = {}
            for name, words_counter in strategy_words.items():
                if word in words_counter:
                    versions[name] = words_counter[word]

            if len(versions) > 1:
                word_analysis[word] = versions

        return word_analysis

    def find_low_confidence_regions(self, strategy_name: str, threshold: int = 30) -> List[Dict]:
        """Find regions with low OCR confidence"""
        if strategy_name not in self.strategies:
            return []

        strategy = self.strategies[strategy_name]
        confidence_map = strategy['confidence_map']
        text = strategy['text']

        if not confidence_map:
            return []

        low_conf_regions = []
        current_region = None

        for pos in sorted(confidence_map.keys()):
            conf = confidence_map[pos]

            if conf < threshold:
                if current_region is None:
                    current_region = {
                        'start': pos,
                        'end': pos,
                        'min_conf': conf,
                        'avg_conf': conf,
                        'chars': 1
                    }
                else:
                    current_region['end'] = pos
                    current_region['min_conf'] = min(current_region['min_conf'], conf)
                    current_region['avg_conf'] = (current_region['avg_conf'] * current_region['chars'] + conf) / (current_region['chars'] + 1)
                    current_region['chars'] += 1
            else:
                if current_region and current_region['chars'] >= 3:  # At least 3 chars
                    # Extract text
                    start = current_region['start']
                    end = current_region['end'] + 1
                    current_region['text'] = text[start:end] if start < len(text) and end <= len(text) else ''
                    low_conf_regions.append(current_region)
                current_region = None

        return low_conf_regions

    def extract_text_from_xml(self, xml_file: str, output_file: str):
        """Extract clean text from ABBYY XML"""
        text, _ = self.parse_abbyy_xml(xml_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        return len(text)

    def compare_line_by_line(self, strategy1: str, strategy2: str, num_lines: int = 100) -> List[Dict]:
        """Compare two strategies line by line"""
        if strategy1 not in self.strategies or strategy2 not in self.strategies:
            return []

        lines1 = self.strategies[strategy1]['text'].split('\n')
        lines2 = self.strategies[strategy2]['text'].split('\n')

        differences = []
        for i in range(min(len(lines1), len(lines2), num_lines)):
            if lines1[i] != lines2[i]:
                similarity = SequenceMatcher(None, lines1[i], lines2[i]).ratio()
                differences.append({
                    'line_num': i,
                    'strategy1_text': lines1[i],
                    'strategy2_text': lines2[i],
                    'similarity': similarity
                })

        return differences

    def generate_competitive_report(self) -> str:
        """Generate a comprehensive competitive analysis report"""
        report = []
        report.append("="*80)
        report.append("COMPETITIVE OCR ANALYSIS REPORT")
        report.append("Multi-Strategy Comparison for Gandhi Letters")
        report.append("="*80)
        report.append("")

        # Strategy overview
        report.append("## LOADED STRATEGIES")
        report.append("")
        for name, data in self.strategies.items():
            text_len = len(data['text'])
            has_conf = 'Yes' if data['confidence_map'] else 'No'
            avg_conf = 'N/A'
            if data['confidence_map']:
                avg_conf = f"{sum(data['confidence_map'].values()) / len(data['confidence_map']):.1f}%"

            report.append(f"**{name}**")
            report.append(f"  - Text length: {text_len:,} characters")
            report.append(f"  - Has confidence scores: {has_conf}")
            report.append(f"  - Average confidence: {avg_conf}")
            report.append("")

        # Low confidence analysis
        if 'ABBYY FineReader' in self.strategies:
            report.append("## LOW CONFIDENCE REGIONS (ABBYY)")
            report.append("")
            low_conf = self.find_low_confidence_regions('ABBYY FineReader', threshold=30)
            report.append(f"Found {len(low_conf)} low-confidence regions (< 30% confidence)")
            report.append("")

            if low_conf:
                report.append("### Sample Low Confidence Regions (first 20):")
                for region in low_conf[:20]:
                    report.append(f"  Position {region['start']}-{region['end']}: \"{region.get('text', '')[:50]}\"")
                    report.append(f"    Min confidence: {region['min_conf']}%, Avg: {region['avg_conf']:.1f}%")
                report.append("")

        # Line-by-line comparison
        if len(self.strategies) >= 2:
            strat_names = list(self.strategies.keys())
            report.append(f"## LINE-BY-LINE COMPARISON: {strat_names[0]} vs {strat_names[1]}")
            report.append("")

            diffs = self.compare_line_by_line(strat_names[0], strat_names[1], num_lines=200)
            report.append(f"Differences found in first 200 lines: {len(diffs)}")
            report.append("")

            if diffs:
                report.append("### Sample Differences (first 15):")
                for diff in diffs[:15]:
                    report.append(f"  Line {diff['line_num']} (Similarity: {diff['similarity']:.2%}):")
                    report.append(f"    {strat_names[0]}: {diff['strategy1_text'][:70]}")
                    report.append(f"    {strat_names[1]}: {diff['strategy2_text'][:70]}")
                    report.append("")

        return "\n".join(report)

    def create_best_version(self) -> str:
        """Create the best version by combining strategies"""
        print("\n" + "="*80)
        print("CREATING BEST VERSION")
        print("="*80)

        # For now, use ABBYY if available (usually best quality)
        if 'ABBYY FineReader' in self.strategies:
            print("Using ABBYY FineReader as base (highest quality)")
            best_text = self.strategies['ABBYY FineReader']['text']
        elif 'DjVu Text' in self.strategies:
            print("Using DjVu Text as base")
            best_text = self.strategies['DjVu Text']['text']
        else:
            print("Using first available strategy")
            best_text = list(self.strategies.values())[0]['text']

        return best_text


def main():
    print("="*80)
    print("GANDHI LETTERS - COMPETITIVE OCR IMPROVEMENT SYSTEM")
    print("="*80)
    print()

    improver = CompetitiveOCRImprover()

    # Load Strategy 1: DjVu Text (baseline)
    improver.load_strategy(
        'DjVu Text',
        '/home/user/poesis/gandhi_letters/ocr_text.txt',
        improver.parse_djvu_txt
    )

    # Load Strategy 2: ABBYY FineReader (with confidence scores)
    improver.load_strategy(
        'ABBYY FineReader',
        '/home/user/poesis/gandhi_letters/abbyy_ocr.xml',
        improver.parse_abbyy_xml
    )

    # Load Strategy 3: hOCR Text
    improver.load_strategy(
        'hOCR Text',
        '/home/user/poesis/gandhi_letters/hocr_text.txt',
        improver.parse_djvu_txt
    )

    # Generate competitive analysis
    print("\nGenerating competitive analysis report...")
    report = improver.generate_competitive_report()

    # Save report
    with open('/home/user/poesis/gandhi_letters/competitive_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("✓ Report saved to: competitive_analysis.txt")

    # Extract ABBYY text (usually best quality)
    print("\nExtracting text from ABBYY XML...")
    chars = improver.extract_text_from_xml(
        '/home/user/poesis/gandhi_letters/abbyy_ocr.xml',
        '/home/user/poesis/gandhi_letters/abbyy_extracted.txt'
    )
    print(f"✓ Extracted {chars:,} characters to: abbyy_extracted.txt")

    # Create best version
    best_version = improver.create_best_version()
    with open('/home/user/poesis/gandhi_letters/best_combined.txt', 'w', encoding='utf-8') as f:
        f.write(best_version)
    print(f"✓ Best version saved to: best_combined.txt ({len(best_version):,} characters)")

    print("\n" + "="*80)
    print("COMPETITIVE ANALYSIS COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Review competitive_analysis.txt to see differences")
    print("2. Use best_combined.txt as the base for letter extraction")
    print("3. Apply iterative improvements based on low-confidence regions")


if __name__ == '__main__':
    main()
