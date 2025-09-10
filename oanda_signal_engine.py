"""
OANDA-Based AI Signal Generation Engine
=====================================

Professional signal generation system using OANDA market data and AI analysis.
Replaces VPS/MT5 dependency with direct OANDA REST API integration.

Features:
- Real-time market data from OANDA
- Advanced technical analysis
- AI-powered signal generation using Gemini
- Risk management and position sizing
- Production-ready error handling

Author: Backend Performance Architect
Date: September 2025
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, asdict
import json
import numpy as np
import pandas as pd
from enum import Enum

# Import our OANDA client
from oanda_api_integration import (
    OANDAClient, 
    create_oanda_client, 
    OANDAMarketDataProvider,
    Granularity, 
    MarketPrice,
    OANDAAPIError,
    OANDAConnectionError
)

# AI Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google GenerativeAI not available - AI analysis will be limited")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# === SIGNAL TYPES AND DATA MODELS ===

class SignalType(Enum):
    """Signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class RiskLevel(Enum):
    """Risk levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"

@dataclass
class TechnicalIndicators:
    """Technical analysis indicators"""
    rsi: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    sma_20: float
    sma_50: float
    sma_200: float
    bollinger_upper: float
    bollinger_lower: float
    bollinger_middle: float
    atr: float
    volume_sma: float
    momentum: float
    stochastic_k: float
    stochastic_d: float

@dataclass
class MarketContext:
    """Market context and conditions"""
    symbol: str
    timeframe: str
    current_price: float
    price_change_24h: float
    price_change_pct_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    volatility: float
    spread: float
    market_session: str
    major_news_events: List[str]

@dataclass
class TradingSignal:
    """Complete trading signal with AI analysis"""
    id: str
    symbol: str
    signal_type: SignalType
    confidence: float
    reliability: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_level: RiskLevel
    position_size_suggestion: float
    risk_reward_ratio: float
    timeframe: str
    technical_indicators: TechnicalIndicators
    market_context: MarketContext
    ai_analysis: str
    gemini_explanation: str
    generated_at: datetime
    expires_at: datetime
    data_sources: List[str]
    metadata: Dict[str, Any]

# === TECHNICAL ANALYSIS ENGINE ===

class TechnicalAnalyzer:
    """Advanced technical analysis using OANDA market data"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TechnicalAnalyzer")
    
    async def analyze_symbol(
        self, 
        oanda_provider: OANDAMarketDataProvider, 
        symbol: str, 
        timeframe: str = "H1"
    ) -> TechnicalIndicators:
        """
        Perform comprehensive technical analysis on a symbol
        
        Args:
            oanda_provider: OANDA market data provider
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Analysis timeframe (H1, H4, D1, etc.)
        
        Returns:
            Technical indicators
        """
        try:
            # Get historical data for analysis
            df = await oanda_provider.get_market_data(symbol, timeframe, count=200)
            
            if df is None or df.empty:
                raise ValueError(f"No market data available for {symbol}")
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            self.logger.info(f"Technical analysis completed for {symbol} - RSI: {indicators.rsi:.2f}")
            return indicators
            
        except Exception as e:
            self.logger.error(f"Technical analysis failed for {symbol}: {e}")
            # Return neutral indicators on error
            return self._get_neutral_indicators()
    
    def _calculate_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Calculate all technical indicators"""
        try:
            # Ensure we have enough data
            if len(df) < 50:
                return self._get_neutral_indicators()
            
            # Price data
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df.get('volume', df.get('tick_volume', pd.Series([1000] * len(df))))
            
            # RSI (14-period)
            rsi = self._calculate_rsi(close, 14)
            
            # MACD (12, 26, 9)
            macd_line, macd_signal, macd_histogram = self._calculate_macd(close)
            
            # Moving Averages
            sma_20 = close.rolling(20).mean().iloc[-1]
            sma_50 = close.rolling(50).mean().iloc[-1]
            sma_200 = close.rolling(min(200, len(close))).mean().iloc[-1]
            
            # Bollinger Bands (20, 2)
            bb_middle = sma_20
            bb_std = close.rolling(20).std().iloc[-1]
            bb_upper = bb_middle + (2 * bb_std)
            bb_lower = bb_middle - (2 * bb_std)
            
            # ATR (14-period)
            atr = self._calculate_atr(high, low, close, 14)
            
            # Volume SMA
            volume_sma = volume.rolling(20).mean().iloc[-1]
            
            # Momentum (10-period)
            momentum = ((close.iloc[-1] - close.iloc[-10]) / close.iloc[-10]) * 100 if len(close) > 10 else 0
            
            # Stochastic (14, 3, 3)
            stoch_k, stoch_d = self._calculate_stochastic(high, low, close)
            
            return TechnicalIndicators(
                rsi=float(rsi),
                macd_line=float(macd_line),
                macd_signal=float(macd_signal),
                macd_histogram=float(macd_histogram),
                sma_20=float(sma_20),
                sma_50=float(sma_50),
                sma_200=float(sma_200),
                bollinger_upper=float(bb_upper),
                bollinger_lower=float(bb_lower),
                bollinger_middle=float(bb_middle),
                atr=float(atr),
                volume_sma=float(volume_sma),
                momentum=float(momentum),
                stochastic_k=float(stoch_k),
                stochastic_d=float(stoch_d)
            )
            
        except Exception as e:
            self.logger.error(f"Indicator calculation failed: {e}")
            return self._get_neutral_indicators()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50.0
        except:
            return 50.0
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float, float]:
        """Calculate MACD indicator"""
        try:
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9).mean()
            macd_histogram = macd_line - macd_signal
            
            return (
                float(macd_line.iloc[-1]),
                float(macd_signal.iloc[-1]),
                float(macd_histogram.iloc[-1])
            )
        except:
            return (0.0, 0.0, 0.0)
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]
            return float(atr)
        except:
            return 0.001
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Tuple[float, float]:
        """Calculate Stochastic oscillator"""
        try:
            lowest_low = low.rolling(14).min()
            highest_high = high.rolling(14).max()
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(3).mean()
            
            return (
                float(k_percent.iloc[-1]),
                float(d_percent.iloc[-1])
            )
        except:
            return (50.0, 50.0)
    
    def _get_neutral_indicators(self) -> TechnicalIndicators:
        """Return neutral technical indicators when calculation fails"""
        return TechnicalIndicators(
            rsi=50.0,
            macd_line=0.0,
            macd_signal=0.0,
            macd_histogram=0.0,
            sma_20=1.0,
            sma_50=1.0,
            sma_200=1.0,
            bollinger_upper=1.01,
            bollinger_lower=0.99,
            bollinger_middle=1.0,
            atr=0.001,
            volume_sma=1000.0,
            momentum=0.0,
            stochastic_k=50.0,
            stochastic_d=50.0
        )

# === AI SIGNAL GENERATOR ===

class AISignalGenerator:
    """AI-powered signal generation using technical analysis and Gemini AI"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.logger = logging.getLogger(f"{__name__}.AISignalGenerator")
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                self.gemini_enabled = True
                self.logger.info("Gemini AI initialized successfully")
            except Exception as e:
                self.logger.error(f"Gemini initialization failed: {e}")
                self.gemini_enabled = False
        else:
            self.gemini_enabled = False
            self.logger.warning("Gemini AI not available")
    
    async def generate_signal(
        self,
        symbol: str,
        current_price: float,
        technical_indicators: TechnicalIndicators,
        market_context: MarketContext,
        risk_tolerance: str = "medium"
    ) -> TradingSignal:
        """
        Generate comprehensive trading signal using AI analysis
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            technical_indicators: Technical analysis results
            market_context: Market context information
            risk_tolerance: Risk tolerance level (low/medium/high)
        
        Returns:
            Complete trading signal with AI analysis
        """
        try:
            # Generate base signal from technical analysis
            base_signal = self._generate_technical_signal(
                symbol, current_price, technical_indicators, market_context
            )
            
            # Enhance with AI analysis if available
            ai_analysis, gemini_explanation = await self._generate_ai_analysis(
                symbol, current_price, technical_indicators, market_context, base_signal
            )
            
            # Calculate position sizing and risk management
            position_size, risk_level = self._calculate_position_sizing(
                base_signal, technical_indicators, risk_tolerance
            )
            
            # Create complete signal
            signal = TradingSignal(
                id=f"OANDA_{symbol}_{int(datetime.now().timestamp())}",
                symbol=symbol,
                signal_type=base_signal["type"],
                confidence=base_signal["confidence"],
                reliability=base_signal["reliability"],
                entry_price=base_signal["entry_price"],
                stop_loss=base_signal["stop_loss"],
                take_profit=base_signal["take_profit"],
                risk_level=risk_level,
                position_size_suggestion=position_size,
                risk_reward_ratio=base_signal["risk_reward"],
                timeframe=market_context.timeframe,
                technical_indicators=technical_indicators,
                market_context=market_context,
                ai_analysis=ai_analysis,
                gemini_explanation=gemini_explanation,
                generated_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
                data_sources=["OANDA", "TechnicalAnalysis", "GeminiAI"] if self.gemini_enabled else ["OANDA", "TechnicalAnalysis"],
                metadata={
                    "oanda_spread": market_context.spread,
                    "volatility": market_context.volatility,
                    "market_session": market_context.market_session,
                    "technical_score": base_signal["technical_score"]
                }
            )
            
            self.logger.info(f"Generated {signal.signal_type.value} signal for {symbol} - Confidence: {signal.confidence:.1f}%, Reliability: {signal.reliability:.1f}%")
            return signal
            
        except Exception as e:
            self.logger.error(f"Signal generation failed for {symbol}: {e}")
            raise
    
    def _generate_technical_signal(
        self,
        symbol: str,
        current_price: float,
        indicators: TechnicalIndicators,
        context: MarketContext
    ) -> Dict[str, Any]:
        """Generate signal based on technical analysis"""
        try:
            # Technical scoring system
            buy_signals = 0
            sell_signals = 0
            total_weight = 0
            
            # RSI Analysis (Weight: 20)
            if indicators.rsi < 30:
                buy_signals += 20
            elif indicators.rsi > 70:
                sell_signals += 20
            elif indicators.rsi < 45:
                buy_signals += 5
            elif indicators.rsi > 55:
                sell_signals += 5
            total_weight += 20
            
            # MACD Analysis (Weight: 25)
            if indicators.macd_line > indicators.macd_signal and indicators.macd_histogram > 0:
                buy_signals += 25
            elif indicators.macd_line < indicators.macd_signal and indicators.macd_histogram < 0:
                sell_signals += 25
            total_weight += 25
            
            # Moving Average Analysis (Weight: 20)
            ma_score = 0
            if current_price > indicators.sma_20 > indicators.sma_50:
                ma_score += 10
            if current_price > indicators.sma_50 > indicators.sma_200:
                ma_score += 10
            if ma_score > 0:
                buy_signals += ma_score
            elif current_price < indicators.sma_20 < indicators.sma_50:
                sell_signals += 20
            total_weight += 20
            
            # Bollinger Bands (Weight: 15)
            if current_price < indicators.bollinger_lower:
                buy_signals += 15  # Oversold
            elif current_price > indicators.bollinger_upper:
                sell_signals += 15  # Overbought
            total_weight += 15
            
            # Stochastic (Weight: 10)
            if indicators.stochastic_k < 20 and indicators.stochastic_d < 20:
                buy_signals += 10
            elif indicators.stochastic_k > 80 and indicators.stochastic_d > 80:
                sell_signals += 10
            total_weight += 10
            
            # Momentum (Weight: 10)
            if indicators.momentum > 1.0:
                buy_signals += 10
            elif indicators.momentum < -1.0:
                sell_signals += 10
            total_weight += 10
            
            # Determine signal type and strength
            buy_score = (buy_signals / total_weight) * 100
            sell_score = (sell_signals / total_weight) * 100
            
            if buy_score > sell_score and buy_score > 40:
                signal_type = SignalType.BUY
                confidence = min(95, buy_score)
                reliability = min(90, buy_score * 0.8)
            elif sell_score > buy_score and sell_score > 40:
                signal_type = SignalType.SELL
                confidence = min(95, sell_score)
                reliability = min(90, sell_score * 0.8)
            else:
                signal_type = SignalType.HOLD
                confidence = 30
                reliability = 20
            
            # Calculate entry, stop loss, and take profit
            if signal_type == SignalType.BUY:
                entry_price = current_price
                stop_loss = current_price - (indicators.atr * 2)
                take_profit = current_price + (indicators.atr * 3)
            elif signal_type == SignalType.SELL:
                entry_price = current_price
                stop_loss = current_price + (indicators.atr * 2)
                take_profit = current_price - (indicators.atr * 3)
            else:
                entry_price = current_price
                stop_loss = current_price
                take_profit = current_price
            
            # Calculate risk/reward ratio
            risk_reward = 0
            if signal_type != SignalType.HOLD:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                risk_reward = reward / risk if risk > 0 else 0
            
            return {
                "type": signal_type,
                "confidence": confidence,
                "reliability": reliability,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_reward": risk_reward,
                "technical_score": (buy_signals + sell_signals) / total_weight * 100,
                "buy_score": buy_score,
                "sell_score": sell_score
            }
            
        except Exception as e:
            self.logger.error(f"Technical signal generation failed: {e}")
            # Return neutral signal on error
            return {
                "type": SignalType.HOLD,
                "confidence": 20,
                "reliability": 10,
                "entry_price": current_price,
                "stop_loss": current_price,
                "take_profit": current_price,
                "risk_reward": 0,
                "technical_score": 0,
                "buy_score": 0,
                "sell_score": 0
            }
    
    async def _generate_ai_analysis(
        self,
        symbol: str,
        current_price: float,
        indicators: TechnicalIndicators,
        context: MarketContext,
        base_signal: Dict[str, Any]
    ) -> Tuple[str, str]:
        """Generate AI-powered analysis using Gemini"""
        
        # Comprehensive technical analysis summary
        technical_summary = f"""
        Technical Analysis for {symbol}:
        - Current Price: {current_price:.5f}
        - RSI: {indicators.rsi:.2f} ({'Oversold' if indicators.rsi < 30 else 'Overbought' if indicators.rsi > 70 else 'Neutral'})
        - MACD: {indicators.macd_line:.6f} ({'Bullish' if indicators.macd_line > indicators.macd_signal else 'Bearish'})
        - Price vs SMA20: {((current_price - indicators.sma_20) / indicators.sma_20 * 100):+.2f}%
        - Bollinger Position: {'Upper' if current_price > indicators.bollinger_upper else 'Lower' if current_price < indicators.bollinger_lower else 'Middle'}
        - Momentum: {indicators.momentum:+.2f}%
        - ATR: {indicators.atr:.5f}
        - Market Session: {context.market_session}
        - 24h Change: {context.price_change_pct_24h:+.2f}%
        
        Signal: {base_signal['type'].value} (Confidence: {base_signal['confidence']:.1f}%, Technical Score: {base_signal['technical_score']:.1f})
        """
        
        if not self.gemini_enabled:
            return technical_summary, "AI analysis not available - using technical analysis only"
        
        try:
            # Create comprehensive prompt for Gemini
            prompt = f"""
            You are an expert forex/CFD trading analyst. Analyze this market data and provide professional trading insight:

            {technical_summary}

            Please provide:
            1. Market condition assessment
            2. Key technical levels and patterns
            3. Risk factors and considerations
            4. Trade timing and execution advice
            5. Overall market outlook

            Keep response concise but professional (200-300 words).
            """
            
            # Generate AI analysis with timeout
            response = await asyncio.wait_for(
                self._call_gemini_async(prompt),
                timeout=15.0
            )
            
            gemini_analysis = response.text if response else "AI analysis unavailable"
            
            return technical_summary, gemini_analysis
            
        except asyncio.TimeoutError:
            self.logger.warning("Gemini API timeout")
            return technical_summary, "AI analysis timeout - using technical analysis"
        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            return technical_summary, f"AI analysis error: {str(e)}"
    
    async def _call_gemini_async(self, prompt: str):
        """Call Gemini API asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.gemini_model.generate_content(prompt)
        )
    
    def _calculate_position_sizing(
        self,
        base_signal: Dict[str, Any],
        indicators: TechnicalIndicators,
        risk_tolerance: str
    ) -> Tuple[float, RiskLevel]:
        """Calculate position size and risk level"""
        try:
            # Risk multipliers based on tolerance
            risk_multipliers = {
                "low": 0.5,
                "medium": 1.0,
                "high": 1.5
            }
            
            multiplier = risk_multipliers.get(risk_tolerance, 1.0)
            
            # Base position size (conservative)
            base_position = 0.01  # 0.01 lots
            
            # Adjust based on signal confidence
            confidence_factor = base_signal["confidence"] / 100
            
            # Adjust based on volatility (ATR)
            volatility_factor = min(2.0, 0.001 / indicators.atr) if indicators.atr > 0 else 1.0
            
            # Calculate final position size
            position_size = base_position * confidence_factor * volatility_factor * multiplier
            position_size = max(0.01, min(1.0, position_size))  # Clamp between 0.01 and 1.0
            
            # Determine risk level
            if base_signal["confidence"] < 50 or indicators.atr > 0.002:
                risk_level = RiskLevel.HIGH
            elif base_signal["confidence"] > 75 and indicators.atr < 0.0005:
                risk_level = RiskLevel.LOW
            else:
                risk_level = RiskLevel.MEDIUM
            
            return round(position_size, 2), risk_level
            
        except Exception as e:
            self.logger.error(f"Position sizing calculation failed: {e}")
            return 0.01, RiskLevel.MEDIUM

# === MAIN SIGNAL ENGINE ===

class OANDASignalEngine:
    """Main OANDA-based signal generation engine"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.OANDASignalEngine")
        
        # Initialize components
        self.oanda_client = None
        self.oanda_provider = None
        self.technical_analyzer = TechnicalAnalyzer()
        self.ai_generator = AISignalGenerator(gemini_api_key)
        
        # Supported instruments
        self.supported_symbols = [
            "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD", 
            "USD_CAD", "NZD_USD", "EUR_GBP", "EUR_JPY", "GBP_JPY",
            "XAU_USD", "XAG_USD", "US500_USD", "DE30_EUR", "UK100_GBP"
        ]
        
        self.logger.info("OANDA Signal Engine initialized")
    
    async def initialize(self):
        """Initialize OANDA connection and providers"""
        try:
            # Create OANDA client
            self.oanda_client = create_oanda_client()
            await self.oanda_client.connect()
            
            # Create market data provider
            self.oanda_provider = OANDAMarketDataProvider(self.oanda_client)
            
            # Validate connection
            health = await self.oanda_client.health_check()
            if health["status"] != "healthy":
                raise OANDAConnectionError("OANDA connection unhealthy")
            
            self.logger.info("OANDA Signal Engine fully initialized and connected")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OANDA Signal Engine: {e}")
            raise
    
    async def generate_signal_for_symbol(
        self, 
        symbol: str, 
        timeframe: str = "H1",
        risk_tolerance: str = "medium"
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal for a specific symbol
        
        Args:
            symbol: Trading symbol (OANDA format, e.g., "EUR_USD")
            timeframe: Analysis timeframe
            risk_tolerance: Risk tolerance level
        
        Returns:
            Trading signal or None if generation fails
        """
        try:
            if not self.oanda_client or not self.oanda_provider:
                await self.initialize()
            
            # Normalize symbol to OANDA format
            oanda_symbol = self.oanda_client.normalize_instrument(symbol)
            
            if oanda_symbol not in self.supported_symbols:
                self.logger.warning(f"Symbol {symbol} not supported")
                return None
            
            # Get current market data
            current_price = await self.oanda_provider.get_real_time_price(symbol)
            if not current_price:
                self.logger.error(f"Could not get current price for {symbol}")
                return None
            
            # Perform technical analysis
            technical_indicators = await self.technical_analyzer.analyze_symbol(
                self.oanda_provider, symbol, timeframe
            )
            
            # Build market context
            market_context = await self._build_market_context(symbol, current_price, timeframe)
            
            # Generate AI signal
            signal = await self.ai_generator.generate_signal(
                symbol,
                current_price,
                technical_indicators,
                market_context,
                risk_tolerance
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Signal generation failed for {symbol}: {e}")
            return None
    
    async def generate_signals_batch(
        self, 
        symbols: List[str],
        timeframe: str = "H1",
        min_confidence: float = 60.0
    ) -> List[TradingSignal]:
        """
        Generate signals for multiple symbols
        
        Args:
            symbols: List of trading symbols
            timeframe: Analysis timeframe
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of trading signals meeting confidence criteria
        """
        try:
            signals = []
            
            # Generate signals concurrently with rate limiting
            tasks = []
            for symbol in symbols[:10]:  # Limit concurrent requests
                task = asyncio.create_task(
                    self.generate_signal_for_symbol(symbol, timeframe)
                )
                tasks.append(task)
                
                # Small delay between requests to respect rate limits
                await asyncio.sleep(0.1)
            
            # Wait for all signals to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful signals
            for result in results:
                if isinstance(result, TradingSignal):
                    if result.confidence >= min_confidence:
                        signals.append(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Signal generation error: {result}")
            
            self.logger.info(f"Generated {len(signals)} signals meeting confidence threshold {min_confidence}%")
            return signals
            
        except Exception as e:
            self.logger.error(f"Batch signal generation failed: {e}")
            return []
    
    async def _build_market_context(
        self, 
        symbol: str, 
        current_price: float, 
        timeframe: str
    ) -> MarketContext:
        """Build market context information"""
        try:
            # Get historical data for context
            df = await self.oanda_provider.get_market_data(symbol, timeframe, count=24)
            
            if df is not None and not df.empty:
                high_24h = df['high'].max()
                low_24h = df['low'].min()
                volume_24h = df['volume'].sum() if 'volume' in df else 0
                
                # Calculate price change
                if len(df) > 1:
                    prev_price = df['close'].iloc[-2]
                    price_change_24h = current_price - prev_price
                    price_change_pct_24h = (price_change_24h / prev_price) * 100
                else:
                    price_change_24h = 0
                    price_change_pct_24h = 0
                
                # Calculate volatility (ATR-based)
                volatility = df['high'].subtract(df['low']).mean() / current_price if not df.empty else 0.001
            else:
                high_24h = current_price * 1.01
                low_24h = current_price * 0.99
                volume_24h = 0
                price_change_24h = 0
                price_change_pct_24h = 0
                volatility = 0.001
            
            # Determine market session
            current_hour = datetime.now().hour
            if 0 <= current_hour < 6:
                market_session = "Asia-Pacific"
            elif 6 <= current_hour < 14:
                market_session = "European"
            else:
                market_session = "North American"
            
            # Get current prices to calculate spread
            try:
                prices = await self.oanda_client.get_current_prices([symbol])
                spread = prices[0].spread if prices else 0.0001
            except:
                spread = 0.0001
            
            return MarketContext(
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
                price_change_24h=price_change_24h,
                price_change_pct_24h=price_change_pct_24h,
                volume_24h=volume_24h,
                high_24h=high_24h,
                low_24h=low_24h,
                volatility=volatility,
                spread=spread,
                market_session=market_session,
                major_news_events=[]  # Could be enhanced with news feeds
            )
            
        except Exception as e:
            self.logger.error(f"Market context building failed for {symbol}: {e}")
            
            # Return minimal context on error
            return MarketContext(
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
                price_change_24h=0,
                price_change_pct_24h=0,
                volume_24h=0,
                high_24h=current_price * 1.01,
                low_24h=current_price * 0.99,
                volatility=0.001,
                spread=0.0001,
                market_session="Unknown",
                major_news_events=[]
            )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get engine health status"""
        try:
            if not self.oanda_client:
                return {"status": "disconnected", "error": "Not initialized"}
            
            # Check OANDA connection
            health = await self.oanda_client.health_check()
            
            # Test signal generation
            try:
                test_signal = await self.generate_signal_for_symbol("EUR_USD", "H1")
                signal_generation = "operational" if test_signal else "degraded"
            except:
                signal_generation = "error"
            
            return {
                "status": "healthy" if health["status"] == "healthy" else "degraded",
                "oanda_connection": health["status"],
                "signal_generation": signal_generation,
                "ai_analysis": "enabled" if self.ai_generator.gemini_enabled else "disabled",
                "supported_symbols": len(self.supported_symbols),
                "response_time_ms": health.get("response_time_ms", 0),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.oanda_client:
                await self.oanda_client.disconnect()
            self.logger.info("OANDA Signal Engine cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

# === EXAMPLE USAGE ===

async def example_usage():
    """Example of how to use the OANDA Signal Engine"""
    
    # Initialize engine
    engine = OANDASignalEngine()
    
    try:
        await engine.initialize()
        
        # Generate single signal
        signal = await engine.generate_signal_for_symbol("EURUSD", "H1", "medium")
        
        if signal:
            print(f"Generated Signal:")
            print(f"  Symbol: {signal.symbol}")
            print(f"  Type: {signal.signal_type.value}")
            print(f"  Confidence: {signal.confidence:.1f}%")
            print(f"  Entry: {signal.entry_price:.5f}")
            print(f"  Stop Loss: {signal.stop_loss:.5f}")
            print(f"  Take Profit: {signal.take_profit:.5f}")
            print(f"  Risk/Reward: {signal.risk_reward_ratio:.2f}")
            print(f"  AI Analysis: {signal.ai_analysis[:200]}...")
        
        # Generate batch signals
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        signals = await engine.generate_signals_batch(symbols)
        
        print(f"\nGenerated {len(signals)} batch signals")
        for s in signals:
            print(f"  {s.symbol}: {s.signal_type.value} - {s.confidence:.1f}%")
        
        # Check health
        health = await engine.get_health_status()
        print(f"\nEngine Health: {health['status']}")
        
    finally:
        await engine.cleanup()

if __name__ == "__main__":
    asyncio.run(example_usage())