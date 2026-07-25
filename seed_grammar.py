from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Card, UserCard
import json
import os

def seed_grammar():
    db = SessionLocal()
    users = db.query(User).all()
    
    path = "/home/ubuntu/japanese-app/app/data/grammar_lessons.json"
    with open(path, "r", encoding="utf-8") as f:
        lessons = json.load(f)
        
    for user in users:
        # Check existing grammar cards
        existing_g_cards = db.query(Card).filter(Card.phase == "grammar").all()
        existing_g_fronts = {c.front for c in existing_g_cards}
        
        for lesson in lessons:
            front = lesson["title"]
            back = lesson["rule"]
            romanji = lesson["formula"]
            group = lesson["group_name"]
            
            if front not in existing_g_fronts:
                card = Card(phase="grammar", group_name=group, front=front, back=back, romanji=romanji)
                db.add(card)
                db.commit() # commit to get ID
                
                uc = db.query(UserCard).filter(UserCard.user_id == user.id, UserCard.card_id == card.id).first()
                if not uc:
                    uc = UserCard(user_id=user.id, card_id=card.id)
                    db.add(uc)
                    
        db.commit()
    db.close()
    print("Grammar seed complete.")

if __name__ == "__main__":
    seed_grammar()
