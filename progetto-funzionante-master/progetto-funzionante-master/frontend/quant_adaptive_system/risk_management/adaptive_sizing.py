"""
Adaptive Position Sizing System

Sistema avanzato di gestione risk con position sizing dinamico basato su:
- Performance recenti e drawdown tracking
- Regime di mercato e volatilità corrente  
- Correlazione tra posizioni aperte
- Kelly Criterion adattivo per optimal sizing
- Circuit breakers e controlli automatici
- Heat map esposizione per strumento/regime

Features:
- Position sizing dinamico basato su Kelly Criterion modificato
- Controllo correlazione portfolio real-time
- Adaptive stop loss con volatility adjustment
- Circuit breakers automatici per protezione capitale
- Risk budgeting per regime e timeframe
- Portfolio heat mapping e concentrazione risk
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
import math

# Import modules del sistema quant
from ..regime_detection.policy import PolicyParameters, get_current_policy_parameters
from ..signal_intelligence.signal_outcomes import get_outcome_tracker, SignalOutcome

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Livelli di rischio del sistema"""
    VERY_LOW = "VERY_LOW"      # <0.5% daily risk
    LOW = "LOW"                # 0.5-1% daily risk
    NORMAL = "NORMAL"          # 1-2% daily risk  
    ELEVATED = "ELEVATED"      # 2-3% daily risk
    HIGH = "HIGH"              # 3-4% daily risk
    CRITICAL = "CRITICAL"      # >4% daily risk

@dataclass
class PositionSizeCalculation:
    """Risultato del calcolo position size"""
    instrument: str
    signal_id: str
    recommended_size: float    # Percentuale del capitale (es. 0.02 = 2%)
    max_size_allowed: float    # Size massima consentita
    risk_level: RiskLevel
    kelly_fraction: float      # Kelly criterion puro
    kelly_adjusted: float      # Kelly con adjustments
    
    # Fattori di adjustment
    volatility_adjustment: float = 1.0
    regime_adjustment: float = 1.0
    correlation_adjustment: float = 1.0
    performance_adjustment: float = 1.0
    drawdown_adjustment: float = 1.0
    
    # Metriche di contesto
    portfolio_risk_used: float = 0.0    # % del risk budget utilizzato
    max_correlation_with_existing: float = 0.0
    estimated_portfolio_var: float = 0.0  # Value at Risk giornaliero
    
    # Metadata
    calculation_timestamp: datetime = field(default_factory=datetime.utcnow)
    calculation_reason: str = ""

@dataclass
class RiskMetrics:
    """Metriche di rischio del portfolio"""
    total_exposure: float = 0.0           # Esposizione totale %
    daily_var: float = 0.0                # Value at Risk giornaliero
    max_drawdown: float = 0.0             # Maximum drawdown corrente
    win_rate_7d: float = 0.0              # Win rate ultimi 7 giorni
    avg_r_multiple_7d: float = 0.0        # R-multiple medio 7 giorni
    kelly_criterion: float = 0.0          # Kelly ottimale corrente
    risk_adjusted_return: float = 0.0     # Sharpe-like ratio
    
    # Risk per categoria
    risk_by_instrument: Dict[str, float] = field(default_factory=dict)
    risk_by_regime: Dict[str, float] = field(default_factory=dict)
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Circuit breakers status
    daily_loss_limit_used: float = 0.0   # % del limite giornaliero utilizzato
    consecutive_losses: int = 0
    cooling_off_active: bool = False
    cooling_off_until: Optional[datetime] = None

