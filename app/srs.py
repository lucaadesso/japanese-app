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
from datetime import date, timedelta, datetime
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
    "vowels", "ka", "sa", "ta", "na", "ha", "ma", "ya", "ra", "wa", "n",
    "dakuten", "handakuten", "yoon", "sokuon"
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
    ("っ", "(doppia)", "sokuon", "sokuon", "Piccolo Tsu: Raddoppia la consonante successiva"),
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
    uc.due_date      = datetime.now() + timedelta(days=uc.interval)
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


def get_learn_cards_for_session(db: Session, user: User, limit: Optional[int] = None) -> list[UserCard]:
    """
    Get up to `limit` unseen UserCards (srs_stage=0) from the current group,
    respecting the user's personal daily new-card target.
    """
    cap = limit if limit is not None else (user.target_daily_new_cards or NEW_LEARN_PER_DAY)
    current = get_current_learn_group(db, user)
    if not current:
        return []

    phase = current["phase"]
    group = current["group"]

    # First, get all fast_lane=True cards for this group (unlimited)
    fast_lane_cards = (
        db.query(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .filter(
            UserCard.user_id    == user.id,
            UserCard.srs_stage  == 0,
            UserCard.fast_lane  == True,
            Card.phase          == phase,
            Card.group_name     == group,
        )
        .order_by(Card.id)
        .all()
    )

    if fast_lane_cards:
        return fast_lane_cards

    already_today = count_new_learned_today(db, user)
    remaining_slots = max(0, cap - already_today)
    if remaining_slots == 0:
        return []

    unseen = (
        db.query(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .filter(
            UserCard.user_id    == user.id,
            UserCard.srs_stage  == 0,
            Card.phase          == phase,
            Card.group_name     == group,
        )
        .order_by(Card.id)
        .limit(remaining_slots)
        .all()
    )
    return unseen


def count_new_learned_today(db: Session, user: User) -> int:
    """Count cards introduced via Learn TODAY (uses introduced_date, not last_reviewed)."""
    from datetime import date as _date
    today = _date.today()
    return (
        db.query(UserCard)
        .filter(
            UserCard.user_id       == user.id,
            UserCard.introduced_date == today,    # set only by mark_card_learned()
        )
        .count()
    )


def mark_card_learned(db: Session, uc: UserCard, fast_lane_failed: bool = False) -> UserCard:
    """Mark a UserCard as introduced via Learn."""
    today = date.today()
    uc.is_new         = False
    uc.last_reviewed  = today
    uc.introduced_date = today          # ← track when this card was first introduced

    if getattr(uc, "fast_lane", False) and not fast_lane_failed:
        # Fast-lane success! Graduate immediately.
        uc.srs_stage = 2
        uc.interval = 1
        uc.repetitions = 1
        uc.due_date = datetime.now() + timedelta(days=1)
        uc.fast_lane = False
    else:
        uc.srs_stage = 1
        uc.due_date = datetime.now() # Due immediately for the mini-review
        uc.fast_lane = False

    db.commit()
    db.refresh(uc)
    return uc


# ─── Daily card queue (Review) ────────────────────────────────────────────────

def get_due_cards(db: Session, user: User, limit: int = DAILY_CARD_CAP) -> list[UserCard]:
    """Returns up to `limit` UserCards due today (srs_stage >= 1, due today or overdue)."""
    today = date.today()
    cards = (
        db.query(UserCard)
        .filter(
            UserCard.user_id == user.id,
            UserCard.srs_stage >= 1,
            UserCard.due_date <= datetime.now(),
        )
        .order_by(UserCard.due_date)
        .limit(limit)
        .all()
    )
    import random
    random.shuffle(cards)
    return cards


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
    """Return time status using the user's personal daily target."""
    seconds      = get_today_seconds(db, user)
    target_secs  = (user.target_daily_minutes or 20) * 60
    soft_secs    = int(target_secs * 0.75)  # soft warn at 75% of target
    pct_target   = min(100, int(seconds / target_secs * 100))
    pct_soft     = min(100, int(seconds / soft_secs   * 100))
    return {
        "seconds_studied":      seconds,
        "target_seconds":       target_secs,
        "soft_limit":           SOFT_LIMIT_SECONDS,    # kept for compatibility
        "hard_limit":           HARD_LIMIT_SECONDS,
        "target_daily_minutes": user.target_daily_minutes or 20,
        "strict_mode":          bool(user.strict_mode),
        "pct_soft":             pct_soft,
        "pct_hard":             pct_target,            # rename alias kept for templates
        "pct_target":           pct_target,
        "over_soft":            seconds >= soft_secs,
        "over_hard":            seconds >= target_secs,
        "over_target":          seconds >= target_secs,
        "minutes_studied":      round(seconds / 60, 1),
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


# ─── Zen Mode: Word Discovery ─────────────────────────────────────────────────

# Vocab list: (id, japanese, romaji, meaning_it, kana_set)
# kana_set = frozenset of individual kana characters that compose the word.
# Only hiragana words for now; katakana words added once unlocked.
# Meanings in Italian.
import json
import os

ZEN_VOCAB_PATH = os.path.join(os.path.dirname(__file__), "data", "zen_vocab.json")
try:
    with open(ZEN_VOCAB_PATH, "r", encoding="utf-8") as f:
        ZEN_VOCAB = json.load(f)
    for w in ZEN_VOCAB:
        w["k"] = set(w["k"])
except FileNotFoundError:
    ZEN_VOCAB = []


def get_user_learned_kana(db: Session, user: User) -> frozenset[str]:
    """Return frozenset of kana characters (front) the user has learned (srs_stage>=1)."""
    rows = (
        db.query(Card.front)
        .join(UserCard, Card.id == UserCard.card_id)
        .filter(
            UserCard.user_id == user.id,
            UserCard.srs_stage >= 1,
            Card.phase.in_(["hiragana", "katakana"]),
        )
        .all()
    )
    return frozenset(r[0] for r in rows)


def get_zen_words(db: Session, user: User, exclude_id: Optional[int] = None) -> list[dict]:
    """
    Return vocab words whose kana are ALL in the user's learned set.
    Optionally exclude a word id (to avoid showing the same word twice).
    Words are randomised.
    """
    import random
    from app.models import ZenWordProgress
    learned = get_user_learned_kana(db, user)
    if not learned:
        return []

    progress_records = db.query(ZenWordProgress).filter(ZenWordProgress.user_id == user.id).all()
    progress_map = {p.word_id: p for p in progress_records}

    available = []
    for w in ZEN_VOCAB:
        if not w["k"].issubset(learned) or w["id"] == exclude_id:
            continue
            
        p = progress_map.get(w["id"])
        if p:
            import json
            try:
                arr = json.loads(p.step1_progress)
                step1 = sum(arr) if arr else 0
            except:
                step1 = 0
            step2 = p.step2_correct_count
        else:
            step1 = 0
            step2 = 0
        
        if step2 >= 10:
            if random.random() < 0.9:
                continue
            step = 2
        elif step1 >= 5:
            step = 2
        else:
            step = 1
            
        word_data = dict(w)
        word_data["step"] = step
        word_data["_step1_count"] = step1
        
        if step == 2:
            correct_chars = list(word_data["j"])
            distractors = list(learned)
            random.shuffle(distractors)
            
            symbols = list(correct_chars)
            while len(symbols) < 10:
                if distractors:
                    symbols.append(distractors.pop())
                else:
                    symbols.append(random.choice(HIRAGANA_DATA)[0])
            
            random.shuffle(symbols)
            word_data["symbols"] = symbols
            
        available.append(word_data)

    random.shuffle(available)
    # Give priority to step 1 words, especially those with 0 progress
    available.sort(key=lambda x: (x["step"], x["_step1_count"]))
    return available

def record_zen_word_success(db: Session, user: User, word_id: int, step: int, match_idx: int = -1, total_variants: int = 1):
    from app.models import ZenWordProgress
    from datetime import datetime
    import json
    p = db.query(ZenWordProgress).filter(ZenWordProgress.user_id == user.id, ZenWordProgress.word_id == word_id).first()
    if not p:
        p = ZenWordProgress(user_id=user.id, word_id=word_id, step1_progress="[]", step2_correct_count=0)
        db.add(p)
    
    if step == 1:
        try:
            arr = json.loads(p.step1_progress)
        except:
            arr = []
        if len(arr) != total_variants:
            arr = [0] * total_variants
        if 0 <= match_idx < total_variants:
            arr[match_idx] += 1
        p.step1_progress = json.dumps(arr)
    elif step == 2:
        p.step2_correct_count += 1
    
    p.last_reviewed = datetime.now()
    db.commit()


def get_zen_word_by_id(word_id: int) -> Optional[dict]:
    """Look up a single vocab word from the in-memory list."""
    for w in ZEN_VOCAB:
        if w["id"] == word_id:
            return w
    return None

def enable_fast_lane(db: Session, user: User, phase: str, max_group_index: int) -> None:
    """Enables fast lane for cards up to the specified group index in a given phase."""
    groups = HIRAGANA_GROUP_ORDER if phase == "hiragana" else KATAKANA_GROUP_ORDER
    allowed_groups = groups[:max_group_index + 1]
    
    ucs = (
        db.query(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .filter(UserCard.user_id == user.id, Card.phase == phase, Card.group_name.in_(allowed_groups))
        .all()
    )
    for uc in ucs:
        if uc.srs_stage == 0:
            uc.fast_lane = True
    db.commit()

def generate_placement_quiz(phase: str, num_questions: int = 5) -> list[dict]:
    import random
    data = HIRAGANA_DATA if phase == "hiragana" else KATAKANA_DATA
    if not data:
        return []
    
    questions = random.sample(data, min(num_questions, len(data)))
    quiz = []
    all_romaji = list(set([item[2] for item in data]))
    
    for i, item in enumerate(questions):
        correct = item[2]
        wrong_options = random.sample([r for r in all_romaji if r != correct], 3)
        options = [correct] + wrong_options
        random.shuffle(options)
        quiz.append({
            "id": i,
            "char": item[0],
            "answer": correct,
            "options": options
        })
    return quiz

