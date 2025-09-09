#!/usr/bin/env python3
"""
VPS Main Server - AI Trading System
Collega il sistema VPS al frontend Railway per generazione segnali
"""

import os
import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from signal_engine import ProfessionalSignalEngine
from ml_data_storage import get_ml_storage
from auto_trader import get_auto_trader
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Load environment
load_dotenv('.env_vps')

# Configuration
RAILWAY_FRONTEND_URL = os.getenv("RAILWAY_FRONTEND_URL", "https://your-railway-app.railway.app")
# Usa MT5_SECRET_KEY come chiave API per Railway
VPS_API_KEY = os.getenv("MT5_SECRET_KEY", "vps-secret-key-change-this")
MT5_BRIDGE_PORT = int(os.getenv("MT5_BRIDGE_PORT", "8000"))
VPS_SERVER_PORT = int(os.getenv("VPS_SERVER_PORT", "8001"))

# Signal reliability thresholds
MIN_RELIABILITY_THRESHOLD = int(os.getenv("MIN_RELIABILITY_THRESHOLD", "55"))  # Send threshold
ML_DATA_THRESHOLD = int(os.getenv("ML_DATA_THRESHOLD", "70"))  # ML storage threshold

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vps_main_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="VPS AI Trading Server",
    description="VPS server per generazione segnali AI collegato al frontend Railway",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
signal_engine = None
last_signals = []

