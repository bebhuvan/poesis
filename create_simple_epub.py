#!/usr/bin/env python3
"""
Simple EPUB Generator - Creates a single-file EPUB with all content
"""

import os
import re
import zipfile
from pathlib import Path
from datetime import datetime
from html import escape


class SimpleEPUBGenerator:
    def __init__(self, markdown_file: str):
        with open(markdown_file, 'r', encoding='utf-8') as f:
            self.markdown = f.read()

        self.title = "Life and Letters of Toru Dutt"
        self.author = "Harihar Das"

    def markdown_to_html(self, md_text: str) -> str:
        """Convert markdown to HTML with better paragraph handling"""
        lines = md_text.split('\n')
        html_lines = []
        in_paragraph = False
        current_para = []

        for line in lines:
            stripped = line.strip()

            # Check if it's a heading
            if stripped.startswith('###'):
                # Close any open paragraph
                if current_para:
                    html_lines.append(f'<p>{" ".join(current_para)}</p>')
                    current_para = []
                    in_paragraph = False
                heading_text = stripped[3:].strip()
                html_lines.append(f'<h3>{escape(heading_text)}</h3>')

            elif stripped.startswith('##'):
                if current_para:
                    html_lines.append(f'<p>{" ".join(current_para)}</p>')
                    current_para = []
                    in_paragraph = False
                heading_text = stripped[2:].strip()
                html_lines.append(f'<h2>{escape(heading_text)}</h2>')

            elif stripped.startswith('#'):
                if current_para:
                    html_lines.append(f'<p>{" ".join(current_para)}</p>')
                    current_para = []
                    in_paragraph = False
                heading_text = stripped[1:].strip()
                html_lines.append(f'<h1>{escape(heading_text)}</h1>')

            elif stripped == '---':
                if current_para:
                    html_lines.append(f'<p>{" ".join(current_para)}</p>')
                    current_para = []
                    in_paragraph = False
                html_lines.append('<hr/>')

            elif stripped.startswith('**') or stripped.startswith('*'):
                # Special formatting lines (dedication, etc.)
                if current_para:
                    html_lines.append(f'<p>{" ".join(current_para)}</p>')
                    current_para = []
                    in_paragraph = False

                formatted = stripped
                formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', formatted)
                formatted = re.sub(r'\*(.+?)\*', r'<em>\1</em>', formatted)
                html_lines.append(f'<p class="centered">{formatted}</p>')

            elif stripped:
                # Regular text line
                escaped = escape(stripped)
                # Apply inline formatting
                escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
                escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)
                current_para.append(escaped)

            else:
                # Empty line - close paragraph
                if current_para:
                    html_lines.append(f'<p>{" ".join(current_para)}</p>')
                    current_para = []
                    in_paragraph = False

        # Close any remaining paragraph
        if current_para:
            html_lines.append(f'<p>{" ".join(current_para)}</p>')

        return '\n'.join(html_lines)

    def create_html_document(self) -> str:
        """Create complete HTML document"""
        content_html = self.markdown_to_html(self.markdown)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{escape(self.title)}</title>
    <link rel="stylesheet" type="text/css" href="styles/main.css"/>
    <meta charset="UTF-8"/>
</head>
<body>
{content_html}
</body>
</html>"""

    def create_css(self) -> str:
        """Create CSS stylesheet"""
        return """/* EPUB Stylesheet for Life and Letters of Toru Dutt */

body {
    font-family: "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
    line-height: 1.7;
    margin: 1.5em;
    color: #2c2c2c;
    text-align: justify;
    font-size: 1em;
}

h1, h2, h3, h4 {
    font-family: "Palatino Linotype", "Book Antiqua", Palatino, serif;
    text-align: center;
    margin-top: 2em;
    margin-bottom: 1.2em;
    font-weight: bold;
    color: #1a1a1a;
}

