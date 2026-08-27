"""Unified CLI Pipeline Runner for Q1 Deep Research & IEEE Paper Engine."""

import argparse
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from open_deep_research.deep_researcher import deep_researcher
from open_deep_research.pdf_parser import parse_document_to_markdown
from open_deep_research.ieee_exporter import export_to_ieee

async def run_pipeline(topic: str, pdf_path: str = None, output_dir: str = "output", author: str = "Research Agent System"):
    print(f"==================================================")
    print(f"🚀 Starting Q1 Deep Research Pipeline")
    print(f"📌 Research Topic: {topic}")
    print(f"==================================================")
    
    initial_messages = []
    
    # Check for specific pdf path OR default reference_papers directory
    target_path = pdf_path
    if not target_path:
        default_dir = Path("reference_papers")
        if default_dir.exists() and default_dir.is_dir() and any(default_dir.iterdir()):
            target_path = "reference_papers"

    # 1. Handle Reference Documents / Papers Ingestion
    if target_path and Path(target_path).exists():
        print(f"\n📂 Ingesting reference papers from: {target_path}...")
        parsed_doc = parse_document_to_markdown(target_path)
        if parsed_doc.strip():
            initial_messages.append({
                "role": "user", 
                "content": f"Reference Knowledge Base & Local Papers:\n{parsed_doc[:6000]}\n\nUser Research Task:\n{topic}"
            })
            print(f"✅ Ingested reference papers knowledge base.")
        else:
            initial_messages.append({"role": "user", "content": topic})
    else:
        initial_messages.append({"role": "user", "content": topic})
        
    # 2. Execute Deep Researcher Graph
    print(f"\n🔬 Running Deep Researcher multi-agent graph...")
    inputs = {"messages": initial_messages}
    
    try:
        result = await deep_researcher.ainvoke(inputs)
        final_report = result.get("final_report", "")
        
        if not final_report:
            print("❌ No report generated. Please check your API keys in .env")
            return
            
        print(f"\n✅ Research completed successfully!")
        
        # 3. Export to IEEE Paper Format
        print(f"\n📄 Exporting to IEEE Paper Format...")
        export_result = export_to_ieee(
            markdown_report=final_report,
            output_dir=output_dir,
            title=topic,
            author=author
        )
        
        print(f"🎉 Pipeline Complete! Exported files:")
        print(f"  - IEEE Markdown: {export_result['markdown_file']}")
        print(f"  - Typst IEEE Source: {export_result['typst_file']}")
        if export_result['pdf_compiled']:
            print(f"  - IEEE PDF Output: {export_result['pdf_file']}")
        else:
            print(f"  - Note: PDF compiler ('typst') not found in PATH. You can compile '{export_result['typst_file']}' or view the IEEE Markdown file.")
            
    except Exception as e:
        print(f"❌ Error during research execution: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Q1 Deep Research & IEEE Paper Engine")
    parser.add_argument("--topic", type=str, required=True, help="Research topic or prompt")
    parser.add_argument("--pdf", type=str, default=None, help="Optional path to reference PDF or directory of papers")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--author", type=str, default="Research Agent System", help="Author name")
    
    args = parser.parse_args()
    asyncio.run(run_pipeline(args.topic, args.pdf, args.output, args.author))
