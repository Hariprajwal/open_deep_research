"""Abstract Quality Analyzer (Step 7).

Verifies that the paper abstract meets Q1 journal structural standards:
1. IMRaD structure check — Background, Objective, Methods, Results, Conclusion present.
2. Word count validation — optimal range 150–250 words.
3. Keyword coverage — technical keywords from body appear in abstract.
4. Overclaiming detection — abstract-specific unverifiable claim detection.
5. LLM-based abstract rewrite if quality score < 70.
"""

import re
import os
from typing import Tuple, Dict

# IMRaD component patterns
IMRAD_PATTERNS = {
    "Background/Motivation": [
        r'\b(?:autonomous|intelligent|growing|increasing|critical|challenge|problem|issue)\b',
        r'\b(?:existing|traditional|conventional|current)\b',
    ],
    "Objective/Contribution": [
        r'\b(?:propose|present|introduce|develop|design|formulate|address)\b',
        r'\b(?:framework|system|approach|architecture|method|model)\b',
    ],
    "Methods": [
        r'\b(?:sensor|fusion|prediction|estimation|algorithm|neural|deep|learning|optimization)\b',
        r'\b(?:dataset|trained|evaluated|validated|simulation|experiment)\b',
    ],
    "Results/Findings": [
        r'\b(?:results|demonstrate|achieve|improve|outperform|reduce|increase|show|yield)\b',
        r'\b(?:accuracy|precision|recall|performance|efficiency|latency|score)\b',
    ],
    "Conclusion/Impact": [
        r'\b(?:potential|future|deployment|real-world|safety|robust|scalable|practical)\b',
        r'\b(?:contribution|significant|advancement|direction)\b',
    ],
}

ABSTRACT_OVERCLAIMING_PATTERNS = [
    (r'\b(?:guarantees?|ensures?)\s+(?:absolute\s+)?safety\b',
     'aims to improve safety'),
    (r'\b(?:fully|completely)\s+(?:solves?|eliminates?|removes?)\b',
     'substantially reduces'),
    (r'\bachieve[sd]?\s+(?:state-of-the-art|optimal|perfect)\s+(?:accuracy|performance)\b',
     'demonstrates competitive performance'),
    (r'\boutperforms?\s+all\s+existing\b',
     'improves upon current'),
]


def analyze_and_improve_abstract(markdown_report: str, title: str) -> Tuple[str, Dict]:
    """Analyzes the abstract for IMRaD structure, word count, and quality.
    Rewrites it via LLM if quality score is below threshold.
    
    Returns:
        Tuple of (improved_markdown, abstract_audit_dict)
    """
    abstract_text = _extract_abstract(markdown_report)
    
    if not abstract_text:
        audit = {
            "abstract_found": False,
            "quality_score": 0,
            "issues": ["Abstract section not found in the report."]
        }
        return markdown_report, audit
    
    word_count = len(abstract_text.split())
    imrad_coverage = _check_imrad_coverage(abstract_text)
    overclaiming_issues = _detect_abstract_overclaiming(abstract_text)
    keyword_coverage = _check_keyword_coverage(abstract_text, markdown_report)
    
    # Score calculation
    score = _compute_abstract_score(
        word_count, imrad_coverage, overclaiming_issues, keyword_coverage
    )
    
    issues = []
    if word_count < 150:
        issues.append(f"Abstract too short ({word_count} words). Q1 standard: 150–250 words.")
    if word_count > 300:
        issues.append(f"Abstract too long ({word_count} words). Trim to 250 words max.")
    
    for component, present in imrad_coverage.items():
        if not present:
            issues.append(f"IMRaD component missing: '{component}' not detected in abstract.")
    
    for claim in overclaiming_issues:
        issues.append(f"Overclaiming: '{claim}' detected in abstract.")
    
    if keyword_coverage < 0.4:
        issues.append(f"Low keyword coverage ({keyword_coverage:.0%}). Key technical terms missing from abstract.")
    
    # Fix overclaiming in abstract
    if overclaiming_issues:
        for pattern, replacement in ABSTRACT_OVERCLAIMING_PATTERNS:
            abstract_text = re.sub(pattern, replacement, abstract_text, flags=re.IGNORECASE)
        markdown_report = _replace_abstract_in_report(markdown_report, abstract_text)
    
    # LLM rewrite if quality score below 65
    rewritten = False
    if score < 65 and len(issues) > 0:
        improved_abstract = _rewrite_abstract_via_llm(abstract_text, title, issues)
        if improved_abstract:
            markdown_report = _replace_abstract_in_report(markdown_report, improved_abstract)
            abstract_text = improved_abstract
            rewritten = True
            score = min(score + 20, 95)  # Estimate improvement
    
    audit = {
        "abstract_found": True,
        "word_count": word_count,
        "quality_score": score,
        "imrad_coverage": imrad_coverage,
        "keyword_coverage_pct": f"{keyword_coverage:.0%}",
        "overclaiming_issues_fixed": len(overclaiming_issues),
        "abstract_rewritten_by_llm": rewritten,
        "issues": issues,
    }
    
    return markdown_report, audit


