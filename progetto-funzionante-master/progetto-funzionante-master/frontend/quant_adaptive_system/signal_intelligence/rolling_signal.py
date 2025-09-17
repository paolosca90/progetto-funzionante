"""
Rolling Signal Generation System

Sistema di generazione segnali rolling ogni 5 minuti per auto-validazione
e apprendimento continuo. Integra dati CBOE opzioni, futures volume profile,
e sistema di learning per miglioramenti adattivi.

Features:
- Generazione automatica ogni 5 minuti durante RTH
- Integrazione con market context (opzioni CBOE)
- Utilizzo volume profile da futures (ES, NQ, YM, FDAX)
- Virtual execution per tracking outcome
- Learning automatico e adaptive weights
- Export automatico per analisi
"""

import asyncio
import logging
import json
from datetime import datetime, time, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
import uuid
from pathlib import Path

# Import modules del sistema quant
from ..data_ingestion.market_context import CBOEDataProvider, MarketContext
from ..data_ingestion.futures_volmap import FuturesVolumeMapper, VolumeProfile
from .signal_outcomes import (
    SignalSnapshot, TechnicalFeatures, VolumeProfileFeatures, 
    MarketContextFeatures, SignalType, SignalOutcome, 
    get_outcome_tracker, track_new_signal
)

# Import sistema esistente
import sys
from pathlib import Path
# Add parent directories to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from oanda_api_client import OANDAClient
from oanda_signal_engine import OANDASignalEngine 
from advanced_signal_analyzer import AdvancedSignalAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class RollingSignalConfig:
    """Configurazione per il rolling signal generator"""
    # Timing
    generation_interval_minutes: int = 5
    # Reduced blackout period: only 22:00-23:00 UTC (1 hour instead of 2)
    blackout_start_hour: int = 22  # UTC  
    blackout_end_hour: int = 23    # UTC
    
    # Instruments
    instruments: List[str] = None
    
    # Risk management - increased limits for more signals
    max_concurrent_signals: int = 20  # Increased from 15
    daily_signal_limit: int = 120     # Increased from 80
    min_confidence_threshold: float = 0.4  # Lowered further from 0.45 to 0.4
    
    # Learning settings
    learning_lookback_days: int = 7
    min_signals_for_adaptation: int = 20
    
    def __post_init__(self):
        if self.instruments is None:
            # Default instruments - focus sui major pairs e indici
            self.instruments = [
                "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD",
                "EUR_GBP", "GBP_JPY", "AUD_JPY",
                "SPX500_USD", "NAS100_USD", "US30_USD", "GER40_USD",
                "XAU_USD"  # Gold
            ]

