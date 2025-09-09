# 🚀 VPS AI Trading System - Guida Installazione

## 📋 Panoramica

Questo sistema VPS si collega al frontend Railway per fornire segnali di trading AI in tempo reale tramite MetaTrader 5.

### 🔧 Componenti Principali

- **vps_auto_launcher.py** - Launcher principale con interfaccia utente
- **vps_main_server.py** - Server principale che comunica con Railway
- **signal_engine.py** - Motore AI per generazione segnali
- **mt5_bridge_vps/main_bridge.py** - Bridge per connessione MT5
- **vps_installer.bat** - Installer automatico Windows

## 🔄 Architettura Sistema

```
VPS Windows                          Railway Frontend
┌─────────────────┐                 ┌──────────────────┐
│ MetaTrader 5    │                 │                  │
│ ↓               │                 │  Web Dashboard   │
│ MT5 Bridge      │◄───────────────►│                  │
│ (Port 8000)     │                 │  User Interface  │
│ ↓               │                 │                  │
│ Signal Engine   │                 │  Signal Display  │
│ (AI Analysis)   │                 │                  │
│ ↓               │                 │  Trading Panel   │
│ VPS Main Server │─────────────────►│                  │
│ (Port 8001)     │   HTTP/HTTPS    │  (Railway App)   │
└─────────────────┘                 └──────────────────┘
```

## 🛠️ Installazione Rapida

### 1. Esegui Installer Automatico
```batch
# Doppio click su:
vps_installer.bat
```

L'installer automaticamente:
- ✅ Verifica Python e MT5
- ✅ Installa dipendenze
- ✅ Configura ambiente
- ✅ Crea shortcuts desktop
- ✅ Testa connessioni

### 2. Configurazione Manuale

Se preferisci installazione manuale:

```bash
# 1. Installa dipendenze
pip install -r requirements_vps.txt

# 2. Configura .env_vps
copy .env_vps.example .env_vps
# Modifica con i tuoi dati

# 3. Testa installazione
python vps_auto_launcher.py
```

## ⚙️ Configurazione .env_vps

```env
# Connessione MetaTrader 5
MT5_BROKER_SERVER=ICMarkets-Live
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_BRIDGE_PORT=8000

# Connessione Railway Frontend
RAILWAY_FRONTEND_URL=https://your-app-name.railway.app
VPS_API_KEY=your-secure-vps-key

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Database e Logging
DATABASE_VPS_URL=sqlite:///vps_trading.db
LOG_LEVEL=INFO

# Configurazioni Trading
MAX_SIGNALS_PER_HOUR=5
MIN_RELIABILITY_THRESHOLD=70
VPS_SERVER_PORT=8001
```

## 🚀 Avvio del Sistema

### Modalità Interattiva (Raccomandata)
```bash
python vps_auto_launcher.py
```

Menu opzioni:
- `1` - 🚀 Avvia Sistema Completo
- `2` - 🛑 Arresta Sistema  
- `3` - 📊 Mostra Stato
- `4` - 🔄 Riavvia Servizio
- `5` - ⚙️ Configurazione
- `6` - 🔍 Test Connessione MT5

### Modalità Automatica
```bash
python vps_auto_launcher.py --auto
```

### Modalità Background
```bash
python vps_auto_launcher.py --start
```

## 📡 Endpoints API VPS

Il sistema espone API locali per monitoraggio:

### Server Principale (Port 8001)
- `GET /` - Stato sistema
- `GET /health` - Health check
- `GET /signals/latest` - Ultimi segnali
- `POST /signals/generate` - Genera segnale manuale
- `POST /system/start` - Avvia sistema
- `POST /system/stop` - Ferma sistema

### MT5 Bridge (Port 8000)  
- `GET /` - Stato bridge MT5
- `POST /bridge/login` - Login MT5
- `GET /bridge/account` - Info account
- `POST /bridge/rates` - Dati storici

