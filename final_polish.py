#!/usr/bin/env python3
"""
Final polish - fix remaining OCR errors to reach 99%+ quality
"""

import re
from pathlib import Path


def fix_french_accents(text):
    """Fix corrupted French accents where numbers replaced accent marks"""

    # Common French words with accent patterns
    # é (e-acute) was corrupted to 6
    # è (e-grave) was corrupted to 4

    french_fixes = {
        # é -> 6 corruptions
        r'\bB6ranger\b': 'Béranger',
        r'\bR6my\b': 'Rémy',
        r'\bRen6\b': 'René',
        r'\bAndr6\b': 'André',
        r'\bG6rard\b': 'Gérard',
        r'\bMerim6e\b': 'Merimée',
        r'\bF6nelon\b': 'Fénelon',
        r'\bTh6ophile\b': 'Théophile',
        r'\bAcad6mie\b': 'Académie',
        r'\bAcad6mique\b': 'Académique',
        r'\bHelv6tique\b': 'Helvétique',
        r'\bL6gion\b': 'Légion',
        r'\bChr6tienne\b': 'Chrétienne',
        r'\bH6breux\b': 'Hébreux',
        r'\bLittr6\b': 'Littré',

        # Common words with é
        r'\btrouv6\b': 'trouvé',
        r'\bsant6\b': 'santé',
        r'\bint6ressante?\b': 'intéressante',
        r'\bexauc6\b': 'exaucé',
        r'\bet6\b': 'été',
        r'\bbeaut6\b': 'beauté',
        r'\babb6\b': 'abbé',
        r'\baim6\b': 'aimé',
        r'\bamiti6\b': 'amitié',
        r'\bbouch6e\b': 'bouchée',
        r'\bch6ne\b': 'chêne',
        r'\bchang6s\b': 'changés',
        r'\bcharit6\b': 'charité',
        r'\bcouronn6\b': 'couronné',
        r'\bcreus6es\b': 'creusées',
        r'\bdevin6\b': 'deviné',
        r'\bdonn6e\b': 'donnée',
        r'\benvoy6\b': 'envoyé',
        r'\besp6rais\b': 'espérais',
        r'\baccoutum6\b': 'accoutumé',
        r'\bb6nediction\b': 'bénédiction',
        r'\bbord6\b': 'bordé',
        r'\bempi6ter\b': 'empiéter',

        # è -> 4 corruptions
        r'\bMis4rables\b': 'Misérables',
        r'\bMis6rahles\b': 'Misérables',
        r'\bd4ses\b': 'désses',
        r'\bch4re\b': 'chère',
        r'\bembl4me\b': 'emblème',
        r'\bdej4\b': 'déjà',

        # Special cases
        r'\bGeor#\?:e\b': 'George',
        r'\bUAnn4e\b': "L'Année",
        r'\bSociet4\b': 'Société',
        r'\bH6bchette\b': 'Hachette',

        # Patterns: number at end of French word
        r'([a-zé]+)6([se]?s?)(\b|[\s,\.\)])': r'\1é\2\3',
        r'([a-z]+)4([se]?s?)(\b|[\s,\.\)])': r'\1è\2\3',

        # d6 patterns
        r'\bd6\b': 'de',
        r'\bd6faut\b': 'défaut',
        r'\bd6fen\b': 'défen',
        r'\bd6fendre\b': 'défendre',

        # Other corruptions
        r'\bB6q\b': 'Bécq',
        r'\bZfY9\b': '',  # Garbage
        r'\bda3rs\b': 'dans',
        r'\bt8\b': 'té',
        r'\bt4\b': 'té',
        r'\bvJ2\b': '',  # Garbage
        r'\bP8\b': '',  # Garbage
        r'\bb2\b': '',  # Garbage
        r'\bus6\b': 'usé',
        r'\btr6sors\b': 'trésors',
        r'\btouch6e\b': 'touchée',
        r'\btant6t\b': 'tantôt',
        r'\bsup6rieur\b': 'supérieur',
        r'\bsucc6de\b': 'succède',
        r'\by6ritables\b': 'véritables',
        r'\bz6phyr\b': 'zéphyr',
    }

    for pattern, replacement in french_fixes.items():
        text = re.sub(pattern, replacement, text)

    return text


