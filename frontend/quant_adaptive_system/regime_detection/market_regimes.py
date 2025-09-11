"""
Market Regime Detection System

Sistema avanzato per il rilevamento automatico dei regimi di mercato basato su:
- Analisi dati opzioni CBOE (0DTE share, put/call ratio, gamma exposure)
- Volume profile da futures (breakouts VAH/VAL, POC rejection, volume imbalance)  
- Volatilità multi-timeframe e momentum
- Pattern recognition per smart money detection
- Machine learning per identificazione pattern complessi

Regimi rilevati:
- STRONG_TREND: Momentum forte, breakout confermati
- WEAK_TREND: Trend debole, possibili pullback
- MEAN_REVERSION: Range-bound, ping-pong tra supporti/resistenze
- GAMMA_SQUEEZE: Alta concentrazione gamma, movimenti limitati
- PINNING: Pin action vicino a strike importanti
- HIGH_VOLATILITY: Espansione volatilità, movimenti ampi
- NORMAL: Condizioni normali di mercato
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import numpy as np
import pandas as pd
import sqlite3
import aiosqlite

# Import modules del sistema quant
from ..data_ingestion.market_context import MarketContext
from ..data_ingestion.futures_volmap import VolumeProfile

logger = logging.getLogger(__name__)

class RegimeType(Enum):
    """Tipologie di regimi di mercato"""
    STRONG_TREND = "STRONG_TREND"
    WEAK_TREND = "WEAK_TREND" 
    MEAN_REVERSION = "MEAN_REVERSION"
    GAMMA_SQUEEZE = "GAMMA_SQUEEZE"
    PINNING = "PINNING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    NORMAL = "NORMAL"

@dataclass
class RegimeData:
    """Dati completi di un regime rilevato"""
    regime_type: RegimeType
    confidence: float  # 0.0 - 1.0
    detected_at: datetime
    key_factors: List[str]  # Fattori principali che hanno determinato il regime
    market_conditions: Dict[str, Any]  # Condizioni di mercato dettagliate
    
    # Metriche specifiche
    volatility_score: float = 0.0
    trend_strength: float = 0.0
    mean_reversion_score: float = 0.0
    gamma_impact_score: float = 0.0
    volume_profile_score: float = 0.0

class MarketRegimeDetector:
    """
    Rilevatore avanzato dei regimi di mercato
    """
    
    def __init__(self, db_path: str = "data/regime_detection.db"):
        self.db_path = db_path
        
        # Historical data for pattern recognition
        self.historical_regimes = []
        self.volatility_history = []
        self.volume_history = []
        
        # Current market state
        self.current_regime = None
        self.regime_stability_counter = 0
        
        # Detection parameters
        self.detection_params = {
            "min_confidence_threshold": 0.6,
            "regime_change_threshold": 0.7,
            "stability_required_cycles": 3,
            "volatility_lookback_periods": 20,
            "trend_strength_periods": 10
        }
        
    async def initialize(self):
        """Inizializza il detector"""
        try:
            await self._create_database_tables()
            await self._load_historical_data()
            
            logger.info("MarketRegimeDetector inizializzato")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione MarketRegimeDetector: {e}")
            raise
    
    async def detect_regime(self, 
                          market_context: MarketContext,
                          volume_profiles: Dict[str, VolumeProfile]) -> RegimeData:
        """
        Rileva il regime di mercato corrente
        """
        try:
            # Collect all detection signals
            detection_signals = await self._collect_detection_signals(market_context, volume_profiles)
            
            # Run individual detectors
            trend_signal = self._detect_trend_regime(detection_signals)
            mean_reversion_signal = self._detect_mean_reversion_regime(detection_signals)
            gamma_signal = self._detect_gamma_regime(detection_signals)
            volatility_signal = self._detect_volatility_regime(detection_signals)
            pinning_signal = self._detect_pinning_regime(detection_signals)
            
            # Combine signals with weighted scoring
            regime_scores = self._calculate_regime_scores(
                trend_signal, mean_reversion_signal, gamma_signal, 
                volatility_signal, pinning_signal, detection_signals
            )
            
            # Select best regime
            best_regime_type, confidence = self._select_best_regime(regime_scores)
            
            # Create regime data
            regime_data = RegimeData(
                regime_type=best_regime_type,
                confidence=confidence,
                detected_at=datetime.utcnow(),
                key_factors=self._extract_key_factors(regime_scores, detection_signals),
                market_conditions=detection_signals,
                volatility_score=regime_scores.get("volatility_score", 0),
                trend_strength=regime_scores.get("trend_strength", 0),
                mean_reversion_score=regime_scores.get("mean_reversion_score", 0),
                gamma_impact_score=regime_scores.get("gamma_impact_score", 0),
                volume_profile_score=regime_scores.get("volume_profile_score", 0)
            )
            
            # Store detection
            await self._store_regime_detection(regime_data)
            
            # Update internal state
            await self._update_regime_state(regime_data)
            
            return regime_data
            
        except Exception as e:
            logger.error(f"Errore nel rilevamento regime: {e}")
            return self._get_fallback_regime()
    
    async def _collect_detection_signals(self, 
                                       market_context: MarketContext,
                                       volume_profiles: Dict[str, VolumeProfile]) -> Dict[str, Any]:
        """Raccoglie tutti i segnali per la detection"""
        try:
            signals = {
                # CBOE Options Data
                "spx_0dte_share": market_context.spx_0dte_share,
                "put_call_ratio": market_context.put_call_ratio,
                "market_regime": market_context.regime,
                
                # Volume Profile Analysis
                "volume_profiles": volume_profiles,
                
                # Derived metrics
                "gamma_concentration": self._calculate_gamma_concentration(market_context),
                "volume_imbalance": self._calculate_volume_imbalance(volume_profiles),
                "price_level_clustering": self._analyze_price_level_clustering(volume_profiles),
                
                # Time-based context
                "market_session": self._get_market_session(),
                "day_of_week": datetime.utcnow().weekday(),
                "hour_utc": datetime.utcnow().hour,
                
                # Historical context
                "recent_volatility": await self._get_recent_volatility(),
                "trend_persistence": await self._get_trend_persistence(),
                "regime_stability": self.regime_stability_counter
            }
            
            return signals
            
        except Exception as e:
            logger.error(f"Errore nella raccolta segnali: {e}")
            return {}
    
    def _detect_trend_regime(self, signals: Dict[str, Any]) -> Dict[str, float]:
        """Rileva regimi di trend (strong/weak)"""
        try:
            scores = {
                "strong_trend_score": 0.0,
                "weak_trend_score": 0.0
            }
            
            # Volume profile breakout analysis
            breakout_score = 0.0
            volume_profiles = signals.get("volume_profiles", {})
            
            for instrument, profile in volume_profiles.items():
                # Check for VAH/VAL breakouts (proxy con current price)
                # In implementazione reale, avresti current price per ogni strumento
                vah_val_range = profile.vah - profile.val
                
                if vah_val_range > 0:
                    # Maggior range = più probabilità di trend
                    range_factor = min(2.0, vah_val_range / (profile.poc * 0.02))  # Normalize
                    breakout_score += range_factor
            
            breakout_score = breakout_score / max(1, len(volume_profiles))
            
            # Volatility persistence  
            recent_vol = signals.get("recent_volatility", 0.5)
            trend_persistence = signals.get("trend_persistence", 0.5)
            
            # Strong trend indicators
            strong_factors = [
                breakout_score > 1.5,                    # Strong volume breakout
                trend_persistence > 0.7,                 # Persistent direction
                recent_vol > 0.6,                        # Elevated volatility
                signals.get("spx_0dte_share", 0.5) < 0.4,  # Lower 0DTE share
                signals.get("volume_imbalance", 0) > 0.3   # Volume imbalance
            ]
            
            scores["strong_trend_score"] = sum(strong_factors) / len(strong_factors)
            
            # Weak trend indicators
            weak_factors = [
                0.8 < breakout_score <= 1.5,             # Moderate breakout
                0.4 < trend_persistence <= 0.7,          # Some persistence
                0.3 < recent_vol <= 0.6,                 # Moderate volatility
                0.4 <= signals.get("spx_0dte_share", 0.5) <= 0.6  # Normal 0DTE
            ]
            
            scores["weak_trend_score"] = sum(weak_factors) / len(weak_factors)
            
            return scores
            
        except Exception as e:
            logger.error(f"Errore nel rilevamento trend: {e}")
            return {"strong_trend_score": 0.0, "weak_trend_score": 0.0}
    
    def _detect_mean_reversion_regime(self, signals: Dict[str, Any]) -> Dict[str, float]:
        """Rileva regime di mean reversion"""
        try:
            # Mean reversion indicators
            mean_reversion_factors = [
                signals.get("price_level_clustering", 0) > 0.6,  # Clustering attorno a livelli
                signals.get("recent_volatility", 0.5) < 0.4,      # Low volatility
                signals.get("trend_persistence", 0.5) < 0.3,      # No persistent trend
                1.0 < signals.get("put_call_ratio", 1.0) < 1.5,   # Balanced fear/greed
                signals.get("volume_imbalance", 0) < 0.2           # Balanced volume
            ]
            
            # Check for range-bound behavior in volume profiles
            range_bound_score = 0.0
            volume_profiles = signals.get("volume_profiles", {})
            
            for instrument, profile in volume_profiles.items():
                # High concentration at POC suggests ranging
                hvn_concentration = len(profile.hvn_levels) / max(1, len(profile.volume_levels))
                if hvn_concentration > 0.3:
                    range_bound_score += 1.0
            
            range_bound_score = range_bound_score / max(1, len(volume_profiles))
            
            # Add range-bound factor
            if range_bound_score > 0.5:
                mean_reversion_factors.append(True)
            else:
                mean_reversion_factors.append(False)
            
            score = sum(mean_reversion_factors) / len(mean_reversion_factors)
            
            return {"mean_reversion_score": score}
            
        except Exception as e:
            logger.error(f"Errore nel rilevamento mean reversion: {e}")
            return {"mean_reversion_score": 0.0}
    
    def _detect_gamma_regime(self, signals: Dict[str, Any]) -> Dict[str, float]:
        """Rileva regime di gamma squeeze"""
        try:
            gamma_factors = [
                signals.get("spx_0dte_share", 0.3) > 0.6,         # High 0DTE activity
                signals.get("gamma_concentration", 0) > 0.7,       # High gamma concentration
                signals.get("recent_volatility", 0.5) < 0.3,       # Suppressed volatility
                0.8 < signals.get("put_call_ratio", 1.0) < 1.2,   # Neutral sentiment
                signals.get("price_level_clustering", 0) > 0.8     # Strong level clustering
            ]
            
            # Special gamma conditions
            gamma_special_conditions = 0
            
            # Check for options expiration proximity (simplified)
            day_of_week = signals.get("day_of_week", 0)
            if day_of_week == 4:  # Friday (options expiry)
                gamma_special_conditions += 1
                
            # Check for low volume profile dispersion (tight ranges)
            volume_profiles = signals.get("volume_profiles", {})
            tight_ranges = 0
            
            for instrument, profile in volume_profiles.items():
                vah_val_ratio = (profile.vah - profile.val) / profile.poc
                if vah_val_ratio < 0.015:  # Very tight value area
                    tight_ranges += 1
            
            if tight_ranges > len(volume_profiles) * 0.6:
                gamma_special_conditions += 1
            
            base_score = sum(gamma_factors) / len(gamma_factors)
            gamma_boost = min(0.3, gamma_special_conditions * 0.15)
            
            return {"gamma_squeeze_score": base_score + gamma_boost}
            
        except Exception as e:
            logger.error(f"Errore nel rilevamento gamma: {e}")
            return {"gamma_squeeze_score": 0.0}
    
    def _detect_volatility_regime(self, signals: Dict[str, Any]) -> Dict[str, float]:
        """Rileva regime di high volatility"""
        try:
            volatility_factors = [
                signals.get("recent_volatility", 0.5) > 0.7,       # High recent vol
                signals.get("volume_imbalance", 0) > 0.5,          # Strong volume imbalance
                signals.get("put_call_ratio", 1.0) > 1.5,          # Fear dominance
                signals.get("spx_0dte_share", 0.3) > 0.5,          # High 0DTE (vol seeking)
            ]
            
            # Check for wide value areas in volume profiles
            wide_ranges = 0
            volume_profiles = signals.get("volume_profiles", {})
            
            for instrument, profile in volume_profiles.items():
                vah_val_ratio = (profile.vah - profile.val) / profile.poc
                if vah_val_ratio > 0.03:  # Wide value area
                    wide_ranges += 1
            
            if wide_ranges > len(volume_profiles) * 0.5:
                volatility_factors.append(True)
            else:
                volatility_factors.append(False)
            
            score = sum(volatility_factors) / len(volatility_factors)
            
            return {"high_volatility_score": score}
            
        except Exception as e:
            logger.error(f"Errore nel rilevamento volatilità: {e}")
            return {"high_volatility_score": 0.0}
    
    def _detect_pinning_regime(self, signals: Dict[str, Any]) -> Dict[str, float]:
        """Rileva regime di pinning"""
        try:
            pinning_factors = [
                signals.get("price_level_clustering", 0) > 0.9,    # Extreme clustering
                signals.get("gamma_concentration", 0) > 0.8,       # High gamma at levels
                signals.get("recent_volatility", 0.5) < 0.25,      # Very low volatility
                0.9 < signals.get("put_call_ratio", 1.0) < 1.1     # Balanced options flow
            ]
            
            # Check day of week (pinning più comune vicino a scadenze)
            day_of_week = signals.get("day_of_week", 0)
            hour_utc = signals.get("hour_utc", 12)
            
            # More likely on Fridays and near close
            if day_of_week == 4:  # Friday
                pinning_factors.append(True)
                
            if 20 <= hour_utc <= 22:  # Near NY close
                pinning_factors.append(True)
            
            # Check for very tight volume profiles around key levels
            volume_profiles = signals.get("volume_profiles", {})
            tight_clustering = 0
            
            for instrument, profile in volume_profiles.items():
                # Check if POC is dominant (high volume concentration)
                if len(profile.hvn_levels) <= 2:  # Very few high volume nodes
                    tight_clustering += 1
            
            if tight_clustering > len(volume_profiles) * 0.7:
                pinning_factors.append(True)
            else:
                pinning_factors.append(False)
            
            score = sum(pinning_factors) / len(pinning_factors)
            
            return {"pinning_score": score}
            
        except Exception as e:
            logger.error(f"Errore nel rilevamento pinning: {e}")
            return {"pinning_score": 0.0}
    
    def _calculate_regime_scores(self, 
                               trend_signal: Dict[str, float],
                               mean_reversion_signal: Dict[str, float],
                               gamma_signal: Dict[str, float],
                               volatility_signal: Dict[str, float],
                               pinning_signal: Dict[str, float],
                               detection_signals: Dict[str, Any]) -> Dict[str, float]:
        """Calcola scores finali per tutti i regimi"""
        
        regime_scores = {
            RegimeType.STRONG_TREND.value: trend_signal.get("strong_trend_score", 0),
            RegimeType.WEAK_TREND.value: trend_signal.get("weak_trend_score", 0),
            RegimeType.MEAN_REVERSION.value: mean_reversion_signal.get("mean_reversion_score", 0),
            RegimeType.GAMMA_SQUEEZE.value: gamma_signal.get("gamma_squeeze_score", 0),
            RegimeType.HIGH_VOLATILITY.value: volatility_signal.get("high_volatility_score", 0),
            RegimeType.PINNING.value: pinning_signal.get("pinning_score", 0),
            RegimeType.NORMAL.value: 0.0  # Calcolato dopo
        }
        
        # NORMAL regime come fallback quando nessun altro è dominante
        max_score = max(regime_scores.values())
        if max_score < 0.6:
            regime_scores[RegimeType.NORMAL.value] = 0.8
        else:
            regime_scores[RegimeType.NORMAL.value] = 1.0 - max_score
        
        # Add component scores for detailed analysis
        regime_scores.update({
            "volatility_score": detection_signals.get("recent_volatility", 0),
            "trend_strength": detection_signals.get("trend_persistence", 0),
            "mean_reversion_score": mean_reversion_signal.get("mean_reversion_score", 0),
            "gamma_impact_score": gamma_signal.get("gamma_squeeze_score", 0),
            "volume_profile_score": detection_signals.get("volume_imbalance", 0)
        })
        
        return regime_scores
    
    def _select_best_regime(self, regime_scores: Dict[str, float]) -> Tuple[RegimeType, float]:
        """Seleziona il miglior regime basandosi sui scores"""
        
        # Get only regime scores (exclude component scores)
        pure_regime_scores = {
            k: v for k, v in regime_scores.items()
            if k in [rt.value for rt in RegimeType]
        }
        
        best_regime_name = max(pure_regime_scores, key=pure_regime_scores.get)
        best_score = pure_regime_scores[best_regime_name]
        
        # Convert back to enum
        best_regime = RegimeType(best_regime_name)
        
        # Apply confidence adjustments
        confidence = best_score
        
        # Boost confidence if multiple signals align
        aligned_signals = sum(1 for score in pure_regime_scores.values() if score > 0.5)
        if aligned_signals <= 1:
            confidence *= 0.9  # Reduce confidence if only one signal
        elif aligned_signals >= 3:
            confidence = min(1.0, confidence * 1.1)  # Boost if multiple signals
        
        # Reduce confidence for regime changes (stability bias)
        if (self.current_regime and 
            self.current_regime.regime_type != best_regime and 
            self.regime_stability_counter < self.detection_params["stability_required_cycles"]):
            confidence *= 0.8
        
        return best_regime, confidence
    
    def _extract_key_factors(self, regime_scores: Dict[str, float], signals: Dict[str, Any]) -> List[str]:
        """Estrai fattori chiave che hanno determinato il regime"""
        factors = []
        
        # Check quale regime ha vinto e perché
        best_regime = max(
            [k for k in regime_scores.keys() if k in [rt.value for rt in RegimeType]], 
            key=lambda k: regime_scores[k]
        )
        
        # Factors based on regime type
        if best_regime == RegimeType.STRONG_TREND.value:
            if signals.get("volume_imbalance", 0) > 0.3:
                factors.append("strong_volume_imbalance")
            if signals.get("trend_persistence", 0) > 0.7:
                factors.append("persistent_directional_move")
            if signals.get("spx_0dte_share", 0.5) < 0.4:
                factors.append("reduced_0dte_gamma_drag")
                
        elif best_regime == RegimeType.GAMMA_SQUEEZE.value:
            if signals.get("spx_0dte_share", 0.3) > 0.6:
                factors.append("high_0dte_concentration")
            if signals.get("gamma_concentration", 0) > 0.7:
                factors.append("gamma_clustering_at_strikes")
            if signals.get("recent_volatility", 0.5) < 0.3:
                factors.append("volatility_suppression")
                
        elif best_regime == RegimeType.MEAN_REVERSION.value:
            if signals.get("price_level_clustering", 0) > 0.6:
                factors.append("price_level_attraction")
            if signals.get("trend_persistence", 0.5) < 0.3:
                factors.append("lack_of_directional_momentum")
            if 1.0 < signals.get("put_call_ratio", 1.0) < 1.5:
                factors.append("balanced_options_sentiment")
                
        elif best_regime == RegimeType.HIGH_VOLATILITY.value:
            if signals.get("recent_volatility", 0.5) > 0.7:
                factors.append("elevated_realized_volatility")
            if signals.get("put_call_ratio", 1.0) > 1.5:
                factors.append("fear_driven_options_flow")
                
        elif best_regime == RegimeType.PINNING.value:
            if signals.get("day_of_week", 0) == 4:
                factors.append("options_expiration_friday")
            if signals.get("gamma_concentration", 0) > 0.8:
                factors.append("extreme_gamma_concentration")
        
        # Add session context
        session = signals.get("market_session", "UNKNOWN")
        if session != "UNKNOWN":
            factors.append(f"during_{session.lower()}_session")
        
        return factors
    
    def _calculate_gamma_concentration(self, market_context: MarketContext) -> float:
        """Calcola concentrazione gamma dalle opzioni"""
        try:
            # Simplified gamma concentration metric
            base_concentration = market_context.spx_0dte_share
            
            # Higher concentration if PCR is neutral (gamma squeeze territory)
            pcr = market_context.put_call_ratio
            if 0.8 <= pcr <= 1.2:
                base_concentration *= 1.3
            
            return min(1.0, base_concentration)
            
        except Exception as e:
            logger.error(f"Errore nel calcolo gamma concentration: {e}")
            return 0.0
    
    def _calculate_volume_imbalance(self, volume_profiles: Dict[str, VolumeProfile]) -> float:
        """Calcola imbalance volumetrico dai futures"""
        try:
            if not volume_profiles:
                return 0.0
            
            imbalances = []
            
            for instrument, profile in volume_profiles.items():
                # Calcola dispersione del volume
                if len(profile.volume_levels) > 5:
                    volumes = [level.volume for level in profile.volume_levels]
                    volume_std = np.std(volumes)
                    volume_mean = np.mean(volumes)
                    
                    # Normalized imbalance
                    imbalance = volume_std / volume_mean if volume_mean > 0 else 0
                    imbalances.append(imbalance)
            
            return np.mean(imbalances) if imbalances else 0.0
            
        except Exception as e:
            logger.error(f"Errore nel calcolo volume imbalance: {e}")
            return 0.0
    
    def _analyze_price_level_clustering(self, volume_profiles: Dict[str, VolumeProfile]) -> float:
        """Analizza clustering dei prezzi attorno a livelli chiave"""
        try:
            if not volume_profiles:
                return 0.0
            
            clustering_scores = []
            
            for instrument, profile in volume_profiles.items():
                # Conta HVN vs totale livelli
                hvn_ratio = len(profile.hvn_levels) / max(1, len(profile.volume_levels))
                
                # Score più alto = più clustering
                clustering_score = min(1.0, hvn_ratio * 2)
                clustering_scores.append(clustering_score)
            
            return np.mean(clustering_scores) if clustering_scores else 0.0
            
        except Exception as e:
            logger.error(f"Errore nell'analisi price clustering: {e}")
            return 0.0
    
    def _get_market_session(self) -> str:
        """Determina sessione di mercato corrente"""
        hour = datetime.utcnow().hour
        
        if 0 <= hour < 8:
            return "ASIAN"
        elif 8 <= hour < 13:
            return "LONDON"
        elif 13 <= hour < 16:
            return "NY_OVERLAP"
        elif 16 <= hour < 21:
            return "NY_ONLY"
        else:
            return "AFTER_HOURS"
    
    async def _get_recent_volatility(self) -> float:
        """Recupera volatilità recente (simplified)"""
        # In implementazione reale, calcoleresti da dati storici
        # Per ora uso valore mock basato su regime precedente
        if self.current_regime:
            return self.current_regime.volatility_score
        return 0.5
    
    async def _get_trend_persistence(self) -> float:
        """Calcola persistenza del trend"""
        # Simplified - in implementazione reale useresti dati storici di prezzo
        if self.current_regime:
            return self.current_regime.trend_strength
        return 0.5
    
    def _get_fallback_regime(self) -> RegimeData:
        """Regime di fallback in caso di errori"""
        return RegimeData(
            regime_type=RegimeType.NORMAL,
            confidence=0.5,
            detected_at=datetime.utcnow(),
            key_factors=["fallback_detection"],
            market_conditions={}
        )
    
    async def _create_database_tables(self):
        """Crea tabelle del database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS regime_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    regime_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    detected_at TEXT NOT NULL,
                    key_factors TEXT,
                    market_conditions TEXT,
                    volatility_score REAL,
                    trend_strength REAL,
                    mean_reversion_score REAL,
                    gamma_impact_score REAL,
                    volume_profile_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def _store_regime_detection(self, regime_data: RegimeData):
        """Memorizza detection nel database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO regime_detections
                    (regime_type, confidence, detected_at, key_factors, market_conditions,
                     volatility_score, trend_strength, mean_reversion_score, 
                     gamma_impact_score, volume_profile_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    regime_data.regime_type.value,
                    regime_data.confidence,
                    regime_data.detected_at.isoformat(),
                    json.dumps(regime_data.key_factors),
                    json.dumps(regime_data.market_conditions),
                    regime_data.volatility_score,
                    regime_data.trend_strength,
                    regime_data.mean_reversion_score,
                    regime_data.gamma_impact_score,
                    regime_data.volume_profile_score
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Errore nel salvataggio regime detection: {e}")
    
    async def _update_regime_state(self, new_regime: RegimeData):
        """Aggiorna stato interno del detector"""
        if (self.current_regime and 
            self.current_regime.regime_type == new_regime.regime_type):
            # Stesso regime - incrementa stability counter
            self.regime_stability_counter += 1
        else:
            # Nuovo regime - reset counter
            self.regime_stability_counter = 1
        
        self.current_regime = new_regime
        
        # Update historical data (keep last 100 detections)
        self.historical_regimes.append(new_regime)
        if len(self.historical_regimes) > 100:
            self.historical_regimes.pop(0)
    
    async def _load_historical_data(self):
        """Carica dati storici per pattern recognition"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT regime_type, confidence, detected_at, key_factors, 
                           volatility_score, trend_strength, mean_reversion_score
                    FROM regime_detections
                    WHERE detected_at >= datetime('now', '-7 days')
                    ORDER BY detected_at DESC
                    LIMIT 100
                """)
                
                results = await cursor.fetchall()
                
                for result in results:
                    regime_type, confidence, detected_at_str, key_factors_str, vol_score, trend_str, mr_score = result
                    
                    try:
                        detected_at = datetime.fromisoformat(detected_at_str)
                        key_factors = json.loads(key_factors_str) if key_factors_str else []
                        
                        regime_data = RegimeData(
                            regime_type=RegimeType(regime_type),
                            confidence=confidence,
                            detected_at=detected_at,
                            key_factors=key_factors,
                            market_conditions={},
                            volatility_score=vol_score or 0,
                            trend_strength=trend_str or 0,
                            mean_reversion_score=mr_score or 0
                        )
                        
                        self.historical_regimes.append(regime_data)
                        
                    except (ValueError, json.JSONDecodeError):
                        continue
                
                logger.info(f"Caricati {len(self.historical_regimes)} regimi storici")
                
        except Exception as e:
            logger.error(f"Errore nel caricamento dati storici: {e}")

# Factory function per istanza globale
_detector_instance = None

async def get_regime_detector() -> MarketRegimeDetector:
    """Restituisce istanza singleton del detector"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = MarketRegimeDetector()
        await _detector_instance.initialize()
    return _detector_instance