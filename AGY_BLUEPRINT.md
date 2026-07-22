# AGY Blueprint: App Gamificata per l'Apprendimento del Giapponese

## 1. Principi di Gamification (NON PUNITIVA)
* Nessun meccanismo punitivo (niente vite o cuori che si consumano).
* Gestione flessibile della streak tramite "Giorni Attivi Mensili" e "Punti Riposo".
* Limite massimo di studio guidato: **15-20 minuti al giorno**.
  * A 15 min: avviso soft (continua pure o vai in Zen Mode).
  * A 20 min: redirect automatico in Zen Mode (hard limit).
* Nella sezione `/learn`: al raggiungimento del limite, si completa la carta corrente, si congratula l'utente e si reindirizza alla Zen Mode.
* Algoritmo SRS con **Capping del backlog** a max 25 carte/giorno (review) e max 5 carte/giorno (learn).
* Il timer si **ferma automaticamente** quando la finestra perde il focus (blur / visibilitychange).

## 2. Percorso Didattico Progressivo

### Modalità LEARN (`/learn`)
* Introduce max **5 carte NUOVE** al giorno.
* Sequenza guidata per gruppo:
  1. **Fase studio** (4 sec): mostra il carattere + lettura + romanji + **nota mnemonica visiva**.
  2. **Mini-quiz**: l'utente scrive la romanizzazione → verifica immediata.
  3. Se corretto: avanza automaticamente (0.8s).
  4. Se sbagliato: mostra risposta corretta → bottone "Avanti" → carta comunque introdotta.
* La carta passa a `srs_stage = 1` e `is_new = False` dopo il mini-quiz.
* La carta entra nella coda SRS con `due_date = domani`.

### Modalità REVIEW (`/review`)
* Solo carte con `srs_stage >= 1` e `due_date <= oggi`.
* L'utente scrive la risposta → SM-2 aggiorna ease_factor, interval, due_date.

### Unlock progressivo dei gruppi
```
Hiragana gruppi (sequenziale, in ordine):
  vowels → ka → sa → ta → na → ha → ma → ya → ra → wa → n

Katakana: sbloccato quando Hiragana >= 80% completato.
Vocaboli (fase 2): sbloccato dopo 100% Katakana.
```

### Fasi Didattiche Complete
1. **Fase 1**: Hiragana & Katakana (46+46 sillabe con riconoscimento visivo e note mnemoniche).
2. **Fase 2**: Vocaboli ad Alta Frequenza (300-500 parole) + Radicali dei Kanji *(in sviluppo)*.
3. **Fase 3**: Frasi Brevi (struttura SOV), Ascolto (3-5 sec) e Grammatica base *(in sviluppo)*.
4. **Fase 4**: Lettura Guidata con Furigana *(in sviluppo)*.

## 3. Stack Tecnologico (No Docker)
* **Backend**: Python 3.11+ con FastAPI + Uvicorn
* **Frontend**: Jinja2 Templates + HTMX + CSS personalizzato (dark mode, glassmorphism)
* **Database**: SQLite con SQLAlchemy ORM
* **Auth**: Google OAuth2 (Authlib)
* **Manager**: Systemd (`japanese-app.service`) su `127.0.0.1:8015`
* **Reverse Proxy**: Nginx + Let's Encrypt (nihon.minkyos.com:443)

## 4. Struttura del Progetto
```
japanese-app/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI: /, /dashboard, /learn, /learn/card,
│   │                        #          /review/start, /review, /zen, /api/*
│   ├── auth.py              # Google OAuth2 (Authlib)
│   ├── database.py          # SQLite connection
│   ├── models.py            # User, Card (+ group_name), UserCard (+ srs_stage),
│   │                        # ReviewLog, DailyStudy
│   ├── srs.py               # SM-2, Learn logic, group progress, seed data
│   ├── templates/
│   │   ├── base.html            # Nav (Impara/Ripassa/Zen) + timer JS (focus-aware)
│   │   ├── login.html           # Landing con sakura petals
│   │   ├── dashboard.html       # Stats + griglia gruppi con barre progresso
│   │   ├── learn_home.html      # Learn landing: gruppo corrente + CTA sessione
│   │   ├── learn_card.html      # Singola carta: fase studio → mini-quiz
│   │   ├── learn_done.html      # Fine sessione learn / limite raggiunto
│   │   ├── review_start.html    # Tutorial pre-ripasso
│   │   ├── review.html          # Carta SRS: input testuale + verifica
│   │   ├── review_done.html     # Fine ripasso
│   │   └── zen_mode.html        # Zen Mode: galleria carte + respirazione
│   └── static/
│       └── css/style.css
├── venv/
├── japanese_app.db
├── requirements.txt
├── .env / .env.example
└── systemd/
    ├── japanese-app.service
    └── nginx-japanese-app.conf
```

## 5. Schema DB (rilevante)

| Tabella | Colonne chiave |
|---------|---------------|
| `users` | `google_id`, `active_days_this_month`, `rest_points`, `last_active_date` |
| `cards` | `phase`, `group_name`, `front`, `back`, `romanji`, `notes` (mnemonic) |
| `user_cards` | `srs_stage` (0=unseen, 1=learned, 2+=SRS), `is_new`, `interval`, `ease_factor`, `due_date` |
| `daily_studies` | `study_date`, `seconds_studied` |
| `review_logs` | `quality`, `time_spent_ms` |

## 6. Logica SRS dettagliata

```python
# Costanti
NEW_LEARN_PER_DAY  = 5     # carte nuove/giorno via Learn
DAILY_CARD_CAP     = 25    # carte review/giorno (backlog capped)
SOFT_LIMIT_SECONDS = 900   # 15 min → avviso
HARD_LIMIT_SECONDS = 1200  # 20 min → redirect Zen
UNLOCK_THRESHOLD   = 0.80  # 80% Hiragana → sblocca Katakana

# srs_stage lifecycle
# 0 → (Learn mini-quiz) → 1 → (first SRS review) → 2 → SM-2 cycle...
```

## 7. Deployment

* **Servizio**: `sudo systemctl status japanese-app`
* **URL produzione**: https://nihon.minkyos.com
* **Logs**: `sudo journalctl -u japanese-app -f`
* **Riavvio**: `sudo systemctl restart japanese-app`
* **SSL**: Let's Encrypt, scade 2026-10-20, rinnovo automatico via Certbot
