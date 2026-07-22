"""
main.py – FastAPI application entry point.

Routes:
  GET  /               → landing / login page
  GET  /dashboard      → user dashboard with group progress
  GET  /learn          → Learn Mode: current group intro + session start
  GET  /learn/card     → present one new card (study phase)
  POST /learn/card/{uc_id} → submit learn quiz, advance
  GET  /review/start   → tutorial + start screen
  GET  /review         → SRS review session
  POST /review/{id}    → submit review answer
  GET  /zen            → Zen Mode
  POST /api/time       → add study seconds
  GET  /api/status     → study-time JSON
"""
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.auth import get_current_user, require_user, router as auth_router, _LoginRequired
from app.database import Base, engine, get_db
from app.models import Card, ReviewLog, UserCard
from app import srs

# ─── App & Middleware ─────────────────────────────────────────────────────────

app = FastAPI(title="Japanese Learning App", version="1.1.0")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-please-use-a-long-random-string")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=7 * 24 * 3600)

# ─── Static & Templates ───────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="/home/ubuntu/japanese-app/app/static"), name="static")
templates = Jinja2Templates(directory="/home/ubuntu/japanese-app/app/templates")

# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(auth_router)


@app.exception_handler(_LoginRequired)
async def login_required_handler(request: Request, exc: _LoginRequired):
    return RedirectResponse(url="/")