h1 {
    font-size: 2.2em;
    margin-top: 3em;
    margin-bottom: 2em;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

h2 {
    font-size: 1.6em;
    page-break-before: always;
    margin-top: 3em;
    margin-bottom: 1.5em;
    letter-spacing: 0.03em;
}

h3 {
    font-size: 1.2em;
    font-style: italic;
    margin-top: 1.5em;
}

p {
    margin: 0.8em 0;
    text-indent: 1.8em;
}

/* No indent for first paragraphs */
h1 + p,
h2 + p,
h3 + p,
hr + p {
    text-indent: 0;
}

p.centered {
    text-align: center;
    text-indent: 0;
    margin: 1em 0;
}

em {
    font-style: italic;
}

strong {
    font-weight: bold;
    font-size: 1.05em;
}

hr {
    border: none;
    border-top: 2px solid #999;
    margin: 3em auto;
    width: 30%;
}

/* Poem/verse styling */
p em {
    display: block;
}

/* Page breaks */
h2 {
    page-break-before: always;
}

/* Prevent orphans and widows */
p {
    orphans: 3;
    widows: 3;
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

    def create_content_opf(self) -> str:
        """Create content.opf"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="bookid">urn:uuid:toru-dutt-life-letters-1921</dc:identifier>
        <dc:title>{escape(self.title)}</dc:title>
        <dc:creator id="creator">{escape(self.author)}</dc:creator>
        <meta refines="#creator" property="role" scheme="marc:relators">aut</meta>
        <dc:contributor id="contributor">H. A. L. Fisher</dc:contributor>
        <meta refines="#contributor" property="role" scheme="marc:relators">aui</meta>
        <dc:language>en</dc:language>
        <dc:date>1921</dc:date>
        <dc:publisher>Oxford University Press</dc:publisher>
        <dc:description>A biography and collection of letters of Toru Dutt (1856-1877), the remarkable Indian poet who wrote in English, French, and Sanskrit. Includes her correspondence with Mary Martin, biographical details, and critical analysis of her literary achievements including 'Ancient Ballads and Legends of Hindustan' and 'A Sheaf Gleaned in French Fields'.</dc:description>
        <dc:subject>Biography</dc:subject>
        <dc:subject>Poetry</dc:subject>
        <dc:subject>Indian Literature</dc:subject>
        <dc:subject>Toru Dutt</dc:subject>
        <dc:subject>19th Century Literature</dc:subject>
        <dc:rights>Public Domain</dc:rights>
        <meta property="dcterms:modified">{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        <item id="css" href="styles/main.css" media-type="text/css"/>
        <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
    </manifest>
    <spine toc="ncx">
        <itemref idref="content"/>
    </spine>
</package>"""

    def create_toc_ncx(self) -> str:
        """Create toc.ncx"""
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
        <navPoint id="navpoint-1" playOrder="1">
            <navLabel>
                <text>Start</text>
            </navLabel>
            <content src="content.xhtml"/>
        </navPoint>
    </navMap>
</ncx>"""

    def generate_epub(self, output_path: str):
        """Generate the EPUB file"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # mimetype must be first and uncompressed
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

            # META-INF
            epub.writestr('META-INF/container.xml', self.create_container_xml())

            # OEBPS
            epub.writestr('OEBPS/content.opf', self.create_content_opf())
            epub.writestr('OEBPS/toc.ncx', self.create_toc_ncx())
            epub.writestr('OEBPS/styles/main.css', self.create_css())
            epub.writestr('OEBPS/content.xhtml', self.create_html_document())

        file_size = os.path.getsize(output_path)
        print(f"✓ Created EPUB: {output_path}")
        print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

        return output_path


def main():
    output_dir = Path('/home/user/poesis/toru_dutt_output')
    markdown_file = output_dir / 'toru_dutt_enhanced.md'

    if not markdown_file.exists():
        print(f"Error: {markdown_file} not found")
        return

    generator = SimpleEPUBGenerator(str(markdown_file))
    epub_path = output_dir / 'Life_and_Letters_of_Toru_Dutt.epub'
    generator.generate_epub(str(epub_path))

    print(f"\n✓ E-book successfully generated!")
    print(f"  Location: {epub_path}")
    print(f"\nThis EPUB can be read on:")
    print(f"  • E-readers (Kindle, Kobo, Nook, etc.)")
    print(f"  • Mobile apps (Apple Books, Google Play Books)")
    print(f"  • Desktop software (Calibre, Adobe Digital Editions)")


if __name__ == '__main__':
    main()
