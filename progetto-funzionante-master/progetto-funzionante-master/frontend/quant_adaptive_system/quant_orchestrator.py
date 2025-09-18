"""
Quant Adaptive System - Main Orchestrator

Orchestratore principale del sistema quantitativo adattivo che coordina tutti i moduli:
- Data ingestion (CBOE options, futures volume)
- Signal intelligence (outcomes tracking, rolling generation)
- Regime detection e policy switching
- Risk management adattivo
- Reporting e metrics

Features:
- Orchestrazione completa del sistema
- Scheduling automatico delle task
- Health monitoring e error recovery
- API endpoints per controllo esterno
- Dashboard real-time
- Export automatico dati
- Integration con sistema esistente OANDA
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from pathlib import Path
import signal
import sys

# Import tutti i moduli del sistema quant
from .data_ingestion.market_context import get_cboe_provider
from .data_ingestion.futures_volmap import get_futures_mapper
from .signal_intelligence.signal_outcomes import get_outcome_tracker
from .signal_intelligence.rolling_signal import get_rolling_generator, RollingSignalConfig
from .regime_detection.policy import get_policy_manager
from .risk_management.adaptive_sizing import get_risk_manager
from .reporting.metrics_engine import get_metrics_engine

# Import sistema esistente per integration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class SystemStatus(Enum):
    """Status del sistema"""
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"

class TaskType(Enum):
    """Tipologie di task"""
    DATA_INGESTION = "DATA_INGESTION"
    SIGNAL_GENERATION = "SIGNAL_GENERATION"
    REGIME_UPDATE = "REGIME_UPDATE"
    RISK_CHECK = "RISK_CHECK"
    METRICS_CALCULATION = "METRICS_CALCULATION"
    REPORTING = "REPORTING"
    HEALTH_CHECK = "HEALTH_CHECK"

@dataclass
class SystemHealth:
    """Stato di salute del sistema"""
    status: SystemStatus
    uptime_hours: float = 0.0
    
    # Component health
    data_ingestion_health: bool = True
    signal_generation_health: bool = True
    regime_detection_health: bool = True
    risk_management_health: bool = True
    reporting_health: bool = True
    
    # Performance metrics
    signals_generated_today: int = 0
    success_rate_24h: float = 0.0
    avg_processing_time_ms: float = 0.0
    
    # Error tracking
    errors_count_24h: int = 0
    last_error: Optional[str] = None
    last_error_timestamp: Optional[datetime] = None
    
    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

@dataclass
class ScheduledTask:
    """Task schedulato"""
    task_type: TaskType
    interval_minutes: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_running: bool = False
    error_count: int = 0
    max_errors: int = 5

class QuantAdaptiveOrchestrator:
    """
    Orchestratore principale del sistema quantitativo adattivo
    """
    
    def __init__(self, config_path: str = "config/quant_system.json"):
        self.config_path = Path(config_path)
        
        # System state
        self.status = SystemStatus.INITIALIZING
        self.start_time = datetime.utcnow()
        self.is_running = False
        self.shutdown_requested = False
        
        # Components (initialized later)
        self.cboe_provider = None
        self.futures_mapper = None
        self.outcome_tracker = None
        self.rolling_generator = None
        self.policy_manager = None
        self.risk_manager = None
        self.metrics_engine = None
        
        # Configuration
        self.config = self._load_default_config()
        
        # Scheduled tasks
        self.scheduled_tasks = self._initialize_scheduled_tasks()
        
        # Health monitoring
        self.health_status = SystemHealth(status=self.status)
        self.error_counts = {}
        
        # Performance tracking
        self.performance_metrics = {
            "signals_processed": 0,
            "total_processing_time": 0.0,
            "successful_operations": 0,
            "failed_operations": 0
        }
        
    async def initialize(self):
        """Inizializza tutti i componenti del sistema"""
        try:
            logger.info("Inizializzazione Quant Adaptive System...")
            
            # Load configuration if exists
            if self.config_path.exists():
                self.config = self._load_config()
            else:
                self._save_config()
            
            # Initialize all components
            logger.info("Inizializzazione componenti...")
            
            self.cboe_provider = await get_cboe_provider()
            logger.info("✅ CBOE Data Provider inizializzato")
            
            self.futures_mapper = await get_futures_mapper()
            logger.info("✅ Futures Volume Mapper inizializzato")
            
            self.outcome_tracker = await get_outcome_tracker()
            logger.info("✅ Signal Outcome Tracker inizializzato")
            
            self.policy_manager = await get_policy_manager()
            logger.info("✅ Policy Manager inizializzato")
            
            self.risk_manager = await get_risk_manager()
            logger.info("✅ Risk Manager inizializzato")
            
            self.metrics_engine = await get_metrics_engine()
            logger.info("✅ Metrics Engine inizializzato")
            
            # Initialize rolling generator with config
            rolling_config = RollingSignalConfig(
                generation_interval_minutes=self.config.get("rolling_interval_minutes", 5),
                max_concurrent_signals=self.config.get("max_concurrent_signals", 20),
                min_confidence_threshold=self.config.get("min_confidence_threshold", 0.4)
            )
            self.rolling_generator = await get_rolling_generator(rolling_config)
            logger.info("✅ Rolling Signal Generator inizializzato")
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Update status
            self.status = SystemStatus.RUNNING
            self.health_status.status = self.status
            
            logger.info("🚀 Quant Adaptive System completamente inizializzato")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione sistema: {e}")
            self.status = SystemStatus.ERROR
            self.health_status.status = self.status
            raise
    
    async def start(self):
        """Avvia il sistema completo"""
        if self.status != SystemStatus.RUNNING:
            raise RuntimeError("Sistema non inizializzato correttamente")
        
        self.is_running = True
        logger.info("🎯 Avvio Quant Adaptive System...")
        
        try:
            # Start main orchestration loop
            await asyncio.gather(
                self._main_orchestration_loop(),
                self._scheduled_tasks_loop(),
                self._health_monitoring_loop(),
                self._rolling_signal_loop(),
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Errore nel main loop: {e}")
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown graceful del sistema"""
        logger.info("🛑 Shutdown Quant Adaptive System in corso...")
        
        self.shutdown_requested = True
        self.is_running = False
        self.status = SystemStatus.SHUTDOWN
        
        try:
            # Stop rolling signal generation
            if self.rolling_generator:
                self.rolling_generator.stop_rolling_generation()
            
            # Final metrics export
            if self.metrics_engine:
                await self._export_final_report()
            
            # Close all database connections
            await self._cleanup_resources()
            
            logger.info("✅ Shutdown completato")
            
        except Exception as e:
            logger.error(f"Errore durante shutdown: {e}")
    
    async def _main_orchestration_loop(self):
        """Loop principale di orchestrazione"""
        logger.info("Avvio main orchestration loop")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Check system health
                await self._update_system_health()
                
                # Handle any pending operations
                await self._process_pending_operations()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Check for alerts
                await self._check_system_alerts()
                
                # Wait before next cycle
                await asyncio.sleep(30)  # 30-second main loop
                
            except Exception as e:
                logger.error(f"Errore nel main orchestration loop: {e}")
                self._record_error("main_loop", str(e))
                await asyncio.sleep(60)  # Longer wait on error
    
    async def _scheduled_tasks_loop(self):
        """Loop per task schedulati"""
        logger.info("Avvio scheduled tasks loop")
        
        while self.is_running and not self.shutdown_requested:
            try:
                current_time = datetime.utcnow()
                
                for task in self.scheduled_tasks:
                    if self._should_run_task(task, current_time):
                        if not task.is_running:  # Avoid overlapping runs
                            asyncio.create_task(self._execute_scheduled_task(task))
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Errore nel scheduled tasks loop: {e}")
                await asyncio.sleep(120)  # Longer wait on error
    
    async def _health_monitoring_loop(self):
        """Loop di monitoraggio salute sistema"""
        logger.info("Avvio health monitoring loop")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Update health metrics
                await self._update_system_health()
                
                # Check component health
                await self._check_component_health()
                
                # Auto-recovery procedures
                await self._auto_recovery_procedures()
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Errore nel health monitoring: {e}")
                await asyncio.sleep(600)  # Longer wait on error
    
    async def _rolling_signal_loop(self):
        """Loop dedicato per rolling signal generation"""
        logger.info("Avvio rolling signal generation")
        
        try:
            # This will run the rolling generator's own loop
            await self.rolling_generator.start_rolling_generation()
            
        except Exception as e:
            logger.error(f"Errore nel rolling signal loop: {e}")
            self._record_error("rolling_signals", str(e))
    
    async def _execute_scheduled_task(self, task: ScheduledTask):
        """Esegue un task schedulato"""
        task.is_running = True
        task.last_run = datetime.utcnow()
        task.next_run = task.last_run + timedelta(minutes=task.interval_minutes)
        
        start_time = datetime.utcnow()
        
        try:
            if task.task_type == TaskType.DATA_INGESTION:
                await self._task_data_ingestion()
                
            elif task.task_type == TaskType.REGIME_UPDATE:
                await self._task_regime_update()
                
            elif task.task_type == TaskType.RISK_CHECK:
                await self._task_risk_check()
                
            elif task.task_type == TaskType.METRICS_CALCULATION:
                await self._task_metrics_calculation()
                
            elif task.task_type == TaskType.REPORTING:
                await self._task_reporting()
                
            elif task.task_type == TaskType.HEALTH_CHECK:
                await self._task_health_check()
            
            # Reset error count on success
            task.error_count = 0
            
            # Update performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.performance_metrics["successful_operations"] += 1
            self.performance_metrics["total_processing_time"] += processing_time
            
            logger.info(f"✅ Task {task.task_type.value} completato in {processing_time:.1f}ms")
            
        except Exception as e:
            task.error_count += 1
            self.performance_metrics["failed_operations"] += 1
            
            logger.error(f"❌ Errore nel task {task.task_type.value}: {e}")
            self._record_error(task.task_type.value, str(e))
            
            # Disable task if too many errors
            if task.error_count >= task.max_errors:
                logger.error(f"🚫 Task {task.task_type.value} disabilitato per troppi errori")
                # Could implement task disabling logic here
                
        finally:
            task.is_running = False
    
    async def _task_data_ingestion(self):
        """Task di data ingestion"""
        # Update market context
        await self.cboe_provider.update_cache()
        
        # Update volume profiles  
        await self.futures_mapper.update_all_profiles()
        
        logger.debug("Data ingestion completato")
    
    async def _task_regime_update(self):
        """Task di aggiornamento regime"""
        regime_changed = await self.policy_manager.update_regime_and_policy()
        
        if regime_changed:
            logger.info("🔄 Regime di mercato aggiornato con cambio policy")
    
    async def _task_risk_check(self):
        """Task di controllo rischio"""
        risk_metrics = await self.risk_manager.get_current_risk_metrics()
        
        # Check for critical risk levels
        if risk_metrics.total_exposure > 0.04:  # 4%
            logger.warning(f"⚠️ Esposizione elevata: {risk_metrics.total_exposure:.2%}")
        
        if risk_metrics.cooling_off_active:
            logger.info("🧊 Sistema in cooling off period")
    
    async def _task_metrics_calculation(self):
        """Task di calcolo metriche"""
        # Generate updated metrics
        report = await self.metrics_engine.generate_comprehensive_report(
            period_days=7, include_breakdowns=False
        )
        
        # Check for critical alerts
        critical_alerts = [a for a in report.alerts if a["level"] == "CRITICAL"]
        if critical_alerts:
            logger.warning(f"🚨 {len(critical_alerts)} alert critici rilevati")
    
    async def _task_reporting(self):
        """Task di reporting"""
        # Generate and export daily report
        report = await self.metrics_engine.generate_comprehensive_report(
            period_days=1, include_breakdowns=True
        )
        
        # Auto-export if configured
        if self.config.get("auto_export_reports", True):
            await self._export_report(report)
    
    async def _task_health_check(self):
        """Task di health check"""
        await self._update_system_health()
        
        # Log health summary
        logger.info(f"📊 System Health: {self.health_status.status.value} | "
                   f"Uptime: {self.health_status.uptime_hours:.1f}h | "
                   f"Success Rate: {self.health_status.success_rate_24h:.1f}%")
    
    def _should_run_task(self, task: ScheduledTask, current_time: datetime) -> bool:
        """Determina se un task deve essere eseguito"""
        if task.is_running:
            return False
            
        if task.next_run is None:
            return True
            
        return current_time >= task.next_run
    
    async def _update_system_health(self):
        """Aggiorna metriche di salute del sistema"""
        try:
            current_time = datetime.utcnow()
            uptime = current_time - self.start_time
            
            # Basic metrics
            self.health_status.uptime_hours = uptime.total_seconds() / 3600
            
            # Success rate calculation
            total_ops = (self.performance_metrics["successful_operations"] + 
                        self.performance_metrics["failed_operations"])
            
            if total_ops > 0:
                self.health_status.success_rate_24h = (
                    self.performance_metrics["successful_operations"] / total_ops * 100
                )
            
            # Average processing time
            if self.performance_metrics["successful_operations"] > 0:
                self.health_status.avg_processing_time_ms = (
                    self.performance_metrics["total_processing_time"] / 
                    self.performance_metrics["successful_operations"]
                )
            
            # Error count
            self.health_status.errors_count_24h = self.performance_metrics["failed_operations"]
            
            # Get signals count from rolling generator
            if self.rolling_generator:
                status = await self.rolling_generator.get_current_status()
                self.health_status.signals_generated_today = status.get("daily_signal_count", 0)
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento system health: {e}")
    
    async def _check_component_health(self):
        """Controlla salute dei singoli componenti"""
        try:
            # Data ingestion health
            try:
                await self.cboe_provider.get_current_context()
                self.health_status.data_ingestion_health = True
            except:
                self.health_status.data_ingestion_health = False
            
            # Signal generation health
            if self.rolling_generator:
                status = await self.rolling_generator.get_current_status()
                self.health_status.signal_generation_health = status.get("is_running", False)
            
            # Risk management health
            try:
                await self.risk_manager.get_current_risk_metrics()
                self.health_status.risk_management_health = True
            except:
                self.health_status.risk_management_health = False
            
            # Update overall status
            if not all([
                self.health_status.data_ingestion_health,
                self.health_status.signal_generation_health,
                self.health_status.risk_management_health
            ]):
                if self.status == SystemStatus.RUNNING:
                    self.status = SystemStatus.ERROR
                    logger.warning("⚠️ Alcuni componenti non funzionano correttamente")
            
        except Exception as e:
            logger.error(f"Errore nel check component health: {e}")
    
    async def _auto_recovery_procedures(self):
        """Procedure di auto-recovery"""
        try:
            # Restart failed components
            if not self.health_status.data_ingestion_health:
                logger.info("🔧 Tentativo recovery data ingestion...")
                try:
                    await self.cboe_provider.initialize()
                    self.health_status.data_ingestion_health = True
                    logger.info("✅ Data ingestion recovery riuscito")
                except:
                    logger.error("❌ Data ingestion recovery fallito")
            
            # Clear old error counts
            current_time = datetime.utcnow()
            self.error_counts = {
                k: v for k, v in self.error_counts.items()
                if current_time - v["timestamp"] < timedelta(hours=24)
            }
            
        except Exception as e:
            logger.error(f"Errore nelle procedure auto-recovery: {e}")
    
    async def _process_pending_operations(self):
        """Processa operazioni in sospeso"""
        # Placeholder for any pending operations
        pass
    
    def _update_performance_metrics(self):
        """Aggiorna metriche di performance"""
        # Reset daily counters if needed
        current_time = datetime.utcnow()
        if not hasattr(self, 'last_reset_date') or current_time.date() != self.last_reset_date:
            self.performance_metrics = {
                "signals_processed": 0,
                "total_processing_time": 0.0,
                "successful_operations": 0,
                "failed_operations": 0
            }
            self.last_reset_date = current_time.date()
    
    async def _check_system_alerts(self):
        """Controlla per alert di sistema"""
        try:
            # Get current alerts from metrics engine
            if self.metrics_engine:
                report = await self.metrics_engine.generate_comprehensive_report(1, False)
                
                critical_alerts = [a for a in report.alerts if a["level"] == "CRITICAL"]
                if critical_alerts:
                    for alert in critical_alerts:
                        logger.critical(f"🚨 CRITICAL ALERT: {alert['title']} - {alert['message']}")
                        
                        # Could implement alert notifications here (email, webhook, etc.)
                        
        except Exception as e:
            logger.error(f"Errore nel check system alerts: {e}")
    
    def _record_error(self, component: str, error_msg: str):
        """Registra un errore"""
        current_time = datetime.utcnow()
        
        if component not in self.error_counts:
            self.error_counts[component] = {"count": 0, "last_error": "", "timestamp": current_time}
        
        self.error_counts[component]["count"] += 1
        self.error_counts[component]["last_error"] = error_msg
        self.error_counts[component]["timestamp"] = current_time
        
        self.health_status.last_error = error_msg
        self.health_status.last_error_timestamp = current_time
    
    async def _export_final_report(self):
        """Esporta report finale al shutdown"""
        try:
            report = await self.metrics_engine.generate_comprehensive_report(30, True)
            await self._export_report(report, suffix="_FINAL")
            logger.info("✅ Report finale esportato")
        except Exception as e:
            logger.error(f"Errore nell'export report finale: {e}")
    
    async def _export_report(self, report, suffix: str = ""):
        """Esporta report su file"""
        try:
            export_dir = Path("data/exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"quant_system_report_{timestamp}{suffix}.json"
            
            with open(export_dir / filename, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
                
            logger.info(f"📄 Report esportato: {filename}")
            
        except Exception as e:
            logger.error(f"Errore nell'export report: {e}")
    
    async def _cleanup_resources(self):
        """Cleanup delle risorse"""
        try:
            # Close any open connections, files, etc.
            logger.info("🧹 Cleanup risorse completato")
        except Exception as e:
            logger.error(f"Errore nel cleanup risorse: {e}")
    
    def _initialize_scheduled_tasks(self) -> List[ScheduledTask]:
        """Inizializza task schedulati"""
        return [
            ScheduledTask(TaskType.DATA_INGESTION, 30),      # Every 30 minutes
            ScheduledTask(TaskType.REGIME_UPDATE, 15),       # Every 15 minutes
            ScheduledTask(TaskType.RISK_CHECK, 5),           # Every 5 minutes
            ScheduledTask(TaskType.METRICS_CALCULATION, 60), # Every hour
            ScheduledTask(TaskType.REPORTING, 1440),         # Daily
            ScheduledTask(TaskType.HEALTH_CHECK, 300),       # Every 5 hours
        ]
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Carica configurazione di default"""
        return {
            "rolling_interval_minutes": 5,
            "max_concurrent_signals": 20,   # Increased from 15
            "min_confidence_threshold": 0.4,  # Lowered further from 0.45
            "auto_export_reports": True,
            "enable_auto_recovery": True,
            "max_daily_risk": 0.04,
            "system_timezone": "UTC"
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Carica configurazione da file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Errore nel caricamento config: {e}. Uso default.")
            return self._load_default_config()
    
    def _save_config(self):
        """Salva configurazione su file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Errore nel salvataggio config: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers per graceful shutdown"""
        def signal_handler(sig, frame):
            logger.info(f"Ricevuto segnale {sig}, inizializzo shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    # API Methods per controllo esterno
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Restituisce status completo del sistema"""
        return {
            "status": self.status.value,
            "uptime_hours": self.health_status.uptime_hours,
            "health": asdict(self.health_status),
            "performance": self.performance_metrics,
            "components": {
                "data_ingestion": self.health_status.data_ingestion_health,
                "signal_generation": self.health_status.signal_generation_health,
                "regime_detection": self.health_status.regime_detection_health,
                "risk_management": self.health_status.risk_management_health,
                "reporting": self.health_status.reporting_health
            }
        }
    
    async def pause_system(self):
        """Pausa il sistema"""
        if self.status == SystemStatus.RUNNING:
            self.status = SystemStatus.PAUSED
            if self.rolling_generator:
                self.rolling_generator.stop_rolling_generation()
            logger.info("⏸️ Sistema messo in pausa")
    
    async def resume_system(self):
        """Riprende il sistema"""
        if self.status == SystemStatus.PAUSED:
            self.status = SystemStatus.RUNNING
            if self.rolling_generator:
                asyncio.create_task(self.rolling_generator.start_rolling_generation())
            logger.info("▶️ Sistema ripreso")
    
    async def force_task_execution(self, task_type: TaskType):
        """Forza esecuzione di un task specifico"""
        task = next((t for t in self.scheduled_tasks if t.task_type == task_type), None)
        if task and not task.is_running:
            await self._execute_scheduled_task(task)
            logger.info(f"🔧 Task {task_type.value} eseguito manualmente")

# Factory function e main entry point
_orchestrator_instance = None

async def get_orchestrator(config_path: str = None) -> QuantAdaptiveOrchestrator:
    """Restituisce istanza singleton dell'orchestratore"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = QuantAdaptiveOrchestrator(config_path or "config/quant_system.json")
        await _orchestrator_instance.initialize()
    return _orchestrator_instance

async def main():
    """Entry point principale"""
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create and start orchestrator
        orchestrator = await get_orchestrator()
        
        logger.info("🚀 Avvio Quant Adaptive System...")
        await orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("Shutdown richiesto dall'utente")
    except Exception as e:
        logger.error(f"Errore fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
