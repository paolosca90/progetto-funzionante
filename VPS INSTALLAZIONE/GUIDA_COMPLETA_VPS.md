# 🚀 GUIDA COMPLETA VPS AI TRADING SYSTEM

## 📋 Panoramica Completa

Questa guida ti accompagnerà passo-passo nell'installazione del sistema di trading AI sulla tua VPS Windows, collegandolo al frontend Railway per un'esperienza di trading automatizzata completa.

---

## 🎯 FASE 1: PREPARAZIONE VPS

### Requisiti VPS Minimi
- **OS:** Windows Server 2019+ o Windows 10/11
- **CPU:** 2 cores (raccomandati 4 cores)
- **RAM:** 4GB (raccomandati 8GB) 
- **Storage:** 20GB SSD (raccomandati 50GB)
- **Network:** Connessione stabile, IP pubblico statico (opzionale)

### Software Richiesti Pre-Installazione
1. **MetaTrader 5** - Scarica da [metatrader5.com](https://www.metatrader5.com/en/download)
2. **Python 3.8+** - Scarica da [python.org](https://www.python.org/downloads/)

---

## 🚀 FASE 2: CONNESSIONE E SETUP VPS

### Step 1: Connessione alla VPS

```bash
# Via RDP (Remote Desktop)
mstsc /v:YOUR_VPS_IP

# Via TeamViewer o altro software di controllo remoto
# Assicurati di avere le credenziali di accesso
```

### Step 2: Download File Sistema

1. **Connettiti alla tua VPS Windows**
2. **Scarica tutti i file dalla cartella "VPS INSTALLAZIONE"** sul desktop della VPS
3. **Estrai tutti i file in una cartella dedicata** (es: `C:\AITradingVPS\`)

### File Principali Inclusi:
```
VPS INSTALLAZIONE/
├── vps_auto_launcher.py          # Launcher principale
├── vps_main_server.py             # Server principale  
├── signal_engine.py               # Motore AI segnali
├── mt5_bridge_vps/               
│   └── main_bridge.py             # Bridge MT5
├── requirements_vps.txt           # Dipendenze Python
├── .env_vps                       # Configurazione ambiente
├── vps_installer.bat              # Installer automatico
├── README_VPS.md                  # Documentazione tecnica
└── GUIDA_COMPLETA_VPS.md         # Questa guida
```

---

## ⚙️ FASE 3: INSTALLAZIONE AUTOMATICA

### Step 1: Esegui Installer Automatico

1. **Apri CMD/PowerShell come Amministratore**
2. **Naviga nella cartella dei file**
   ```cmd
   cd C:\AITradingVPS\
   ```
3. **Esegui l'installer automatico**
   ```cmd
   vps_installer.bat
   ```

### Cosa Fa l'Installer:
- ✅ Verifica Python e MetaTrader 5
- ✅ Installa tutte le dipendenze automaticamente
- ✅ Configura l'ambiente di sistema  
- ✅ Crea collegamenti desktop
- ✅ Testa le connessioni
- ✅ Configura i servizi

### Step 2: Configurazione Personalizzata

**Modifica il file `.env_vps`** con i tuoi dati reali:

```env
# === CONNESSIONE METATRADER 5 ===
MT5_BROKER_SERVER=ICMarkets-Live              # Nome server del tuo broker
MT5_LOGIN=12345678                           # Il tuo numero account MT5
MT5_PASSWORD=your_mt5_password               # Password del tuo account MT5
MT5_BRIDGE_PORT=8000                         # Porta locale bridge MT5

# === CONNESSIONE RAILWAY FRONTEND ===
RAILWAY_FRONTEND_URL=https://your-app-name.railway.app  # URL della tua app Railway
VPS_API_KEY=your-secure-vps-key-2024        # Chiave sicura per comunicazione
VPS_SERVER_PORT=8001                         # Porta server principale VPS

# === GOOGLE GEMINI AI ===
GEMINI_API_KEY=your_gemini_api_key_here      # API Key per AI (da Google AI Studio)

# === CONFIGURAZIONI TRADING ===
MAX_SIGNALS_PER_HOUR=5                       # Massimo 5 segnali/ora
MIN_RELIABILITY_THRESHOLD=70                 # Soglia minima affidabilità 70%
BRIDGE_HOST=0.0.0.0                         # Host bridge (lasciare così)

# === DATABASE E LOG ===
DATABASE_VPS_URL=sqlite:///vps_trading.db   # Database locale
LOG_LEVEL=INFO                               # Livello di logging
```

### 🔑 Come Ottenere le Chiavi API:

**Google Gemini API Key:**
1. Vai su [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea un nuovo progetto o seleziona esistente
3. Genera una nuova API Key
4. Copia e incolla in GEMINI_API_KEY

**Railway Frontend URL:**
1. Vai al tuo progetto Railway
2. Nella tab "Deployments" trovi l'URL pubblico
3. Copia l'URL completo (https://...)

---

## 🚀 FASE 4: AVVIO E TESTING DEL SISTEMA

### Step 1: Primo Avvio (Modalità Interattiva)

```cmd
# Avvia il sistema principale
python vps_auto_launcher.py
```

**Menu Controllo Sistema:**
```
🎮 VPS TRADING SYSTEM - MENU CONTROLLO
1. 🚀 Avvia Sistema Completo
2. 🛑 Arresta Sistema  
3. 📊 Mostra Stato
4. 🔄 Riavvia Servizio
5. ⚙️  Configurazione
6. 🔍 Test Connessione MT5
7. 📝 Visualizza Log
0. ❌ Esci
```

### Step 2: Test Connessioni

1. **Seleziona opzione 6** - Test Connessione MT5
2. **Verifica che MT5 sia connesso** correttamente
3. **Seleziona opzione 1** - Avvia Sistema Completo  
4. **Seleziona opzione 3** - Mostra Stato per monitorare

### Step 3: Verifica Generazione Segnali

```cmd
# Controlla i log in tempo reale
tail -f vps_main_server.log

# Oppure dal menu: opzione 7 - Visualizza Log
```

**Segnali di Successo:**
```
✅ MT5 connesso - Account: 12345678
✅ Frontend Railway raggiungibile  
💚 Heartbeat inviato con successo
🔄 Generazione nuovi segnali...
✅ Segnale EURUSD inviato al frontend
```

---

## 🔄 FASE 5: CONFIGURAZIONE MODALITÀ AUTOMATICA

### Step 1: Modalità Automatica (24/7)

```cmd
# Avvio automatico in background
python vps_auto_launcher.py --auto
```

### Step 2: Configurazione Servizio Windows

Crea un servizio Windows per avvio automatico:

1. **Crea file `start_service.bat`:**
   ```batch
   @echo off
   cd /d "C:\AITradingVPS"
   python vps_auto_launcher.py --auto
   ```

2. **Installa come servizio Windows** (opzionale):
   ```cmd
   sc create "VPSAITrading" binPath="C:\AITradingVPS\start_service.bat" start=auto
   sc start "VPSAITrading"
   ```

### Step 3: Monitoraggio Automatico

Il sistema include monitoraggio automatico con:
- ♻️ **Auto-restart** in caso di errori
- 📊 **Health monitoring** continuo
- 💚 **Heartbeat** verso Railway ogni minuto
- 📝 **Logging** completo di tutte le operazioni

---

## 📡 FASE 6: INTEGRAZIONE CON RAILWAY FRONTEND

### Configurazione Lato Railway

Nel tuo progetto Railway, assicurati di avere questi endpoints:

```javascript
// Endpoint per heartbeat VPS
POST /api/vps/heartbeat

// Endpoint per ricevere segnali
POST /api/signals/receive

// Health check
GET /health
```

### Configurazione Variabili Ambiente Railway

Aggiungi queste variabili nel tuo Railway dashboard:

```env
VPS_API_KEY=your-secure-vps-key-2024        # Stessa chiave del VPS
GEMINI_API_KEY=your_gemini_api_key_here     # Per backup AI frontend
```

### Test Connessione VPS ↔ Railway

```bash
# Test dal VPS
curl -X POST https://your-app.railway.app/api/vps/heartbeat \
     -H "X-VPS-API-Key: your-secure-vps-key-2024" \
     -H "Content-Type: application/json" \
     -d '{"vps_id":"vps-001","status":"active"}'

# Risposta attesa: {"status":"success"}
```

---

## 🔍 FASE 7: MONITORAGGIO E TROUBLESHOOTING

### Dashboard di Monitoraggio

**Accesso API VPS Locale:**
```
http://localhost:8001/              # Stato generale
http://localhost:8001/health        # Health check
http://localhost:8001/signals/latest # Ultimi segnali
```

**Bridge MT5:**
```
http://localhost:8000/              # Stato MT5
http://localhost:8000/bridge/account # Info account MT5
```

### File di Log Principali

```bash
# Log principale sistema
type vps_launcher.log

# Log server principale  
type vps_main_server.log

# Log Windows (se configurato come servizio)
eventvwr.msc
```

### Comandi di Debug Utili

```cmd
# Verifica processi Python attivi
tasklist | findstr python

# Test connessione MT5 rapido
python -c "import MetaTrader5 as mt5; print('OK' if mt5.initialize() else 'FAIL'); mt5.shutdown()"

# Test connessione Railway
curl -I https://your-app.railway.app/health

# Verifica porte aperte
netstat -an | findstr "8000\|8001"
```

---

## 🛡️ FASE 8: SICUREZZA E BACKUP

### Configurazioni Sicurezza

1. **Firewall Windows:**
   ```cmd
   # Consenti porte necessarie (solo se necessario dall'esterno)
   netsh advfirewall firewall add rule name="VPS AI Trading" dir=in action=allow protocol=TCP localport=8001
   ```

2. **Credenziali Sicure:**
   - Usa password complesse per MT5
   - Cambia VPS_API_KEY regolarmente  
   - Non condividere mai .env_vps

3. **Backup Configurazioni:**
   ```cmd
   # Backup completo configurazione
   copy .env_vps .env_vps.backup
   copy vps_launcher.log logs\backup\
   ```

### Monitoraggio Security

```cmd
# Controlla accessi non autorizzati
eventvwr.msc -> Windows Logs -> Security

# Monitor connessioni di rete  
netstat -an | findstr ESTABLISHED
```

---

## 📊 FASE 9: OTTIMIZZAZIONI PRESTAZIONI

### Configurazioni VPS Ottimali

**Performance Tuning:**
```cmd
# Priorità alta per processi Python
wmic process where name="python.exe" CALL setpriority "high priority"

# Disabilita servizi non necessari
services.msc -> Disabilita Windows Search, Print Spooler, ecc.
```

**Resource Monitoring:**
```cmd
# Monitor risorse sistema
perfmon.msc

# Task Manager avanzato  
taskmgr -> Performance tab -> Resource Monitor
```

### Configurazioni Trading Ottimali

```env
# In .env_vps - Configurazioni per performance
MAX_SIGNALS_PER_HOUR=3               # Riduci per broker con limitazioni
MIN_RELIABILITY_THRESHOLD=75         # Aumenta per segnali più selettivi
LOG_LEVEL=WARNING                    # Riduci logging per performance
```

---

## 🆘 TROUBLESHOOTING GUIDE

### Problemi Comuni e Soluzioni

#### 1. MT5 Non Si Connette
```
❌ Errore: MT5 initialization failed

✅ Soluzioni:
1. Verifica MetaTrader 5 sia installato
2. Controlla credenziali in .env_vps
3. Assicurati MT5 sia aperto e loggato
4. Verifica connessione internet VPS
```

#### 2. Railway Non Raggiungibile  
```
❌ Errore: Frontend Railway non raggiungibile

✅ Soluzioni:
1. Verifica RAILWAY_FRONTEND_URL corretto
2. Controlla che app Railway sia online
3. Testa connessione: curl -I [URL]
4. Verifica VPS_API_KEY sia identica su entrambi lati
```

#### 3. Segnali Non Generati
```
❌ Errore: Nessun segnale generato

✅ Soluzioni:
1. Verifica GEMINI_API_KEY valida
2. Controlla log per errori specifici
3. Testa manualmente: opzione 6 nel menu
4. Verifica connessione MT5 Bridge
```

#### 4. Sistema Non Parte
```
❌ Errore: Launcher non si avvia

✅ Soluzioni:
1. Esegui come Amministratore
2. Verifica Python installato correttamente
3. Reinstalla dipendenze: pip install -r requirements_vps.txt
4. Controlla file .env_vps presente
```

#### 5. Errori Python/Dipendenze
```
❌ Errore: ModuleNotFoundError

✅ Soluzioni:
1. Reinstalla dipendenze complete
2. Verifica versione Python >= 3.8
3. Usa virtual environment se necessario
4. Controlla PATH Python corretto
```

---

## 📞 SUPPORTO E MANUTENZIONE

### Checklist Manutenzione Settimanale

- [ ] Controlla log per errori
- [ ] Verifica generazione segnali
- [ ] Test connessioni MT5 e Railway  
- [ ] Backup configurazioni .env_vps
- [ ] Monitor utilizzo risorse VPS
- [ ] Update sicurezza Windows

### Escalation Supporto

1. **Level 1:** Controlla questa guida e README_VPS.md
2. **Level 2:** Analizza log dettagliati (vps_launcher.log)
3. **Level 3:** Test manuali componenti individuali
4. **Level 4:** Riconfigura da zero seguendo questa guida

### File di Log Diagnosi

```cmd
# Genera report completo stato sistema
python -c "
import subprocess, os, sys, json, requests
from datetime import datetime

print('=== VPS TRADING SYSTEM - DIAGNOSTIC REPORT ===')
print(f'Timestamp: {datetime.now()}')
print(f'Python: {sys.version}')
print(f'Platform: {os.name}')

try:
    import MetaTrader5 as mt5
    print('MT5: Available')
except ImportError:
    print('MT5: NOT AVAILABLE')

# Test Railway connection
try:
    resp = requests.get('https://your-app.railway.app/health', timeout=10)
    print(f'Railway: {resp.status_code}')
except:
    print('Railway: UNREACHABLE')

print('=== END REPORT ===')
"
```

---

## ✅ CHECKLIST FINALE PRE-PRODUZIONE

### Prima di Andare Live:

- [ ] **VPS:** Windows Server configurato e stabile
- [ ] **MT5:** Installato, account configurato e connesso
- [ ] **Python:** Versione 3.8+ con tutte dipendenze
- [ ] **Sistema:** Tutti file copiati e configurati
- [ ] **Environment:** File .env_vps con dati reali
- [ ] **Railway:** App online e raggiungibile
- [ ] **API Keys:** Gemini API valida e funzionante
- [ ] **Network:** Connessione stabile VPS ↔ Railway
- [ ] **Testing:** Sistema avviato e segnali generati
- [ ] **Monitoring:** Log attivi e controllati
- [ ] **Security:** Firewall e credenziali sicure
- [ ] **Backup:** Configurazioni salvate
- [ ] **Service:** Configurato per avvio automatico

### Test Finale Completo:

```cmd
# 1. Test MT5
python -c "import MetaTrader5 as mt5; print('✅' if mt5.initialize() else '❌'); mt5.shutdown()"

# 2. Test Railway  
curl -I https://your-app.railway.app/health

# 3. Test Sistema Completo
python vps_auto_launcher.py --status

# 4. Test Generazione Segnale
# Dal menu interattivo -> opzione 1 -> opzione 3
```

---

## 🎯 FASE 10: GO LIVE!

### Avvio Finale Produzione

```cmd
# Modalità produzione completa
python vps_auto_launcher.py --auto

# Monitor in tempo reale
tail -f vps_main_server.log
```

### KPI da Monitorare

- 📈 **Segnali/Ora:** Target 3-5 segnali/ora
- 🎯 **Affidabilità Media:** Target >75%
- ⚡ **Uptime Sistema:** Target >99.5%
- 🔗 **Connettività Railway:** Target 100%
- 📊 **Response Time:** Target <2 secondi

---

## 🏁 CONCLUSIONE

Hai ora un sistema di trading AI completamente automatizzato che:

- 🤖 **Analizza mercati** in tempo reale con AI
- 📊 **Genera segnali** professionali automaticamente  
- 🔗 **Comunica** seamlessly con il frontend Railway
- 🛡️ **Si auto-monitora** e riavvia in caso di problemi
- 📈 **Scale** automaticamente con la crescita

**Il tuo VPS AI Trading System è pronto per operare 24/7! 🚀📈**

---

*Guida creata per deployment professionale VPS AI Trading System v1.0*