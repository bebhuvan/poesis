#!/usr/bin/env python3
"""
Comprehensive OCR fixes based on cross-reference with 1945 edition.
"""

import re
from pathlib import Path


def apply_comprehensive_fixes(content: str) -> str:
    """Apply all comprehensive OCR fixes"""

    fixes = [
        # Fix specific OCR errors found in manual review
        (r'\bwalnut I\b', 'mahout'),
        (r'\bmahant\b', 'mahout'),
        (r'\bmahaut\b', 'mahout'),

        # Fix remaining common OCR errors
        (r'\bwc\b', 'we'),
        (r'\bWc\b', 'We'),
        (r'\bwilt\b', 'will'),
        (r'\bEnd\b', 'find'),
        (r'\banci\b', 'and'),
        (r'\btlie\b', 'the'),
        (r'\bTlie\b', 'The'),
        (r'\btiie\b', 'the'),
        (r'\bTiie\b', 'The'),
        (r'\bthc\b', 'the'),
        (r'\bTHC\b', 'THE'),
        (r'\bwlien\b', 'when'),
        (r'\bWlien\b', 'When'),
        (r'\bwliich\b', 'which'),
        (r'\bWliich\b', 'Which'),
        (r'\btliis\b', 'this'),
        (r'\bTliis\b', 'This'),
        (r'\bwliat\b', 'what'),
        (r'\bWliat\b', 'What'),
        (r'\bwliere\b', 'where'),
        (r'\bWliere\b', 'Where'),
        (r'\bwlio\b', 'who'),
        (r'\bWlio\b', 'Who'),
        (r'\bwhv\b', 'why'),
        (r'\bWhv\b', 'Why'),
        (r'\bdocs\b', 'does'),
        (r'\bDocs\b', 'Does'),
        (r'\bBbojpatra\b', 'Bhojpatra'),
        (r'\bKnglish\b', 'English'),
        (r'\blie\b', 'he'),
        (r'\bLie\b', 'He'),
        (r'\bam!\b', 'and'),
        (r'\bAm!\b', 'And'),

        # Fix hyphenated line breaks
        (r'atten-\s*\n\s*tion', 'attention'),
        (r'be-\s*\n\s*cause', 'because'),
        (r'there-\s*\n\s*fore', 'therefore'),
        (r'how to-\s*\n\s*grow', 'how to\ngrow'),
        (r'(\w)-\s*\n\s*([a-z])', r'\1\2'),  # General hyphenated line breaks

        # Fix spacing
        (r'atten- \n tion', 'attention'),
        (r'oft"', 'off'),

        # Remove artifacts
        (r'\bc y\s*\n+', '\n'),
        (r'\[\s*\d+\s*\]\s*\n+', '\n'),  # Page numbers

        # Clean up excessive newlines
        (r'\n{4,}', '\n\n'),
    ]

    result = content
    for pattern, replacement in fixes:
        result = re.sub(pattern, replacement, result)

    return result


