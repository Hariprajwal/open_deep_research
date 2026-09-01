import os

pattern = 'model = os.environ.get("RESEARCH_MODEL", "openai/gpt-oss-120b")'
replacement = 'model = os.environ.get("RESEARCH_MODEL", "openai/gpt-oss-120b")\n        if model and ":" in model:\n            model = model.split(":", 1)[1]'

files = [
    r'd:\downloads\Research-paper\src\open_deep_research\abstract_analyzer.py',
    r'd:\downloads\Research-paper\src\open_deep_research\ai_signal_reducer.py',
    r'd:\downloads\Research-paper\src\open_deep_research\algorithmic_formalizer.py',
    r'd:\downloads\Research-paper\src\open_deep_research\submission_verifier.py'
]

for file in files:
    with open(file, "r") as f:
        content = f.read()
    content = content.replace(pattern, replacement)
    with open(file, "w") as f:
        f.write(content)
print("Done replacing.")
