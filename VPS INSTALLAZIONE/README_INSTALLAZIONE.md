# 📁 VPS INSTALLAZIONE - Cartella Completa

## 🎯 Panoramica

Questa cartella contiene tutto il necessario per installare il sistema AI Trading sulla tua VPS Windows e collegarlo al frontend Railway.

---

## 📋 Contenuto Cartella

### 📄 File Principali del Sistema

| File | Descrizione | Uso |
|------|-------------|-----|
| `vps_auto_launcher.py` | **Launcher principale** | Core del sistema con menu interattivo |
| `vps_main_server.py` | **Server principale** | Comunica con Railway frontend |
| `signal_engine.py` | **Motore AI segnali** | Genera segnali trading automatici |
| `database.py` | **Gestione database** | Salvataggio dati sistema |
| `models.py` | **Modelli dati** | Strutture dati SQLAlchemy |
| `schemas.py` | **Schema validazione** | Validazione input/output |

### 🔧 File di Configurazione

| File | Descrizione | Azione Richiesta |
|------|-------------|------------------|
| `.env_vps` | **Configurazione ambiente** | ⚠️ **MODIFICARE con i tuoi dati!** |
| `requirements_vps.txt` | **Dipendenze Python** | Installate automaticamente |
| `mt5_symbols.json` | **Simboli MT5** | Lista simboli trading |

### 🛠️ Script di Installazione

| File | Descrizione | Quando Usare |
|------|-------------|--------------|
| `quick_installer.bat` | **Installer rapido** | ✅ **RECOMMENDED** - Primo avvio |
| `vps_installer.bat` | **Installer completo** | Installazione dettagliata |
| `build_vps_installer.bat` | **Crea EXE** | Solo per creare eseguibile |
| `check_system.py` | **Diagnostica sistema** | Test e troubleshooting |

### 📚 Documentazione

| File | Descrizione | Target |
|------|-------------|--------|
| `GUIDA_COMPLETA_VPS.md` | **Guida completa passo-passo** | Utenti tecnici |
| `README_VPS.md` | **Documentazione tecnica** | Sviluppatori |
| `README_INSTALLAZIONE.md` | **Questo file** | Panoramica generale |

### 📁 Directory

| Directory | Contenuto | Descrizione |
|-----------|-----------|-------------|
| `mt5_bridge_vps/` | Bridge MetaTrader 5 | Connessione MT5 ↔ Sistema |

---

## 🚀 INSTALLAZIONE RAPIDA (5 MINUTI)

### Step 1: Carica sulla VPS
1. Connettiti alla tua VPS Windows (RDP/TeamViewer)
2. Crea cartella `C:\AITradingVPS\`
3. Carica tutti i file di questa cartella

### Step 2: Installazione Automatica
```cmd
# Esegui come Amministratore
quick_installer.bat
```

### Step 3: Configurazione
1. Si aprirà automaticamente `.env_vps`
2. Modifica con i tuoi dati:
   - **MT5_LOGIN**: Il tuo numero account MT5
   - **MT5_PASSWORD**: La tua password MT5
   - **MT5_BROKER_SERVER**: Server broker (es: ICMarkets-Live)
   - **RAILWAY_FRONTEND_URL**: URL della tua app Railway
   - **GEMINI_API_KEY**: API key Google Gemini

### Step 4: Avvio
```cmd
# Dal desktop o da linea comando
python vps_auto_launcher.py
```

---

## ⚙️ CONFIGURAZIONE DETTAGLIATA

### File .env_vps - DA MODIFICARE OBBLIGATORIAMENTE

```env
# === CONNESSIONE METATRADER 5 ===
MT5_BROKER_SERVER=ICMarkets-Live           # CAMBIA: Nome server broker
MT5_LOGIN=12345678                        # CAMBIA: Tuo account MT5
MT5_PASSWORD=your_password                # CAMBIA: Password MT5

# === CONNESSIONE RAILWAY ===
RAILWAY_FRONTEND_URL=https://your-app.railway.app  # CAMBIA: URL Railway
VPS_API_KEY=secure-key-2024               # CAMBIA: Chiave sicura

