"""Pre-Submission Audit Report Generator (Step 8).

Collects the results from ALL 8 pipeline steps and generates:
  1. A structured Markdown audit report (output/audit_report.md)
  2. A PDF version of the audit report (output/audit_report.pdf)

The audit report is a transparent, human-readable record of every change
made to the manuscript during the pipeline — suitable for author review
before final submission to a Q1 journal.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def generate_audit_report(pipeline_results: Dict[str, Any], output_dir: str,
                           title: str, author: str) -> Dict[str, str]:
    """Generates comprehensive pre-submission audit report.
    
    Args:
        pipeline_results: Dict containing results from each of the 8 pipeline steps.
        output_dir: Directory to write audit report files.
        title: Paper title.
        author: Author name.
    
    Returns:
        Dict with paths to generated audit_report.md and audit_report.pdf.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    md_content = _build_audit_markdown(pipeline_results, title, author)
    
    import re
    safe_title = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')[:50]
    if not safe_title:
        safe_title = "audit_report"
    
    # Write markdown audit report
    md_file = out_path / f"{safe_title}_audit.md"
    md_file.write_text(md_content, encoding="utf-8")
    
    # Attempt PDF generation
    pdf_file = out_path / f"{safe_title}_audit.pdf"
    pdf_generated = False
    try:
        from open_deep_research.pdf_generator import generate_pdf_from_markdown
        pdf_generated = generate_pdf_from_markdown(md_content, str(pdf_file),
                                                    title=f"Audit Report — {title}", author=author)
    except Exception as e:
        print(f"[Audit Report] PDF generation failed: {e}")
    
    print(f"[Audit Report] Written → {md_file}")
    if pdf_generated:
        print(f"[Audit Report] PDF compiled → {pdf_file}")
    
    return {
        "audit_md": str(md_file),
        "audit_pdf": str(pdf_file) if pdf_generated else None,
    }


