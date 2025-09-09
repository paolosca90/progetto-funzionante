@echo off
title VPS AI Trading System - EXE Installer Builder
echo.
echo ========================================================================
echo                  VPS AI TRADING SYSTEM - EXE INSTALLER BUILDER
echo ========================================================================
echo.
echo 🛠️  Creazione installer eseguibile per distribuzione VPS
echo 📦 Include tutti i componenti necessari per installazione automatica
echo.
echo ========================================================================
echo.

:: Check Python installation  
echo [STEP 1] Controllo installazione Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python non trovato! Installare Python 3.8+ da python.org
    pause
    exit /b 1
)
echo ✅ Python installato correttamente
echo.

:: Install PyInstaller and dependencies
echo [STEP 2] Installazione PyInstaller e dipendenze...
python -m pip install --upgrade pip
python -m pip install pyinstaller>=6.2.0
python -m pip install -r requirements_vps.txt

if %errorlevel% neq 0 (
    echo ⚠️  Alcune dipendenze potrebbero non essere installate
    echo Continuando comunque...
)
echo ✅ Dipendenze installate
echo.

:: Clean previous builds
echo [STEP 3] Pulizia build precedenti...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "*.spec" del "*.spec"
if exist __pycache__ rmdir /s /q __pycache__
echo ✅ Pulizia completata
echo.

:: Create PyInstaller spec file for VPS launcher
echo [STEP 4] Creazione configurazione PyInstaller...

echo # VPS Trading System PyInstaller Configuration > vps_installer.spec
echo # Generated automatically - do not edit manually >> vps_installer.spec
echo. >> vps_installer.spec
echo import sys >> vps_installer.spec
echo from pathlib import Path >> vps_installer.spec
echo. >> vps_installer.spec
echo block_cipher = None >> vps_installer.spec
echo. >> vps_installer.spec
echo # Data files to include >> vps_installer.spec
echo added_files = [ >> vps_installer.spec
echo     ('requirements_vps.txt', '.'), >> vps_installer.spec
echo     ('.env_vps', '.'), >> vps_installer.spec
echo     ('mt5_symbols.json', '.'), >> vps_installer.spec
echo     ('vps_installer.bat', '.'), >> vps_installer.spec
echo     ('README_VPS.md', '.'), >> vps_installer.spec
echo     ('mt5_bridge_vps/main_bridge.py', 'mt5_bridge_vps/'), >> vps_installer.spec
echo     ('signal_engine.py', '.'), >> vps_installer.spec
echo     ('models.py', '.'), >> vps_installer.spec
echo     ('schemas.py', '.'), >> vps_installer.spec
echo     ('database.py', '.'), >> vps_installer.spec
echo     ('vps_main_server.py', '.') >> vps_installer.spec
echo ] >> vps_installer.spec
echo. >> vps_installer.spec
echo a = Analysis( >> vps_installer.spec
echo     ['vps_auto_launcher.py'], >> vps_installer.spec
echo     pathex=[], >> vps_installer.spec
echo     binaries=[], >> vps_installer.spec
echo     datas=added_files, >> vps_installer.spec
echo     hiddenimports=[ >> vps_installer.spec
echo         'MetaTrader5', >> vps_installer.spec
echo         'fastapi', >> vps_installer.spec
echo         'uvicorn', >> vps_installer.spec
echo         'pandas', >> vps_installer.spec
echo         'numpy', >> vps_installer.spec
echo         'sqlalchemy', >> vps_installer.spec
echo         'requests', >> vps_installer.spec
echo         'psutil', >> vps_installer.spec
echo         'google.generativeai', >> vps_installer.spec
echo         'dotenv', >> vps_installer.spec
echo         'talib', >> vps_installer.spec
echo         'datetime', >> vps_installer.spec
echo         'threading', >> vps_installer.spec
echo         'asyncio', >> vps_installer.spec
echo         'logging', >> vps_installer.spec
echo         'json', >> vps_installer.spec
echo         'subprocess' >> vps_installer.spec
echo     ], >> vps_installer.spec
echo     hookspath=[], >> vps_installer.spec
echo     hooksconfig={}, >> vps_installer.spec
echo     runtime_hooks=[], >> vps_installer.spec
echo     excludes=[], >> vps_installer.spec
echo     win_no_prefer_redirects=False, >> vps_installer.spec
echo     win_private_assemblies=False, >> vps_installer.spec
echo     cipher=block_cipher, >> vps_installer.spec
echo     noarchive=False, >> vps_installer.spec
echo ) >> vps_installer.spec
echo. >> vps_installer.spec
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher) >> vps_installer.spec
echo. >> vps_installer.spec
echo exe = EXE( >> vps_installer.spec
echo     pyz, >> vps_installer.spec
echo     a.scripts, >> vps_installer.spec
echo     a.binaries, >> vps_installer.spec
echo     a.zipfiles, >> vps_installer.spec
echo     a.datas, >> vps_installer.spec
echo     [], >> vps_installer.spec
echo     name='VPS_AI_Trading_Installer', >> vps_installer.spec
echo     debug=False, >> vps_installer.spec
echo     bootloader_ignore_signals=False, >> vps_installer.spec
echo     strip=False, >> vps_installer.spec
echo     upx=True, >> vps_installer.spec
echo     upx_exclude=[], >> vps_installer.spec
echo     runtime_tmpdir=None, >> vps_installer.spec
echo     console=True, >> vps_installer.spec
echo     disable_windowed_traceback=False, >> vps_installer.spec
echo     argv_emulation=False, >> vps_installer.spec
echo     target_arch=None, >> vps_installer.spec
echo     codesign_identity=None, >> vps_installer.spec
echo     entitlements_file=None, >> vps_installer.spec
echo     icon=None, >> vps_installer.spec
echo     version_file=None >> vps_installer.spec
echo ) >> vps_installer.spec

