#!/usr/bin/env python3
"""
Master Pipeline Script
Runs complete extraction, verification, and website generation
"""

import os
import sys
import json
from datetime import datetime


def check_prerequisites():
    """Check if OCR extraction is complete"""
    print("🔍 Checking prerequisites...")

    if not os.path.exists('tagore_full_ocr.json'):
        print("❌ tagore_full_ocr.json not found")
        print("   Please run: python full_ocr_extraction.py")
        return False

    with open('tagore_full_ocr.json', 'r') as f:
        ocr_data = json.load(f)
        pages = len(ocr_data)

        if pages < 200:
            print(f"⚠️  Only {pages}/210 pages extracted")
            print("   OCR extraction may still be running")
            return False

    print(f"✅ OCR complete: {pages} pages")
    return True


def run_multi_strategy_extraction():
    """Run all extraction strategies"""
    print("\n" + "=" * 80)
    print("STEP 1: MULTI-STRATEGY EXTRACTION")
    print("=" * 80)

    import subprocess
    result = subprocess.run(['python', 'multi_strategy_extractor.py'],
                          capture_output=True, text=True)

    print(result.stdout)

    if result.returncode != 0:
        print("❌ Extraction failed")
        print(result.stderr)
        return False

    print("✅ Multi-strategy extraction complete")
    return True


def run_verification():
    """Run verification framework"""
    print("\n" + "=" * 80)
    print("STEP 2: VERIFICATION FRAMEWORK")
    print("=" * 80)

    import subprocess
    result = subprocess.run(['python', 'verification_framework.py'],
                          capture_output=True, text=True)

    print(result.stdout)

    if result.returncode != 0:
        print("❌ Verification failed")
        print(result.stderr)
        return False

    print("✅ Verification complete")
    return True


def generate_website():
    """Generate static website"""
    print("\n" + "=" * 80)
    print("STEP 3: WEBSITE GENERATION")
    print("=" * 80)

    import subprocess
    result = subprocess.run(['python', 'website_generator.py'],
                          capture_output=True, text=True)

    print(result.stdout)

    if result.returncode != 0:
        print("❌ Website generation failed")
        print(result.stderr)
        return False

    print("✅ Website generation complete")
    return True


def generate_summary_report():
    """Generate final summary report"""
    print("\n" + "=" * 80)
    print("FINAL SUMMARY REPORT")
    print("=" * 80)

    try:
        # Load results
        with open('strategy_comparison.json', 'r') as f:
            strategies = json.load(f)

        with open('verification_report.json', 'r') as f:
            verification = json.load(f)

        # Find best strategy
        best_strategy = strategies['strategies'][0]

        print(f"\n📊 EXTRACTION RESULTS")
        print(f"   Best Strategy: {best_strategy['name']}")
        print(f"   Letters Extracted: {best_strategy['letter_count']}")
        print(f"   Average Confidence: {best_strategy['avg_confidence']:.2f}")

        print(f"\n✅ VERIFICATION STATUS")
        print(f"   Overall Status: {verification['summary']['overall_status']}")
        print(f"\n   Individual Checks:")

        for check_name, result in verification['verifications'].items():
            status = result.get('status', 'UNKNOWN')
            emoji = '✅' if status == 'PASS' else '⚠️' if status == 'WARN' else '❌'
            print(f"   {emoji} {check_name}: {status}")

        print(f"\n🌐 WEBSITE")
        print(f"   Location: tagore_website/")
        print(f"   Open: tagore_website/index.html")

        print(f"\n📁 OUTPUT FILES")
        files = [
            ('tagore_full_ocr.json', 'Full OCR text'),
            ('strategy_comparison.json', 'Strategy comparison'),
            ('verification_report.json', 'Verification results'),
            ('tagore_website/', 'Static website'),
        ]

        for filename, description in files:
            exists = '✅' if os.path.exists(filename) else '❌'
            print(f"   {exists} {filename:<30} - {description}")

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'extraction': {
                'best_strategy': best_strategy['name'],
                'letters_extracted': best_strategy['letter_count'],
                'avg_confidence': best_strategy['avg_confidence']
            },
            'verification': {
                'overall_status': verification['summary']['overall_status'],
                'checks': {k: v.get('status', 'UNKNOWN')
                          for k, v in verification['verifications'].items()}
            },
            'website': {
                'generated': os.path.exists('tagore_website/index.html'),
                'location': 'tagore_website/'
            }
        }

        with open('final_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n💾 Summary saved to: final_summary.json")

    except Exception as e:
        print(f"⚠️  Could not generate summary: {e}")


def main():
    print("=" * 80)
    print("TAGORE LETTERS - FULL PIPELINE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please run OCR extraction first.")
        sys.exit(1)

    # Run pipeline
    steps = [
        ("Multi-Strategy Extraction", run_multi_strategy_extraction),
        ("Verification Framework", run_verification),
        ("Website Generation", generate_website),
    ]

    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Pipeline failed at: {step_name}")
            sys.exit(1)

    # Generate summary
    generate_summary_report()

    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Review verification_report.json for quality assessment")
    print("  2. Open tagore_website/index.html in your browser")
    print("  3. Review letters manually if needed")
    print("  4. Push to GitHub or deploy website")
    print("=" * 80)


if __name__ == '__main__':
    main()
