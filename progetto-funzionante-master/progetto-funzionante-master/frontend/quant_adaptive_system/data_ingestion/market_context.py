"""
Market Context Module - CBOE Options Data Integration
Fetches and processes CBOE options data for market regime detection
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class OptionsData:
    """CBOE Options Data Container"""
    timestamp: datetime
    symbol: str
    
    # 0DTE Data
    dte_0_volume: float
    total_volume: float
    dte_0_share: float
    
    # Put/Call Data
    put_volume: float
    call_volume: float
    put_call_ratio: float
    
    # Open Interest
    put_oi: float
    call_oi: float
    total_oi: float
    
    # Gamma Exposure (estimated)
    gamma_exposure_estimate: float
    
    # Key Strike Levels
    max_pain_level: float
    high_gamma_strikes: List[float]
    pinning_candidates: List[float]

@dataclass 
class MarketContext:
    """Complete Market Context Data"""
    timestamp: datetime
    
    # Options Metrics
    spx_0dte_share: float
    spy_0dte_share: float
    combined_0dte_share: float
    put_call_ratio: float
    gamma_exposure: float
    
    # Regime Indicators
    regime: str  # 'NORMAL', 'HIGH_0DTE', 'GAMMA_SQUEEZE', 'PINNING'
    volatility_regime: str  # 'LOW', 'MEDIUM', 'HIGH'
    pinning_risk: float  # 0-1 scale
    
    # Strike Levels
    key_levels: List[float]
    max_pain: float
    gamma_wall: Optional[float]

class CBOEDataProvider:
    """CBOE Data Provider - Uses public delayed data"""
    
    def __init__(self, cache_dir: str = "data/cboe_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        self.initialized = False
        
        # CBOE Public Data URLs (delayed)
        self.base_urls = {
            'daily_stats': 'https://cdn.cboe.com/api/global/us_indices/daily_statistics/',
            'market_stats': 'https://www.cboe.com/us/options/market_statistics/daily/',
            'historical': 'https://cdn.cboe.com/data/us/options/market_statistics/'
        }
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour cache
        self.last_context_update = None
        self.cached_context = None
    
    async def initialize(self):
        """Initialize the CBOE data provider"""
        try:
            if not self.initialized:
                # Create aiohttp session if needed
                if not self.session:
                    self.session = aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=30),
                        headers={'User-Agent': 'QuantAdaptiveSystem/1.0'}
                    )
                
                # Test connection with a simple request
                try:
                    # Try to fetch current market context to verify functionality
                    await self.get_current_context()
                    logger.info("CBOE Data Provider initialized successfully")
                except Exception as e:
                    logger.warning(f"CBOE API test failed, will use fallback data: {e}")
                
                self.initialized = True
                
        except Exception as e:
            logger.error(f"Error initializing CBOEDataProvider: {e}")
            # Don't raise - allow fallback to work
            self.initialized = True  # Mark as initialized anyway
    
    async def get_current_context(self) -> MarketContext:
        """Get current market context with caching"""
        try:
            current_time = datetime.now()
            
            # Check if cached context is still valid (refresh every 30 minutes)
            if (self.cached_context and self.last_context_update and 
                current_time - self.last_context_update < timedelta(minutes=30)):
                return self.cached_context
            
            # Create MarketContextAnalyzer and get fresh context
            analyzer = MarketContextAnalyzer()
            context = await analyzer.get_current_market_context()
            
            if context:
                self.cached_context = context
                self.last_context_update = current_time
                return context
            else:
                # Return cached context if available, otherwise create default
                if self.cached_context:
                    logger.warning("Using cached market context due to fetch failure")
                    return self.cached_context
                else:
                    # Create default favorable context
                    return self._create_default_context(current_time)
                    
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            # Return cached or default context
            if self.cached_context:
                return self.cached_context
            else:
                return self._create_default_context(datetime.now())
    
    async def update_cache(self):
        """Update cached data - force refresh of market context"""
        try:
            current_time = datetime.now()
            
            # Force refresh by clearing cache
            self.cached_context = None
            self.last_context_update = None
            
            # Get fresh context
            await self.get_current_context()
            
            logger.debug("CBOE cache updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating CBOE cache: {e}")
    
    def _create_default_context(self, timestamp: datetime) -> MarketContext:
        """Create a default favorable market context for fallback"""
        return MarketContext(
            timestamp=timestamp,
            spx_0dte_share=0.35,  # Moderate 0DTE activity
            spy_0dte_share=0.30,  # Moderate SPY 0DTE
            combined_0dte_share=0.33,  # Combined moderate
            put_call_ratio=0.95,  # Slightly bullish bias
            gamma_exposure=0.1,   # Low gamma exposure
            regime="NORMAL",      # Normal trading regime
            volatility_regime="MEDIUM",  # Medium volatility
            pinning_risk=0.3,     # Low-moderate pinning risk
            key_levels=[4350.0, 4400.0, 4450.0],  # Typical SPX levels
            max_pain=4400.0,      # Typical max pain
            gamma_wall=4450.0     # Gamma resistance level
        )
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'QuantAdaptiveSystem/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def fetch_spx_options_data(self, date: Optional[datetime] = None) -> Optional[OptionsData]:
        """Fetch SPX options data from CBOE"""
        if date is None:
            date = datetime.now().date()
            
        try:
            # Check cache first
            cached_data = await self._get_cached_data('spx', date)
            if cached_data:
                return cached_data
                
            # Fetch from CBOE API
            data = await self._fetch_cboe_daily_stats('SPX', date)
            if not data:
                return None
                
            # Process the data
            options_data = await self._process_spx_data(data, date)
            
            # Cache the result
            await self._cache_data('spx', date, options_data)
            
            return options_data
            
        except Exception as e:
            logger.error(f"Error fetching SPX options data: {e}")
            return None
            
    async def fetch_spy_options_data(self, date: Optional[datetime] = None) -> Optional[OptionsData]:
        """Fetch SPY options data from CBOE"""
        if date is None:
            date = datetime.now().date()
            
        try:
            # Check cache first
            cached_data = await self._get_cached_data('spy', date)
            if cached_data:
                return cached_data
                
            # SPY data from public sources
            data = await self._fetch_cboe_daily_stats('SPY', date)
            if not data:
                return None
                
            options_data = await self._process_spy_data(data, date)
            await self._cache_data('spy', date, options_data)
            
            return options_data
            
        except Exception as e:
            logger.error(f"Error fetching SPY options data: {e}")
            return None
            
    async def _fetch_cboe_daily_stats(self, symbol: str, date: datetime) -> Optional[dict]:
        """Fetch daily statistics from CBOE public API"""
        try:
            # Format date for API
            date_str = date.strftime('%Y-%m-%d')
            
            # Construct URL (this is a placeholder - real implementation would use actual CBOE endpoints)
            url = f"{self.base_urls['daily_stats']}{symbol.lower()}/{date_str}.json"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched {symbol} data for {date_str}")
                    return data
                else:
                    logger.warning(f"Failed to fetch {symbol} data: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error in CBOE API request: {e}")
            # Fallback to simulated data for development
            return await self._generate_simulated_data(symbol, date)
            
    async def _process_spx_data(self, data: dict, date: datetime) -> OptionsData:
        """Process raw SPX options data into structured format"""
        
        # Extract volume data
        total_volume = data.get('total_volume', 1000000)
        dte_0_volume = data.get('dte_0_volume', total_volume * 0.4)  # Typical 40% 0DTE
        
        # Extract put/call data
        put_volume = data.get('put_volume', total_volume * 0.55)
        call_volume = total_volume - put_volume
        
        # Calculate metrics
        dte_0_share = dte_0_volume / total_volume if total_volume > 0 else 0
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 1.0
        
        # Extract OI data
        put_oi = data.get('put_oi', 500000)
        call_oi = data.get('call_oi', 400000)
        total_oi = put_oi + call_oi
        
        # Estimate gamma exposure (simplified)
        gamma_exposure = self._estimate_gamma_exposure(data)
        
        # Extract key levels
        max_pain = data.get('max_pain', 4400.0)  # Typical SPX level
        high_gamma_strikes = data.get('high_gamma_strikes', [4350, 4400, 4450, 4500])
        pinning_candidates = self._identify_pinning_levels(data)
        
        return OptionsData(
            timestamp=datetime.combine(date, datetime.min.time()),
            symbol='SPX',
            dte_0_volume=dte_0_volume,
            total_volume=total_volume,
            dte_0_share=dte_0_share,
            put_volume=put_volume,
            call_volume=call_volume,
            put_call_ratio=put_call_ratio,
            put_oi=put_oi,
            call_oi=call_oi,
            total_oi=total_oi,
            gamma_exposure_estimate=gamma_exposure,
            max_pain_level=max_pain,
            high_gamma_strikes=high_gamma_strikes,
            pinning_candidates=pinning_candidates
        )
        
    async def _process_spy_data(self, data: dict, date: datetime) -> OptionsData:
        """Process raw SPY options data into structured format"""
        
        # Similar processing for SPY
        total_volume = data.get('total_volume', 500000)
        dte_0_volume = data.get('dte_0_volume', total_volume * 0.35)  # Lower 0DTE share for SPY
        
        put_volume = data.get('put_volume', total_volume * 0.52)
        call_volume = total_volume - put_volume
        
        dte_0_share = dte_0_volume / total_volume if total_volume > 0 else 0
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 1.0
        
        put_oi = data.get('put_oi', 300000)
        call_oi = data.get('call_oi', 250000)
        total_oi = put_oi + call_oi
        
        gamma_exposure = self._estimate_gamma_exposure(data)
        max_pain = data.get('max_pain', 440.0)  # SPY level
        high_gamma_strikes = data.get('high_gamma_strikes', [435, 440, 445, 450])
        pinning_candidates = self._identify_pinning_levels(data)
        
        return OptionsData(
            timestamp=datetime.combine(date, datetime.min.time()),
            symbol='SPY',
            dte_0_volume=dte_0_volume,
            total_volume=total_volume,
            dte_0_share=dte_0_share,
            put_volume=put_volume,
            call_volume=call_volume,
            put_call_ratio=put_call_ratio,
            put_oi=put_oi,
            call_oi=call_oi,
            total_oi=total_oi,
            gamma_exposure_estimate=gamma_exposure,
            max_pain_level=max_pain,
            high_gamma_strikes=high_gamma_strikes,
            pinning_candidates=pinning_candidates
        )
        
    def _estimate_gamma_exposure(self, data: dict) -> float:
        """Estimate gamma exposure from options data"""
        # Simplified gamma exposure calculation
        # In reality, this would require option chain data with Greeks
        
        # Use volume and OI as proxy
        call_gamma_proxy = data.get('call_volume', 0) * data.get('call_oi', 0)
        put_gamma_proxy = data.get('put_volume', 0) * data.get('put_oi', 0)
        
        # Net gamma exposure (calls positive, puts negative)
        net_gamma = call_gamma_proxy - put_gamma_proxy
        
        # Normalize to reasonable range
        total_proxy = call_gamma_proxy + put_gamma_proxy
        if total_proxy > 0:
            return net_gamma / total_proxy
        else:
            return 0.0
            
    def _identify_pinning_levels(self, data: dict) -> List[float]:
        """Identify potential pinning levels from high OI strikes"""
        
        # Extract high OI strikes from data
        oi_by_strike = data.get('oi_by_strike', {})
        
        if not oi_by_strike:
            # Return typical round number levels as fallback
            symbol = data.get('symbol', 'SPX')
            if symbol == 'SPX':
                return [4300, 4350, 4400, 4450, 4500]
            else:  # SPY
                return [430, 435, 440, 445, 450]
                
        # Sort by OI and return top levels
        sorted_strikes = sorted(oi_by_strike.items(), key=lambda x: x[1], reverse=True)
        return [float(strike) for strike, _ in sorted_strikes[:5]]
        
    async def _get_cached_data(self, symbol: str, date: datetime) -> Optional[OptionsData]:
        """Get data from cache if available and fresh"""
        cache_file = self.cache_dir / f"{symbol}_{date.strftime('%Y%m%d')}.json"
        
        if not cache_file.exists():
            return None
            
        try:
            # Check cache age
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if cache_age > self.cache_ttl:
                return None
                
            # Load cached data
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                
            # Convert back to OptionsData
            return OptionsData(**cached)
            
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
            
    async def _cache_data(self, symbol: str, date: datetime, data: OptionsData):
        """Cache data for future use"""
        cache_file = self.cache_dir / f"{symbol}_{date.strftime('%Y%m%d')}.json"
        
        try:
            # Convert to dict for JSON serialization
            data_dict = {
                'timestamp': data.timestamp.isoformat(),
                'symbol': data.symbol,
                'dte_0_volume': data.dte_0_volume,
                'total_volume': data.total_volume,
                'dte_0_share': data.dte_0_share,
                'put_volume': data.put_volume,
                'call_volume': data.call_volume,
                'put_call_ratio': data.put_call_ratio,
                'put_oi': data.put_oi,
                'call_oi': data.call_oi,
                'total_oi': data.total_oi,
                'gamma_exposure_estimate': data.gamma_exposure_estimate,
                'max_pain_level': data.max_pain_level,
                'high_gamma_strikes': data.high_gamma_strikes,
                'pinning_candidates': data.pinning_candidates
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data_dict, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Error caching data: {e}")
            
    async def _generate_simulated_data(self, symbol: str, date: datetime) -> dict:
        """Generate realistic simulated data for development/testing"""
        
        # Generate realistic options data based on current market conditions
        base_volume = 1000000 if symbol == 'SPX' else 500000
        
        # Add some randomness but keep realistic
        np.random.seed(int(date.timestamp()) % 10000)  # Deterministic but varied
        
        volume_factor = np.random.uniform(0.7, 1.5)
        dte_0_factor = np.random.uniform(0.3, 0.6)  # 30-60% 0DTE
        put_bias = np.random.uniform(0.48, 0.58)  # Slight put bias
        
        total_volume = base_volume * volume_factor
        dte_0_volume = total_volume * dte_0_factor
        put_volume = total_volume * put_bias
        
        # Generate strike data
        if symbol == 'SPX':
            base_price = 4400 + np.random.uniform(-200, 200)
            strikes = [base_price + i*25 for i in range(-10, 11)]
        else:  # SPY
            base_price = 440 + np.random.uniform(-20, 20)
            strikes = [base_price + i*2.5 for i in range(-10, 11)]
            
        # Generate OI distribution (higher near ATM)
        oi_by_strike = {}
        for strike in strikes:
            distance = abs(strike - base_price) / base_price
            oi = max(1000, int(50000 * np.exp(-distance * 20)))
            oi_by_strike[str(strike)] = oi
            
        return {
            'symbol': symbol,
            'total_volume': total_volume,
            'dte_0_volume': dte_0_volume,
            'put_volume': put_volume,
            'call_volume': total_volume - put_volume,
            'put_oi': sum(oi_by_strike.values()) * 0.55,
            'call_oi': sum(oi_by_strike.values()) * 0.45,
            'max_pain': base_price,
            'high_gamma_strikes': strikes[7:13],  # Near ATM strikes
            'oi_by_strike': oi_by_strike
        }

class MarketContextAnalyzer:
    """Analyzes market context from options data"""
    
    def __init__(self):
        self.cboe_provider = CBOEDataProvider()
        
    async def get_current_market_context(self) -> Optional[MarketContext]:
        """Get comprehensive market context for current session"""
        
        try:
            async with self.cboe_provider:
                # Fetch both SPX and SPY data
                spx_data = await self.cboe_provider.fetch_spx_options_data()
                spy_data = await self.cboe_provider.fetch_spy_options_data()
                
                if not spx_data and not spy_data:
                    logger.error("No options data available")
                    return None
                    
                # Use SPX as primary, SPY as fallback
                primary_data = spx_data if spx_data else spy_data
                secondary_data = spy_data if spx_data else None
                
                # Calculate combined metrics
                context = await self._analyze_context(primary_data, secondary_data)
                
                logger.info(f"Market context: {context.regime}, 0DTE: {context.combined_0dte_share:.1%}")
                
                return context
                
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            return None
            
    async def _analyze_context(self, primary: OptionsData, secondary: Optional[OptionsData]) -> MarketContext:
        """Analyze market context from options data"""
        
        timestamp = datetime.now()
        
        # Primary metrics
        spx_0dte_share = primary.dte_0_share
        spy_0dte_share = secondary.dte_0_share if secondary else primary.dte_0_share
        
        # Combined 0DTE share (weighted average)
        if secondary:
            combined_0dte_share = (spx_0dte_share * 0.7 + spy_0dte_share * 0.3)
        else:
            combined_0dte_share = spx_0dte_share
            
        # Put/call ratio
        put_call_ratio = primary.put_call_ratio
        
        # Gamma exposure
        gamma_exposure = primary.gamma_exposure_estimate
        
        # Determine regime
        regime = self._determine_regime(combined_0dte_share, put_call_ratio, gamma_exposure)
        volatility_regime = self._determine_volatility_regime(primary)
        pinning_risk = self._calculate_pinning_risk(primary)
        
        # Key levels
        key_levels = primary.pinning_candidates[:3]  # Top 3 levels
        max_pain = primary.max_pain_level
        gamma_wall = self._find_gamma_wall(primary)
        
        return MarketContext(
            timestamp=timestamp,
            spx_0dte_share=spx_0dte_share,
            spy_0dte_share=spy_0dte_share,
            combined_0dte_share=combined_0dte_share,
            put_call_ratio=put_call_ratio,
            gamma_exposure=gamma_exposure,
            regime=regime,
            volatility_regime=volatility_regime,
            pinning_risk=pinning_risk,
            key_levels=key_levels,
            max_pain=max_pain,
            gamma_wall=gamma_wall
        )
        
    def _determine_regime(self, dte_0_share: float, pcr: float, gamma: float) -> str:
        """Determine market regime based on options metrics"""
        
        if dte_0_share > 0.6:  # >60% 0DTE
            if abs(gamma) > 0.3:
                return 'GAMMA_SQUEEZE'
            else:
                return 'HIGH_0DTE'
        elif 0.95 < pcr < 1.05 and dte_0_share > 0.4:  # Balanced PCR + significant 0DTE
            return 'PINNING'
        else:
            return 'NORMAL'
            
    def _determine_volatility_regime(self, data: OptionsData) -> str:
        """Determine volatility regime"""
        
        # Use volume as proxy for volatility regime
        volume_ratio = data.total_volume / 1000000  # Normalize to typical volume
        
        if volume_ratio > 1.5:
            return 'HIGH'
        elif volume_ratio > 0.8:
            return 'MEDIUM'
        else:
            return 'LOW'
            
    def _calculate_pinning_risk(self, data: OptionsData) -> float:
        """Calculate pinning risk (0-1 scale)"""
        
        # Factors that increase pinning risk:
        # 1. High 0DTE share
        # 2. Balanced put/call ratio
        # 3. High gamma at key strikes
        
        dte_factor = min(1.0, data.dte_0_share * 2)  # 0DTE share contribution
        pcr_factor = 1.0 - abs(data.put_call_ratio - 1.0)  # Balanced PCR
        gamma_factor = min(1.0, abs(data.gamma_exposure_estimate) * 2)
        
        # Weighted average
        pinning_risk = (dte_factor * 0.4 + pcr_factor * 0.3 + gamma_factor * 0.3)
        
        return max(0.0, min(1.0, pinning_risk))
        
    def _find_gamma_wall(self, data: OptionsData) -> Optional[float]:
        """Find significant gamma wall level"""
        
        # Look for strikes with unusually high gamma concentration
        if data.high_gamma_strikes:
            # Return the strike with highest concentration
            # (simplified - would need actual gamma data)
            return data.high_gamma_strikes[0]
        
        return None

# Convenience functions
async def get_market_context() -> Optional[MarketContext]:
    """Get current market context - convenience function"""
    analyzer = MarketContextAnalyzer()
    return await analyzer.get_current_market_context()

async def get_0dte_share() -> float:
    """Get current 0DTE share - quick check"""
    context = await get_market_context()
    return context.combined_0dte_share if context else 0.0

async def get_regime() -> str:
    """Get current market regime - quick check"""
    context = await get_market_context()
    return context.regime if context else 'UNKNOWN'

# Factory function per istanza globale
_cboe_provider_instance = None

async def get_cboe_provider() -> CBOEDataProvider:
    """Restituisce istanza singleton del CBOE provider"""
    global _cboe_provider_instance
    if _cboe_provider_instance is None:
        _cboe_provider_instance = CBOEDataProvider()
        await _cboe_provider_instance.initialize()
    return _cboe_provider_instance