"""
Regime Detection and Policy Switching System

Sistema avanzato per rilevamento dei regimi di mercato e switching automatico
delle policy di trading basato su:
- Analisi dati opzioni CBOE (0DTE share, PCR, gamma)
- Volume profile da futures (VAH/VAL breakouts, POC rejection)
- Volatilità multi-timeframe e momentum
- Machine learning per pattern recognition

Features:
- Rilevamento automatico regimi: TREND, MEAN_REVERSION, PINNING, GAMMA_SQUEEZE
- Policy switching dinamico con parametri adattivi
- Integration con signal generation per adjustment real-time
- Learning da outcome storici per miglioramento continuo
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import numpy as np
import pandas as pd
from pathlib import Path
import sqlite3
import aiosqlite

# Import modules del sistema quant
from ..data_ingestion.market_context import MarketContext, CBOEDataProvider
from ..data_ingestion.futures_volmap import VolumeProfile, FuturesVolumeMapper
from .market_regimes import MarketRegimeDetector, RegimeType, RegimeData

logger = logging.getLogger(__name__)

class PolicyType(Enum):
    """Tipologie di policy di trading"""
    AGGRESSIVE_TREND = "AGGRESSIVE_TREND"        # High momentum, breakout focus
    CONSERVATIVE_TREND = "CONSERVATIVE_TREND"    # Confirmed trend, pullback entries
    MEAN_REVERSION = "MEAN_REVERSION"           # Range bound, support/resistance
    GAMMA_SQUEEZE = "GAMMA_SQUEEZE"             # Options-driven, reduced size
    PINNING_AWARE = "PINNING_AWARE"             # Strike-level focused
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION" # High ATR, wider stops
    DEFENSIVE = "DEFENSIVE"                      # Risk-off, reduced exposure

@dataclass 
class PolicyParameters:
    """Parametri configurabili per ogni policy"""
    # Risk Management
    max_position_size: float = 0.02
    risk_reward_min: float = 1.5
    max_concurrent_trades: int = 5
    max_daily_trades: int = 20
    
    # Entry Criteria
    min_confidence: float = 0.4  # Lowered from 0.6 to 0.4 for more signals
    confluence_required: int = 1  # Reduced from 2 to 1 for more signals
    volume_confirmation: bool = True
    
    # Stop Loss / Take Profit
    atr_stop_multiplier: float = 2.0
    atr_target_multiplier: float = 4.0
    trailing_stop: bool = False
    
    # Timeframe Weights
    timeframe_weights: Dict[str, float] = field(default_factory=lambda: {
        "M1": 1.0, "M5": 2.0, "M15": 3.0, "M30": 4.0
    })
    
    # Indicator Weights  
    indicator_weights: Dict[str, float] = field(default_factory=lambda: {
        "RSI": 1.0, "MACD": 1.0, "BB": 1.0, "MA": 1.0, "ATR": 1.0
    })
    
    # Special Conditions
    avoid_news_events: bool = True
    max_correlation_exposure: float = 0.3
    session_restrictions: List[str] = field(default_factory=list)

@dataclass
class PolicyState:
    """Stato corrente di una policy"""
    policy_type: PolicyType
    parameters: PolicyParameters
    active_since: datetime
    last_update: datetime
    performance_score: float = 0.0
    usage_count: int = 0
    avg_holding_time: float = 0.0
    win_rate: float = 0.0
    avg_r_multiple: float = 0.0

class PolicyManager:
    """
    Manager per switching automatico delle policy basato sui regimi
    """
    
    def __init__(self, db_path: str = "data/policy_manager.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Current state
        self.current_policy = None
        self.current_regime = None
        self.policy_history = []
        
        # Components
        self.regime_detector = MarketRegimeDetector()
        self.cboe_provider = CBOEDataProvider()
        self.volume_mapper = FuturesVolumeMapper()
        
        # Policy definitions
        self.policy_templates = self._initialize_policy_templates()
        
        # Performance tracking
        self.policy_performance = {}
        self.regime_transitions = []
        
    async def initialize(self):
        """Inizializza il policy manager"""
        try:
            await self._create_database_tables()
            await self.regime_detector.initialize()
            await self.cboe_provider.initialize()
            await self.volume_mapper.initialize()
            
            # Load historical data
            await self._load_policy_performance()
            
            # Set initial policy
            initial_regime = await self._detect_current_regime()
            initial_policy = self._select_policy_for_regime(initial_regime)
            await self._switch_to_policy(initial_policy, initial_regime)
            
            logger.info("PolicyManager inizializzato correttamente")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione PolicyManager: {e}")
            raise
    
    async def update_regime_and_policy(self) -> bool:
        """
        Aggiorna rilevamento regime e switch policy se necessario
        Returns True se c'è stato un cambio di policy
        """
        try:
            # Detect current regime
            new_regime = await self._detect_current_regime()
            
            # Check se c'è un cambio di regime significativo
            if self._should_switch_regime(new_regime):
                logger.info(f"Cambio regime rilevato: {self.current_regime} -> {new_regime.regime_type.value}")
                
                # Select new policy
                new_policy = self._select_policy_for_regime(new_regime)
                
                # Switch policy se diversa
                if new_policy.policy_type != self.current_policy.policy_type:
                    await self._switch_to_policy(new_policy, new_regime)
                    return True
                else:
                    # Update regime without policy change
                    self.current_regime = new_regime
                    await self._log_regime_transition(new_regime, policy_changed=False)
            
            # Update policy parameters based on performance
            await self._adapt_current_policy()
            
            return False
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento regime/policy: {e}")
            return False
    
    def get_current_policy_parameters(self) -> PolicyParameters:
        """Restituisce parametri della policy corrente"""
        if self.current_policy:
            return self.current_policy.parameters
        else:
            # Fallback to default conservative policy
            return self.policy_templates[PolicyType.CONSERVATIVE_TREND]
    
    def get_current_regime_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul regime corrente"""
        if self.current_regime:
            return {
                "regime_type": self.current_regime.regime_type.value,
                "confidence": self.current_regime.confidence,
                "key_factors": self.current_regime.key_factors,
                "duration_minutes": int((datetime.utcnow() - self.current_regime.detected_at).total_seconds() / 60),
                "market_conditions": self.current_regime.market_conditions
            }
        else:
            return {"regime_type": "UNKNOWN", "confidence": 0.0}
    
    async def get_policy_performance_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """Restituisce summary delle performance delle policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        policy_type,
                        COUNT(*) as usage_count,
                        AVG(performance_score) as avg_performance,
                        AVG(win_rate) as avg_win_rate,
                        AVG(avg_r_multiple) as avg_r_multiple,
                        SUM(duration_minutes) as total_duration_minutes
                    FROM policy_history
                    WHERE started_at >= ?
                    GROUP BY policy_type
                    ORDER BY avg_performance DESC
                """, (cutoff_date.isoformat(),))
                
                results = await cursor.fetchall()
                
                performance_summary = {}
                for policy_type, count, perf, win_rate, r_mult, duration in results:
                    performance_summary[policy_type] = {
                        "usage_count": count,
                        "avg_performance_score": round(perf or 0, 3),
                        "avg_win_rate": round(win_rate or 0, 2),
                        "avg_r_multiple": round(r_mult or 0, 3),
                        "total_hours": round((duration or 0) / 60, 1)
                    }
                
                return performance_summary
                
        except Exception as e:
            logger.error(f"Errore nel calcolo performance summary: {e}")
            return {}
    
    async def _detect_current_regime(self) -> RegimeData:
        """Rileva il regime di mercato corrente"""
        try:
            # Get market data
            market_context = await self.cboe_provider.get_current_context()
            volume_profiles = await self.volume_mapper.get_all_current_profiles()
            
            # Run regime detection
            regime = await self.regime_detector.detect_regime(market_context, volume_profiles)
            
            return regime
            
        except Exception as e:
            logger.error(f"Errore nel rilevamento regime: {e}")
            # Return default regime
            return RegimeData(
                regime_type=RegimeType.NORMAL,
                confidence=0.5,
                detected_at=datetime.utcnow(),
                key_factors=["fallback_detection"],
                market_conditions={}
            )
    
    def _should_switch_regime(self, new_regime: RegimeData) -> bool:
        """Determina se dovremmo switchare al nuovo regime"""
        if not self.current_regime:
            return True
        
        # Check confidence threshold
        if new_regime.confidence < 0.6:
            return False
        
        # Check se è diverso dal regime corrente
        if new_regime.regime_type != self.current_regime.regime_type:
            return True
        
        # Check se è passato abbastanza tempo (min 15 minuti)
        if datetime.utcnow() - self.current_regime.detected_at < timedelta(minutes=15):
            return False
        
        # Check se c'è un miglioramento significativo nella confidence
        if new_regime.confidence > self.current_regime.confidence + 0.2:
            return True
        
        return False
    
    def _select_policy_for_regime(self, regime: RegimeData) -> PolicyState:
        """Seleziona la policy ottimale per il regime rilevato"""
        
        # Mapping regime -> policy preferita
        regime_policy_mapping = {
            RegimeType.STRONG_TREND: PolicyType.AGGRESSIVE_TREND,
            RegimeType.WEAK_TREND: PolicyType.CONSERVATIVE_TREND,
            RegimeType.MEAN_REVERSION: PolicyType.MEAN_REVERSION,
            RegimeType.GAMMA_SQUEEZE: PolicyType.GAMMA_SQUEEZE,
            RegimeType.PINNING: PolicyType.PINNING_AWARE,
            RegimeType.HIGH_VOLATILITY: PolicyType.VOLATILITY_EXPANSION,
            RegimeType.NORMAL: PolicyType.CONSERVATIVE_TREND
        }
        
        # Get preferred policy type
        preferred_policy = regime_policy_mapping.get(regime.regime_type, PolicyType.CONSERVATIVE_TREND)
        
        # Check performance history per override
        if preferred_policy in self.policy_performance:
            perf_data = self.policy_performance[preferred_policy]
            
            # Se performance è scarsa, usa policy più conservativa
            if perf_data.get('avg_r_multiple', 0) < -0.5:
                preferred_policy = PolicyType.DEFENSIVE
            elif perf_data.get('win_rate', 0) < 30:
                preferred_policy = PolicyType.CONSERVATIVE_TREND
        
        # Create policy state
        parameters = self._get_adapted_parameters(preferred_policy, regime)
        
        return PolicyState(
            policy_type=preferred_policy,
            parameters=parameters,
            active_since=datetime.utcnow(),
            last_update=datetime.utcnow()
        )
    
    def _get_adapted_parameters(self, policy_type: PolicyType, regime: RegimeData) -> PolicyParameters:
        """Ottieni parametri adattati per policy e regime"""
        # Start with base template
        base_params = self.policy_templates[policy_type]
        
        # Create copy for adaptation
        adapted_params = PolicyParameters(
            max_position_size=base_params.max_position_size,
            risk_reward_min=base_params.risk_reward_min,
            max_concurrent_trades=base_params.max_concurrent_trades,
            max_daily_trades=base_params.max_daily_trades,
            min_confidence=base_params.min_confidence,
            confluence_required=base_params.confluence_required,
            volume_confirmation=base_params.volume_confirmation,
            atr_stop_multiplier=base_params.atr_stop_multiplier,
            atr_target_multiplier=base_params.atr_target_multiplier,
            trailing_stop=base_params.trailing_stop,
            timeframe_weights=base_params.timeframe_weights.copy(),
            indicator_weights=base_params.indicator_weights.copy(),
            avoid_news_events=base_params.avoid_news_events,
            max_correlation_exposure=base_params.max_correlation_exposure,
            session_restrictions=base_params.session_restrictions.copy()
        )
        
        # Adapt based on regime
        if regime.regime_type == RegimeType.HIGH_VOLATILITY:
            adapted_params.max_position_size *= 0.8  # Less conservative (was 0.7)
            adapted_params.atr_stop_multiplier *= 1.3  # Less conservative (was 1.5)
            adapted_params.min_confidence += 0.05  # Much smaller increase (was 0.1)
            
        elif regime.regime_type == RegimeType.GAMMA_SQUEEZE:
            adapted_params.max_position_size *= 0.6  # Less conservative (was 0.5)
            adapted_params.max_concurrent_trades = max(3, adapted_params.max_concurrent_trades // 2)  # Allow more (was 2)
            adapted_params.min_confidence += 0.08  # Much smaller increase (was 0.15)
            
        elif regime.regime_type == RegimeType.PINNING:
            adapted_params.confluence_required = max(3, adapted_params.confluence_required)
            adapted_params.volume_confirmation = True
            
        elif regime.regime_type == RegimeType.STRONG_TREND:
            adapted_params.trailing_stop = True
            adapted_params.atr_target_multiplier *= 1.3
        
        return adapted_params
    
    async def _switch_to_policy(self, new_policy: PolicyState, regime: RegimeData):
        """Switcha alla nuova policy"""
        try:
            # Log transition
            if self.current_policy:
                await self._finalize_current_policy()
            
            # Set new policy
            self.current_policy = new_policy
            self.current_regime = regime
            
            # Log to database
            await self._log_policy_activation(new_policy)
            await self._log_regime_transition(regime, policy_changed=True)
            
            logger.info(f"Policy switched to: {new_policy.policy_type.value} for regime: {regime.regime_type.value}")
            
        except Exception as e:
            logger.error(f"Errore nello switch policy: {e}")
    
    async def _adapt_current_policy(self):
        """Adatta parametri della policy corrente basandosi su performance"""
        if not self.current_policy:
            return
        
        try:
            # Get recent performance data
            policy_type = self.current_policy.policy_type.value
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT AVG(performance_score), AVG(win_rate), AVG(avg_r_multiple)
                    FROM policy_history
                    WHERE policy_type = ? 
                    AND started_at >= datetime('now', '-7 days')
                """, (policy_type,))
                
                result = await cursor.fetchone()
                
                if result and result[0] is not None:
                    avg_perf, avg_win_rate, avg_r_mult = result
                    
                    # Adaptive adjustments - more forgiving
                    if avg_perf < 0.2:  # Only adjust on very poor performance (was 0.3)
                        self.current_policy.parameters.min_confidence += 0.02  # Smaller increase (was 0.05)
                        self.current_policy.parameters.max_position_size *= 0.95  # Less penalty (was 0.9)
                        
                    elif avg_perf > 0.7:  # Good performance
                        self.current_policy.parameters.max_position_size *= 1.05
                        self.current_policy.parameters.max_concurrent_trades = min(
                            self.current_policy.parameters.max_concurrent_trades + 1, 8
                        )
                    
                    # Update policy state
                    self.current_policy.performance_score = avg_perf
                    self.current_policy.win_rate = avg_win_rate or 0
                    self.current_policy.avg_r_multiple = avg_r_mult or 0
                    self.current_policy.last_update = datetime.utcnow()
                    
        except Exception as e:
            logger.error(f"Errore nell'adattamento policy: {e}")
    
    def _initialize_policy_templates(self) -> Dict[PolicyType, PolicyParameters]:
        """Inizializza template delle policy"""
        return {
            PolicyType.AGGRESSIVE_TREND: PolicyParameters(
                max_position_size=0.025,
                risk_reward_min=2.0,
                max_concurrent_trades=6,
                min_confidence=0.45,  # Lowered from 0.65
                confluence_required=2,
                atr_stop_multiplier=1.5,
                atr_target_multiplier=4.0,
                trailing_stop=True,
                timeframe_weights={"M1": 2.0, "M5": 3.0, "M15": 2.0, "M30": 1.0}
            ),
            
            PolicyType.CONSERVATIVE_TREND: PolicyParameters(
                max_position_size=0.02,
                risk_reward_min=2.0,
                max_concurrent_trades=4,
                min_confidence=0.5,  # Lowered from 0.7
                confluence_required=3,
                atr_stop_multiplier=2.0,
                atr_target_multiplier=4.0,
                trailing_stop=False
            ),
            
            PolicyType.MEAN_REVERSION: PolicyParameters(
                max_position_size=0.015,
                risk_reward_min=1.5,
                max_concurrent_trades=3,
                min_confidence=0.55,  # Lowered from 0.75
                confluence_required=3,
                atr_stop_multiplier=1.5,
                atr_target_multiplier=2.0,
                volume_confirmation=True,
                timeframe_weights={"M1": 1.0, "M5": 2.0, "M15": 3.0, "M30": 2.0}
            ),
            
            PolicyType.GAMMA_SQUEEZE: PolicyParameters(
                max_position_size=0.01,
                risk_reward_min=3.0,
                max_concurrent_trades=3,  # Increased from 2
                max_daily_trades=15,      # Increased from 10
                min_confidence=0.6,       # Lowered from 0.8
                confluence_required=4,
                atr_stop_multiplier=3.0,
                atr_target_multiplier=6.0,
                avoid_news_events=True
            ),
            
            PolicyType.PINNING_AWARE: PolicyParameters(
                max_position_size=0.015,
                risk_reward_min=1.0,
                max_concurrent_trades=4,  # Increased from 3
                min_confidence=0.45,      # Lowered from 0.6
                confluence_required=2,
                atr_stop_multiplier=1.0,
                atr_target_multiplier=2.0,
                volume_confirmation=True
            ),
            
            PolicyType.VOLATILITY_EXPANSION: PolicyParameters(
                max_position_size=0.01,
                risk_reward_min=2.5,
                max_concurrent_trades=5,  # Increased from 4
                min_confidence=0.5,       # Lowered from 0.7
                atr_stop_multiplier=2.5,
                atr_target_multiplier=5.0,
                trailing_stop=True
            ),
            
            PolicyType.DEFENSIVE: PolicyParameters(
                max_position_size=0.005,
                risk_reward_min=3.0,
                max_concurrent_trades=2,  # Increased from 1
                max_daily_trades=10,      # Increased from 5
                min_confidence=0.65,      # Lowered from 0.85
                confluence_required=4,
                atr_stop_multiplier=2.0,
                atr_target_multiplier=6.0,
                avoid_news_events=True
            )
        }
    
    async def _create_database_tables(self):
        """Crea tabelle del database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Policy history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS policy_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_type TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    duration_minutes INTEGER,
                    performance_score REAL,
                    win_rate REAL,
                    avg_r_multiple REAL,
                    avg_holding_time REAL,
                    usage_count INTEGER DEFAULT 0,
                    regime_type TEXT,
                    parameters_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Regime transitions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS regime_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_regime TEXT,
                    to_regime TEXT,
                    transition_time TEXT NOT NULL,
                    confidence REAL,
                    key_factors TEXT,
                    policy_changed BOOLEAN DEFAULT 0,
                    market_conditions TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def _load_policy_performance(self):
        """Carica performance storiche delle policy"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        policy_type,
                        AVG(performance_score) as avg_performance,
                        AVG(win_rate) as avg_win_rate,
                        AVG(avg_r_multiple) as avg_r_multiple,
                        COUNT(*) as usage_count
                    FROM policy_history
                    WHERE started_at >= datetime('now', '-30 days')
                    GROUP BY policy_type
                """)
                
                results = await cursor.fetchall()
                
                for policy_type, avg_perf, avg_win, avg_r, count in results:
                    self.policy_performance[policy_type] = {
                        'avg_performance': avg_perf or 0,
                        'avg_win_rate': avg_win or 0,
                        'avg_r_multiple': avg_r or 0,
                        'usage_count': count or 0
                    }
                
        except Exception as e:
            logger.error(f"Errore nel caricamento performance policy: {e}")
    
    async def _log_policy_activation(self, policy: PolicyState):
        """Logga attivazione di una nuova policy"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO policy_history
                    (policy_type, started_at, regime_type, parameters_json)
                    VALUES (?, ?, ?, ?)
                """, (
                    policy.policy_type.value,
                    policy.active_since.isoformat(),
                    self.current_regime.regime_type.value if self.current_regime else "UNKNOWN",
                    json.dumps({
                        "max_position_size": policy.parameters.max_position_size,
                        "risk_reward_min": policy.parameters.risk_reward_min,
                        "min_confidence": policy.parameters.min_confidence,
                        "confluence_required": policy.parameters.confluence_required
                    })
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Errore nel log policy activation: {e}")
    
    async def _log_regime_transition(self, new_regime: RegimeData, policy_changed: bool):
        """Logga transizione di regime"""
        try:
            from_regime = self.current_regime.regime_type.value if self.current_regime else "NONE"
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO regime_transitions
                    (from_regime, to_regime, transition_time, confidence, key_factors, policy_changed, market_conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    from_regime,
                    new_regime.regime_type.value,
                    new_regime.detected_at.isoformat(),
                    new_regime.confidence,
                    json.dumps(new_regime.key_factors),
                    policy_changed,
                    json.dumps(new_regime.market_conditions)
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Errore nel log regime transition: {e}")
    
    async def _finalize_current_policy(self):
        """Finalizza la policy corrente con metriche finali"""
        if not self.current_policy:
            return
            
        try:
            duration = datetime.utcnow() - self.current_policy.active_since
            duration_minutes = int(duration.total_seconds() / 60)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE policy_history 
                    SET ended_at = ?, duration_minutes = ?, performance_score = ?, 
                        win_rate = ?, avg_r_multiple = ?, usage_count = ?
                    WHERE policy_type = ? AND started_at = ? AND ended_at IS NULL
                """, (
                    datetime.utcnow().isoformat(),
                    duration_minutes,
                    self.current_policy.performance_score,
                    self.current_policy.win_rate,
                    self.current_policy.avg_r_multiple,
                    self.current_policy.usage_count,
                    self.current_policy.policy_type.value,
                    self.current_policy.active_since.isoformat()
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Errore nella finalizzazione policy: {e}")

# Factory function per istanza globale
_policy_manager_instance = None

async def get_policy_manager() -> PolicyManager:
    """Restituisce istanza singleton del policy manager"""
    global _policy_manager_instance
    if _policy_manager_instance is None:
        _policy_manager_instance = PolicyManager()
        await _policy_manager_instance.initialize()
    return _policy_manager_instance

# Helper functions
async def get_current_policy_parameters() -> PolicyParameters:
    """Restituisce parametri della policy corrente"""
    manager = await get_policy_manager()
    return manager.get_current_policy_parameters()

async def get_current_regime() -> Dict[str, Any]:
    """Restituisce informazioni sul regime corrente"""
    manager = await get_policy_manager()
    return manager.get_current_regime_info()

async def update_market_regime() -> bool:
    """Force update del regime e policy - returns True se c'è stato cambio"""
    manager = await get_policy_manager()
    return await manager.update_regime_and_policy()

async def get_policy_performance(days_back: int = 30) -> Dict[str, Any]:
    """Restituisce performance delle policy"""
    manager = await get_policy_manager()
    return await manager.get_policy_performance_summary(days_back)
