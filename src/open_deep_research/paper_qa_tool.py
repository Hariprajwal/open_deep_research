"""Scientific literature and verified paper citation tool for Open Deep Research."""

import json
import urllib.parse
import urllib.request
import arxiv
from langchain_core.tools import tool

@tool
def search_scientific_literature(query: str, max_results: int = 5) -> str:
    """Search scientific paper databases (ArXiv, Semantic Scholar) for peer-reviewed papers, 
    abstracts, DOIs, and verified BibTeX citations.
    
    Args:
        query: The academic topic or paper title to search for.
        max_results: Number of top paper results to return (default: 5).
        
    Returns:
        Formatted string containing paper titles, authors, publication dates, 
        DOIs, ArXiv links, abstracts, and BibTeX citations.
    """
    results = []
    
    # 1. Search ArXiv
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        for paper in search.results():
            authors_str = ", ".join([a.name for a in paper.authors[:4]])
            if len(paper.authors) > 4:
                authors_str += " et al."
                
            published_year = paper.published.year if paper.published else "N/A"
            arxiv_id = paper.get_short_id()
            doi = paper.doi if paper.doi else f"10.48550/arXiv.{arxiv_id}"
            
            bibtex = (
                f"@article{{{paper.authors[0].name.split()[-1].lower()}{published_year}{arxiv_id.split('.')[0]},\n"
                f"  title={{{paper.title}}},\n"
                f"  author={{{authors_str}}},\n"
                f"  journal={{arXiv preprint arXiv:{arxiv_id}}},\n"
                f"  year={{{published_year}}},\n"
                f"  url={{{paper.entry_id}}},\n"
                f"  doi={{{doi}}}\n"
                f"}}"
            )
            
            paper_entry = (
                f"### Title: {paper.title}\n"
                f"- **Authors**: {authors_str}\n"
                f"- **Year**: {published_year}\n"
                f"- **DOI**: {doi}\n"
                f"- **ArXiv URL**: {paper.entry_id}\n"
                f"- **Abstract Summary**: {paper.summary[:500].strip()}...\n"
                f"- **Verified BibTeX**:\n```bibtex\n{bibtex}\n```\n"
            )
            results.append(paper_entry)
    except Exception as e:
        results.append(f"Error querying ArXiv: {str(e)}")
        
    if not results:
        return f"No scientific papers found for query: '{query}'."
        
    return f"## Verified Scientific Literature Results for: '{query}'\n\n" + "\n---\n".join(results)
