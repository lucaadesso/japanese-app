from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Card
import json

def seed_lv1():
    db = SessionLocal()
    
    # 1. Seed Kanji
    with open("app/data/zen_lv1_kanji.json", "r", encoding="utf-8") as f:
        kanji_data = json.load(f)
        
    for k in kanji_data:
        front = k["kanji"]
        back = k["meaning"]
        romanji = f"ON: {', '.join(k['onyomi'])} | KUN: {', '.join(k['kunyomi'])}"
        notes = " | ".join(k["examples"])
        
        # Decide group based on id index roughly
        idx = int(k["id"].replace("k", ""))
        group_num = ((idx - 1) // 10) + 1
        group_name = f"kanji_{group_num}"
        
        existing = db.query(Card).filter(Card.phase == "kanji", Card.front == front).first()
        if not existing:
            card = Card(phase="kanji", group_name=group_name, front=front, back=back, romanji=romanji, notes=notes)
            db.add(card)
            
    # 2. Seed Vocab
    with open("app/data/zen_lv1_vocab.json", "r", encoding="utf-8") as f:
        vocab_data = json.load(f)
        
    for v in vocab_data:
        front = v["kanji"]
        back = " / ".join(v["meaning"])
        romanji = v["romaji"]
        notes = f"Kana: {v['kana']} | Tipo: {v['type']}"
        
        idx = int(v["id"].replace("v", ""))
        group_num = ((idx - 1) // 10) + 1
        group_name = f"vocab_{group_num}"
        
        existing = db.query(Card).filter(Card.phase == "vocab", Card.front == front).first()
        if not existing:
            card = Card(phase="vocab", group_name=group_name, front=front, back=back, romanji=romanji, notes=notes)
            db.add(card)
            
    db.commit()
    print("Seed completo!")
    db.close()

if __name__ == "__main__":
    seed_lv1()