def _build_audit_markdown(results: Dict[str, Any], title: str, author: str) -> str:
    """Builds the full audit report markdown string."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    # Overall Q1 Readiness Score (from Step 4)
    preflight = results.get("preflight_audit", {})
    q1_score = preflight.get("readiness_score", "N/A")
    q1_status = preflight.get("q1_status", "UNKNOWN")
    score_emoji = "✅" if str(q1_score) == "100" else ("⚠️" if int(q1_score or 0) >= 80 else "❌")
    
    # AI Signal stats (from Step 5)
    ai_audit = results.get("ai_signal_audit", {})
    ai_before = ai_audit.get("avg_ai_score_before", "N/A")
    ai_after = ai_audit.get("avg_ai_score_after", "N/A")
    ai_delta = ai_audit.get("ai_signal_delta", "N/A")
    ai_rewrites = ai_audit.get("paragraphs_rewritten", 0)
    
    # Citation stats (from Step 1)
    citation_stats = results.get("citation_stats", {})
    placeholders_fixed = citation_stats.get("dois_corrected", 0)
    claims_reframed = citation_stats.get("claims_reframed", 0)
    
    # Reference audit (from Step 6)
    ref_audit = results.get("reference_audit", {})
    orphans = ref_audit.get("orphan_citations", [])
    ghosts = ref_audit.get("ghost_references", [])
    ref_score = ref_audit.get("completeness_score", "N/A")
    
    # Abstract audit (from Step 7)
    abstract_audit = results.get("abstract_audit", {})
    abstract_score = abstract_audit.get("quality_score", "N/A")
    abstract_issues = abstract_audit.get("issues", [])
    abstract_rewritten = abstract_audit.get("abstract_rewritten_by_llm", False)
    
    # Benchmark (from Step 2)
    benchmark_injected = results.get("benchmark_injected", False)
    
    # Algorithm (from Step 3)
    algo_blocks = results.get("algo_blocks_added", 0)
    
    lines = [
        f"# Pre-Submission Q1 Audit Report",
        f"",
        f"**Paper Title:** {title}",
        f"**Author:** {author}",
        f"**Generated:** {now}",
        f"**Pipeline Version:** v2.0 (10/10 Architecture)",
        f"",
        f"---",
        f"",
        f"## {score_emoji} Overall Q1 Readiness Score: {q1_score}/100 — {q1_status}",
        f"",
        f"---",
        f"",
        f"## Step-by-Step Pipeline Results",
        f"",
        f"### Step 1 — Citation Integrity Guardrail",
        f"| Metric | Result |",
        f"| :--- | :--- |",
        f"| Placeholder DOIs detected | {citation_stats.get('placeholders_detected', 0)} |",
        f"| DOIs auto-corrected via CrossRef | {placeholders_fixed} |",
        f"| Overclaiming claims reframed | {claims_reframed} |",
        f"",
        f"### Step 2 — Experimental Benchmark Protocol",
        f"| Metric | Result |",
        f"| :--- | :--- |",
        f"| Evaluation protocol injected | {'Yes' if benchmark_injected else 'Skipped (real data found)'} |",
        f"",
        f"### Step 3 — Algorithmic Formalization",
        f"| Metric | Result |",
        f"| :--- | :--- |",
        f"| Algorithm blocks injected | {algo_blocks} |",
        f"| AI filler phrases replaced | 40+ vocabulary applied |",
        f"",
        f"### Step 4 — Structural Pre-Flight Audit",
        f"| Section | Present |",
        f"| :--- | :--- |",
    ]
    
    # Section status table
    section_status = preflight.get("section_status", {})
    for section, present in section_status.items():
        icon = "✅" if present else "❌"
        lines.append(f"| {section} | {icon} |")
    
    missing_fixed = preflight.get("missing_sections_fixed", [])
    if missing_fixed:
        lines.append(f"")
        lines.append(f"**Auto-Injected Sections:** {', '.join(missing_fixed)}")
    
    lines += [
        f"",
        f"### Step 5 — AI Writing Signal Reduction",
        f"| Metric | Result |",
        f"| :--- | :--- |",
        f"| Paragraphs analyzed | {ai_audit.get('paragraphs_analyzed', 'N/A')} |",
        f"| High-AI-signal paragraphs (before) | {ai_audit.get('high_ai_signal_before', 'N/A')} |",
        f"| High-AI-signal paragraphs (after) | {ai_audit.get('high_ai_signal_after', 'N/A')} |",
        f"| Average AI score (before) | {ai_before} |",
        f"| Average AI score (after) | {ai_after} |",
        f"| **AI Signal Improvement (Δ)** | **{ai_delta}** |",
        f"| Paragraphs rewritten by LLM | {ai_rewrites} |",
        f"",
    ]
    
    if ai_audit.get("rewrite_log"):
        lines.append("**Rewrite Log:**")
        for entry in ai_audit["rewrite_log"]:
            lines.append(f"- Score {entry['original_score']}: *\"{entry['paragraph_preview']}\"* → {entry['status']}")
        lines.append("")
    
    lines += [
        f"### Step 6 — Reference Completeness Audit",
        f"| Metric | Result |",
        f"| :--- | :--- |",
        f"| Bibliography entries found | {len(ref_audit.get('bibliography_entries_found', []))} |",
        f"| In-text citations found | {len(ref_audit.get('inline_citations_found', []))} |",
        f"| Completeness score | {ref_score}/100 |",
    ]
    
    if orphans:
        lines.append(f"| ❌ Orphan citations (critical) | {orphans} |")
    else:
        lines.append(f"| ✅ Orphan citations | None |")
    
    if ghosts:
        lines.append(f"| ⚠️ Ghost references | {ghosts} |")
    else:
        lines.append(f"| ✅ Ghost references | None |")
    
    lines += [
        f"",
        f"### Step 7 — Abstract Quality Analysis",
        f"| Metric | Result |",
        f"| :--- | :--- |",
        f"| Abstract word count | {abstract_audit.get('word_count', 'N/A')} |",
        f"| Quality score | {abstract_score}/100 |",
        f"| Keyword coverage | {abstract_audit.get('keyword_coverage_pct', 'N/A')} |",
        f"| Overclaiming phrases fixed | {abstract_audit.get('overclaiming_issues_fixed', 0)} |",
        f"| Abstract rewritten by LLM | {'Yes' if abstract_rewritten else 'No'} |",
    ]
    
    if abstract_issues:
        lines.append("")
        lines.append("**Abstract Issues Detected:**")
        for issue in abstract_issues:
            lines.append(f"- {issue}")
    
    # IMRaD table
    imrad = abstract_audit.get("imrad_coverage", {})
    if imrad:
        lines += [
            f"",
            f"**IMRaD Coverage:**",
            f"| Component | Present |",
            f"| :--- | :--- |",
        ]
        for component, present in imrad.items():
            icon = "✅" if present else "❌"
            lines.append(f"| {component} | {icon} |")
    
    lines += [
        f"",
        f"---",
        f"",
        f"## Final Recommendations",
        f"",
    ]
    
    recommendations = _build_recommendations(results)
    for rec in recommendations:
        lines.append(f"- {rec}")
    
    lines += [
        f"",
        f"---",
        f"",
        f"*This audit report was generated automatically by the Q1 Research Paper Pipeline v2.0.*",
        f"*All automated changes are reversible. Manual review is recommended before submission.*",
    ]
    
    return "\n".join(lines)


def _build_recommendations(results: Dict) -> list:
    """Generates actionable recommendations from all audit results."""
    recs = []
    
    ref_audit = results.get("reference_audit", {})
    if ref_audit.get("orphan_citations"):
        recs.append(f"🔴 **CRITICAL**: Add bibliography entries for orphan citations {ref_audit['orphan_citations']} before submission.")
    if ref_audit.get("ghost_references"):
        recs.append(f"⚠️ **WARNING**: Remove or cite unused references {ref_audit['ghost_references']}.")
    if ref_audit.get("entries_missing_doi"):
        recs.append(f"🔗 **INFO**: Add verified DOIs to references {ref_audit['entries_missing_doi']}.")
    
    abstract_audit = results.get("abstract_audit", {})
    if abstract_audit.get("quality_score", 100) < 70:
        recs.append("⚠️ **WARNING**: Abstract quality score below 70. Review rewritten abstract carefully.")
    
    ai_audit = results.get("ai_signal_audit", {})
    if ai_audit.get("high_ai_signal_after", 0) > 0:
        recs.append(f"📝 **INFO**: {ai_audit['high_ai_signal_after']} paragraphs still have elevated AI signal. Manual paraphrasing recommended.")
    
    preflight = results.get("preflight_audit", {})
    if preflight.get("readiness_score", 100) < 100:
        recs.append("📋 **INFO**: Not all Q1 structural sections passed. Review section status table above.")
    
    if not recs:
        recs.append("✅ All checks passed. The manuscript meets Q1 structural standards. Proceed to journal submission.")
    
    return recs
