# 🚀 AI Trading System - Railway Frontend

Sistema completo di trading automatizzato con intelligenza artificiale per analisi di mercato e generazione segnali professionali.

## 📋 Panoramica Architettura

```
┌─────────────────────────┐     ┌─────────────────────────┐
│    RAILWAY FRONTEND     │     │      VPS WINDOWS        │
│                         │     │                         │
│  • Web Dashboard        │◄────┤  • MetaTrader 5         │
│  • User Management      │     │  • AI Signal Engine     │
│  • Signal Display       │     │  • MT5 Bridge           │  
│  • FastAPI Backend      │     │  • VPS Main Server      │
│  • Database             │     │                         │
└─────────────────────────┘     └─────────────────────────┘
```

## 🌐 Railway Frontend (Questo Progetto)

### 🎯 Componenti Principali

- **main.py** - Server FastAPI principale
- **jwt_auth.py** - Autenticazione JWT
- **email_utils.py** - Gestione email
- **HTML Templates** - Interface utente web
- **static/** - CSS, JS, immagini

### ⚙️ Configurazione Railway

```env
# Database
DATABASE_URL=postgresql://...

# JWT & Security
JWT_SECRET_KEY=your-secret-key
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# VPS Integration
VPS_API_KEY=your-secure-vps-key
GEMINI_API_KEY=your-gemini-api-key
```

### 🚀 Deploy su Railway

1. **Connetti repository** GitHub a Railway
2. **Configura variabili** ambiente nel dashboard
3. **Deploy automatico** ad ogni push
4. **URL automatico** generato da Railway

### 📱 Features Frontend

- ✅ **Dashboard** trading completo
- ✅ **Gestione utenti** con registrazione/login
- ✅ **Visualizzazione segnali** in tempo reale
- ✅ **Statistiche** performance
- ✅ **Profilo utente** personalizzabile
- ✅ **API RESTful** per VPS communication

## 🔧 VPS Backend (Cartella Separata)

### 📁 Cartella "VPS INSTALLAZIONE"

Contiene tutto il necessario per la VPS Windows:
- Sistema completo Python
- Installer automatico
- Connessione MetaTrader 5
- AI Signal Engine
- Documentazione completa

### 🛠️ Setup VPS

1. **Carica cartella** "VPS INSTALLAZIONE" sulla VPS
2. **Esegui installer**: `quick_installer.bat`
3. **Configura .env_vps** con i tuoi dati
4. **Avvia sistema**: `python vps_auto_launcher.py`

## 🔗 Comunicazione Frontend ↔ VPS

### API Endpoints Railway

```python
# VPS Communication
POST /api/vps/heartbeat      # Riceve heartbeat da VPS
POST /api/signals/receive    # Riceve segnali trading dal VPS
GET  /api/signals/latest     # Ultimi segnali per dashboard
GET  /api/vps/status         # Stato sistemi VPS connessi

# Health & Monitoring
GET  /health                 # Health check sistema completo

# Headers richiesti per VPS endpoints:
X-VPS-API-Key: 1d2376ae63aedb38f4d13e1041fb5f0b56cc48c44a8f106194d2da23e4039736
```

### Flusso Dati

```
VPS → Analizza mercato → Genera segnali → Invia a Railway → Dashboard utente
```

## 📊 Tecnologie Utilizzate

### Frontend (Railway)
- **FastAPI** - Backend API
- **Jinja2** - Template engine
- **PostgreSQL** - Database produzione
- **JWT** - Autenticazione
- **HTML/CSS/JS** - Interface utente

### Backend (VPS)
- **Python 3.8+** - Core system
- **MetaTrader5** - Market data
- **Google Gemini AI** - Signal analysis
- **SQLAlchemy** - Database ORM
- **FastAPI** - Internal API

## 📁 Struttura Progetto

```
├── main.py                    # Server FastAPI principale
├── jwt_auth.py               # Autenticazione JWT
├── email_utils.py            # Gestione email
├── *.html                    # Templates web
├── static/                   # Assets statici
│   ├── css/                 # Stili
│   ├── js/                  # JavaScript
│   └── images/              # Immagini
├── VPS INSTALLAZIONE/        # 📁 Sistema VPS completo
│   ├── vps_auto_launcher.py # Launcher principale
│   ├── quick_installer.bat  # Installer automatico
│   ├── .env_vps             # Config VPS
│   └── ...                  # Altri file VPS
└── requirements.txt          # Dipendenze Railway
```

## 🚀 Quick Start

### Railway Frontend
```bash
# Le dipendenze vengono installate automaticamente
# Configura variabili ambiente nel dashboard Railway
# Push → Deploy automatico
```

### VPS Setup
```bash
# Sulla VPS Windows:
1. Carica cartella "VPS INSTALLAZIONE"
2. Esegui: quick_installer.bat
3. Configura: .env_vps
4. Avvia: python vps_auto_launcher.py
```

## 📈 Monitoring

- **Railway Dashboard**: Logs, metrics, deployments
- **VPS Logs**: Sistema auto-monitora e riavvia
- **Database**: PostgreSQL Railway managed
- **Uptime**: >99.5% target sia Railway che VPS

## 🔒 Sicurezza

- JWT authentication con refresh tokens
- API key validation VPS ↔ Railway
- Password hashing bcrypt
- Environment variables per secrets
- HTTPS automatic su Railway

## 📞 Supporto

- **Frontend issues**: Controllare Railway logs
- **VPS issues**: Documentazione in "VPS INSTALLAZIONE/"
- **Integration**: Verificare API keys matching

---

**🤖 Sistema di trading AI professionale pronto per produzione! 📈**

*Frontend Railway + VPS Windows = Trading automatizzato completo*