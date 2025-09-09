#!/usr/bin/env python3
"""
Sistema di diagnostica completa per VPS AI Trading System
Controlla tutti i componenti e genera report dettagliato
"""

import os
import sys
import json
import requests
import platform
import subprocess
from datetime import datetime
from pathlib import Path

def print_header(title):
    """Print sezione header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_status(item, status, details=""):
    """Print status con colori"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {item:<30} {'OK' if status else 'FAIL'}")
    if details:
        print(f"   └─ {details}")

def check_python():
    """Controlla Python e versione"""
    print_header("🐍 CONTROLLO PYTHON")
    
    version = sys.version_info
    python_ok = version.major == 3 and version.minor >= 8
    
    print_status(
        "Python Version", 
        python_ok, 
        f"v{version.major}.{version.minor}.{version.micro}"
    )
    
    # Check pip
    try:
        import pip
        pip_version = pip.__version__
        print_status("Pip Available", True, f"v{pip_version}")
    except ImportError:
        print_status("Pip Available", False, "Not found")
    
    return python_ok

def check_required_packages():
    """Controlla pacchetti richiesti"""
    print_header("📦 CONTROLLO DIPENDENZE PYTHON")
    
    required_packages = [
        ("MetaTrader5", "MetaTrader5"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("requests", "Requests"),
        ("psutil", "PSUtil"),
        ("dotenv", "Python-dotenv"),
        ("sqlalchemy", "SQLAlchemy")
    ]
    
    missing_packages = []
    
    for package_name, display_name in required_packages:
        try:
            __import__(package_name)
            print_status(display_name, True, "Available")
        except ImportError:
            print_status(display_name, False, "Missing")
            missing_packages.append(package_name)
    
    return len(missing_packages) == 0, missing_packages

def check_mt5():
    """Controlla MetaTrader 5"""
    print_header("🎮 CONTROLLO METATRADER 5")
    
    # Check MT5 installation
    mt5_paths = [
        "C:/Program Files/MetaTrader 5/terminal64.exe",
        "C:/Program Files (x86)/MetaTrader 5/terminal64.exe"
    ]
    
    mt5_installed = False
    for path in mt5_paths:
        if os.path.exists(path):
            mt5_installed = True
            print_status("MT5 Installation", True, path)
            break
    
    if not mt5_installed:
        print_status("MT5 Installation", False, "Not found in standard locations")
    
    # Check MT5 Python connection
    try:
        import MetaTrader5 as mt5
        
        if mt5.initialize():
            print_status("MT5 Python Module", True, "Connection successful")
            
            # Get account info if available
            account_info = mt5.account_info()
            if account_info:
                print_status("MT5 Account", True, f"Login: {account_info.login}")
                print_status("MT5 Server", True, f"Server: {account_info.server}")
                print_status("MT5 Balance", True, f"Balance: {account_info.balance}")
            else:
                print_status("MT5 Account", False, "No account configured")
            
            mt5.shutdown()
            mt5_connected = True
        else:
            print_status("MT5 Python Module", False, "Cannot initialize")
            mt5_connected = False
    except ImportError:
        print_status("MT5 Python Module", False, "Module not available")
        mt5_connected = False
    except Exception as e:
        print_status("MT5 Python Module", False, str(e))
        mt5_connected = False
    
    return mt5_installed and mt5_connected

def check_files():
    """Controlla file necessari"""
    print_header("📁 CONTROLLO FILE SISTEMA")
    
    required_files = [
        ("vps_auto_launcher.py", "Main Launcher"),
        ("vps_main_server.py", "Main Server"),
        ("signal_engine.py", "Signal Engine"),
        ("requirements_vps.txt", "Requirements"),
        (".env_vps", "Environment Config"),
        ("mt5_bridge_vps/main_bridge.py", "MT5 Bridge")
    ]
    
    missing_files = []
    
    for filename, display_name in required_files:
        file_path = Path(filename)
        exists = file_path.exists()
        
        if exists:
            size = file_path.stat().st_size
            print_status(display_name, True, f"{size} bytes")
        else:
            print_status(display_name, False, "File not found")
            missing_files.append(filename)
    
    return len(missing_files) == 0, missing_files

def check_environment():
    """Controlla configurazione ambiente"""
    print_header("⚙️ CONTROLLO CONFIGURAZIONE")
    
    env_file = Path(".env_vps")
    if not env_file.exists():
        print_status("Environment File", False, ".env_vps not found")
        return False
    
    print_status("Environment File", True, "Found")
    
    # Read and check key variables
    try:
        from dotenv import load_dotenv
        load_dotenv('.env_vps')
        
        required_vars = [
            ("MT5_BROKER_SERVER", "MetaTrader 5 Server"),
            ("MT5_LOGIN", "MetaTrader 5 Login"),
            ("MT5_PASSWORD", "MetaTrader 5 Password"),
            ("RAILWAY_FRONTEND_URL", "Railway Frontend URL"),
            ("GEMINI_API_KEY", "Gemini API Key"),
            ("VPS_API_KEY", "VPS API Key")
        ]
        
        missing_vars = []
        for var_name, display_name in required_vars:
            value = os.getenv(var_name)
            if value and value not in ["", "your_", "change_this", "123456", "password123"]:
                # Mask sensitive data
                if "password" in var_name.lower() or "key" in var_name.lower():
                    masked_value = "*" * len(value)
                elif var_name == "MT5_LOGIN":
                    masked_value = value
                else:
                    masked_value = value[:20] + "..." if len(value) > 20 else value
                
                print_status(display_name, True, masked_value)
            else:
                print_status(display_name, False, "Not configured or using default")
                missing_vars.append(var_name)
        
        return len(missing_vars) == 0
        
    except ImportError:
        print_status("Dotenv Module", False, "python-dotenv not available")
        return False

def check_network():
    """Controlla connettività di rete"""
    print_header("🌐 CONTROLLO CONNETTIVITÀ")
    
    # Check Railway connection
    try:
        from dotenv import load_dotenv
        load_dotenv('.env_vps')
        railway_url = os.getenv("RAILWAY_FRONTEND_URL")
        
        if railway_url and not railway_url.startswith("https://your-"):
            response = requests.get(f"{railway_url}/health", timeout=10)
            print_status("Railway Frontend", True, f"{response.status_code} - {railway_url}")
        else:
            print_status("Railway Frontend", False, "URL not configured")
    except Exception as e:
        print_status("Railway Frontend", False, str(e))
    
    # Check local ports
    try:
        import socket
        
        # Check if ports are available
        ports_to_check = [8000, 8001]
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                print_status(f"Port {port}", False, "Already in use")
            else:
                print_status(f"Port {port}", True, "Available")
    except Exception as e:
        print_status("Port Check", False, str(e))

def check_system_resources():
    """Controlla risorse sistema"""
    print_header("💻 CONTROLLO RISORSE SISTEMA")
    
    # OS Info
    os_info = platform.system() + " " + platform.release()
    print_status("Operating System", True, os_info)
    
    # Memory
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = round(memory.total / (1024**3), 1)
        memory_used_percent = memory.percent
        
        memory_ok = memory_gb >= 4  # Minimum 4GB
        print_status(
            "System Memory", 
            memory_ok, 
            f"{memory_gb}GB total, {memory_used_percent}% used"
        )
        
        # CPU
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_ok = cpu_count >= 2  # Minimum 2 cores
        
        print_status(
            "CPU Cores",
            cpu_ok,
            f"{cpu_count} cores, {cpu_percent}% usage"
        )
        
        # Disk Space
        disk = psutil.disk_usage('.')
        disk_free_gb = round(disk.free / (1024**3), 1)
        disk_ok = disk_free_gb >= 5  # Minimum 5GB free
        
        print_status(
            "Disk Space",
            disk_ok,
            f"{disk_free_gb}GB free"
        )
        
        return memory_ok and cpu_ok and disk_ok
        
    except ImportError:
        print_status("Resource Check", False, "psutil not available")
        return False

def generate_report():
    """Genera report completo sistema"""
    print_header("📊 REPORT DIAGNOSTICA COMPLETA")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "os": platform.system() + " " + platform.release(),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "architecture": platform.architecture()[0]
        },
        "checks": {}
    }
    
    # Run all checks
    checks = [
        ("python", check_python),
        ("packages", lambda: check_required_packages()[0]),
        ("mt5", check_mt5),
        ("files", lambda: check_files()[0]),
        ("environment", check_environment),
        ("resources", check_system_resources)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            report["checks"][check_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            report["checks"][check_name] = False
            print_status(f"{check_name} check", False, str(e))
            all_passed = False
    
    report["overall_status"] = all_passed
    
    # Save report
    report_file = Path("diagnostic_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print_status("Diagnostic Report", True, str(report_file))
    
    return all_passed, report

def print_recommendations(report):
    """Stampa raccomandazioni basate sui risultati"""
    print_header("💡 RACCOMANDAZIONI")
    
    if not report["checks"].get("python", True):
        print("🔧 PYTHON: Installa Python 3.8+ da python.org")
    
    if not report["checks"].get("packages", True):
        print("🔧 DIPENDENZE: Esegui 'pip install -r requirements_vps.txt'")
    
    if not report["checks"].get("mt5", True):
        print("🔧 MT5: Installa MetaTrader 5 e configura un account")
    
    if not report["checks"].get("files", True):
        print("🔧 FILE: Verifica che tutti i file siano presenti nella directory")
    
    if not report["checks"].get("environment", True):
        print("🔧 CONFIG: Modifica .env_vps con i tuoi dati reali")
    
    if not report["checks"].get("resources", True):
        print("🔧 SISTEMA: Considera upgrade RAM/CPU per prestazioni ottimali")
    
    if report["overall_status"]:
        print("\n🎉 SISTEMA PRONTO!")
        print("   Puoi avviare il sistema con: python vps_auto_launcher.py")
    else:
        print("\n⚠️  CORREGGERE I PROBLEMI SOPRA PRIMA DI AVVIARE")

def main():
    """Funzione principale"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                VPS AI TRADING SYSTEM                         ║
║                  DIAGNOSTIC CHECKER                          ║
║                                                              ║
║  🔍 Controllo completo sistema e componenti                  ║
║  📊 Generazione report dettagliato                          ║
║  💡 Raccomandazioni automatiche                             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Run complete diagnosis
        all_passed, report = generate_report()
        
        # Network check (separate as it might fail)
        try:
            check_network()
        except Exception as e:
            print_status("Network Check", False, str(e))
        
        # Print recommendations
        print_recommendations(report)
        
        # Final status
        print_header("🏁 RISULTATO FINALE")
        if all_passed:
            print("✅ SISTEMA COMPLETAMENTE FUNZIONANTE")
            print("   Ready per trading automatico!")
        else:
            print("❌ SISTEMA RICHIEDE CONFIGURAZIONE")
            print("   Seguire le raccomandazioni sopra")
        
        print(f"\n📄 Report completo salvato in: diagnostic_report.json")
        print(f"🕒 Controllo completato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE DIAGNOSTICA: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())