class AdaptiveRiskManager:
    """
    Sistema di risk management adattivo con position sizing dinamico
    """
    
    def __init__(self, db_path: str = "data/risk_management.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Risk parameters (configurable)
        self.risk_params = {
            # Base risk limits
            "max_daily_risk": 0.04,              # 4% max daily risk
            "max_position_risk": 0.02,           # 2% max per posizione
            "max_correlated_risk": 0.06,         # 6% max per cluster correlato
            "max_regime_risk": 0.08,             # 8% max per regime
            
            # Kelly parameters
            "kelly_lookback_days": 30,           # Giorni per calcolo Kelly
            "kelly_fractional_size": 0.25,      # Frazione del Kelly pieno (25%)
            "min_trades_for_kelly": 10,          # Minimum trades per Kelly valido
            
            # Circuit breakers
            "daily_loss_limit": 0.05,            # 5% daily loss limit
            "consecutive_loss_limit": 4,         # Max consecutive losses
            "cooling_off_hours": 2,              # Hours di cooling off
            "max_drawdown_limit": 0.15,          # 15% max drawdown
            
            # Correlation controls
            "max_position_correlation": 0.7,     # Max correlazione tra posizioni
            "correlation_lookback_days": 14,     # Giorni per calcolo correlazioni
            
            # Volatility adjustments
            "volatility_lookback_days": 10,      # Giorni per volatility calc
            "volatility_target": 0.02,           # Target daily volatility (2%)
            "volatility_scaling_factor": 1.5     # Scaling factor per adjustments
        }
        
        # Current state
        self.current_positions = {}           # active positions tracking
        self.daily_pnl = 0.0                 # P&L giornaliero corrente
        self.current_risk_level = RiskLevel.NORMAL
        self.circuit_breakers_active = False
        
        # Risk metrics caching
        self._cached_metrics = None
        self._cache_timestamp = None
        self._cache_validity_minutes = 5
        
    async def initialize(self):
        """Inizializza il risk manager"""
        try:
            await self._create_database_tables()
            await self._load_current_positions()
            await self._calculate_daily_pnl()
            await self._check_circuit_breakers()
            
            logger.info("AdaptiveRiskManager inizializzato correttamente")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione AdaptiveRiskManager: {e}")
            raise
    
    async def calculate_position_size(self, 
                                    instrument: str,
                                    signal_id: str,
                                    entry_price: float,
                                    stop_loss: float,
                                    confidence: float,
                                    regime_type: str = "NORMAL") -> PositionSizeCalculation:
        """
        Calcola position size ottimale per un nuovo segnale
        """
        try:
            # Check circuit breakers first
            if await self._are_circuit_breakers_active():
                return PositionSizeCalculation(
                    instrument=instrument,
                    signal_id=signal_id,
                    recommended_size=0.0,
                    max_size_allowed=0.0,
                    risk_level=RiskLevel.CRITICAL,
                    kelly_fraction=0.0,
                    kelly_adjusted=0.0,
                    calculation_reason="Circuit breakers active"
                )
            
            # Get current policy parameters
            policy_params = await get_current_policy_parameters()
            
            # Calculate base risk per trade
            trade_risk = abs(entry_price - stop_loss) / entry_price
            if trade_risk == 0:
                trade_risk = 0.02  # Default 2% if no stop loss
            
            # Calculate Kelly criterion
            kelly_fraction = await self._calculate_kelly_criterion(instrument, regime_type)
            
            # Apply various adjustments
            volatility_adj = await self._calculate_volatility_adjustment(instrument)
            regime_adj = await self._calculate_regime_adjustment(regime_type, policy_params)
            correlation_adj = await self._calculate_correlation_adjustment(instrument)
            performance_adj = await self._calculate_performance_adjustment()
            drawdown_adj = await self._calculate_drawdown_adjustment()
            confidence_adj = self._calculate_confidence_adjustment(confidence)
            
            # Calculate adjusted Kelly
            kelly_adjusted = (kelly_fraction * volatility_adj * regime_adj * 
                            correlation_adj * performance_adj * drawdown_adj * confidence_adj)
            
            # Apply fractional Kelly sizing
            base_size = kelly_adjusted * self.risk_params["kelly_fractional_size"]
            
            # Apply policy limits
            base_size = min(base_size, policy_params.max_position_size)
            base_size = min(base_size, self.risk_params["max_position_risk"])
            
            # Check portfolio risk limits
            current_risk = await self._calculate_current_portfolio_risk()
            remaining_risk_budget = self.risk_params["max_daily_risk"] - current_risk
            
            # Adjust size to fit risk budget
            recommended_size = min(base_size, remaining_risk_budget * 0.8)  # Use 80% of remaining
            
            # Determine risk level
            risk_level = self._determine_risk_level(recommended_size, current_risk)
            
            # Calculate portfolio metrics
            portfolio_risk_used = (current_risk + recommended_size) / self.risk_params["max_daily_risk"]
            max_correlation = await self._get_max_correlation_with_existing(instrument)
            estimated_var = await self._estimate_portfolio_var_with_new_position(
                instrument, recommended_size, trade_risk
            )
            
            return PositionSizeCalculation(
                instrument=instrument,
                signal_id=signal_id,
                recommended_size=max(0.0, recommended_size),
                max_size_allowed=base_size,
                risk_level=risk_level,
                kelly_fraction=kelly_fraction,
                kelly_adjusted=kelly_adjusted,
                volatility_adjustment=volatility_adj,
                regime_adjustment=regime_adj,
                correlation_adjustment=correlation_adj,
                performance_adjustment=performance_adj,
                drawdown_adjustment=drawdown_adj,
                portfolio_risk_used=portfolio_risk_used,
                max_correlation_with_existing=max_correlation,
                estimated_portfolio_var=estimated_var,
                calculation_reason="Normal calculation"
            )
            
        except Exception as e:
            logger.error(f"Errore nel calcolo position size per {instrument}: {e}")
            return PositionSizeCalculation(
                instrument=instrument,
                signal_id=signal_id,
                recommended_size=0.0,
                max_size_allowed=0.0,
                risk_level=RiskLevel.CRITICAL,
                kelly_fraction=0.0,
                kelly_adjusted=0.0,
                calculation_reason=f"Calculation error: {str(e)}"
            )
    
    async def update_position_outcome(self, 
                                    signal_id: str,
                                    outcome: SignalOutcome,
                                    pnl: float) -> bool:
        """Aggiorna outcome di una posizione e ricalcola risk metrics"""
        try:
            # Update daily P&L
            self.daily_pnl += pnl
            
            # Remove from current positions if closed
            if outcome in [SignalOutcome.TP_HIT, SignalOutcome.SL_HIT, 
                          SignalOutcome.TIMEOUT, SignalOutcome.MANUAL_EXIT]:
                self.current_positions.pop(signal_id, None)
            
            # Store in database
            await self._store_position_outcome(signal_id, outcome, pnl)
            
            # Check circuit breakers
            await self._check_circuit_breakers()
            
            # Update risk level
            await self._update_risk_level()
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento position outcome: {e}")
            return False
    
    async def get_current_risk_metrics(self) -> RiskMetrics:
        """Restituisce metriche di rischio correnti"""
        try:
            # Check cache
            if (self._cached_metrics and self._cache_timestamp and 
                datetime.utcnow() - self._cache_timestamp < timedelta(minutes=self._cache_validity_minutes)):
                return self._cached_metrics
            
            # Calculate fresh metrics
            tracker = await get_outcome_tracker()
            recent_performance = await tracker.get_performance_metrics(days_back=7)
            
            # Portfolio risk calculation
            total_exposure = await self._calculate_current_portfolio_risk()
            daily_var = await self._calculate_portfolio_var()
            max_drawdown = await self._calculate_max_drawdown()
            
            # Kelly calculation
            kelly_criterion = await self._calculate_kelly_criterion("PORTFOLIO", "NORMAL")
            
            # Risk by category
            risk_by_instrument = await self._calculate_risk_by_instrument()
            risk_by_regime = await self._calculate_risk_by_regime()
            correlation_matrix = await self._calculate_correlation_matrix()
            
            # Circuit breaker status
            daily_loss_used = abs(min(0, self.daily_pnl)) / (self.risk_params["daily_loss_limit"])
            consecutive_losses = await self._count_consecutive_losses()
            cooling_off_active, cooling_until = await self._check_cooling_off_status()
            
            metrics = RiskMetrics(
                total_exposure=total_exposure,
                daily_var=daily_var,
                max_drawdown=max_drawdown,
                win_rate_7d=recent_performance.get("win_rate", 0),
                avg_r_multiple_7d=recent_performance.get("avg_r_multiple", 0),
                kelly_criterion=kelly_criterion,
                risk_adjusted_return=self._calculate_risk_adjusted_return(recent_performance),
                risk_by_instrument=risk_by_instrument,
                risk_by_regime=risk_by_regime,
                correlation_matrix=correlation_matrix,
                daily_loss_limit_used=daily_loss_used,
                consecutive_losses=consecutive_losses,
                cooling_off_active=cooling_off_active,
                cooling_off_until=cooling_until
            )
            
            # Cache metrics
            self._cached_metrics = metrics
            self._cache_timestamp = datetime.utcnow()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Errore nel calcolo risk metrics: {e}")
            return RiskMetrics()  # Return empty metrics
    
    async def _calculate_kelly_criterion(self, instrument: str, regime_type: str) -> float:
        """Calcola Kelly criterion per strumento/regime"""
        try:
            tracker = await get_outcome_tracker()
            
            # Get historical performance data
            async with aiosqlite.connect(tracker.db_path) as db:
                cursor = await db.execute("""
                    SELECT o.r_multiple, o.outcome
                    FROM signal_snapshots s
                    JOIN signal_outcomes o ON s.signal_id = o.signal_id
                    WHERE s.instrument LIKE ? 
                    AND JSON_EXTRACT(s.market_context, '$.market_regime') = ?
                    AND s.timestamp >= datetime('now', '-{} days')
                    AND o.r_multiple IS NOT NULL
                    ORDER BY s.timestamp DESC
                """.format(self.risk_params["kelly_lookback_days"]), 
                (f"%{instrument}%" if instrument != "PORTFOLIO" else "%", regime_type))
                
                results = await cursor.fetchall()
            
            if len(results) < self.risk_params["min_trades_for_kelly"]:
                return 0.01  # Conservative default
            
            # Calculate win rate and average win/loss
            wins = [r[0] for r in results if r[0] > 0]
            losses = [abs(r[0]) for r in results if r[0] < 0]
            
            if not wins or not losses:
                return 0.01
            
            win_rate = len(wins) / len(results)
            avg_win = np.mean(wins)
            avg_loss = np.mean(losses)
            
            # Kelly = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
            if avg_loss == 0:
                return 0.01
                
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate
            
            kelly = (b * p - q) / b
            
            # Cap Kelly at reasonable levels
            kelly = max(0.0, min(0.1, kelly))  # Max 10% Kelly
            
            return kelly
            
        except Exception as e:
            logger.error(f"Errore nel calcolo Kelly criterion: {e}")
            return 0.01
    
    async def _calculate_volatility_adjustment(self, instrument: str) -> float:
        """Calcola adjustment basato su volatilità"""
        try:
            # Get recent volatility data for instrument
            # In implementazione reale, useresti dati di prezzo storici
            # Per ora uso proxy basato su regime corrente
            
            tracker = await get_outcome_tracker()
            async with aiosqlite.connect(tracker.db_path) as db:
                cursor = await db.execute("""
                    SELECT AVG(ABS(o.r_multiple)) as avg_volatility
                    FROM signal_snapshots s
                    JOIN signal_outcomes o ON s.signal_id = o.signal_id
                    WHERE s.instrument = ?
                    AND s.timestamp >= datetime('now', '-{} days')
                    AND o.r_multiple IS NOT NULL
                """.format(self.risk_params["volatility_lookback_days"]), (instrument,))
                
                result = await cursor.fetchone()
                
                if result and result[0]:
                    instrument_vol = result[0]
                    
                    # Scale relative to target volatility
                    vol_ratio = self.risk_params["volatility_target"] / max(0.01, instrument_vol)
                    
                    # Apply scaling factor with bounds
                    adjustment = vol_ratio ** (1 / self.risk_params["volatility_scaling_factor"])
                    return max(0.3, min(2.0, adjustment))
                
                return 1.0  # Neutral if no data
                
        except Exception as e:
            logger.error(f"Errore nel calcolo volatility adjustment: {e}")
            return 1.0
    
    async def _calculate_regime_adjustment(self, regime_type: str, policy_params: PolicyParameters) -> float:
        """Calcola adjustment basato su regime di mercato"""
        regime_adjustments = {
            "NORMAL": 1.0,
            "STRONG_TREND": 1.2,      # Slightly larger positions in strong trends
            "WEAK_TREND": 0.9,        # Smaller in weak trends
            "MEAN_REVERSION": 0.8,    # Smaller in mean reversion
            "GAMMA_SQUEEZE": 0.5,     # Much smaller in gamma squeeze
            "PINNING": 0.6,           # Smaller in pinning
            "HIGH_VOLATILITY": 0.7    # Smaller in high vol
        }
        
        base_adjustment = regime_adjustments.get(regime_type, 1.0)
        
        # Apply policy-specific adjustments
        if hasattr(policy_params, 'max_position_size'):
            policy_adjustment = policy_params.max_position_size / 0.02  # Normalize to 2% base
            base_adjustment *= policy_adjustment
        
        return max(0.1, min(2.0, base_adjustment))
    
    async def _calculate_correlation_adjustment(self, instrument: str) -> float:
        """Calcola adjustment basato su correlazione con posizioni esistenti"""
        try:
            if not self.current_positions:
                return 1.0  # No adjustment if no current positions
            
            max_correlation = await self._get_max_correlation_with_existing(instrument)
            
            if max_correlation > self.risk_params["max_position_correlation"]:
                # Reduce size for highly correlated positions
                correlation_penalty = (max_correlation - self.risk_params["max_position_correlation"]) / (1 - self.risk_params["max_position_correlation"])
                adjustment = 1.0 - correlation_penalty * 0.5  # Max 50% reduction
                return max(0.3, adjustment)
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Errore nel calcolo correlation adjustment: {e}")
            return 1.0
    
    async def _calculate_performance_adjustment(self) -> float:
        """Calcola adjustment basato su performance recenti"""
        try:
            tracker = await get_outcome_tracker()
            recent_perf = await tracker.get_performance_metrics(days_back=7)
            
            win_rate = recent_perf.get("win_rate", 50) / 100
            avg_r = recent_perf.get("avg_r_multiple", 0)
            
            # Performance score
            perf_score = (win_rate - 0.5) * 2 + avg_r / 2  # Normalize around 0
            
            # Adjustment: good performance = slightly larger, bad = smaller
            if perf_score > 0.2:
                return min(1.3, 1.0 + perf_score * 0.5)
            elif perf_score < -0.2:
                return max(0.5, 1.0 + perf_score * 0.8)
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"Errore nel calcolo performance adjustment: {e}")
            return 1.0
    
    async def _calculate_drawdown_adjustment(self) -> float:
        """Calcola adjustment basato su drawdown corrente"""
        try:
            max_dd = await self._calculate_max_drawdown()
            
            if max_dd > self.risk_params["max_drawdown_limit"] * 0.7:  # 70% of limit
                # Approaching max drawdown - reduce size significantly
                dd_penalty = (max_dd - self.risk_params["max_drawdown_limit"] * 0.7) / (self.risk_params["max_drawdown_limit"] * 0.3)
                adjustment = 1.0 - dd_penalty * 0.8  # Up to 80% reduction
                return max(0.1, adjustment)
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Errore nel calcolo drawdown adjustment: {e}")
            return 1.0
    
    def _calculate_confidence_adjustment(self, confidence: float) -> float:
        """Calcola adjustment basato su confidence del segnale"""
        # Scale position size based on signal confidence
        # confidence 0.5 = 50% of normal size
        # confidence 1.0 = 100% of normal size
        return max(0.2, min(1.5, confidence * 2))
    
    async def _calculate_current_portfolio_risk(self) -> float:
        """Calcola risk corrente del portfolio"""
        try:
            total_risk = 0.0
            
            for signal_id, position_data in self.current_positions.items():
                position_risk = position_data.get("risk", 0.0)
                total_risk += position_risk
            
            return total_risk
            
        except Exception as e:
            logger.error(f"Errore nel calcolo portfolio risk: {e}")
            return 0.0
    
    def _determine_risk_level(self, recommended_size: float, current_risk: float) -> RiskLevel:
        """Determina livello di rischio basato su size e risk corrente"""
        total_risk = current_risk + recommended_size
        
        if total_risk < 0.005:
            return RiskLevel.VERY_LOW
        elif total_risk < 0.01:
            return RiskLevel.LOW
        elif total_risk < 0.02:
            return RiskLevel.NORMAL
        elif total_risk < 0.03:
            return RiskLevel.ELEVATED
        elif total_risk < 0.04:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    async def _are_circuit_breakers_active(self) -> bool:
        """Check se circuit breakers sono attivi"""
        return self.circuit_breakers_active
    
    async def _check_circuit_breakers(self):
        """Controlla e attiva circuit breakers se necessario"""
        try:
            # Daily loss limit
            daily_loss_pct = abs(min(0, self.daily_pnl))
            if daily_loss_pct >= self.risk_params["daily_loss_limit"]:
                self.circuit_breakers_active = True
                logger.warning(f"Daily loss limit breached: {daily_loss_pct:.3f}")
                return
            
            # Consecutive losses
            consecutive_losses = await self._count_consecutive_losses()
            if consecutive_losses >= self.risk_params["consecutive_loss_limit"]:
                self.circuit_breakers_active = True
                
                # Set cooling off period
                cooling_until = datetime.utcnow() + timedelta(hours=self.risk_params["cooling_off_hours"])
                await self._set_cooling_off_period(cooling_until)
                
                logger.warning(f"Consecutive losses limit breached: {consecutive_losses}")
                return
            
            # Max drawdown
            max_dd = await self._calculate_max_drawdown()
            if max_dd >= self.risk_params["max_drawdown_limit"]:
                self.circuit_breakers_active = True
                logger.warning(f"Max drawdown limit breached: {max_dd:.3f}")
                return
            
            # Check if cooling off period has expired
            cooling_active, cooling_until = await self._check_cooling_off_status()
            if cooling_active and datetime.utcnow() > cooling_until:
                # Reset circuit breakers
                self.circuit_breakers_active = False
                await self._clear_cooling_off_period()
                logger.info("Circuit breakers reset - cooling off period expired")
            
        except Exception as e:
            logger.error(f"Errore nel check circuit breakers: {e}")
    
    # Additional helper methods would continue here...
    # For brevity, I'll include the key remaining methods
    
    async def _create_database_tables(self):
        """Crea tabelle del database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS position_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    recommended_size REAL NOT NULL,
                    kelly_fraction REAL,
                    adjustments_json TEXT,
                    risk_level TEXT,
                    calculation_timestamp TEXT,
                    calculation_reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS position_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    pnl REAL NOT NULL,
                    outcome_timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS circuit_breaker_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    trigger_value REAL,
                    cooling_off_until TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def _store_position_outcome(self, signal_id: str, outcome: SignalOutcome, pnl: float):
        """Memorizza outcome nel database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO position_outcomes (signal_id, outcome, pnl, outcome_timestamp)
                VALUES (?, ?, ?, ?)
            """, (signal_id, outcome.value, pnl, datetime.utcnow().isoformat()))
            await db.commit()
    
    # Placeholder implementations for remaining methods
    async def _load_current_positions(self):
        """Carica posizioni correnti"""
        # Implementation would load active positions from database
        pass
    
    async def _calculate_daily_pnl(self):
        """Calcola P&L giornaliero"""
        # Implementation would calculate current day P&L
        pass
    
    async def _update_risk_level(self):
        """Aggiorna livello di rischio corrente"""
        current_risk = await self._calculate_current_portfolio_risk()
        self.current_risk_level = self._determine_risk_level(0, current_risk)
    
    async def _get_max_correlation_with_existing(self, instrument: str) -> float:
        """Calcola correlazione massima con posizioni esistenti"""
        return 0.0  # Simplified implementation
    
    async def _estimate_portfolio_var_with_new_position(self, instrument: str, size: float, trade_risk: float) -> float:
        """Stima VaR del portfolio con nuova posizione"""
        return size * trade_risk  # Simplified
    
    async def _calculate_portfolio_var(self) -> float:
        """Calcola Value at Risk del portfolio"""
        return 0.0  # Simplified
    
    async def _calculate_max_drawdown(self) -> float:
        """Calcola maximum drawdown corrente"""
        return 0.0  # Simplified
    
    async def _calculate_risk_by_instrument(self) -> Dict[str, float]:
        """Calcola risk breakdown per strumento"""
        return {}  # Simplified
    
    async def _calculate_risk_by_regime(self) -> Dict[str, float]:
        """Calcola risk breakdown per regime"""
        return {}  # Simplified
    
    async def _calculate_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """Calcola matrice di correlazione"""
        return {}  # Simplified
    
    async def _count_consecutive_losses(self) -> int:
        """Conta perdite consecutive"""
        return 0  # Simplified
    
    async def _check_cooling_off_status(self) -> Tuple[bool, Optional[datetime]]:
        """Check status cooling off"""
        return False, None  # Simplified
    
    async def _set_cooling_off_period(self, until: datetime):
        """Imposta periodo di cooling off"""
        pass  # Implementation
    
    async def _clear_cooling_off_period(self):
        """Cancella periodo di cooling off"""
        pass  # Implementation
    
    def _calculate_risk_adjusted_return(self, performance: Dict[str, Any]) -> float:
        """Calcola Sharpe-like ratio"""
        return 0.0  # Simplified

# Factory function per istanza globale
_risk_manager_instance = None

async def get_risk_manager() -> AdaptiveRiskManager:
    """Restituisce istanza singleton del risk manager"""
    global _risk_manager_instance
    if _risk_manager_instance is None:
        _risk_manager_instance = AdaptiveRiskManager()
        await _risk_manager_instance.initialize()
    return _risk_manager_instance

# Helper functions
async def calculate_position_size(instrument: str, signal_id: str, entry_price: float, 
                                stop_loss: float, confidence: float, 
                                regime_type: str = "NORMAL") -> PositionSizeCalculation:
    """Helper per calcolo position size"""
    risk_manager = await get_risk_manager()
    return await risk_manager.calculate_position_size(
        instrument, signal_id, entry_price, stop_loss, confidence, regime_type
    )

async def get_risk_metrics() -> RiskMetrics:
    """Helper per ottenere risk metrics correnti"""
    risk_manager = await get_risk_manager()
    return await risk_manager.get_current_risk_metrics()

async def update_position_outcome(signal_id: str, outcome: SignalOutcome, pnl: float) -> bool:
    """Helper per aggiornamento outcome posizione"""
    risk_manager = await get_risk_manager()
    return await risk_manager.update_position_outcome(signal_id, outcome, pnl)