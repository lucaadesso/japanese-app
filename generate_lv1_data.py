import json

kanji = [
    {"id": "k1", "kanji": "一", "meaning": "Uno", "onyomi": ["ichi", "itsu"], "kunyomi": ["hito"], "examples": ["一つ (hitotsu)"]},
    {"id": "k2", "kanji": "二", "meaning": "Due", "onyomi": ["ni", "ji"], "kunyomi": ["futa"], "examples": ["二つ (futatsu)"]},
    {"id": "k3", "kanji": "三", "meaning": "Tre", "onyomi": ["san"], "kunyomi": ["mi"], "examples": ["三つ (mittsu)"]},
    {"id": "k4", "kanji": "四", "meaning": "Quattro", "onyomi": ["shi"], "kunyomi": ["yon", "yo"], "examples": ["四つ (yottsu)"]},
    {"id": "k5", "kanji": "五", "meaning": "Cinque", "onyomi": ["go"], "kunyomi": ["itsu"], "examples": ["五つ (itsutsu)"]},
    {"id": "k6", "kanji": "六", "meaning": "Sei", "onyomi": ["roku"], "kunyomi": ["mu"], "examples": ["六つ (muttsu)"]},
    {"id": "k7", "kanji": "七", "meaning": "Sette", "onyomi": ["shichi"], "kunyomi": ["nana"], "examples": ["七つ (nanatsu)"]},
    {"id": "k8", "kanji": "八", "meaning": "Otto", "onyomi": ["hachi"], "kunyomi": ["ya"], "examples": ["八つ (yattsu)"]},
    {"id": "k9", "kanji": "九", "meaning": "Nove", "onyomi": ["kyuu", "ku"], "kunyomi": ["kokono"], "examples": ["九つ (kokonotsu)"]},
    {"id": "k10", "kanji": "十", "meaning": "Dieci", "onyomi": ["juu"], "kunyomi": ["too"], "examples": ["十 (too)"]},
    {"id": "k11", "kanji": "百", "meaning": "Cento", "onyomi": ["hyaku"], "kunyomi": [], "examples": ["三百 (sanbyaku)"]},
    {"id": "k12", "kanji": "千", "meaning": "Mille", "onyomi": ["sen"], "kunyomi": ["chi"], "examples": ["三千 (sanzen)"]},
    {"id": "k13", "kanji": "万", "meaning": "Diecimila", "onyomi": ["man", "ban"], "kunyomi": [], "examples": ["一万 (ichiman)"]},
    {"id": "k14", "kanji": "日", "meaning": "Sole / Giorno", "onyomi": ["nichi", "jitsu"], "kunyomi": ["hi", "ka"], "examples": ["日本 (nihon)"]},
    {"id": "k15", "kanji": "月", "meaning": "Luna / Mese", "onyomi": ["getsu", "gatsu"], "kunyomi": ["tsuki"], "examples": ["月曜日 (getsuyoubi)"]},
    {"id": "k16", "kanji": "火", "meaning": "Fuoco", "onyomi": ["ka"], "kunyomi": ["hi"], "examples": ["火曜日 (kayoubi)"]},
    {"id": "k17", "kanji": "水", "meaning": "Acqua", "onyomi": ["sui"], "kunyomi": ["mizu"], "examples": ["水曜日 (suiyoubi)"]},
    {"id": "k18", "kanji": "木", "meaning": "Albero", "onyomi": ["moku", "boku"], "kunyomi": ["ki"], "examples": ["木曜日 (mokuyoubi)"]},
    {"id": "k19", "kanji": "金", "meaning": "Oro / Denaro", "onyomi": ["kin", "kon"], "kunyomi": ["kane"], "examples": ["金曜日 (kinyoubi)"]},
    {"id": "k20", "kanji": "土", "meaning": "Terra", "onyomi": ["do", "to"], "kunyomi": ["tsuchi"], "examples": ["土曜日 (doyoubi)"]},
    {"id": "k21", "kanji": "人", "meaning": "Persona", "onyomi": ["jin", "nin"], "kunyomi": ["hito"], "examples": ["日本人 (nihonjin)"]},
    {"id": "k22", "kanji": "大", "meaning": "Grande", "onyomi": ["dai", "tai"], "kunyomi": ["oo"], "examples": ["大きい (ookii)"]},
    {"id": "k23", "kanji": "中", "meaning": "Centro / Dentro", "onyomi": ["chuu"], "kunyomi": ["naka"], "examples": ["中国 (chuugoku)"]},
    {"id": "k24", "kanji": "小", "meaning": "Piccolo", "onyomi": ["shou"], "kunyomi": ["chii", "ko", "o"], "examples": ["小さい (chiisai)"]},
    {"id": "k25", "kanji": "上", "meaning": "Sopra", "onyomi": ["jou", "shou"], "kunyomi": ["ue", "a", "no"], "examples": ["上 (ue)"]},
    {"id": "k26", "kanji": "下", "meaning": "Sotto", "onyomi": ["ka", "ge"], "kunyomi": ["shita", "sa", "kuda"], "examples": ["下 (shita)"]},
    {"id": "k27", "kanji": "本", "meaning": "Libro / Radice", "onyomi": ["hon"], "kunyomi": ["moto"], "examples": ["本 (hon)"]},
    {"id": "k28", "kanji": "行", "meaning": "Andare", "onyomi": ["kou", "gyou"], "kunyomi": ["i", "yu", "okona"], "examples": ["行く (iku)"]},
    {"id": "k29", "kanji": "来", "meaning": "Venire", "onyomi": ["rai"], "kunyomi": ["ku", "ki", "ko"], "examples": ["来る (kuru)"]},
    {"id": "k30", "kanji": "食", "meaning": "Mangiare", "onyomi": ["shoku"], "kunyomi": ["ta", "ku"], "examples": ["食べる (taberu)"]}
]

