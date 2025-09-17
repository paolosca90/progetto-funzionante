# Sistema di Trading AI con OANDA - Documentazione Completa

## Panoramica del Progetto

Questo è un sistema completo di trading automatizzato che utilizza l'intelligenza artificiale per generare segnali di trading su coppie di valute forex. Il sistema si basa su:

- **OANDA API**: Per dati di mercato in tempo reale e storici
- **Google Gemini AI**: Per analisi di mercato avanzate
- **FastAPI**: Backend web ad alte prestazioni
- **PostgreSQL**: Database per archiviazione dati
- **Railway**: Piattaforma cloud per deployment

## Architettura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend Web  │────│   FastAPI App   │────│   PostgreSQL    │
│   (HTML/CSS/JS) │    │   (main.py)     │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OANDA API     │
                       │   + Gemini AI   │
                       └─────────────────┘
```

## Componenti Principali

### 1. `main.py` - Applicazione FastAPI Principale
**Funzione**: Server web principale che gestisce tutte le API e l'interfaccia utente.

**Caratteristiche principali**:
- **Autenticazione JWT**: Sistema sicuro di login/logout
- **Gestione utenti**: Registrazione, conferma email, gestione profili
- **API REST**: Endpoint per generazione segnali e gestione dati
- **Interface web**: Servizio delle pagine HTML con templating Jinja2
- **CORS**: Configurazione per accesso web cross-origin

**Endpoint chiave**:
- `POST /admin/generate-signals`: Genera segnali trading (admin only)
- `GET /api/signals/latest`: Ottiene gli ultimi segnali per dashboard
- `GET /health`: Controllo salute sistema
- `POST /login`, `/register`: Autenticazione utenti

### 2. `oanda_signal_engine.py` - Motore di Segnali AI
**Funzione**: Cuore del sistema per la generazione di segnali di trading intelligenti.

**Algoritmo di generazione**:
1. **Recupero dati storici** da OANDA (candlestick ultimi 500 periodi)
2. **Analisi tecnica** con indicatori:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Bande di Bollinger
   - ATR (Average True Range)
   - EMA (Exponential Moving Averages)
3. **Analisi AI** tramite Google Gemini per contesto di mercato
4. **Calcolo confidenza** con soglia del 60%:
   - ≥60%: Segnale BUY/SELL
   - <60%: Segnale HOLD con messaggio "Non conviene operare ora"
5. **Risk management** automatico con stop-loss e take-profit

**Caratteristiche avanzate**:
- Analisi multi-timeframe (H1, H4, D1)
- Riconoscimento sessioni di mercato
- Gestione volatilità dinamica
- Fallback robusto per problemi di connessione

### 3. `oanda_api_integration.py` - Client API OANDA
**Funzione**: Interface diretta con i server OANDA per dati di mercato.

**Funzionalità**:
- Autenticazione sicura con API key
- Recupero prezzi in tempo reale
- Download dati storici (candlestick)
- Gestione errori e retry automatici
- Conversione formati simboli (EURUSD → EUR_USD)

### 4. `models.py` - Modelli Database
**Funzione**: Definisce la struttura dei dati con SQLAlchemy ORM.

**Modelli principali**:
- **User**: Utenti del sistema con autenticazione
- **Signal**: Segnali di trading generati
- **OANDAConnection**: Configurazioni connessioni OANDA
- **UserSignalAccess**: Controllo accessi ai segnali

**Campi segnale importanti**:
- `signal_type`: BUY/SELL/HOLD
- `confidence_score`: Percentuale fiducia (0-1)
- `technical_score`: Punteggio analisi tecnica
- `ai_analysis`: Spiegazione AI in italiano
- `stop_loss`, `take_profit`: Livelli risk management

### 5. `jwt_auth.py` - Sistema Autenticazione
**Funzione**: Gestisce autenticazione sicura con JSON Web Tokens.

**Caratteristiche**:
- Generazione e validazione JWT
- Hash password con bcrypt
- Middleware protezione endpoint
- Gestione scadenza token

### 6. `email_utils.py` - Gestione Email
**Funzione**: Invia email per conferme registrazione e notifiche.

**Configurazione**:
- SMTP server configurabile
- Template HTML per email
- Gestione errori invio

### 7. File Template HTML

#### `dashboard.html`
**Funzione**: Interfaccia principale per visualizzare segnali.
**Caratteristiche**:
- Design a tema Matrix (verde/nero)
- Visualizzazione real-time segnali
- Indicatori visivi per BUY/SELL/HOLD
- Percentuali di confidenza prominenti

#### `login.html` e `register.html`
**Funzione**: Pagine autenticazione utente.
**Design**: Coerente con tema Matrix

#### `signals.html`
**Funzione**: Pagina dedicata visualizzazione dettagliata segnali.

### 8. `styles.css` - Stilizzazione
**Funzione**: Stili CSS per il tema Matrix.

**Caratteristiche visuali**:
- Colori Matrix: verde lime (#00ff00) su nero
- Effetti glow e ombreggiature
- Animazioni per segnali
- Design responsive

## Flusso di Generazione Segnali

```
1. Richiesta API → /admin/generate-signals
                   ↓