class RollingSignalGenerator:
    """
    Generatore di segnali rolling con learning automatico
    """
    
    def __init__(self, config: RollingSignalConfig = None):
        self.config = config or RollingSignalConfig()
        
        # Core components
        self.oanda_client = None
        self.signal_engine = None
        self.analyzer = None
        
        # Data providers
        self.cboe_provider = CBOEDataProvider()
        self.volume_mapper = FuturesVolumeMapper()
        
        # State tracking
        self.is_running = False
        self.current_signals = {}  # signal_id -> signal_data
        self.daily_signal_count = 0
        self.last_reset_date = None
        
        # Performance tracking
        self.recent_performance = {}
        self.adaptive_weights = {
            "timeframes": {"M1": 1.0, "M5": 2.0, "M15": 3.0, "M30": 4.0},
            "indicators": {"RSI": 1.0, "MACD": 1.0, "BB": 1.0, "ATR": 1.0}
        }
        
    async def initialize(self):
        """Inizializza tutti i componenti necessari"""
        try:
            # Get OANDA credentials from environment
            import os
            api_key = os.getenv("OANDA_API_KEY")
            account_id = os.getenv("OANDA_ACCOUNT_ID") 
            environment = os.getenv("OANDA_ENVIRONMENT", "practice")
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key or not account_id:
                logger.error("OANDA credentials not found in environment variables")
                logger.error("Please set OANDA_API_KEY and OANDA_ACCOUNT_ID")
                raise ValueError("Missing OANDA credentials")
            
            # Inizializza OANDA client with proper credentials
            from oanda_api_client import create_oanda_client
            self.oanda_client = create_oanda_client(api_key, account_id, environment)
            await self.oanda_client.__aenter__()
            
            # Inizializza signal engine with credentials
            self.signal_engine = OANDASignalEngine(api_key, account_id, environment, gemini_api_key)
            
            # Inizializza analyzer with credentials
            self.analyzer = AdvancedSignalAnalyzer(api_key, gemini_api_key=gemini_api_key)
            
            # Inizializza data providers
            await self.cboe_provider.initialize()
            await self.volume_mapper.initialize()
            
            # Inizializza outcome tracker
            await get_outcome_tracker()
            
            # Load adaptive weights da database
            await self._load_adaptive_weights()
            
            logger.info("RollingSignalGenerator inizializzato correttamente")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione RollingSignalGenerator: {e}")
            raise
    
    async def start_rolling_generation(self):
        """Avvia il loop di generazione segnali rolling"""
        if self.is_running:
            logger.warning("Rolling generation già in esecuzione")
            return
            
        self.is_running = True
        logger.info("Avvio rolling signal generation...")
        
        try:
            while self.is_running:
                current_time = datetime.utcnow()
                
                # Check se siamo in orari di mercato
                if self._is_market_hours(current_time):
                    # Reset contatore giornaliero se necessario
                    if self._should_reset_daily_count(current_time):
                        self.daily_signal_count = 0
                        self.last_reset_date = current_time.date()
                        logger.info("Reset contatore giornaliero segnali")
                    
                    # Check limiti giornalieri
                    if self.daily_signal_count < self.config.daily_signal_limit:
                        # Genera segnali per tutti gli strumenti
                        await self._generate_rolling_signals(current_time)
                    else:
                        logger.info(f"Limite giornaliero segnali raggiunto: {self.daily_signal_count}")
                
                # Update existing signals
                await self._update_existing_signals()
                
                # Wait per prossimo ciclo
                await asyncio.sleep(self.config.generation_interval_minutes * 60)
                
        except Exception as e:
            logger.error(f"Errore nel loop rolling generation: {e}")
        finally:
            self.is_running = False
            logger.info("Rolling signal generation terminato")
    
    def stop_rolling_generation(self):
        """Ferma il rolling generation"""
        self.is_running = False
        logger.info("Stop richiesto per rolling signal generation")
    
    async def _generate_rolling_signals(self, timestamp: datetime):
        """Genera segnali per tutti gli strumenti configurati"""
        try:
            # Ottieni contesto di mercato corrente
            market_context = await self._get_current_market_context(timestamp)
            
            # Check se le condizioni di mercato sono favorevoli
            if not self._should_generate_signals(market_context):
                logger.warning(f"Condizioni di mercato estreme rilevate: regime={market_context.regime}, 0DTE={market_context.spx_0dte_share:.1%}, P/C={market_context.put_call_ratio:.2f}")
                logger.info("Skipping signal generation due to truly extreme market conditions")
                return  # Skip completely only in extreme conditions
            
            # Ottieni volume profile corrente
            volume_profiles = await self._get_current_volume_profiles()
            
            signals_generated = 0
            
            for instrument in self.config.instruments:
                try:
                    # Check concurrent signals limit
                    active_signals = len([s for s in self.current_signals.values() 
                                        if s.get('instrument') == instrument and s.get('status') == 'ACTIVE'])
                    
                    if active_signals >= 4:  # Increased from 3 to 4 signals per instrument
                        continue
                    
                    # Genera segnale per questo strumento
                    signal = await self._generate_single_signal(
                        instrument, timestamp, market_context, volume_profiles
                    )
                    
                    if signal:
                        # Track il segnale
                        await track_new_signal(signal)
                        
                        # Aggiungi a tracking locale
                        self.current_signals[signal.signal_id] = {
                            'signal': signal,
                            'instrument': instrument,
                            'timestamp': timestamp,
                            'status': 'ACTIVE'
                        }
                        
                        signals_generated += 1
                        self.daily_signal_count += 1
                        
                        logger.info(f"Generato segnale rolling per {instrument}: {signal.signal_type.value}")
                    
                    # Piccolo delay tra strumenti
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Errore nella generazione segnale per {instrument}: {e}")
                    continue
            
            logger.info(f"Generati {signals_generated} segnali rolling (totale giornaliero: {self.daily_signal_count})")
            
        except Exception as e:
            logger.error(f"Errore nella generazione segnali rolling: {e}")
    
    async def _generate_single_signal(self, 
                                    instrument: str, 
                                    timestamp: datetime,
                                    market_context: MarketContext,
                                    volume_profiles: Dict[str, VolumeProfile]) -> Optional[SignalSnapshot]:
        """Genera un singolo segnale per uno strumento"""
        try:
            # Ottieni dati di mercato
            market_data = await self.oanda_client.get_instrument_data(
                instrument, 
                timeframes=["M1", "M5", "M15", "M30"]
            )
            
            if not market_data:
                return None
            
            # Applica adaptive weights ai dati
            weighted_data = self._apply_adaptive_weights(market_data)
            
            # Esegui analisi tecnica con sistema esistente
            try:
                # Use the existing analyze_symbol method from AdvancedSignalAnalyzer
                advanced_analysis = await self.analyzer.analyze_symbol(instrument)
                
                # Convert to expected format for rolling signal system
                analysis_result = {
                    'confidence': advanced_analysis.confidence_score,
                    'signal': {
                        'direction': advanced_analysis.signal_direction,
                        'entry_price': advanced_analysis.entry_price,
                        'stop_loss': advanced_analysis.stop_loss,
                        'take_profit': advanced_analysis.take_profit,
                        'risk_reward_ratio': advanced_analysis.risk_reward_ratio,
                        'atr_multiplier': 2.0  # Default multiplier
                    },
                    'reasoning': advanced_analysis.ai_reasoning,
                    'key_factors': advanced_analysis.price_action_patterns or []
                }
            except Exception as e:
                logger.warning(f"Advanced analyzer failed for {instrument}: {e}")
                # Fallback to OANDA engine analysis (lowered threshold)
                try:
                    oanda_signal = await self.signal_engine.generate_signal(instrument)
                    if oanda_signal and oanda_signal.confidence_score > 0.4:  # Lowered from 0.5
                        analysis_result = {
                            'confidence': oanda_signal.confidence_score,
                            'signal': {
                                'direction': oanda_signal.signal_type.value,
                                'entry_price': oanda_signal.entry_price,
                                'stop_loss': oanda_signal.stop_loss,
                                'take_profit': oanda_signal.take_profit,
                                'risk_reward_ratio': oanda_signal.risk_reward_ratio,
                                'atr_multiplier': 2.0
                            },
                            'reasoning': oanda_signal.reasoning,
                            'key_factors': []
                        }
                    else:
                        # Generate a basic signal if OANDA also fails but we have market data
                        logger.info(f"Generating basic fallback signal for {instrument}")
                        analysis_result = self._generate_basic_fallback_signal(weighted_data, instrument)
                except Exception as fallback_error:
                    logger.warning(f"OANDA fallback failed for {instrument}: {fallback_error}")
                    # Final fallback - generate basic signal
                    analysis_result = self._generate_basic_fallback_signal(weighted_data, instrument)
            
            if not analysis_result or analysis_result.get('confidence', 0) < self.config.min_confidence_threshold:
                confidence = analysis_result.get('confidence', 0) if analysis_result else 0
                logger.debug(f"Signal rejected for {instrument}: confidence {confidence:.3f} < threshold {self.config.min_confidence_threshold}")
                return None
            
            # Estrai informazioni del segnale
            signal_info = analysis_result.get('signal', {})
            if not signal_info.get('direction'):
                return None
            
            # Crea snapshot completo
            signal_id = f"ROLL_{timestamp.strftime('%Y%m%d_%H%M%S')}_{instrument}_{uuid.uuid4().hex[:8]}"
            
            # Extract technical features
            technical_features = self._extract_technical_features(weighted_data)
            
            # Extract volume profile features
            volume_features = self._extract_volume_features(instrument, volume_profiles, signal_info.get('entry_price', 0))
            
            # Convert market context
            market_context_features = self._convert_market_context(market_context)
            
            # Determina signal type
            signal_type = SignalType.BUY if signal_info['direction'] == 'BUY' else SignalType.SELL
            
            # Crea snapshot
            snapshot = SignalSnapshot(
                signal_id=signal_id,
                timestamp=timestamp,
                instrument=instrument,
                signal_type=signal_type,
                entry_price=signal_info.get('entry_price', 0),
                stop_loss=signal_info.get('stop_loss', 0),
                take_profit=signal_info.get('take_profit', 0),
                current_price=weighted_data.get('M1', {}).get('current_price', 0),
                risk_reward_ratio=signal_info.get('risk_reward_ratio', 0),
                position_size_suggested=self._calculate_position_size(signal_info, market_context),
                atr_stop_multiplier=signal_info.get('atr_multiplier', 2.0),
                technical_features=technical_features,
                volume_features=volume_features,
                market_context=market_context_features,
                ai_reasoning=analysis_result.get('reasoning', ''),
                confidence_score=analysis_result.get('confidence', 0),
                key_factors=analysis_result.get('key_factors', []),
                source="ROLLING_GENERATOR"
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Errore nella generazione segnale singolo per {instrument}: {e}")
            return None
    
    async def _update_existing_signals(self):
        """Aggiorna stato dei segnali esistenti"""
        try:
            signals_to_remove = []
            
            for signal_id, signal_data in self.current_signals.items():
                if signal_data['status'] != 'ACTIVE':
                    continue
                
                signal = signal_data['signal']
                instrument = signal.instrument
                
                try:
                    # Ottieni prezzo corrente
                    current_data = await self.oanda_client.get_current_price(instrument)
                    if not current_data:
                        continue
                    
                    current_price = current_data.get('mid', 0)
                    if current_price == 0:
                        continue
                    
                    # Check se segnale è stato triggered
                    outcome = self._check_signal_outcome(signal, current_price)
                    
                    if outcome != SignalOutcome.PENDING:
                        # Aggiorna outcome nel tracker
                        tracker = await get_outcome_tracker()
                        await tracker.update_signal_outcome(
                            signal_id, outcome, current_price, 
                            f"Virtual execution - {outcome.value}"
                        )
                        
                        # Mark for removal
                        signal_data['status'] = 'COMPLETED'
                        signal_data['outcome'] = outcome
                        signal_data['exit_price'] = current_price
                        signals_to_remove.append(signal_id)
                        
                        logger.info(f"Segnale {signal_id} completato: {outcome.value} @ {current_price}")
                    
                    # Check timeout (24h)
                    elif datetime.utcnow() - signal_data['timestamp'] > timedelta(hours=24):
                        tracker = await get_outcome_tracker()
                        await tracker.update_signal_outcome(
                            signal_id, SignalOutcome.TIMEOUT, current_price, "24h timeout"
                        )
                        
                        signal_data['status'] = 'TIMEOUT'
                        signals_to_remove.append(signal_id)
                        
                        logger.info(f"Segnale {signal_id} scaduto per timeout")
                
                except Exception as e:
                    logger.error(f"Errore nell'aggiornamento segnale {signal_id}: {e}")
                    continue
            
            # Rimuovi segnali completati
            for signal_id in signals_to_remove:
                self.current_signals.pop(signal_id, None)
                
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento segnali esistenti: {e}")
    
    def _check_signal_outcome(self, signal: SignalSnapshot, current_price: float) -> SignalOutcome:
        """Controlla se un segnale ha raggiunto TP o SL"""
        try:
            if signal.signal_type == SignalType.BUY:
                if current_price >= signal.take_profit:
                    return SignalOutcome.TP_HIT
                elif current_price <= signal.stop_loss:
                    return SignalOutcome.SL_HIT
            else:  # SELL
                if current_price <= signal.take_profit:
                    return SignalOutcome.TP_HIT
                elif current_price >= signal.stop_loss:
                    return SignalOutcome.SL_HIT
            
            return SignalOutcome.PENDING
            
        except Exception as e:
            logger.error(f"Errore nel check outcome: {e}")
            return SignalOutcome.PENDING
    
    async def _get_current_market_context(self, timestamp: datetime) -> MarketContext:
        """Ottieni contesto di mercato corrente da CBOE con fallback ottimizzato"""
        try:
            return await self.cboe_provider.get_current_context()
        except Exception as e:
            logger.warning(f"Errore nel recupero market context: {e} - usando fallback favorevole")
            # Return more favorable default context to allow signal generation
            return MarketContext(
                timestamp=timestamp,
                spx_0dte_share=0.25,    # Lower value (more favorable)
                combined_0dte_share=0.25,
                put_call_ratio=0.9,     # Neutral value 
                regime="NORMAL",        # Normal regime allows signals
                key_levels=[]
            )
    
    async def _get_current_volume_profiles(self) -> Dict[str, VolumeProfile]:
        """Ottieni volume profiles correnti da futures"""
        try:
            return await self.volume_mapper.get_all_current_profiles()
        except Exception as e:
            logger.error(f"Errore nel recupero volume profiles: {e}")
            return {}
    
    def _should_generate_signals(self, market_context: MarketContext) -> bool:
        """Determina se le condizioni sono favorevoli per generare segnali"""
        # Much more permissive - allow signals in almost all conditions
        
        # Only skip during absolutely extreme conditions  
        if market_context.regime == "EXTREME_VOLATILITY" and market_context.spx_0dte_share > 0.95:
            logger.info("Skipping signals: Extreme volatility with 95%+ 0DTE share")
            return False
        
        # Extremely high 0DTE share (95%+) - very rare occurrence 
        if market_context.spx_0dte_share > 0.95:
            logger.info(f"Skipping signals: Extremely high 0DTE share: {market_context.spx_0dte_share:.1%}")
            return False
        
        # Only skip on truly extreme put/call ratios (wider range)
        if market_context.put_call_ratio > 5.0 or market_context.put_call_ratio < 0.1:
            logger.info(f"Skipping signals: Extreme P/C ratio: {market_context.put_call_ratio:.2f}")
            return False
        
        # Allow signals in all other conditions including:
        # - High 0DTE activity (up to 95%)
        # - Gamma squeeze (can create opportunities)
        # - High volatility (manageable with proper risk management)
        # - Pinning events (short-term opportunities)
        
        return True
    
    def _is_market_hours(self, timestamp: datetime) -> bool:
        """Check se siamo in orari di mercato - 24h tranne blackout 21:00-23:00 UTC"""
        hour = timestamp.hour
        # Genera segnali 24h/giorno tranne durante blackout 21:00-23:00 UTC (23:00-01:00 CEST)
        # Evita solo il periodo di bassa liquidità tra chiusura NY e apertura Sydney
        return not (self.config.blackout_start_hour <= hour < self.config.blackout_end_hour)
    
    def _should_reset_daily_count(self, timestamp: datetime) -> bool:
        """Check se dobbiamo resettare il contatore giornaliero"""
        return (self.last_reset_date is None or 
                timestamp.date() != self.last_reset_date)
    
    def _apply_adaptive_weights(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Applica pesi adattivi ai dati di mercato"""
        weighted_data = market_data.copy()
        
        # Applica weights ai timeframes
        for tf, weight in self.adaptive_weights["timeframes"].items():
            if tf in weighted_data:
                tf_data = weighted_data[tf]
                
                # Amplifica/attenua segnali basandosi sul weight
                if "rsi" in tf_data:
                    tf_data["rsi_weighted"] = tf_data["rsi"] * weight
                if "macd_signal" in tf_data:
                    tf_data["macd_weight"] = weight
        
        return weighted_data
    
    def _extract_technical_features(self, market_data: Dict[str, Any]) -> TechnicalFeatures:
        """Estrai features tecniche dai dati di mercato"""
        try:
            return TechnicalFeatures(
                mtf_rsi_1m=market_data.get("M1", {}).get("rsi", 0),
                mtf_rsi_5m=market_data.get("M5", {}).get("rsi", 0),
                mtf_rsi_15m=market_data.get("M15", {}).get("rsi", 0),
                mtf_rsi_30m=market_data.get("M30", {}).get("rsi", 0),
                
                mtf_macd_1m=market_data.get("M1", {}).get("macd_signal", ""),
                mtf_macd_5m=market_data.get("M5", {}).get("macd_signal", ""),
                mtf_macd_15m=market_data.get("M15", {}).get("macd_signal", ""),
                mtf_macd_30m=market_data.get("M30", {}).get("macd_signal", ""),
                
                atr_1m=market_data.get("M1", {}).get("atr", 0),
                atr_5m=market_data.get("M5", {}).get("atr", 0),
                atr_15m=market_data.get("M15", {}).get("atr", 0),
                atr_30m=market_data.get("M30", {}).get("atr", 0),
                
                confluence_score=market_data.get("confluence_score", 0),
                signal_strength=market_data.get("signal_strength", 0)
            )
        except Exception as e:
            logger.error(f"Errore nell'estrazione technical features: {e}")
            return TechnicalFeatures()
    
    def _extract_volume_features(self, 
                               instrument: str, 
                               volume_profiles: Dict[str, VolumeProfile], 
                               current_price: float) -> VolumeProfileFeatures:
        """Estrai features da volume profiles"""
        try:
            # Mappa strumento a contratto futures
            contract_mapping = {
                "SPX500_USD": "ES",
                "NAS100_USD": "NQ", 
                "US30_USD": "YM",
                "GER40_USD": "FDAX"
            }
            
            contract = contract_mapping.get(instrument)
            if not contract or contract not in volume_profiles:
                return VolumeProfileFeatures()
            
            profile = volume_profiles[contract]
            
            # Calcola distanze in pips (approssimativamente)
            pip_value = 0.0001 if "USD" in instrument else 0.01
            
            return VolumeProfileFeatures(
                distance_to_poc=abs(current_price - profile.poc) / pip_value,
                distance_to_vah=abs(current_price - profile.vah) / pip_value,
                distance_to_val=abs(current_price - profile.val) / pip_value,
                price_in_value_area=profile.val <= current_price <= profile.vah,
                above_poc=current_price > profile.poc,
                volume_context="HIGH_VOLUME" if len(profile.hvn_levels) > 3 else "NORMAL"
            )
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione volume features: {e}")
            return VolumeProfileFeatures()
    
    def _convert_market_context(self, market_context: MarketContext) -> MarketContextFeatures:
        """Converte MarketContext in MarketContextFeatures"""
        try:
            # Determina session corrente (24h coverage)
            hour = datetime.utcnow().hour
            if 0 <= hour < 8:
                session = "ASIAN"
            elif 8 <= hour < 13:
                session = "LONDON"
            elif 13 <= hour < 16:
                session = "NY_OVERLAP"
            elif 16 <= hour < 21:
                session = "NY_ONLY"
            elif 21 <= hour < 23:
                session = "BLACKOUT"  # Blackout period 21:00-23:00 UTC
            else:  # 23:00-00:00
                session = "ASIAN_OPEN"
            
            return MarketContextFeatures(
                spx_0dte_share=market_context.spx_0dte_share,
                put_call_ratio=market_context.put_call_ratio,
                market_regime=market_context.regime,
                market_session=session
            )
            
        except Exception as e:
            logger.error(f"Errore nella conversione market context: {e}")
            return MarketContextFeatures()
    
    def _calculate_position_size(self, signal_info: Dict[str, Any], market_context: MarketContext) -> float:
        """Calcola position size suggerita basata su volatilità e regime"""
        try:
            base_size = 0.02  # 2% base risk
            
            # Adattamento per regime
            regime_multipliers = {
                "NORMAL": 1.0,
                "HIGH_0DTE": 0.7,
                "GAMMA_SQUEEZE": 0.4,
                "PINNING": 0.6
            }
            
            regime_mult = regime_multipliers.get(market_context.regime, 1.0)
            
            # Adattamento per confidence
            confidence_mult = min(1.5, max(0.5, signal_info.get('confidence', 0.7)))
            
            return base_size * regime_mult * confidence_mult
            
        except Exception as e:
            logger.error(f"Errore nel calcolo position size: {e}")
            return 0.01  # Fallback minimo
    
    async def _load_adaptive_weights(self):
        """Carica adaptive weights dal sistema di learning"""
        try:
            tracker = await get_outcome_tracker()
            insights = await tracker.get_learning_insights()
            
            # Aggiorna weights basandosi su performance recenti
            top_features = insights.get('top_features', [])
            
            for feature_data in top_features[:5]:  # Top 5 features
                feature_name = feature_data['feature']
                importance = feature_data['importance']
                
                # Aggiorna indicator weights
                for indicator in self.adaptive_weights['indicators']:
                    if indicator.lower() in feature_name.lower():
                        self.adaptive_weights['indicators'][indicator] = 1.0 + importance
            
            logger.info("Adaptive weights caricati dal learning system")
            
        except Exception as e:
            logger.error(f"Errore nel caricamento adaptive weights: {e}")
    
    def _generate_basic_fallback_signal(self, market_data: Dict[str, Any], instrument: str) -> Dict[str, Any]:
        """Generate a basic fallback signal when advanced analysis fails"""
        try:
            # Get current price from M1 or M5 timeframe
            current_price = None
            for tf in ["M1", "M5", "M15", "M30"]:
                if tf in market_data and "current_price" in market_data[tf]:
                    current_price = market_data[tf]["current_price"]
                    break
            
            if not current_price:
                logger.error(f"No current price available for fallback signal: {instrument}")
                return None
            
            # Simple RSI-based signal
            rsi = market_data.get("M5", {}).get("rsi", 50)
            
            # Determine direction based on RSI
            if rsi < 35:  # Oversold
                direction = "BUY"
                confidence = 0.45 + (35 - rsi) * 0.01  # Higher confidence for more oversold
            elif rsi > 65:  # Overbought
                direction = "SELL" 
                confidence = 0.45 + (rsi - 65) * 0.01  # Higher confidence for more overbought
            else:
                # Neutral zone - still generate signal but with lower confidence
                direction = "BUY" if rsi < 50 else "SELL"
                confidence = 0.42  # Just above threshold
            
            # Cap confidence
            confidence = min(0.6, confidence)
            
            # Calculate basic levels using 2% rules
            if direction == "BUY":
                stop_loss = current_price * 0.98   # 2% below
                take_profit = current_price * 1.04  # 4% above (2:1 R/R)
            else:  # SELL
                stop_loss = current_price * 1.02   # 2% above
                take_profit = current_price * 0.96  # 4% below (2:1 R/R)
            
            risk_reward = 2.0
            
            return {
                'confidence': confidence,
                'signal': {
                    'direction': direction,
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'risk_reward_ratio': risk_reward,
                    'atr_multiplier': 2.0
                },
                'reasoning': f"Fallback signal based on RSI {rsi:.1f} - {direction} signal",
                'key_factors': [f"RSI {rsi:.1f}", "Basic fallback analysis"]
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback signal for {instrument}: {e}")
            return None
    
    async def get_current_status(self) -> Dict[str, Any]:
        """Restituisce status corrente del rolling generator"""
        return {
            "is_running": self.is_running,
            "active_signals": len([s for s in self.current_signals.values() if s['status'] == 'ACTIVE']),
            "daily_signal_count": self.daily_signal_count,
            "last_reset_date": str(self.last_reset_date) if self.last_reset_date else None,
            "adaptive_weights": self.adaptive_weights,
            "next_generation_in_minutes": self.config.generation_interval_minutes,
            "market_hours_active": self._is_market_hours(datetime.utcnow())
        }

# Factory function per istanza globale
_generator_instance = None

async def get_rolling_generator(config: RollingSignalConfig = None) -> RollingSignalGenerator:
    """Restituisce istanza singleton del rolling generator"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = RollingSignalGenerator(config)
        await _generator_instance.initialize()
    return _generator_instance

# CLI helpers per controllo
async def start_rolling_signals(config: RollingSignalConfig = None):
    """Avvia rolling signal generation"""
    generator = await get_rolling_generator(config)
    await generator.start_rolling_generation()

async def stop_rolling_signals():
    """Ferma rolling signal generation"""
    global _generator_instance
    if _generator_instance:
        _generator_instance.stop_rolling_generation()

async def get_rolling_status() -> Dict[str, Any]:
    """Status del rolling generator"""
    global _generator_instance
    if _generator_instance:
        return await _generator_instance.get_current_status()
    return {"status": "not_initialized"}