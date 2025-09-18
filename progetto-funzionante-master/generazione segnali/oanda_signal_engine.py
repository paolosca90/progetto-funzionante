"""
OANDA Signal Engine v2.0
Professional signal generation using OANDA v20 API and AI analysis
Completely rewritten following OANDA official documentation
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os
import google.generativeai as genai

# Quantistes integration for enhanced index predictions
try:
    from quantistes_integration import QuantistesEnhancer
    QUANTISTES_AVAILABLE = True
except ImportError:
    QUANTISTES_AVAILABLE = False

from oanda_api_client import (
    OANDAClient, OANDAAPIError, OANDACandle, OANDAPrice,
    Granularity, PriceComponent, create_oanda_client
)

# Setup logging
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class TechnicalAnalysis:
    """Technical analysis indicators calculated from OANDA data"""
    # Trend indicators
    rsi: float
    rsi_signal: str  # "oversold", "overbought", "neutral"
    
    # MACD
    macd_line: float
    macd_signal: float
    macd_histogram: float
    macd_trend: str  # "bullish", "bearish", "neutral"
    
    # Bollinger Bands
    bb_upper: float
    bb_lower: float
    bb_middle: float
    bb_position: str  # "above", "below", "middle"
    bb_squeeze: bool
    
    # Moving Averages
    ema_9: float
    ema_21: float
    ema_50: float
    sma_200: float
    ma_trend: str  # "bullish", "bearish", "neutral"
    
    # Volatility
    atr: float
    volatility_level: str  # "low", "medium", "high"
    
    # Volume and momentum
    volume_avg: float
    momentum: float
    
    # Overall technical score (0-1)
    technical_score: float

@dataclass
class MarketContext:
    """Market context and session information"""
    current_price: float
    spread: float
    spread_quality: str  # "tight", "normal", "wide"
    
    market_session: str  # "Tokyo", "London", "New York", "Sydney"
    session_overlap: bool
    volatility_expected: str  # "low", "medium", "high"
    
    trend_strength: float  # 0-1
    support_level: Optional[float]
    resistance_level: Optional[float]

@dataclass
class RiskManagement:
    """Risk management calculations"""
    suggested_stop_loss: float
    suggested_take_profit: float
    risk_reward_ratio: float
    position_size_pct: float  # Percentage of account
    max_loss_amount: float
    probability_success: float

@dataclass
class TradingSignal:
    """Complete trading signal with all analysis"""
    # Basic signal info
    instrument: str
    signal_type: SignalType
    confidence_score: float  # 0-1 scale
    
    # Price levels
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # Risk management
    risk_level: RiskLevel
    risk_reward_ratio: float
    position_size: float
    
    # Analysis components
    technical_analysis: TechnicalAnalysis
    market_context: MarketContext
    risk_management: RiskManagement
    
    # AI analysis
    ai_analysis: str
    reasoning: str
    
    # Metadata
    timeframe: str
    timestamp: datetime
    expires_at: datetime
    
    # Properties for backward compatibility
    @property
    def technical_score(self) -> float:
        return self.technical_analysis.technical_score
    
    @property
    def indicators(self) -> TechnicalAnalysis:
        return self.technical_analysis
    
    @property
    def spread(self) -> float:
        return self.market_context.spread
    
    @property
    def volatility(self) -> float:
        return self.technical_analysis.atr
    
    @property
    def market_session(self) -> str:
        return self.market_context.market_session

class TechnicalAnalyzer:
    """Technical analysis calculator using OANDA data"""
    
    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD indicator"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        exp1 = pd.Series(prices).ewm(span=fast).mean()
        exp2 = pd.Series(prices).ewm(span=slow).mean()
        
        macd_line = exp1.iloc[-1] - exp2.iloc[-1]
        
        # Calculate signal line
        macd_series = exp1 - exp2
        signal_line = macd_series.ewm(span=signal).mean().iloc[-1]
        
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current_price = prices[-1]
            return current_price * 1.01, current_price, current_price * 0.99
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower
    
    @staticmethod
    def calculate_ema(prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.mean(prices)
        
        return pd.Series(prices).ewm(span=period).mean().iloc[-1]
    
    @staticmethod
    def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(high) < 2:
            return 0.01
        
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        
        if len(true_range) < period:
            return np.mean(true_range)
        
        return np.mean(true_range[-period:])

class MarketSessionDetector:
    """Detect current market session and characteristics"""
    
    @staticmethod
    def get_current_session(utc_time: datetime) -> Tuple[str, bool]:
        """
        Get current market session and overlap status
        
        Returns:
            (session_name, is_overlap)
        """
        hour = utc_time.hour
        
        # Session times in UTC
        sessions = {
            "Sydney": (21, 6),    # 21:00 - 06:00 UTC
            "Tokyo": (23, 8),     # 23:00 - 08:00 UTC  
            "London": (7, 16),    # 07:00 - 16:00 UTC
            "New York": (12, 21)  # 12:00 - 21:00 UTC
        }
        
        active_sessions = []
        for session, (start, end) in sessions.items():
            if start > end:  # Crosses midnight
                if hour >= start or hour < end:
                    active_sessions.append(session)
            else:
                if start <= hour < end:
                    active_sessions.append(session)
        
        if len(active_sessions) > 1:
            # Session overlap
            primary_session = active_sessions[0]
            return primary_session, True
        elif len(active_sessions) == 1:
            return active_sessions[0], False
        else:
            return "Off-hours", False

class OANDASignalEngine:
    """
    Professional signal generation engine using OANDA v20 API
    Completely rewritten following official documentation
    """
    
    def __init__(self, api_key: str, account_id: str, environment: str = "practice", gemini_api_key: Optional[str] = None):
        """
        Initialize signal engine
        
        Args:
            api_key: OANDA API key
            account_id: OANDA account ID
            environment: "practice" or "live"
            gemini_api_key: Google Gemini API key for AI analysis
        """
        self.api_key = api_key
        self.account_id = account_id
        self.environment = environment
        self.gemini_api_key = gemini_api_key
        
        # Initialize OANDA client
        self.oanda_client: Optional[OANDAClient] = None
        
        # AI configuration
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini AI configured for market analysis")
        else:
            self.gemini_model = None
            logger.warning("⚠️ No Gemini API key provided - AI analysis disabled")
        
        # Risk management settings
        self.confidence_threshold = 0.60  # 60% minimum confidence for BUY/SELL
        self.max_risk_per_trade = 0.02    # 2% maximum risk per trade
        self.default_rrr = 2.5            # 1:2.5 risk/reward ratio
        
        logger.info(f"OANDA Signal Engine initialized for {environment} environment")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.oanda_client = create_oanda_client(self.api_key, self.account_id, self.environment)
        await self.oanda_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.oanda_client:
            await self.oanda_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def health_check(self) -> bool:
        """Check if engine is ready"""
        try:
            # Auto-initialize client if needed
            if not self.oanda_client:
                self.oanda_client = create_oanda_client(self.api_key, self.account_id, self.environment)
                await self.oanda_client.__aenter__()
            
            return await self.oanda_client.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def _get_market_data(self, instrument: str, granularity: Granularity = Granularity.H1, count: int = 200) -> Tuple[List[OANDACandle], OANDAPrice]:
        """Get market data for analysis"""
        if not self.oanda_client:
            raise OANDAAPIError("OANDA client not initialized")
        
        # Get historical candles
        candles = await self.oanda_client.get_candles(
            instrument=instrument,
            granularity=granularity,
            count=count,
            price_component=PriceComponent.MID
        )
        
        # Get current price
        try:
            current_prices = await self.oanda_client.get_current_prices([instrument])
            if not current_prices:
                raise OANDAAPIError(f"No current price available for {instrument}")
            
            # Debug: Log the pricing data
            current_price = current_prices[0]
            logger.info(f"🔍 OANDA Price Data for {instrument}: bid={current_price.bid}, ask={current_price.ask}, mid={current_price.mid}, spread={current_price.spread}")
            
            # Validate pricing data
            if current_price.bid == 0.0 or current_price.ask == 0.0 or current_price.mid == 1.0:
                logger.error(f"❌ Invalid price data received for {instrument}: bid={current_price.bid}, ask={current_price.ask}, mid={current_price.mid}")
                raise OANDAAPIError(f"Invalid price data for {instrument} - possible API authentication issue")
            
            return candles, current_price
            
        except OANDAAPIError as e:
            if "Invalid API key" in str(e) or "unauthorized access" in str(e):
                logger.error(f"❌ OANDA API Authentication Failed: {e}")
                logger.error(f"❌ Please check OANDA_API_KEY and OANDA_ACCOUNT_ID environment variables")
                logger.error(f"❌ Current API Key (first 10 chars): {self.api_key[:10]}...")
                logger.error(f"❌ Current Account ID: {self.account_id}")
            raise
    
    def _calculate_technical_analysis(self, candles: List[OANDACandle]) -> TechnicalAnalysis:
        """Calculate comprehensive technical analysis"""
        if len(candles) < 50:
            raise ValueError("Insufficient data for technical analysis")
        
        # Convert to numpy arrays
        closes = np.array([c.close for c in candles])
        highs = np.array([c.high for c in candles])
        lows = np.array([c.low for c in candles])
        volumes = np.array([c.volume for c in candles])
        
        # Calculate indicators
        rsi = TechnicalAnalyzer.calculate_rsi(closes)
        macd_line, macd_signal, macd_histogram = TechnicalAnalyzer.calculate_macd(closes)
        bb_upper, bb_middle, bb_lower = TechnicalAnalyzer.calculate_bollinger_bands(closes)
        
        ema_9 = TechnicalAnalyzer.calculate_ema(closes, 9)
        ema_21 = TechnicalAnalyzer.calculate_ema(closes, 21)
        ema_50 = TechnicalAnalyzer.calculate_ema(closes, 50)
        sma_200 = np.mean(closes[-200:]) if len(closes) >= 200 else np.mean(closes)
        
        atr = TechnicalAnalyzer.calculate_atr(highs, lows, closes)
        
        current_price = closes[-1]
        
        # Determine signals
        rsi_signal = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
        macd_trend = "bullish" if macd_line > macd_signal else "bearish"
        bb_position = "above" if current_price > bb_upper else "below" if current_price < bb_lower else "middle"
        bb_squeeze = (bb_upper - bb_lower) < np.std(closes[-20:]) * 1.5
        
        # MA trend
        if ema_9 > ema_21 > ema_50:
            ma_trend = "bullish"
        elif ema_9 < ema_21 < ema_50:
            ma_trend = "bearish"
        else:
            ma_trend = "neutral"
        
        # Volatility level
        atr_percentile = np.percentile(closes[-50:] * 0.02, 70)  # Rough volatility measure
        if atr > atr_percentile * 1.5:
            volatility_level = "high"
        elif atr < atr_percentile * 0.5:
            volatility_level = "low"
        else:
            volatility_level = "medium"
        
        # Calculate overall technical score
        score_components = []
        
        # RSI score
        if 30 <= rsi <= 70:
            score_components.append(0.7)
        elif rsi < 30:
            score_components.append(0.9)  # Oversold = potential buy
        else:
            score_components.append(0.9)  # Overbought = potential sell
        
        # MACD score
        if abs(macd_histogram) > abs(macd_line) * 0.1:
            score_components.append(0.8)
        else:
            score_components.append(0.5)
        
        # MA trend score
        score_components.append(0.8 if ma_trend != "neutral" else 0.4)
        
        # Bollinger Bands score
        if bb_position != "middle":
            score_components.append(0.7)
        else:
            score_components.append(0.5)
        
        technical_score = np.mean(score_components)
        
        return TechnicalAnalysis(
            rsi=rsi,
            rsi_signal=rsi_signal,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            macd_trend=macd_trend,
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            bb_middle=bb_middle,
            bb_position=bb_position,
            bb_squeeze=bb_squeeze,
            ema_9=ema_9,
            ema_21=ema_21,
            ema_50=ema_50,
            sma_200=sma_200,
            ma_trend=ma_trend,
            atr=atr,
            volatility_level=volatility_level,
            volume_avg=np.mean(volumes[-20:]),
            momentum=closes[-1] / closes[-5] - 1 if len(closes) >= 5 else 0,
            technical_score=technical_score
        )
    
    def _analyze_market_context(self, current_price: OANDAPrice, technical: TechnicalAnalysis) -> MarketContext:
        """Analyze market context and session"""
        session, overlap = MarketSessionDetector.get_current_session(datetime.utcnow())
        
        # Spread quality
        spread_pct = (current_price.spread / current_price.mid) * 100
        if spread_pct < 0.02:
            spread_quality = "tight"
        elif spread_pct < 0.05:
            spread_quality = "normal"
        else:
            spread_quality = "wide"
        
        # Expected volatility based on session
        volatility_map = {
            "London": "high",
            "New York": "high", 
            "Tokyo": "medium",
            "Sydney": "low",
            "Off-hours": "low"
        }
        volatility_expected = volatility_map.get(session, "low")
        if overlap:
            volatility_expected = "high"
        
        # Trend strength (simplified)
        trend_strength = min(technical.technical_score * 1.2, 1.0)
        
        return MarketContext(
            current_price=current_price.mid,
            spread=current_price.spread,
            spread_quality=spread_quality,
            market_session=session,
            session_overlap=overlap,
            volatility_expected=volatility_expected,
            trend_strength=trend_strength,
            support_level=technical.bb_lower,
            resistance_level=technical.bb_upper
        )
    
    def _calculate_risk_management(self, current_price: float, technical: TechnicalAnalysis, signal_type: SignalType) -> RiskManagement:
        """Calculate risk management levels with improved precision"""
        atr = technical.atr
        
        # Ensure ATR is meaningful (minimum 0.0001 for forex, proportional for other instruments)
        min_atr = max(current_price * 0.0001, 0.0001)  # 0.01% of price or 0.0001 minimum
        atr = max(atr, min_atr)
        
        if signal_type == SignalType.BUY:
            # More conservative stop loss and better risk/reward calculation
            stop_distance = atr * 1.2  # Slightly tighter stop loss
            stop_loss = current_price - stop_distance
            take_profit = current_price + (stop_distance * self.default_rrr)
            
        elif signal_type == SignalType.SELL:
            # More conservative stop loss and better risk/reward calculation  
            stop_distance = atr * 1.2  # Slightly tighter stop loss
            stop_loss = current_price + stop_distance
            take_profit = current_price - (stop_distance * self.default_rrr)
            
        else:  # HOLD
            # For HOLD signals, provide reasonable levels for reference
            stop_distance = atr * 1.0
            stop_loss = current_price - stop_distance if technical.ma_trend != "bearish" else current_price + stop_distance
            take_profit = current_price + stop_distance if technical.ma_trend != "bearish" else current_price - stop_distance
        
        # Ensure stop loss is meaningful
        stop_distance = abs(current_price - stop_loss)
        profit_distance = abs(take_profit - current_price)
        
        # Calculate risk/reward ratio
        if stop_distance > 0:
            risk_reward = round(profit_distance / stop_distance, 2)
        else:
            risk_reward = 0
        
        # Position size calculation (2% risk)
        position_size_pct = self.max_risk_per_trade
        max_loss = stop_distance * position_size_pct
        
        # Probability based on technical score and signal type
        if signal_type == SignalType.HOLD:
            probability = min(technical.technical_score * 0.8, 0.60)  # Lower probability for HOLD
        else:
            probability = min(technical.technical_score * 1.1, 0.95)
        
        return RiskManagement(
            suggested_stop_loss=round(stop_loss, 5),  # Round to 5 decimal places for precision
            suggested_take_profit=round(take_profit, 5),
            risk_reward_ratio=risk_reward,
            position_size_pct=position_size_pct,
            max_loss_amount=max_loss,
            probability_success=probability
        )
    
    async def _generate_ai_analysis(self, instrument: str, technical: TechnicalAnalysis, market: MarketContext, signal_type: SignalType) -> Tuple[str, str]:
        """Generate AI analysis using Gemini"""
        if not self.gemini_model:
            return "AI analysis not available", "Technical analysis only"
        
        try:
            prompt = f"""
            Analizza questa situazione di trading per {instrument}:
            
            DATI TECNICI:
            - RSI: {technical.rsi:.1f} ({technical.rsi_signal})
            - MACD: {technical.macd_trend} (linea: {technical.macd_line:.5f}, segnale: {technical.macd_signal:.5f})
            - Bollinger: prezzo {technical.bb_position} le bande
            - Trend MA: {technical.ma_trend}
            - Volatilità: {technical.volatility_level}
            - Score tecnico: {technical.technical_score:.1%}
            
            CONTESTO MERCATO:
            - Sessione: {market.market_session} (overlap: {market.session_overlap})
            - Spread: {market.spread_quality}
            - Volatilità attesa: {market.volatility_expected}
            
            SEGNALE GENERATO: {signal_type.value}
            
            Fornisci un'analisi professionale in italiano di max 200 parole che spieghi:
            1. Perché questo segnale è stato generato
            2. I fattori di supporto tecnici principali
            3. I rischi da considerare
            4. Una raccomandazione finale
            
            Usa un tono professionale ma comprensibile.
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, prompt
            )
            
            ai_analysis = response.text.strip()
            
            # Generate reasoning
            if signal_type == SignalType.HOLD:
                reasoning = f"Confidenza insufficiente ({technical.technical_score:.1%} < 60%). " + \
                           f"Fattori: RSI {technical.rsi:.0f}, trend {technical.ma_trend}, volatilità {technical.volatility_level}."
            else:
                reasoning = f"Segnale {signal_type.value} con confidenza {technical.technical_score:.1%}. " + \
                           f"Supportato da: {technical.rsi_signal} RSI, {technical.macd_trend} MACD, trend {technical.ma_trend}."
            
            return ai_analysis, reasoning
            
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            fallback_analysis = f"Analisi tecnica per {instrument}: score {technical.technical_score:.1%}, " + \
                              f"RSI {technical.rsi:.0f}, trend {technical.ma_trend}. " + \
                              f"Sessione {market.market_session} con volatilità {market.volatility_expected}."
            
            reasoning = f"Segnale basato su analisi tecnica: {signal_type.value}"
            return fallback_analysis, reasoning
    
    async def generate_signal(self, instrument: str, timeframe: str = "H1") -> Optional[TradingSignal]:
        """
        Generate trading signal for instrument
        
        Args:
            instrument: Instrument name (e.g., "EUR_USD")
            timeframe: Timeframe (H1, H4, D1)
            
        Returns:
            TradingSignal or None if generation fails
        """
        try:
            logger.info(f"Generating signal for {instrument} on {timeframe}")
            
            # Auto-initialize client if needed
            if not self.oanda_client:
                self.oanda_client = create_oanda_client(self.api_key, self.account_id, self.environment)
                await self.oanda_client.__aenter__()
            
            # Normalize instrument name
            instrument = self.oanda_client.normalize_instrument(instrument)
            
            # Get market data
            granularity = Granularity.H1  # Default to H1
            if timeframe == "H4":
                granularity = Granularity.H4
            elif timeframe == "D1":
                granularity = Granularity.D
            
            candles, current_price = await self._get_market_data(instrument, granularity)
            
            if len(candles) < 50:
                logger.warning(f"Insufficient data for {instrument} - only {len(candles)} candles")
                return None
            
            # Perform technical analysis
            technical = self._calculate_technical_analysis(candles)
            
            # Analyze market context
            market = self._analyze_market_context(current_price, technical)
            
            # Determine signal type based on confidence threshold
            if technical.technical_score >= self.confidence_threshold:
                # Determine direction based on technical factors
                bullish_factors = 0
                bearish_factors = 0
                
                # RSI
                if technical.rsi < 30:
                    bullish_factors += 1
                elif technical.rsi > 70:
                    bearish_factors += 1
                
                # MACD
                if technical.macd_trend == "bullish":
                    bullish_factors += 1
                elif technical.macd_trend == "bearish":
                    bearish_factors += 1
                
                # MA trend
                if technical.ma_trend == "bullish":
                    bullish_factors += 1
                elif technical.ma_trend == "bearish":
                    bearish_factors += 1
                
                # Bollinger position
                if technical.bb_position == "below":
                    bullish_factors += 1
                elif technical.bb_position == "above":
                    bearish_factors += 1
                
                if bullish_factors > bearish_factors:
                    signal_type = SignalType.BUY
                elif bearish_factors > bullish_factors:
                    signal_type = SignalType.SELL
                else:
                    signal_type = SignalType.HOLD
            else:
                signal_type = SignalType.HOLD
            
            # Calculate risk management
            risk_mgmt = self._calculate_risk_management(current_price.mid, technical, signal_type)
            
            # Generate AI analysis
            ai_analysis, reasoning = await self._generate_ai_analysis(instrument, technical, market, signal_type)
            
            # Determine risk level
            if technical.volatility_level == "high" or market.spread_quality == "wide":
                risk_level = RiskLevel.HIGH
            elif technical.volatility_level == "low" and market.spread_quality == "tight":
                risk_level = RiskLevel.LOW
            else:
                risk_level = RiskLevel.MEDIUM
            
            # Create signal
            signal = TradingSignal(
                instrument=instrument,
                signal_type=signal_type,
                confidence_score=technical.technical_score,
                entry_price=current_price.mid,
                stop_loss=risk_mgmt.suggested_stop_loss,
                take_profit=risk_mgmt.suggested_take_profit,
                risk_level=risk_level,
                risk_reward_ratio=risk_mgmt.risk_reward_ratio,
                position_size=risk_mgmt.position_size_pct,
                technical_analysis=technical,
                market_context=market,
                risk_management=risk_mgmt,
                ai_analysis=ai_analysis,
                reasoning=reasoning,
                timeframe=timeframe,
                timestamp=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=4)
            )
            
            confidence_pct = technical.technical_score * 100
            logger.info(f"✅ Generated {signal_type.value} signal for {instrument} (confidence: {confidence_pct:.1f}%)")
            
            return signal
            
        except Exception as e:
            logger.error(f"Signal generation failed for {instrument}: {e}")
            return None
    
    async def generate_signals_batch(self, instruments: List[str], timeframe: str = "H1") -> List[TradingSignal]:
        """Generate signals for multiple instruments"""
        signals = []
        
        # Auto-initialize client if needed
        if not self.oanda_client:
            self.oanda_client = create_oanda_client(self.api_key, self.account_id, self.environment)
            await self.oanda_client.__aenter__()
        
        for instrument in instruments:
            try:
                signal = await self.generate_signal(instrument, timeframe)
                if signal:
                    signals.append(signal)
                    
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to generate signal for {instrument}: {e}")
                continue
        
        return signals

# Factory function
async def create_signal_engine(api_key: str, account_id: str, environment: str = "practice", gemini_api_key: Optional[str] = None) -> OANDASignalEngine:
    """Create and initialize signal engine"""
    return OANDASignalEngine(api_key, account_id, environment, gemini_api_key)
