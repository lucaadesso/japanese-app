# 日本語 — Japanese Learning App

Un'app gamificata per imparare il giapponese (Hiragana e Katakana) con SRS adattivo, costruita con FastAPI + HTMX.

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

## 3. Struttura del Progetto
```
japanese-app/
├── app/
│   ├── main.py              # FastAPI routes & app config
│   ├── auth.py              # Google OAuth2 (Authlib)
│   ├── database.py          # SQLite connection
│   ├── models.py            # User, Card (+ group_name), UserCard (+ srs_stage)
│   ├── srs.py               # SM-2, Learn logic, group progress, seed data
│   ├── templates/           # Jinja2 templates (HTMX)
│   └── static/
│       └── css/style.css
├── systemd/
│   ├── japanese-app.service      # Systemd service (porta 8015)
│   └── nginx-japanese-app.conf   # Nginx reverse proxy
├── .env                          # Variabili d'ambiente (non committare!)
├── .env.example                  # Template .env
└── requirements.txt
```

## 4. Setup Rapido

### 1. Configura `.env`
```bash
cp .env.example .env
# Modifica .env con le tue credenziali Google OAuth2 e SECRET_KEY
nano .env
```

### 2. Crea il venv (se non esiste)
```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 3. Test in locale
```bash
set -a; source .env; set +a
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8015 --reload
```

### 4. Deploy con systemd
```bash
sudo cp systemd/japanese-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable japanese-app
sudo systemctl start japanese-app
```

### 5. Nginx reverse proxy
```bash
sudo cp systemd/nginx-japanese-app.conf /etc/nginx/sites-available/japanese-app
sudo ln -s /etc/nginx/sites-available/japanese-app /etc/nginx/sites-enabled/japanese-app
sudo nginx -t && sudo systemctl reload nginx
```

### 6. SSL con Certbot
```bash
sudo certbot --nginx -d nihon.tuodominio.com
```

## 5. Google OAuth2 Setup
1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto e abilita "Google People API"
3. Crea credenziali OAuth 2.0 (Web application)
4. Aggiungi URI di reindirizzamento: `https://tuodominio.com/auth/callback`
5. Copia Client ID e Client Secret in `.env`