# === AI CONFIGURATION ===
GEMINI_API_KEY=your_gemini_key            # CAMBIA: API Google Gemini
```

### Come Ottenere le Chiavi:

**🔑 Gemini API Key:**
1. Vai su [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea progetto → Genera API Key
3. Copia in `GEMINI_API_KEY`

**🌐 Railway URL:**
1. Dashboard Railway → Tuo progetto
2. Tab "Deployments" → Copia URL pubblico
3. Incolla in `RAILWAY_FRONTEND_URL`

---

## 🎮 MODALITÀ DI UTILIZZO

### 1. Menu Interattivo (Raccomandato)
```cmd
python vps_auto_launcher.py
```
- Controllo completo sistema
- Monitoraggio in tempo reale
- Test e diagnostica

### 2. Modalità Automatica (Produzione)
```cmd
python vps_auto_launcher.py --auto
```
- Trading 24/7 automatico
- Auto-restart in caso errori
- Logging completo

### 3. Comandi Rapidi
```cmd
python vps_auto_launcher.py --start    # Avvia in background
python vps_auto_launcher.py --stop     # Ferma sistema
python vps_auto_launcher.py --status   # Mostra stato
```

---

## 🔍 TESTING E DIAGNOSTICA

### Test Sistema Completo
```cmd
python check_system.py
```

Output esempio:
```
✅ Python Version             OK    v3.12.0
✅ MetaTrader5               OK    Available
✅ MT5 Connection            OK    Account: 12345678
✅ Railway Frontend          OK    200 - https://app.railway.app
✅ System Resources          OK    8GB RAM, 4 cores
```

### Monitor in Tempo Reale
```cmd
# Dal menu: opzione 7 - Visualizza Log
# Oppure direttamente:
tail -f vps_main_server.log
```

---

## 🌐 INTEGRAZIONE RAILWAY

### Verifica Connessione
Il sistema invia automaticamente:
- 💚 **Heartbeat** ogni minuto
- 📊 **Segnali trading** quando generati
- 📈 **Statistiche sistema** in tempo reale

### Endpoint Railway Richiesti
```javascript
POST /api/vps/heartbeat     // Heartbeat VPS
POST /api/signals/receive   // Ricezione segnali
GET  /health               // Health check
```

---

## ⚠️ TROUBLESHOOTING RAPIDO

### Problema: MT5 Non Connette
```
❌ MT5 initialization failed

✅ Soluzioni:
1. Verifica MT5 installato e account configurato
2. Controlla credenziali in .env_vps
3. Assicurati MT5 sia aperto sulla VPS
```

### Problema: Railway Unreachable
```
❌ Frontend Railway non raggiungibile

✅ Soluzioni:
1. Verifica URL corretto in .env_vps
2. Controlla app Railway sia online
3. Test: curl -I https://your-app.railway.app/health
```

### Problema: Dipendenze Python
```
❌ ModuleNotFoundError

✅ Soluzioni:
1. Riesegui: quick_installer.bat come Amministratore
2. Manuale: pip install -r requirements_vps.txt
3. Verifica Python >= 3.8
```

---

## 📊 MONITORAGGIO PRESTAZIONI

### Dashboard Locale (VPS)
- **Sistema Generale**: http://localhost:8001
- **MT5 Bridge**: http://localhost:8000
- **Stato Processi**: Menu → Opzione 3

### KPI Target
- **Segnali/Ora**: 3-5 segnali/ora
- **Affidabilità**: >75% accuracy
- **Uptime**: >99.5%
- **Response Time**: <2 secondi

---

## 🔒 SICUREZZA

### Checklist Sicurezza
- [ ] Cambiato `VPS_API_KEY` con chiave forte
- [ ] Password MT5 complessa
- [ ] Firewall VPS configurato
- [ ] Accesso RDP sicuro
- [ ] Backup configurazioni

### File Sensibili
- `.env_vps` - Non condividere mai
- `*.log` - Possono contenere info sensibili
- Database files - Backup regolari

---

## 📞 SUPPORTO

### Ordine di Troubleshooting
1. **Esegui diagnostica**: `python check_system.py`
2. **Controlla log**: Visualizza log dal menu
3. **Testa componenti**: Menu → Test MT5 Connection
4. **Consulta guida**: `GUIDA_COMPLETA_VPS.md`

### File di Log
- `vps_launcher.log` - Log generale sistema
- `vps_main_server.log` - Log server principale
- `diagnostic_report.json` - Report diagnostica

---

## ✅ CHECKLIST PRE-PRODUZIONE

Prima di andare live:

- [ ] VPS Windows stabile e performante
- [ ] MetaTrader 5 installato e account configurato
- [ ] Python 3.8+ con tutte dipendenze
- [ ] File `.env_vps` configurato con dati reali
- [ ] Railway app online e raggiungibile
- [ ] Test sistema completo passato
- [ ] Gemini API key valida
- [ ] Monitoraggio attivato
- [ ] Backup configurazioni fatto

---

## 🎯 RISULTATO FINALE

Dopo installazione avrai:

🤖 **Sistema AI completamente automatizzato**
- Analizza mercati 24/7
- Genera segnali professionali
- Si auto-monitora e riavvia

🔗 **Integrazione Railway seamless**
- Comunicazione tempo reale
- Dashboard web completa
- API RESTful complete

📊 **Monitoraggio avanzato**
- Log dettagliati
- Health checks automatici
- Performance metrics

---

**🚀 Il tuo VPS AI Trading System è pronto per operazioni di trading professionale! 📈**

*Per supporto dettagliato, consulta `GUIDA_COMPLETA_VPS.md`*