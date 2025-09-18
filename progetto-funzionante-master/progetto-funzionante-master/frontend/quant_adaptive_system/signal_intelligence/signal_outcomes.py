"""
Signal Outcomes Tracking and Learning System

Questo modulo traccia tutti i segnali generati (reali e simulati), memorizza snapshot
completi dei dati di input, parametri tecnici e outcome, e implementa un sistema
di machine learning per migliorare continuamente le performance.

Features:
- Tracking completo di ogni segnale con snapshot dettagliato
- Calcolo automatico di metriche: R-multiple, MAE, MFE, holding time
- Sistema di learning basato su feature importance
- Adaptive weights per parametri e timeframe
- Export automatico per analisi esterna
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from enum import Enum
import sqlite3
import aiofiles
import aiosqlite

logger = logging.getLogger(__name__)

class SignalOutcome(Enum):
    """Possibili outcome per un segnale"""
    PENDING = "PENDING"      # Segnale aperto, in attesa di outcome
    TP_HIT = "TP_HIT"        # Take Profit raggiunto
    SL_HIT = "SL_HIT"        # Stop Loss raggiunto
    TIMEOUT = "TIMEOUT"      # Scadenza temporale
    MANUAL_EXIT = "MANUAL_EXIT"  # Exit manuale
    CANCELLED = "CANCELLED"   # Segnale cancellato

class SignalType(Enum):
    """Tipologie di segnale"""
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class TechnicalFeatures:
    """Features tecniche al momento del segnale"""
    # Multi-timeframe features
    mtf_rsi_1m: float = 0.0
    mtf_rsi_5m: float = 0.0
    mtf_rsi_15m: float = 0.0
    mtf_rsi_30m: float = 0.0
    
    mtf_macd_1m: str = ""
    mtf_macd_5m: str = ""
    mtf_macd_15m: str = ""
    mtf_macd_30m: str = ""
    
    # Volatility indicators
    atr_1m: float = 0.0
    atr_5m: float = 0.0
    atr_15m: float = 0.0
    atr_30m: float = 0.0
    
    # Bollinger Bands
    bb_position_1m: float = 0.0  # Posizione rispetto alle BB (0=lower, 1=upper)
    bb_position_5m: float = 0.0
    bb_position_15m: float = 0.0
    bb_position_30m: float = 0.0
    
    # Moving averages
    ma_distance_1m: float = 0.0  # Distanza % da MA principale
    ma_distance_5m: float = 0.0
    ma_distance_15m: float = 0.0
    ma_distance_30m: float = 0.0
    
    # Confluence score
    confluence_score: float = 0.0
    signal_strength: float = 0.0

@dataclass
class VolumeProfileFeatures:
    """Features derivate dai dati volume profile"""
    # Distanze da livelli volumetrici (in pips)
    distance_to_poc: float = 0.0
    distance_to_vah: float = 0.0
    distance_to_val: float = 0.0
    
    # Nearest HVN/LVN levels
    nearest_hvn_distance: float = 0.0
    nearest_lvn_distance: float = 0.0
    
    # Context volumetrico
    price_in_value_area: bool = False
    above_poc: bool = False
    volume_context: str = ""  # "HIGH_VOLUME", "LOW_VOLUME", "NEUTRAL"

@dataclass
class MarketContextFeatures:
    """Features del contesto di mercato"""
    # Dati opzioni CBOE
    spx_0dte_share: float = 0.0
    put_call_ratio: float = 0.0
    gamma_exposure_estimate: float = 0.0
    
    # Regime identificato
    market_regime: str = ""  # "NORMAL", "HIGH_0DTE", "GAMMA_SQUEEZE", "PINNING"
    volatility_regime: str = ""  # "LOW", "NORMAL", "HIGH", "EXTREME"
    
    # Session context
    market_session: str = ""  # "ASIAN", "LONDON", "NY_OVERLAP", "NY_ONLY"
    session_volume: str = ""  # "HIGH", "MEDIUM", "LOW"

@dataclass
class SignalSnapshot:
    """Snapshot completo di un segnale al momento della generazione"""
    # Identificazione
    signal_id: str
    timestamp: datetime
    instrument: str
    signal_type: SignalType
    
    # Prezzi e livelli
    entry_price: float
    stop_loss: float
    take_profit: float
    current_price: float
    
    # Risk management
    risk_reward_ratio: float
    position_size_suggested: float
    atr_stop_multiplier: float
    
    # Technical analysis
    technical_features: TechnicalFeatures
    volume_features: VolumeProfileFeatures
    market_context: MarketContextFeatures
    
    # AI Analysis
    ai_reasoning: str
    confidence_score: float
    key_factors: List[str]
    
    # Metadata
    source: str = "ROLLING_GENERATOR"  # "MANUAL", "ROLLING_GENERATOR", "BACKTEST"
    version: str = "1.0"

@dataclass
class SignalOutcomeRecord:
    """Record completo dell'outcome di un segnale"""
    # Riferimento al segnale originale
    signal_id: str
    
    # Outcome tracking
    outcome: SignalOutcome
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None
    
    # Performance metrics
    r_multiple: Optional[float] = None
    mae: Optional[float] = None  # Maximum Adverse Excursion
    mfe: Optional[float] = None  # Maximum Favorable Excursion
    holding_time_minutes: Optional[int] = None
    
    # Analisi post-outcome
    exit_reason: str = ""
    market_condition_at_exit: str = ""
    lessons_learned: List[str] = None
    
    # Metadata
    tracked_since: datetime = None
    last_update: datetime = None

