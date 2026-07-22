"""
srs.py – Adaptive Spaced-Repetition System (SM-2) + Learn Mode logic

Key features:
- SM-2 ease-factor scheduling
- Daily cap: max 25 review cards / max 5 new learn cards per day
- Study-time cap: 15 min soft / 20 min hard → Zen Mode
- Learn Mode: present → quiz → mark srs_stage=1 → enters SRS queue
- Unlock progression: vowels → ka → sa → ta → na → ha → ma → ya → ra → wa → n
  Katakana unlocks at 80% Hiragana mastery; Vocab after all Kana
- Per-group progress API for dashboard grid
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Card, DailyStudy, User, UserCard

# ─── Constants ───────────────────────────────────────────────────────────────
DAILY_CARD_CAP      = 25          # max review cards shown per day
NEW_LEARN_PER_DAY   = 5           # max NEW cards introduced via Learn per day
SOFT_LIMIT_SECONDS  = 15 * 60     # 15 min → warn
HARD_LIMIT_SECONDS  = 20 * 60     # 20 min → Zen Mode redirect
MIN_EASE            = 1.3         # SM-2 minimum ease factor

# Unlock threshold: fraction of a phase that must be learned before next phase
UNLOCK_THRESHOLD    = 0.80        # 80%

# ─── Group ordering (sequential unlock within phase) ─────────────────────────
HIRAGANA_GROUP_ORDER = [
    "vowels", "ka", "sa", "ta", "na", "ha", "ma", "ya", "ra", "wa", "n"
]
KATAKANA_GROUP_ORDER = [
    "vowels", "ka", "sa", "ta", "na", "ha", "ma", "ya", "ra", "wa", "n"
]

# ─── Hiragana seed data: (front, back, romanji, group, mnemonic note) ────────
HIRAGANA_DATA = [
    # Vowels
    ("あ", "a",  "a",   "vowels", "Sembra una persona con le braccia aperte: 'Aah!'"),
    ("い", "i",  "i",   "vowels", "Due linee verticali come due persone in piedi: 'i i'"),
    ("う", "u",  "u",   "vowels", "Una bocca arrotondata che fa 'u'"),
    ("え", "e",  "e",   "vowels", "Come una croce con un cappello: 'e' come 'ella'"),
    ("お", "o",  "o",   "vowels", "Un vortice rotondo: 'o' come 'oh!'"),
    # Ka-row
    ("か", "ka", "ka",  "ka", "Come una persona che cade: 'KA-boom!'"),
    ("き", "ki", "ki",  "ka", "Sembra una chiave (key): 'ki'"),
    ("く", "ku", "ku",  "ka", "Il becco di un uccello che dice 'ku-ku'"),
    ("け", "ke", "ke",  "ka", "Come una cassetta (keg): 'ke'"),
    ("こ", "ko", "ko",  "ka", "Due linee che si incrociano come in 'ko-cross'"),
    # Sa-row
    ("さ", "sa", "sa",  "sa", "Sembra una persona che saluta (sa-lute)"),
    ("し", "shi","shi", "sa", "Un uncino che fischia: 'shi'"),
    ("す", "su", "su",  "sa", "Una spirale come un tornado: 'su'-perfice"),
    ("せ", "se", "se",  "sa", "Come una sedia (seat): 'se'"),
    ("そ", "so", "so",  "sa", "Una curva come il numero 3 al contrario: 'so'"),
    # Ta-row
    ("た", "ta", "ta",  "ta", "Come una croce con un braccio che dice 'ta-tà!'"),
    ("ち", "chi","chi", "ta", "Come una piccola sedia (chair): 'chi'"),
    ("つ", "tsu","tsu", "ta", "Un tsunami! 'tsu'nami"),
    ("て", "te", "te",  "ta", "Come un gancio (te-nacious): 'te'"),
    ("と", "to", "to",  "ta", "Come una candela che dice 'to-rcia'"),
    # Na-row
    ("な", "na", "na",  "na", "Come la parola 'na-turally' scritta in corsivo"),
    ("に", "ni", "ni",  "na", "Due linee come le gambe di qualcuno che cammina: 'ni'"),
    ("ぬ", "nu", "nu",  "na", "Come spaghetti (noodles): 'nu'"),
    ("ね", "ne", "ne",  "na", "Come un gatto che dorme (neko): 'ne'"),
    ("の", "no", "no",  "na", "Una spirale che dice 'no no no!'"),
    # Ha-row
    ("は", "ha", "ha",  "ha", "Come qualcuno che ride: 'ha ha ha!'"),
    ("ひ", "hi", "hi",  "ha", "Come una montagna con la cima (high): 'hi'"),
    ("ふ", "fu", "fu",  "ha", "Come un vulcano che soffia: 'fu'"),
    ("へ", "he", "he",  "ha", "Una piccola collinetta: 'he'llo"),
    ("ほ", "ho", "ho",  "ha", "Come Babbo Natale: 'ho ho ho!'"),
    # Ma-row
    ("ま", "ma", "ma",  "ma", "Come 'mamma' che abbraccia: 'ma'"),
    ("み", "mi", "mi",  "ma", "Come una nota musicale 'mi': 'mi'"),
    ("む", "mu", "mu",  "ma", "Come una mucca che muggisce: 'mu'"),
    ("め", "me", "me",  "ma", "Come un occhio (me=eye in spirit): 'me'"),
    ("も", "mo", "mo",  "ma", "Come un verme (worm): 'mo'"),
    # Ya-row
    ("や", "ya", "ya",  "ya", "Come qualcuno che dice 'ya' (sì in tedesco!)"),
    ("ゆ", "yu", "yu",  "ya", "Come un pesce che nuota: 'yu'"),
    ("よ", "yo", "yo",  "ya", "Come qualcuno che saluta: 'yo!'"),
    # Ra-row
    ("ら", "ra", "ra",  "ra", "Come ra-ggi di sole: 'ra'"),
    ("り", "ri", "ri",  "ra", "Due virgole come rami: 'ri'"),
    ("る", "ru", "ru",  "ra", "Una spirale come un rubinetto aperto: 'ru'"),
    ("れ", "re", "re",  "ra", "Come una re-gina con lo scettro: 're'"),
    ("ろ", "ro", "ro",  "ra", "Come una strada (road): 'ro'"),
    # Wa-row
    ("わ", "wa", "wa",  "wa", "Come qualcuno che dice 'wow': 'wa'"),
    ("を", "wo", "wo",  "wa", "Come la lettera 'o' con un cappello: 'wo'"),
    # N
    ("ん", "n",  "n",   "n",  "Come una onda (wave) che finisce in 'n'"),
]

# ─── Katakana seed data: (front, back, romanji, group, mnemonic note) ────────
KATAKANA_DATA = [
    # Vowels
    ("ア", "a",  "a",   "vowels", "Come due linee che si incontrano in punta: 'A'"),
    ("イ", "i",  "i",   "vowels", "Come due alberi inclinati: 'i'"),
    ("ウ", "u",  "u",   "vowels", "Come un cappello con una testa: 'u'"),
    ("エ", "e",  "e",   "vowels", "Come la lettera H: 'e'"),
    ("オ", "o",  "o",   "vowels", "Come una croce con una linea: 'o'"),
    # Ka-row
    ("カ", "ka", "ka",  "ka", "Come una katana (spada): 'ka'"),
    ("キ", "ki", "ki",  "ka", "Come una chiave: 'ki'"),
    ("ク", "ku", "ku",  "ka", "Come il becco di un uccello: 'ku'"),
    ("ケ", "ke", "ke",  "ka", "Come una K grande: 'ke'"),
    ("コ", "ko", "ko",  "ka", "Come due segmenti ad angolo retto: 'ko'"),
    # Sa-row
    ("サ", "sa", "sa",  "sa", "Come una forchetta: 'sa'"),
    ("シ", "shi","shi", "sa", "Come tre linee di pioggia: 'shi'"),
    ("ス", "su", "su",  "sa", "Come una curva con un punto: 'su'"),
    ("セ", "se", "se",  "sa", "Come una piccola S: 'se'"),
    ("ソ", "so", "so",  "sa", "Come una virgola grande: 'so'"),
    # Ta-row
    ("タ", "ta", "ta",  "ta", "Come un tamburello: 'ta'"),
    ("チ", "chi","chi", "ta", "Come una freccia verso destra: 'chi'"),
    ("ツ", "tsu","tsu", "ta", "Come tre gocce d'acqua: 'tsu'"),
    ("テ", "te", "te",  "ta", "Come una T con una croce: 'te'"),
    ("ト", "to", "to",  "ta", "Come un palo con una freccia: 'to'"),
    # Na-row
    ("ナ", "na", "na",  "na", "Come una croce con una linea: 'na'"),
    ("ニ", "ni", "ni",  "na", "Come il numero 2 (ni in giapponese!): 'ni'"),
    ("ヌ", "nu", "nu",  "na", "Come una curva intrecciata: 'nu'"),
    ("ネ", "ne", "ne",  "na", "Come una rete (net): 'ne'"),
    ("ノ", "no", "no",  "na", "Come una barra obliqua: 'no'"),
    # Ha-row
    ("ハ", "ha", "ha",  "ha", "Come due gambe aperte: 'ha'"),
    ("ヒ", "hi", "hi",  "ha", "Come la lettera H con una barra: 'hi'"),
    ("フ", "fu", "fu",  "ha", "Come un gancio: 'fu'"),
    ("ヘ", "he", "he",  "ha", "Come una piccola collina: 'he'"),
    ("ホ", "ho", "ho",  "ha", "Come una croce con due gambe: 'ho'"),
    # Ma-row
    ("マ", "ma", "ma",  "ma", "Come una persona con le braccia alzate: 'ma'"),
    ("ミ", "mi", "mi",  "ma", "Come tre linee orizzontali: 'mi'"),
    ("ム", "mu", "mu",  "ma", "Come una mucca di profilo: 'mu'"),
    ("メ", "me", "me",  "ma", "Come una X barrata: 'me'"),
    ("モ", "mo", "mo",  "ma", "Come tre linee con un gancio: 'mo'"),
    # Ya-row
    ("ヤ", "ya", "ya",  "ya", "Come una Y stilizzata: 'ya'"),
    ("ユ", "yu", "yu",  "ya", "Come un U squadrato: 'yu'"),
    ("ヨ", "yo", "yo",  "ya", "Come tre linee che dicono 'yo!': 'yo'"),
    # Ra-row
    ("ラ", "ra", "ra",  "ra", "Come una L con un cappello: 'ra'"),
    ("リ", "ri", "ri",  "ra", "Come due linee parallele: 'ri'"),
    ("ル", "ru", "ru",  "ra", "Come una curva a destra: 'ru'"),
    ("レ", "re", "re",  "ra", "Come una L maiuscola: 're'"),
    ("ロ", "ro", "ro",  "ra", "Come un quadrato (room): 'ro'"),
    # Wa-row
    ("ワ", "wa", "wa",  "wa", "Come la lettera ワ simile a U: 'wa'"),
    ("ヲ", "wo", "wo",  "wa", "Come una croce con base: 'wo'"),
    # N
    ("ン", "n",  "n",   "n",  "Come una ン simile a 'so' ma specchiata: 'n'"),
]


# ─── SM-2 Core ───────────────────────────────────────────────────────────────

def sm2_update(uc: UserCard, quality: int) -> UserCard:
    """Apply SM-2: quality 0-5 (0=blackout, 5=perfect)."""
    q = max(0, min(5, quality))
    if q < 3:
        uc.repetitions = 0
        uc.interval    = 1
    else:
        if uc.repetitions == 0:
            uc.interval = 1
        elif uc.repetitions == 1:
            uc.interval = 6
        else:
            uc.interval = math.ceil(uc.interval * uc.ease_factor)
        uc.repetitions += 1

    uc.ease_factor = max(
        MIN_EASE,
        uc.ease_factor + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02),
    )
    uc.due_date      = date.today() + timedelta(days=uc.interval)
    uc.last_reviewed = date.today()
    uc.is_new        = False
    if uc.srs_stage < 2:
        uc.srs_stage = 2   # graduated from Learn → SRS
    return uc


# ─── Learn Mode helpers ───────────────────────────────────────────────────────

def get_current_learn_group(db: Session, user: User) -> Optional[dict]:
    """
    Returns the next group the user should learn, following unlock rules.
    Returns None if all groups are completed.

    Unlock order:
      Hiragana groups in HIRAGANA_GROUP_ORDER (sequential)
      Katakana unlocks when Hiragana >= UNLOCK_THRESHOLD
      (Vocab not yet implemented)
    """
    # Check hiragana groups first
    for group in HIRAGANA_GROUP_ORDER:
        progress = get_group_progress(db, user, "hiragana", group)
        if progress["pct_learned"] < 100:
            return {"phase": "hiragana", "group": group, "progress": progress}

    # All Hiragana done → check if Katakana is unlocked
    hira_total = get_phase_progress(db, user, "hiragana")
    if hira_total["pct_learned"] >= int(UNLOCK_THRESHOLD * 100):
        for group in KATAKANA_GROUP_ORDER:
            progress = get_group_progress(db, user, "katakana", group)
            if progress["pct_learned"] < 100:
                return {"phase": "katakana", "group": group, "progress": progress}

    return None   # everything complete


def get_learn_cards_for_session(db: Session, user: User, limit: int = NEW_LEARN_PER_DAY) -> list[UserCard]:
    """
    Get up to `limit` unseen UserCards (srs_stage=0) from the current group,
    respecting daily new-card cap.
    """
    current = get_current_learn_group(db, user)
    if not current:
        return []

    phase = current["phase"]
    group = current["group"]

    # Count how many new cards already introduced today
    already_today = count_new_learned_today(db, user)
    remaining_slots = max(0, limit - already_today)
    if remaining_slots == 0:
        return []

    # Get unseen UserCards for this group
    unseen = (
        db.query(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .filter(
            UserCard.user_id == user.id,
            UserCard.srs_stage == 0,
            Card.phase == phase,
            Card.group_name == group,
        )
        .order_by(Card.id)
        .limit(remaining_slots)
        .all()
    )
    return unseen


def count_new_learned_today(db: Session, user: User) -> int:
    """Count cards that moved from srs_stage=0→1 today."""
    from datetime import date as _date
    today = _date.today()
    return (
        db.query(UserCard)
        .filter(
            UserCard.user_id == user.id,
            UserCard.srs_stage >= 1,
            UserCard.last_reviewed == today,
        )
        .count()
    )


def mark_card_learned(db: Session, uc: UserCard) -> UserCard:
    """Mark a UserCard as introduced via Learn (srs_stage=1, is_new=False)."""
    uc.srs_stage     = 1
    uc.is_new        = False
    uc.last_reviewed = date.today()
    # Set initial due date for first SRS review: tomorrow
    uc.due_date      = date.today() + timedelta(days=1)
    db.commit()
    db.refresh(uc)
    return uc


# ─── Daily card queue (Review) ────────────────────────────────────────────────

def get_due_cards(db: Session, user: User, limit: int = DAILY_CARD_CAP) -> list[UserCard]:
    """Returns up to `limit` UserCards due today (srs_stage >= 1, due today or overdue)."""
    today = date.today()
    return (
        db.query(UserCard)
        .filter(
            UserCard.user_id == user.id,
            UserCard.srs_stage >= 1,
            UserCard.due_date <= today,
        )
        .order_by(UserCard.due_date)
        .limit(limit)
        .all()
    )


# ─── Progress helpers ─────────────────────────────────────────────────────────

def get_group_progress(db: Session, user: User, phase: str, group: str) -> dict:
    """Per-group progress stats."""
    total_cards = (
        db.query(Card)
        .filter(Card.phase == phase, Card.group_name == group)
        .count()
    )
    learned = (
        db.query(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .filter(
            UserCard.user_id == user.id,
            UserCard.srs_stage >= 1,
            Card.phase == phase,
            Card.group_name == group,
        )
        .count()
    )
    mastered = (
        db.query(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .filter(
            UserCard.user_id == user.id,
            UserCard.repetitions >= 3,
            Card.phase == phase,
            Card.group_name == group,
        )
        .count()
    )
    pct = int(learned / total_cards * 100) if total_cards else 0
    return {
        "phase": phase,
        "group": group,
        "total": total_cards,
        "learned": learned,
        "mastered": mastered,
        "pct_learned": pct,
        "complete": pct >= 100,
    }


def get_phase_progress(db: Session, user: User, phase: str) -> dict:
    """Aggregate progress for an entire phase."""
    total = db.query(Card).filter(Card.phase == phase).count()
    learned = (
        db.query(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .filter(UserCard.user_id == user.id, UserCard.srs_stage >= 1, Card.phase == phase)
        .count()
    )
    pct = int(learned / total * 100) if total else 0
    return {"phase": phase, "total": total, "learned": learned, "pct_learned": pct}


def get_dashboard_progress(db: Session, user: User) -> dict:
    """Full progress data for the dashboard: per-group + phase totals + unlock status."""
    hira_groups = [
        get_group_progress(db, user, "hiragana", g) for g in HIRAGANA_GROUP_ORDER
    ]
    kata_groups = [
        get_group_progress(db, user, "katakana", g) for g in KATAKANA_GROUP_ORDER
    ]
    hira_phase = get_phase_progress(db, user, "hiragana")
    kata_phase = get_phase_progress(db, user, "katakana")

    katakana_unlocked = hira_phase["pct_learned"] >= int(UNLOCK_THRESHOLD * 100)
    vocab_unlocked    = kata_phase["pct_learned"] >= 100

    # Determine which group is currently being unlocked
    current = get_current_learn_group(db, user)

    return {
        "hiragana": {"phase": hira_phase, "groups": hira_groups},
        "katakana": {"phase": kata_phase, "groups": kata_groups, "unlocked": katakana_unlocked},
        "vocab":    {"unlocked": vocab_unlocked},
        "current_learn": current,
    }


# ─── Study-time helpers ───────────────────────────────────────────────────────

def get_today_seconds(db: Session, user: User) -> int:
    today = date.today()
    record = db.query(DailyStudy).filter(
        DailyStudy.user_id == user.id, DailyStudy.study_date == today
    ).first()
    return record.seconds_studied if record else 0


def add_study_seconds(db: Session, user: User, seconds: int) -> DailyStudy:
    today = date.today()
    record = db.query(DailyStudy).filter(
        DailyStudy.user_id == user.id, DailyStudy.study_date == today
    ).first()
    if not record:
        record = DailyStudy(user_id=user.id, study_date=today, seconds_studied=0)
        db.add(record)
    record.seconds_studied += seconds
    db.commit()
    db.refresh(record)
    return record


def is_over_soft_limit(db: Session, user: User) -> bool:
    return get_today_seconds(db, user) >= SOFT_LIMIT_SECONDS


def is_over_hard_limit(db: Session, user: User) -> bool:
    return get_today_seconds(db, user) >= HARD_LIMIT_SECONDS


def time_status(db: Session, user: User) -> dict:
    seconds = get_today_seconds(db, user)
    pct_hard = min(100, int(seconds / HARD_LIMIT_SECONDS * 100))
    pct_soft = min(100, int(seconds / SOFT_LIMIT_SECONDS * 100))
    return {
        "seconds_studied": seconds,
        "soft_limit": SOFT_LIMIT_SECONDS,
        "hard_limit": HARD_LIMIT_SECONDS,
        "pct_soft": pct_soft,
        "pct_hard": pct_hard,
        "over_soft": seconds >= SOFT_LIMIT_SECONDS,
        "over_hard": seconds >= HARD_LIMIT_SECONDS,
        "minutes_studied": round(seconds / 60, 1),
    }


# ─── Active Days ──────────────────────────────────────────────────────────────

def update_active_days(db: Session, user: User) -> None:
    today = date.today()
    if user.last_active_date is None or user.last_active_date.month != today.month:
        user.active_days_this_month = 1
    elif user.last_active_date != today:
        user.active_days_this_month += 1
    user.last_active_date = today
    db.commit()


# ─── Seed ─────────────────────────────────────────────────────────────────────

def seed_cards(db: Session) -> None:
    """Insert/update Hiragana and Katakana cards with groups and mnemonic notes."""
    # Check if already seeded with group_name populated
    existing = db.query(Card).filter(Card.group_name.isnot(None)).count()

    if existing == 0:
        # First time or needs re-seed with groups
        # Remove all existing cards and re-create (only safe at startup if no reviews)
        existing_total = db.query(Card).count()
        if existing_total == 0:
            # Fresh seed
            cards = []
            for front, back, romanji, group, note in HIRAGANA_DATA:
                cards.append(Card(phase="hiragana", group_name=group,
                                  front=front, back=back, romanji=romanji, notes=note))
            for front, back, romanji, group, note in KATAKANA_DATA:
                cards.append(Card(phase="katakana", group_name=group,
                                  front=front, back=back, romanji=romanji, notes=note))
            db.add_all(cards)
            db.commit()
        else:
            # Update existing cards with group_name and notes
            hira_map = {row[0]: row for row in HIRAGANA_DATA}
            kata_map = {row[0]: row for row in KATAKANA_DATA}
            for card in db.query(Card).all():
                row = hira_map.get(card.front) or kata_map.get(card.front)
                if row and card.group_name is None:
                    card.group_name = row[3]
                    card.notes      = row[4]
            db.commit()


def ensure_user_cards(db: Session, user: User) -> None:
    """Create UserCard rows for any Card not yet assigned to this user."""
    all_cards    = db.query(Card).all()
    existing_ids = {uc.card_id for uc in
                    db.query(UserCard).filter(UserCard.user_id == user.id).all()}
    new_ucs = [
        UserCard(user_id=user.id, card_id=c.id)
        for c in all_cards if c.id not in existing_ids
    ]
    if new_ucs:
        db.add_all(new_ucs)
        db.commit()
