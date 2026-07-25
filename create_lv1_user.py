from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Base, User, Card, UserCard
import datetime
from datetime import date
import json

def seed_kanji_and_user():
    db = SessionLocal()
    
    # 1. Seed Kanji cards
    with open("app/data/zen_lv1_kanji.json", "r", encoding="utf-8") as f:
        kanji_data = json.load(f)
        
    for k in kanji_data:
        front = k["kanji"]
        back = k["meaning"]
        romanji = f"ON: {', '.join(k['onyomi'])} | KUN: {', '.join(k['kunyomi'])}"
        notes = " | ".join(k["examples"])
        
        existing = db.query(Card).filter(Card.phase == "kanji", Card.front == front).first()
        if not existing:
            card = Card(phase="kanji", group_name="kanji_1", front=front, back=back, romanji=romanji, notes=notes)
            db.add(card)
            
    db.commit()
    
    # 2. Create test user
    test_user = db.query(User).filter(User.email == "test_lv1@dev.com").first()
    if not test_user:
        test_user = User(
            google_id="dev_lv1",
            email="test_lv1@dev.com",
            name="Test Level 1",
            target_daily_new_cards=5,
            target_daily_minutes=20,
            active_days_this_month=1
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
    # 3. Unlock all previous phases for this user
    all_cards = db.query(Card).all()
    for card in all_cards:
        if card.phase in ["hiragana", "katakana", "grammar"]:
            # Set to learned
            uc = db.query(UserCard).filter(UserCard.user_id == test_user.id, UserCard.card_id == card.id).first()
            if not uc:
                uc = UserCard(user_id=test_user.id, card_id=card.id)
                db.add(uc)
            uc.srs_stage = 5
            uc.introduced_date = date.today() - datetime.timedelta(days=1)
            
    db.commit()
    print("Test user 'test_lv1' created with password 'password'. All Hiragana/Katakana/Grammar unlocked.")
    db.close()

if __name__ == "__main__":
    seed_kanji_and_user()
