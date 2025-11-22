#!/usr/bin/env python3
"""
EPUB Generator for Toru Dutt's Life and Letters
Creates a proper EPUB 3.0 e-book from the cleaned text
"""

import os
import re
import json
import zipfile
from pathlib import Path
from datetime import datetime
from html import escape


class EPUBGenerator:
    def __init__(self, markdown_file: str, chapters_file: str):
        with open(markdown_file, 'r', encoding='utf-8') as f:
            self.markdown = f.read()

        with open(chapters_file, 'r', encoding='utf-8') as f:
            self.chapters = json.load(f)

        self.title = "Life and Letters of Toru Dutt"
        self.author = "Harihar Das"
        self.year = "1921"
        self.foreword_author = "H. A. L. Fisher"

    def markdown_to_html(self, md_text: str) -> str:
        """Convert simple markdown to HTML"""
        html = escape(md_text)

        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Emphasis
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Paragraphs (group consecutive non-empty lines)
        lines = html.split('\n')
        paragraphs = []
        current_para = []

        for line in lines:
            stripped = line.strip()

            # If line is HTML tag, close current paragraph and add the tag
            if stripped.startswith('<h') or stripped.startswith('</h') or \
               stripped.startswith('<div') or stripped.startswith('</div') or \
               stripped == '<hr>' or stripped == '---':
                if current_para:
                    para_text = ' '.join(current_para)
                    if para_text.strip():
                        paragraphs.append(f'<p>{para_text}</p>')
                    current_para = []
                if stripped == '---':
                    paragraphs.append('<hr/>')
                else:
                    paragraphs.append(stripped)
            elif stripped:
                current_para.append(stripped)
            else:
                # Empty line - close paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    if para_text.strip():
                        paragraphs.append(f'<p>{para_text}</p>')
                    current_para = []

        # Don't forget last paragraph
        if current_para:
            para_text = ' '.join(current_para)
            if para_text.strip():
                paragraphs.append(f'<p>{para_text}</p>')

        return '\n'.join(paragraphs)

    def create_html_wrapper(self, content: str, title: str = "") -> str:
        """Wrap content in proper HTML structure"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{escape(title or self.title)}</title>
    <link rel="stylesheet" type="text/css" href="../styles/main.css"/>
</head>
<body>
{content}
</body>
</html>"""

    def split_into_chapters(self) -> dict:
        """Split markdown into individual chapter files"""
        sections = {}

        # Split by chapters
        chapter_pattern = r'^## Chapter ([IVXLCDM]+)\s*$'
        parts = re.split(f'({chapter_pattern})', self.markdown, flags=re.MULTILINE)

        # Handle front matter (before first chapter)
        front_matter = parts[0]
        sections['front'] = front_matter

        # Process chapters
        i = 1
        while i < len(parts):
            if re.match(chapter_pattern, parts[i], re.MULTILINE):
                chapter_num = re.search(r'Chapter ([IVXLCDM]+)', parts[i]).group(1)
                chapter_content = parts[i] + (parts[i + 1] if i + 1 < len(parts) else '')
                sections[f'chapter_{chapter_num}'] = chapter_content
                i += 2
            else:
                i += 1

        return sections

    def create_css(self) -> str:
        """Create CSS stylesheet"""
        return """/* EPUB Stylesheet */
body {
    font-family: Georgia, serif;
    line-height: 1.6;
    margin: 1em;
    text-align: justify;
}

h1, h2, h3 {
    font-family: "Palatino Linotype", "Book Antiqua", Palatino, serif;
    text-align: center;
    margin-top: 1.5em;
    margin-bottom: 1em;
    font-weight: bold;
}

h1 {
    font-size: 2em;
    margin-top: 2em;
    margin-bottom: 1.5em;
}

h2 {
    font-size: 1.5em;
    page-break-before: always;
}

h3 {
    font-size: 1.2em;
    font-style: italic;
}

p {
    margin: 0.5em 0;
    text-indent: 1.5em;
}

p:first-of-type,
h1 + p,
h2 + p,
h3 + p {
    text-indent: 0;
}

em {
    font-style: italic;
}

strong {
    font-weight: bold;
}

hr {
    border: none;
    border-top: 1px solid #999;
    margin: 2em auto;
    width: 50%;
}

.dedication,
.epigraph {
    text-align: center;
    font-style: italic;
    margin: 2em 0;
}
"""

    def create_container_xml(self) -> str:
        """Create META-INF/container.xml"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""

    def create_content_opf(self, chapter_files: list) -> str:
        """Create content.opf (package document)"""
        # Generate manifest items
        manifest_items = [
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '<item id="css" href="styles/main.css" media-type="text/css"/>',
        ]

        for i, (file_id, _) in enumerate(chapter_files):
            manifest_items.append(
                f'<item id="{file_id}" href="text/{file_id}.xhtml" media-type="application/xhtml+xml"/>'
            )

        # Generate spine itemrefs
        spine_items = [f'<itemref idref="{file_id}"/>' for file_id, _ in chapter_files]

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="bookid">urn:uuid:toru-dutt-life-letters-1921</dc:identifier>
        <dc:title>{escape(self.title)}</dc:title>
        <dc:creator>{escape(self.author)}</dc:creator>
        <dc:contributor>{escape(self.foreword_author)} (Foreword)</dc:contributor>
        <dc:language>en</dc:language>
        <dc:date>{self.year}</dc:date>
        <dc:publisher>Oxford University Press</dc:publisher>
        <dc:description>A biography and collection of letters of Toru Dutt (1856-1877), the remarkable Indian poet who wrote in English, French, and Sanskrit. This work includes her correspondence, biographical details, and analysis of her literary achievements.</dc:description>
        <dc:subject>Biography</dc:subject>
        <dc:subject>Poetry</dc:subject>
        <dc:subject>Indian Literature</dc:subject>
        <dc:subject>Toru Dutt</dc:subject>
        <meta property="dcterms:modified">{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
    </metadata>
    <manifest>
        {chr(10).join(manifest_items)}
    </manifest>
    <spine toc="ncx">
        {chr(10).join(spine_items)}
    </spine>
</package>"""

    def create_toc_ncx(self, chapter_files: list) -> str:
        """Create toc.ncx (navigation)"""
        nav_points = []

        for i, (file_id, title) in enumerate(chapter_files, 1):
            nav_points.append(f"""
    <navPoint id="navpoint-{i}" playOrder="{i}">
        <navLabel>
            <text>{escape(title)}</text>
        </navLabel>
        <content src="text/{file_id}.xhtml"/>
    </navPoint>""")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:toru-dutt-life-letters-1921"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{escape(self.title)}</text>
    </docTitle>
    <navMap>
        {''.join(nav_points)}
    </navMap>
