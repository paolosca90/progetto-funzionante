"""
OANDA Signal Engine
Advanced signal generation using OANDA market data and AI analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from decimal import Decimal
import json
import os
import google.generativeai as genai
from oanda_api_integration import create_oanda_client, MarketData, CandleData, OANDAAPIError

# Setup logging
logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class TechnicalIndicators:
    """Technical analysis indicators"""
    rsi: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_lower: float
    bb_middle: float
    atr: float
    ema_9: float
    ema_21: float
    ema_50: float
    sma_200: float
    volume_avg: float
    volatility: float

@dataclass
class TradingSignal:
    """Complete trading signal with analysis"""
    instrument: str
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence_score: float
    risk_level: RiskLevel
    risk_reward_ratio: float
    position_size: float
    
    # Technical analysis
    technical_score: float
    indicators: TechnicalIndicators
    
    # Market context
    market_session: str
    spread: float
    volatility: float
    
    # AI analysis
    ai_analysis: str
    reasoning: str
    
    # Metadata
    timeframe: str
    timestamp: datetime
    expires_at: datetime

class OANDASignalEngine:
    """
    Advanced signal generation engine using OANDA data
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.oanda_client = None
        self._is_initialized = False
        
        # Technical analysis parameters
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2
        self.atr_period = 14
        
        # Risk management
        self.max_risk_per_trade = 0.02  # 2% risk per trade
        self.default_risk_reward = 2.5  # 1:2.5 risk/reward ratio
        
        # AI configuration
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini AI configured")
        else:
            self.gemini_model = None
            logger.warning("⚠️ Gemini AI not available - using technical analysis only")
    
    async def initialize(self):
        """Initialize the signal engine"""
        try:
            self.oanda_client = await create_oanda_client()
            self._is_initialized = True
            logger.info("🚀 OANDA Signal Engine initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize signal engine: {e}")
            raise
    
    async def __aenter__(self):
        if not self._is_initialized:
            await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.oanda_client:
            await self.oanda_client.disconnect()
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
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
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        prices_array = np.array(prices)
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices_array, fast)
        ema_slow = self._calculate_ema(prices_array, slow)
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line (EMA of MACD line)
        macd_values = []
        for i in range(slow - 1, len(prices)):
            macd_values.append(ema_fast - ema_slow)
        
        if len(macd_values) >= signal_period:
            signal_line = self._calculate_ema(np.array(macd_values), signal_period)
            histogram = macd_line - signal_line
        else:
            signal_line = macd_line
            histogram = 0.0
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current_price = prices[-1]
            return current_price * 1.01, current_price, current_price * 0.99
        
        prices_array = np.array(prices[-period:])
        middle = np.mean(prices_array)
        std = np.std(prices_array)
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def calculate_atr(self, candles: List[CandleData], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(candles) < period:
            return 0.01  # Default ATR
        
        true_ranges = []
        for i in range(1, len(candles)):
            current = candles[i]
            previous = candles[i-1]
            
            tr1 = current.high - current.low
            tr2 = abs(current.high - previous.close)
            tr3 = abs(current.low - previous.close)
            
            true_ranges.append(max(tr1, tr2, tr3))
        
        return np.mean(true_ranges[-period:])
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) == 0:
            return 0.0
        
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return np.mean(prices)
        return np.mean(prices[-period:])
    
    async def get_technical_indicators(self, instrument: str, timeframe: str = "H1") -> TechnicalIndicators:
        """Calculate comprehensive technical indicators"""
        try:
            # Get historical data
            candles = await self.oanda_client.get_candles(
                instrument=instrument,
                granularity=timeframe,
                count=200  # Enough for all indicators
            )
            
            if len(candles) < 50:
                logger.warning(f"Insufficient data for {instrument}: {len(candles)} candles")
                # Return neutral indicators
                return self._get_neutral_indicators()
            
            # Extract prices and volumes
            closes = [c.close for c in candles]
            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            volumes = [c.volume for c in candles]
            
            # Calculate indicators
            rsi = self.calculate_rsi(closes, self.rsi_period)
            macd_line, macd_signal, macd_hist = self.calculate_macd(closes)
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(closes)
            atr = self.calculate_atr(candles, self.atr_period)
            
            # Moving averages
            ema_9 = self._calculate_ema(np.array(closes), 9)
            ema_21 = self._calculate_ema(np.array(closes), 21)
            ema_50 = self._calculate_ema(np.array(closes), 50)
            sma_200 = self._calculate_sma(closes, 200)
            
            # Volume and volatility
            volume_avg = np.mean(volumes[-20:]) if volumes else 1000
            volatility = atr / closes[-1] if closes[-1] > 0 else 0.01
            
            return TechnicalIndicators(
                rsi=rsi,
                macd_signal=macd_signal,
                macd_histogram=macd_hist,
                bb_upper=bb_upper,
                bb_lower=bb_lower,
                bb_middle=bb_middle,
                atr=atr,
                ema_9=ema_9,
                ema_21=ema_21,
                ema_50=ema_50,
                sma_200=sma_200,
                volume_avg=volume_avg,
                volatility=volatility
            )
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {instrument}: {e}")
            return self._get_neutral_indicators()
    
    def _get_neutral_indicators(self) -> TechnicalIndicators:
        """Return neutral technical indicators"""
        return TechnicalIndicators(
            rsi=50.0,
            macd_signal=0.0,
            macd_histogram=0.0,
            bb_upper=1.01,
            bb_lower=0.99,
            bb_middle=1.00,
            atr=0.01,
            ema_9=1.00,
            ema_21=1.00,
            ema_50=1.00,
            sma_200=1.00,
            volume_avg=1000.0,
            volatility=0.01
        )
    
    def analyze_technical_signals(self, indicators: TechnicalIndicators, current_price: float) -> Tuple[SignalType, float, str]:
        """Analyze technical indicators and generate signal"""
        signals = []
        score = 0.0
        reasoning = []
        
        # RSI Analysis
        if indicators.rsi < 30:
            signals.append("BUY")
            score += 0.8
            reasoning.append(f"RSI oversold ({indicators.rsi:.1f})")
        elif indicators.rsi > 70:
            signals.append("SELL")
            score += 0.8
            reasoning.append(f"RSI overbought ({indicators.rsi:.1f})")
        elif 40 <= indicators.rsi <= 60:
            score += 0.2
            reasoning.append("RSI neutral")
        
        # MACD Analysis
        if indicators.macd_histogram > 0:
            signals.append("BUY")
            score += 0.6
            reasoning.append("MACD bullish crossover")
        elif indicators.macd_histogram < 0:
            signals.append("SELL")
            score += 0.6
            reasoning.append("MACD bearish crossover")
        
        # Bollinger Bands Analysis
        bb_position = (current_price - indicators.bb_lower) / (indicators.bb_upper - indicators.bb_lower)
        if bb_position < 0.2:
            signals.append("BUY")
            score += 0.5
            reasoning.append("Price near lower Bollinger Band")
        elif bb_position > 0.8:
            signals.append("SELL")
            score += 0.5
            reasoning.append("Price near upper Bollinger Band")
        
        # EMA Trend Analysis
        if current_price > indicators.ema_9 > indicators.ema_21 > indicators.ema_50:
            signals.append("BUY")
            score += 0.7
            reasoning.append("Strong uptrend (EMAs aligned)")
        elif current_price < indicators.ema_9 < indicators.ema_21 < indicators.ema_50:
            signals.append("SELL")
            score += 0.7
            reasoning.append("Strong downtrend (EMAs aligned)")
        
        # Determine final signal
        buy_signals = signals.count("BUY")
        sell_signals = signals.count("SELL")
        
        if buy_signals > sell_signals:
            final_signal = SignalType.BUY
        elif sell_signals > buy_signals:
            final_signal = SignalType.SELL
        else:
            final_signal = SignalType.HOLD
        
        # Normalize score
        max_possible_score = 2.6  # Sum of all possible scores
        normalized_score = min(score / max_possible_score, 1.0)
        
        return final_signal, normalized_score, " | ".join(reasoning)
    
    def calculate_risk_levels(self, indicators: TechnicalIndicators, signal_type: SignalType, current_price: float) -> Tuple[float, float, RiskLevel]:
        """Calculate stop loss, take profit, and risk level"""
        atr = indicators.atr
        
        # Risk level based on volatility and market conditions
        volatility_threshold_low = 0.005  # 0.5%
        volatility_threshold_high = 0.02   # 2%
        
        if indicators.volatility < volatility_threshold_low:
            risk_level = RiskLevel.LOW
            atr_multiplier = 1.5
        elif indicators.volatility > volatility_threshold_high:
            risk_level = RiskLevel.HIGH
            atr_multiplier = 3.0
        else:
            risk_level = RiskLevel.MEDIUM
            atr_multiplier = 2.0
        
        # Calculate stop loss and take profit
        if signal_type == SignalType.BUY:
            stop_loss = current_price - (atr * atr_multiplier)
            take_profit = current_price + (atr * atr_multiplier * self.default_risk_reward)
        elif signal_type == SignalType.SELL:
            stop_loss = current_price + (atr * atr_multiplier)
            take_profit = current_price - (atr * atr_multiplier * self.default_risk_reward)
        else:
            stop_loss = current_price
            take_profit = current_price
        
        return stop_loss, take_profit, risk_level
    
    def calculate_position_size(self, account_balance: float, entry_price: float, stop_loss: float, risk_level: RiskLevel) -> float:
        """Calculate appropriate position size based on risk management"""
        risk_amount = account_balance * self.max_risk_per_trade
        
        # Adjust risk based on risk level
        if risk_level == RiskLevel.LOW:
            risk_amount *= 1.5  # Allow slightly larger positions for low-risk trades
        elif risk_level == RiskLevel.HIGH:
            risk_amount *= 0.5  # Reduce position size for high-risk trades
        
        price_diff = abs(entry_price - stop_loss)
        if price_diff > 0:
            position_size = risk_amount / price_diff
        else:
            position_size = 0.01  # Minimum position size
        
        # Ensure minimum and maximum limits
        position_size = max(0.01, min(position_size, 10.0))
        return round(position_size, 2)
    
    async def get_ai_analysis(self, instrument: str, signal_type: SignalType, indicators: TechnicalIndicators, market_context: str) -> str:
        """Get AI-powered market analysis using Gemini"""
        if not self.gemini_model:
            return f"Technical analysis suggests {signal_type.value} signal for {instrument} based on current indicators."
        
        try:
            prompt = f"""
            As a professional forex trading analyst, provide a concise analysis of {instrument} based on these indicators:
            
            Technical Indicators:
            - RSI: {indicators.rsi:.1f}
            - MACD Histogram: {indicators.macd_histogram:.5f}
            - Price vs Bollinger Bands: Middle={indicators.bb_middle:.5f}, Upper={indicators.bb_upper:.5f}, Lower={indicators.bb_lower:.5f}
            - ATR (volatility): {indicators.atr:.5f}
            - EMA 9: {indicators.ema_9:.5f}, EMA 21: {indicators.ema_21:.5f}
            - Volatility: {indicators.volatility:.3%}
            
            Market Context: {market_context}
            Suggested Signal: {signal_type.value}
            
            Provide a 2-3 sentence analysis explaining:
            1. Why this signal makes sense
            2. Key risk factors to consider
            3. Market conditions impact
            
            Keep it professional and actionable for traders.
            """
            
            response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return f"Technical analysis indicates {signal_type.value} opportunity for {instrument}. Monitor price action and market conditions."
    
    async def generate_signal(self, instrument: str, timeframe: str = "H1") -> Optional[TradingSignal]:
        """Generate comprehensive trading signal"""
        if not self._is_initialized:
            await self.initialize()
        
        try:
            # Get current market data
            prices = await self.oanda_client.get_prices([instrument])
            if not prices:
                logger.error(f"No price data available for {instrument}")
                return None
            
            current_market = prices[0]
            current_price = (current_market.bid + current_market.ask) / 2
            
            # Get technical indicators
            indicators = await self.get_technical_indicators(instrument, timeframe)
            
            # Analyze signals
            signal_type, technical_score, reasoning = self.analyze_technical_signals(indicators, current_price)
            
            if signal_type == SignalType.HOLD:
                logger.info(f"No clear signal for {instrument}")
                return None
            
            # Calculate risk levels
            stop_loss, take_profit, risk_level = self.calculate_risk_levels(indicators, signal_type, current_price)
            
            # Calculate position size (assuming $10,000 account)
            position_size = self.calculate_position_size(10000, current_price, stop_loss, risk_level)
            
            # Risk/reward ratio
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Market context
            from oanda_api_integration import get_market_hours_info
            market_info = await get_market_hours_info()
            
            active_sessions = [name for name, info in market_info["sessions"].items() if info["active"]]
            market_session = ", ".join(active_sessions) if active_sessions else "Off-hours"
            
            market_context = f"Session: {market_session}, Volatility: {indicators.volatility:.3%}, Spread: {current_market.spread:.5f}"
            
            # Get AI analysis
            ai_analysis = await self.get_ai_analysis(instrument, signal_type, indicators, market_context)
            
            # Calculate confidence score
            confidence_score = technical_score
            
            # Adjust confidence based on market conditions
            if market_info["high_volatility"]:
                confidence_score *= 1.1  # Boost during high volatility periods
            
            if current_market.spread > indicators.atr * 0.5:
                confidence_score *= 0.8  # Reduce confidence for wide spreads
            
            confidence_score = min(confidence_score, 1.0)
            
            # Create signal
            signal = TradingSignal(
                instrument=instrument,
                signal_type=signal_type,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence_score=confidence_score,
                risk_level=risk_level,
                risk_reward_ratio=risk_reward_ratio,
                position_size=position_size,
                technical_score=technical_score,
                indicators=indicators,
                market_session=market_session,
                spread=current_market.spread,
                volatility=indicators.volatility,
                ai_analysis=ai_analysis,
                reasoning=reasoning,
                timeframe=timeframe,
                timestamp=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=4)  # Signals expire in 4 hours
            )
            
            logger.info(f"✅ Generated {signal_type.value} signal for {instrument} (confidence: {confidence_score:.1%})")
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {instrument}: {e}")
            return None
    
    async def generate_signals_batch(self, instruments: List[str], timeframe: str = "H1") -> List[TradingSignal]:
        """Generate signals for multiple instruments"""
        signals = []
        
        # Process instruments concurrently (with some rate limiting)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def generate_single_signal(instrument: str):
            async with semaphore:
                signal = await self.generate_signal(instrument, timeframe)
                if signal and signal.confidence_score >= 0.6:  # Only return high-confidence signals
                    signals.append(signal)
        
        # Run all signal generation concurrently
        tasks = [generate_single_signal(instrument) for instrument in instruments]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Sort by confidence score
        signals.sort(key=lambda s: s.confidence_score, reverse=True)
        
        logger.info(f"Generated {len(signals)} high-confidence signals from {len(instruments)} instruments")
        return signals


