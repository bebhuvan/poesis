#!/usr/bin/env python3
"""Clean and improve transcript quality for In the Money podcast episodes."""

import re
import os


def clean_transcript(text, guest_name, host_name="Bhuvan"):
    """Apply mechanical fixes to a transcript."""
    # Decode HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&gt;&gt;", ">>")
    text = text.replace("&gt;", ">")
    text = text.replace("&lt;", "<")

    # Fix common auto-transcription proper noun errors
    # Use regex for word-boundary-aware replacements where needed
    simple_replacements = {
        "SIBO floor": "CBOE floor",
        "SIBO": "CBOE",
        "OEEX": "OEX",
        "Schwagger": "Schwager",
        "Thinker Swim": "Thinkorswim",
        "Think or Swim": "Thinkorswim",
        "thinkers swim": "Thinkorswim",
        "Thinkerswim": "Thinkorswim",
        "America Trade": "Ameritrade",
        "Castup Larsson": "Kaastrup-Larsen",
        "Kelner": "Keltner",
        "Boinger": "Bollinger",
        "Bowlinger": "Bollinger",
        "Ballinger": "Bollinger",
        "Benorp": "Bensdorp",
        "sock gen": "SocGen",
        "Sochen": "SocGen",
        "alter boys": "altar boys",
        "marktomark": "mark-to-market",
        "HW Bush's": "H.W. Bush's",
        "HW Bush": "H.W. Bush",
        "illlquid": "illiquid",
        "anyformational": "any informational",
    }

    for old, new in simple_replacements.items():
        text = text.replace(old, new)

    # Regex-based replacements for tricky cases
    regex_replacements = [
        # "donin" variants -> "Donchian" (but not inside other words)
        (r'\bdonin\b', 'Donchian'),
        (r'\bdonins\b', 'Donchian'),
        (r'\bDonin\b', 'Donchian'),
        # "dungeon" in trading context -> "Donchian"
        (r'\bdungeon\b', 'Donchian'),
        # "don channels" / "Don channels"
        (r'\b[Dd]on channels\b', 'Donchian channels'),
        (r'\b[Dd]on channel\b', 'Donchian channel'),
        # Specific "21-day don" pattern (Donchian)
        (r'(\d+-day\s+)[Dd]on\b', r'\1Donchian'),
        (r'a\s+[Dd]on\s+strategy', 'a Donchian strategy'),
        (r'3-day don\b', '3-day Donchian'),
        # "Dun Capital" -> "Dunn Capital"
        (r'\bDun Capital\b', 'Dunn Capital'),
        (r'\bDone Capital\b', 'Dunn Capital'),
        (r'\bDone capital\b', 'Dunn Capital'),
        (r'\bDon Capital\b', 'Dunn Capital'),
        # Dawn -> Dunn (only in context of capital management firm)
        (r'\bat Dawn\b', 'at Dunn'),
        (r'\bat Don\b', 'at Dunn'),
        # "ManHl" / "Man HI" -> "Man AHL"
        (r'\bManHl\b', 'Man AHL'),
        (r'\bMan HI\b', 'Man AHL'),
        (r'\bman HI\b', 'Man AHL'),
        # "EHL" -> "AHL" (in context of hedge fund)
        (r'\bEHL\b', 'AHL'),
        (r'\bAFL\b', 'AHL'),
        # "Neils" -> "Niels" (but not "Neil's" in possessive)
        (r'\bNeils\b', 'Niels'),
        (r"\bNeil's\b", "Niels'"),
        # "Delio" -> "Dalio"
        (r'\bDelio\b', 'Dalio'),
        # "bare market" -> "bear market"
        (r'\bbare market\b', 'bear market'),
        (r'\bbare markets\b', 'bear markets'),
        # zero-DTE variants
        (r'\bzerod\b', 'zero-DTE'),
        (r'\bzerodt\b', 'zero-DTE'),
        (r'\bzero DT\b', 'zero-DTE'),
        (r'\bzero GTE\b', 'zero-DTE'),
        (r'\bzero DD\b', 'zero-DTE'),
        (r'\bZero DTE\b', 'zero-DTE'),
        (r'\bzero DTE\b', 'zero-DTE'),
        (r'\b0DTE\b', 'zero-DTE'),
        # FTSE
        (r'\bfoots\b', 'FTSE'),
        (r'\bfoots is\b', 'FTSE is'),
        # Kuwait
        (r'\bUwait\b', 'Kuwait'),
        # "explanary" / "explanatory" weighted
        (r'\bexplanary\b', 'exponentially'),
        (r'\bexplainary\b', 'exponentially'),
    ]

    for pattern, replacement in regex_replacements:
        text = re.sub(pattern, replacement, text)

    return text


def process_file(input_path, output_path, guest_name, host_name="Bhuvan"):
    """Process a single transcript file."""
    with open(input_path, 'r') as f:
        text = f.read()

    cleaned = clean_transcript(text, guest_name, host_name)

    with open(output_path, 'w') as f:
        f.write(cleaned)

    print(f"Processed: {input_path} -> {output_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    episodes = [
        ("01_tom_sosnoff_transcript.txt", "Tom Sosnoff"),
        ("02_tom_basso_transcript.txt", "Tom Basso"),
        ("03_niels_kaastrup_transcript.txt", "Niels Kaastrup-Larsen"),
        ("04_robert_carver_transcript.txt", "Robert Carver"),
    ]

    for filename, guest_name in episodes:
        input_path = os.path.join(base_dir, filename)
        if os.path.exists(input_path):
            process_file(input_path, input_path, guest_name)
        else:
            print(f"File not found: {input_path}")
