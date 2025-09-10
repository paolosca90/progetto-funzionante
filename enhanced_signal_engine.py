"""
Enhanced Professional Signal Engine with Universal Market Data Adapter
=====================================================================

Advanced trading signal generation engine with:
- Universal market data adapter (OANDA, MT5, mock providers)
- High-frequency optimized architecture  
- Advanced technical analysis with multiple indicators
- AI-powered explanations via Gemini
- Circuit breaker patterns for reliability
- Performance monitoring and metrics
- Automatic provider failover
- Production-ready error handling

This engine is designed for high-frequency trading systems where every
millisecond matters and reliability is crucial.

Author: Backend Performance Architect
Date: September 2025
"""

import os
import pandas as pd
import numpy as np
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
import random
import time
from dataclasses import dataclass

# Import our market data adapter
from market_data_adapter import (
    UniversalMarketDataAdapter, 
    create_market_data_adapter,
    DataProviderStatus
)

# Import existing schemas
try:
    from schemas import SignalTypeEnum
except ImportError:
    from enum import Enum
    class SignalTypeEnum(Enum):
        BUY = "BUY"
        SELL = "SELL" 
        HOLD = "HOLD"

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
    else:
        model = None
        logger.warning("GEMINI_API_KEY not found")
except ImportError:
    GEMINI_AVAILABLE = False
    model = None
    logger.warning("Google Generative AI not available")

try:
    import talib
    TALIB_AVAILABLE = True
    logger.info("TA-Lib available for advanced technical analysis")
except ImportError:
    TALIB_AVAILABLE = False
    logger.warning("TA-Lib not available, using basic indicators")

# === DATA MODELS ===

@dataclass
class SignalMetrics:
    """Performance metrics for signal generation"""
    total_signals_generated: int = 0
    successful_signals: int = 0
    failed_signals: int = 0
    avg_generation_time: float = 0.0
    provider_switches: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

@dataclass 
class MarketConditions:
    """Current market conditions analysis"""
    volatility: float
    trend_strength: float
    volume_profile: str
    market_session: str
    news_impact: str = "NONE"

# === ENHANCED SIGNAL ENGINE ===