def fix_letter_1_opening(content: str) -> str:
    """Fix Letter 1's missing opening paragraph"""

    if not content.startswith('# Letter 1: The Book of Nature\n\n. This book'):
        return content  # Already fixed or different issue

    opening = """# Letter 1: The Book of Nature

When you and I are together you often ask me questions about many things and I try to answer them. Now that you are at Mussoorie and I am in Allahabad we cannot have these talks. I am therefore going to write to you from time to time short accounts of the story of our earth and the many countries, great and small, in which it is divided. You have read a little about English history and Indian history. But England is only a little island and India, though a big country, is only a small part of the earth's surface. If we want to know something about the story of this world of ours we must think of all the countries and all the peoples that have inhabited it, and not merely of one little country where we may have been born.

I am afraid I can only tell you very little in these letters of mine. But that little, I hope, will interest you and make you think of the world as a whole, and of other peoples in it as our brothers and sisters. When you grow up you will read about the story of the earth and her peoples in fat books and you will find it more interesting than any other story or novel that you may have read.

You know of course that our earth is very, very old — millions and millions of years old. And for a long long time there were no men or women living in it. Before the men came there were only animals, and before the animals there was a time when no kind of life existed on the earth. It is difficult to imagine this world of ours, which is so full today of all kinds of animals and men, to be without them. But scientists and those who have studied and thought a great deal about these matters tell us that there was a time when the earth was too hot for any living being to live on it. And if we read their books and study the rocks and the fossils (the remains of old animals) we can ourselves see that this must have been so.

You read history in books. But in old times when men did not exist surely no books could have been written. How then can we find out what happened then? We cannot merely sit down and imagine everything. This would be very interesting for we could imagine anything we wanted to and would thus make up the most beautiful fairy tales. But this need not be true as it would not be based on any facts that we had seen. But although we have no books written in those far off days, fortunately we have some things which tell us a great deal as well almost as a book would. We have rocks and mountains and seas and stars and rivers and deserts and fossils of old animals. These and other like things are our books for the earth's early story. And the real way to understand this story is not merely to read about it in other people's books but to go to the great Book of Nature itself. You will I hope soon begin to learn how to read this story from the rocks and mountains. Imagine how fascinating it is! Every little stone that you see lying in the road or on the mountain side may be a little page in nature's book and may be able to tell you something if you only knew how to read it. To be able to read any language, Hindi or Urdu or English you have to learn its alphabet. So also you must learn the alphabet of nature before you can read her story in her books of stone and rock. Even now perhaps you know a little how to read this. If you see a little round shiny pebble, does it not tell you something? How did it get round and smooth and shiny without any corners or rough edges? If you break a big rock into small bits, each bit is rough and has corners and rough edges. It is not at all like a round smooth pebble. How then did the pebble become so round and smooth and shiny? It will tell you its story if you have good eyes to see and ears to hear it. It tells you that once upon a time, it may be long ago, it was a bit of a rock, just like the bit you may break from a big rock or stone with plenty of edges and corners. Probably it rested on some mountain side. Then came the rain and washed it down to the little valley where it found a mountain stream which pushed it on and on till it reached a little river. And the little river took it to the big river. And all the while it rolled at the bottom of the river and its edges were worn away and its rough surface made smooth and shiny. So it became the pebble that you see. Somehow the river left it behind and you found it. If the river had carried it on, it would have become smaller and smaller till at last it became a grain of sand and joined its brothers at the sea side to make a beautiful beach where little children can play and make castles out of the sand.

If a little pebble can tell you so much, how much more could we learn from all the rocks and mountains and the many other things we see around us?"""

    # Find where the mangled content starts (". This book consists")
    match = re.search(r'\. This book consists', content)
    if match:
        # Keep everything from "This book consists" onwards
        remaining = content[match.start()+2:]  # +2 to skip ". "
        return opening + "\n\nThis book consists" + remaining

    return content


def main():
    """Apply comprehensive fixes"""

    base_dir = Path(__file__).parent
    letters_dir = base_dir / "final_letters/jawaharlal_nehru_1929"

    print("=" * 80)
    print("COMPREHENSIVE OCR CORRECTION")
    print("=" * 80)

    for letter_file in sorted(letters_dir.glob("letter-*.md")):
        # Read content
        content = letter_file.read_text(encoding='utf-8')

        # Split into frontmatter and body
        parts = content.split('---\n', 2)
        if len(parts) != 3:
            print(f"⚠ Skipping {letter_file.name}: No frontmatter")
            continue

        frontmatter = parts[1]
        body = parts[2]

        # Apply fixes to body only
        fixed_body = apply_comprehensive_fixes(body)

        # Special fix for Letter 1
        if 'letter-01-' in letter_file.name:
            fixed_body = fix_letter_1_opening(fixed_body)

        # Reassemble
        fixed_content = f"---\n{frontmatter}---\n{fixed_body}"

        # Write back
        letter_file.write_text(fixed_content, encoding='utf-8')
        print(f"✓ Processed: {letter_file.name}")

    print(f"\n{'=' * 80}")
    print("COMPREHENSIVE CORRECTIONS COMPLETE")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