# ─── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        srs.seed_cards(db)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Landing & Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    srs.update_active_days(db, user)
    srs.ensure_user_cards(db, user)
    ts = srs.time_status(db, user)

    if ts["over_hard"]:
        return RedirectResponse(url="/zen")

    due_count  = len(srs.get_due_cards(db, user))
    progress   = srs.get_dashboard_progress(db, user)
    learn_info = srs.get_learn_cards_for_session(db, user)
    new_today  = srs.count_new_learned_today(db, user)

    return templates.TemplateResponse("dashboard.html", {
        "request":    request,
        "user":       user,
        "ts":         ts,
        "due_count":  due_count,
        "progress":   progress,
        "learn_count": len(learn_info),
        "new_today":  new_today,
        "max_new":    srs.NEW_LEARN_PER_DAY,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Learn Mode
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/learn", response_class=HTMLResponse)
async def learn_home(request: Request, db: Session = Depends(get_db)):
    """Learn dashboard: shows current group and starts session."""
    user = require_user(request, db)
    srs.ensure_user_cards(db, user)
    ts = srs.time_status(db, user)

    if ts["over_hard"]:
        return RedirectResponse(url="/zen")

    current_group = srs.get_current_learn_group(db, user)
    new_today     = srs.count_new_learned_today(db, user)
    learn_cards   = srs.get_learn_cards_for_session(db, user)
    progress      = srs.get_dashboard_progress(db, user)

    return templates.TemplateResponse("learn_home.html", {
        "request":       request,
        "user":          user,
        "ts":            ts,
        "current_group": current_group,
        "learn_cards":   learn_cards,
        "new_today":     new_today,
        "max_new":       srs.NEW_LEARN_PER_DAY,
        "progress":      progress,
    })


@app.get("/learn/card", response_class=HTMLResponse)
async def learn_card(request: Request, db: Session = Depends(get_db)):
    """Show the next unseen card in study (presentation) phase."""
    user = require_user(request, db)
    ts   = srs.time_status(db, user)

    if ts["over_hard"]:
        return RedirectResponse(url="/zen")

    session_cards = srs.get_learn_cards_for_session(db, user)
    if not session_cards:
        # All new cards for today done
        return templates.TemplateResponse("learn_done.html", {
            "request": request, "user": user, "ts": ts,
        })

    uc   = session_cards[0]
    card = db.query(Card).filter(Card.id == uc.card_id).first()
    remaining = len(session_cards)

    return templates.TemplateResponse("learn_card.html", {
        "request":   request,
        "user":      user,
        "uc":        uc,
        "card":      card,
        "remaining": remaining,
        "ts":        ts,
    })


@app.post("/learn/card/{uc_id}", response_class=HTMLResponse)
async def submit_learn(uc_id: int, request: Request, db: Session = Depends(get_db)):
    """Process the Learn quiz answer and mark card as introduced."""
    user = require_user(request, db)
    form = await request.form()
    time_ms = int(form.get("time_ms", 0))

    uc = db.query(UserCard).filter(
        UserCard.id == uc_id, UserCard.user_id == user.id
    ).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Card not found")

    # Mark as learned (srs_stage=1)
    srs.mark_card_learned(db, uc)

    # Accrue study time
    seconds = max(1, time_ms // 1000)
    srs.add_study_seconds(db, user, seconds)
    db.commit()

    ts = srs.time_status(db, user)

    # Check if over hard limit after completing this card
    remaining = srs.get_learn_cards_for_session(db, user)
    if ts["over_hard"] or not remaining:
        congratulate = not remaining
        return templates.TemplateResponse("learn_done.html", {
            "request":     request,
            "user":        user,
            "ts":          ts,
            "over_limit":  ts["over_hard"],
            "congratulate": congratulate,
        })

    return RedirectResponse(url="/learn/card", status_code=303)


# ═══════════════════════════════════════════════════════════════════════════════
# Review Mode
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/review/start", response_class=HTMLResponse)
async def review_start(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    srs.ensure_user_cards(db, user)
    ts = srs.time_status(db, user)
    if ts["over_hard"]:
        return RedirectResponse(url="/zen")
    due_count = len(srs.get_due_cards(db, user))
    if due_count == 0:
        return templates.TemplateResponse("review_done.html", {
            "request": request, "user": user, "ts": ts,
        })
    return templates.TemplateResponse("review_start.html", {
        "request": request, "user": user, "due_count": due_count, "ts": ts,
    })


@app.get("/review", response_class=HTMLResponse)
async def review_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    ts   = srs.time_status(db, user)

    if ts["over_hard"]:
        return RedirectResponse(url="/zen")

    due_cards = srs.get_due_cards(db, user)
    if not due_cards:
        return templates.TemplateResponse("review_done.html", {
            "request": request, "user": user, "ts": ts,
        })

    first_uc  = due_cards[0]
    card      = db.query(Card).filter(Card.id == first_uc.card_id).first()
    remaining = len(due_cards)

    return templates.TemplateResponse("review.html", {
        "request":   request,
        "user":      user,
        "uc":        first_uc,
        "card":      card,
        "remaining": remaining,
        "ts":        ts,
        "over_soft": ts["over_soft"],
    })


@app.post("/review/{uc_id}", response_class=HTMLResponse)
async def submit_review(uc_id: int, request: Request, db: Session = Depends(get_db)):
    user    = require_user(request, db)
    form    = await request.form()
    quality = int(form.get("quality", 3))
    time_ms = int(form.get("time_ms", 0))

    uc = db.query(UserCard).filter(
        UserCard.id == uc_id, UserCard.user_id == user.id
    ).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Card not found")

    srs.sm2_update(uc, quality)
    db.commit()

    log = ReviewLog(user_id=user.id, card_id=uc.card_id, quality=quality, time_spent_ms=time_ms)
    db.add(log)

    seconds = max(1, time_ms // 1000)
    srs.add_study_seconds(db, user, seconds)
    db.commit()

    ts = srs.time_status(db, user)
    if ts["over_hard"]:
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Redirect"] = "/zen"
        return response

    return RedirectResponse(url="/review", status_code=303)


# ═══════════════════════════════════════════════════════════════════════════════
# Zen Mode
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/zen", response_class=HTMLResponse)
async def zen_mode(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    ts   = srs.time_status(db, user)
    learned_ucs = (
        db.query(UserCard)
        .filter(UserCard.user_id == user.id, UserCard.srs_stage >= 1)
        .order_by(UserCard.last_reviewed)
        .limit(20)
        .all()
    )
    cards = [db.query(Card).filter(Card.id == uc.card_id).first() for uc in learned_ucs]
    return templates.TemplateResponse("zen_mode.html", {
        "request": request, "user": user, "ts": ts,
        "cards": [c for c in cards if c],
    })


# ═══════════════════════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/time", response_class=JSONResponse)
async def add_time(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    body = await request.json()
    seconds = int(body.get("seconds", 0))
    if seconds > 0:
        srs.add_study_seconds(db, user, seconds)
    return srs.time_status(db, user)


@app.get("/api/status", response_class=JSONResponse)
async def get_status(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    return srs.time_status(db, user)