class SignalOutcomeTracker:
    """
    Sistema di tracking degli outcome dei segnali con learning automatico
    """
    
    def __init__(self, db_path: str = "data/signal_outcomes.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Feature importance tracking
        self.feature_weights = {}
        self.learning_history = []
        
        # Performance caching
        self._cached_metrics = {}
        self._cache_timestamp = None
        
    async def initialize(self):
        """Inizializza il database e le tabelle"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS signal_snapshots (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    current_price REAL NOT NULL,
                    risk_reward_ratio REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    ai_reasoning TEXT,
                    technical_features TEXT,
                    volume_features TEXT,
                    market_context TEXT,
                    source TEXT DEFAULT 'ROLLING_GENERATOR',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS signal_outcomes (
                    signal_id TEXT PRIMARY KEY,
                    outcome TEXT NOT NULL,
                    exit_timestamp TEXT,
                    exit_price REAL,
                    r_multiple REAL,
                    mae REAL,
                    mfe REAL,
                    holding_time_minutes INTEGER,
                    exit_reason TEXT,
                    tracked_since TEXT,
                    last_update TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES signal_snapshots (signal_id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS feature_importance (
                    feature_name TEXT PRIMARY KEY,
                    importance_score REAL NOT NULL,
                    update_count INTEGER DEFAULT 1,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS learning_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_signals INTEGER,
                    win_rate REAL,
                    avg_r_multiple REAL,
                    avg_holding_time INTEGER,
                    best_features TEXT,
                    regime_performance TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
            
        logger.info("SignalOutcomeTracker inizializzato correttamente")
    
    async def track_signal(self, snapshot: SignalSnapshot) -> bool:
        """
        Registra un nuovo segnale per il tracking
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO signal_snapshots 
                    (signal_id, timestamp, instrument, signal_type, entry_price, 
                     stop_loss, take_profit, current_price, risk_reward_ratio,
                     confidence_score, ai_reasoning, technical_features, 
                     volume_features, market_context, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.signal_id,
                    snapshot.timestamp.isoformat(),
                    snapshot.instrument,
                    snapshot.signal_type.value,
                    snapshot.entry_price,
                    snapshot.stop_loss,
                    snapshot.take_profit,
                    snapshot.current_price,
                    snapshot.risk_reward_ratio,
                    snapshot.confidence_score,
                    snapshot.ai_reasoning,
                    json.dumps(asdict(snapshot.technical_features)),
                    json.dumps(asdict(snapshot.volume_features)),
                    json.dumps(asdict(snapshot.market_context)),
                    snapshot.source
                ))
                
                # Inizializza outcome record
                await db.execute("""
                    INSERT OR REPLACE INTO signal_outcomes
                    (signal_id, outcome, tracked_since)
                    VALUES (?, ?, ?)
                """, (
                    snapshot.signal_id,
                    SignalOutcome.PENDING.value,
                    datetime.now().isoformat()
                ))
                
                await db.commit()
                
            logger.info(f"Segnale {snapshot.signal_id} registrato per tracking")
            return True
            
        except Exception as e:
            logger.error(f"Errore nel tracking del segnale {snapshot.signal_id}: {e}")
            return False
    
    async def update_signal_outcome(self, signal_id: str, outcome: SignalOutcome, 
                                  exit_price: Optional[float] = None,
                                  exit_reason: str = "") -> bool:
        """
        Aggiorna l'outcome di un segnale e calcola le metriche
        """
        try:
            # Recupera dati originali del segnale
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT entry_price, stop_loss, take_profit, signal_type, timestamp
                    FROM signal_snapshots WHERE signal_id = ?
                """, (signal_id,))
                
                signal_data = await cursor.fetchone()
                if not signal_data:
                    logger.error(f"Segnale {signal_id} non trovato")
                    return False
                
                entry_price, stop_loss, take_profit, signal_type, timestamp_str = signal_data
                
                # Calcola metriche se abbiamo exit_price
                r_multiple = None
                mae = None
                mfe = None
                holding_time_minutes = None
                
                if exit_price is not None:
                    # Calcola R-multiple
                    risk = abs(entry_price - stop_loss)
                    if risk > 0:
                        if signal_type == "BUY":
                            r_multiple = (exit_price - entry_price) / risk
                        else:  # SELL
                            r_multiple = (entry_price - exit_price) / risk
                    
                    # Per semplicità, MAE e MFE vengono calcolate qui
                    # In un sistema completo, dovresti tracciare i prezzi in tempo reale
                    if signal_type == "BUY":
                        mae = min(0, exit_price - entry_price) / risk if risk > 0 else 0
                        mfe = max(0, exit_price - entry_price) / risk if risk > 0 else 0
                    else:
                        mae = min(0, entry_price - exit_price) / risk if risk > 0 else 0
                        mfe = max(0, entry_price - exit_price) / risk if risk > 0 else 0
                    
                    # Calcola holding time
                    signal_timestamp = datetime.fromisoformat(timestamp_str)
                    holding_time_minutes = int((datetime.now() - signal_timestamp).total_seconds() / 60)
                
                # Aggiorna outcome record
                await db.execute("""
                    UPDATE signal_outcomes SET
                        outcome = ?,
                        exit_timestamp = ?,
                        exit_price = ?,
                        r_multiple = ?,
                        mae = ?,
                        mfe = ?,
                        holding_time_minutes = ?,
                        exit_reason = ?,
                        last_update = ?
                    WHERE signal_id = ?
                """, (
                    outcome.value,
                    datetime.now().isoformat() if exit_price is not None else None,
                    exit_price,
                    r_multiple,
                    mae,
                    mfe,
                    holding_time_minutes,
                    exit_reason,
                    datetime.now().isoformat(),
                    signal_id
                ))
                
                await db.commit()
                
            logger.info(f"Outcome aggiornato per segnale {signal_id}: {outcome.value}")
            
            # Se il segnale è completato, triggera learning update
            if outcome in [SignalOutcome.TP_HIT, SignalOutcome.SL_HIT, 
                          SignalOutcome.TIMEOUT, SignalOutcome.MANUAL_EXIT]:
                await self._trigger_learning_update()
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento outcome per {signal_id}: {e}")
            return False
    
    async def get_performance_metrics(self, 
                                    days_back: int = 30,
                                    instrument: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcola metriche di performance per un periodo specifico
        """
        try:
            # Check cache
            cache_key = f"{days_back}_{instrument or 'ALL'}"
            if (self._cache_timestamp and 
                datetime.now() - self._cache_timestamp < timedelta(minutes=15) and
                cache_key in self._cached_metrics):
                return self._cached_metrics[cache_key]
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Query base
                where_clause = "WHERE s.timestamp >= ?"
                params = [cutoff_date.isoformat()]
                
                if instrument:
                    where_clause += " AND s.instrument = ?"
                    params.append(instrument)
                
                cursor = await db.execute(f"""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN o.outcome IN ('TP_HIT', 'MANUAL_EXIT') AND o.r_multiple > 0 THEN 1 END) as wins,
                        COUNT(CASE WHEN o.outcome IN ('SL_HIT', 'MANUAL_EXIT') AND o.r_multiple <= 0 THEN 1 END) as losses,
                        AVG(CASE WHEN o.r_multiple IS NOT NULL THEN o.r_multiple END) as avg_r_multiple,
                        AVG(CASE WHEN o.holding_time_minutes IS NOT NULL THEN o.holding_time_minutes END) as avg_holding_time,
                        MAX(o.r_multiple) as best_trade,
                        MIN(o.r_multiple) as worst_trade,
                        AVG(o.mae) as avg_mae,
                        AVG(o.mfe) as avg_mfe
                    FROM signal_snapshots s
                    LEFT JOIN signal_outcomes o ON s.signal_id = o.signal_id
                    {where_clause}
                """, params)
                
                result = await cursor.fetchone()
                
                if result:
                    total_signals, wins, losses, avg_r_multiple, avg_holding_time, best_trade, worst_trade, avg_mae, avg_mfe = result
                    
                    metrics = {
                        "total_signals": total_signals or 0,
                        "wins": wins or 0,
                        "losses": losses or 0,
                        "win_rate": (wins / total_signals * 100) if total_signals > 0 else 0,
                        "avg_r_multiple": round(avg_r_multiple or 0, 3),
                        "avg_holding_time_hours": round((avg_holding_time or 0) / 60, 2),
                        "best_trade": round(best_trade or 0, 3),
                        "worst_trade": round(worst_trade or 0, 3),
                        "avg_mae": round(avg_mae or 0, 3),
                        "avg_mfe": round(avg_mfe or 0, 3),
                        "expectancy": round((avg_r_multiple or 0) * ((wins or 0) / max(total_signals, 1)), 3),
                        "profit_factor": 0  # Calcolato separatamente
                    }
                    
                    # Calcola profit factor
                    cursor = await db.execute(f"""
                        SELECT 
                            SUM(CASE WHEN o.r_multiple > 0 THEN o.r_multiple ELSE 0 END) as total_profit,
                            SUM(CASE WHEN o.r_multiple < 0 THEN ABS(o.r_multiple) ELSE 0 END) as total_loss
                        FROM signal_snapshots s
                        LEFT JOIN signal_outcomes o ON s.signal_id = o.signal_id
                        {where_clause}
                    """, params)
                    
                    profit_loss = await cursor.fetchone()
                    if profit_loss and profit_loss[1] and profit_loss[1] > 0:
                        metrics["profit_factor"] = round(profit_loss[0] / profit_loss[1], 3)
                    
                    # Cache result
                    self._cached_metrics[cache_key] = metrics
                    self._cache_timestamp = datetime.now()
                    
                    return metrics
                else:
                    return {"error": "No data found"}
                    
        except Exception as e:
            logger.error(f"Errore nel calcolo metriche: {e}")
            return {"error": str(e)}
    
    async def get_regime_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Analizza performance per regime di mercato
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        JSON_EXTRACT(s.market_context, '$.market_regime') as regime,
                        COUNT(*) as total_signals,
                        AVG(CASE WHEN o.r_multiple IS NOT NULL THEN o.r_multiple END) as avg_r_multiple,
                        COUNT(CASE WHEN o.outcome = 'TP_HIT' THEN 1 END) * 100.0 / COUNT(*) as win_rate
                    FROM signal_snapshots s
                    LEFT JOIN signal_outcomes o ON s.signal_id = o.signal_id
                    WHERE s.timestamp >= datetime('now', '-30 days')
                    AND JSON_EXTRACT(s.market_context, '$.market_regime') IS NOT NULL
                    GROUP BY regime
                    ORDER BY avg_r_multiple DESC
                """)
                
                results = await cursor.fetchall()
                
                regime_performance = {}
                for regime, total, avg_r, win_rate in results:
                    if regime:
                        regime_performance[regime] = {
                            "total_signals": total,
                            "avg_r_multiple": round(avg_r or 0, 3),
                            "win_rate": round(win_rate or 0, 2),
                            "expectancy": round((avg_r or 0) * (win_rate or 0) / 100, 3)
                        }
                
                return regime_performance
                
        except Exception as e:
            logger.error(f"Errore nell'analisi performance per regime: {e}")
            return {}
    
    async def _trigger_learning_update(self):
        """
        Triggera aggiornamento del sistema di learning
        """
        try:
            # Calcola feature importance dai segnali recenti
            await self._update_feature_importance()
            
            # Salva snapshot delle metriche per tracking storico
            metrics = await self.get_performance_metrics(days_back=7)
            regime_perf = await self.get_regime_performance()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO learning_metrics
                    (timestamp, total_signals, win_rate, avg_r_multiple, 
                     avg_holding_time, regime_performance)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    metrics.get("total_signals", 0),
                    metrics.get("win_rate", 0),
                    metrics.get("avg_r_multiple", 0),
                    int(metrics.get("avg_holding_time_hours", 0) * 60),
                    json.dumps(regime_perf)
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento learning: {e}")
    
    async def _update_feature_importance(self):
        """
        Aggiorna importance delle feature basandosi sui risultati recenti
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Recupera dati per analisi feature importance
                cursor = await db.execute("""
                    SELECT s.technical_features, o.r_multiple, o.outcome
                    FROM signal_snapshots s
                    JOIN signal_outcomes o ON s.signal_id = o.signal_id
                    WHERE s.timestamp >= datetime('now', '-7 days')
                    AND o.r_multiple IS NOT NULL
                    AND o.outcome IN ('TP_HIT', 'SL_HIT', 'MANUAL_EXIT')
                """)
                
                results = await cursor.fetchall()
                
                if len(results) < 10:  # Minimum data per analisi significativa
                    return
                
                # Prepara dati per analisi
                features_data = []
                outcomes = []
                
                for features_json, r_multiple, outcome in results:
                    try:
                        features = json.loads(features_json)
                        
                        # Converti features in array numerico
                        feature_vector = [
                            features.get("mtf_rsi_1m", 0),
                            features.get("mtf_rsi_5m", 0),
                            features.get("mtf_rsi_15m", 0),
                            features.get("mtf_rsi_30m", 0),
                            features.get("atr_1m", 0),
                            features.get("atr_5m", 0),
                            features.get("atr_15m", 0),
                            features.get("atr_30m", 0),
                            features.get("confluence_score", 0),
                            features.get("signal_strength", 0)
                        ]
                        
                        features_data.append(feature_vector)
                        outcomes.append(r_multiple)
                        
                    except json.JSONDecodeError:
                        continue
                
                if len(features_data) >= 10:
                    # Calcola correlation-based importance
                    feature_names = [
                        "mtf_rsi_1m", "mtf_rsi_5m", "mtf_rsi_15m", "mtf_rsi_30m",
                        "atr_1m", "atr_5m", "atr_15m", "atr_30m",
                        "confluence_score", "signal_strength"
                    ]
                    
                    features_df = pd.DataFrame(features_data, columns=feature_names)
                    outcomes_series = pd.Series(outcomes)
                    
                    # Calcola correlazione tra features e outcome
                    correlations = features_df.corrwith(outcomes_series).abs()
                    
                    # Aggiorna database feature importance
                    for feature_name, importance in correlations.items():
                        if not np.isnan(importance):
                            await db.execute("""
                                INSERT OR REPLACE INTO feature_importance
                                (feature_name, importance_score, update_count, last_updated)
                                VALUES (?, ?, COALESCE((SELECT update_count FROM feature_importance WHERE feature_name = ?) + 1, 1), ?)
                            """, (feature_name, float(importance), feature_name, datetime.now().isoformat()))
                    
                    await db.commit()
                    
                    logger.info(f"Feature importance aggiornata per {len(feature_names)} features")
                
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento feature importance: {e}")
    
    async def export_data_to_csv(self, export_path: str = "data/exports/") -> bool:
        """
        Esporta tutti i dati per analisi esterna
        """
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            async with aiosqlite.connect(self.db_path) as db:
                # Export signals con outcomes
                cursor = await db.execute("""
                    SELECT 
                        s.*,
                        o.outcome,
                        o.exit_timestamp,
                        o.exit_price,
                        o.r_multiple,
                        o.mae,
                        o.mfe,
                        o.holding_time_minutes,
                        o.exit_reason
                    FROM signal_snapshots s
                    LEFT JOIN signal_outcomes o ON s.signal_id = o.signal_id
                    ORDER BY s.timestamp DESC
                """)
                
                results = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                df = pd.DataFrame(results, columns=columns)
                
                # Export CSV principale
                csv_file = export_dir / f"signal_analysis_{timestamp}.csv"
                df.to_csv(csv_file, index=False)
                
                # Export metriche summary
                metrics = await self.get_performance_metrics(days_back=30)
                regime_perf = await self.get_regime_performance()
                
                summary_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "performance_metrics": metrics,
                    "regime_performance": regime_perf,
                    "total_records": len(df)
                }
                
                summary_file = export_dir / f"performance_summary_{timestamp}.json"
                async with aiofiles.open(summary_file, 'w') as f:
                    await f.write(json.dumps(summary_data, indent=2))
                
                logger.info(f"Dati esportati: {csv_file}, {summary_file}")
                return True
                
        except Exception as e:
            logger.error(f"Errore nell'export dati: {e}")
            return False
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """
        Genera insights dal sistema di learning
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Top performing features
                cursor = await db.execute("""
                    SELECT feature_name, importance_score, update_count
                    FROM feature_importance
                    ORDER BY importance_score DESC
                    LIMIT 10
                """)
                
                top_features = await cursor.fetchall()
                
                # Learning trend
                cursor = await db.execute("""
                    SELECT timestamp, win_rate, avg_r_multiple
                    FROM learning_metrics
                    ORDER BY timestamp DESC
                    LIMIT 30
                """)
                
                learning_trend = await cursor.fetchall()
                
                # Performance by timeframe
                cursor = await db.execute("""
                    SELECT 
                        CASE 
                            WHEN JSON_EXTRACT(technical_features, '$.confluence_score') > 0.7 THEN 'HIGH_CONFLUENCE'
                            WHEN JSON_EXTRACT(technical_features, '$.confluence_score') > 0.5 THEN 'MEDIUM_CONFLUENCE'
                            ELSE 'LOW_CONFLUENCE'
                        END as confluence_level,
                        AVG(o.r_multiple) as avg_r_multiple,
                        COUNT(*) as count
                    FROM signal_snapshots s
                    JOIN signal_outcomes o ON s.signal_id = o.signal_id
                    WHERE s.timestamp >= datetime('now', '-30 days')
                    AND o.r_multiple IS NOT NULL
                    GROUP BY confluence_level
                """)
                
                confluence_perf = await cursor.fetchall()
                
                insights = {
                    "top_features": [
                        {"feature": feat, "importance": round(imp, 3), "updates": cnt}
                        for feat, imp, cnt in top_features
                    ],
                    "learning_trend": [
                        {
                            "timestamp": ts,
                            "win_rate": round(wr or 0, 2),
                            "avg_r_multiple": round(ar or 0, 3)
                        }
                        for ts, wr, ar in learning_trend
                    ],
                    "confluence_performance": [
                        {
                            "level": level,
                            "avg_r_multiple": round(ar or 0, 3),
                            "count": cnt
                        }
                        for level, ar, cnt in confluence_perf
                    ],
                    "generated_at": datetime.now().isoformat()
                }
                
                return insights
                
        except Exception as e:
            logger.error(f"Errore nel recupero learning insights: {e}")
            return {"error": str(e)}

# Factory function per istanza globale
_tracker_instance = None

async def get_outcome_tracker() -> SignalOutcomeTracker:
    """Restituisce istanza singleton del tracker"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = SignalOutcomeTracker()
        await _tracker_instance.initialize()
    return _tracker_instance

# Utility functions per integrazione facile
async def track_new_signal(snapshot: SignalSnapshot) -> str:
    """Helper per tracciare un nuovo segnale"""
    tracker = await get_outcome_tracker()
    await tracker.track_signal(snapshot)
    return snapshot.signal_id

async def update_signal_result(signal_id: str, outcome: SignalOutcome, 
                             exit_price: float = None, reason: str = "") -> bool:
    """Helper per aggiornare outcome di un segnale"""
    tracker = await get_outcome_tracker()
    return await tracker.update_signal_outcome(signal_id, outcome, exit_price, reason)

async def get_current_performance(days_back: int = 7) -> Dict[str, Any]:
    """Helper per ottenere performance correnti"""
    tracker = await get_outcome_tracker()
    return await tracker.get_performance_metrics(days_back)
