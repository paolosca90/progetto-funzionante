@echo off
title VPS AI Trading System - Quick Installer
color 0A

echo.
echo ===============================================================================
echo              🚀 VPS AI TRADING SYSTEM - QUICK INSTALLER 🚀
echo ===============================================================================
echo.
echo     Installazione rapida per VPS Windows - Tutti i componenti inclusi
echo     Sistema completo per trading automatico con intelligenza artificiale
echo.
echo ===============================================================================

:: Set working directory
set INSTALL_DIR=%~dp0
cd /d "%INSTALL_DIR%"

echo.
echo [1/10] 📋 Controllo Sistema Operativo...
ver | findstr /i "windows" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Sistema operativo non supportato - Richiesto Windows
    pause
    exit /b 1
)
echo ✅ Sistema operativo compatibile

echo.
echo [2/10] 🐍 Verifica Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python non trovato!
    echo.
    echo 📥 SCARICA E INSTALLA PYTHON:
    echo    1. Vai su: https://www.python.org/downloads/
    echo    2. Scarica Python 3.8 o superiore
    echo    3. Durante installazione: SELEZIONA "Add Python to PATH"
    echo    4. Riavvia questo installer dopo installazione
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version') do set PYTHON_VERSION=%%v
echo ✅ Python %PYTHON_VERSION% trovato

echo.
echo [3/10] 🎮 Verifica MetaTrader 5...
set MT5_FOUND=0
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" set MT5_FOUND=1
if exist "C:\Program Files (x86)\MetaTrader 5\terminal64.exe" set MT5_FOUND=1
if %MT5_FOUND% equ 1 (
    echo ✅ MetaTrader 5 trovato
) else (
    echo ⚠️  MetaTrader 5 non trovato in posizioni standard
    echo.
    echo 📥 SCARICA E INSTALLA METATRADER 5:
    echo    1. Vai su: https://www.metatrader5.com/en/download
    echo    2. Scarica e installa MetaTrader 5  
    echo    3. Configura il tuo account di trading
    echo    4. Assicurati che sia aperto e connesso
    echo.
    echo ⏭️  Continuo comunque con l'installazione...
    timeout /t 3 >nul
)

echo.
echo [4/10] 📦 Installazione dipendenze Python...
echo     Questo può richiedere alcuni minuti - attendere prego...

python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo ⚠️  Errore aggiornamento pip - continuo comunque...
)

echo     Installazione pacchetti essenziali...
python -m pip install -r requirements_vps.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ⚠️  Alcune dipendenze potrebbero non essere installate
    echo     Installazione pacchetti individuali...
    
    python -m pip install MetaTrader5 --quiet
    python -m pip install fastapi --quiet
    python -m pip install uvicorn --quiet  
    python -m pip install pandas --quiet
    python -m pip install requests --quiet
    python -m pip install python-dotenv --quiet
    python -m pip install psutil --quiet
)
echo ✅ Dipendenze Python installate

echo.
echo [5/10] ⚙️  Configurazione ambiente...
if not exist ".env_vps" (
    echo     Creazione file configurazione base...
    
    echo # VPS AI Trading System Configuration > .env_vps
    echo # IMPORTANTE: Modifica questi valori con i tuoi dati reali >> .env_vps
    echo. >> .env_vps
    echo # === CONNESSIONE METATRADER 5 === >> .env_vps
    echo MT5_BROKER_SERVER=MetaQuotes-Demo >> .env_vps
    echo MT5_LOGIN=123456 >> .env_vps
    echo MT5_PASSWORD=password123 >> .env_vps
    echo MT5_BRIDGE_PORT=8000 >> .env_vps
    echo. >> .env_vps
    echo # === CONNESSIONE RAILWAY FRONTEND === >> .env_vps
    echo RAILWAY_FRONTEND_URL=https://your-railway-app.railway.app >> .env_vps
    echo VPS_API_KEY=your-secure-vps-key-change-this >> .env_vps
    echo VPS_SERVER_PORT=8001 >> .env_vps
    echo. >> .env_vps
    echo # === GOOGLE GEMINI AI === >> .env_vps
    echo GEMINI_API_KEY=your_gemini_api_key_here >> .env_vps
    echo. >> .env_vps
    echo # === CONFIGURAZIONI TRADING === >> .env_vps
    echo MAX_SIGNALS_PER_HOUR=5 >> .env_vps
    echo MIN_RELIABILITY_THRESHOLD=70 >> .env_vps
    echo BRIDGE_HOST=0.0.0.0 >> .env_vps
    echo DATABASE_VPS_URL=sqlite:///vps_trading.db >> .env_vps
    echo LOG_LEVEL=INFO >> .env_vps
    
    echo ✅ File .env_vps creato
) else (
    echo ✅ File .env_vps già esistente
)