</ncx>"""

    def generate_epub(self, output_path: str):
        """Generate the complete EPUB file"""
        # Split content
        sections = self.split_into_chapters()

        # Prepare chapter files list
        chapter_files = [('front', 'Title & Foreword')]

        for ch in self.chapters:
            ch_id = f"chapter_{ch['number']}"
            ch_title = f"Chapter {ch['number']}"
            if ch['title']:
                ch_title += f": {ch['title'][:50]}"
            chapter_files.append((ch_id, ch_title))

        # Create EPUB (it's a ZIP file)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # mimetype (must be first, uncompressed)
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

            # META-INF/container.xml
            epub.writestr('META-INF/container.xml', self.create_container_xml())

            # CSS
            epub.writestr('OEBPS/styles/main.css', self.create_css())

            # Content files
            for file_id, title in chapter_files:
                if file_id in sections:
                    content_md = sections[file_id]
                    content_html = self.markdown_to_html(content_md)
                    full_html = self.create_html_wrapper(content_html, title)
                    epub.writestr(f'OEBPS/text/{file_id}.xhtml', full_html)

            # OPF and NCX
            epub.writestr('OEBPS/content.opf', self.create_content_opf(chapter_files))
            epub.writestr('OEBPS/toc.ncx', self.create_toc_ncx(chapter_files))

        print(f"✓ Created EPUB: {output_path}")
        print(f"  Chapters: {len(chapter_files)}")
        file_size = os.path.getsize(output_path)
        print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")


def main():
    output_dir = Path('/home/user/poesis/toru_dutt_output')

    generator = EPUBGenerator(
        markdown_file=str(output_dir / 'toru_dutt_enhanced.md'),
        chapters_file=str(output_dir / 'chapters.json')
    )

    epub_path = output_dir / 'Life_and_Letters_of_Toru_Dutt.epub'
    generator.generate_epub(str(epub_path))

    print(f"\n✓ E-book generation complete!")
    print(f"  EPUB file: {epub_path}")
    print(f"\nYou can now read this on any e-reader that supports EPUB format.")


if __name__ == '__main__':
    main()