# Convenience functions
async def get_major_pairs_signals(timeframe: str = "H1") -> List[TradingSignal]:
    """Get signals for major currency pairs"""
    major_pairs = [
        "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF",
        "AUD_USD", "USD_CAD", "NZD_USD", "EUR_GBP",
        "GBP_JPY", "EUR_JPY", "AUD_JPY", "GBP_CHF"
    ]
    
    async with OANDASignalEngine() as engine:
        return await engine.generate_signals_batch(major_pairs, timeframe)


if __name__ == "__main__":
    # Test the signal engine
    async def test_signal_engine():
        try:
            print("Testing OANDA Signal Engine...")
            
            async with OANDASignalEngine() as engine:
                print("✅ Engine initialized")
                
                # Test single signal generation
                signal = await engine.generate_signal("EUR_USD")
                if signal:
                    print(f"✅ Signal: {signal.signal_type.value} {signal.instrument}")
                    print(f"   Entry: {signal.entry_price:.5f}")
                    print(f"   SL: {signal.stop_loss:.5f}, TP: {signal.take_profit:.5f}")
                    print(f"   Confidence: {signal.confidence_score:.1%}")
                    print(f"   AI Analysis: {signal.ai_analysis[:100]}...")
                else:
                    print("No signal generated")
                
                # Test batch generation
                print("\nTesting batch signal generation...")
                signals = await get_major_pairs_signals()
                print(f"✅ Generated {len(signals)} signals")
                
                for signal in signals[:3]:  # Show top 3
                    print(f"   {signal.signal_type.value} {signal.instrument} - {signal.confidence_score:.1%}")
        
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run test
    asyncio.run(test_signal_engine())