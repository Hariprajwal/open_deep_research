"""Native PDF Generator for Open Deep Research using xhtml2pdf (Pure Python)."""

import os
from pathlib import Path
import markdown
from xhtml2pdf import pisa

IEEE_PDF_CSS = """
@page {
    size: a4;
    margin: 1.5cm;
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.3;
    color: #111;
}

.paper-title {
    font-size: 16pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 8px;
}

.paper-author {
    font-size: 11pt;
    font-style: italic;
    text-align: center;
    margin-bottom: 15px;
}

.divider {
    border-bottom: 1px solid #000;
    margin: 15px 0;
}

h1 {
    font-size: 14pt;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    margin-top: 15px;
    margin-bottom: 10px;
}

h2 {
    font-size: 11pt;
    font-weight: bold;
    border-bottom: 1px solid #444;
    padding-bottom: 2px;
    margin-top: 15px;
    margin-bottom: 8px;
    text-transform: uppercase;
}

h3 {
    font-size: 10pt;
    font-weight: bold;
    margin-top: 12px;
    margin-bottom: 5px;
}

p {
    margin-bottom: 8px;
    text-align: justify;
}

ul, ol {
    margin-top: 4px;
    margin-bottom: 8px;
    padding-left: 15px;
}

li {
    margin-bottom: 3px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 9pt;
}

th, td {
    border: 1px solid #555;
    padding: 4px 6px;
    text-align: left;
}

th {
    background-color: #eee;
    font-weight: bold;
}

code {
    font-family: Courier;
    font-size: 8.5pt;
    background-color: #f4f4f4;
}

pre {
    background-color: #f4f4f4;
    border: 1px solid #ccc;
    padding: 6px;
    font-family: Courier;
    font-size: 8.5pt;
}
"""

def generate_pdf_from_markdown(md_content: str, output_pdf_path: str, title: str = "Deep Research Analysis", author: str = "Research Agent System") -> bool:
    """Converts markdown content into a professional PDF using xhtml2pdf."""
    pdf_path = Path(output_pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Convert Markdown to HTML
        html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc'])
        
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{IEEE_PDF_CSS}
</style>
</head>
<body>
<div class="paper-title">{title}</div>
<div class="paper-author">{author}</div>
<div class="divider"></div>
{html_body}
</body>
</html>
"""
        
        # Render HTML to PDF via xhtml2pdf
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
            
        if not pisa_status.err and pdf_path.exists() and pdf_path.stat().st_size > 0:
            print(f"[PDF Gen] Successfully compiled IEEE PDF via xhtml2pdf ({pdf_path.stat().st_size} bytes)")
            return True
        else:
            print(f"[PDF Gen] xhtml2pdf failed with status error: {pisa_status.err}")
            return False
            
    except Exception as e:
        print(f"[PDF Gen] Exception during PDF creation: {e}")
        return False