## 🔍 Monitoraggio e Debug

### File di Log
```bash
# Log principale sistema
tail -f vps_launcher.log

# Log server principale  
tail -f vps_main_server.log

# Log signal engine
tail -f signal_engine.log
```

### Comandi Utili
```bash
# Verifica processi attivi
python -c "import psutil; [print(p.info) for p in psutil.process_iter(['pid', 'name', 'cmdline']) if 'vps' in str(p.info.get('cmdline', [])).lower()]"

# Test connessione MT5
python -c "import MetaTrader5 as mt5; print('OK' if mt5.initialize() else 'FAIL'); mt5.shutdown()"

# Test connessione Railway  
curl https://your-app.railway.app/health
```

## 🔧 Risoluzione Problemi

### Errore MT5 Connection
```bash
# Verifica MT5 installato
ls "C:\Program Files\MetaTrader 5\"

# Verifica credenziali in .env_vps
# Assicurati MT5 sia aperto e connesso
```

### Errore Railway Connection
```bash
# Verifica URL in .env_vps
curl -I https://your-app.railway.app

# Controlla API key VPS
grep VPS_API_KEY .env_vps
```

### Errore Dipendenze Python
```bash
# Reinstalla dipendenze
pip uninstall -y -r requirements_vps.txt
pip install -r requirements_vps.txt

# Verifica versione Python >= 3.8
python --version
```

## 📊 Prestazioni e Ottimizzazione

### Configurazioni Consigliate VPS

**Minimo:**
- CPU: 2 cores
- RAM: 4GB  
- Disco: 20GB SSD
- OS: Windows Server 2019+

**Raccomandato:**
- CPU: 4 cores
- RAM: 8GB
- Disco: 50GB NVMe SSD  
- OS: Windows Server 2022

### Ottimizzazioni
```bash
# Priorità processo alta
wmic process where name="python.exe" CALL setpriority "high priority"

# Limita uso CPU per altri processi
# Configura Task Manager -> Details -> Set Priority
```

## 🔒 Sicurezza

### Raccomandazioni
1. **Cambia VPS_API_KEY** in .env_vps
2. **Usa HTTPS** per Railway frontend  
3. **Firewall VPS** - blocca porte non necessarie
4. **Monitor accessi** - controlla log regolarmente
5. **Backup configurazioni** - salva .env_vps

### Ports Utilizzate
- `8000` - MT5 Bridge (locale)
- `8001` - VPS Main Server (locale)
- `443/80` - Connessioni HTTPS/HTTP verso Railway

## 📞 Supporto

### Problemi Comuni
1. **Sistema non parte** → Controlla log, verifica .env_vps
2. **Segnali non generati** → Verifica Gemini API key  
3. **MT5 disconnesso** → Controlla credenziali, riavvia MT5
4. **Railway unreachable** → Verifica URL e connessione internet

### File Importante da Controllare
- `vps_launcher.log` - Log principale
- `vps_main_server.log` - Log server  
- `.env_vps` - Configurazioni
- `requirements_vps.txt` - Dipendenze

---

## ✅ Checklist Pre-Produzione

- [ ] MT5 installato e configurato con account reale
- [ ] Python 3.8+ installato con PATH
- [ ] Tutte dipendenze installate senza errori
- [ ] File .env_vps configurato con dati reali
- [ ] Test connessione MT5 riuscito
- [ ] Test connessione Railway riuscito  
- [ ] Gemini API key valida e configurata
- [ ] Sistema avviato e segnali generati
- [ ] Monitoraggio attivo e log controllati
- [ ] Backup configurazioni effettuato

## 🎯 Versioni

- **v1.0** - Release iniziale
- Sistema completo VPS + Railway
- Auto-installer Windows
- Monitoraggio e logging completo
- API per integrazione frontend

---

**🤖 Sistema pronto per trading automatizzato professionale! 📈**