vocab = [
    {"id": "v1", "type": "noun", "kanji": "日本", "kana": "にほん", "romaji": "nihon", "meaning": ["Giappone"]},
    {"id": "v2", "type": "noun", "kanji": "日本人", "kana": "にほんじん", "romaji": "nihonjin", "meaning": ["Giapponese (persona)"]},
    {"id": "v3", "type": "noun", "kanji": "月曜日", "kana": "げつようび", "romaji": "getsuyoubi", "meaning": ["Lunedi", "Lunedì"]},
    {"id": "v4", "type": "noun", "kanji": "火曜日", "kana": "かようび", "romaji": "kayoubi", "meaning": ["Martedi", "Martedì"]},
    {"id": "v5", "type": "noun", "kanji": "水曜日", "kana": "すいようび", "romaji": "suiyoubi", "meaning": ["Mercoledi", "Mercoledì"]},
    {"id": "v6", "type": "noun", "kanji": "木曜日", "kana": "もくようび", "romaji": "mokuyoubi", "meaning": ["Giovedi", "Giovedì"]},
    {"id": "v7", "type": "noun", "kanji": "金曜日", "kana": "きんようび", "romaji": "kinyoubi", "meaning": ["Venerdi", "Venerdì"]},
    {"id": "v8", "type": "noun", "kanji": "土曜日", "kana": "どようび", "romaji": "doyoubi", "meaning": ["Sabato"]},
    {"id": "v9", "type": "noun", "kanji": "日曜日", "kana": "にちようび", "romaji": "nichiyoubi", "meaning": ["Domenica"]},
    {"id": "v10", "type": "verb", "kanji": "食べる", "kana": "たべる", "romaji": "taberu", "meaning": ["Mangiare"]},
    {"id": "v11", "type": "verb", "kanji": "飲む", "kana": "のむ", "romaji": "nomu", "meaning": ["Bere"]},
    {"id": "v12", "type": "verb", "kanji": "行く", "kana": "いく", "romaji": "iku", "meaning": ["Andare"]},
    {"id": "v13", "type": "verb", "kanji": "来る", "kana": "くる", "romaji": "kuru", "meaning": ["Venire"]},
    {"id": "v14", "type": "verb", "kanji": "見る", "kana": "みる", "romaji": "miru", "meaning": ["Vedere", "Guardare"]},
    {"id": "v15", "type": "verb", "kanji": "聞く", "kana": "きく", "romaji": "kiku", "meaning": ["Ascoltare", "Sentire", "Chiedere"]},
    {"id": "v16", "type": "adjective", "kanji": "大きい", "kana": "おおきい", "romaji": "ookii", "meaning": ["Grande"]},
    {"id": "v17", "type": "adjective", "kanji": "小さい", "kana": "ちいさい", "romaji": "chiisai", "meaning": ["Piccolo"]},
    {"id": "v18", "type": "adjective", "kanji": "高い", "kana": "たかい", "romaji": "takai", "meaning": ["Alto", "Costoso"]},
    {"id": "v19", "type": "adjective", "kanji": "安い", "kana": "やすい", "romaji": "yasui", "meaning": ["Economico"]},
    {"id": "v20", "type": "adjective", "kanji": "新しい", "kana": "あたらしい", "romaji": "atarashii", "meaning": ["Nuovo"]},
    {"id": "v21", "type": "adjective", "kanji": "古い", "kana": "ふるい", "romaji": "furui", "meaning": ["Vecchio"]},
    {"id": "v22", "type": "noun", "kanji": "本", "kana": "ほん", "romaji": "hon", "meaning": ["Libro"]},
    {"id": "v23", "type": "noun", "kanji": "学生", "kana": "がくせい", "romaji": "gakusei", "meaning": ["Studente"]},
    {"id": "v24", "type": "noun", "kanji": "先生", "kana": "せんせい", "romaji": "sensei", "meaning": ["Insegnante", "Maestro"]},
    {"id": "v25", "type": "noun", "kanji": "学校", "kana": "がっこう", "romaji": "gakkou", "meaning": ["Scuola"]},
    {"id": "v26", "type": "noun", "kanji": "水", "kana": "みず", "romaji": "mizu", "meaning": ["Acqua"]},
    {"id": "v27", "type": "noun", "kanji": "人", "kana": "ひと", "romaji": "hito", "meaning": ["Persona"]},
    {"id": "v28", "type": "noun", "kanji": "今日", "kana": "きょう", "romaji": "kyou", "meaning": ["Oggi"]},
    {"id": "v29", "type": "noun", "kanji": "明日", "kana": "あした", "romaji": "ashita", "meaning": ["Domani"]},
    {"id": "v30", "type": "noun", "kanji": "昨日", "kana": "きのう", "romaji": "kinou", "meaning": ["Ieri"]}
]

with open("app/data/zen_lv1_kanji.json", "w", encoding="utf-8") as f:
    json.dump(kanji, f, ensure_ascii=False, indent=2)
    
with open("app/data/zen_lv1_vocab.json", "w", encoding="utf-8") as f:
    json.dump(vocab, f, ensure_ascii=False, indent=2)
    
print("Generated lv1 kanji and vocab")
