"""Generate a premium styled PDF of the Mock Any Exam custom report artifact."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

ARTIFACT_PATH = r"C:\Users\harip\.gemini\antigravity-ide\brain\dc78f3ed-da97-4b19-9883-ee16e3ec736f\mock_any_exam_custom_report.md"
OUTPUT_PDF = r"output\mock_any_exam_report\Mock_Any_Exam_Custom_Report.pdf"

PREMIUM_CSS = """
@page {
    size: A4;
    margin: 2cm 2cm 2.2cm 2cm;
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.45;
    color: #1E293B;
    background: white;
}

/* ---- Title block ---- */
h1 {
    font-size: 15pt;
    font-weight: bold;
    color: #0F172A;
    text-align: center;
    margin-top: 0;
    margin-bottom: 4px;
    line-height: 1.3;
}

/* ---- Section headers ---- */
h2 {
    font-size: 10.5pt;
    font-weight: bold;
    color: #0F172A;
    border-bottom: 1.5px solid #0EA5E9;
    padding-bottom: 2px;
    margin-top: 16px;
    margin-bottom: 7px;
    text-transform: uppercase;
    letter-spacing: 0.3pt;
}

h3 {
    font-size: 9.5pt;
    font-weight: bold;
    color: #0EA5E9;
    margin-top: 11px;
    margin-bottom: 4px;
}

/* ---- Body text ---- */
p {
    margin-top: 3px;
    margin-bottom: 7px;
    text-align: justify;
}

/* ---- Code & pre ---- */
code {
    font-family: Courier, monospace;
    font-size: 8pt;
    background-color: #F1F5F9;
    padding: 1px 3px;
}

pre {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 3px solid #0EA5E9;
    padding: 7px 10px;
    font-family: Courier, monospace;
    font-size: 7.8pt;
    line-height: 1.35;
    margin: 8px 0;
    white-space: pre-wrap;
}

/* ---- Tables ---- */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 8.5pt;
}

th {
    background-color: #0F172A;
    color: #FFFFFF;
    font-weight: bold;
    padding: 5px 7px;
    text-align: left;
    border: 1px solid #334155;
}

td {
    padding: 4px 7px;
    border: 1px solid #CBD5E1;
    vertical-align: top;
}

tr:nth-child(even) td {
    background-color: #F8FAFC;
}

/* ---- Lists ---- */
ul, ol {
    margin: 4px 0 7px 0;
    padding-left: 16px;
}

li {
    margin-bottom: 3px;
}

/* ---- Horizontal rule ---- */
hr {
    border: none;
    border-top: 1px solid #CBD5E1;
    margin: 12px 0;
}

/* ---- Emphasis ---- */
strong {
    color: #0F172A;
    font-weight: bold;
}

em {
    color: #475569;
}

blockquote {
    border-left: 3px solid #0EA5E9;
    margin: 8px 0;
    padding: 5px 10px;
    background: #F0F9FF;
    font-size: 9pt;
    color: #334155;
}
"""

import re
import markdown
from xhtml2pdf import pisa

def sanitize(text: str) -> str:
    replacements = {
        "\u2011": "-", "\u2010": "-", "\u2012": "-", "\u2013": "-", "\u2014": "--",
        "\u2026": "...", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u202f": " ", "\xa0": " ", "\u2265": ">=", "\u2264": "<=", "\u2260": "!=",
        "\u2248": "~=", "\u2212": "-", "\u200b": "", "\u00d7": "x",
        "\u00b1": "+/-", "\u03c4": "tau", "\u03b1": "alpha", "\u03b2": "beta",
        "\u2192": "->", "\u21d2": "=>",
        # Angle brackets used in algorithm input notation ⟨ ⟩
        "\u27e8": "<", "\u27e9": ">",
        "\u2329": "<", "\u232a": ">",
        # Floor / ceiling brackets ⌊ ⌋ ⌈ ⌉
        "\u230a": "floor(", "\u230b": ")",
        "\u2308": "ceil(", "\u2309": ")",
        # Symbols & emoji
        "\u26a1": "",   # ⚡ lightning bolt
        "\u2713": "OK", "\u2714": "OK",   # check marks
        "\u2715": "x",  "\u2717": "x",    # cross marks
        "\u00d7": "x",  # multiplication sign (already above, safe duplicate)
        "\u2022": "-",  # bullet
        "\u25a0": "",   # black square itself — strip completely
        "\u25cf": "-",  # black circle
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    # Strip $$...$$ LaTeX blocks (not renderable in xhtml2pdf)
    text = re.sub(r'\$\$.*?\$\$', '[see formula in manuscript PDF]', text, flags=re.DOTALL)
    # Strip inline $...$ too
    text = re.sub(r'\$[^$]+?\$', '', text)
    # Remove markdown links pointing to local file:// paths (xhtml2pdf can't handle them)
    text = re.sub(r'\[([^\]]+)\]\(file://[^\)]+\)', r'\1', text)
    return text

def build_pdf(md_path: str, out_path: str) -> bool:
    md_content = Path(md_path).read_text(encoding="utf-8")
    clean_md = sanitize(md_content)

    html_body = markdown.markdown(
        clean_md,
        extensions=["tables", "fenced_code", "nl2br"]
    )

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Mock Any Exam - Custom Technical Report</title>
<style>
{PREMIUM_CSS}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "wb") as f:
        status = pisa.CreatePDF(full_html, dest=f)

    if not status.err and out.exists() and out.stat().st_size > 0:
        print(f"[OK] PDF compiled: {out.resolve()} ({out.stat().st_size:,} bytes)")
        return True
    else:
        print(f"[FAIL] xhtml2pdf error: {status.err}")
        return False

if __name__ == "__main__":
    ok = build_pdf(ARTIFACT_PATH, OUTPUT_PDF)
    if ok:
        print("[DONE] Custom Report PDF ready.")
    else:
        print("[ERROR] PDF generation failed.")