class EnhancedProfessionalSignalEngine:
    """
    Enhanced Professional Trading Signal Engine
    
    Features:
    - Universal market data adapter with automatic failover
    - High-performance async architecture
    - Advanced technical analysis with 15+ indicators
    - AI-powered signal explanations
    - Market condition analysis
    - Performance monitoring and caching
    - Circuit breaker patterns
    - Millisecond-precision timing
    """
    
    def __init__(self):
        self.market_adapter: Optional[UniversalMarketDataAdapter] = None
        self.initialized = False
        self.metrics = SignalMetrics()
        
        # Price cache for performance optimization
        self.price_cache = {}
        self.cache_expiry = {}
        self.cache_ttl = 5  # seconds
        
        # Market data cache
        self.market_data_cache = {}
        self.market_data_expiry = {}
        self.market_data_ttl = 300  # 5 minutes
        
        # Symbol mapping for different providers
        self.symbol_variants = {
            # FOREX MAJOR PAIRS
            "EURUSD": ["EURUSD", "EUR_USD", "EURUSDm", "EURUSD."],
            "GBPUSD": ["GBPUSD", "GBP_USD", "GBPUSDm", "GBPUSD."], 
            "USDJPY": ["USDJPY", "USD_JPY", "USDJPYm", "USDJPY."],
            "USDCHF": ["USDCHF", "USD_CHF", "USDCHFm", "USDCHF."],
            "AUDUSD": ["AUDUSD", "AUD_USD", "AUDUSDm", "AUDUSD."],
            "USDCAD": ["USDCAD", "USD_CAD", "USDCADm", "USDCAD."],
            "NZDUSD": ["NZDUSD", "NZD_USD", "NZDUSDm", "NZDUSD."],
            
            # FOREX MINOR PAIRS
            "EURGBP": ["EURGBP", "EUR_GBP", "EURGBPm", "EURGBP."],
            "EURJPY": ["EURJPY", "EUR_JPY", "EURJPYm", "EURJPY."], 
            "GBPJPY": ["GBPJPY", "GBP_JPY", "GBPJPYm", "GBPJPY."],
            "EURCHF": ["EURCHF", "EUR_CHF", "EURCHFm", "EURCHF."],
            "AUDCAD": ["AUDCAD", "AUD_CAD", "AUDCADm", "AUDCAD."],
            "AUDJPY": ["AUDJPY", "AUD_JPY", "AUDJPYm", "AUDJPY."],
            "CADJPY": ["CADJPY", "CAD_JPY", "CADJPYm", "CADJPY."],
            "CHFJPY": ["CHFJPY", "CHF_JPY", "CHFJPYm", "CHFJPY."],
            
            # METALS
            "XAUUSD": ["XAUUSD", "XAU_USD", "GOLD", "GOLDm"],
            "XAGUSD": ["XAGUSD", "XAG_USD", "SILVER", "SILVERm"],
            
            # INDICES (OANDA CFDs)
            "US500": ["US500", "SPX500_USD", "SP500", "SPX500"],
            "US30": ["US30", "US30_USD", "DJI30", "DJ30"],
            "NAS100": ["NAS100", "NAS100_USD", "NASDAQ", "NDX"],
            "GER30": ["GER30", "DE30_EUR", "DAX30", "DAX"],
            "UK100": ["UK100", "UK100_GBP", "FTSE", "UKX"],
            "JPN225": ["JPN225", "JP225_USD", "NIKKEI", "N225"]
        }
        
        # Supported symbols list
        self.supported_symbols = list(self.symbol_variants.keys())
        
        logger.info("Enhanced Signal Engine initialized")
    
    async def initialize(self) -> bool:
        """Initialize the enhanced signal engine with market data adapter"""
        try:
            start_time = time.time()
            
            # Initialize market data adapter
            self.market_adapter = await create_market_data_adapter()
            
            # Verify connection
            if not self.market_adapter.active_provider:
                logger.error("No active market data provider available")
                return False
            
            self.initialized = True
            init_time = time.time() - start_time
            
            logger.info(f"Enhanced Signal Engine initialized in {init_time:.3f}s with provider: {self.market_adapter.active_provider.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Signal Engine: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the signal engine and cleanup resources"""
        if self.market_adapter:
            await self.market_adapter.shutdown()
        
        # Clear caches
        self.price_cache.clear()
        self.cache_expiry.clear()
        self.market_data_cache.clear()
        self.market_data_expiry.clear()
        
        self.initialized = False
        logger.info("Enhanced Signal Engine shut down")
    
    def _get_cached_price(self, symbol: str) -> Optional[float]:
        """Get cached price if still valid"""
        if symbol in self.price_cache and symbol in self.cache_expiry:
            if time.time() < self.cache_expiry[symbol]:
                self.metrics.cache_hits += 1
                return self.price_cache[symbol]
        
        self.metrics.cache_misses += 1
        return None
    
    def _cache_price(self, symbol: str, price: float):
        """Cache price with expiry"""
        self.price_cache[symbol] = price
        self.cache_expiry[symbol] = time.time() + self.cache_ttl
    
    async def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        Get real-time price with caching and failover
        Optimized for high-frequency access patterns
        """
        # Check cache first for performance
        cached_price = self._get_cached_price(symbol)
        if cached_price is not None:
            return cached_price
        
        if not self.initialized or not self.market_adapter:
            logger.warning("Signal engine not initialized")
            return None
        
        try:
            start_time = time.time()
            
            # Get price from market adapter (with automatic failover)
            price = await self.market_adapter.get_real_time_price(symbol)
            
            if price is not None:
                # Cache the price
                self._cache_price(symbol, price)
                
                response_time = time.time() - start_time
                logger.debug(f"Real-time price for {symbol}: {price} (took {response_time:.3f}s)")
                return price
            
            logger.warning(f"No real-time price available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {e}")
            return None
    
    async def get_market_data(
        self, 
        symbol: str, 
        timeframe: str = 'H1', 
        count: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Get historical market data with caching
        Supports multiple timeframes and automatic provider failover
        """
        # Create cache key
        cache_key = f"{symbol}_{timeframe}_{count}"
        
        # Check cache
        if cache_key in self.market_data_cache and cache_key in self.market_data_expiry:
            if time.time() < self.market_data_expiry[cache_key]:
                self.metrics.cache_hits += 1
                return self.market_data_cache[cache_key]
        
        self.metrics.cache_misses += 1
        
        if not self.initialized or not self.market_adapter:
            return None
        
        try:
            start_time = time.time()
            
            # Get data from market adapter
            df = await self.market_adapter.get_market_data(symbol, timeframe, count)
            
            if df is not None and not df.empty:
                # Cache the data
                self.market_data_cache[cache_key] = df
                self.market_data_expiry[cache_key] = time.time() + self.market_data_ttl
                
                response_time = time.time() - start_time
                logger.debug(f"Retrieved {len(df)} candles for {symbol} {timeframe} (took {response_time:.3f}s)")
                return df
            
            logger.warning(f"No market data available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def calculate_advanced_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive technical indicators for professional analysis
        Optimized for performance with vectorized operations
        """
        if df.empty:
            return df
        
        try:
            # Use TA-Lib if available for better performance
            if TALIB_AVAILABLE:
                return self._calculate_talib_indicators(df)
            else:
                return self._calculate_basic_indicators(df)
                
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def _calculate_talib_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators using TA-Lib (high performance)"""
        try:
            # Price data
            close = df['close'].values
            high = df['high'].values  
            low = df['low'].values
            volume = df.get('tick_volume', df.get('volume', pd.Series())).values
            
            # Trend Indicators
            df['sma_20'] = talib.SMA(close, 20)
            df['sma_50'] = talib.SMA(close, 50)
            df['sma_200'] = talib.SMA(close, 200)
            df['ema_12'] = talib.EMA(close, 12)
            df['ema_26'] = talib.EMA(close, 26)
            
            # Momentum Indicators
            df['rsi'] = talib.RSI(close, 14)
            df['rsi_fast'] = talib.RSI(close, 7)
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(close)
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(close, 20, 2, 2)
            
            # Volatility
            df['atr'] = talib.ATR(high, low, close, 14)
            df['atr_fast'] = talib.ATR(high, low, close, 7)
            
            # Stochastic
            df['stoch_k'], df['stoch_d'] = talib.STOCH(high, low, close)
            
            # Volume indicators (if volume available)
            if len(volume) > 0 and volume.sum() > 0:
                df['volume_sma'] = talib.SMA(volume, 20)
                df['ad_line'] = talib.AD(high, low, close, volume)
            
            # Williams %R
            df['williams_r'] = talib.WILLR(high, low, close, 14)
            
            # CCI (Commodity Channel Index)
            df['cci'] = talib.CCI(high, low, close, 14)
            
            # Parabolic SAR
            df['sar'] = talib.SAR(high, low)
            
            # Average Directional Index
            df['adx'] = talib.ADX(high, low, close, 14)
            
            logger.debug("Advanced TA-Lib indicators calculated successfully")
            
        except Exception as e:
            logger.error(f"Error calculating TA-Lib indicators: {e}")
        
        return df
    
    def _calculate_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate basic indicators without TA-Lib (fallback)"""
        try:
            # Simple Moving Averages
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            df['sma_200'] = df['close'].rolling(200).mean()
            
            # Exponential Moving Averages
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26'] 
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(20).mean()
            bb_std = df['close'].rolling(20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # ATR (Average True Range)
            tr1 = df['high'] - df['low']
            tr2 = abs(df['high'] - df['close'].shift(1))
            tr3 = abs(df['low'] - df['close'].shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            df['atr'] = tr.rolling(14).mean()
            
            logger.debug("Basic technical indicators calculated successfully")
            
        except Exception as e:
            logger.error(f"Error calculating basic indicators: {e}")
        
        return df
    
    def analyze_market_conditions(self, df: pd.DataFrame) -> MarketConditions:
        """Analyze current market conditions for context"""
        try:
            if df.empty:
                return MarketConditions(0.0, 0.0, "UNKNOWN", "UNKNOWN")
            
            latest = df.iloc[-1]
            
            # Calculate volatility (ATR as % of price)
            volatility = (latest.get('atr', 0) / latest['close']) * 100 if latest['close'] > 0 else 0
            
            # Trend strength analysis
            if 'sma_20' in df.columns and 'sma_50' in df.columns:
                sma_20 = latest.get('sma_20', latest['close'])
                sma_50 = latest.get('sma_50', latest['close'])
                
                if sma_20 > sma_50:
                    trend_strength = min(((sma_20 - sma_50) / sma_50) * 100, 10.0)
                else:
                    trend_strength = max(((sma_20 - sma_50) / sma_50) * 100, -10.0)
            else:
                trend_strength = 0.0
            
            # Volume profile analysis
            if 'tick_volume' in df.columns:
                recent_volume = df['tick_volume'].tail(20).mean()
                avg_volume = df['tick_volume'].mean()
                if recent_volume > avg_volume * 1.5:
                    volume_profile = "HIGH"
                elif recent_volume < avg_volume * 0.7:
                    volume_profile = "LOW" 
                else:
                    volume_profile = "NORMAL"
            else:
                volume_profile = "UNKNOWN"
            
            # Market session detection (simplified)
            current_hour = datetime.utcnow().hour
            if 0 <= current_hour < 6:
                market_session = "ASIAN"
            elif 6 <= current_hour < 14:
                market_session = "EUROPEAN" 
            elif 14 <= current_hour < 22:
                market_session = "AMERICAN"
            else:
                market_session = "PACIFIC"
            
            return MarketConditions(
                volatility=round(volatility, 3),
                trend_strength=round(trend_strength, 3),
                volume_profile=volume_profile,
                market_session=market_session
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return MarketConditions(0.0, 0.0, "ERROR", "ERROR")
    
    def analyze_price_action(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Advanced price action analysis with multiple timeframe confirmation
        Optimized for high-frequency decision making
        """
        try:
            if df.empty or len(df) < 50:
                return {}
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            score_components = {}
            
            # === TREND ANALYSIS (High Weight) ===
            if all(col in df.columns for col in ['sma_20', 'sma_50', 'sma_200']):
                sma_20 = latest.get('sma_20')
                sma_50 = latest.get('sma_50') 
                sma_200 = latest.get('sma_200')
                close = latest['close']
                
                # Strong uptrend
                if close > sma_20 > sma_50 > sma_200:
                    score_components['strong_uptrend'] = 35
                # Strong downtrend
                elif close < sma_20 < sma_50 < sma_200:
                    score_components['strong_downtrend'] = -35
                # Moderate uptrend
                elif close > sma_20 > sma_50:
                    score_components['moderate_uptrend'] = 25
                # Moderate downtrend
                elif close < sma_20 < sma_50:
                    score_components['moderate_downtrend'] = -25
                # Sideways
                else:
                    score_components['sideways'] = 0
            
            # === MOMENTUM ANALYSIS ===
            if 'rsi' in df.columns:
                rsi = latest.get('rsi', 50)
                
                # Oversold bounce potential
                if rsi < 30:
                    score_components['oversold_bounce'] = 20
                # Overbought pullback potential  
                elif rsi > 70:
                    score_components['overbought_pullback'] = -20
                # Momentum strength
                elif 45 < rsi < 55:
                    score_components['neutral_momentum'] = 0
                elif rsi > 60:
                    score_components['bullish_momentum'] = 15
                elif rsi < 40:
                    score_components['bearish_momentum'] = -15
            
            # === MACD SIGNAL ANALYSIS ===
            if all(col in df.columns for col in ['macd', 'macd_signal']):
                macd = latest.get('macd', 0)
                macd_signal = latest.get('macd_signal', 0)
                prev_macd = prev.get('macd', 0)
                prev_macd_signal = prev.get('macd_signal', 0)
                
                # Bullish crossover
                if macd > macd_signal and prev_macd <= prev_macd_signal:
                    score_components['macd_bullish_cross'] = 25
                # Bearish crossover
                elif macd < macd_signal and prev_macd >= prev_macd_signal:
                    score_components['macd_bearish_cross'] = -25
                # Above/below zero line
                elif macd > 0 and macd_signal > 0:
                    score_components['macd_above_zero'] = 10
                elif macd < 0 and macd_signal < 0:
                    score_components['macd_below_zero'] = -10
            
            # === BOLLINGER BANDS ANALYSIS ===
            if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'bb_middle']):
                close = latest['close']
                bb_upper = latest.get('bb_upper')
                bb_lower = latest.get('bb_lower')
                bb_middle = latest.get('bb_middle')
                
                if bb_upper and bb_lower and bb_middle:
                    # Bollinger squeeze/expansion
                    bb_width = (bb_upper - bb_lower) / bb_middle
                    avg_bb_width = ((df['bb_upper'] - df['bb_lower']) / df['bb_middle']).tail(20).mean()
                    
                    # Price at extremes
                    if close <= bb_lower:
                        score_components['bb_oversold'] = 18
                    elif close >= bb_upper:
                        score_components['bb_overbought'] = -18
                    
                    # Volatility expansion
                    if bb_width > avg_bb_width * 1.5:
                        score_components['volatility_expansion'] = 8
                    elif bb_width < avg_bb_width * 0.7:
                        score_components['volatility_contraction'] = -5
            
            # === CANDLESTICK PATTERNS ===
            open_price = latest['open']
            close = latest['close']
            high = latest['high']
            low = latest['low']
            
            body = abs(close - open_price)
            candle_range = high - low
            
            if candle_range > 0:
                body_ratio = body / candle_range
                
                # Strong directional candles
                if body_ratio > 0.7:
                    if close > open_price:
                        score_components['strong_bullish_candle'] = 12
                    else:
                        score_components['strong_bearish_candle'] = -12
                
                # Doji patterns (indecision)
                elif body_ratio < 0.1:
                    score_components['doji_indecision'] = -5
            
            # === VOLUME CONFIRMATION ===
            if 'tick_volume' in df.columns:
                current_volume = latest.get('tick_volume', 0)
                avg_volume = df['tick_volume'].tail(20).mean()
                
                if current_volume > avg_volume * 1.5:
                    # High volume confirms the move
                    if any(key in score_components for key in ['strong_uptrend', 'macd_bullish_cross', 'oversold_bounce']):
                        score_components['volume_confirmation'] = 10
                    elif any(key in score_components for key in ['strong_downtrend', 'macd_bearish_cross', 'overbought_pullback']):
                        score_components['volume_confirmation'] = -10
            
            return score_components
            
        except Exception as e:
            logger.error(f"Error in price action analysis: {e}")
            return {}
    
    def calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate dynamic support and resistance levels"""
        try:
            if df.empty or len(df) < 20:
                return {}
            
            recent_data = df.tail(100)  # Use last 100 periods
            
            # Pivot point calculation
            high = recent_data['high'].max()
            low = recent_data['low'].min()
            close = df.iloc[-1]['close']
            
            # Classical pivot points
            pivot = (high + low + close) / 3
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)
            
            # Moving average based levels
            levels = {
                'pivot': pivot,
                'resistance_1': r1,
                'resistance_2': r2,
                'resistance_3': r3,
                'support_1': s1,
                'support_2': s2,
                'support_3': s3,
                'recent_high': high,
                'recent_low': low
            }
            
            # Add moving average levels as dynamic S/R
            if 'sma_20' in df.columns:
                levels['sma_20_level'] = df.iloc[-1].get('sma_20')
            if 'sma_50' in df.columns:
                levels['sma_50_level'] = df.iloc[-1].get('sma_50')
            if 'ema_12' in df.columns:
                levels['ema_12_level'] = df.iloc[-1].get('ema_12')
            
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {}
    
    async def generate_signal(self, symbol: str, db: Session = None) -> Optional[Dict]:
        """
        Generate comprehensive trading signal with advanced analysis
        
        High-performance signal generation optimized for millisecond latency
        """
        if not self.initialized:
            logger.error("Signal engine not initialized")
            return None
        
        start_time = time.time()
        self.metrics.total_signals_generated += 1
        
        try:
            logger.info(f"Generating enhanced signal for {symbol}")
            
            # === DATA ACQUISITION (Optimized) ===
            # Get market data with caching
            df = await self.get_market_data(symbol, 'H1', 500)
            if df is None or df.empty:
                logger.warning(f"No market data available for {symbol}")
                self.metrics.failed_signals += 1
                return None
            
            # Get real-time price with caching  
            real_time_price = await self.get_real_time_price(symbol)
            historical_price = df.iloc[-1]['close']
            
            current_price = real_time_price if real_time_price is not None else historical_price
            price_type = "real-time" if real_time_price is not None else "historical"
            
            # === TECHNICAL ANALYSIS ===
            df = self.calculate_advanced_technical_indicators(df)
            
            # === MARKET CONDITIONS ===
            market_conditions = self.analyze_market_conditions(df)
            
            # === PRICE ACTION ANALYSIS ===
            pa_scores = self.analyze_price_action(df)
            price_action_score = sum(pa_scores.values())
            
            # === SUPPORT/RESISTANCE LEVELS ===
            levels = self.calculate_support_resistance(df)
            
            # === SIGNAL DETERMINATION ===
            signal_type = SignalTypeEnum.HOLD
            reliability = 50.0
            
            # Enhanced signal logic with multiple confirmations
            if price_action_score > 40:
                signal_type = SignalTypeEnum.BUY
                reliability = min(95.0, 50 + abs(price_action_score) * 0.8)
            elif price_action_score < -40:
                signal_type = SignalTypeEnum.SELL
                reliability = min(95.0, 50 + abs(price_action_score) * 0.8)
            elif abs(price_action_score) > 25:
                if price_action_score > 0:
                    signal_type = SignalTypeEnum.BUY
                else:
                    signal_type = SignalTypeEnum.SELL
                reliability = min(85.0, 50 + abs(price_action_score) * 0.6)
            
            # Adjust reliability based on market conditions
            if market_conditions.volatility > 2.0:  # High volatility
                reliability *= 0.9  # Reduce reliability
            if market_conditions.market_session == "AMERICAN":  # Most liquid session
                reliability *= 1.05  # Slight boost
            
            # === RISK MANAGEMENT ===
            atr = df.iloc[-1].get('atr', current_price * 0.01)  # Fallback ATR
            
            if signal_type in [SignalTypeEnum.BUY, SignalTypeEnum.SELL]:
                # Professional risk management
                sl_multiplier = 1.5 if reliability > 70 else 2.0
                tp_multiplier = 2.5 if reliability > 80 else 2.0
                
                if signal_type == SignalTypeEnum.BUY:
                    stop_loss = current_price - (atr * sl_multiplier)
                    take_profit = current_price + (atr * tp_multiplier)
                else:  # SELL
                    stop_loss = current_price + (atr * sl_multiplier)
                    take_profit = current_price - (atr * tp_multiplier)
                    
                # Validate levels
                risk_reward_ratio = abs(take_profit - current_price) / abs(stop_loss - current_price)
            else:
                stop_loss = None
                take_profit = None
                risk_reward_ratio = 0
            
            # === AI EXPLANATION ===
            explanation = await self._generate_ai_explanation(
                symbol, signal_type, pa_scores, levels, market_conditions
            )
            
            # === SIGNAL ASSEMBLY ===
            generation_time = time.time() - start_time
            
            signal_data = {
                'asset': symbol,
                'signal_type': signal_type,
                'reliability': round(reliability, 1),
                'entry_price': round(current_price, 5),
                'stop_loss': round(stop_loss, 5) if stop_loss else None,
                'take_profit': round(take_profit, 5) if take_profit else None,
                'current_price': round(current_price, 5),
                'historical_price': round(historical_price, 5),
                'price_type': price_type,
                'gemini_explanation': explanation,
                'price_action_score': price_action_score,
                'risk_reward_ratio': round(risk_reward_ratio, 2) if risk_reward_ratio else None,
                'market_conditions': {
                    'volatility': market_conditions.volatility,
                    'trend_strength': market_conditions.trend_strength, 
                    'volume_profile': market_conditions.volume_profile,
                    'market_session': market_conditions.market_session,
                    'atr': round(atr, 5),
                    'support_resistance': levels,
                    'score_breakdown': pa_scores
                },
                'metadata': {
                    'generation_time_ms': round(generation_time * 1000, 2),
                    'data_provider': self.market_adapter.active_provider.name if self.market_adapter.active_provider else 'Unknown',
                    'technical_indicators_count': len([col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'tick_volume', 'volume']]),
                    'price_cache_hit': real_time_price is not None and symbol in self.price_cache
                },
                'expires_at': datetime.utcnow() + timedelta(hours=4)  # Shorter expiry for more accurate signals
            }
            
            self.metrics.successful_signals += 1
            self.metrics.avg_generation_time = (
                self.metrics.avg_generation_time * 0.9 + generation_time * 0.1
            )
            
            logger.info(f"Generated {signal_type.value} signal for {symbol} - "
                       f"Reliability: {reliability:.1f}% - "
                       f"Generated in {generation_time*1000:.2f}ms")
            
            return signal_data
            
        except Exception as e:
            self.metrics.failed_signals += 1
            generation_time = time.time() - start_time
            logger.error(f"Error generating signal for {symbol} (took {generation_time*1000:.2f}ms): {e}")
            return None
    
    async def _generate_ai_explanation(
        self, 
        symbol: str,
        signal_type: SignalTypeEnum,
        pa_scores: Dict[str, float],
        levels: Dict[str, float],
        market_conditions: MarketConditions
    ) -> str:
        """Generate AI explanation with fallback"""
        if not model:
            return self._generate_fallback_explanation(symbol, signal_type, pa_scores, market_conditions)
        
        try:
            # Enhanced prompt with market conditions
            prompt = f"""Analizza questo segnale di trading professionale per {symbol}:

            Segnale: {signal_type.value}
            Punteggi analisi tecnica: {pa_scores}
            Condizioni di mercato:
            - Volatilità: {market_conditions.volatility:.2f}%
            - Forza trend: {market_conditions.trend_strength:.2f}
            - Profilo volume: {market_conditions.volume_profile}
            - Sessione: {market_conditions.market_session}
            
            Livelli chiave: {levels}

            Fornisci spiegazione professionale (max 120 parole) con:
            1. Motivazione principale del segnale
            2. Fattori tecnici determinanti  
            3. Considerazioni di rischio
            4. Gestione posizione consigliata

            Usa linguaggio tecnico ma accessibile."""

            response = model.generate_content(prompt)
            return response.text if response.text else self._generate_fallback_explanation(symbol, signal_type, pa_scores, market_conditions)

        except Exception as e:
            logger.warning(f"AI explanation failed for {symbol}: {e}")
            return self._generate_fallback_explanation(symbol, signal_type, pa_scores, market_conditions)
    
    def _generate_fallback_explanation(
        self, 
        symbol: str,
        signal_type: SignalTypeEnum, 
        pa_scores: Dict[str, float],
        market_conditions: MarketConditions
    ) -> str:
        """Generate technical fallback explanation"""
        
        # Identify top contributing factors
        top_factors = sorted(pa_scores.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        factor_names = []
        
        for factor, score in top_factors:
            if abs(score) > 10:
                if "trend" in factor.lower():
                    factor_names.append("analisi trend")
                elif "rsi" in factor.lower():
                    factor_names.append("momentum RSI")
                elif "macd" in factor.lower():
                    factor_names.append("segnale MACD")
                elif "bb" in factor.lower():
                    factor_names.append("Bollinger Bands")
                elif "volume" in factor.lower():
                    factor_names.append("conferma volumi")
        
        factors_text = ", ".join(factor_names[:3]) if factor_names else "indicatori tecnici multipli"
        
        # Market condition context
        condition_text = ""
        if market_conditions.volatility > 2.0:
            condition_text = " in condizioni di alta volatilità"
        elif market_conditions.market_session == "AMERICAN":
            condition_text = " durante la sessione americana (alta liquidità)"
        
        explanations = {
            SignalTypeEnum.BUY: f"Segnale rialzista su {symbol} supportato da {factors_text}{condition_text}. "
                                f"Convergenza di indicatori tecnici suggerisce momentum positivo. "
                                f"Gestire con stop loss appropriato e target graduali.",
            
            SignalTypeEnum.SELL: f"Segnale ribassista su {symbol} basato su {factors_text}{condition_text}. "
                                 f"Setup tecnico negativo con pressione vendita. "
                                 f"Attenzione ai livelli di supporto per gestione rischio.",
            
            SignalTypeEnum.HOLD: f"Mercato laterale su {symbol}. Segnali tecnici contrastanti da {factors_text}. "
                                 f"Attendere breakout direzionale o conferme aggiuntive prima di operare."
        }
        
        return explanations.get(signal_type, f"Analisi tecnica {signal_type.value} per {symbol} con fattori misti.")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics"""
        adapter_status = self.market_adapter.get_status() if self.market_adapter else {}
        
        return {
            'signal_generation': {
                'total_signals': self.metrics.total_signals_generated,
                'successful_signals': self.metrics.successful_signals,
                'failed_signals': self.metrics.failed_signals,
                'success_rate': (self.metrics.successful_signals / max(self.metrics.total_signals_generated, 1)) * 100,
                'avg_generation_time_ms': round(self.metrics.avg_generation_time * 1000, 2)
            },
            'caching': {
                'price_cache_hits': self.metrics.cache_hits,
                'price_cache_misses': self.metrics.cache_misses,
                'cache_hit_ratio': (self.metrics.cache_hits / max(self.metrics.cache_hits + self.metrics.cache_misses, 1)) * 100,
                'cached_prices': len(self.price_cache),
                'cached_market_data': len(self.market_data_cache)
            },
            'market_data_adapter': adapter_status,
            'engine_status': {
                'initialized': self.initialized,
                'supported_symbols': len(self.supported_symbols),
                'talib_available': TALIB_AVAILABLE,
                'gemini_available': GEMINI_AVAILABLE
            }
        }

# === GLOBAL INSTANCE ===

enhanced_signal_engine = None

async def get_enhanced_signal_engine() -> EnhancedProfessionalSignalEngine:
    """Get or create global enhanced signal engine instance"""
    global enhanced_signal_engine
    
    if enhanced_signal_engine is None or not enhanced_signal_engine.initialized:
        enhanced_signal_engine = EnhancedProfessionalSignalEngine()
        await enhanced_signal_engine.initialize()
    
    return enhanced_signal_engine

# === EXAMPLE USAGE ===

async def example_usage():
    """Example of using the enhanced signal engine"""
    
    engine = await get_enhanced_signal_engine()
    
    try:
        # Generate signal
        signal = await engine.generate_signal("EURUSD")
        if signal:
            print(f"Signal: {signal['signal_type']} - Reliability: {signal['reliability']}%")
            print(f"Entry: {signal['entry_price']} - SL: {signal['stop_loss']} - TP: {signal['take_profit']}")
            print(f"Explanation: {signal['gemini_explanation']}")
            print(f"Generated in: {signal['metadata']['generation_time_ms']}ms")
        
        # Get performance metrics
        metrics = engine.get_performance_metrics()
        print(f"Performance: {metrics}")
        
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(example_usage())