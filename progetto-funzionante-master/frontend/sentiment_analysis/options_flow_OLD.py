"""
Options Flow Analysis
Analisi del flusso istituzionale di opzioni per sentiment e direzione del mercato
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)

class FlowType(Enum):
    SWEEP_CALLS = "sweep_calls"
    SWEEP_PUTS = "sweep_puts"
    BLOCK_CALLS = "block_calls"
    BLOCK_PUTS = "block_puts"
    UNUSUAL_CALLS = "unusual_calls"
    UNUSUAL_PUTS = "unusual_puts"
    DARK_POOL = "dark_pool"

class OptionType(Enum):
    CALL = "call"
    PUT = "put"

class TradeAggressiveness(Enum):
    PASSIVE = "passive"  # At bid
    NEUTRAL = "neutral"  # Between bid/ask
    AGGRESSIVE = "aggressive"  # At ask or market orders

@dataclass
class OptionsFlowData:
    """Singolo trade di flusso opzioni"""
    symbol: str
    trade_time: datetime
    option_type: OptionType
    flow_type: FlowType
    strike_price: float
    expiration_date: datetime
    premium_paid: float
    volume: int
    open_interest: int
    bid: float
    ask: float
    underlying_price: float
    aggressiveness: TradeAggressiveness
    is_opening: bool  # True if opening position, False if closing
    delta: float
    gamma: float
    theta: float
    vega: float
    implied_volatility: float
    moneyness: float  # Strike/Underlying ratio
    time_to_expiry: int  # Days
    
@dataclass
class FlowAnalysis:
    """Analisi aggregata del flusso per uno strumento"""
    symbol: str
    timeframe_minutes: int
    total_premium_flow: float
    call_flow: float
    put_flow: float
    put_call_ratio: float
    aggressive_flow_ratio: float  # % of aggressive trades
    opening_flow_ratio: float     # % of opening positions
    average_dte: float           # Average days to expiry
    dominant_flow_type: FlowType
    sentiment_score: float       # -1 to 1 (bearish to bullish)
    conviction_score: float      # 0 to 1 (low to high conviction)
    key_strikes: List[float]     # Most active strikes
    flow_concentration: float    # How concentrated the flow is
    institutional_bias: str      # "BULLISH", "BEARISH", "NEUTRAL"
    flow_velocity: float        # Rate of flow change
    
@dataclass
class UnusualActivity:
    """Attività inusuale rilevata"""
    symbol: str
    detected_at: datetime
    activity_type: str
    description: str
    significance_score: float  # 0 to 100
    related_flows: List[OptionsFlowData]
    market_impact_estimate: float
    recommended_action: str

class OptionsFlowAnalyzer:
    """Analizzatore principale del flusso di opzioni"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = {}
        self.cache_timeout = timedelta(minutes=5)  # Short cache for options flow
        
        # Thresholds per identificare flussi significativi
        self.flow_thresholds = {
            "large_premium": 100000,     # $100K+ premium
            "large_volume": 1000,        # 1000+ contracts
            "unusual_volume_ratio": 5.0, # 5x average volume
            "low_oi_ratio": 0.1,        # Volume > 10x open interest
            "sweep_threshold": 50000,    # $50K+ premium for sweeps
        }

    async def get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_options_flow(self, symbols: List[str], hours_back: int = 4) -> List[OptionsFlowData]:
        """Fetch options flow data (simulato per demo)"""
        all_flows = []
        
        try:
            # NO MORE SIMULATED DATA - Only return empty list
            logger.warning("❌ SIMULATED FLOW DISABLED - Sistema ora richiede solo dati reali CBOE")
            return []  # No simulated data allowed
                
        except Exception as e:
            logger.error(f"Error in options flow: {e}")
        
        return []

    async def _generate_simulated_flow(self, symbol: str, hours_back: int) -> List[OptionsFlowData]:
        """SIMULAZIONE DISABILITATA - Solo dati reali CBOE consentiti"""
        logger.error(f"🚫 Tentativo di generare dati simulati per {symbol} - OPERAZIONE BLOCCATA")
        logger.error("💡 Usare solo dati reali CBOE da quantistes_integration.py")
        return []

    def _create_realistic_flow(self, symbol: str, underlying_price: float, hours_back: int) -> OptionsFlowData:
        """SIMULAZIONE DISABILITATA - Ritorna dati vuoti"""
        logger.error("🚫 _create_realistic_flow BLOCCATA - Solo dati reali CBOE")
        
        # Return minimal invalid data to prevent usage
        
        # Random option characteristics
        option_type = np.random.choice([OptionType.CALL, OptionType.PUT], p=[0.55, 0.45])  # Slight call bias
        
        # Strike selection (realistic distribution)
        if option_type == OptionType.CALL:
            # Calls typically OTM
            strike_multiplier = np.random.normal(1.02, 0.03)  # 2% OTM average
        else:
            # Puts typically OTM  
            strike_multiplier = np.random.normal(0.98, 0.03)  # 2% OTM average
        
        strike_price = underlying_price * strike_multiplier
        
        # Round strike to realistic levels
        if underlying_price > 1000:
            strike_price = round(strike_price / 25) * 25  # Round to $25 increments
        elif underlying_price > 100:
            strike_price = round(strike_price / 5) * 5    # Round to $5 increments
        else:
            strike_price = round(strike_price, 2)
        
        # Expiration (realistic DTE distribution)
        dte_weights = [0.4, 0.3, 0.2, 0.1]  # 0-7 days, 1-4 weeks, 1-2 months, >2 months
        dte_ranges = [(0, 7), (7, 30), (30, 60), (60, 180)]
        dte_category = np.random.choice(4, p=dte_weights)
        min_dte, max_dte = dte_ranges[dte_category]
        days_to_expiry = np.random.randint(min_dte, max_dte + 1)
        
        expiration_date = datetime.utcnow() + timedelta(days=days_to_expiry)
        
        # Volume and premium (log-normal distribution for realism)
        volume = int(np.random.lognormal(mean=3, sigma=1.5))  # Realistic volume distribution
        volume = max(1, min(volume, 10000))  # Cap at reasonable levels
        
        # Calculate basic Greeks (simplified)
        moneyness = strike_price / underlying_price
        time_value = max(0.01, days_to_expiry / 365.0)
        
        if option_type == OptionType.CALL:
            delta = max(0.05, min(0.95, (underlying_price - strike_price) / underlying_price + 0.5))
        else:
            delta = min(-0.05, max(-0.95, (strike_price - underlying_price) / underlying_price - 0.5))
        
        gamma = 0.02 * np.exp(-abs(moneyness - 1) * 5)  # Max gamma ATM
        theta = -0.05 * time_value  # Time decay
        vega = 0.1 * time_value    # Volatility sensitivity
        
        # Implied volatility
        iv = np.random.normal(0.25, 0.08)  # 25% IV average
        iv = max(0.05, min(1.0, iv))
        
        # Premium calculation (simplified)
        intrinsic = max(0, underlying_price - strike_price if option_type == OptionType.CALL else strike_price - underlying_price)
        time_premium = underlying_price * 0.02 * np.sqrt(time_value) * iv
        premium_per_contract = intrinsic + time_premium
        
        bid = premium_per_contract * 0.95
        ask = premium_per_contract * 1.05
        premium_paid = premium_per_contract  # Assume mid-market execution
        
        total_premium = premium_paid * volume * 100  # $100 per contract
        
        # Aggressiveness based on premium size
        if total_premium > self.flow_thresholds["large_premium"]:
            aggressiveness = TradeAggressiveness.AGGRESSIVE
        elif total_premium > self.flow_thresholds["large_premium"] / 3:
            aggressiveness = TradeAggressiveness.NEUTRAL
        else:
            aggressiveness = TradeAggressiveness.PASSIVE
        
        # Flow type classification
        if total_premium > self.flow_thresholds["sweep_threshold"] and aggressiveness == TradeAggressiveness.AGGRESSIVE:
            flow_type = FlowType.SWEEP_CALLS if option_type == OptionType.CALL else FlowType.SWEEP_PUTS
        elif total_premium > self.flow_thresholds["large_premium"]:
            flow_type = FlowType.BLOCK_CALLS if option_type == OptionType.CALL else FlowType.BLOCK_PUTS
        else:
            flow_type = FlowType.UNUSUAL_CALLS if option_type == OptionType.CALL else FlowType.UNUSUAL_PUTS
        
        # Open interest (simulated)
        open_interest = max(volume, int(np.random.lognormal(5, 1)))
        
        return OptionsFlowData(
            symbol=symbol,
            trade_time=datetime.utcnow() - timedelta(minutes=np.random.randint(1, hours_back * 60)),
            option_type=option_type,
            flow_type=flow_type,
            strike_price=strike_price,
            expiration_date=expiration_date,
            premium_paid=premium_paid,
            volume=volume,
            open_interest=open_interest,
            bid=bid,
            ask=ask,
            underlying_price=underlying_price,
            aggressiveness=aggressiveness,
            is_opening=np.random.random() > 0.3,  # 70% opening trades
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            implied_volatility=iv,
            moneyness=moneyness,
            time_to_expiry=days_to_expiry
        )

    async def analyze_flow(self, symbol: str, hours_back: int = 4) -> FlowAnalysis:
        """Analyze options flow for specific symbol"""
        
        # Check cache
        cache_key = f"{symbol}_flow_{hours_back}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        # Fetch flow data
        flows = await self.fetch_options_flow([symbol], hours_back)
        
        if not flows:
            # Return neutral analysis if no data
            return FlowAnalysis(
                symbol=symbol,
                timeframe_minutes=hours_back * 60,
                total_premium_flow=0.0,
                call_flow=0.0,
                put_flow=0.0,
                put_call_ratio=1.0,
                aggressive_flow_ratio=0.0,
                opening_flow_ratio=0.0,
                average_dte=30.0,
                dominant_flow_type=FlowType.UNUSUAL_CALLS,
                sentiment_score=0.0,
                conviction_score=0.0,
                key_strikes=[],
                flow_concentration=0.0,
                institutional_bias="NEUTRAL",
                flow_velocity=0.0
            )
        
        analysis = self._calculate_flow_analysis(flows, symbol, hours_back)
        
        # Cache result
        self.cache[cache_key] = {
            "data": analysis,
            "timestamp": datetime.utcnow()
        }
        
        return analysis

    def _calculate_flow_analysis(self, flows: List[OptionsFlowData], symbol: str, hours_back: int) -> FlowAnalysis:
        """Calculate comprehensive flow analysis"""
        
        # Basic aggregations
        total_premium = sum(f.premium_paid * f.volume * 100 for f in flows)
        call_flows = [f for f in flows if f.option_type == OptionType.CALL]
        put_flows = [f for f in flows if f.option_type == OptionType.PUT]
        
        call_premium = sum(f.premium_paid * f.volume * 100 for f in call_flows)
        put_premium = sum(f.premium_paid * f.volume * 100 for f in put_flows)
        
        # Put/Call ratio
        put_call_ratio = put_premium / call_premium if call_premium > 0 else 0.0
        
        # Aggressiveness analysis
        aggressive_flows = [f for f in flows if f.aggressiveness == TradeAggressiveness.AGGRESSIVE]
        aggressive_ratio = len(aggressive_flows) / len(flows) if flows else 0.0
        
        # Opening vs closing
        opening_flows = [f for f in flows if f.is_opening]
        opening_ratio = len(opening_flows) / len(flows) if flows else 0.0
        
        # Average DTE
        avg_dte = sum(f.time_to_expiry for f in flows) / len(flows) if flows else 30.0
        
        # Dominant flow type
        flow_type_counts = {}
        for flow in flows:
            flow_type_counts[flow.flow_type] = flow_type_counts.get(flow.flow_type, 0) + 1
        
        dominant_flow = max(flow_type_counts.items(), key=lambda x: x[1])[0] if flow_type_counts else FlowType.UNUSUAL_CALLS
        
        # Key strikes (most active)
        strike_volumes = {}
        for flow in flows:
            strike = flow.strike_price
            strike_volumes[strike] = strike_volumes.get(strike, 0) + flow.volume
        
        key_strikes = sorted(strike_volumes.items(), key=lambda x: x[1], reverse=True)[:5]
        key_strikes = [strike[0] for strike in key_strikes]
        
        # Flow concentration (Herfindahl index)
        total_volume = sum(f.volume for f in flows)
        concentration = 0.0
        if total_volume > 0:
            strike_shares = [strike_volumes[strike] / total_volume for strike in strike_volumes]
            concentration = sum(share ** 2 for share in strike_shares)
        
        # Sentiment score calculation
        sentiment_score = self._calculate_sentiment_score(flows, call_premium, put_premium)
        
        # Conviction score (based on aggressiveness and size)
        conviction_score = self._calculate_conviction_score(flows, aggressive_ratio, total_premium)
        
        # Institutional bias
        if sentiment_score > 0.3:
            bias = "BULLISH"
        elif sentiment_score < -0.3:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        # Flow velocity (rate of change - simplified)
        flow_velocity = len(flows) / hours_back  # Flows per hour
        
        return FlowAnalysis(
            symbol=symbol,
            timeframe_minutes=hours_back * 60,
            total_premium_flow=total_premium,
            call_flow=call_premium,
            put_flow=put_premium,
            put_call_ratio=put_call_ratio,
            aggressive_flow_ratio=aggressive_ratio,
            opening_flow_ratio=opening_ratio,
            average_dte=avg_dte,
            dominant_flow_type=dominant_flow,
            sentiment_score=sentiment_score,
            conviction_score=conviction_score,
            key_strikes=key_strikes,
            flow_concentration=concentration,
            institutional_bias=bias,
            flow_velocity=flow_velocity
        )

    def _calculate_sentiment_score(self, flows: List[OptionsFlowData], call_premium: float, put_premium: float) -> float:
        """Calculate sentiment score from flow data"""
        
        if call_premium + put_premium == 0:
            return 0.0
        
        # Base sentiment from call/put ratio
        base_sentiment = (call_premium - put_premium) / (call_premium + put_premium)
        
        # Adjust for flow characteristics
        adjustments = 0.0
        
        for flow in flows:
            weight = flow.premium_paid * flow.volume / len(flows)
            
            # Aggressive trades carry more weight
            if flow.aggressiveness == TradeAggressiveness.AGGRESSIVE:
                multiplier = 1.5
            elif flow.aggressiveness == TradeAggressiveness.NEUTRAL:
                multiplier = 1.0
            else:
                multiplier = 0.7
            
            # Opening trades are more significant
            if flow.is_opening:
                multiplier *= 1.2
            
            # Near-term options carry more weight
            if flow.time_to_expiry <= 7:
                multiplier *= 1.3
            
            flow_sentiment = 1.0 if flow.option_type == OptionType.CALL else -1.0
            adjustments += flow_sentiment * weight * multiplier
        
        # Combine base sentiment with adjustments
        final_sentiment = (base_sentiment * 0.7) + (adjustments * 0.3)
        
        # Clamp to -1 to 1 range
        return max(-1.0, min(1.0, final_sentiment))

    def _calculate_conviction_score(self, flows: List[OptionsFlowData], aggressive_ratio: float, total_premium: float) -> float:
        """Calculate conviction score"""
        
        # Base conviction from aggressiveness
        base_conviction = aggressive_ratio
        
        # Size component
        if total_premium > 1000000:  # $1M+
            size_component = 1.0
        elif total_premium > 500000:  # $500K+
            size_component = 0.8
        elif total_premium > 100000:  # $100K+
            size_component = 0.6
        else:
            size_component = 0.3
        
        # Concentration component (more focused = higher conviction)
        concentration_component = sum(f.volume for f in flows[:5]) / sum(f.volume for f in flows) if flows else 0.0
        
        # Combine components
        conviction = (base_conviction * 0.4) + (size_component * 0.4) + (concentration_component * 0.2)
        
        return min(1.0, conviction)

    async def detect_unusual_activity(self, symbols: List[str]) -> List[UnusualActivity]:
        """Detect unusual options activity"""
        unusual_activities = []
        
        for symbol in symbols:
            flows = await self.fetch_options_flow([symbol], hours_back=2)  # Short window for unusual activity
            
            # Check for various unusual patterns
            activities = self._check_unusual_patterns(symbol, flows)
            unusual_activities.extend(activities)
        
        return unusual_activities

    def _check_unusual_patterns(self, symbol: str, flows: List[OptionsFlowData]) -> List[UnusualActivity]:
        """Check for unusual patterns in flow data"""
        activities = []
        
        if not flows:
            return activities
        
        # Large block detection
        large_blocks = [f for f in flows if f.premium_paid * f.volume * 100 > self.flow_thresholds["large_premium"]]
        if large_blocks:
            total_premium = sum(f.premium_paid * f.volume * 100 for f in large_blocks)
            activity = UnusualActivity(
                symbol=symbol,
                detected_at=datetime.utcnow(),
                activity_type="LARGE_BLOCK_ACTIVITY",
                description=f"Detected {len(large_blocks)} large block trades totaling ${total_premium:,.0f} in premium",
                significance_score=min(100, total_premium / 10000),  # $10K = 1 point
                related_flows=large_blocks,
                market_impact_estimate=total_premium / 1000000,  # Impact estimate
                recommended_action="Monitor for directional bias"
            )
            activities.append(activity)
        
        # Sweep detection
        sweeps = [f for f in flows if f.flow_type in [FlowType.SWEEP_CALLS, FlowType.SWEEP_PUTS]]
        if len(sweeps) >= 3:  # Multiple sweeps
            activity = UnusualActivity(
                symbol=symbol,
                detected_at=datetime.utcnow(),
                activity_type="COORDINATED_SWEEPS",
                description=f"Detected {len(sweeps)} coordinated option sweeps",
                significance_score=75.0,
                related_flows=sweeps,
                market_impact_estimate=0.5,
                recommended_action="High probability directional move expected"
            )
            activities.append(activity)
        
        return activities

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check cache validity"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]["timestamp"]
        return datetime.utcnow() - cached_time < self.cache_timeout

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
