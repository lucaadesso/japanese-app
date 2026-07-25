# 日本語 — Japanese Learning App

Un'app gamificata per imparare il giapponese (Hiragana e Katakana) con SRS adattivo, costruita con FastAPI + HTMX.

## 1. Principi di Gamification (NON PUNITIVA)
* Nessun meccanismo punitivo (niente vite o cuori che si consumano).
* Gestione flessibile della streak tramite "Giorni Attivi Mensili" e "Punti Riposo".
* **Limiti di studio giornaliero personalizzabili** (tramite la pagina Impostazioni):
  * **Minuti al giorno** (default: 20 min): Al raggiungimento del limite soft si riceve un avviso. Al raggiungimento del limite hard si viene reindirizzati alla Zen Mode.
  * **Nuove carte al giorno** (default: 5 carte): Capping del backlog per l'introduzione di nuovi concetti nella sezione `/learn`.
* Capping del backlog anche per i ripassi (review): max 25 carte al giorno per evitare sovraccarico.
* Nella sezione `/learn`: al raggiungimento del limite di nuove carte introdotte o del tempo giornaliero, la sessione si ferma per non sovraccaricare la memoria.
* Il timer si **ferma automaticamente** quando la finestra perde il focus (blur / visibilitychange).

## 2. Percorso Didattico Progressivo

### Modalità LEARN (`/learn`)
* Introduce max **X carte NUOVE** al giorno (configurabile).
* **Chunking (Blocchi da 5)**: L'apprendimento è suddiviso in mini-blocchi. Dopo ogni 5 carte nuove studiate, parte automaticamente un mini-ripasso per fissare i concetti.
* Sequenza guidata per carta:
  1. **Fase studio** (4 sec): mostra il carattere + lettura + romanji + **nota mnemonica visiva**.
  2. **Mini-quiz**: l'utente scrive la romanizzazione → verifica immediata.
  3. Se corretto: avanza automaticamente (0.8s).
  4. Se sbagliato: mostra risposta corretta → bottone "Avanti" → carta comunque introdotta.
* La carta passa a `srs_stage = 1` ed è messa in scadenza *immediata* per forzare la comparsa nel mini-ripasso.

### Modalità REVIEW (`/review`)
* Solo carte con `srs_stage >= 1` e `due_date <= oggi`.
* L'utente scrive la risposta → SM-2 aggiorna ease_factor, interval, due_date.

### Unlock progressivo dei gruppi
```
Hiragana Base (sequenziale):
  vowels → ka → sa → ta → na → ha → ma → ya → ra → wa → n

Hiragana 1.5 (Regole Avanzate):
  dakuten (゛) → handakuten (゜) → yoon (ゃゅょ) → sokuon (っ)

Katakana: sbloccato quando Hiragana Base + 1.5 >= 80% completato.
```

### Zen Mode (`/zen`)
* Gioco di composizione vocabolario focalizzato sulla lettura.
* Propone 146 vocaboli (JLPT N5) letti da `app/data/zen_vocab.json`.
* **Step 1**: Inserimento del romaji o traduzione con controllo bilanciato per evitare di usare sempre lo stesso significato. Se si forza la rotazione, l'app suggerisce la variante mancante.
* **Step 2**: Costruzione della parola tappando i kana corretti in mezzo a distrattori.
* Le parole non vengono mostrate finché *tutti* i kana che le compongono non sono stati imparati.
* L'ordine dà priorità alle parole mai viste o che contengono caratteri appresi di recente.

### Audio (TTS)
* Riproduzione audio integrata basata su `Web Speech API`. 
* Presenta un delay intenzionale di 250ms per impedire il troncamento della prima sillaba su dispositivi mobile (come iOS Safari).

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
