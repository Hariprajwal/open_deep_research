"""IEEE Two-Column Conference Paper PDF Generator.

Generates a proper IEEE conference paper PDF matching the official IEEEtran format:
  - Letter page size, 0.75in margins
  - Two-column body layout
  - Times New Roman (serif) fonts
  - Roman numeral section headers (I. INTRODUCTION)
  - Bold-italic abstract block
  - Index Terms line
  - Proper table/figure styling
"""

import re
from pathlib import Path


IEEE_CONFERENCE_CSS = """
@page {
    size: 8.5in 11in;
    margin: 0.75in 0.625in 1in 0.625in;
}

body {
    font-family: "Times New Roman", Times, serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #000;
}

/* ─── TITLE BLOCK ─────────────────────────────── */
.ieee-title-block {
    text-align: center;
    margin-bottom: 14px;
}

.ieee-title {
    font-size: 22pt;
    font-weight: bold;
    font-family: "Times New Roman", Times, serif;
    text-align: center;
    margin-bottom: 10px;
    line-height: 1.25;
}

.ieee-authors {
    font-size: 10pt;
    text-align: center;
    margin-bottom: 4px;
}

.ieee-affil {
    font-size: 9pt;
    font-style: italic;
    text-align: center;
    color: #333;
    margin-bottom: 14px;
}

/* ─── ABSTRACT BLOCK ──────────────────────────── */
.ieee-abstract {
    font-size: 9pt;
    font-style: italic;
    margin: 12px 0 10px 0;
}

.ieee-abstract-label {
    font-weight: bold;
    font-style: italic;
}

.ieee-index-terms {
    font-size: 9pt;
    font-style: italic;
    margin-bottom: 12px;
}

.ieee-index-terms .label {
    font-weight: bold;
}

/* ─── DIVIDER ─────────────────────────────────── */
.ieee-divider {
    border-top: 1px solid #000;
    margin: 10px 0;
}

/* ─── TWO-COLUMN BODY ─────────────────────────── */
.ieee-body {
    /* xhtml2pdf doesn't support CSS columns; we use a table-based two-col layout */
}

.ieee-columns {
    width: 100%;
}

.ieee-col {
    width: 48%;
    vertical-align: top;
    padding: 0 1%;
    font-size: 10pt;
    font-family: "Times New Roman", Times, serif;
    line-height: 1.4;
}

/* ─── SECTION HEADERS ─────────────────────────── */
h1 {
    font-size: 10pt;
    font-weight: bold;
    font-family: "Times New Roman", Times, serif;
    text-align: center;
    text-transform: uppercase;
    margin: 14px 0 6px 0;
    letter-spacing: 0.02em;
}

h2 {
    font-size: 10pt;
    font-weight: bold;
    font-style: italic;
    font-family: "Times New Roman", Times, serif;
    margin: 10px 0 4px 0;
    text-transform: none;
}

h3 {
    font-size: 10pt;
    font-weight: bold;
    font-family: "Times New Roman", Times, serif;
    margin: 8px 0 3px 0;
}

/* ─── PARAGRAPHS ──────────────────────────────── */
p {
    margin: 0 0 6px 0;
    text-align: justify;
    text-indent: 0.25in;
}

p:first-child, h1 + p, h2 + p, h3 + p {
    text-indent: 0;
}

/* ─── LISTS ───────────────────────────────────── */
ul, ol {
    margin: 4px 0 6px 0;
    padding-left: 18px;
}

li {
    margin-bottom: 3px;
}

/* ─── TABLES ──────────────────────────────────── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 9pt;
    font-family: "Times New Roman", Times, serif;
}

th {
    border-top: 1.5px solid #000;
    border-bottom: 1px solid #000;
    padding: 3px 5px;
    font-weight: bold;
    text-align: center;
}

td {
    border-bottom: 0.5px solid #ccc;
    padding: 3px 5px;
}

.table-caption {
    font-size: 9pt;
    text-align: center;
    font-weight: bold;
    text-transform: uppercase;
    margin-bottom: 4px;
}

/* ─── CODE BLOCKS ─────────────────────────────── */
pre {
    font-family: "Courier New", Courier, monospace;
    font-size: 8pt;
    background-color: #f9f9f9;
    border: 0.5px solid #ccc;
    padding: 5px;
    margin: 6px 0;
}

code {
    font-family: "Courier New", Courier, monospace;
    font-size: 8pt;
}

/* ─── REFERENCES ──────────────────────────────── */
.ieee-references {
    font-size: 9pt;
    font-family: "Times New Roman", Times, serif;
}

.ieee-references p {
    text-indent: 0;
    padding-left: 18px;
    text-indent: -18px;
    margin-bottom: 4px;
}
"""


