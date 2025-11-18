#!/usr/bin/env python3
"""
Fix remaining OCR errors found in manual review.
"""

import re
from pathlib import Path


def fix_letter_content(content: str, letter_num: int) -> str:
    """Apply letter-specific fixes"""

    # Common fixes for all letters
    fixes = [
        # Character-level OCR errors
        (r'\bwc\b', 'we'),
        (r'\bwilt\b', 'will'),
        (r'\bEnd\b', 'find'),
        (r'\banci\b', 'and'),
        (r'\btlie\b', 'the'),
        (r'\btiie\b', 'the'),
        (r'\bthc\b', 'the'),
        (r'\bBbojpatra\b', 'Bhojpatra'),
        (r'\bmahant\b', 'mahout'),
        (r'walnut I\nsitting', 'mahout\nsitting'),
        (r' oft"', ' off'),
        (r'how to-\ngrow', 'how to\ngrow'),

        # Remove stray characters and artifacts
        (r'\bc y\s*\n', '\n'),
        (r'\[\s*\d+\s*\]\s*\n', '\n'),  # Page numbers like [ 64 ]

        # Fix spacing issues
        (r'atten-\s*\n\s*tion', 'attention'),
        (r'be-\s*\n\s*cause', 'because'),
        (r'there-\s*\n\s*fore', 'therefore'),

        # Remove multiple blank lines (keep max 2)
        (r'\n\n\n+', '\n\n'),
    ]

    result = content
    for pattern, replacement in fixes:
        result = re.sub(pattern, replacement, result)

    # Letter-specific fixes
    if letter_num == 1:
        # Fix missing opening
        if result.startswith('# Letter 1: The Book of Nature\n\n. This book'):
            # Need to add the opening paragraph
            opening = """# Letter 1: The Book of Nature

When you and I are together you often ask me questions about many things and I try to answer them. Now that you are at Mussoorie and I am in Allahabad we cannot have these talks. I am therefore going to write to you from time to time short accounts of the story of our earth and the many countries, great and small, in which it is divided. You have read a little about English history and Indian history. But England is only a little island and India, though a big country, is only a small part of the earth's surface. If we want to know something about the story of this world of ours we must think of all the countries and all the peoples that have inhabited it, and not merely of one little country where we may have been born.

I am afraid I can only tell you very little in these letters of mine. But that little, I hope, will interest you and make you think of the world as a whole, and of other peoples in it as our brothers and sisters. When you grow up you will read about the story of the earth and her peoples in fat books and you will find it more interesting than any other story or novel that you may have read.

You know of course that our earth is very, very old — millions and millions of years old. And for a long long time there were no men or women living in it. Before the men came there were only animals, and before the animals there was a time when no kind of life existed on the earth. It is difficult to imagine this world of ours, which is so full today of all kinds of animals and men, to be without them. But scientists and those who have studied and thought a great deal about these matters tell us that there was a time when the earth was too hot for any living being to live on it. And if we read their books and study the rocks and the fossils (the remains of old animals) we can ourselves see that this must have been so.

You read history in books. But in old times when men did not exist surely no books could have been written. How then can we find out what happened then? We cannot merely sit down and imagine everything. This would be very interesting for we could imagine anything we wanted to and would thus make up the most beautiful fairy tales. But this need not be true as it would not be based on any facts that we had seen. But although we have no books written in those far off days, fortunately we have some things which tell us a great deal as well almost as a book would. We have rocks and mountains and seas and stars and rivers and deserts and fossils of old animals. These and other like things are our books for the earth's early story. And the real way to understand this story is not merely to read about it in other people's books but to go to the great Book of Nature itself. You will I hope soon begin to learn how to read this story from the rocks and mountains. Imagine how fascinating it is! Every little stone that you see lying in the road or on the mountain side may be a little page in nature's book and may be able to tell you something if you only knew how to read it. To be able to read any language, Hindi or Urdu or English you have to learn its alphabet. So also you must learn the alphabet of nature before you can read her story in her books of stone and rock. Even now perhaps you know a little how to read this"""

            # Find where current content should continue
            match = re.search(r'This book consists', result)
            if match:
                result = opening + ". " + result[match.start():]

    if letter_num == 15:
        # Remove image caption that got mixed in
        result = re.sub(r'Tur, Mammoth.*?Elephant\s*\n+', '\n\n', result, flags=re.DOTALL)

    return result


def main():
    """Apply fixes to all letters"""

    base_dir = Path(__file__).parent
    letters_dir = base_dir / "final_letters/jawaharlal_nehru_1929"

    print("=" * 80)
    print("APPLYING OCR CORRECTIONS")
    print("=" * 80)

    fixed_count = 0

    for letter_file in sorted(letters_dir.glob("letter-*.md")):
        # Extract letter number
        match = re.search(r'letter-(\d+)-', letter_file.name)
        if not match:
            continue

        letter_num = int(match.group(1))

        # Read content
        content = letter_file.read_text(encoding='utf-8')
        original_content = content

        # Apply fixes
        fixed_content = fix_letter_content(content, letter_num)

        # Write back if changed
        if fixed_content != original_content:
            letter_file.write_text(fixed_content, encoding='utf-8')
            fixed_count += 1
            print(f"✓ Fixed: {letter_file.name}")

    print(f"\n{'=' * 80}")
    print(f"COMPLETED: Fixed {fixed_count} letters")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
