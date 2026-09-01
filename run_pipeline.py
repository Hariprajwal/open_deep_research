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
    import datetime
    import re
    
    # Create unique output directory based on topic and timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = re.sub(r'[^a-zA-Z0-9]+', '_', topic.lower()).strip('_')[:30]
    unique_out_dir = Path(output_dir) / f"{safe_topic}_{timestamp}"
    unique_out_dir.mkdir(parents=True, exist_ok=True)
    output_dir = str(unique_out_dir)

    print(f"==================================================")
    print(f"[START] Q1 Deep Research Pipeline")
    print(f"[TOPIC] {topic}")
    print(f"[OUTPUT DIR] {output_dir}")
    print(f"==================================================")

    initial_messages = []

    # Check for specific pdf path OR default reference_papers directory
    target_path = pdf_path
    if not target_path:
        default_dir = Path("reference_papers")
        if default_dir.exists() and default_dir.is_dir() and any(default_dir.iterdir()):
            target_path = "reference_papers"

    # 0. Handle ad-hoc reference.txt
    additional_context = ""
    ref_file = Path("reference.txt")
    if ref_file.exists() and ref_file.is_file():
        with open(ref_file, "r", encoding="utf-8") as f:
            ref_content = f.read().strip()
        if ref_content:
            additional_context = f"Additional User Provided References:\n{ref_content}\n\n"
        
        # Backup the reference file to the unique output folder
        backup_name = unique_out_dir / "reference_backup.txt"
        ref_file.rename(backup_name)
        # Create an empty reference.txt
        Path("reference.txt").touch()
        print(f"\n[INFO] Processed reference.txt and backed it up to {backup_name}")

    # 1. Handle Reference Documents / Papers Ingestion
    if target_path and Path(target_path).exists():
        print(f"\n[INFO] Ingesting reference papers from: {target_path}...")
        parsed_doc = parse_document_to_markdown(target_path)
        if parsed_doc.strip() or additional_context:
            combined_context = additional_context
            if parsed_doc.strip():
                combined_context += f"Reference Knowledge Base & Local Papers:\n{parsed_doc[:6000]}\n\n"
            
            initial_messages.append({
                "role": "user",
                "content": f"{combined_context}User Research Task:\n{topic}"
            })
            print(f"[OK] Ingested reference knowledge base.")
        else:
            initial_messages.append({"role": "user", "content": topic})
    else:
        if additional_context:
            initial_messages.append({
                "role": "user",
                "content": f"{additional_context}User Research Task:\n{topic}"
            })
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
            print(f"  - Standard PDF  : {export_result['pdf_file']}")
        if export_result.get('conference_pdf_compiled'):
            print(f"  - IEEE Conf PDF : {export_result['conference_pdf_file']}")
        if not export_result['pdf_compiled'] and not export_result.get('conference_pdf_compiled'):
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
