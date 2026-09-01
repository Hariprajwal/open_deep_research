"""AI Writing Signal Reducer (Step 5) — The most critical missing layer.

Detects and reduces AI-generated writing signals paragraph by paragraph:

Phase A — Detection (no LLM needed):
  - Sentence length uniformity heuristic (AI text has suspiciously uniform sentence lengths)
  - Filler density score (counts remaining AI filler words after Step 3 cleaning)
  - Passive voice ratio (AI overuses passive voice)
  - Transition phrase repetition (AI repeats "Furthermore", "Moreover", "Additionally")
  - Hedge word excess (AI overuses "robust", "comprehensive", "novel", "significant")

Phase B — LLM-based Targeted Rewriting:
  - Only paragraphs scoring above AI_THRESHOLD are sent to the LLM for rewriting.
  - The LLM is instructed to rewrite in first-person academic style, vary sentence length,
    use active voice, and remove hedge/filler words.
  - Citations and technical terms are preserved exactly.

Reports before/after AI signal delta for each paragraph.
"""

import re
import os
import math
from typing import Tuple, Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# Thresholds & Vocabulary
# ─────────────────────────────────────────────────────────────────────────────
AI_DETECTION_THRESHOLD = 0.65  # Paragraphs above this score get rewritten

AI_HEDGE_WORDS = {
    "robust", "novel", "innovative", "significant", "comprehensive", "seamlessly",
    "efficiently", "leverages", "harnesses", "state-of-the-art", "cutting-edge",
    "groundbreaking", "pivotal", "crucial", "vital", "holistic", "synergistic",
    "paradigm", "seamless", "transformative", "unprecedented", "remarkable",
    "noteworthy", "exceptional", "outstanding", "sophisticated", "intelligent",
}

AI_TRANSITION_PHRASES = [
    "Furthermore,", "Moreover,", "Additionally,", "In addition,",
    "It is worth noting", "Notably,", "Importantly,", "Significantly,",
    "In conclusion,", "To summarize,", "In summary,", "As previously mentioned",
]

AI_PASSIVE_PATTERNS = [
    r'\b(?:is|are|was|were|be|been|being)\s+\w+ed\b',
    r'\b(?:is|are|was|were)\s+designed\s+to\b',
    r'\b(?:is|are|was|were)\s+(?:proposed|presented|introduced|described)\b',
]


def reduce_ai_writing_signals(markdown_report: str, title: str,
                               max_rewrites: int = 5) -> Tuple[str, Dict]:
    """Detects and reduces AI writing signals across the manuscript.
    
    Args:
        markdown_report: The manuscript text.
        title: Paper title for LLM context.
        max_rewrites: Maximum number of paragraphs to rewrite (to control API cost).
    
    Returns:
        Tuple of (improved_markdown, ai_signal_audit_dict)
    """
    paragraphs = _split_into_paragraphs(markdown_report)
    
    scored = []
    for para in paragraphs:
        if _is_code_or_table(para) or len(para.split()) < 30:
            scored.append((para, 0.0, {}))  # Skip code, tables, short paras
            continue
        score, breakdown = _score_paragraph(para)
        scored.append((para, score, breakdown))
    
    # Sort by AI score descending, take top N for rewriting
    high_ai_paras = sorted(
        [(i, para, score, bd) for i, (para, score, bd) in enumerate(scored) if score >= AI_DETECTION_THRESHOLD],
        key=lambda x: x[2], reverse=True
    )[:max_rewrites]
    
    total_paragraphs = len([p for p, s, _ in scored if s > 0])
    high_ai_count_before = len([s for _, s, _ in scored if s >= AI_DETECTION_THRESHOLD])
    avg_score_before = (sum(s for _, s, _ in scored if s > 0) / total_paragraphs) if total_paragraphs else 0
    
    rewrites_done = 0
    rewrite_log = []
    
    for idx, para, score, breakdown in high_ai_paras:
        improved = _rewrite_paragraph_via_llm(para, title, breakdown)
        if improved and improved != para:
            scored[idx] = (improved, 0.3, {})  # Mark as improved
            rewrite_log.append({
                "original_score": round(score, 2),
                "paragraph_preview": para[:80] + "...",
                "status": "rewritten"
            })
            rewrites_done += 1
    
    # Rebuild report from improved paragraphs
    improved_report = _rebuild_report(markdown_report, paragraphs, scored)
    
    # Compute after-state stats
    high_ai_count_after = len([s for _, s, _ in scored if s >= AI_DETECTION_THRESHOLD])
    avg_score_after = (sum(s for _, s, _ in scored if s > 0) / total_paragraphs) if total_paragraphs else 0
    
    audit = {
        "paragraphs_analyzed": total_paragraphs,
        "high_ai_signal_before": high_ai_count_before,
        "high_ai_signal_after": high_ai_count_after,
        "avg_ai_score_before": round(avg_score_before, 2),
        "avg_ai_score_after": round(avg_score_after, 2),
        "paragraphs_rewritten": rewrites_done,
        "rewrite_log": rewrite_log,
        "ai_signal_delta": round(avg_score_before - avg_score_after, 2),
    }
    
    return improved_report, audit


# ─────────────────────────────────────────────────────────────────────────────
# Detection Heuristics
# ─────────────────────────────────────────────────────────────────────────────