echo ✅ Configurazione PyInstaller creata
echo.

:: Build the executable
echo [STEP 5] Costruzione eseguibile...
echo ⚡ Questa operazione può richiedere 5-10 minuti...
echo.

pyinstaller vps_installer.spec --clean --noconfirm --log-level INFO

:: Check build result
echo.
echo [STEP 6] Verifica risultato build...

if exist "dist\VPS_AI_Trading_Installer.exe" (
    echo.
    echo ========================================================================
    echo                           🎉 BUILD COMPLETATO! 🎉
    echo ========================================================================
    echo.
    echo ✅ Eseguibile creato con successo!
    echo.
    echo 📁 Percorso file: %CD%\dist\VPS_AI_Trading_Installer.exe
    echo 📏 Dimensione file:
    for %%A in ("dist\VPS_AI_Trading_Installer.exe") do echo    %%~zA bytes (%%~zA:~0,-3% KB)
    echo.
    echo 🚀 ISTRUZIONI D'USO:
    echo.
    echo 1. 📋 Copia VPS_AI_Trading_Installer.exe sulla tua VPS Windows
    echo 2. ✅ Assicurati che MetaTrader 5 sia installato sulla VPS
    echo 3. 🔧 Esegui VPS_AI_Trading_Installer.exe come Amministratore
    echo 4. ⚙️  Segui le istruzioni per configurazione automatica
    echo 5. 🎯 Il sistema configurerà tutto automaticamente
    echo.
    echo 💡 FEATURES INCLUSE:
    echo    • Installazione automatica dipendenze Python
    echo    • Configurazione ambiente .env_vps
    echo    • Test connessione MetaTrader 5
    echo    • Creazione servizi Windows
    echo    • Setup collegamento con Railway frontend
    echo    • Monitoraggio sistema completo
    echo.
    echo 🔧 MODALITÀ DISPONIBILI:
    echo    • Menu interattivo ^(default^)
    echo    • Modalità automatica ^(--auto^)
    echo    • Background service ^(--service^)
    echo.
    echo 📞 SUPPORTO:
    echo    • README_VPS.md per documentazione completa
    echo    • Log files per troubleshooting
    echo    • Controlli automatici di sistema
    echo.
    echo ========================================================================
    echo.
    echo 🎯 DISTRIBUZIONE:
    echo    L'installer è pronto per essere distribuito su qualsiasi VPS Windows
    echo    con MetaTrader 5. Include tutto il necessario per setup completo.
    echo.
    echo ========================================================================
    
) else (
    echo.
    echo ========================================================================
    echo                              ❌ BUILD FALLITO
    echo ========================================================================
    echo.
    echo Build non riuscito! Possibili cause:
    echo.
    echo • Dipendenze mancanti - controllare requirements_vps.txt
    echo • Errori Python - verificare versione Python 3.8+
    echo • File mancanti - verificare tutti i file necessari siano presenti
    echo • Spazio disco insufficiente
    echo • Permessi insufficienti - eseguire come Amministratore
    echo.
    echo Controlla l'output sopra per dettagli specifici dell'errore.
    echo.
    echo ========================================================================
)

echo.
echo 🔄 Pulizia file temporanei...
if exist "*.spec" del "*.spec"
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo ========================================================================
echo Build process completato. Controllare cartella dist/ per il risultato.
echo ========================================================================

pause