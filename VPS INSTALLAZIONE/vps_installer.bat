@echo off
title VPS AI Trading System - Installer v1.0

echo.
echo ========================================================================
echo                   VPS AI TRADING SYSTEM - INSTALLER v1.0
echo ========================================================================
echo.
echo 🚀 Configurazione automatica del sistema di trading VPS
echo 📊 Connessione a MetaTrader 5 e generazione segnali AI
echo 🤖 Sistema completo per analisi di mercato automatizzata
echo.
echo ========================================================================
echo.

:: Check Python installation
echo [STEP 1] Controllo installazione Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python non trovato! Installare Python 3.8+ da python.org
    echo.
    echo Scaricare da: https://www.python.org/downloads/
    echo IMPORTANTE: Durante installazione selezionare "Add to PATH"
    echo.
    pause
    exit /b 1
)
echo ✅ Python installato correttamente
echo.

:: Check MetaTrader 5
echo [STEP 2] Controllo MetaTrader 5...
if not exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    if not exist "C:\Program Files (x86)\MetaTrader 5\terminal64.exe" (
        echo ⚠️  MetaTrader 5 non trovato in posizioni standard
        echo.
        echo Download MetaTrader 5: https://www.metatrader5.com/en/download
        echo IMPORTANTE: Installare e configurare un account di trading
        echo.
        pause
    ) else (
        echo ✅ MetaTrader 5 trovato in C:\Program Files (x86)\MetaTrader 5\
    )
) else (
    echo ✅ MetaTrader 5 trovato in C:\Program Files\MetaTrader 5\
)
echo.

:: Install Python dependencies
echo [STEP 3] Installazione dipendenze Python...
echo Installazione pacchetti richiesti (può richiedere alcuni minuti)...
python -m pip install --upgrade pip
python -m pip install -r requirements_vps.txt

if %errorlevel% neq 0 (
    echo ❌ Errore installazione dipendenze
    echo Tentativo installazione manuale pacchetti essenziali...
    
    python -m pip install MetaTrader5>=5.0.5260
    python -m pip install fastapi>=0.104.0
    python -m pip install uvicorn>=0.24.0
    python -m pip install pandas>=2.0.0
    python -m pip install numpy>=1.24.0
    python -m pip install requests>=2.31.0
    python -m pip install psutil>=5.9.0
    python -m pip install python-dotenv>=1.0.0
    
    echo ⚠️  Alcuni pacchetti potrebbero non essere installati
) else (
    echo ✅ Tutte le dipendenze installate correttamente
)
echo.

:: Configure environment
echo [STEP 4] Configurazione ambiente...

:: Check if .env_vps exists and configure
if not exist ".env_vps" (
    echo ❌ File .env_vps non trovato
    echo Creazione file configurazione base...
    
    echo # VPS Trading System Configuration > .env_vps
    echo MT5_BROKER_SERVER=MetaQuotes-Demo >> .env_vps
    echo MT5_LOGIN=123456 >> .env_vps
    echo MT5_PASSWORD=password123 >> .env_vps
    echo MT5_BRIDGE_PORT=8000 >> .env_vps
    echo GEMINI_API_KEY=your_gemini_api_key_here >> .env_vps
    echo DATABASE_VPS_URL=sqlite:///vps_trading.db >> .env_vps
    echo LOG_LEVEL=INFO >> .env_vps
    echo BRIDGE_HOST=0.0.0.0 >> .env_vps
    echo MAX_SIGNALS_PER_HOUR=5 >> .env_vps
    echo MIN_RELIABILITY_THRESHOLD=70 >> .env_vps
    echo RAILWAY_FRONTEND_URL=https://your-railway-app.railway.app >> .env_vps
    
    echo ✅ File .env_vps creato
) else (
    echo ✅ File .env_vps trovato
)

echo.
echo ⚠️  IMPORTANTE: CONFIGURARE .env_vps con i tuoi dati reali!
echo.
echo Devi modificare:
echo - MT5_BROKER_SERVER: Server del tuo broker (es: ICMarkets-Live)
echo - MT5_LOGIN: Il tuo numero account MT5
echo - MT5_PASSWORD: Password del tuo account MT5
echo - GEMINI_API_KEY: Chiave API Google Gemini per AI
echo - RAILWAY_FRONTEND_URL: URL della tua app Railway
echo.

:: Test MT5 Connection
echo [STEP 5] Test connessione MT5...
echo Esecuzione test connessione...
python -c "
import MetaTrader5 as mt5
import sys

print('Tentativo inizializzazione MT5...')
if not mt5.initialize():
    print('❌ Errore inizializzazione MT5')
    print('Verificare che MT5 sia installato e accessibile')
    sys.exit(1)
else:
    print('✅ MT5 inizializzato correttamente')
    mt5.shutdown()
    print('Test completato con successo')
"

if %errorlevel% neq 0 (
    echo ⚠️  Test MT5 fallito - verificare installazione
) else (
    echo ✅ Test MT5 completato con successo
)
echo.

:: Create Windows service
echo [STEP 6] Configurazione servizio Windows...

:: Create start script
echo @echo off > start_vps_system.bat
echo title VPS AI Trading System >> start_vps_system.bat
echo echo Avvio VPS AI Trading System... >> start_vps_system.bat
echo python vps_auto_launcher.py --auto >> start_vps_system.bat

:: Create desktop shortcut script
echo @echo off > create_shortcut.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") >> create_shortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\VPS AI Trading System.lnk" >> create_shortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcut.vbs
echo oLink.TargetPath = "%CD%\start_vps_system.bat" >> create_shortcut.vbs
echo oLink.WorkingDirectory = "%CD%" >> create_shortcut.vbs
echo oLink.Description = "VPS AI Trading System" >> create_shortcut.vbs
echo oLink.IconLocation = "%CD%\vps_auto_launcher.py,0" >> create_shortcut.vbs
echo oLink.Save >> create_shortcut.vbs

cscript //nologo create_shortcut.vbs
del create_shortcut.vbs

echo ✅ Collegamento desktop creato
echo.

:: Final instructions
echo ========================================================================
echo                              🎉 INSTALLAZIONE COMPLETATA! 🎉
echo ========================================================================
echo.
echo PROSSIMI PASSAGGI:
echo.
echo 1. ⚙️  CONFIGURARE .env_vps con i tuoi dati reali MT5 e API
echo    - Aprire .env_vps con blocco note
echo    - Inserire login, password, server MT5
echo    - Inserire API key Google Gemini
echo    - Inserire URL Railway del frontend
echo.
echo 2. 🚀 AVVIARE IL SISTEMA:
echo    - Doppio click su "VPS AI Trading System" sul desktop
echo    - Oppure eseguire: python vps_auto_launcher.py
echo.
echo 3. 🔍 VERIFICARE FUNZIONAMENTO:
echo    - Controllare log per errori
echo    - Verificare connessione MT5
echo    - Testare generazione segnali
echo.
echo 4. 🌐 COLLEGARE AL FRONTEND RAILWAY:
echo    - Il sistema si connetterà automaticamente al frontend
echo    - Verificare che l'URL in .env_vps sia corretto
echo.
echo ========================================================================
echo.
echo Per supporto: controllare i file di log e la documentazione
echo Sistema pronto per il trading automatizzato! 🤖📈
echo.
echo ========================================================================

pause