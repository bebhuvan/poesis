#!/usr/bin/env python3
"""
Regenerate website using Hybrid Multi-Signal Strategy (49 letters)
instead of Roman Numeral Strategy (10 sections)
"""

import json
import sys
import os

# Import the website generator
sys.path.insert(0, '/home/user/poesis')
from website_generator import WebsiteGenerator


def main():
    print("=" * 80)
    print("REGENERATING WEBSITE WITH HYBRID STRATEGY (49 LETTERS)")
    print("=" * 80)

    # Load strategy comparison
    with open('strategy_comparison.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Find Hybrid Multi-Signal Strategy
    hybrid_strategy = None
    for strategy in data['strategies']:
        if strategy['name'] == 'Hybrid Multi-Signal Strategy':
            hybrid_strategy = strategy
            break

    if not hybrid_strategy:
        print("❌ Hybrid Multi-Signal Strategy not found")
        return

    letters = hybrid_strategy['letters']
    print(f"\n✓ Loaded {len(letters)} letters from Hybrid strategy")
    print(f"  Average words/letter: {sum(l['word_count'] for l in letters) / len(letters):.0f}")
    print(f"  Total words: {sum(l['word_count'] for l in letters):,}")

    # Remove old website
    import shutil
    if os.path.exists('tagore_website'):
        shutil.rmtree('tagore_website')
        print("\n✓ Removed old website")

    # Generate new website
    print("\n📝 Generating website with all 49 letters...")
    generator = WebsiteGenerator(letters, output_dir='tagore_website')
    generator.generate()

    print("\n" + "=" * 80)
    print("✅ WEBSITE REGENERATED!")
    print("=" * 80)
    print(f"Total letters: {len(letters)}")
    print(f"Location: tagore_website/")
    print(f"Open: tagore_website/index.html")
    print("=" * 80)


if __name__ == '__main__':
    main()
