# 🚀 AI Trading System - Railway Frontend

Sistema completo di trading automatizzato con intelligenza artificiale per analisi di mercato e generazione segnali professionali.

## 📋 Panoramica Architettura

```
┌─────────────────────────┐
│    RAILWAY FRONTEND     │
│                         │
│  • Web Dashboard        │
│  • User Management      │
│  • Signal Display       │
│  • FastAPI Backend      │
│  • Database             │
│  • OANDA Integration    │
└─────────────────────────┘
```

## 🌐 Railway Frontend - Sistema OANDA Trading

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

# OANDA Integration
OANDA_API_KEY=your-oanda-api-key
OANDA_ACCOUNT_ID=your-account-id
OANDA_ENVIRONMENT=demo
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
- ✅ **API RESTful** per OANDA integration

## 🔗 OANDA Signal Engine

### API Endpoints Railway

```python
# OANDA Signal Generation
POST /admin/generate-signals  # Generate AI signals using OANDA
GET  /api/signals/latest      # Ultimi segnali per dashboard
GET  /api/signals/top         # Top performing signals

# Health & Monitoring
GET  /health                  # Health check sistema completo
```

### Flusso Dati

```
OANDA API → Signal Engine → Database → Dashboard utente
```

## 📊 Tecnologie Utilizzate

### Frontend (Railway)
- **FastAPI** - Backend API
- **Jinja2** - Template engine
- **PostgreSQL** - Database produzione
- **JWT** - Autenticazione
- **HTML/CSS/JS** - Interface utente

### Backend (OANDA)
- **Python 3.8+** - Core system
- **OANDA API** - Market data
- **Google Gemini AI** - Signal analysis
- **SQLAlchemy** - Database ORM
- **FastAPI** - Signal engine

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
├── oanda_signal_engine.py   # OANDA Signal Engine
├── oanda_api_integration.py # OANDA API Client
└── requirements.txt          # Dipendenze Railway
```

## 🚀 Quick Start

### Railway Frontend
```bash
# Le dipendenze vengono installate automaticamente
# Configura variabili ambiente nel dashboard Railway
# Push → Deploy automatico
```

### OANDA Setup
```bash
# Configura variabili ambiente:
OANDA_API_KEY=your-api-key
OANDA_ACCOUNT_ID=your-account-id
OANDA_ENVIRONMENT=demo  # o live
```

## 📈 Monitoring

- **Railway Dashboard**: Logs, metrics, deployments
- **OANDA Engine**: Generazione segnali automatica
- **Database**: PostgreSQL Railway managed
- **Uptime**: >99.5% target Railway

## 🔒 Sicurezza

- JWT authentication con refresh tokens
- OANDA API authentication
- Password hashing bcrypt
- Environment variables per secrets
- HTTPS automatic su Railway

## 📞 Supporto

- **Frontend issues**: Controllare Railway logs
- **OANDA issues**: Verificare API key e account
- **Integration**: Verificare API keys matching

---

**🤖 Sistema di trading AI professionale pronto per produzione! 📈**

*Frontend Railway + OANDA API = Trading automatizzato completo*
