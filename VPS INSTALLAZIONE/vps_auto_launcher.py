#!/usr/bin/env python3
"""
🚀 VPS AUTO LAUNCHER - AI TRADING SYSTEM
Automated setup and launch for complete VPS trading system
"""

import os
import sys
import time
import subprocess
import threading
import logging
import json
import requests
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vps_launcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VPSAutoLauncher:
    """Automated VPS Trading System Launcher"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.processes = {}
        self.config = {}
        self.is_running = False
        self.monitor_thread = None
        
    def print_banner(self):
        """Print startup banner"""
        banner = """
        ╔══════════════════════════════════════════════════════════════╗
        ║                    🚀 VPS AUTO LAUNCHER                      ║
        ║                   AI TRADING SYSTEM v1.0                    ║
        ║                                                              ║
        ║  🤖 Automated MT5 Signal Generation                         ║
        ║  📊 Machine Learning Trading Analysis                       ║
        ║  🔄 Auto-restart & Health Monitoring                        ║
        ║  🛡️  Complete System Automation                             ║
        ╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        logger.info("VPS Auto Launcher iniziato")

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed"""
        logger.info("Controllo prerequisiti sistema...")
        
        # Check Python
        if sys.version_info < (3, 8):
            logger.error("Python 3.8+ richiesto")
            return False
            
        # Check required files
        required_files = [
            'main_vps.py', 'signal_engine.py', 'mt5_bridge_server.py',
            'requirements_vps.txt', '.env_vps'
        ]
        
        for file in required_files:
            if not (self.base_dir / file).exists():
                logger.warning(f"File mancante: {file}")
                
        # Check MT5
        try:
            import MetaTrader5 as mt5
            logger.info("✅ MetaTrader5 disponibile")
        except ImportError:
            logger.error("❌ MetaTrader5 non installato")
            return False
            
        return True

    def install_dependencies(self):
        """Install required Python packages"""
        logger.info("Installazione dipendenze...")
        
        req_file = self.base_dir / 'requirements_vps.txt'
        if req_file.exists():
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(req_file)], 
                             check=True, capture_output=True)
                logger.info("✅ Dipendenze installate")
            except subprocess.CalledProcessError as e:
                logger.error(f"Errore installazione: {e}")
        else:
            # Install essential packages
            packages = [
                'MetaTrader5>=5.0.5260',
                'fastapi>=0.104.0',
                'uvicorn>=0.24.0',
                'pandas>=2.0.0',
                'numpy>=1.24.0',
                'sqlalchemy>=2.0.0',
                'TA-Lib>=0.6.7',
                'google-generativeai>=0.8.5',
                'psutil>=5.9.0',
                'requests>=2.31.0'
            ]
            
            for package in packages:
                try:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                 check=True, capture_output=True)
                    logger.info(f"✅ Installato: {package}")
                except subprocess.CalledProcessError:
                    logger.warning(f"⚠️  Errore installazione: {package}")

    def setup_environment(self):
        """Setup environment configuration"""
        logger.info("Configurazione ambiente...")
        
        env_file = self.base_dir / '.env_vps'
        if not env_file.exists():
            # Create default .env_vps
            default_env = """# VPS Trading System Configuration
MT5_BROKER_SERVER=MetaQuotes-Demo
MT5_LOGIN=123456
MT5_PASSWORD=password123
MT5_BRIDGE_PORT=8000
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_VPS_URL=sqlite:///vps_trading.db
LOG_LEVEL=INFO
BRIDGE_HOST=0.0.0.0
MAX_SIGNALS_PER_HOUR=5
MIN_RELIABILITY_THRESHOLD=70
"""
            env_file.write_text(default_env)
            logger.info("✅ File .env_vps creato")
            logger.warning("⚠️  CONFIGURARE .env_vps con i tuoi dati MT5!")

    def create_required_files(self):
        """Create missing required files"""
        logger.info("Creazione file necessari...")
        
        # Create main_vps.py if missing
        main_vps_file = self.base_dir / 'main_vps.py'
        if not main_vps_file.exists():
            main_vps_content = '''#!/usr/bin/env python3
"""
VPS Main Server - AI Trading System
"""
import asyncio
import logging
from signal_engine import SignalEngine
from mt5_bridge_server import MT5BridgeServer

async def main():
    """Main VPS application"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Avvio VPS Trading System...")
    
    # Start Signal Engine
    signal_engine = SignalEngine()
    await signal_engine.start()
    
    logger.info("✅ Sistema VPS avviato con successo")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
            logger.info("💚 Sistema VPS attivo")
    except KeyboardInterrupt:
        logger.info("🛑 Arresto sistema VPS...")
        await signal_engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
