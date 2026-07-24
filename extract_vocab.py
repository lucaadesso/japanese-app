import json
import sys
from app.srs import ZEN_VOCAB

# Convert sets to lists
for w in ZEN_VOCAB:
    if "k" in w:
        w["k"] = list(w["k"])

with open('/home/ubuntu/japanese-app/app/data/zen_vocab.json', 'w', encoding='utf-8') as f:
    json.dump(ZEN_VOCAB, f, ensure_ascii=False, indent=4)
print("Extracted!")
