"""Document and PDF parser for offline academic literature ingestion."""

import os
from pathlib import Path
import fitz  # PyMuPDF

def parse_document_to_markdown(path_str: str) -> str:
    """Parse a single PDF/text document OR an entire directory of reference papers into structured Markdown.
    
    Args:
        path_str: Path to a file (.pdf, .txt, .md) OR a directory containing reference files.
        
    Returns:
        Structured Markdown string containing document text organized by pages/sections.
    """
    path = Path(path_str)
    if not path.exists():
        return ""
        
    if path.is_dir():
        return parse_directory_to_markdown(path_str)
        
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(path_str)
    elif suffix in [".txt", ".md"]:
        with open(path_str, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        return ""

def parse_directory_to_markdown(dir_path: str) -> str:
    """Parse all supported documents (.pdf, .txt, .md) in a directory."""
    path = Path(dir_path)
    if not path.exists() or not path.is_dir():
        return ""
        
    parsed_documents = []
    files = sorted(list(path.glob("*.*")))
    
    for file_path in files:
        if file_path.suffix.lower() in [".pdf", ".txt", ".md"]:
            try:
                doc_md = parse_document_to_markdown(str(file_path))
                if doc_md.strip():
                    parsed_documents.append(f"### Reference File: {file_path.name}\n\n{doc_md.strip()}")
            except Exception as e:
                print(f"Warning: Could not parse {file_path.name}: {e}")
                
    if not parsed_documents:
        return ""
        
    return "## Local Reference Papers Knowledge Base\n\n" + "\n\n---\n\n".join(parsed_documents)

def _parse_pdf(pdf_path: str) -> str:
    """Extract text and layout from PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    markdown_chunks = [f"# Document: {Path(pdf_path).name}\n"]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        
        if text.strip():
            markdown_chunks.append(f"## Page {page_num + 1}\n\n{text.strip()}\n")
            
    doc.close()
    return "\n---\n".join(markdown_chunks)
