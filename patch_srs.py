with open("app/srs.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace HIRAGANA_GROUP_ORDER
content = content.replace(
    'HIRAGANA_GROUP_ORDER = [\n    "vowels", "ka", "sa", "ta", "na", "ha", "ma", "ya", "ra", "wa", "n"\n]',
    'HIRAGANA_GROUP_ORDER = [\n    "vowels", "ka", "sa", "ta", "na", "ha", "ma", "ya", "ra", "wa", "n",\n    "dakuten", "handakuten", "yoon", "sokuon"\n]'
)

# Append Advanced Hiragana rules before Katakana seed data
advanced_rules = """    ("ん", "n",  "n",   "n",  "Come una onda (wave) che finisce in 'n'"),
    
    # ─── Hiragana 1.5: Dakuten (゛) ─────────────────────────────────────────────
    ("が", "ga", "ga",  "dakuten", "K + trattini (゛) = G"),
    ("ぎ", "gi", "gi",  "dakuten", "K + trattini (゛) = G"),
    ("ぐ", "gu", "gu",  "dakuten", "K + trattini (゛) = G"),
    ("げ", "ge", "ge",  "dakuten", "K + trattini (゛) = G"),
    ("ご", "go", "go",  "dakuten", "K + trattini (゛) = G"),
    ("ざ", "za", "za",  "dakuten", "S + trattini (゛) = Z"),
    ("じ", "ji", "ji",  "dakuten", "Shi + trattini = Ji"),
    ("ず", "zu", "zu",  "dakuten", "Su + trattini = Zu"),
    ("ぜ", "ze", "ze",  "dakuten", "S + trattini (゛) = Z"),
    ("ぞ", "zo", "zo",  "dakuten", "S + trattini (゛) = Z"),
    ("だ", "da", "da",  "dakuten", "T + trattini (゛) = D"),
    ("ぢ", "ji", "ji",  "dakuten", "Chi + trattini = Ji (raro)"),
    ("づ", "zu", "zu",  "dakuten", "Tsu + trattini = Zu (raro)"),
    ("で", "de", "de",  "dakuten", "Te + trattini = De"),
    ("ど", "do", "do",  "dakuten", "To + trattini = Do"),
    ("ば", "ba", "ba",  "dakuten", "H + trattini (゛) = B"),
    ("び", "bi", "bi",  "dakuten", "H + trattini (゛) = B"),
    ("ぶ", "bu", "bu",  "dakuten", "H + trattini (゛) = B"),
    ("べ", "be", "be",  "dakuten", "H + trattini (゛) = B"),
    ("ぼ", "bo", "bo",  "dakuten", "H + trattini (゛) = B"),
    
    # ─── Hiragana 1.5: Handakuten (゜) ─────────────────────────────────────────
    ("ぱ", "pa", "pa",  "handakuten", "H + pallino (゜) = P"),
    ("ぴ", "pi", "pi",  "handakuten", "H + pallino (゜) = P"),
    ("ぷ", "pu", "pu",  "handakuten", "H + pallino (゜) = P"),
    ("ぺ", "pe", "pe",  "handakuten", "H + pallino (゜) = P"),
    ("ぽ", "po", "po",  "handakuten", "H + pallino (゜) = P"),
    
    # ─── Hiragana 1.5: Yoon (Combinazioni con ya/yu/yo) ─────────────────────
    ("きゃ", "kya", "kya", "yoon", "Ki + ya piccolo"),
    ("きゅ", "kyu", "kyu", "yoon", "Ki + yu piccolo"),
    ("きょ", "kyo", "kyo", "yoon", "Ki + yo piccolo"),
    ("しゃ", "sha", "sha", "yoon", "Shi + ya piccolo"),
    ("しゅ", "shu", "shu", "yoon", "Shi + yu piccolo"),
    ("しょ", "sho", "sho", "yoon", "Shi + yo piccolo"),
    ("ちゃ", "cha", "cha", "yoon", "Chi + ya piccolo"),
    ("ちゅ", "chu", "chu", "yoon", "Chi + yu piccolo"),
    ("ちょ", "cho", "cho", "yoon", "Chi + yo piccolo"),
    ("にゃ", "nya", "nya", "yoon", "Ni + ya piccolo"),
    ("にゅ", "nyu", "nyu", "yoon", "Ni + yu piccolo"),
    ("にょ", "nyo", "nyo", "yoon", "Ni + yo piccolo"),
    ("ひゃ", "hya", "hya", "yoon", "Hi + ya piccolo"),
    ("ひゅ", "hyu", "hyu", "yoon", "Hi + yu piccolo"),
    ("ひょ", "hyo", "hyo", "yoon", "Hi + yo piccolo"),
    ("みゃ", "mya", "mya", "yoon", "Mi + ya piccolo"),
    ("みゅ", "myu", "myu", "yoon", "Mi + yu piccolo"),
    ("みょ", "myo", "myo", "yoon", "Mi + yo piccolo"),
    ("りゃ", "rya", "rya", "yoon", "Ri + ya piccolo"),
    ("りゅ", "ryu", "ryu", "yoon", "Ri + yu piccolo"),
    ("りょ", "ryo", "ryo", "yoon", "Ri + yo piccolo"),
    
    ("ぎゃ", "gya", "gya", "yoon", "Gi + ya piccolo"),
    ("ぎゅ", "gyu", "gyu", "yoon", "Gi + yu piccolo"),
    ("ぎょ", "gyo", "gyo", "yoon", "Gi + yo piccolo"),
    ("じゃ", "ja", "ja",  "yoon", "Ji + ya piccolo"),
    ("じゅ", "ju", "ju",  "yoon", "Ji + yu piccolo"),
    ("じょ", "jo", "jo",  "yoon", "Ji + yo piccolo"),
    ("びゃ", "bya", "bya", "yoon", "Bi + ya piccolo"),
    ("びゅ", "byu", "byu", "yoon", "Bi + yu piccolo"),
    ("びょ", "byo", "byo", "yoon", "Bi + yo piccolo"),
    ("ぴゃ", "pya", "pya", "yoon", "Pi + ya piccolo"),
    ("ぴゅ", "pyu", "pyu", "yoon", "Pi + yu piccolo"),
    ("ぴょ", "pyo", "pyo", "yoon", "Pi + yo piccolo"),

    # ─── Hiragana 1.5: Sokuon (Piccolo Tsu) ─────────────────────────────────
    ("っ", "(doppia)", "sokuon", "sokuon", "Piccolo Tsu: Raddoppia la consonante successiva"),"""

content = content.replace('    ("ん", "n",  "n",   "n",  "Come una onda (wave) che finisce in \'n\'"),', advanced_rules)

# Replace ZEN_VOCAB correctly by finding start and end
start_idx = content.find("ZEN_VOCAB: list[dict] = [")
end_idx = content.find("]\n\n\ndef get_user_learned_kana", start_idx) + 1
if start_idx != -1 and end_idx > start_idx:
    json_load = """import json
import os

ZEN_VOCAB_PATH = os.path.join(os.path.dirname(__file__), "data", "zen_vocab.json")
try:
    with open(ZEN_VOCAB_PATH, "r", encoding="utf-8") as f:
        ZEN_VOCAB = json.load(f)
    for w in ZEN_VOCAB:
        w["k"] = set(w["k"])
except FileNotFoundError:
    ZEN_VOCAB = []"""
    content = content[:start_idx] + json_load + content[end_idx:]
else:
    print("Could not find ZEN_VOCAB bounds!")
    print("start_idx:", start_idx)
    print("end_idx:", end_idx)

with open("app/srs.py", "w", encoding="utf-8") as f:
    f.write(content)