class VPSMainServer:
    """
    Server principale VPS che coordina:
    - Connessione a MT5 tramite bridge
    - Generazione segnali AI
    - Comunicazione con frontend Railway
    - Monitoraggio sistema
    """
    
    def __init__(self):
        self.signal_engine = ProfessionalSignalEngine()
        self.ml_storage = get_ml_storage()
        self.auto_trader = get_auto_trader()
        self.is_running = False
        self.last_heartbeat = datetime.now()
        self.signals_generated = 0
        self.errors_count = 0
        
    async def start_system(self):
        """Avvia tutto il sistema VPS"""
        logger.info("🚀 Avvio VPS Main Server...")
        
        try:
            # 1. Test MT5 Bridge connection
            logger.info("Testando connessione MT5 Bridge...")
            bridge_status = await self.test_mt5_bridge()
            if not bridge_status:
                logger.warning("⚠️ MT5 Bridge non disponibile - alcuni segnali potrebbero non funzionare")
            
            # 2. Initialize Signal Engine
            logger.info("Inizializzazione Signal Engine...")
            success = await self.signal_engine.initialize()
            if not success:
                raise Exception("Fallimento inizializzazione Signal Engine")
            
            # 3. Initialize AutoTrader for ML
            logger.info("Inizializzazione AutoTrader per ML...")
            if self.auto_trader.connect_mt5():
                logger.info("✅ AutoTrader connesso per trading automatico ML")
            else:
                logger.warning("⚠️ AutoTrader non connesso - trading ML disabilitato")
            
            # 3. Test Railway Frontend connection
            logger.info("Testando connessione Railway Frontend...")
            frontend_status = await self.test_railway_connection()
            if not frontend_status:
                logger.warning("⚠️ Frontend Railway non raggiungibile")
            
            self.is_running = True
            logger.info("✅ VPS Main Server avviato con successo!")
            
            # Start background tasks
            asyncio.create_task(self.heartbeat_loop())
            asyncio.create_task(self.signal_generation_loop())
            asyncio.create_task(self.trade_monitoring_loop())
            
        except Exception as e:
            logger.error(f"❌ Errore avvio sistema: {e}")
            raise
    
    async def test_mt5_bridge(self) -> bool:
        """Test connessione al MT5 Bridge"""
        try:
            response = requests.get(f"http://localhost:{MT5_BRIDGE_PORT}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ MT5 Bridge connesso")
                return True
        except Exception as e:
            logger.warning(f"⚠️ MT5 Bridge non disponibile: {e}")
        return False
    
    async def test_railway_connection(self) -> bool:
        """Test connessione al frontend Railway"""
        try:
            response = requests.get(f"{RAILWAY_FRONTEND_URL}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Frontend Railway raggiungibile")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Frontend Railway non raggiungibile: {e}")
        return False
    
    async def heartbeat_loop(self):
        """Loop di heartbeat verso il frontend"""
        while self.is_running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(60)  # Heartbeat ogni minuto
            except Exception as e:
                logger.error(f"Errore heartbeat: {e}")
                self.errors_count += 1
                await asyncio.sleep(30)
    
    async def send_heartbeat(self):
        """Invia heartbeat al frontend Railway"""
        try:
            heartbeat_data = {
                "vps_id": "vps-001",
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "signals_generated": self.signals_generated,
                "errors_count": self.errors_count,
                "uptime_seconds": int((datetime.now() - self.last_heartbeat).total_seconds())
            }
            
            response = requests.post(
                f"{RAILWAY_FRONTEND_URL}/api/vps/heartbeat",
                json=heartbeat_data,
                headers={"X-VPS-API-Key": VPS_API_KEY},
                timeout=10
            )
            
            if response.status_code == 200:
                self.last_heartbeat = datetime.now()
                logger.debug("💚 Heartbeat inviato con successo")
            else:
                logger.warning(f"⚠️ Heartbeat fallito: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Errore invio heartbeat: {e}")
    
    async def signal_generation_loop(self):
        """Loop principale generazione segnali"""
        while self.is_running:
            try:
                # Verifica orari di mercato
                if not self._is_market_open():
                    logger.info("🕐 Generazione segnali sospesa: mercati chiusi")
                    await asyncio.sleep(3600)  # Check ogni ora quando chiuso
                    continue
                
                await self.generate_and_send_signals()
                await asyncio.sleep(300)  # Genera segnali ogni 5 minuti
            except Exception as e:
                logger.error(f"Errore generazione segnali: {e}")
                self.errors_count += 1
                await asyncio.sleep(60)
    
    async def generate_and_send_signals(self):
        """Genera segnali e li invia al frontend"""
        try:
            logger.info("🔄 Generazione nuovi segnali...")
            
            # Simboli principali per trading (Forex + Commodities + Indices)
            symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD", "US30", "NAS100", "SPX500"]
            
            for symbol in symbols:
                try:
                    # Genera segnale
                    signal = await self.signal_engine.generate_complete_signal(symbol)
                    
                    if signal:
                        reliability = signal.get('reliability', 0)
                        
                        # Logica doppia soglia + AutoTrading
                        # 1. Archivia per ML se affidabilità ≥ 70%
                        if reliability >= ML_DATA_THRESHOLD:
                            success_ml = self.ml_storage.store_high_quality_signal(signal)
                            if success_ml:
                                logger.info(f"📚 Segnale {symbol} archiviato per ML ({reliability}%)")
                            
                            # Esegui trade automatico per ML data collection
                            if self.auto_trader.is_connected:
                                trade_result = self.auto_trader.execute_signal_trade(signal)
                                if trade_result:
                                    logger.info(f"🎯 Trade automatico eseguito per ML: {symbol} (Ticket: {trade_result.get('ticket')})")
                                else:
                                    logger.debug(f"Trade automatico non eseguito per {symbol}")
                        
                        # 2. Invia al frontend se affidabilità ≥ 55%
                        if reliability >= MIN_RELIABILITY_THRESHOLD:
                            success = await self.send_signal_to_frontend(signal)
                            if success:
                                self.signals_generated += 1
                                logger.info(f"✅ Segnale {symbol} inviato al frontend ({reliability}%)")
                            
                            # Salva localmente
                            global last_signals
                            last_signals.append(signal)
                            if len(last_signals) > 50:  # Mantieni solo ultimi 50
                                last_signals = last_signals[-50:]
                        else:
                            logger.info(f"⚠️ Segnale {symbol} scartato (affidabilità {reliability}% < {MIN_RELIABILITY_THRESHOLD}%)")
                            
                except Exception as e:
                    logger.error(f"Errore generazione segnale {symbol}: {e}")
                    
                # Pausa tra simboli
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Errore loop generazione segnali: {e}")
    
    async def trade_monitoring_loop(self):
        """Loop per monitoraggio e chiusura trade ML"""
        while self.is_running:
            try:
                # Pausa iniziale
                await asyncio.sleep(60)  # Controlla ogni minuto
                
                if not self.auto_trader.is_connected:
                    continue
                
                # Controlla trade chiusi per ML
                closed_trades = self.auto_trader.check_and_close_trades()
                
                if closed_trades:
                    for trade in closed_trades:
                        # Log risultato per ML
                        profit = trade.get('profit', 0)
                        symbol = trade.get('symbol')
                        was_profitable = trade.get('was_profitable', False)
                        duration = trade.get('duration_minutes', 0)
                        reliability = trade.get('reliability', 0)
                        
                        status_emoji = "✅" if was_profitable else "❌"
                        logger.info(f"{status_emoji} Trade ML completato: {symbol}")
                        logger.info(f"   P&L: ${profit:.2f} | Durata: {duration}min | Affidabilità originale: {reliability}%")
                        
                        # TODO: Qui si potrebbe implementare feedback per migliorare il signal engine
                        # in base ai risultati dei trade effettivi
                
                # Pulizia periodica dati vecchi (una volta al giorno)
                current_hour = datetime.now().hour
                if current_hour == 2:  # 2 AM cleanup
                    self.auto_trader.cleanup_old_trade_data(days_to_keep=30)
                    self.ml_storage.cleanup_old_data(days_to_keep=90)
                    
            except Exception as e:
                logger.error(f"Errore trade monitoring loop: {e}")
                await asyncio.sleep(10)  # Pausa prima di riprovare

    def _is_market_open(self) -> bool:
        """Verifica se i mercati sono aperti (no weekend)"""
        now = datetime.now()
        
        # Forex aperto dalla domenica sera al venerdì sera
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        if weekday == 5:  # Saturday - chiuso
            return False
        elif weekday == 6:  # Sunday
            # Aperto dalle 22:00 di domenica
            return now.hour >= 22
        elif weekday == 4:  # Friday  
            # Chiude alle 22:00 di venerdì
            return now.hour < 22
        else:
            # Lunedì-Giovedì sempre aperto
            return True

    async def send_signal_to_frontend(self, signal: Dict) -> bool:
        """Invia segnale al frontend Railway"""
        try:
            signal_data = {
                "vps_id": "vps-001",
                "signal": signal,
                "generated_at": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{RAILWAY_FRONTEND_URL}/api/signals/receive",
                json=signal_data,
                headers={"X-VPS-API-Key": VPS_API_KEY},
                timeout=15
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Invio segnale fallito: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Errore invio segnale: {e}")
            return False

# Global server instance
vps_server = VPSMainServer()

# API Endpoints
@app.get("/")
def root():
    return {
        "service": "VPS AI Trading Server",
        "version": "1.0.0",
        "status": "active" if vps_server.is_running else "stopped",
        "signals_generated": vps_server.signals_generated,
        "errors_count": vps_server.errors_count
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "vps_running": vps_server.is_running,
        "last_heartbeat": vps_server.last_heartbeat.isoformat(),
        "signals_generated": vps_server.signals_generated,
        "errors_count": vps_server.errors_count
    }

@app.get("/signals/latest")
def get_latest_signals():
    """Ottieni ultimi segnali generati"""
    return {
        "status": "success",
        "count": len(last_signals),
        "signals": last_signals[-10:]  # Ultimi 10 segnali
    }

@app.post("/signals/generate")
async def generate_signal_manual(symbol: str):
    """Genera segnale manualmente per un simbolo"""
    try:
        signal = await vps_server.signal_engine.generate_complete_signal(symbol)
        if signal:
            # Salva localmente
            last_signals.append(signal)
            
            # Doppia soglia anche per generazione manuale
            reliability = signal.get('reliability', 0)
            
            # Archivia per ML se affidabilità ≥ 70%
            if reliability >= ML_DATA_THRESHOLD:
                success_ml = vps_server.ml_storage.store_high_quality_signal(signal)
                if success_ml:
                    logger.info(f"📚 Segnale manuale {signal.get('symbol')} archiviato per ML ({reliability}%)")
            
            # Invia al frontend se affidabilità ≥ 55%
            if reliability >= MIN_RELIABILITY_THRESHOLD:
                await vps_server.send_signal_to_frontend(signal)
                vps_server.signals_generated += 1
            
            return {"status": "success", "signal": signal}
        else:
            return {"status": "error", "message": "Impossibile generare segnale"}
            
    except Exception as e:
        logger.error(f"Errore generazione manuale segnale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/start")
async def start_system():
    """Avvia il sistema VPS"""
    try:
        if not vps_server.is_running:
            await vps_server.start_system()
            return {"status": "success", "message": "Sistema VPS avviato"}
        else:
            return {"status": "success", "message": "Sistema già avviato"}
    except Exception as e:
        logger.error(f"Errore avvio sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/stop")
async def stop_system():
    """Ferma il sistema VPS"""
    vps_server.is_running = False
    return {"status": "success", "message": "Sistema VPS fermato"}

@app.get("/ml/stats")
def get_ml_stats():
    """Ottieni statistiche ML e trading automatico"""
    try:
        # Statistiche ML data storage
        ml_stats = vps_server.ml_storage.get_ml_stats()
        
        # Statistiche trading automatico
        trading_stats = vps_server.auto_trader.get_ml_trading_stats()
        
        # Trade attivi
        active_trades_count = len(vps_server.auto_trader.active_trades)
        
        return {
            "ml_data": ml_stats,
            "trading_performance": trading_stats,
            "active_trades": active_trades_count,
            "auto_trader_connected": vps_server.auto_trader.is_connected,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Errore recupero ML stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/trades/active")
def get_active_trades():
    """Ottieni lista trade attivi"""
    try:
        if not vps_server.auto_trader.is_connected:
            return {"error": "AutoTrader non connesso"}
        
        active_trades = []
        for ticket, trade_data in vps_server.auto_trader.active_trades.items():
            active_trades.append({
                "ticket": ticket,
                "symbol": trade_data.get('symbol'),
                "signal_type": trade_data.get('signal_type'),
                "reliability": trade_data.get('reliability'),
                "open_time": trade_data.get('open_time'),
                "open_price": trade_data.get('open_price')
            })
        
        return {
            "active_trades": active_trades,
            "count": len(active_trades),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Errore recupero trade attivi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def main():
    """Funzione principale"""
    logger.info("🚀 Avvio VPS AI Trading Server...")
    
    # Avvia sistema
    await vps_server.start_system()
    
    # Avvia server FastAPI
    logger.info(f"🌐 Server in ascolto su porta {VPS_SERVER_PORT}")
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=VPS_SERVER_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Sistema arrestato dall'utente")
    except Exception as e:
        logger.error(f"❌ Errore critico: {e}")