import json
import os

NEW_WORDS = [
    {"j": "おはよう", "r": "ohayou", "m": "Buongiorno"},
    {"j": "ぎんこう", "r": "ginkou", "m": "Banca"},
    {"j": "でんしゃ", "r": "densha", "m": "Treno"},
    {"j": "じてんしゃ", "r": "jitensha", "m": "Bicicletta"},
    {"j": "きっぷ", "r": "kippu", "m": "Biglietto"},
    {"j": "がっこう", "r": "gakkou", "m": "Scuola"},
    {"j": "かばん", "r": "kaban", "m": "Borsa"},
    {"j": "とけい", "r": "tokei", "m": "Orologio"},
    {"j": "くつ", "r": "kutsu", "m": "Scarpe"},
    {"j": "しんぶん", "r": "shinbun", "m": "Giornale"},
    {"j": "えんぴつ", "r": "enpitsu", "m": "Matita"},
    {"j": "ぼうし", "r": "boushi", "m": "Cappello"},
    {"j": "かぞく", "r": "kazoku", "m": "Famiglia"},
    {"j": "おかあさん", "r": "okaasan", "m": "Mamma (altrui)"},
    {"j": "おにいさん", "r": "oniisan", "m": "Fratello maggiore"},
    {"j": "おねえさん", "r": "oneesan", "m": "Sorella maggiore"},
    {"j": "おとうと", "r": "otouto", "m": "Fratello minore"},
    {"j": "いもうと", "r": "imouto", "m": "Sorella minore"},
    {"j": "ぎゅうにゅう", "r": "gyuunyuu", "m": "Latte vaccino"},
    {"j": "おちゃ", "r": "ocha", "m": "Tè"},
    {"j": "たべもの", "r": "tabemono", "m": "Cibo"},
    {"j": "のみもの", "r": "nomimono", "m": "Bevanda"},
    {"j": "くだもの", "r": "kudamono", "m": "Frutta"},
    {"j": "やさい", "r": "yasai", "m": "Verdura"},
    {"j": "けさ", "r": "kesa", "m": "Stamattina"},
    {"j": "あした", "r": "ashita", "m": "Domani"},
    {"j": "きょう", "r": "kyou", "m": "Oggi"},
    {"j": "きのう", "r": "kinou", "m": "Ieri"},
    {"j": "こんしゅう", "r": "konshuu", "m": "Questa settimana"},
    {"j": "らいしゅう", "r": "raishuu", "m": "Prossima settimana"},
    {"j": "びょういん", "r": "byouin", "m": "Ospedale"},
    {"j": "びよういん", "r": "biyouin", "m": "Parrucchiere"},
    {"j": "ゆうびんきょく", "r": "yuubinkyoku", "m": "Ufficio postale"},
    {"j": "えき", "r": "eki", "m": "Stazione"},
    {"j": "こうえん", "r": "kouen", "m": "Parco"},
    {"j": "だいがく", "r": "daigaku", "m": "Università"},
    {"j": "としょかん", "r": "toshokan", "m": "Biblioteca"},
    {"j": "えいが", "r": "eiga", "m": "Film"},
    {"j": "くもり", "r": "kumori", "m": "Nuvoloso"},
    {"j": "はれ", "r": "hare", "m": "Sereno (meteo)"},
    {"j": "じしょ", "r": "jisho", "m": "Dizionario"},
    {"j": "ざっし", "r": "zasshi", "m": "Rivista"},
    {"j": "へや", "r": "heya", "m": "Stanza"},
    {"j": "しゃしん", "r": "shashin", "m": "Foto"},
    {"j": "きって", "r": "kitte", "m": "Francobollo"},
    {"j": "しゅくだい", "r": "shukudai", "m": "Compiti"},
    {"j": "たんじょうび", "r": "tanjoubi", "m": "Compleanno"},
    {"j": "りょこう", "r": "ryokou", "m": "Viaggio"},
    {"j": "ひこうき", "r": "hikouki", "m": "Aereo"},
    {"j": "ちかてつ", "r": "chikatetsu", "m": "Metropolitana"},
    {"j": "ともだち", "r": "tomodachi", "m": "Amico"},
    {"j": "おかね", "r": "okane", "m": "Soldi"},
    {"j": "おみやげ", "r": "omiyage", "m": "Souvenir"},
    {"j": "おてら", "r": "otera", "m": "Tempio buddista"},
    {"j": "じんじゃ", "r": "jinja", "m": "Santuario shintoista"},
    {"j": "むずかしい", "r": "muzukashii", "m": "Difficile"},
    {"j": "おいしい", "r": "oishii", "m": "Delizioso"},
    {"j": "たのしい", "r": "tanoshii", "m": "Divertente"},
    {"j": "いそがしい", "r": "isogashii", "m": "Occupato"},
    {"j": "きたない", "r": "kitanai", "m": "Sporco"},
    {"j": "しずか", "r": "shizuka", "m": "Silenzioso"},
    {"j": "げんき", "r": "genki", "m": "Energico / Sano"},
    {"j": "しんせつ", "r": "shinsetsu", "m": "Gentile"},
    {"j": "べんり", "r": "benri", "m": "Comodo"},
    {"j": "じょうず", "r": "jouzu", "m": "Bravo in"},
    {"j": "へた", "r": "heta", "m": "Scarso in"}
]

vocab_path = "/home/ubuntu/japanese-app/app/data/zen_vocab.json"
with open(vocab_path, "r", encoding="utf-8") as f:
    vocab = json.load(f)

current_max_id = max(w["id"] for w in vocab) if vocab else 0

existing_j = {w["j"] for w in vocab}

for word in NEW_WORDS:
    if word["j"] not in existing_j:
        current_max_id += 1
        word["id"] = current_max_id
        # Calculate needed chars correctly
        word["k"] = list(set(word["j"]))
        vocab.append(word)

with open(vocab_path, "w", encoding="utf-8") as f:
    json.dump(vocab, f, ensure_ascii=False, indent=4)

print(f"Added new words. Total words now: {len(vocab)}")
