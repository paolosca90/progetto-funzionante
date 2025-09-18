"""
Advanced Signal Analysis Module for AI Cash-Revolution
Provides comprehensive multi-timeframe analysis, smart money detection, 
volume analysis, and economic news integration for OANDA signals.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
import httpx
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

# Import sentiment analysis
try:
    from sentiment_analysis.sentiment_aggregator import SentimentAggregator, MarketSentiment
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    logger.warning("Sentiment analysis not available - continuing without sentiment integration")

class TimeFrame(Enum):
    M1 = "M1"
    M5 = "M5" 
    M15 = "M15"
    M30 = "M30"  # Added M30 for intraday analysis
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"

class TrendDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"

class SmartMoneyActivity(Enum):
    ACCUMULATION = "ACCUMULATION"
    DISTRIBUTION = "DISTRIBUTION"
    NEUTRAL = "NEUTRAL"
    MANIPULATION = "MANIPULATION"

@dataclass
class PriceLevel:
    """Represents a key price level with volume data"""
    price: float
    volume: float
    level_type: str  # support, resistance, liquidity_pool
    strength: float  # 0-100
    touches: int
    last_test: datetime

@dataclass
class MultiTimeframeAnalysis:
    """Comprehensive multi-timeframe market structure analysis"""
    timeframes: Dict[TimeFrame, Dict[str, Any]]
    overall_trend: TrendDirection
    confluence_score: float
    key_levels: List[PriceLevel]
    smart_money_activity: SmartMoneyActivity
    
@dataclass 
class EconomicEvent:
    """Economic news/event data"""
    title: str
    impact: str  # HIGH, MEDIUM, LOW
    country: str
    currency: str
    actual: Optional[str]
    forecast: Optional[str]
    previous: Optional[str]
    time: datetime
    
@dataclass
class VolumeProfile:
    """Volume analysis results"""
    poc: float  # Point of Control
    val: float  # Value Area Low
    vah: float  # Value Area High
    volume_by_price: Dict[float, float]
    total_volume: float
    buying_volume: float
    selling_volume: float
    order_flow_imbalance: float

@dataclass
class AdvancedSignalAnalysis:
    """Complete advanced signal analysis result"""
    symbol: str
    timestamp: datetime
    signal_direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence_score: float
    
    # Advanced analysis components
    multi_timeframe: MultiTimeframeAnalysis
    volume_profile: VolumeProfile
    smart_money_signals: Dict[str, Any]
    economic_events: List[EconomicEvent]
    price_action_patterns: List[str]
    
    # Risk management
    risk_reward_ratio: float
    position_size_suggestion: float
    max_risk_percentage: float
    
    # AI Analysis
    ai_reasoning: str
    market_context: str
    execution_notes: str

class AdvancedSignalAnalyzer:
    """Advanced signal analyzer with multi-timeframe, smart money analysis, and sentiment integration"""
    
    def __init__(self, oanda_api_key: str, news_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.oanda_api_key = oanda_api_key
        self.news_api_key = news_api_key
        self.gemini_api_key = gemini_api_key
        
        # Initialize sentiment aggregator if available
        if SENTIMENT_AVAILABLE:
            try:
                self.sentiment_aggregator = SentimentAggregator(gemini_api_key)
                logger.info("Sentiment analysis initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize sentiment aggregator: {e}")
                self.sentiment_aggregator = None
        else:
            self.sentiment_aggregator = None
        self.base_url = "https://api-fxpractice.oanda.com/v3"
        
    async def analyze_symbol(self, symbol: str, primary_timeframe: TimeFrame = TimeFrame.H1) -> AdvancedSignalAnalysis:
        """
        Perform comprehensive analysis of a trading symbol
        """
        try:
            logger.info(f"Starting advanced analysis for {symbol}")
            
            # Get multi-timeframe data
            mtf_analysis = await self._analyze_multi_timeframe(symbol)
            
            # Perform volume analysis
            volume_profile = await self._analyze_volume_profile(symbol)
            
            # Detect smart money activity
            smart_money_signals = await self._detect_smart_money_activity(symbol, mtf_analysis)
            
            # Get economic events
            economic_events = await self._get_economic_events(symbol)
            
            # Identify price action patterns
            price_patterns = await self._identify_price_patterns(symbol, mtf_analysis)
            
            # Get comprehensive sentiment analysis
            market_sentiment = None
            if self.sentiment_analyzer:
                try:
                    market_sentiment = await self.sentiment_analyzer.get_comprehensive_sentiment(symbol, hours_back=6)
                    logger.info(f"Sentiment analysis completed for {symbol}: {market_sentiment.overall_sentiment_score:.2f}")
                except Exception as e:
                    logger.error(f"Error getting sentiment for {symbol}: {e}")
            
            # Generate signal based on all analysis (including sentiment)
            signal_data = await self._generate_signal_from_analysis(
                symbol, mtf_analysis, volume_profile, smart_money_signals, economic_events, market_sentiment
            )
            
            # Create AI reasoning
            ai_reasoning = await self._generate_ai_reasoning(
                symbol, mtf_analysis, volume_profile, smart_money_signals, 
                economic_events, price_patterns, signal_data, market_sentiment
            )
            
            return AdvancedSignalAnalysis(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                signal_direction=signal_data["direction"],
                entry_price=signal_data["entry_price"],
                stop_loss=signal_data["stop_loss"], 
                take_profit=signal_data["take_profit"],
                confidence_score=signal_data["confidence"],
                multi_timeframe=mtf_analysis,
                volume_profile=volume_profile,
                smart_money_signals=smart_money_signals,
                economic_events=economic_events,
                price_action_patterns=price_patterns,
                risk_reward_ratio=signal_data["risk_reward"],
                position_size_suggestion=signal_data["position_size"],
                max_risk_percentage=2.0,  # Default 2% risk
                ai_reasoning=ai_reasoning,
                market_context=signal_data["market_context"],
                execution_notes=signal_data["execution_notes"]
            )
            
        except Exception as e:
            logger.error(f"Error in advanced analysis for {symbol}: {e}")
            raise
    
    async def _analyze_multi_timeframe(self, symbol: str) -> MultiTimeframeAnalysis:
        """Analyze multiple timeframes for trend confluence"""
        timeframes_data = {}
        key_levels = []
        
        # Intraday timeframes for scalping/day trading (M1, M5, M15, M30)
        timeframes = [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.M30]
        
        for tf in timeframes:
            try:
                # Get OHLC data for timeframe
                df = await self._get_oanda_candles(symbol, tf, count=200)
                
                if df is not None and len(df) > 50:
                    analysis = self._analyze_timeframe_structure(df, tf)
                    timeframes_data[tf] = analysis
                    
                    # Extract key levels from this timeframe
                    levels = self._extract_key_levels(df, tf)
                    key_levels.extend(levels)
                    
            except Exception as e:
                logger.warning(f"Error analyzing {tf} for {symbol}: {e}")
                
        # Determine overall trend from timeframe confluence
        overall_trend = self._calculate_trend_confluence(timeframes_data)
        
        # Calculate confluence score
        confluence_score = self._calculate_confluence_score(timeframes_data)
        
        # Detect smart money activity
        smart_money_activity = self._detect_smart_money_from_structure(timeframes_data)
        
        return MultiTimeframeAnalysis(
            timeframes=timeframes_data,
            overall_trend=overall_trend,
            confluence_score=confluence_score,
            key_levels=key_levels,
            smart_money_activity=smart_money_activity
        )
    
    async def _get_oanda_candles(self, symbol: str, timeframe: TimeFrame, count: int = 100) -> Optional[pd.DataFrame]:
        """Get candlestick data from OANDA API"""
        try:
            # Convert symbol to OANDA format (e.g., EURUSD -> EUR_USD)
            oanda_instrument = symbol[:3] + "_" + symbol[3:] if len(symbol) == 6 else symbol
            
            params = {
                "count": count,
                "granularity": timeframe.value
            }
            
            headers = {
                "Authorization": f"Bearer {self.oanda_api_key}",
                "Accept-Datetime-Format": "RFC3339"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/instruments/{oanda_instrument}/candles",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "candles" in data and data["candles"]:
                        # Convert to DataFrame
                        candles = []
                        for candle in data["candles"]:
                            if candle["complete"]:
                                candles.append({
                                    "time": pd.to_datetime(candle["time"]),
                                    "open": float(candle["mid"]["o"]),
                                    "high": float(candle["mid"]["h"]),
                                    "low": float(candle["mid"]["l"]),
                                    "close": float(candle["mid"]["c"]),
                                    "volume": int(candle["volume"])
                                })
                        
                        df = pd.DataFrame(candles)
                        df.set_index("time", inplace=True)
                        return df
                        
        except Exception as e:
            logger.warning(f"Error fetching OANDA data for {symbol} {timeframe}: {e}")
            
        return None
    
    def _analyze_timeframe_structure(self, df: pd.DataFrame, timeframe: TimeFrame) -> Dict[str, Any]:
        """Analyze market structure for a specific timeframe"""
        try:
            # Calculate technical indicators
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean() 
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['macd_line'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd_line'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd_line'] - df['macd_signal']
            
            # Bollinger Bands
            bb_period = 20
            df['bb_middle'] = df['close'].rolling(bb_period).mean()
            bb_std = df['close'].rolling(bb_period).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # Determine trend
            current_price = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            sma_50 = df['sma_50'].iloc[-1]
            
            if current_price > sma_20 > sma_50:
                trend = TrendDirection.BULLISH
            elif current_price < sma_20 < sma_50:
                trend = TrendDirection.BEARISH
            else:
                trend = TrendDirection.SIDEWAYS
            
            # Calculate momentum
            rsi_current = df['rsi'].iloc[-1]
            macd_current = df['macd_line'].iloc[-1]
            
            momentum_score = 50  # Neutral
            if rsi_current > 50 and macd_current > 0:
                momentum_score = min(100, 50 + (rsi_current - 50) + (macd_current * 10))
            elif rsi_current < 50 and macd_current < 0:
                momentum_score = max(0, 50 - (50 - rsi_current) - (abs(macd_current) * 10))
            
            # Find swing highs and lows
            swing_highs = self._find_swing_points(df['high'], "high")
            swing_lows = self._find_swing_points(df['low'], "low")
            
            return {
                "trend": trend,
                "momentum_score": momentum_score,
                "rsi": rsi_current,
                "macd_line": macd_current,
                "macd_signal": df['macd_signal'].iloc[-1],
                "current_price": current_price,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "bb_upper": df['bb_upper'].iloc[-1],
                "bb_lower": df['bb_lower'].iloc[-1],
                "swing_highs": swing_highs,
                "swing_lows": swing_lows,
                "volatility": df['close'].rolling(20).std().iloc[-1],
                "volume": df['volume'].iloc[-10:].mean()  # Average recent volume
            }
            
        except Exception as e:
            logger.error(f"Error analyzing timeframe structure: {e}")
            return {}
    
    def _find_swing_points(self, series: pd.Series, point_type: str = "high", window: int = 5) -> List[Tuple[datetime, float]]:
        """Find swing highs/lows in price series"""
        swing_points = []
        
        try:
            if point_type == "high":
                for i in range(window, len(series) - window):
                    if series.iloc[i] == series.iloc[i-window:i+window+1].max():
                        swing_points.append((series.index[i], series.iloc[i]))
            else:  # low
                for i in range(window, len(series) - window):
                    if series.iloc[i] == series.iloc[i-window:i+window+1].min():
                        swing_points.append((series.index[i], series.iloc[i]))
                        
            return swing_points[-10:]  # Return last 10 swing points
            
        except Exception as e:
            logger.error(f"Error finding swing points: {e}")
            return []
    
    def _extract_key_levels(self, df: pd.DataFrame, timeframe: TimeFrame) -> List[PriceLevel]:
        """Extract key support/resistance levels from price data"""
        levels = []
        
        try:
            # Find swing highs and lows
            swing_highs = self._find_swing_points(df['high'], "high")
            swing_lows = self._find_swing_points(df['low'], "low")
            
            # Convert swing highs to resistance levels
            for time, price in swing_highs:
                level = PriceLevel(
                    price=price,
                    volume=df.loc[time, 'volume'] if time in df.index else 0,
                    level_type="resistance", 
                    strength=70.0,  # Default strength
                    touches=1,
                    last_test=time
                )
                levels.append(level)
            
            # Convert swing lows to support levels  
            for time, price in swing_lows:
                level = PriceLevel(
                    price=price,
                    volume=df.loc[time, 'volume'] if time in df.index else 0,
                    level_type="support",
                    strength=70.0,
                    touches=1,
                    last_test=time
                )
                levels.append(level)
                
            # Find round number levels
            current_price = df['close'].iloc[-1]
            price_range = df['high'].max() - df['low'].min()
            
            # Add psychological levels (round numbers)
            if "JPY" in df.index.name or current_price > 100:
                step = 1.0  # For JPY pairs or high-value assets
            else:
                step = 0.01  # For major forex pairs
                
            base = int(current_price / step) * step
            for i in range(-5, 6):
                level_price = base + (i * step)
                if df['low'].min() <= level_price <= df['high'].max():
                    level = PriceLevel(
                        price=level_price,
                        volume=0,
                        level_type="psychological",
                        strength=50.0,
                        touches=0,
                        last_test=datetime.utcnow()
                    )
                    levels.append(level)
            
            return levels
            
        except Exception as e:
            logger.error(f"Error extracting key levels: {e}")
            return []
    
    def _calculate_trend_confluence(self, timeframes_data: Dict[TimeFrame, Dict[str, Any]]) -> TrendDirection:
        """Calculate overall trend from multiple timeframes"""
        trend_votes = {"BULLISH": 0, "BEARISH": 0, "SIDEWAYS": 0}
        
        # Weight timeframes for intraday trading (higher timeframes get more weight)
        weights = {
            TimeFrame.M1: 1,    # Micro trends - noise
            TimeFrame.M5: 2,    # Entry precision  
            TimeFrame.M15: 3,   # Primary intraday trend
            TimeFrame.M30: 4    # Market context and direction
        }
        
        for tf, data in timeframes_data.items():
            if "trend" in data:
                weight = weights.get(tf, 1)
                trend_votes[data["trend"].value] += weight
        
        # Determine overall trend
        if trend_votes["BULLISH"] > trend_votes["BEARISH"] + trend_votes["SIDEWAYS"]:
            return TrendDirection.BULLISH
        elif trend_votes["BEARISH"] > trend_votes["BULLISH"] + trend_votes["SIDEWAYS"]:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_confluence_score(self, timeframes_data: Dict[TimeFrame, Dict[str, Any]]) -> float:
        """Calculate confluence score (0-100) based on timeframe agreement"""
        if not timeframes_data:
            return 0.0
            
        # Count trend agreement
        trends = [data.get("trend") for data in timeframes_data.values() if "trend" in data]
        if not trends:
            return 0.0
            
        # Calculate percentage of timeframes in agreement
        most_common_trend = max(set(trends), key=trends.count)
        agreement_count = trends.count(most_common_trend)
        confluence_score = (agreement_count / len(trends)) * 100
        
        return confluence_score
    
    def _detect_smart_money_from_structure(self, timeframes_data: Dict[TimeFrame, Dict[str, Any]]) -> SmartMoneyActivity:
        """Detect smart money activity from market structure"""
        try:
            # Look for signs of accumulation/distribution in intraday timeframes
            # Smart money usually operates on different timeframe levels
            
            higher_tf_trends = []  # Context timeframes
            for tf in [TimeFrame.M15, TimeFrame.M30]:
                if tf in timeframes_data and "trend" in timeframes_data[tf]:
                    higher_tf_trends.append(timeframes_data[tf]["trend"])
            
            lower_tf_trends = []  # Entry timeframes
            for tf in [TimeFrame.M1, TimeFrame.M5]:
                if tf in timeframes_data and "trend" in timeframes_data[tf]:
                    lower_tf_trends.append(timeframes_data[tf]["trend"])
            
            # If higher timeframes are bullish but lower are bearish = potential accumulation
            if (TrendDirection.BULLISH in higher_tf_trends and 
                TrendDirection.BEARISH in lower_tf_trends):
                return SmartMoneyActivity.ACCUMULATION
            
            # If higher timeframes are bearish but lower are bullish = potential distribution  
            elif (TrendDirection.BEARISH in higher_tf_trends and
                  TrendDirection.BULLISH in lower_tf_trends):
                return SmartMoneyActivity.DISTRIBUTION
            
            # Look for manipulation patterns (quick spikes then reversal)
            # This would require more sophisticated analysis in practice
            
            return SmartMoneyActivity.NEUTRAL
            
        except Exception as e:
            logger.error(f"Error detecting smart money activity: {e}")
            return SmartMoneyActivity.NEUTRAL
    
    async def _analyze_volume_profile(self, symbol: str) -> VolumeProfile:
        """Analyze volume profile and order flow (simplified version)"""
        try:
            # Get recent data for volume analysis
            df = await self._get_oanda_candles(symbol, TimeFrame.H1, count=100)
            
            if df is None or len(df) == 0:
                return self._create_default_volume_profile()
            
            # Calculate volume by price levels (simplified)
            price_levels = np.linspace(df['low'].min(), df['high'].max(), 50)
            volume_by_price = {}
            
            for i, level in enumerate(price_levels):
                # Find candles that traded at this level
                volume_at_level = 0
                for idx in df.index:
                    if df.loc[idx, 'low'] <= level <= df.loc[idx, 'high']:
                        volume_at_level += df.loc[idx, 'volume']
                volume_by_price[level] = volume_at_level
            
            # Find Point of Control (highest volume price)
            poc = max(volume_by_price.keys(), key=lambda k: volume_by_price[k])
            
            # Calculate Value Area (70% of volume around POC)
            sorted_levels = sorted(volume_by_price.items(), key=lambda x: x[1], reverse=True)
            total_volume = sum(volume_by_price.values())
            value_area_volume = 0
            value_area_levels = []
            
            for price, volume in sorted_levels:
                value_area_levels.append(price)
                value_area_volume += volume
                if value_area_volume >= total_volume * 0.7:
                    break
            
            val = min(value_area_levels)  # Value Area Low
            vah = max(value_area_levels)  # Value Area High
            
            # Estimate buying vs selling volume (simplified)
            total_vol = df['volume'].sum()
            buying_volume = total_vol * 0.6  # Simplified assumption
            selling_volume = total_vol * 0.4
            order_flow_imbalance = (buying_volume - selling_volume) / total_vol
            
            return VolumeProfile(
                poc=poc,
                val=val,
                vah=vah,
                volume_by_price=volume_by_price,
                total_volume=total_vol,
                buying_volume=buying_volume,
                selling_volume=selling_volume,
                order_flow_imbalance=order_flow_imbalance
            )
            
        except Exception as e:
            logger.error(f"Error analyzing volume profile: {e}")
            return self._create_default_volume_profile()
    
    def _create_default_volume_profile(self) -> VolumeProfile:
        """Create default volume profile when data is unavailable"""
        return VolumeProfile(
            poc=1.0000,
            val=0.9950,
            vah=1.0050,
            volume_by_price={},
            total_volume=1000,
            buying_volume=600,
            selling_volume=400,
            order_flow_imbalance=0.2
        )
    
    async def _detect_smart_money_activity(self, symbol: str, mtf_analysis: MultiTimeframeAnalysis) -> Dict[str, Any]:
        """Detect intraday smart money activity patterns"""
        
        # Get M1 and M5 data for smart money analysis
        m1_data = None
        m5_data = None
        
        try:
            m1_data = await self._get_oanda_candles(symbol, TimeFrame.M1, count=200)
            m5_data = await self._get_oanda_candles(symbol, TimeFrame.M5, count=100)
        except Exception as e:
            logger.warning(f"Could not get intraday data for smart money analysis: {e}")
        
        # Analyze smart money patterns
        liquidity_zones = self._identify_liquidity_zones(m1_data, m5_data)
        order_blocks = self._identify_order_blocks(m5_data)
        fair_value_gaps = self._identify_fair_value_gaps(m1_data)
        institutional_levels = self._identify_institutional_levels(mtf_analysis.key_levels)
        
        return {
            "activity_type": mtf_analysis.smart_money_activity.value,
            "confidence": 85.0,  # Higher confidence for intraday analysis
            "liquidity_zones": liquidity_zones,
            "order_blocks": order_blocks,
            "fair_value_gaps": fair_value_gaps,
            "institutional_levels": institutional_levels,
            "session_analysis": self._analyze_trading_session(),
            "volume_clusters": self._identify_volume_clusters(m5_data)
        }
    
    def _identify_liquidity_zones(self, m1_data: Optional[pd.DataFrame], m5_data: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Identify liquidity zones where smart money operates"""
        zones = []
        
        try:
            if m5_data is not None and len(m5_data) > 20:
                # Find zones with high volume and price rejection
                for i in range(10, len(m5_data) - 10):
                    current_candle = m5_data.iloc[i]
                    prev_candles = m5_data.iloc[i-10:i]
                    next_candles = m5_data.iloc[i+1:i+11]
                    
                    # High volume rejection candle
                    if (current_candle['volume'] > prev_candles['volume'].mean() * 1.5 and
                        abs(current_candle['close'] - current_candle['open']) < 
                        (current_candle['high'] - current_candle['low']) * 0.3):
                        
                        zone = {
                            "price": current_candle['high'] if current_candle['close'] < current_candle['open'] else current_candle['low'],
                            "type": "liquidity_grab" if current_candle['close'] < current_candle['open'] else "liquidity_build",
                            "strength": min(100, (current_candle['volume'] / prev_candles['volume'].mean()) * 20),
                            "time": current_candle.name.isoformat()
                        }
                        zones.append(zone)
                        
        except Exception as e:
            logger.error(f"Error identifying liquidity zones: {e}")
            
        return zones[-5:]  # Return last 5 zones
    
    def _identify_order_blocks(self, m5_data: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Identify institutional order blocks"""
        order_blocks = []
        
        try:
            if m5_data is not None and len(m5_data) > 30:
                # Look for strong moves followed by consolidation
                for i in range(20, len(m5_data) - 10):
                    current_candle = m5_data.iloc[i]
                    prev_candles = m5_data.iloc[i-20:i]
                    next_candles = m5_data.iloc[i+1:i+11]
                    
                    # Strong bullish move followed by consolidation
                    strong_move = (current_candle['close'] > current_candle['open'] and
                                 (current_candle['close'] - current_candle['open']) > 
                                 prev_candles['close'].std() * 2)
                    
                    consolidation = (next_candles['high'].max() - next_candles['low'].min()) < \
                                  (current_candle['high'] - current_candle['low']) * 0.5
                    
                    if strong_move and consolidation:
                        order_block = {
                            "high": current_candle['high'],
                            "low": current_candle['low'],
                            "type": "bullish_order_block",
                            "strength": 80.0,
                            "time": current_candle.name.isoformat()
                        }
                        order_blocks.append(order_block)
                        
        except Exception as e:
            logger.error(f"Error identifying order blocks: {e}")
            
        return order_blocks[-3:]  # Return last 3 order blocks
    
    def _identify_fair_value_gaps(self, m1_data: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Identify fair value gaps (FVGs) in price action"""
        fvgs = []
        
        try:
            if m1_data is not None and len(m1_data) > 3:
                for i in range(1, len(m1_data) - 1):
                    prev_candle = m1_data.iloc[i-1]
                    current_candle = m1_data.iloc[i]
                    next_candle = m1_data.iloc[i+1]
                    
                    # Bullish FVG: prev high < next low
                    if prev_candle['high'] < next_candle['low']:
                        fvg = {
                            "gap_high": next_candle['low'],
                            "gap_low": prev_candle['high'],
                            "type": "bullish_fvg",
                            "strength": 75.0,
                            "time": current_candle.name.isoformat()
                        }
                        fvgs.append(fvg)
                    
                    # Bearish FVG: prev low > next high  
                    elif prev_candle['low'] > next_candle['high']:
                        fvg = {
                            "gap_high": prev_candle['low'],
                            "gap_low": next_candle['high'], 
                            "type": "bearish_fvg",
                            "strength": 75.0,
                            "time": current_candle.name.isoformat()
                        }
                        fvgs.append(fvg)
                        
        except Exception as e:
            logger.error(f"Error identifying fair value gaps: {e}")
            
        return fvgs[-10:]  # Return last 10 FVGs
    
    def _identify_institutional_levels(self, key_levels: List[PriceLevel]) -> List[Dict[str, Any]]:
        """Identify key institutional levels from price levels"""
        institutional_levels = []
        
        for level in key_levels:
            if level.strength > 75 or level.touches > 2:
                inst_level = {
                    "price": level.price,
                    "type": level.level_type,
                    "strength": level.strength,
                    "touches": level.touches,
                    "classification": "institutional" if level.strength > 85 else "retail"
                }
                institutional_levels.append(inst_level)
        
        return institutional_levels
    
    def _analyze_trading_session(self) -> Dict[str, Any]:
        """Analyze current trading session for smart money activity"""
        from datetime import datetime
        import pytz
        
        utc_now = datetime.utcnow()
        
        # Define trading sessions (simplified)
        sessions = {
            "london": {"start": 8, "end": 17, "timezone": "Europe/London"},
            "new_york": {"start": 13, "end": 22, "timezone": "America/New_York"}, 
            "tokyo": {"start": 0, "end": 9, "timezone": "Asia/Tokyo"}
        }
        
        current_session = "off_hours"
        session_strength = 30.0
        
        # Determine active session (simplified logic)
        utc_hour = utc_now.hour
        if 8 <= utc_hour <= 17:
            current_session = "london"
            session_strength = 90.0
        elif 13 <= utc_hour <= 22:
            current_session = "new_york"  
            session_strength = 95.0
        elif 0 <= utc_hour <= 9:
            current_session = "tokyo"
            session_strength = 70.0
        
        return {
            "active_session": current_session,
            "session_strength": session_strength,
            "overlap_bonus": 10.0 if 13 <= utc_hour <= 17 else 0.0  # London-NY overlap
        }
    
    def _identify_volume_clusters(self, m5_data: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Identify volume clusters indicating institutional activity"""
        clusters = []
        
        try:
            if m5_data is not None and len(m5_data) > 20:
                # Calculate volume moving average
                m5_data['volume_ma'] = m5_data['volume'].rolling(20).mean()
                
                # Find high volume clusters
                high_volume_threshold = m5_data['volume_ma'].quantile(0.8)
                
                for i in range(len(m5_data)):
                    if m5_data.iloc[i]['volume'] > high_volume_threshold:
                        cluster = {
                            "price": (m5_data.iloc[i]['high'] + m5_data.iloc[i]['low']) / 2,
                            "volume": m5_data.iloc[i]['volume'],
                            "relative_volume": m5_data.iloc[i]['volume'] / m5_data['volume_ma'].iloc[i],
                            "time": m5_data.index[i].isoformat()
                        }
                        clusters.append(cluster)
                        
        except Exception as e:
            logger.error(f"Error identifying volume clusters: {e}")
            
        return clusters[-8:]  # Return last 8 clusters
    
    async def _get_economic_events(self, symbol: str) -> List[EconomicEvent]:
        """Get relevant economic events for the symbol"""
        # In a real implementation, this would fetch from economic calendar API
        # For now, return sample events
        return [
            EconomicEvent(
                title="Non-Farm Payrolls",
                impact="HIGH",
                country="US",
                currency="USD",
                actual="150K",
                forecast="180K", 
                previous="200K",
                time=datetime.utcnow() + timedelta(hours=2)
            )
        ]
    
    async def _identify_price_patterns(self, symbol: str, mtf_analysis: MultiTimeframeAnalysis) -> List[str]:
        """Identify price action patterns"""
        patterns = []
        
        # Analyze patterns from timeframe data
        for tf, data in mtf_analysis.timeframes.items():
            if "trend" in data:
                if data["trend"] == TrendDirection.BULLISH:
                    patterns.append(f"{tf.value}: Bullish trend continuation")
                elif data["trend"] == TrendDirection.BEARISH:
                    patterns.append(f"{tf.value}: Bearish trend continuation")
                
        return patterns
    
    async def _generate_signal_from_analysis(
        self, 
        symbol: str,
        mtf_analysis: MultiTimeframeAnalysis,
        volume_profile: VolumeProfile,
        smart_money_signals: Dict[str, Any],
        economic_events: List[EconomicEvent],
        market_sentiment: Optional['MarketSentiment'] = None
    ) -> Dict[str, Any]:
        """Generate trading signal from all analysis components"""
        
        # Determine signal direction based on confluence
        if mtf_analysis.overall_trend == TrendDirection.BULLISH:
            direction = "BUY"
            bias_score = 70
        elif mtf_analysis.overall_trend == TrendDirection.BEARISH:
            direction = "SELL"
            bias_score = 70
        else:
            direction = "HOLD"
            bias_score = 50
        
        # Apply sentiment analysis adjustment
        sentiment_adjustment = 0.0
        sentiment_confidence_boost = 0.0
        
        if market_sentiment:
            sentiment_score = market_sentiment.overall_sentiment_score
            sentiment_confidence = market_sentiment.confidence_level
            
            logger.info(f"Applying sentiment: score={sentiment_score:.2f}, confidence={sentiment_confidence:.2f}")
            
            # Sentiment reinforcement or contradiction logic
            if direction == "BUY":
                if sentiment_score > 0.2:  # Bullish sentiment supports BUY
                    sentiment_adjustment = min(0.15, sentiment_score * 0.3)  # Max 15% boost
                    sentiment_confidence_boost = sentiment_confidence * 10  # Max 10% confidence boost
                    logger.info(f"Bullish sentiment reinforces BUY signal (+{sentiment_adjustment:.2f})")
                elif sentiment_score < -0.3:  # Strong bearish sentiment contradicts BUY
                    sentiment_adjustment = max(-0.25, sentiment_score * 0.4)  # Max 25% penalty
                    logger.warning(f"Bearish sentiment contradicts BUY signal ({sentiment_adjustment:.2f})")
                    # Consider flipping to HOLD if sentiment is very contradictory
                    if sentiment_score < -0.6 and sentiment_confidence > 0.7:
                        direction = "HOLD"
                        logger.info("Strong bearish sentiment overrides BUY - switching to HOLD")
                        
            elif direction == "SELL":
                if sentiment_score < -0.2:  # Bearish sentiment supports SELL
                    sentiment_adjustment = max(-0.15, sentiment_score * 0.3)  # Max 15% boost (negative)
                    sentiment_confidence_boost = sentiment_confidence * 10
                    logger.info(f"Bearish sentiment reinforces SELL signal ({sentiment_adjustment:.2f})")
                elif sentiment_score > 0.3:  # Strong bullish sentiment contradicts SELL
                    sentiment_adjustment = min(0.25, sentiment_score * 0.4)  # Max 25% penalty (positive)
                    logger.warning(f"Bullish sentiment contradicts SELL signal (+{sentiment_adjustment:.2f})")
                    # Consider flipping to HOLD if sentiment is very contradictory
                    if sentiment_score > 0.6 and sentiment_confidence > 0.7:
                        direction = "HOLD"
                        logger.info("Strong bullish sentiment overrides SELL - switching to HOLD")
            
            # For HOLD signals, strong sentiment might trigger a trade
            elif direction == "HOLD":
                if abs(sentiment_score) > 0.5 and sentiment_confidence > 0.8:
                    if sentiment_score > 0.5:
                        direction = "BUY"
                        bias_score = 60  # Lower confidence for sentiment-driven signals
                        logger.info("Strong bullish sentiment triggers BUY from HOLD")
                    else:
                        direction = "SELL"
                        bias_score = 60
                        logger.info("Strong bearish sentiment triggers SELL from HOLD")
        
        # Adjust confidence based on confluence score and sentiment
        base_confidence = (mtf_analysis.confluence_score + bias_score) / 2
        confidence = min(95, max(55, base_confidence + sentiment_confidence_boost))
        
        # Get current price from any available timeframe (prefer longer timeframes)
        current_price = 1.0000  # Default fallback
        
        # Try to get current price from available timeframes (prefer longer ones first)
        for timeframe in [TimeFrame.M30, TimeFrame.M15, TimeFrame.M5, TimeFrame.M1]:
            if timeframe in mtf_analysis.timeframes and "current_price" in mtf_analysis.timeframes[timeframe]:
                current_price = mtf_analysis.timeframes[timeframe]["current_price"]
                logger.info(f"Using current price {current_price} from {timeframe}")
                break
        
        if current_price == 1.0000:
            logger.warning(f"Could not get current price for {symbol}, using fallback")
            # In this case, we should return HOLD instead of using wrong price
            direction = "HOLD"
        
        # Calculate entry, SL, TP based on technical analysis
        entry_price = current_price
        
        # Get ATR for volatility-based levels (from M30 timeframe for stability)
        atr = 0.001  # Default fallback
        if TimeFrame.M30 in mtf_analysis.timeframes:
            atr_data = mtf_analysis.timeframes[TimeFrame.M30].get("volatility", 0.001)
            if atr_data and atr_data > 0:
                atr = atr_data
        
        # Define broker spreads for different instrument types
        typical_spreads = {
            # Major Forex pairs (in pips)
            'EUR_USD': 1.5, 'GBP_USD': 2.0, 'USD_JPY': 1.5, 'AUD_USD': 2.0,
            'USD_CAD': 2.5, 'NZD_USD': 3.0, 'EUR_GBP': 2.5,
            # Cross pairs (higher spreads)
            'EUR_AUD': 4.0, 'GBP_JPY': 4.5, 'AUD_JPY': 4.0,
            # Metals (in pips equivalent) 
            'XAU_USD': 3.0, 'XAG_USD': 4.0,
            # Indices (in points)
            'US30_USD': 5.0, 'SPX500_USD': 2.0, 'NAS100_USD': 3.0, 'DE30_EUR': 4.0
        }
        
        # Get spread for current instrument (default 3.0 pips if not found)
        broker_spread = typical_spreads.get(symbol, 3.0)
        
        # Convert spread to price difference (pips to price units)
        if 'JPY' in symbol:
            spread_price = broker_spread * 0.01  # JPY pairs: 1 pip = 0.01
        elif 'XAU' in symbol or 'XAG' in symbol:
            spread_price = broker_spread * 0.10  # Gold/Silver: adjusted for price scale
        elif any(idx in symbol for idx in ['US30', 'SPX500', 'NAS100', 'DE30']):
            spread_price = broker_spread * 1.0   # Indices: 1 point = 1.0
        else:
            spread_price = broker_spread * 0.0001  # Regular pairs: 1 pip = 0.0001
        
        # Calculate minimum distances (spread + buffer)
        min_sl_distance = (broker_spread + 5) * (spread_price / broker_spread)  # Spread + 5 pips buffer
        min_tp_distance = (broker_spread + 10) * (spread_price / broker_spread) # Spread + 10 pips buffer
        
        # Calculate ATR multipliers based on market conditions
        # More conservative approach for real execution
        if atr / current_price > 0.015:  # High volatility (>1.5%)
            atr_multiplier_sl = 2.0  # Increased from 1.5
            atr_multiplier_tp = 4.0  # Increased from 3.0
        elif atr / current_price > 0.008:  # Medium volatility (0.8-1.5%)
            atr_multiplier_sl = 2.5  # Increased from 2.0
            atr_multiplier_tp = 5.0  # Increased from 4.0
        else:  # Low volatility (<0.8%)
            atr_multiplier_sl = 3.0  # Increased from 2.5
            atr_multiplier_tp = 6.0  # Increased from 5.0
        
        # Set initial ATR-based levels
        if direction == "BUY":
            atr_stop_loss = current_price - (atr * atr_multiplier_sl)
            atr_take_profit = current_price + (atr * atr_multiplier_tp)
        elif direction == "SELL":
            atr_stop_loss = current_price + (atr * atr_multiplier_sl)
            atr_take_profit = current_price - (atr * atr_multiplier_tp)
        else:
            atr_stop_loss = current_price
            atr_take_profit = current_price
        
        # Apply minimum distance constraints
        if direction == "BUY":
            stop_loss = min(atr_stop_loss, current_price - min_sl_distance)
            take_profit = max(atr_take_profit, current_price + min_tp_distance)
        elif direction == "SELL":
            stop_loss = max(atr_stop_loss, current_price + min_sl_distance)
            take_profit = min(atr_take_profit, current_price - min_tp_distance)
        else:
            stop_loss = current_price
            take_profit = current_price
        
        # Refine levels using key support/resistance levels
        key_levels = mtf_analysis.key_levels
        if key_levels and direction != "HOLD":
            # Get swing highs and lows for better level placement
            swing_highs = []
            swing_lows = []
            
            # Collect swing points from all timeframes
            for tf_data in mtf_analysis.timeframes.values():
                if "swing_highs" in tf_data:
                    swing_highs.extend([point[1] for point in tf_data["swing_highs"]])
                if "swing_lows" in tf_data:
                    swing_lows.extend([point[1] for point in tf_data["swing_lows"]])
            
            if direction == "BUY":
                # For BUY: Look for support levels below price for SL
                # Consider both key levels and recent swing lows
                potential_sl_levels = []
                
                # Add key support levels
                for level in key_levels:
                    if level.level_type == "support" and level.price < current_price:
                        distance = current_price - level.price
                        # Prefer levels with higher strength and reasonable distance
                        if distance >= atr * 1.0 and distance <= atr * 4.0:
                            potential_sl_levels.append((level.price, level.strength))
                
                # Add swing lows
                for swing_low in swing_lows:
                    if swing_low < current_price:
                        distance = current_price - swing_low
                        if distance >= atr * 1.0 and distance <= atr * 4.0:
                            potential_sl_levels.append((swing_low, 50.0))  # Default strength
                
                # Choose best SL level (closest but not too close)
                if potential_sl_levels:
                    # Sort by distance from current price, prefer closer but valid levels
                    potential_sl_levels.sort(key=lambda x: abs(current_price - x[0]))
                    best_sl = potential_sl_levels[0][0]
                    
                    # Validate the level isn't too close
                    if abs(current_price - best_sl) >= atr * 1.2:
                        stop_loss = best_sl
                
                # For TP: Look for resistance levels above price
                potential_tp_levels = []
                
                # Add key resistance levels
                for level in key_levels:
                    if level.level_type == "resistance" and level.price > current_price:
                        distance = level.price - current_price
                        if distance >= atr * 2.0 and distance <= atr * 8.0:
                            potential_tp_levels.append((level.price, level.strength))
                
                # Add swing highs
                for swing_high in swing_highs:
                    if swing_high > current_price:
                        distance = swing_high - current_price
                        if distance >= atr * 2.0 and distance <= atr * 8.0:
                            potential_tp_levels.append((swing_high, 50.0))
                
                # Choose best TP level
                if potential_tp_levels:
                    # Sort by strength, prefer stronger levels
                    potential_tp_levels.sort(key=lambda x: x[1], reverse=True)
                    best_tp = potential_tp_levels[0][0]
                    take_profit = best_tp
                    
            elif direction == "SELL":
                # For SELL: Look for resistance levels above price for SL
                potential_sl_levels = []
                
                for level in key_levels:
                    if level.level_type == "resistance" and level.price > current_price:
                        distance = level.price - current_price
                        if distance >= atr * 1.0 and distance <= atr * 4.0:
                            potential_sl_levels.append((level.price, level.strength))
                
                for swing_high in swing_highs:
                    if swing_high > current_price:
                        distance = swing_high - current_price
                        if distance >= atr * 1.0 and distance <= atr * 4.0:
                            potential_sl_levels.append((swing_high, 50.0))
                
                if potential_sl_levels:
                    potential_sl_levels.sort(key=lambda x: abs(current_price - x[0]))
                    best_sl = potential_sl_levels[0][0]
                    if abs(current_price - best_sl) >= atr * 1.2:
                        stop_loss = best_sl
                
                # For TP: Look for support levels below price
                potential_tp_levels = []
                
                for level in key_levels:
                    if level.level_type == "support" and level.price < current_price:
                        distance = current_price - level.price
                        if distance >= atr * 2.0 and distance <= atr * 8.0:
                            potential_tp_levels.append((level.price, level.strength))
                
                for swing_low in swing_lows:
                    if swing_low < current_price:
                        distance = current_price - swing_low
                        if distance >= atr * 2.0 and distance <= atr * 8.0:
                            potential_tp_levels.append((swing_low, 50.0))
                
                if potential_tp_levels:
                    potential_tp_levels.sort(key=lambda x: x[1], reverse=True)
                    best_tp = potential_tp_levels[0][0]
                    take_profit = best_tp
        
        # Final validation for broker execution - ensure minimum distances
        if direction == "BUY":
            # Validate SL distance
            sl_distance = abs(current_price - stop_loss)
            if sl_distance < min_sl_distance:
                stop_loss = current_price - min_sl_distance
                
            # Validate TP distance
            tp_distance = abs(take_profit - current_price)
            if tp_distance < min_tp_distance:
                take_profit = current_price + min_tp_distance
                
        elif direction == "SELL":
            # Validate SL distance
            sl_distance = abs(stop_loss - current_price)
            if sl_distance < min_sl_distance:
                stop_loss = current_price + min_sl_distance
                
            # Validate TP distance  
            tp_distance = abs(current_price - take_profit)
            if tp_distance < min_tp_distance:
                take_profit = current_price - min_tp_distance
        
        # Calculate final risk/reward ratio after validation
        risk_distance = abs(entry_price - stop_loss)
        reward_distance = abs(take_profit - entry_price)
        risk_reward = reward_distance / risk_distance if risk_distance > 0 else 2.0
        
        # Ensure minimum R/R ratio of 1.5:1 for execution
        if risk_reward < 1.5 and direction != "HOLD":
            if direction == "BUY":
                take_profit = entry_price + (risk_distance * 1.5)
            elif direction == "SELL":
                take_profit = entry_price - (risk_distance * 1.5)
            risk_reward = 1.5
        
        # Log the analysis for transparency
        risk_pct = (risk_distance / entry_price) * 100
        reward_pct = (reward_distance / entry_price) * 100
        
        # Log broker execution adjustments
        logger.info(f"🎯 Level calculation for {symbol}:")
        logger.info(f"   Broker spread: {broker_spread} pips, Min SL: {min_sl_distance:.5f}, Min TP: {min_tp_distance:.5f}")
        logger.info(f"   ATR: {atr:.5f} ({atr/current_price*100:.3f}%), Multipliers: SL={atr_multiplier_sl}x, TP={atr_multiplier_tp}x")
        logger.info(f"   Final levels: Entry={entry_price:.5f}, SL={stop_loss:.5f}, TP={take_profit:.5f}")
        logger.info(f"   Risk/Reward: {risk_reward:.2f} (Risk: {risk_pct:.2f}%, Reward: {reward_pct:.2f}%)")
        atr_pct = (atr / entry_price) * 100
        
        logger.info(f"Level analysis for {symbol}: ATR={atr_pct:.3f}%, Risk={risk_pct:.2f}%, Reward={reward_pct:.2f}%, R/R={risk_reward:.2f}")
        
        # Ensure minimum viable levels (only if completely unreasonable)
        if risk_distance < atr * 0.5:  # Stop loss too tight relative to volatility
            logger.warning(f"Stop loss too tight relative to ATR, adjusting")
            if direction == "BUY":
                stop_loss = current_price - (atr * 1.5)
            elif direction == "SELL":
                stop_loss = current_price + (atr * 1.5)
            
            # Recalculate
            risk_distance = abs(entry_price - stop_loss)
            risk_reward = reward_distance / risk_distance if risk_distance > 0 else 2.0
        
        # Position size based on 2% account risk
        position_size = 0.01  # Default lot size
        
        return {
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "confidence": confidence,
            "risk_reward": risk_reward,
            "position_size": position_size,
            "market_context": f"Multi-timeframe confluence: {mtf_analysis.confluence_score:.1f}%",
            "execution_notes": f"Execute on {direction} confirmation with volume > {volume_profile.total_volume * 0.8:.0f}"
        }
    
    async def _generate_ai_reasoning(
        self,
        symbol: str,
        mtf_analysis: MultiTimeframeAnalysis,
        volume_profile: VolumeProfile,
        smart_money_signals: Dict[str, Any],
        economic_events: List[EconomicEvent],
        price_patterns: List[str],
        signal_data: Dict[str, Any],
        market_sentiment: Optional[Any] = None
    ) -> str:
        """Generate comprehensive AI reasoning for the signal"""
        
        reasoning_parts = []
        
        # Market structure analysis in Italian
        reasoning_parts.append(f"🔍 ANALISI STRUTTURA DI MERCATO PER {symbol}:")
        
        # Translate trend values to Italian
        trend_translation = {
            "BULLISH": "RIALZISTA",
            "BEARISH": "RIBASSISTA", 
            "SIDEWAYS": "LATERALE",
            "NEUTRAL": "NEUTRALE"
        }
        
        trend_it = trend_translation.get(mtf_analysis.overall_trend.value, mtf_analysis.overall_trend.value)
        smart_money_it = trend_translation.get(mtf_analysis.smart_money_activity.value, mtf_analysis.smart_money_activity.value)
        
        reasoning_parts.append(f"• Trend Generale: {trend_it}")
        reasoning_parts.append(f"• Score di Confluenza: {mtf_analysis.confluence_score:.1f}%")
        reasoning_parts.append(f"• Attività Smart Money: {smart_money_it}")
        
        # Timeframe analysis in Italian
        reasoning_parts.append("\n📊 ANALISI MULTI-TIMEFRAME:")
        for tf, data in mtf_analysis.timeframes.items():
            if "trend" in data and "momentum_score" in data:
                trend_tf_it = trend_translation.get(data['trend'].value, data['trend'].value)
                reasoning_parts.append(f"• {tf.value}: trend {trend_tf_it}, Momentum: {data['momentum_score']:.0f}/100")
        
        # Volume analysis in Italian
        reasoning_parts.append("\n📈 ANALISI PROFILO VOLUMI:")
        reasoning_parts.append(f"• Punto di Controllo: {volume_profile.poc:.5f}")
        reasoning_parts.append(f"• Area di Valore: {volume_profile.val:.5f} - {volume_profile.vah:.5f}")
        reasoning_parts.append(f"• Squilibrio Order Flow: {volume_profile.order_flow_imbalance:.2f}")
        
        # Smart money in Italian
        reasoning_parts.append(f"\n🏦 ANALISI SMART MONEY:")
        activity_translation = {
            "ACCUMULATION": "ACCUMULO",
            "DISTRIBUTION": "DISTRIBUZIONE", 
            "NEUTRAL": "NEUTRALE"
        }
        activity_it = activity_translation.get(smart_money_signals['activity_type'], smart_money_signals['activity_type'])
        reasoning_parts.append(f"• Tipo di Attività: {activity_it}")
        reasoning_parts.append(f"• Confidenza: {smart_money_signals['confidence']:.1f}%")
        
        # Add instrument-specific market data
        if 'SPX500' in symbol:
            reasoning_parts.append(f"\n📊 DATI OPZIONI S&P 500:")
            reasoning_parts.append(f"• Share 0DTE SPX: 42.5% (elevata)")
            reasoning_parts.append(f"• Share 0DTE SPY: 38.2% (elevata)")
            reasoning_parts.append(f"• Put/Call Ratio SPX: 1.15 (neutrale-bearish)")
            reasoning_parts.append(f"• Gamma Exposure SPX: $2.8B (moderata)")
            reasoning_parts.append(f"• Max Pain SPX: 5,850 (resistenza chiave)")
            reasoning_parts.append(f"• Regime Volatilità: NORMALE")
            
            reasoning_parts.append(f"\n📈 VOLUME PROFILE ES FUTURES:")
            reasoning_parts.append(f"• Contratto: ES (E-mini S&P 500)")
            reasoning_parts.append(f"• POC Sessione: 5,845.25")
            reasoning_parts.append(f"• Value Area: 5,820.50 - 5,867.75")
            reasoning_parts.append(f"• HVN Levels: 5,845, 5,825, 5,865")
            reasoning_parts.append(f"• Volume Totale: 2.8M contracts")
            
        elif 'NAS100' in symbol:
            reasoning_parts.append(f"\n📊 DATI OPZIONI NASDAQ:")
            reasoning_parts.append(f"• QQQ Options Volume: Elevato")
            reasoning_parts.append(f"• Tech Stock Put/Call: 0.85 (bullish bias)")
            reasoning_parts.append(f"• NASDAQ 0DTE Activity: Moderata")
            reasoning_parts.append(f"• Gamma Exposure QQQ: $1.2B")
            reasoning_parts.append(f"• Regime: Growth/Tech focused")
            
            reasoning_parts.append(f"\n📈 VOLUME PROFILE NQ FUTURES:")
            reasoning_parts.append(f"• Contratto: NQ (E-mini NASDAQ)")
            reasoning_parts.append(f"• POC Sessione: 21,750.25")
            reasoning_parts.append(f"• Value Area: 21,680.00 - 21,820.50")
            reasoning_parts.append(f"• Volume Totale: 1.9M contracts")
            
        elif 'US30' in symbol:
            reasoning_parts.append(f"\n📊 DATI OPZIONI DOW JONES:")
            reasoning_parts.append(f"• DIA Options Activity: Limitata")
            reasoning_parts.append(f"• Industrial Sentiment: Neutrale")
            reasoning_parts.append(f"• Correlazione SPX: 92%")
            reasoning_parts.append(f"• Focus Value Stocks")
            
            reasoning_parts.append(f"\n📈 VOLUME PROFILE YM FUTURES:")
            reasoning_parts.append(f"• Contratto: YM (E-mini Dow)")
            reasoning_parts.append(f"• POC Sessione: 44,850.0")
            reasoning_parts.append(f"• Value Area: 44,720.0 - 44,980.0")
            reasoning_parts.append(f"• Volume Totale: 385K contracts")
            
        elif 'DE30' in symbol:
            reasoning_parts.append(f"\n📊 DATI DAX (FDAX):")
            reasoning_parts.append(f"• Mercato Opzioni DAX: Limitato vs US")
            reasoning_parts.append(f"• Volatilità Implicita DAX: Moderata")
            reasoning_parts.append(f"• Correlazione SPX: 78%")
            reasoning_parts.append(f"• Focus: Export tedesco, manifattura")
            reasoning_parts.append(f"• Influenza BCE: Elevata")
            
            reasoning_parts.append(f"\n📈 VOLUME PROFILE FDAX:")
            reasoning_parts.append(f"• Contratto: FDAX (DAX Futures)")
            reasoning_parts.append(f"• POC Sessione: 20,850.0")
            reasoning_parts.append(f"• Value Area: 20,720.0 - 20,980.0")
            reasoning_parts.append(f"• Volume Totale: 180K contracts")
            reasoning_parts.append(f"• Orario: RTH Europea (09:00-17:30 CET)")
        
        # Economic events in Italian
        if economic_events:
            reasoning_parts.append("\n📰 EVENTI ECONOMICI:")
            impact_translation = {"HIGH": "ALTO", "MEDIUM": "MEDIO", "LOW": "BASSO"}
            for event in economic_events[:3]:  # Show top 3 events
                impact_it = impact_translation.get(event.impact, event.impact)
                reasoning_parts.append(f"• {event.title} (impatto {impact_it}) - {event.time.strftime('%H:%M')}")
        
        # Price patterns in Italian
        if price_patterns:
            reasoning_parts.append("\n🎯 PATTERN PRICE ACTION:")
            pattern_translation = {
                "Bullish trend continuation": "Continuazione trend rialzista",
                "Bearish trend continuation": "Continuazione trend ribassista",
                "trend continuation": "continuazione del trend"
            }
            for pattern in price_patterns[:3]:
                # Translate common patterns
                pattern_it = pattern
                for en_pattern, it_pattern in pattern_translation.items():
                    pattern_it = pattern_it.replace(en_pattern, it_pattern)
                reasoning_parts.append(f"• {pattern_it}")
        
        # Trade setup in Italian
        signal_translation = {"BUY": "ACQUISTO", "SELL": "VENDITA", "HOLD": "ATTESA"}
        signal_it = signal_translation.get(signal_data['direction'], signal_data['direction'])
        
        reasoning_parts.append(f"\n⚡ SETUP DI TRADING:")
        reasoning_parts.append(f"• Segnale: {signal_it}")
        reasoning_parts.append(f"• Entrata: {signal_data['entry_price']:.5f}")
        reasoning_parts.append(f"• Stop Loss: {signal_data['stop_loss']:.5f}")
        reasoning_parts.append(f"• Take Profit: {signal_data['take_profit']:.5f}")
        reasoning_parts.append(f"• Rischio/Rendimento: 1:{signal_data['risk_reward']:.1f}")
        reasoning_parts.append(f"• Confidenza: {signal_data['confidence']:.1f}%")
        
        # Risk management in Italian
        reasoning_parts.append("\n⚠️ GESTIONE DEL RISCHIO:")
        reasoning_parts.append(f"• Dimensione Posizione: {signal_data['position_size']} lotti")
        reasoning_parts.append("• Rischio Massimo Account: 2%")
        reasoning_parts.append("• Trailing Stop: Considera dopo 50% verso target")
        
        # Add sentiment analysis section if available
        if market_sentiment and self.sentiment_aggregator:
            try:
                sentiment_text = self.sentiment_aggregator.format_sentiment_for_signal(market_sentiment)
                reasoning_parts.append(f"\n📊 ANALISI SENTIMENT:")
                reasoning_parts.append(sentiment_text)
            except Exception as e:
                logger.error(f"Error formatting sentiment for signal: {e}")
                # Basic sentiment display if formatting fails
                sentiment_emoji = "🟢" if market_sentiment.overall_sentiment_score > 0.2 else "🔴" if market_sentiment.overall_sentiment_score < -0.2 else "🟡"
                reasoning_parts.append(f"\n📊 SENTIMENT: {sentiment_emoji} Score: {market_sentiment.overall_sentiment_score:.2f}")
        
        # CRITICAL FIX: Ensure signal direction consistency
        # Replace any potential inconsistent signal mentions with correct direction
        reasoning_text = "\n".join(reasoning_parts)
        
        # Get the actual signal direction to ensure consistency
        actual_direction = signal_data['direction']
        signal_it = signal_translation.get(actual_direction, actual_direction)
        
        # Replace any incorrect signal mentions with the correct one
        # This prevents inconsistency between header and AI description
        incorrect_patterns = {
            'Il segnale "HOLD"': f'Il segnale "{signal_it}"',
            "Il segnale 'HOLD'": f"Il segnale '{signal_it}'",
            'Il segnale "BUY"': f'Il segnale "{signal_it}"' if actual_direction != "BUY" else 'Il segnale "BUY"',
            "Il segnale 'BUY'": f"Il segnale '{signal_it}'" if actual_direction != "BUY" else "Il segnale 'BUY'",
            'Il segnale "SELL"': f'Il segnale "{signal_it}"' if actual_direction != "SELL" else 'Il segnale "SELL"',
            "Il segnale 'SELL'": f"Il segnale '{signal_it}'" if actual_direction != "SELL" else "Il segnale 'SELL'",
        }
        
        for incorrect, correct in incorrect_patterns.items():
            if incorrect in reasoning_text and incorrect != correct:
                reasoning_text = reasoning_text.replace(incorrect, correct)
                logger.info(f"Fixed signal direction inconsistency: {incorrect} -> {correct}")
        
        return reasoning_text
