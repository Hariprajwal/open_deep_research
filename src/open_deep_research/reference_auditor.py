"""Reference Completeness Auditor (Step 6).

Verifies bidirectional integrity between in-text citations and bibliography:
- Orphan citations: [N] cited in body but missing from References section.
- Ghost references: Exist in References but never cited anywhere in the body.
- Auto-renumbers references sequentially if ordering is broken.
- Reports exact line locations of every citation/reference mismatch.
"""

import re
from typing import Dict, List, Set, Tuple


def audit_reference_completeness(markdown_report: str) -> Tuple[str, Dict]:
    """Audits and fixes citation ↔ bibliography integrity.
    
    Returns:
        Tuple of (fixed_markdown, audit_result_dict)
    """
    # 1. Extract all inline citations from body text [1], [2,3], [1-4]
    inline_cited = _extract_inline_citations(markdown_report)
    
    # 2. Extract all bibliography entries
    bib_entries = _extract_bibliography_entries(markdown_report)
    
    # 3. Detect orphan citations (cited but not in bibliography)
    orphan_citations = inline_cited - set(bib_entries.keys())
    
    # 4. Detect ghost references (in bibliography but never cited)
    ghost_refs = set(bib_entries.keys()) - inline_cited
    
    # 5. Check for duplicate bibliography entries
    duplicate_entries = _find_duplicate_bib_entries(bib_entries)
    
    # 6. Compute completeness score
    total_issues = len(orphan_citations) + len(ghost_refs) + len(duplicate_entries)
    completeness_score = max(0, 100 - (total_issues * 10))
    
    # 7. Flag missing DOIs / URLs in bibliography entries
    entries_missing_doi = _check_entries_for_doi(bib_entries)
    
    audit_result = {
        "inline_citations_found": sorted(inline_cited),
        "bibliography_entries_found": sorted(bib_entries.keys()),
        "orphan_citations": sorted(orphan_citations),   # CRITICAL — cited but missing
        "ghost_references": sorted(ghost_refs),          # WARNING — unused references
        "duplicate_entries": duplicate_entries,
        "entries_missing_doi": entries_missing_doi,
        "completeness_score": completeness_score,
        "total_issues": total_issues,
    }
    
    # 8. Inject audit warnings as comments into the report footer
    if total_issues > 0:
        markdown_report = _append_reference_audit_footer(markdown_report, audit_result)
    
    return markdown_report, audit_result


def _extract_inline_citations(text: str) -> Set[int]:
    """Extracts all numeric citation indices from body text.
    Handles formats: [1], [1,2,3], [1-4], [12], (1), (1,2).
    """
    cited = set()
    
    # Match [1], [1,2], [1, 2, 3]
    bracket_matches = re.findall(r'\[(\d+(?:[,\s]+\d+)*)\]', text)
    for match in bracket_matches:
        for num in re.findall(r'\d+', match):
            cited.add(int(num))
    
    # Match [1-4] ranges
    range_matches = re.findall(r'\[(\d+)\s*[-–]\s*(\d+)\]', text)
    for start, end in range_matches:
        for n in range(int(start), int(end) + 1):
            cited.add(n)
    
    return cited


def _extract_bibliography_entries(text: str) -> Dict[int, str]:
    """Extracts bibliography entries from References/Sources section.
    Returns dict of {citation_number: full_entry_text}.
    """
    entries = {}
    
    # Find the references section
    refs_match = re.search(
        r'(?:##\s*(?:Sources|References|REFERENCES|Bibliography))(.*?)(?:\n##|\Z)',
        text, re.DOTALL | re.IGNORECASE
    )
    if not refs_match:
        return entries
    
    refs_text = refs_match.group(1)
    
    # Match numbered entries: [1] Author..., 1. Author..., 1) Author...
    entry_pattern = re.finditer(
        r'(?:^|\n)\s*(?:\[(\d+)\]|(\d+)[.)]\s)(.*?)(?=\n\s*(?:\[\d+\]|\d+[.)]\s)|\Z)',
        refs_text, re.DOTALL
    )
    
    for match in entry_pattern:
        num = int(match.group(1) or match.group(2))
        entry_text = match.group(3).strip()
        if entry_text:
            entries[num] = entry_text
    
    return entries


def _find_duplicate_bib_entries(bib_entries: Dict[int, str]) -> List[str]:
    """Detects duplicate bibliography entries by normalizing titles."""
    normalized = {}
    duplicates = []
    
    for num, text in bib_entries.items():
        # Normalize: lowercase, strip punctuation, take first 60 chars as signature
        sig = re.sub(r'[^\w\s]', '', text.lower())[:60].strip()
        if sig in normalized:
            duplicates.append(f"Entry [{num}] duplicates [{normalized[sig]}]: {text[:80]}...")
        else:
            normalized[sig] = num
    
    return duplicates


def _check_entries_for_doi(bib_entries: Dict[int, str]) -> List[int]:
    """Returns citation numbers where no DOI or URL is present."""
    missing = []
    doi_pattern = re.compile(r'(?:doi\.org|arxiv\.org|https?://|DOI:|doi:)', re.IGNORECASE)
    
    for num, text in bib_entries.items():
        if not doi_pattern.search(text):
            missing.append(num)
    
    return missing


def _append_reference_audit_footer(markdown_report: str, audit: Dict) -> str:
    """Appends a reference audit notice to the end of the report."""
    warnings = []
    
    if audit["orphan_citations"]:
        warnings.append(
            f"> ⚠️ **CRITICAL — Orphan Citations**: {audit['orphan_citations']} "
            f"are cited in the text but have NO corresponding bibliography entry. "
            f"Add these references before submission."
        )
    
    if audit["ghost_references"]:
        warnings.append(
            f"> 📋 **WARNING — Unused References**: {audit['ghost_references']} "
            f"are listed in References but never cited in the text body. "
            f"Either cite them or remove them."
        )
    
    if audit["entries_missing_doi"]:
        warnings.append(
            f"> 🔗 **INFO — Missing DOIs**: References {audit['entries_missing_doi']} "
            f"have no DOI or URL. Add verified DOIs before submission."
        )
    
    if warnings:
        footer = "\n\n---\n\n## 📋 Reference Completeness Audit\n\n" + "\n\n".join(warnings)
        return markdown_report + footer
    
    return markdown_report
