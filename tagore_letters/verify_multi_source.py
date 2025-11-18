#!/usr/bin/env python3
"""
Multi-Source Verification System for Tagore Letters
Compares extractions from different sources to ensure accuracy
"""

import re
from pathlib import Path
import difflib
import hashlib
from collections import defaultdict
import json

class MultiSourceVerifier:
    """Cross-verify letters across multiple extraction sources"""

    def __init__(self):
        self.sources = {
            'djvu': 'tagore_letters_raw.txt',
            'epub': 'epub_extracted_text.txt'
        }
        self.extracted_letters_dir = Path('extracted_letters_thorough')

    def load_source_texts(self):
        """Load all available source texts"""
        texts = {}

        for name, filepath in self.sources.items():
            path = Path(filepath)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    texts[name] = f.read()
                print(f"✓ Loaded {name}: {len(texts[name]):,} chars")
            else:
                print(f"⚠ Missing {name}: {filepath}")

        return texts

    def find_letter_in_source(self, letter_content, source_text, letter_num):
        """Find where this letter appears in the source text"""

        # Clean both for comparison
        clean_letter = re.sub(r'\s+', ' ', letter_content[:500]).strip()
        clean_source = re.sub(r'\s+', ' ', source_text).strip()

        # Try to find first 200 chars of letter
        search_text = clean_letter[:200]

        pos = clean_source.find(search_text)
        if pos == -1:
            # Try with fewer chars
            search_text = clean_letter[:100]
            pos = clean_source.find(search_text)

        if pos != -1:
            # Extract surrounding context
            start = max(0, pos - 100)
            end = min(len(clean_source), pos + 1000)
            return clean_source[start:end]

        return None

    def compare_letter_across_sources(self, letter_num, letter_file):
        """Compare a single letter across all sources"""

        # Load our extracted letter
        with open(letter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract just the letter content (skip frontmatter)
        lines = content.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('**') and ',' in line:
                start_idx = i + 2
                break

        letter_content = '\n'.join(lines[start_idx:]).strip()

        # Get metadata
        date_match = re.search(r'date: "(.*?)"', content)
        location_match = re.search(r'location: "(.*?)"', content)

        date = date_match.group(1) if date_match else "Unknown"
        location = location_match.group(1) if location_match else "Unknown"

        # Compare across sources
        results = {
            'letter_num': letter_num,
            'date': date,
            'location': location,
            'extracted_length': len(letter_content),
            'sources': {}
        }

        # Load sources
        sources = self.load_source_texts()

        for source_name, source_text in sources.items():
            found_text = self.find_letter_in_source(letter_content, source_text, letter_num)

            if found_text:
                # Calculate similarity
                similarity = difflib.SequenceMatcher(
                    None,
                    letter_content[:500],
                    found_text[:500]
                ).ratio()

                results['sources'][source_name] = {
                    'found': True,
                    'similarity': similarity,
                    'context_length': len(found_text)
                }
            else:
                results['sources'][source_name] = {
                    'found': False,
                    'similarity': 0.0
                }

        return results

    def verify_all_letters(self):
        """Verify all extracted letters against sources"""

        print("=" * 80)
        print("MULTI-SOURCE VERIFICATION")
        print("=" * 80)
        print()

        letter_files = sorted(self.extracted_letters_dir.glob('letter_*.md'))

        print(f"Verifying {len(letter_files)} letters...\n")

        all_results = []
        issues = []

        for i, letter_file in enumerate(letter_files, 1):
            result = self.compare_letter_across_sources(i, letter_file)
            all_results.append(result)

            # Check for issues
            djvu_found = result['sources'].get('djvu', {}).get('found', False)
            epub_found = result['sources'].get('epub', {}).get('found', False)

            if not djvu_found or not epub_found:
                issues.append(result)

            # Progress indicator
            if i % 10 == 0:
                print(f"  Verified {i}/{len(letter_files)}...")

        print(f"\n✓ Verified all {len(letter_files)} letters")

        return all_results, issues

    def generate_verification_report(self, results, issues):
        """Generate detailed verification report"""

        print("\n" + "=" * 80)
        print("VERIFICATION REPORT")
        print("=" * 80)

        # Overall statistics
        total = len(results)
        found_in_djvu = sum(1 for r in results if r['sources'].get('djvu', {}).get('found', False))
        found_in_epub = sum(1 for r in results if r['sources'].get('epub', {}).get('found', False))

        print(f"\nTotal letters verified: {total}")
        print(f"Found in DjVu source:    {found_in_djvu} ({found_in_djvu/total*100:.1f}%)")
        print(f"Found in EPUB source:    {found_in_epub} ({found_in_epub/total*100:.1f}%)")

        # Average similarity scores
        djvu_similarities = [r['sources'].get('djvu', {}).get('similarity', 0)
                            for r in results if r['sources'].get('djvu', {}).get('found', False)]
        epub_similarities = [r['sources'].get('epub', {}).get('similarity', 0)
                            for r in results if r['sources'].get('epub', {}).get('found', False)]

        if djvu_similarities:
            avg_djvu = sum(djvu_similarities) / len(djvu_similarities)
            print(f"\nAverage DjVu similarity: {avg_djvu:.2%}")

        if epub_similarities:
            avg_epub = sum(epub_similarities) / len(epub_similarities)
            print(f"Average EPUB similarity: {avg_epub:.2%}")

        # Report issues
        if issues:
            print(f"\n⚠ Found {len(issues)} letters with verification issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"\n  Letter {issue['letter_num']}: {issue['location']}, {issue['date']}")
                for source, data in issue['sources'].items():
                    status = "✓ Found" if data['found'] else "✗ Not found"
                    sim = data.get('similarity', 0)
                    print(f"    {source}: {status} (similarity: {sim:.2%})")
        else:
            print("\n✓ No verification issues found!")

        # Save detailed report
        report_path = Path('verification_report.json')
        with open(report_path, 'w') as f:
            json.dump({
                'summary': {
                    'total_letters': total,
                    'found_in_djvu': found_in_djvu,
                    'found_in_epub': found_in_epub,
                    'avg_djvu_similarity': avg_djvu if djvu_similarities else 0,
                    'avg_epub_similarity': avg_epub if epub_similarities else 0,
                    'issues_count': len(issues)
                },
                'results': results,
                'issues': issues
            }, f, indent=2)

        print(f"\n✓ Detailed report saved: {report_path}")

        return {
            'total': total,
            'verified': total - len(issues),
            'issues': len(issues)
        }


class ManualVerificationSampler:
    """Select representative samples for manual verification"""

    def __init__(self):
        self.letters_dir = Path('extracted_letters_thorough')

    def select_samples(self, strategy='stratified', count=10):
        """Select sample letters for manual verification"""

        print("\n" + "=" * 80)
        print("MANUAL VERIFICATION SAMPLE SELECTION")
        print("=" * 80)
        print()

        letter_files = sorted(self.letters_dir.glob('letter_*.md'))

        if strategy == 'stratified':
            # Select samples across the timeline
            step = len(letter_files) // count
            samples = [letter_files[i * step] for i in range(count)]
        elif strategy == 'random':
            import random
            samples = random.sample(letter_files, count)
        else:  # 'edges'
            # First, last, and middle
            samples = [
                letter_files[0],
                letter_files[len(letter_files) // 4],
                letter_files[len(letter_files) // 2],
                letter_files[len(letter_files) * 3 // 4],
                letter_files[-1]
            ]

        print(f"Selected {len(samples)} letters for manual verification:\n")

        for i, sample in enumerate(samples, 1):
            with open(sample, 'r') as f:
                content = f.read()

            date_match = re.search(r'date: "(.*?)"', content)
            location_match = re.search(r'location: "(.*?)"', content)

            date = date_match.group(1) if date_match else "Unknown"
            location = location_match.group(1) if location_match else "Unknown"

            print(f"{i}. {sample.name}")
            print(f"   {location}, {date}")
            print(f"   File: {sample}")
            print()

        return samples


def main():
    """Run complete verification process"""

    print("=" * 80)
    print("COMPREHENSIVE VERIFICATION PROCESS")
    print("Tagore Letters - Multi-Source Cross-Verification")
    print("=" * 80)
    print()

    # Step 1: Multi-source verification
    print("STEP 1: Multi-Source Automated Verification")
    print("-" * 80)
    verifier = MultiSourceVerifier()
    results, issues = verifier.verify_all_letters()
    summary = verifier.generate_verification_report(results, issues)

    # Step 2: Manual verification samples
    print("\n\nSTEP 2: Manual Verification Sample Selection")
    print("-" * 80)
    sampler = ManualVerificationSampler()
    samples = sampler.select_samples(strategy='stratified', count=10)

    # Final summary
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print(f"""
Automated Verification:
  ✓ {summary['verified']}/{summary['total']} letters verified
  ⚠ {summary['issues']} letters flagged for review

Manual Verification:
  📋 {len(samples)} sample letters selected

Next Steps:
  1. Review verification_report.json for detailed results
  2. Manually check the {len(samples)} sample letters against Archive.org
  3. Investigate any flagged issues
  4. Cross-reference with physical book if available
    """)


if __name__ == '__main__':
    main()