echo.
echo [6/10] 🔧 Creazione script di avvio...

echo @echo off > start_vps_system.bat
echo title VPS AI Trading System - Running >> start_vps_system.bat
echo cd /d "%~dp0" >> start_vps_system.bat
echo echo 🚀 Avvio VPS AI Trading System... >> start_vps_system.bat
echo python vps_auto_launcher.py >> start_vps_system.bat
echo pause >> start_vps_system.bat

echo @echo off > start_vps_auto.bat
echo title VPS AI Trading System - Auto Mode >> start_vps_auto.bat
echo cd /d "%~dp0" >> start_vps_auto.bat
echo echo 🤖 Avvio modalità automatica... >> start_vps_auto.bat
echo python vps_auto_launcher.py --auto >> start_vps_auto.bat

echo ✅ Script di avvio creati

echo.
echo [7/10] 🖥️  Creazione collegamenti desktop...

:: Crea collegamento VBS per desktop
echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcuts.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\VPS AI Trading System.lnk" >> create_shortcuts.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcuts.vbs
echo oLink.TargetPath = "%CD%\start_vps_system.bat" >> create_shortcuts.vbs
echo oLink.WorkingDirectory = "%CD%" >> create_shortcuts.vbs
echo oLink.Description = "VPS AI Trading System - Menu Controllo" >> create_shortcuts.vbs
echo oLink.Save >> create_shortcuts.vbs
echo. >> create_shortcuts.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\VPS AI Trading Auto.lnk" >> create_shortcuts.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcuts.vbs
echo oLink.TargetPath = "%CD%\start_vps_auto.bat" >> create_shortcuts.vbs
echo oLink.WorkingDirectory = "%CD%" >> create_shortcuts.vbs
echo oLink.Description = "VPS AI Trading System - Modalità Automatica" >> create_shortcuts.vbs
echo oLink.Save >> create_shortcuts.vbs

cscript //nologo create_shortcuts.vbs >nul 2>&1
del create_shortcuts.vbs >nul 2>&1

echo ✅ Collegamenti desktop creati

echo.
echo [8/10] 🧪 Test iniziale sistema...
echo     Test connessione MetaTrader 5...

python -c "
import sys
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        print('✅ MT5 connesso correttamente')
        account_info = mt5.account_info()
        if account_info:
            print(f'   Account: {account_info.login}')
            print(f'   Server: {account_info.server}')
        else:
            print('⚠️  MT5 non ha account configurato')
        mt5.shutdown()
    else:
        print('⚠️  MT5 non può inizializzare - verificare installazione')
except ImportError:
    print('❌ MetaTrader5 non disponibile - installare manualmente')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  Errore test MT5: {e}')
" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Test MT5 fallito - verificare configurazione manualmente
) else (
    echo ✅ Test MT5 completato
)

echo.
echo [9/10] 📝 Generazione documentazione sistema...