def fix_mixed_case_errors(text):
    """Fix words with incorrect mixed case from OCR"""

    mixed_case_fixes = {
        r'\buporTas\b': 'upon as',
        r'\bdiflScult\b': 'difficult',
        r'\bdifiSculties\b': 'difficulties',
        r'\bdiflSculties\b': 'difficulties',
    }

    for pattern, replacement in mixed_case_fixes.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def fix_common_ocr_errors(text):
    """Fix remaining common OCR errors"""

    ocr_fixes = {
        r'\bwas bom\b': 'was born',
        r'\bwere bom\b': 'were born',
        r'\bbom in\b': 'born in',
        r'\bbom at\b': 'born at',
        r'\bbom on\b': 'born on',

        # h/b confusion
        r'\bI bad\b': 'I had',
        r'\bwe bad\b': 'we had',
        r'\bshe bad\b': 'she had',
        r'\bhe bad\b': 'he had',
        r'\bthey bad\b': 'they had',

        # Punctuation issues
        r'D,D,, LL,D\.': 'D.D., LL.D.',
        r'LL,D\.': 'LL.D.',
        r'D,D\.': 'D.D.',
    }

    for pattern, replacement in ocr_fixes.items():
        text = re.sub(pattern, replacement, text)

    return text


def apply_all_fixes(input_file, output_file):
    """Apply all fixes"""

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print("Applying fixes...")

    # Count before
    french_errors_before = len(re.findall(r'\b[A-Za-z]+[0-9][A-Za-z]*\b', text))
    bom_errors_before = len(re.findall(r'\bwas bom\b', text))
    mixed_case_before = len(re.findall(r'\b(uporTas|diflScult|difiSculties)\b', text))

    # Apply fixes
    text = fix_french_accents(text)
    text = fix_mixed_case_errors(text)
    text = fix_common_ocr_errors(text)

    # Count after
    french_errors_after = len(re.findall(r'\b[A-Za-z]+[0-9][A-Za-z]*\b', text))
    bom_errors_after = len(re.findall(r'\bwas bom\b', text))
    mixed_case_after = len(re.findall(r'\b(uporTas|diflScult|difiSculties)\b', text, re.IGNORECASE))

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\n✓ Fixes applied:")
    print(f"  French accent errors: {french_errors_before} → {french_errors_after} (fixed {french_errors_before - french_errors_after})")
    print(f"  'bom' errors: {bom_errors_before} → {bom_errors_after} (fixed {bom_errors_before - bom_errors_after})")
    print(f"  Mixed-case errors: {mixed_case_before} → {mixed_case_after} (fixed {mixed_case_before - mixed_case_after})")

    total_fixed = (french_errors_before - french_errors_after) + (bom_errors_before - bom_errors_after) + (mixed_case_before - mixed_case_after)
    print(f"\n  Total errors fixed: {total_fixed}")

    return text


def main():
    input_file = '/home/user/poesis/toru_dutt_output/toru_dutt_perfect.md'
    output_file = '/home/user/poesis/toru_dutt_output/toru_dutt_final_polished.md'

    text = apply_all_fixes(input_file, output_file)

    print(f"\n✓ Final polished version saved to:")
    print(f"  {output_file}")
    print(f"  Size: {len(text):,} characters")

    # Estimate quality
    total_words = len(text.split())
    remaining_errors = len(re.findall(r'\b[A-Za-z]+[0-9][A-Za-z]*\b', text))

    error_rate = (remaining_errors / total_words * 100) if total_words > 0 else 0
    estimated_quality = 100 - error_rate

    print(f"\n✓ Quality estimate:")
    print(f"  Total words: ~{total_words:,}")
    print(f"  Remaining suspicious patterns: {remaining_errors}")
    print(f"  Estimated quality: {estimated_quality:.2f}%")

    if estimated_quality >= 99:
        print(f"\n🎉 TARGET ACHIEVED: 99%+ quality!")
    else:
        print(f"\n⚠️  Additional review needed for 99%+")


if __name__ == '__main__':
    main()
