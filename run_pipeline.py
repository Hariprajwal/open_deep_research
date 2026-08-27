"""Unified CLI Pipeline Runner for Q1 Deep Research & IEEE Paper Engine."""

import argparse
import asyncio
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

# Fix Windows cp1252 encoding issues with Unicode/emoji output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables from .env
load_dotenv()

from open_deep_research.deep_researcher import deep_researcher
from open_deep_research.pdf_parser import parse_document_to_markdown
from open_deep_research.ieee_exporter import export_to_ieee

async def run_pipeline(topic: str, pdf_path: str = None, output_dir: str = "output", author: str = "Research Agent System"):
    print(f"==================================================")
    print(f"[START] Q1 Deep Research Pipeline")
    print(f"[TOPIC] {topic}")
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
        print(f"\n[INFO] Ingesting reference papers from: {target_path}...")
        parsed_doc = parse_document_to_markdown(target_path)
        if parsed_doc.strip():
            initial_messages.append({
                "role": "user",
                "content": f"Reference Knowledge Base & Local Papers:\n{parsed_doc[:6000]}\n\nUser Research Task:\n{topic}"
            })
            print(f"[OK] Ingested reference papers knowledge base.")
        else:
            initial_messages.append({"role": "user", "content": topic})
    else:
        initial_messages.append({"role": "user", "content": topic})

    # 2. Execute Deep Researcher Graph (with clarification disabled for automated CLI use)
    print(f"\n[RUNNING] Deep Researcher multi-agent graph...")
    print(f"[INFO] This may take 3-8 minutes depending on model speed...")
    inputs = {"messages": initial_messages}

    # Pass allow_clarification=False so the graph runs fully automated
    # without pausing to wait for human input via LangGraph interrupt()
    # streaming=False is set in get_model_config to avoid SSE parse issues with local proxy
    config = RunnableConfig(configurable={"allow_clarification": False})

    try:
        result = await deep_researcher.ainvoke(inputs, config=config)
        final_report = result.get("final_report", "")

        if not final_report:
            print("\n[ERROR] No report generated. Check API keys / model in .env")
            return

        print(f"\n[OK] Research completed successfully!")

        # 3. Export to IEEE Paper Format
        print(f"\n[EXPORT] Generating IEEE Paper Format...")
        export_result = export_to_ieee(
            markdown_report=final_report,
            output_dir=output_dir,
            title=topic,
            author=author
        )

        print(f"\n[DONE] Pipeline Complete! Files:")
        print(f"  - IEEE Markdown : {export_result['markdown_file']}")
        print(f"  - Typst Source  : {export_result['typst_file']}")
        if export_result['pdf_compiled']:
            print(f"  - IEEE PDF      : {export_result['pdf_file']}")
        else:
            print(f"  - PDF Note      : Install 'typst' to auto-compile PDF from '{export_result['typst_file']}'")

    except KeyboardInterrupt:
        print("\n[STOPPED] Pipeline interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Research execution failed: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Q1 Deep Research & IEEE Paper Engine")
    parser.add_argument("--topic", type=str, required=True, help="Research topic or prompt")
    parser.add_argument("--pdf", type=str, default=None, help="Optional path to reference PDF or directory of papers")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--author", type=str, default="Research Agent System", help="Author name")

    args = parser.parse_args()
    asyncio.run(run_pipeline(args.topic, args.pdf, args.output, args.author))