def _sanitize(text: str) -> str:
    """Remove/replace problematic Unicode for PDF rendering."""
    replacements = {
        "\u2011": "-", "\u2010": "-", "\u2012": "-", "\u2013": "-",
        "\u2014": "--", "\u2026": "...", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u202f": " ", "\xa0": " ",
        "\u2265": ">=", "\u2264": "<=", "\u2261": "==", "\u2260": "!=",
        "\u2248": "~=", "\u2212": "-", "\u200b": "",
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text


def _number_sections(html: str) -> str:
    """Replace ## headings with IEEE roman-numeral section counters."""
    counter = [0]

    def replace_h2(m):
        counter[0] += 1
        roman = _to_roman(counter[0])
        label = m.group(1).strip()
        # Strip any leading #
        label = re.sub(r'^#+\s*', '', label)
        return f'<h1>{roman}. {label.upper()}</h1>'

    html = re.sub(r'<h2>(.*?)</h2>', replace_h2, html, flags=re.DOTALL)
    return html


def _to_roman(n: int) -> str:
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),
            (100,'C'),(90,'XC'),(50,'L'),(40,'XL'),
            (10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ''
    for v, s in vals:
        while n >= v:
            result += s
            n -= v
    return result


def _extract_abstract(md_content: str) -> tuple[str, str]:
    """Extract the abstract from the markdown, return (abstract_text, md_without_abstract)."""
    pattern = re.compile(
        r'##\s*(?:ABSTRACT|Abstract)\s*\n(.*?)(?=\n##\s|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    m = pattern.search(md_content)
    if m:
        abstract = m.group(1).strip()
        rest = md_content[:m.start()] + md_content[m.end():]
        return abstract, rest

    # Fallback: look for bold abstract prefix inline
    pattern2 = re.compile(r'\*\*Abstract\*\*[:\s—]+(.*?)(?=\n\n|\n#)', re.DOTALL | re.IGNORECASE)
    m2 = pattern2.search(md_content)
    if m2:
        abstract = m2.group(1).strip()
        rest = md_content[:m2.start()] + md_content[m2.end():]
        return abstract, rest

    # No abstract found — use first paragraph
    paras = md_content.split('\n\n')
    for i, p in enumerate(paras):
        if not p.startswith('#') and len(p) > 80:
            return p.strip(), '\n\n'.join(paras[:i] + paras[i+1:])
    return "", md_content


def _split_into_two_columns(html_body: str) -> str:
    """Wrap HTML content in a two-column table layout for xhtml2pdf."""
    # Split at a logical midpoint (by tags, not characters)
    tags = re.findall(r'<(?:h1|h2|h3|p|pre|ul|ol|table)[^>]*>.*?</(?:h1|h2|h3|p|pre|ul|ol|table)>',
                      html_body, re.DOTALL)
    mid = len(tags) // 2
    col1_content = '\n'.join(tags[:mid]) if tags else html_body
    col2_content = '\n'.join(tags[mid:]) if tags else ''

    return f"""
<table class="ieee-columns" cellpadding="0" cellspacing="0">
  <tr>
    <td class="ieee-col">{col1_content}</td>
    <td class="ieee-col">{col2_content}</td>
  </tr>
</table>
"""


def generate_ieee_conference_pdf(
    md_content: str,
    output_pdf_path: str,
    title: str = "Research Paper",
    author: str = "Research Agent System",
    affiliation: str = "Open Deep Research Engine",
    keywords: list = None
) -> bool:
    """
    Generate a proper IEEE two-column conference paper PDF from markdown content.
    
    Produces a layout matching the official IEEEtran conference style:
    - Two-column body
    - Times New Roman font throughout
    - Roman numeral section headers
    - Bold-italic abstract block
    - Index Terms line
    """
    import markdown as md_lib
    from xhtml2pdf import pisa

    pdf_path = Path(output_pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        clean_md = _sanitize(md_content)
        clean_title = _sanitize(title)
        clean_author = _sanitize(author)

        # Extract abstract before converting
        abstract_text, body_md = _extract_abstract(clean_md)
        abstract_text = _sanitize(abstract_text)

        # Remove duplicate title header from the top of the markdown
        body_md = re.sub(
            rf'^\s*#\s*{re.escape(clean_title)}\s*\n', '', body_md,
            flags=re.IGNORECASE | re.MULTILINE
        )
        # Remove Author(s) line from body if present
        body_md = re.sub(r'\*\*Author\(s\)\*\*:.*?\n', '', body_md)
        # Remove horizontal dividers
        body_md = re.sub(r'\n---+\s*\n', '\n', body_md)

        # Convert body markdown to HTML
        html_body = md_lib.markdown(
            body_md.strip(),
            extensions=['tables', 'fenced_code', 'toc']
        )

        # Apply IEEE roman numeral section numbering
        html_body = _number_sections(html_body)

        # Build two-column layout
        two_col_html = _split_into_two_columns(html_body)

        # Build keyword / index terms line
        if keywords:
            kw_str = ", ".join(keywords)
        else:
            # Auto-extract keywords from title
            words = [w for w in re.split(r'\W+', clean_title.lower()) 
                     if len(w) > 3 and w not in {'with', 'using', 'from', 'that', 'this', 'into', 'based'}]
            kw_str = ", ".join(words[:6]) if words else "deep learning, research, optimization"

        # Truncate abstract for display (first 80 words)
        abstract_words = abstract_text.split()
        short_abstract = ' '.join(abstract_words[:120]) + ('...' if len(abstract_words) > 120 else '')

        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{clean_title}</title>
<style>
{IEEE_CONFERENCE_CSS}
</style>
</head>
<body>

<!-- TITLE BLOCK -->
<div class="ieee-title-block">
  <div class="ieee-title">{clean_title}</div>
  <div class="ieee-authors">{clean_author}</div>
  <div class="ieee-affil">{affiliation}</div>
</div>

<div class="ieee-divider"></div>

<!-- ABSTRACT -->
<p class="ieee-abstract">
  <span class="ieee-abstract-label">Abstract&#8212;</span>{short_abstract}
</p>

<!-- INDEX TERMS -->
<p class="ieee-index-terms">
  <span class="label">Index Terms&#8212;</span>{kw_str}
</p>

<div class="ieee-divider"></div>

<!-- TWO-COLUMN BODY -->
<div class="ieee-body">
{two_col_html}
</div>

</body>
</html>"""

        with open(pdf_path, "wb") as f:
            status = pisa.CreatePDF(full_html, dest=f)

        if not status.err and pdf_path.exists() and pdf_path.stat().st_size > 0:
            print(f"[IEEE Conf PDF] Compiled IEEE conference PDF ({pdf_path.stat().st_size} bytes)")
            return True
        else:
            print(f"[IEEE Conf PDF] xhtml2pdf error: {status.err}")
            return False

    except Exception as e:
        print(f"[IEEE Conf PDF] Exception: {e}")
        return False