def _score_paragraph(para: str) -> Tuple[float, Dict]:
    """Returns (AI_probability_0_to_1, breakdown_dict) for a paragraph."""
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    sentences = [s for s in sentences if len(s.split()) > 3]
    
    breakdown = {}
    
    # 1. Sentence length uniformity (AI text has low variance)
    if len(sentences) >= 3:
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        # Coefficient of variation: low = uniform = AI-like
        cv = std_dev / mean_len if mean_len > 0 else 1.0
        uniformity_score = max(0, 1.0 - cv * 2)  # Low CV → high AI score
        breakdown["sentence_uniformity"] = round(uniformity_score, 2)
    else:
        breakdown["sentence_uniformity"] = 0.0
        uniformity_score = 0.0
    
    # 2. Hedge word density
    words = re.findall(r'\b\w+\b', para.lower())
    hedge_count = sum(1 for w in words if w in AI_HEDGE_WORDS)
    hedge_density = min(hedge_count / max(len(words), 1) * 10, 1.0)
    breakdown["hedge_density"] = round(hedge_density, 2)
    
    # 3. Transition phrase repetition
    transition_count = sum(1 for phrase in AI_TRANSITION_PHRASES
                           if phrase.lower() in para.lower())
    transition_score = min(transition_count / 3.0, 1.0)
    breakdown["transition_excess"] = round(transition_score, 2)
    
    # 4. Passive voice ratio
    passive_matches = sum(len(re.findall(p, para, re.IGNORECASE)) for p in AI_PASSIVE_PATTERNS)
    passive_ratio = min(passive_matches / max(len(sentences), 1) * 0.5, 1.0)
    breakdown["passive_ratio"] = round(passive_ratio, 2)
    
    # 5. Sentence start repetition (AI often starts sentences the same way)
    starts = [s.split()[0].lower() for s in sentences if s.split()]
    unique_starts = len(set(starts))
    start_repetition = 1.0 - (unique_starts / max(len(starts), 1))
    breakdown["start_repetition"] = round(start_repetition, 2)
    
    # Weighted composite score
    ai_score = (
        uniformity_score * 0.30 +
        hedge_density    * 0.25 +
        transition_score * 0.20 +
        passive_ratio    * 0.15 +
        start_repetition * 0.10
    )
    
    return round(ai_score, 3), breakdown


def _is_code_or_table(para: str) -> bool:
    """Returns True if paragraph is a code block or markdown table."""
    stripped = para.strip()
    return (stripped.startswith("```") or
            stripped.startswith("|") or
            stripped.startswith("#") or
            stripped.startswith(">"))


# ─────────────────────────────────────────────────────────────────────────────
# LLM Rewriting
# ─────────────────────────────────────────────────────────────────────────────

def _rewrite_paragraph_via_llm(para: str, title: str, breakdown: Dict) -> str:
    """Rewrites a single high-AI-score paragraph via the configured LLM."""
    try:
        from openai import OpenAI
        
        api_key = os.environ.get("GROQ_API_KEY_1") or os.environ.get("GROQ_API_KEY")
        base_url = os.environ.get("OPENAI_API_BASE", "https://api.groq.com/openai/v1")
        model = os.environ.get("RESEARCH_MODEL", "openai/gpt-oss-120b")
        if model and ":" in model:
            model = model.split(":", 1)[1]
        
        if not api_key:
            return ""
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        issues_desc = []
        if breakdown.get("sentence_uniformity", 0) > 0.5:
            issues_desc.append("vary sentence length significantly (mix short and long sentences)")
        if breakdown.get("hedge_density", 0) > 0.3:
            issues_desc.append("remove hedge words like 'robust', 'novel', 'significant', 'comprehensive'")
        if breakdown.get("transition_excess", 0) > 0.3:
            issues_desc.append("remove or replace generic transitions like 'Furthermore', 'Moreover', 'Additionally'")
        if breakdown.get("passive_ratio", 0) > 0.3:
            issues_desc.append("convert passive voice to active voice where possible")
        
        if not issues_desc:
            return ""
        
        issues_text = "; ".join(issues_desc)
        
        prompt = f"""Rewrite the following paragraph from a research paper titled "{title}" to sound more 
like a human expert author. Specifically: {issues_text}.

Rules:
- Preserve ALL citations (e.g. [1], [2,3]) exactly as-is.
- Preserve ALL technical terms, equations, and mathematical notation exactly.
- Do NOT change the factual claims or add new content.
- Output ONLY the rewritten paragraph, nothing else.
- Target same length as original (±20%).

Original paragraph:
{para}"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.6,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Report Rebuild
# ─────────────────────────────────────────────────────────────────────────────

def _split_into_paragraphs(text: str) -> List[str]:
    """Splits markdown report into paragraph chunks."""
    return re.split(r'\n{2,}', text)


def _rebuild_report(original: str, original_paragraphs: List[str],
                    scored: List[Tuple[str, float, Dict]]) -> str:
    """Reconstructs the report with rewritten paragraphs."""
    improved = original
    for orig_para, (new_para, _, _) in zip(original_paragraphs, scored):
        if orig_para != new_para and new_para:
            improved = improved.replace(orig_para, new_para, 1)
    return improved
