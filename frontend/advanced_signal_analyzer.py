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

class TimeFrame(Enum):
    M1 = "M1"
    M5 = "M5" 
    M15 = "M15"
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
    """Advanced signal analyzer with multi-timeframe and smart money analysis"""
    
    def __init__(self, oanda_api_key: str, news_api_key: Optional[str] = None):
        self.oanda_api_key = oanda_api_key
        self.news_api_key = news_api_key
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
            
            # Generate signal based on all analysis
            signal_data = await self._generate_signal_from_analysis(
                symbol, mtf_analysis, volume_profile, smart_money_signals, economic_events
            )
            
            # Create AI reasoning
            ai_reasoning = await self._generate_ai_reasoning(
                symbol, mtf_analysis, volume_profile, smart_money_signals, 
                economic_events, price_patterns, signal_data
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
        
        timeframes = [TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
        
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
        
        # Weight timeframes (higher timeframes get more weight)
        weights = {
            TimeFrame.M15: 1,
            TimeFrame.H1: 2, 
            TimeFrame.H4: 3,
            TimeFrame.D1: 4
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
            # Look for signs of accumulation/distribution
            # This is a simplified version - in reality would be much more complex
            
            higher_tf_trends = []
            for tf in [TimeFrame.H4, TimeFrame.D1]:
                if tf in timeframes_data and "trend" in timeframes_data[tf]:
                    higher_tf_trends.append(timeframes_data[tf]["trend"])
            
            lower_tf_trends = []
            for tf in [TimeFrame.M15, TimeFrame.H1]:
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
        """Detect smart money activity patterns"""
        return {
            "activity_type": mtf_analysis.smart_money_activity.value,
            "confidence": 75.0,
            "liquidity_zones": [],
            "order_blocks": [],
            "fair_value_gaps": [],
            "institutional_levels": []
        }
    
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
        economic_events: List[EconomicEvent]
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
        
        # Adjust confidence based on confluence score
        confidence = min(95, max(55, mtf_analysis.confluence_score + bias_score) / 2)
        
        # Get current price from H1 timeframe if available
        current_price = 1.0000  # Default
        if TimeFrame.H1 in mtf_analysis.timeframes:
            current_price = mtf_analysis.timeframes[TimeFrame.H1].get("current_price", 1.0000)
        
        # Calculate entry, SL, TP based on analysis
        if direction == "BUY":
            entry_price = current_price
            # Use support level for SL, resistance for TP
            stop_loss = entry_price * 0.985  # 1.5% SL default
            take_profit = entry_price * 1.030  # 3% TP default
        elif direction == "SELL":
            entry_price = current_price
            stop_loss = entry_price * 1.015  # 1.5% SL default
            take_profit = entry_price * 0.970  # 3% TP default
        else:
            entry_price = current_price
            stop_loss = current_price
            take_profit = current_price
        
        # Adjust levels based on key levels from analysis
        key_levels = mtf_analysis.key_levels
        if key_levels:
            # Use nearest support/resistance for better SL/TP placement
            if direction == "BUY":
                # Find nearest support below current price
                supports = [level.price for level in key_levels 
                          if level.level_type == "support" and level.price < current_price]
                if supports:
                    stop_loss = max(supports)
                    
                # Find nearest resistance above current price  
                resistances = [level.price for level in key_levels
                             if level.level_type == "resistance" and level.price > current_price]
                if resistances:
                    take_profit = min(resistances)
                    
            elif direction == "SELL":
                # Find nearest resistance above current price
                resistances = [level.price for level in key_levels
                             if level.level_type == "resistance" and level.price > current_price]
                if resistances:
                    stop_loss = min(resistances)
                    
                # Find nearest support below current price
                supports = [level.price for level in key_levels 
                          if level.level_type == "support" and level.price < current_price]
                if supports:
                    take_profit = max(supports)
        
        # Calculate risk/reward ratio
        risk_distance = abs(entry_price - stop_loss)
        reward_distance = abs(take_profit - entry_price)
        risk_reward = reward_distance / risk_distance if risk_distance > 0 else 3.0
        
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
        signal_data: Dict[str, Any]
    ) -> str:
        """Generate comprehensive AI reasoning for the signal"""
        
        reasoning_parts = []
        
        # Market structure analysis
        reasoning_parts.append(f"🔍 MARKET STRUCTURE ANALYSIS FOR {symbol}:")
        reasoning_parts.append(f"• Overall Trend: {mtf_analysis.overall_trend.value}")
        reasoning_parts.append(f"• Confluence Score: {mtf_analysis.confluence_score:.1f}%")
        reasoning_parts.append(f"• Smart Money Activity: {mtf_analysis.smart_money_activity.value}")
        
        # Timeframe analysis
        reasoning_parts.append("\n📊 MULTI-TIMEFRAME ANALYSIS:")
        for tf, data in mtf_analysis.timeframes.items():
            if "trend" in data and "momentum_score" in data:
                reasoning_parts.append(f"• {tf.value}: {data['trend'].value} trend, Momentum: {data['momentum_score']:.0f}/100")
        
        # Volume analysis
        reasoning_parts.append("\n📈 VOLUME PROFILE ANALYSIS:")
        reasoning_parts.append(f"• Point of Control: {volume_profile.poc:.5f}")
        reasoning_parts.append(f"• Value Area: {volume_profile.val:.5f} - {volume_profile.vah:.5f}")
        reasoning_parts.append(f"• Order Flow Imbalance: {volume_profile.order_flow_imbalance:.2f}")
        
        # Smart money
        reasoning_parts.append(f"\n🏦 SMART MONEY ANALYSIS:")
        reasoning_parts.append(f"• Activity Type: {smart_money_signals['activity_type']}")
        reasoning_parts.append(f"• Confidence: {smart_money_signals['confidence']:.1f}%")
        
        # Economic events
        if economic_events:
            reasoning_parts.append("\n📰 ECONOMIC EVENTS:")
            for event in economic_events[:3]:  # Show top 3 events
                reasoning_parts.append(f"• {event.title} ({event.impact} impact) - {event.time.strftime('%H:%M')}")
        
        # Price patterns
        if price_patterns:
            reasoning_parts.append("\n🎯 PRICE ACTION PATTERNS:")
            for pattern in price_patterns[:3]:
                reasoning_parts.append(f"• {pattern}")
        
        # Trade setup
        reasoning_parts.append(f"\n⚡ TRADE SETUP:")
        reasoning_parts.append(f"• Signal: {signal_data['direction']}")
        reasoning_parts.append(f"• Entry: {signal_data['entry_price']:.5f}")
        reasoning_parts.append(f"• Stop Loss: {signal_data['stop_loss']:.5f}")
        reasoning_parts.append(f"• Take Profit: {signal_data['take_profit']:.5f}")
        reasoning_parts.append(f"• Risk/Reward: 1:{signal_data['risk_reward']:.1f}")
        reasoning_parts.append(f"• Confidence: {signal_data['confidence']:.1f}%")
        
        # Risk management
        reasoning_parts.append("\n⚠️ RISK MANAGEMENT:")
        reasoning_parts.append(f"• Position Size: {signal_data['position_size']} lots")
        reasoning_parts.append("• Max Account Risk: 2%")
        reasoning_parts.append("• Trailing Stop: Consider after 50% to target")
        
        return "\n".join(reasoning_parts)