'''
            main_vps_file.write_text(main_vps_content)
            logger.info("✅ main_vps.py creato")

    def check_mt5_connection(self) -> bool:
        """Check MT5 connection"""
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                logger.error("❌ MT5 initialize fallito")
                return False
                
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("❌ MT5 non connesso")
                mt5.shutdown()
                return False
                
            logger.info(f"✅ MT5 connesso - Account: {account_info.login}")
            mt5.shutdown()
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore connessione MT5: {e}")
            return False

    def start_process(self, name: str, command: List[str], cwd: Optional[str] = None) -> bool:
        """Start a system process"""
        try:
            logger.info(f"Avvio {name}...")
            
            process = subprocess.Popen(
                command,
                cwd=cwd or str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = {
                'process': process,
                'command': command,
                'start_time': datetime.now(),
                'restart_count': 0
            }
            
            logger.info(f"✅ {name} avviato (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore avvio {name}: {e}")
            return False

    def stop_process(self, name: str):
        """Stop a system process"""
        if name in self.processes:
            process_info = self.processes[name]
            process = process_info['process']
            
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"🛑 {name} arrestato")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"⚡ {name} terminato forzatamente")
            except Exception as e:
                logger.error(f"❌ Errore arresto {name}: {e}")
            
            del self.processes[name]

    def restart_process(self, name: str):
        """Restart a system process"""
        logger.info(f"🔄 Riavvio {name}...")
        
        if name in self.processes:
            command = self.processes[name]['command']
            restart_count = self.processes[name]['restart_count']
            
            self.stop_process(name)
            time.sleep(2)
            
            if self.start_process(name, command):
                self.processes[name]['restart_count'] = restart_count + 1
                logger.info(f"✅ {name} riavviato (#{restart_count + 1})")

    def monitor_processes(self):
        """Monitor all processes and restart if needed"""
        logger.info("🔍 Avvio monitoraggio processi...")
        
        while self.is_running:
            try:
                for name, info in list(self.processes.items()):
                    process = info['process']
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        logger.warning(f"⚠️  {name} non risponde - riavvio...")
                        self.restart_process(name)
                
                # Health check every 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Errore monitoraggio: {e}")
                time.sleep(10)

    def start_system(self):
        """Start complete VPS trading system"""
        logger.info("🚀 Avvio sistema completo...")
        
        # 1. Start MT5 Bridge Server
        if (self.base_dir / 'mt5_bridge_server.py').exists():
            self.start_process('MT5_Bridge', [sys.executable, 'mt5_bridge_server.py'])
            time.sleep(3)
        
        # 2. Start Main VPS Server
        if (self.base_dir / 'main_vps.py').exists():
            self.start_process('Main_VPS', [sys.executable, 'main_vps.py'])
            time.sleep(2)
        
        # 3. Start Signal Engine (if separate)
        if (self.base_dir / 'signal_engine.py').exists():
            # Check if it's a standalone script
            with open(self.base_dir / 'signal_engine.py', 'r') as f:
                content = f.read()
                if '__name__ == "__main__"' in content:
                    self.start_process('Signal_Engine', [sys.executable, 'signal_engine.py'])
        
        logger.info("✅ Tutti i servizi avviati")

    def stop_system(self):
        """Stop complete system"""
        logger.info("🛑 Arresto sistema...")
        
        self.is_running = False
        
        # Stop all processes
        for name in list(self.processes.keys()):
            self.stop_process(name)
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("✅ Sistema arrestato completamente")

    def show_status(self):
        """Show system status"""
        print("\n" + "="*60)
        print("📊 STATO SISTEMA VPS")
        print("="*60)
        
        if not self.processes:
            print("❌ Nessun processo attivo")
            return
        
        for name, info in self.processes.items():
            process = info['process']
            start_time = info['start_time']
            restart_count = info['restart_count']
            
            if process.poll() is None:
                status = "🟢 ATTIVO"
                uptime = datetime.now() - start_time
                uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            else:
                status = "🔴 ARRESTATO"
                uptime_str = "N/A"
            
            print(f"{name:15} {status} | Uptime: {uptime_str} | Riavvii: {restart_count}")
        
        print("="*60)

    def run_interactive(self):
        """Run in interactive mode"""
        self.print_banner()
        
        while True:
            print("\n" + "="*50)
            print("🎮 VPS TRADING SYSTEM - MENU CONTROLLO")
            print("="*50)
            print("1. 🚀 Avvia Sistema Completo")
            print("2. 🛑 Arresta Sistema")
            print("3. 📊 Mostra Stato")
            print("4. 🔄 Riavvia Servizio")
            print("5. ⚙️  Configurazione")
            print("6. 🔍 Test Connessione MT5")
            print("7. 📝 Visualizza Log")
            print("0. ❌ Esci")
            
            try:
                choice = input("\n👉 Scegli opzione: ").strip()
                
                if choice == '1':
                    if not self.is_running:
                        self.is_running = True
                        self.start_system()
                        self.monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
                        self.monitor_thread.start()
                    else:
                        print("⚠️  Sistema già avviato")
                
                elif choice == '2':
                    self.stop_system()
                
                elif choice == '3':
                    self.show_status()
                
                elif choice == '4':
                    if self.processes:
                        print("\nServizi attivi:")
                        for i, name in enumerate(self.processes.keys(), 1):
                            print(f"{i}. {name}")
                        
                        try:
                            svc_num = int(input("Numero servizio da riavviare: ")) - 1
                            svc_name = list(self.processes.keys())[svc_num]
                            self.restart_process(svc_name)
                        except (ValueError, IndexError):
                            print("❌ Scelta non valida")
                    else:
                        print("❌ Nessun servizio attivo")
                
                elif choice == '5':
                    print("\n⚙️  Configurazione sistema...")
                    env_file = self.base_dir / '.env_vps'
                    if env_file.exists():
                        print(f"📝 Modifica: {env_file}")
                        os.system(f'notepad "{env_file}"')
                    else:
                        print("❌ File .env_vps non trovato")
                
                elif choice == '6':
                    print("\n🔍 Test connessione MT5...")
                    if self.check_mt5_connection():
                        print("✅ MT5 connesso correttamente!")
                    else:
                        print("❌ Problema connessione MT5")
                
                elif choice == '7':
                    log_file = self.base_dir / 'vps_launcher.log'
                    if log_file.exists():
                        print(f"\n📝 Ultimi log dal file: {log_file}")
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            for line in lines[-20:]:  # Last 20 lines
                                print(line.rstrip())
                    else:
                        print("❌ File log non trovato")
                
                elif choice == '0':
                    print("\n👋 Arresto sistema ed uscita...")
                    self.stop_system()
                    break
                
                else:
                    print("❌ Scelta non valida")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupt ricevuto - arresto sistema...")
                self.stop_system()
                break
            except Exception as e:
                logger.error(f"❌ Errore menu: {e}")

    def run_auto(self):
        """Run in automatic mode"""
        self.print_banner()
        logger.info("🤖 Modalità automatica attivata")
        
        try:
            self.is_running = True
            self.start_system()
            
            # Start monitoring
            self.monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            self.monitor_thread.start()
            
            # Keep running
            while self.is_running:
                time.sleep(60)
                logger.info("💚 Sistema VPS operativo")
                
        except KeyboardInterrupt:
            logger.info("🛑 Interrupt ricevuto")
        finally:
            self.stop_system()

def main():
    """Main entry point"""
    launcher = VPSAutoLauncher()
    
    # Check prerequisites
    if not launcher.check_prerequisites():
        print("❌ Prerequisiti mancanti - installare MT5 e Python 3.8+")
        return 1
    
    # Setup
    launcher.install_dependencies()
    launcher.setup_environment()
    launcher.create_required_files()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            launcher.run_auto()
        elif sys.argv[1] == '--status':
            launcher.show_status()
        elif sys.argv[1] == '--start':
            launcher.is_running = True
            launcher.start_system()
            launcher.monitor_thread = threading.Thread(target=launcher.monitor_processes, daemon=True)
            launcher.monitor_thread.start()
            print("✅ Sistema avviato in background")
        elif sys.argv[1] == '--stop':
            # Find and stop existing processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if any('vps_auto_launcher.py' in str(cmd) for cmd in proc.info['cmdline'] or []):
                        proc.terminate()
                        print(f"🛑 Processo arrestato: {proc.pid}")
                except:
                    pass
        else:
            print("Opzioni: --auto, --status, --start, --stop")
    else:
        # Interactive mode
        launcher.run_interactive()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())