2. OANDASignalEngine.generate_signals()
                   ↓
3. Per ogni coppia valuta:
   - Recupera dati storici OANDA
   - Calcola indicatori tecnici
   - Analizza con Gemini AI
   - Calcola score confidenza
                   ↓
4. Soglia 60%:
   - ≥60%: BUY/SELL con percentuale
   - <60%: HOLD "Non conviene operare"
                   ↓
5. Salva in database PostgreSQL
                   ↓
6. Ritorna JSON con segnali generati
```

## Configurazione Ambiente

### Variabili Richieste:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Autenticazione
JWT_SECRET_KEY=your_secret_key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# OANDA Trading
OANDA_API_KEY=your_oanda_api_key
OANDA_ACCOUNT_ID=your_oanda_account_id
OANDA_ENVIRONMENT=practice  # o "live"

# AI Analysis
GEMINI_API_KEY=your_gemini_api_key
```

## Deployment su Railway

### File Importanti:
- `requirements.txt`: Dipendenze Python
- `Procfile`: Configurazione Railway per avvio app
- `railway.json`: Configurazioni specifiche Railway

### Comandi Deployment:
```bash
# Installazione locale
pip install -r requirements.txt

# Avvio locale
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Deploy Railway
git push origin main  # Auto-deploy su Railway
```

## Caratteristiche di Sicurezza

1. **Autenticazione JWT**: Token sicuri con scadenza
2. **Hash Password**: bcrypt per protezione credenziali
3. **Validazione Input**: Sanitizzazione dati API
4. **CORS Configurato**: Accesso controllato da domini autorizzati
5. **Rate Limiting**: Protezione contro abusi API
6. **API Key Management**: Gestione sicura chiavi OANDA/Gemini

## Monitoraggio e Salute Sistema

### Endpoint Health Check:
- `GET /health`: Verifica stato database e connessioni
- Ritorna status 200 se tutto funziona
- Utilizzato da Railway per monitoring

### Logging:
- Log strutturati per debugging
- Tracciamento errori API OANDA
- Monitor performance generazione segnali

## Algoritmo Soglia 60%

Il sistema implementa una logica rigorosa per garantire qualità segnali:

```python
# Se confidenza < 60%, forza HOLD
if normalized_score < 0.60:
    signal_type = "HOLD"
    message = "Non conviene operare ora su questo asset"
    reasoning = "Probabilità insufficiente per operare (<60%)"
else:
    signal_type = "BUY" o "SELL"  # Basato su analisi tecnica
    message = f"Confidenza: {confidence * 100:.1f}%"
```

## Coppie Valute Supportate

Il sistema è ottimizzato per le principali coppie forex:
- EUR_USD (Euro/Dollaro USA)
- GBP_USD (Sterlina/Dollaro USA)  
- USD_JPY (Dollaro USA/Yen Giapponese)
- AUD_USD (Dollaro Australiano/USA)
- USD_CAD (Dollaro USA/Canadese)
- NZD_USD (Dollaro Neozelandese/USA)
- EUR_GBP (Euro/Sterlina)

## Test e Validazione

### File di Test:
- `test_60_percent_threshold.py`: Verifica soglia 60%
- `test_fallback.py`: Test meccanismo fallback

### Comando Test:
```bash
cd frontend
python test_60_percent_threshold.py
```

## Manutenzione e Aggiornamenti

### Pulizia Database:
```bash
python reset_database.py  # Reset tabelle sviluppo
```

### Aggiornamento Dipendenze:
```bash
pip freeze > requirements.txt  # Aggiorna requirements
```

### Backup Database:
Configurare backup automatici su Railway per protezione dati produzione.

---

**Autore**: Sistema AI Trading OANDA  
**Versione**: 2.0 (Post-cleanup FXCM/VPS)  
**Data**: 2025-09-10  
**Piattaforma**: Railway Cloud + OANDA API