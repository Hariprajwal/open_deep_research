"""
latex_ieee_generator.py
=======================
Pure-function helpers for generating IEEEtran-compliant LaTeX components.

Based on the awesome-ieee-report SKILL.md rules:
  - \documentclass[conference]{IEEEtran}
  - Pseudocode only via algorithm + algorithmic environments
  - booktabs tables
  - \cite{} + .bib references
  - No source code dumps, no file paths, no class/function names in report body
  - Minimum 3 figures (as \includegraphics placeholders)
  - Academic tone throughout
"""

import re
import textwrap
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. Text / prose helpers
# ---------------------------------------------------------------------------

def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in plain text strings."""
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&",  r"\&"),
        ("%",  r"\%"),
        ("$",  r"\$"),
        ("#",  r"\#"),
        ("_",  r"\_"),
        ("{",  r"\{"),
        ("}",  r"\}"),
        ("~",  r"\textasciitilde{}"),
        ("^",  r"\textasciicircum{}"),
    ]
    for src, dst in replacements:
        text = text.replace(src, dst)
    return text


def smart_escape(text: str) -> str:
    """
    Escape LaTeX special characters in plain-text regions only.
    Content inside $...$ (inline math) or $$...$$ (display math)
    is left completely untouched so LaTeX math commands render correctly.
    """
    # Split on math regions; keep delimiters via capturing group
    parts = re.split(r'(\$\$[^$]*?\$\$|\$[^$]*?\$)', text)
    result = []
    for part in parts:
        if part.startswith('$'):
            result.append(part)          # math mode — pass through as-is
        else:
            result.append(escape_latex(part))  # plain text — escape
    return ''.join(result)


def md_inline_to_latex(text: str) -> str:
    """Convert inline markdown (bold, italic, code) to LaTeX equivalents."""
    # Bold+italic: ***text***
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\\textbf{\\textit{\1}}', text)
    # Bold: **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    # Italic: *text*
    text = re.sub(r'\*(.*?)\*', r'\\textit{\1}', text)
    # Inline code: `text`
    text = re.sub(r'`([^`]+)`', r'\\texttt{\1}', text)
    return text


def md_paragraph_to_latex(md_text: str) -> str:
    """
    Convert a plain markdown paragraph block to LaTeX prose.
    Handles inline formatting only — NOT block-level structure
    (sections/algorithms/tables must be handled separately).
    """
    lines = []
    for line in md_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("|") or line.startswith("```"):
            continue
        line = md_inline_to_latex(line)
        lines.append(line)
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# 2. Section / subsection builders
# ---------------------------------------------------------------------------

def section(title: str, body: str = "") -> str:
    """Build a top-level \\section{} block."""
    t = escape_latex(title)
    block = f"\\section{{{t}}}\n"
    if body:
        block += f"{body}\n"
    return block


def subsection(title: str, body: str = "") -> str:
    """Build a \\subsection{} block."""
    t = escape_latex(title)
    block = f"\\subsection{{{t}}}\n"
    if body:
        block += f"{body}\n"
    return block


def subsubsection(title: str, body: str = "") -> str:
    """Build a \\subsubsection{} block."""
    t = escape_latex(title)
    block = f"\\subsubsection{{{t}}}\n"
    if body:
        block += f"{body}\n"
    return block


# ---------------------------------------------------------------------------
# 3. Algorithm environment (IEEE algorithm + algpseudocode)
# ---------------------------------------------------------------------------

def build_algorithm_env(
    steps: list[str],
    caption: str,
    label: str,
    inputs: str = "",
    outputs: str = "",
    algorithm_number: int | None = None,
) -> str:
    """
    Generate an IEEE-compliant \\begin{algorithm} environment.

    Args:
        steps:    List of pseudocode lines. Prefix with INDENT (4 spaces)
                  for indented lines. Use special prefixes:
                    'IF:', 'ELSE:', 'ENDIF', 'FOR:', 'ENDFOR', 'WHILE:', 'ENDWHILE',
                    'RETURN:', 'STATE:' for plain statement
        caption:  Algorithm caption text.
        label:    LaTeX \\label{alg:...} suffix.
        inputs:   Input description for \\REQUIRE line (optional).
        outputs:  Output description for \\ENSURE line (optional).

    Returns:
        Complete LaTeX algorithm block as a string.
    """
    lines = ["\\begin{algorithm}[t]"]
    lines.append(f"\\caption{{{escape_latex(caption)}}}")
    lines.append(f"\\label{{alg:{label}}}")
    lines.append("\\begin{algorithmic}[1]")

    if inputs:
        lines.append(f"\\Require {smart_escape(inputs)}")
    if outputs:
        lines.append(f"\\Ensure {smart_escape(outputs)}")

    for step in steps:
        stripped = step.strip()
        indent = "    " if step.startswith("    ") else ""

        if stripped.upper().startswith("IF ") or stripped.upper().startswith("IF:"):
            cond = re.sub(r'^if\s*:?\s*', '', stripped, flags=re.IGNORECASE)
            lines.append(f"{indent}\\If{{{smart_escape(cond)}}}")
        elif stripped.upper() in ("ELSE", "ELSE:"):
            lines.append(f"{indent}\\Else")
        elif stripped.upper() in ("ENDIF", "END IF", "END"):
            lines.append(f"{indent}\\EndIf")
        elif stripped.upper().startswith("FOR ") or stripped.upper().startswith("FOR:"):
            cond = re.sub(r'^for\s*:?\s*', '', stripped, flags=re.IGNORECASE)
            lines.append(f"{indent}\\For{{{smart_escape(cond)}}}")
        elif stripped.upper() in ("ENDFOR", "END FOR"):
            lines.append(f"{indent}\\EndFor")
        elif stripped.upper().startswith("WHILE ") or stripped.upper().startswith("WHILE:"):
            cond = re.sub(r'^while\s*:?\s*', '', stripped, flags=re.IGNORECASE)
            lines.append(f"{indent}\\While{{{smart_escape(cond)}}}")
        elif stripped.upper() in ("ENDWHILE", "END WHILE"):
            lines.append(f"{indent}\\EndWhile")
        elif stripped.upper().startswith("RETURN ") or stripped.upper().startswith("RETURN:"):
            val = re.sub(r'^return\s*:?\s*', '', stripped, flags=re.IGNORECASE)
            lines.append(f"{indent}\\State \\textbf{{return}} {smart_escape(val)}")
        elif stripped.upper().startswith("COMMENT:"):
            cmt = re.sub(r'^comment\s*:?\s*', '', stripped, flags=re.IGNORECASE)
            lines.append(f"{indent}\\Comment{{{smart_escape(cmt)}}}")
        else:
            lines.append(f"{indent}\\State {smart_escape(stripped)}")

    lines.append("\\end{algorithmic}")
    lines.append("\\end{algorithm}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Table builder (booktabs style)
# ---------------------------------------------------------------------------

def build_table_env(
    headers: list[str],
    rows: list[list[str]],
    caption: str,
    label: str,
    col_format: str = "",
    position: str = "!t",
    footnote: str = "",
) -> str:
    """
    Build a booktabs-style LaTeX table for IEEE two-column format.

    Args:
        headers:    Column header strings.
        rows:       List of rows (each row is a list of cell strings).
        caption:    Table caption (placed above in IEEE style).
        label:      LaTeX \\label{tab:...} suffix.
        col_format: Column format string e.g. 'lccr'. Auto-generated if empty.
        position:   Float position specifier (default '!t').
        footnote:   Optional footnote text below the table.

    Returns:
        Complete LaTeX table block.
    """
    n_cols = len(headers)
    if not col_format:
        # First col left-aligned, rest centered
        col_format = "l" + "c" * (n_cols - 1)

    lines = [f"\\begin{{table}}[{position}]"]
    lines.append("\\centering")
    lines.append(f"\\caption{{\\uppercase{{{caption}}}}}")
    lines.append(f"\\label{{tab:{label}}}")
    lines.append(f"\\begin{{tabular}}{{{col_format}}}")
    lines.append("\\toprule")

    # Header row
    header_cells = " & ".join(f"\\textbf{{{h}}}" for h in headers)
    lines.append(f"{header_cells} \\\\")
    lines.append("\\midrule")

    # Data rows
    for row in rows:
        cells = " & ".join(str(c) for c in row)
        lines.append(f"{cells} \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")

    if footnote:
        lines.append(f"\\begin{{tablenotes}}\\footnotesize\\item {footnote}\\end{{tablenotes}}")

    lines.append("\\end{table}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. Figure builder (\includegraphics with placeholder support)
# ---------------------------------------------------------------------------

def build_figure_env(
    image_path: str,
    caption: str,
    label: str,
    width: str = "\\columnwidth",
    position: str = "!t",
    span_columns: bool = False,
) -> str:
    """
    Build an IEEE figure environment with \\includegraphics.

    Args:
        image_path:    Relative path to the image file (e.g. 'figures/fig1.png').
        caption:       Figure caption text.
        label:         LaTeX \\label{fig:...} suffix.
        width:         Width spec (default: \\columnwidth for single-col figure).
        position:      Float position (default '!t').
        span_columns:  If True, use figure* for a full-width spanning figure.

    Returns:
        Complete LaTeX figure block.
    """
    env = "figure*" if span_columns else "figure"
    lines = [f"\\begin{{{env}}}[{position}]"]
    lines.append("\\centering")
    lines.append(f"\\includegraphics[width={width}]{{{image_path}}}")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{fig:{label}}}")
    lines.append(f"\\end{{{env}}}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6. BibTeX / reference builder
# ---------------------------------------------------------------------------

def build_bibtex_entry(
    key: str,
    entry_type: str,
    fields: dict[str, str],
) -> str:
    """
    Build a single BibTeX entry string.

    Args:
        key:        Citation key (e.g. 'brown2020gpt3').
        entry_type: BibTeX type ('article', 'inproceedings', 'misc', etc.).
        fields:     Dict of field name → value pairs.

    Returns:
        Formatted BibTeX entry string.
    """
    lines = [f"@{entry_type}{{{key},"]
    for field, value in fields.items():
        lines.append(f"  {field} = {{{value}}},")
    lines.append("}")
    return "\n".join(lines)


def generate_bibtex_file(references: list[dict]) -> str:
    """
    Generate a complete .bib file content from a list of reference dicts.

    Each dict must have:
        'key', 'type', and field key-value pairs.

    Example reference dict:
        {
            'key': 'wei2022cot',
            'type': 'article',
            'author': 'Wei, Jason and others',
            'title': 'Chain-of-Thought Prompting Elicits Reasoning in Large Language Models',
            'journal': 'Advances in Neural Information Processing Systems',
            'year': '2022',
        }
    """
    entries = []
    for ref in references:
        key = ref.pop("key")
        entry_type = ref.pop("type")
        entry = build_bibtex_entry(key, entry_type, ref)
        entries.append(entry)
        # Restore so caller's dict isn't mutated
        ref["key"] = key
        ref["type"] = entry_type
    return "\n\n".join(entries)


# ---------------------------------------------------------------------------
# 7. Full document assembler
# ---------------------------------------------------------------------------

def assemble_ieee_document(
    title: str,
    authors: list[dict],
    abstract: str,
    keywords: list[str],
    sections: list[str],
    bib_filename: str = "references",
    packages_extra: list[str] | None = None,
) -> str:
    """
    Assemble a complete IEEEtran LaTeX document.

    Args:
        title:          Paper title string.
        authors:        List of author dicts with keys: name, affiliation, email.
        abstract:       Abstract text (plain, no LaTeX markup needed).
        keywords:       List of index term strings.
        sections:       List of pre-built LaTeX section strings (from section(),
                        subsection(), build_algorithm_env(), etc.).
        bib_filename:   Base name of .bib file (without extension).
        packages_extra: Additional \\usepackage lines to inject.

    Returns:
        Complete .tex document as a string, ready to write to disk.
    """
    # --- Preamble ---
    preamble_lines = [
        r"\documentclass[conference]{IEEEtran}",
        r"\IEEEoverridecommandlockouts",
        "",
        r"% Core packages",
        r"\usepackage{amsmath,amssymb,amsfonts}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\usepackage{cite}",
        r"\usepackage{url}",
        r"\usepackage{hyperref}",
        r"\usepackage{algorithm}",
        r"\usepackage{algpseudocode}",
        r"\usepackage{xcolor}",
        r"\usepackage{multirow}",
        r"\usepackage{array}",
        r"\usepackage{caption}",
        r"\usepackage{subcaption}",
        r"\usepackage{microtype}",
        r"\usepackage{balance}",
    ]

    if packages_extra:
        preamble_lines.append("")
        preamble_lines.append("% Additional packages")
        preamble_lines.extend(packages_extra)

    # --- Title block ---
    preamble_lines += [
        "",
        f"\\title{{{escape_latex(title)}}}",
        "",
    ]

    # Build \\author block
    author_blocks = []
    for i, a in enumerate(authors):
        name = escape_latex(a.get("name", "Author"))
        affil = escape_latex(a.get("affiliation", ""))
        email = a.get("email", "")
        block = (
            f"\\IEEEauthorblockN{{{name}}}\n"
            f"\\IEEEauthorblockA{{{affil} \\\\\n"
            f"\\textit{{Email:}} \\texttt{{{email}}}}}"
        )
        author_blocks.append(block)

    if len(author_blocks) == 1:
        preamble_lines.append(f"\\author{{\n{author_blocks[0]}\n}}")
    else:
        joined = "\n\\and\n".join(author_blocks)
        preamble_lines.append(f"\\author{{\n{joined}\n}}")

    # --- Document body ---
    doc_lines = [
        "",
        "\\begin{document}",
        "\\maketitle",
        "",
        "\\begin{abstract}",
        textwrap.fill(abstract, width=80),
        "\\end{abstract}",
        "",
        "\\begin{IEEEkeywords}",
        ", ".join(escape_latex(k) for k in keywords),
        "\\end{IEEEkeywords}",
        "",
    ]

    # Sections
    for sec in sections:
        doc_lines.append(sec)
        doc_lines.append("")

    # Bibliography
    doc_lines += [
        "\\balance",
        f"\\bibliographystyle{{IEEEtran}}",
        f"\\bibliography{{{bib_filename}}}",
        "",
        "\\end{document}",
    ]

    return "\n".join(preamble_lines) + "\n" + "\n".join(doc_lines)


# ---------------------------------------------------------------------------
# 8. File writer utility
# ---------------------------------------------------------------------------

def write_ieee_paper(
    output_dir: str,
    tex_content: str,
    bib_content: str,
    figure_src_paths: list[str] | None = None,
    tex_filename: str = "paper.tex",
    bib_filename: str = "references.bib",
) -> dict:
    """
    Write the .tex and .bib files to disk, and optionally copy figure images.

    Args:
        output_dir:       Directory to write files into (created if needed).
        tex_content:      Complete .tex document string.
        bib_content:      Complete .bib file string.
        figure_src_paths: Optional list of absolute paths to figure images to copy.
        tex_filename:     Name of the output .tex file.
        bib_filename:     Name of the output .bib file.

    Returns:
        Dict with output file paths and copy stats.
    """
    import shutil

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    figures_dir = out / "figures"
    figures_dir.mkdir(exist_ok=True)

    tex_path = out / tex_filename
    bib_path = out / bib_filename

    tex_path.write_text(tex_content, encoding="utf-8")
    bib_path.write_text(bib_content, encoding="utf-8")

    copied_figures = []
    if figure_src_paths:
        for src in figure_src_paths:
            src_path = Path(src)
            if src_path.exists():
                dst = figures_dir / src_path.name
                shutil.copy2(src_path, dst)
                copied_figures.append(str(dst))

    return {
        "tex_file": str(tex_path),
        "bib_file": str(bib_path),
        "figures_dir": str(figures_dir),
        "figures_copied": copied_figures,
    }