echo === VPS AI TRADING SYSTEM - INFO INSTALLAZIONE === > SISTEMA_INFO.txt
echo Data installazione: %date% %time% >> SISTEMA_INFO.txt
echo Directory installazione: %CD% >> SISTEMA_INFO.txt
echo Versione Python: %PYTHON_VERSION% >> SISTEMA_INFO.txt
echo. >> SISTEMA_INFO.txt
echo === COMANDI PRINCIPALI === >> SISTEMA_INFO.txt
echo 1. Menu interattivo: python vps_auto_launcher.py >> SISTEMA_INFO.txt
echo 2. Modalità automatica: python vps_auto_launcher.py --auto >> SISTEMA_INFO.txt
echo 3. Solo avvio: python vps_auto_launcher.py --start >> SISTEMA_INFO.txt
echo 4. Stop sistema: python vps_auto_launcher.py --stop >> SISTEMA_INFO.txt
echo 5. Stato sistema: python vps_auto_launcher.py --status >> SISTEMA_INFO.txt
echo. >> SISTEMA_INFO.txt
echo === FILE PRINCIPALI === >> SISTEMA_INFO.txt
echo - .env_vps: Configurazione ambiente (MODIFICARE!) >> SISTEMA_INFO.txt
echo - vps_auto_launcher.py: Launcher principale >> SISTEMA_INFO.txt  
echo - vps_main_server.py: Server principale >> SISTEMA_INFO.txt
echo - signal_engine.py: Motore AI segnali >> SISTEMA_INFO.txt
echo - GUIDA_COMPLETA_VPS.md: Documentazione completa >> SISTEMA_INFO.txt
echo. >> SISTEMA_INFO.txt
echo === LOG FILES === >> SISTEMA_INFO.txt
echo - vps_launcher.log: Log launcher >> SISTEMA_INFO.txt
echo - vps_main_server.log: Log server principale >> SISTEMA_INFO.txt

echo ✅ Info sistema generate

echo.
echo [10/10] 🔐 Configurazione sicurezza base...

:: Imposta permessi cartella
icacls . /inheritance:r /grant:r "%USERNAME%":F >nul 2>&1
icacls .env_vps /inheritance:r /grant:r "%USERNAME%":RW >nul 2>&1

echo ✅ Permessi configurati

echo.
echo ===============================================================================
echo                         🎉 INSTALLAZIONE COMPLETATA! 🎉
echo ===============================================================================
echo.
echo ✅ Sistema VPS AI Trading installato con successo!
echo.
echo 🎯 PROSSIMI PASSI OBBLIGATORI:
echo.
echo    1. 📝 CONFIGURA .env_vps CON I TUOI DATI REALI:
echo       • MT5_LOGIN: Il tuo numero account MetaTrader 5
echo       • MT5_PASSWORD: La tua password MetaTrader 5  
echo       • MT5_BROKER_SERVER: Server del tuo broker (es: ICMarkets-Live)
echo       • RAILWAY_FRONTEND_URL: URL della tua app Railway
echo       • GEMINI_API_KEY: Chiave API Google Gemini per AI
echo       • VPS_API_KEY: Chiave sicura per comunicazione (crea una password forte)
echo.
echo    2. 🔧 APRI E MODIFICA IL FILE:
echo       notepad .env_vps
echo.
echo    3. 🚀 AVVIA IL SISTEMA:
echo       • Desktop: Doppio click su "VPS AI Trading System"
echo       • Manuale: python vps_auto_launcher.py
echo.
echo ===============================================================================
echo.
echo 💡 LINKS UTILI:
echo    • Google Gemini API: https://makersuite.google.com/app/apikey
echo    • MetaTrader 5 Download: https://www.metatrader5.com/en/download
echo    • Documentazione: GUIDA_COMPLETA_VPS.md
echo.
echo 🔍 MODALITÀ DISPONIBILI:
echo    • Menu Interattivo: Controllo manuale sistema
echo    • Modalità Automatica: Trading 24/7 completamente automatico  
echo    • Background Service: Servizio Windows invisibile
echo.
echo 📊 MONITORAGGIO SISTEMA:
echo    • Local Dashboard: http://localhost:8001
echo    • MT5 Bridge: http://localhost:8000  
echo    • Log Files: vps_launcher.log, vps_main_server.log
echo.
echo ⚠️  IMPORTANTE:
echo    Prima di andare live, testa tutto in modalità demo e verifica che
echo    tutte le connessioni (MT5, Railway, Gemini) funzionino correttamente!
echo.
echo ===============================================================================
echo                    🤖 SISTEMA PRONTO PER TRADING AI! 📈
echo ===============================================================================
echo.

:: Apri automaticamente il file .env_vps per configurazione
echo 🔧 Apertura file configurazione per modifica...
timeout /t 2 >nul
notepad .env_vps

echo.
echo Installazione completata! Premi un tasto per uscire...
pause >nul