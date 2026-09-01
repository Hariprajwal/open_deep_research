"""IEEE Paper Exporter: 8-Step Universal Q1 Research Paper Enhancement Pipeline.

Steps:
  1. Citation Integrity Guardrail      -- CrossRef DOI verification + overclaiming reframing
  2. Experimental Benchmark Protocol   -- Domain-specific Q1-honest evaluation tables
  3. Algorithmic Formalization         -- LLM-derived pseudo-code + 40+ AI filler phrase removal
  4. Structural Pre-Flight Audit       -- Section completeness + LLM-derived Discussion & Contributions
  5. AI Writing Signal Reduction       -- Paragraph scoring + LLM targeted rewriting
  6. Reference Completeness Audit      -- In-text cite <-> bibliography bidirectional check
  7. Abstract Quality Analysis         -- IMRaD structure + word count + LLM rewrite if needed
  8. Audit Report Generation           -- Full pre-submission audit report (MD + PDF)
"""

import os
import re
import subprocess
from pathlib import Path


def export_to_ieee(markdown_report: str, output_dir: str = "output",
                   title: str = "Deep Research Analysis",
                   author: str = "Research Agent System") -> dict:
    """Convert a raw Markdown research report into an IEEE-formatted manuscript
    via the full 8-step Q1 enhancement pipeline.

    Returns:
        Dictionary with file paths and full pipeline_state audit results.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Shared pipeline state -- collects results from each step for the audit report
    pipeline_state = {
        "title": title,
        "author": author,
        "citation_stats": {},
        "benchmark_injected": False,
        "algo_blocks_added": 0,
        "preflight_audit": {},
        "ai_signal_audit": {},
        "reference_audit": {},
        "abstract_audit": {},
    }

    # STEP 1 -- Citation Integrity Guardrail
    try:
        from open_deep_research.citation_verifier import verify_and_fix_citations
        markdown_report, citation_stats = verify_and_fix_citations(markdown_report)
        pipeline_state["citation_stats"] = citation_stats
        print(f"[Step 1 OK] Citation Guardrail: {citation_stats}")
    except Exception as e:
        print(f"[Step 1 SKIP] Citation Guardrail: {e}")

    # STEP 2 -- Experimental Benchmark Protocol
    try:
        from open_deep_research.experiment_benchmarker import inject_experimental_benchmarks
        before_len = len(markdown_report)
        markdown_report = inject_experimental_benchmarks(markdown_report, title)
        pipeline_state["benchmark_injected"] = len(markdown_report) > before_len
        print(f"[Step 2 OK] Benchmark Engine: injected={pipeline_state['benchmark_injected']}")
    except Exception as e:
        print(f"[Step 2 SKIP] Benchmark Engine: {e}")

    # STEP 3 -- Algorithmic Formalization
    try:
        from open_deep_research.algorithmic_formalizer import formalize_algorithms_and_math
        markdown_report, algo_blocks = formalize_algorithms_and_math(markdown_report, title)
        pipeline_state["algo_blocks_added"] = algo_blocks
        print(f"[Step 3 OK] Algorithmic Formalizer: {algo_blocks} blocks injected")
    except Exception as e:
        print(f"[Step 3 SKIP] Algorithmic Formalizer: {e}")

    # STEP 4 -- Structural Pre-Flight Audit
    try:
        from open_deep_research.submission_verifier import audit_and_enrich_submission_structure
        markdown_report, preflight_audit = audit_and_enrich_submission_structure(markdown_report, title)
        pipeline_state["preflight_audit"] = preflight_audit
        score = preflight_audit.get("readiness_score", 0)
        status = preflight_audit.get("q1_status", "UNKNOWN")
        print(f"[Step 4 OK] Submission Verifier: {score}/100 -- {status}")
    except Exception as e:
        print(f"[Step 4 SKIP] Submission Verifier: {e}")

    # STEP 5 -- AI Writing Signal Reduction
    try:
        from open_deep_research.ai_signal_reducer import reduce_ai_writing_signals
        markdown_report, ai_audit = reduce_ai_writing_signals(markdown_report, title, max_rewrites=5)
        pipeline_state["ai_signal_audit"] = ai_audit
        delta = ai_audit.get("ai_signal_delta", 0)
        rewrites = ai_audit.get("paragraphs_rewritten", 0)
        print(f"[Step 5 OK] AI Signal Reducer: delta={delta}, rewrites={rewrites}")
    except Exception as e:
        print(f"[Step 5 SKIP] AI Signal Reducer: {e}")

    # STEP 6 -- Reference Completeness Audit
    try:
        from open_deep_research.reference_auditor import audit_reference_completeness
        markdown_report, ref_audit = audit_reference_completeness(markdown_report)
        pipeline_state["reference_audit"] = ref_audit
        ref_score = ref_audit.get("completeness_score", 0)
        orphans = ref_audit.get("orphan_citations", [])
        print(f"[Step 6 OK] Reference Auditor: completeness={ref_score}/100, orphans={orphans}")
    except Exception as e:
        print(f"[Step 6 SKIP] Reference Auditor: {e}")

    # STEP 7 -- Abstract Quality Analysis
    try:
        from open_deep_research.abstract_analyzer import analyze_and_improve_abstract
        markdown_report, abstract_audit = analyze_and_improve_abstract(markdown_report, title)
        pipeline_state["abstract_audit"] = abstract_audit
        ab_score = abstract_audit.get("quality_score", 0)
        rewritten = abstract_audit.get("abstract_rewritten_by_llm", False)
        print(f"[Step 7 OK] Abstract Analyzer: quality={ab_score}/100, rewritten={rewritten}")
    except Exception as e:
        print(f"[Step 7 SKIP] Abstract Analyzer: {e}")

    # STEP 8 -- Audit Report Generation
    audit_files = {}
    try:
        from open_deep_research.audit_report_generator import generate_audit_report
        audit_files = generate_audit_report(pipeline_state, output_dir, title, author)
        print(f"[Step 8 OK] Audit Report generated: {list(audit_files.keys())}")
    except Exception as e:
        print(f"[Step 8 SKIP] Audit Report: {e}")

    # FORMAT & EXPORT
    ieee_md = _format_markdown_for_ieee(markdown_report, title, author)
    
    import re
    safe_title = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')[:50]
    if not safe_title:
        safe_title = "ieee_paper"
        
    md_file = out_path / f"{safe_title}.md"
    md_file.write_text(ieee_md, encoding="utf-8")

    typ_file = out_path / f"{safe_title}.typ"
    typ_file.write_text(_generate_typst_content(markdown_report, title, author), encoding="utf-8")

    # --- PDF 1: Standard formatted PDF (existing) ---
    pdf_file = out_path / f"{safe_title}.pdf"
    pdf_compiled = False
    try:
        from open_deep_research.pdf_generator import generate_pdf_from_markdown
        pdf_compiled = generate_pdf_from_markdown(markdown_report, str(pdf_file), title=title, author=author)
    except Exception as e:
        print(f"[Export] PDF generation warning: {e}")

    print(f"[Export] PDF compiled={pdf_compiled} | Size={pdf_file.stat().st_size if pdf_compiled else 0} bytes")

    # --- PDF 2: IEEE Conference Two-Column Format (IEEEtran style) ---
    conf_pdf_file = out_path / f"{safe_title}_conference.pdf"
    conf_pdf_compiled = False
    try:
        from open_deep_research.ieee_conference_pdf import generate_ieee_conference_pdf
        conf_pdf_compiled = generate_ieee_conference_pdf(
            md_content=markdown_report,
            output_pdf_path=str(conf_pdf_file),
            title=title,
            author=author,
        )
    except Exception as e:
        print(f"[IEEE Conf PDF] Warning: {e}")

    return {
        "markdown_file": str(md_file),
        "typst_file": str(typ_file),
        "pdf_file": str(pdf_file) if pdf_compiled else None,
        "pdf_compiled": pdf_compiled,
        "conference_pdf_file": str(conf_pdf_file) if conf_pdf_compiled else None,
        "conference_pdf_compiled": conf_pdf_compiled,
        "audit_report": audit_files.get("audit_md"),
        "pipeline_state": pipeline_state,
    }


def _strip_stacked_headers(text: str, title: str, author: str) -> str:
    """Removes ALL previously prepended headers from the document.
    Handles the case where the pipeline was run multiple times on the
    already-formatted output, stacking headers even if text was injected between them.
    """
    import re
    
    # 1. Globally remove any "**Author(s)**: [name]" lines
    text = re.sub(r'\n?\*\*Author\(s\)\*\*:\s*.*?\n', '\n', text, flags=re.IGNORECASE)
    
    # 2. Globally remove standalone "## ABSTRACT" or "Abstract" headers
    # that are followed immediately by another header, a divider, or the title
    text = re.sub(r'\n?##\s+ABSTRACT\s*\n(?=#|\n?---|Intell|\n)', '\n', text, flags=re.IGNORECASE)
    
    # Remove horizontal dividers
    text = re.sub(r'\n?---\s*\n', '\n\n', text)
    
    # 3. Globally remove the title if it appears multiple times (with or without #)
    # This catches corrupted bare titles injected by previous runs
    escaped_title = re.escape(title)
    text = re.sub(rf'^#?\s*{escaped_title}.*?\n', '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up excessive newlines left behind
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    
    return text


def _format_markdown_for_ieee(text: str, title: str, author: str) -> str:
    """Format markdown text into IEEE paper structure.
    Idempotent: strips any previously stacked headers before prepending one clean copy.
    """
    # Strip ALL previously stacked header blocks from top of document
    clean_text = _strip_stacked_headers(text, title, author)

    header = (
        f"# {title}\n\n"
        f"**Author(s)**: {author}\n\n"
        f"---\n\n"
        f"## ABSTRACT\n\n"
    )
    return header + clean_text.lstrip()


def _generate_typst_content(text: str, title: str, author: str) -> str:
    """Convert Markdown report to Typst IEEE template markup."""
    abstract_match = re.search(
        r'(?:Abstract|ABSTRACT)[:\s\n]+(.*?)(?=\n#|\n\n[A-Z\s]{4,})', text, re.DOTALL | re.IGNORECASE
    )
    abstract_text = (abstract_match.group(1).strip() if abstract_match
                     else "This paper presents a comprehensive research synthesis.")

    clean_body = re.sub(r'#([a-zA-Z]+)', r'\\#\1', text)

    return f"""#import "../templates/ieee_template.typ": ieee

#show: ieee.with(
  title: [{title}],
  authors: (
    (name: "{author}", affiliation: "Open Deep Research Engine", email: "researcher@agent.ai"),
  ),
  abstract: [{abstract_text}],
  keywords: ("Deep Research", "Multi-Agent System", "Literature Survey", "IEEE Format"),
)

{clean_body}
"""
