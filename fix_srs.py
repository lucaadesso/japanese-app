import re

with open("app/srs.py", "r", encoding="utf-8") as f:
    content = f.read()

replacement = """import json
import os

ZEN_VOCAB_PATH = os.path.join(os.path.dirname(__file__), "data", "zen_vocab.json")
try:
    with open(ZEN_VOCAB_PATH, "r", encoding="utf-8") as f:
        ZEN_VOCAB = json.load(f)
    for w in ZEN_VOCAB:
        w["k"] = set(w["k"])
except FileNotFoundError:
    ZEN_VOCAB = []
"""

pattern = re.compile(r"ZEN_VOCAB:\s*list\[dict\]\s*=\s*\[.*?^\]", re.MULTILINE | re.DOTALL)
new_content = pattern.sub(replacement, content)

with open("app/srs.py", "w", encoding="utf-8") as f:
    f.write(new_content)
print("Done regex")