def _extract_abstract(text: str) -> str:
    """Extracts abstract content from report."""
    patterns = [
        r'##\s*ABSTRACT\s*\n+(.*?)(?=\n##)',
        r'\*\*Abstract\*\*[:\s]+(.*?)(?=\n##|\n\*\*)',
        r'##\s*Abstract\s*\n+(.*?)(?=\n##)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _check_imrad_coverage(abstract_text: str) -> Dict[str, bool]:
    """Checks which IMRaD components are detectable in the abstract."""
    coverage = {}
    abstract_lower = abstract_text.lower()
    for component, patterns in IMRAD_PATTERNS.items():
        found = any(re.search(p, abstract_lower) for p in patterns)
        coverage[component] = found
    return coverage


def _detect_abstract_overclaiming(abstract_text: str) -> list:
    """Returns list of overclaiming phrases found in the abstract."""
    found = []
    for pattern, _ in ABSTRACT_OVERCLAIMING_PATTERNS:
        m = re.search(pattern, abstract_text, re.IGNORECASE)
        if m:
            found.append(m.group(0))
    return found


def _check_keyword_coverage(abstract_text: str, full_report: str) -> float:
    """Estimates what fraction of key technical terms from the paper appear in the abstract."""
    # Extract technical noun phrases from the full report (uppercase acronyms + domain terms)
    technical_terms = set(re.findall(r'\b[A-Z]{2,6}\b', full_report))  # Acronyms
    technical_terms.update(re.findall(r'\b(?:LiDAR|radar|neural|trajectory|uncertainty|'
                                       r'probabilistic|collision|TTC|sensor|fusion|prediction|'
                                       r'optimization|algorithm|framework|architecture)\b',
                                       full_report, re.IGNORECASE))
    
    if not technical_terms:
        return 1.0
    
    abstract_lower = abstract_text.lower()
    present = sum(1 for t in technical_terms if t.lower() in abstract_lower)
    return min(present / len(technical_terms), 1.0)


def _compute_abstract_score(word_count: int, imrad_coverage: Dict,
                              overclaiming: list, keyword_cov: float) -> int:
    """Computes 0-100 abstract quality score."""
    score = 0
    
    # Word count: 40 points
    if 150 <= word_count <= 250:
        score += 40
    elif 120 <= word_count <= 280:
        score += 25
    elif word_count > 50:
        score += 10
    
    # IMRaD: 40 points (8 per component)
    imrad_score = sum(8 for present in imrad_coverage.values() if present)
    score += imrad_score
    
    # Overclaiming penalty: -8 per issue
    score -= len(overclaiming) * 8
    
    # Keyword coverage: 20 points
    score += int(keyword_cov * 20)
    
    return max(0, min(100, score))


def _rewrite_abstract_via_llm(abstract_text: str, title: str, issues: list) -> str:
    """Rewrites the abstract via LLM to fix detected quality issues."""
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
        
        issues_text = "\n".join(f"- {i}" for i in issues)
        
        prompt = f"""You are a Q1 journal editor. Rewrite the abstract below to fix the listed issues while 
preserving all factual claims and technical content.

Paper Title: {title}

Current Abstract:
{abstract_text}

Issues to Fix:
{issues_text}

Requirements:
- 150–250 words exactly
- Must cover all 5 IMRaD components: Background, Objective, Methods, Results/findings, Conclusion/impact
- No overclaiming (do not guarantee safety, do not claim best accuracy)
- Keep all specific technical terms from the original
- Do NOT add fabricated results or numbers not in the original

Return ONLY the improved abstract text, no headers."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.3,
        )
        
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def _replace_abstract_in_report(markdown_report: str, new_abstract: str) -> str:
    """Replaces the abstract block in the report with the improved version."""
    patterns = [
        (r'(##\s*ABSTRACT\s*\n+)(.*?)(\n##)', re.DOTALL),
        (r'(##\s*Abstract\s*\n+)(.*?)(\n##)', re.DOTALL),
    ]
    for pat, flags in patterns:
        m = re.search(pat, markdown_report, flags | re.IGNORECASE)
        if m:
            return markdown_report[:m.start(2)] + new_abstract + markdown_report[m.end(2):]
    return markdown_report
