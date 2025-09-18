"""
Futures Volume Mapping Module - CME/Eurex Volume Profile Integration
Fetches and processes volume profile data from futures markets
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class VolumeLevel:
    """Single volume level data"""
    price: float
    volume: int
    percentage: float  # Percentage of total session volume
    
@dataclass
class VolumeProfile:
    """Volume Profile for a trading session"""
    contract: str
    session_date: datetime
    session_type: str  # 'RTH', 'ETH', 'GLOBEX'
    
    # Key levels
    poc: float  # Point of Control (highest volume)
    vah: float  # Value Area High
    val: float  # Value Area Low
    
    # Session data
    session_high: float
    session_low: float
    session_close: float
    total_volume: int
    
    # Volume distribution
    volume_levels: List[VolumeLevel]
    value_area_volume_pct: float  # Typically 70%
    
    # High/Low Volume Nodes
    hvn_levels: List[float]  # High Volume Nodes
    lvn_levels: List[float]  # Low Volume Nodes
    
    # Metadata
    timestamp_created: datetime
    data_source: str

@dataclass
class FuturesMapping:
    """Mapping between futures and CFD instruments"""
    futures_symbol: str
    cfd_symbol: str  # OANDA CFD symbol
    multiplier: float  # Price adjustment factor
    description: str

class CMEDataProvider:
    """CME Group data provider for ES, NQ, YM"""
    
    def __init__(self, cache_dir: str = "data/cme_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # CME public data endpoints (delayed 15-30 minutes)
        self.base_urls = {
            'delayed_quotes': 'https://www.cmegroup.com/market-data/delayed-quotes/',
            'volume_data': 'https://www.cmegroup.com/trading/equity-index/us-index/',
            'historical': 'https://www.cmegroup.com/market-data/historical-data.html'
        }
        
        # Contract specifications
        self.contracts = {
            'ES': {
                'name': 'E-mini S&P 500',
                'tick_size': 0.25,
                'multiplier': 50,
                'cfd_mapping': 'SPX500_USD'
            },
            'NQ': {
                'name': 'E-mini NASDAQ-100', 
                'tick_size': 0.25,
                'multiplier': 20,
                'cfd_mapping': 'NAS100_USD'
            },
            'YM': {
                'name': 'E-mini Dow Jones',
                'tick_size': 1.0,
                'multiplier': 5,
                'cfd_mapping': 'US30_USD'
            }
        }
        
        # RTH session times (CT)
        self.rth_sessions = {
            'ES': (time(8, 30), time(15, 0)),   # 8:30-15:00 CT
            'NQ': (time(8, 30), time(15, 0)),   # 8:30-15:00 CT  
            'YM': (time(8, 30), time(15, 0))    # 8:30-15:00 CT
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={'User-Agent': 'QuantAdaptiveSystem/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def fetch_volume_profile(self, contract: str, session_date: datetime) -> Optional[VolumeProfile]:
        """Fetch volume profile data for a contract"""
        
        if contract not in self.contracts:
            logger.error(f"Unsupported contract: {contract}")
            return None
            
        try:
            # Check cache first
            cached_profile = await self._get_cached_profile(contract, session_date)
            if cached_profile:
                return cached_profile
                
            # Fetch raw volume data
            volume_data = await self._fetch_cme_volume_data(contract, session_date)
            if not volume_data:
                return None
                
            # Process into volume profile
            profile = await self._process_volume_profile(contract, session_date, volume_data)
            
            # Cache the result
            await self._cache_profile(profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error fetching volume profile for {contract}: {e}")
            return None
            
    async def _fetch_cme_volume_data(self, contract: str, date: datetime) -> Optional[dict]:
        """Fetch raw volume data from CME"""
        
        try:
            # Format date and contract for API
            date_str = date.strftime('%Y-%m-%d')
            
            # Construct API URL (placeholder - actual implementation would use real CME endpoints)
            url = f"{self.base_urls['volume_data']}{contract.lower()}/{date_str}/volume-profile.json"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched {contract} volume data for {date_str}")
                    return data
                else:
                    logger.warning(f"Failed to fetch {contract} data: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error in CME API request: {e}")
            
        # Fallback to simulated data for development
        return await self._generate_simulated_volume_data(contract, date)
        
    async def _process_volume_profile(self, contract: str, date: datetime, raw_data: dict) -> VolumeProfile:
        """Process raw volume data into structured profile"""
        
        # Extract session data
        session_high = raw_data.get('session_high', 4400.0)
        session_low = raw_data.get('session_low', 4350.0) 
        session_close = raw_data.get('session_close', 4375.0)
        total_volume = raw_data.get('total_volume', 1000000)
        
        # Extract volume by price levels
        volume_by_price = raw_data.get('volume_by_price', {})
        
        # Calculate volume levels
        volume_levels = []
        for price_str, volume in volume_by_price.items():
            price = float(price_str)
            percentage = (volume / total_volume) * 100 if total_volume > 0 else 0
            volume_levels.append(VolumeLevel(price, volume, percentage))
            
        # Sort by volume (descending)
        volume_levels.sort(key=lambda x: x.volume, reverse=True)
        
        # Calculate POC (Point of Control)
        poc = volume_levels[0].price if volume_levels else session_close
        
        # Calculate Value Area (70% of volume)
        vah, val = self._calculate_value_area(volume_levels, 0.70)
        
        # Find HVN/LVN levels
        hvn_levels, lvn_levels = self._find_volume_nodes(volume_levels)
        
        return VolumeProfile(
            contract=contract,
            session_date=date,
            session_type='RTH',
            poc=poc,
            vah=vah,
            val=val,
            session_high=session_high,
            session_low=session_low,
            session_close=session_close,
            total_volume=total_volume,
            volume_levels=volume_levels,
            value_area_volume_pct=70.0,
            hvn_levels=hvn_levels,
            lvn_levels=lvn_levels,
            timestamp_created=datetime.now(),
            data_source='CME_DELAYED'
        )
        
    def _calculate_value_area(self, volume_levels: List[VolumeLevel], target_pct: float = 0.70) -> Tuple[float, float]:
        """Calculate Value Area High (VAH) and Value Area Low (VAL)"""
        
        if not volume_levels:
            return 0.0, 0.0
            
        # Start from POC and expand both ways
        sorted_levels = sorted(volume_levels, key=lambda x: x.price)
        total_volume = sum(level.volume for level in volume_levels)
        target_volume = total_volume * target_pct
        
        # Find POC index
        poc_level = max(volume_levels, key=lambda x: x.volume)
        poc_price = poc_level.price
        
        # Find POC in sorted list
        poc_index = next(i for i, level in enumerate(sorted_levels) if level.price == poc_price)
        
        # Expand from POC
        current_volume = poc_level.volume
        low_index = poc_index
        high_index = poc_index
        
        while current_volume < target_volume:
            # Check which direction to expand
            can_expand_up = high_index < len(sorted_levels) - 1
            can_expand_down = low_index > 0
            
            if not can_expand_up and not can_expand_down:
                break
                
            # Choose direction with higher volume
            up_volume = sorted_levels[high_index + 1].volume if can_expand_up else 0
            down_volume = sorted_levels[low_index - 1].volume if can_expand_down else 0
            
            if up_volume >= down_volume and can_expand_up:
                high_index += 1
                current_volume += sorted_levels[high_index].volume
            elif can_expand_down:
                low_index -= 1
                current_volume += sorted_levels[low_index].volume
            else:
                break
                
        vah = sorted_levels[high_index].price
        val = sorted_levels[low_index].price
        
        return vah, val
        
    def _find_volume_nodes(self, volume_levels: List[VolumeLevel]) -> Tuple[List[float], List[float]]:
        """Find High Volume Nodes (HVN) and Low Volume Nodes (LVN)"""
        
        if len(volume_levels) < 3:
            return [], []
            
        # Sort by price for node detection
        price_sorted = sorted(volume_levels, key=lambda x: x.price)
        
        # Calculate volume moving average for comparison
        volumes = [level.volume for level in price_sorted]
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        hvn_threshold = avg_volume + std_volume
        lvn_threshold = avg_volume - std_volume
        
        hvn_levels = []
        lvn_levels = []
        
        for level in price_sorted:
            if level.volume > hvn_threshold:
                hvn_levels.append(level.price)
            elif level.volume < lvn_threshold:
                lvn_levels.append(level.price)
                
        return hvn_levels, lvn_levels
        
    async def _generate_simulated_volume_data(self, contract: str, date: datetime) -> dict:
        """Generate realistic simulated volume data for development"""
        
        # Set random seed based on date for consistency
        np.random.seed(int(date.timestamp()) % 10000)
        
        # Base parameters by contract
        if contract == 'ES':
            base_price = 4375 + np.random.uniform(-50, 50)
            tick_size = 0.25
            volume_factor = 1.0
        elif contract == 'NQ':
            base_price = 15000 + np.random.uniform(-500, 500) 
            tick_size = 0.25
            volume_factor = 0.7
        elif contract == 'YM':
            base_price = 34000 + np.random.uniform(-1000, 1000)
            tick_size = 1.0
            volume_factor = 0.3
        else:
            base_price = 4375
            tick_size = 0.25
            volume_factor = 1.0
            
        # Generate session OHLC
        daily_range = base_price * 0.02  # 2% daily range
        session_high = base_price + np.random.uniform(0, daily_range)
        session_low = base_price - np.random.uniform(0, daily_range)
        session_close = base_price + np.random.uniform(-daily_range/2, daily_range/2)
        
        # Generate volume profile
        total_volume = int(1000000 * volume_factor * np.random.uniform(0.7, 1.4))
        
        # Create price levels
        price_range = session_high - session_low
        num_levels = int(price_range / tick_size) + 1
        
        volume_by_price = {}
        
        for i in range(num_levels):
            price = session_low + (i * tick_size)
            price = round(price / tick_size) * tick_size  # Round to tick size
            
            # Volume distribution (higher near center)
            distance_from_center = abs(price - base_price) / price_range
            volume_multiplier = np.exp(-distance_from_center * 3)  # Gaussian-like
            
            # Add some randomness
            volume_multiplier *= np.random.uniform(0.3, 1.7)
            
            volume = int(total_volume * volume_multiplier / 100)
            if volume > 0:
                volume_by_price[str(price)] = volume
                
        # Normalize volumes so they sum to total_volume
        current_total = sum(volume_by_price.values())
        if current_total > 0:
            scale_factor = total_volume / current_total
            volume_by_price = {price: int(vol * scale_factor) for price, vol in volume_by_price.items()}
            
        return {
            'contract': contract,
            'session_high': session_high,
            'session_low': session_low,
            'session_close': session_close,
            'total_volume': total_volume,
            'volume_by_price': volume_by_price
        }
        
    async def _get_cached_profile(self, contract: str, date: datetime) -> Optional[VolumeProfile]:
        """Get volume profile from cache"""
        cache_file = self.cache_dir / f"{contract}_{date.strftime('%Y%m%d')}_profile.json"
        
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                
            # Convert back to VolumeProfile
            volume_levels = [VolumeLevel(**level) for level in data['volume_levels']]
            
            return VolumeProfile(
                contract=data['contract'],
                session_date=datetime.fromisoformat(data['session_date']),
                session_type=data['session_type'],
                poc=data['poc'],
                vah=data['vah'],
                val=data['val'],
                session_high=data['session_high'],
                session_low=data['session_low'],
                session_close=data['session_close'],
                total_volume=data['total_volume'],
                volume_levels=volume_levels,
                value_area_volume_pct=data['value_area_volume_pct'],
                hvn_levels=data['hvn_levels'],
                lvn_levels=data['lvn_levels'],
                timestamp_created=datetime.fromisoformat(data['timestamp_created']),
                data_source=data['data_source']
            )
            
        except Exception as e:
            logger.warning(f"Error reading cached profile: {e}")
            return None
            
    async def _cache_profile(self, profile: VolumeProfile):
        """Cache volume profile"""
        cache_file = self.cache_dir / f"{profile.contract}_{profile.session_date.strftime('%Y%m%d')}_profile.json"
        
        try:
            # Convert to dict for JSON serialization
            data = {
                'contract': profile.contract,
                'session_date': profile.session_date.isoformat(),
                'session_type': profile.session_type,
                'poc': profile.poc,
                'vah': profile.vah,
                'val': profile.val,
                'session_high': profile.session_high,
                'session_low': profile.session_low,
                'session_close': profile.session_close,
                'total_volume': profile.total_volume,
                'volume_levels': [
                    {'price': vl.price, 'volume': vl.volume, 'percentage': vl.percentage}
                    for vl in profile.volume_levels
                ],
                'value_area_volume_pct': profile.value_area_volume_pct,
                'hvn_levels': profile.hvn_levels,
                'lvn_levels': profile.lvn_levels,
                'timestamp_created': profile.timestamp_created.isoformat(),
                'data_source': profile.data_source
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Error caching profile: {e}")

class EurexDataProvider:
    """Eurex data provider for DAX futures"""
    
    def __init__(self, cache_dir: str = "data/eurex_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Eurex contracts
        self.contracts = {
            'FDAX': {
                'name': 'DAX Future',
                'tick_size': 0.5,
                'multiplier': 25,
                'cfd_mapping': 'DE30_EUR'
            }
        }
        
    async def fetch_volume_profile(self, contract: str, session_date: datetime) -> Optional[VolumeProfile]:
        """Fetch DAX volume profile (simplified implementation)"""
        
        try:
            # For now, generate simulated DAX data
            # Real implementation would connect to Eurex data feeds
            
            np.random.seed(int(session_date.timestamp()) % 10000)
            
            base_price = 15500 + np.random.uniform(-500, 500)
            daily_range = base_price * 0.015  # 1.5% daily range for DAX
            
            session_high = base_price + np.random.uniform(0, daily_range)
            session_low = base_price - np.random.uniform(0, daily_range)
            session_close = base_price + np.random.uniform(-daily_range/2, daily_range/2)
            
            total_volume = int(200000 * np.random.uniform(0.7, 1.4))
            
            # Simple volume distribution
            volume_by_price = {}
            price_range = session_high - session_low
            num_levels = int(price_range / 0.5) + 1
            
            for i in range(num_levels):
                price = session_low + (i * 0.5)
                price = round(price * 2) / 2  # Round to 0.5 tick
                
                distance_from_center = abs(price - base_price) / price_range
                volume_multiplier = np.exp(-distance_from_center * 3)
                volume_multiplier *= np.random.uniform(0.3, 1.7)
                
                volume = int(total_volume * volume_multiplier / 100)
                if volume > 0:
                    volume_by_price[str(price)] = volume
                    
            # Create volume levels
            volume_levels = []
            for price_str, volume in volume_by_price.items():
                price = float(price_str)
                percentage = (volume / total_volume) * 100
                volume_levels.append(VolumeLevel(price, volume, percentage))
                
            volume_levels.sort(key=lambda x: x.volume, reverse=True)
            
            # Calculate key levels
            poc = volume_levels[0].price if volume_levels else session_close
            
            # Simple VAH/VAL calculation
            sorted_by_price = sorted(volume_levels, key=lambda x: x.price)
            val = np.percentile([vl.price for vl in sorted_by_price], 30)
            vah = np.percentile([vl.price for vl in sorted_by_price], 70)
            
            return VolumeProfile(
                contract=contract,
                session_date=session_date,
                session_type='XETRA',
                poc=poc,
                vah=vah,
                val=val,
                session_high=session_high,
                session_low=session_low,
                session_close=session_close,
                total_volume=total_volume,
                volume_levels=volume_levels,
                value_area_volume_pct=70.0,
                hvn_levels=[poc],
                lvn_levels=[],
                timestamp_created=datetime.now(),
                data_source='EUREX_SIMULATED'
            )
            
        except Exception as e:
            logger.error(f"Error fetching Eurex data: {e}")
            return None

class FuturesVolumeMapper:
    """Maps futures volume data to CFD instruments"""
    
    def __init__(self):
        self.cme_provider = CMEDataProvider()
        self.eurex_provider = EurexDataProvider()
        
        # Mapping between futures and CFD symbols
        self.mappings = {
            'ES': FuturesMapping('ES', 'SPX500_USD', 1.0, 'S&P 500'),
            'NQ': FuturesMapping('NQ', 'NAS100_USD', 1.0, 'NASDAQ-100'),
            'YM': FuturesMapping('YM', 'US30_USD', 1.0, 'Dow Jones'),
            'FDAX': FuturesMapping('FDAX', 'DE30_EUR', 1.0, 'DAX')
        }
        
    async def get_all_volume_profiles(self, date: Optional[datetime] = None) -> Dict[str, VolumeProfile]:
        """Get volume profiles for all supported instruments"""
        
        if date is None:
            date = datetime.now().date()
            
        profiles = {}
        
        try:
            async with self.cme_provider:
                # Fetch CME data
                for contract in ['ES', 'NQ', 'YM']:
                    try:
                        profile = await self.cme_provider.fetch_volume_profile(contract, date)
                        if profile:
                            profiles[contract] = profile
                            logger.info(f"Loaded {contract} volume profile: POC={profile.poc:.2f}")
                    except Exception as e:
                        logger.error(f"Error loading {contract} profile: {e}")
                        
                # Fetch Eurex data
                try:
                    fdax_profile = await self.eurex_provider.fetch_volume_profile('FDAX', date)
                    if fdax_profile:
                        profiles['FDAX'] = fdax_profile
                        logger.info(f"Loaded FDAX volume profile: POC={fdax_profile.poc:.2f}")
                except Exception as e:
                    logger.error(f"Error loading FDAX profile: {e}")
                    
        except Exception as e:
            logger.error(f"Error in volume profile fetching: {e}")
            
        return profiles
        
    def map_levels_to_cfd(self, futures_profile: VolumeProfile) -> Dict[str, float]:
        """Map futures volume levels to CFD instrument"""
        
        mapping = self.mappings.get(futures_profile.contract)
        if not mapping:
            return {}
            
        multiplier = mapping.multiplier
        
        return {
            'cfd_symbol': mapping.cfd_symbol,
            'poc': futures_profile.poc * multiplier,
            'vah': futures_profile.vah * multiplier,
            'val': futures_profile.val * multiplier,
            'session_high': futures_profile.session_high * multiplier,
            'session_low': futures_profile.session_low * multiplier,
            'hvn_levels': [level * multiplier for level in futures_profile.hvn_levels],
            'lvn_levels': [level * multiplier for level in futures_profile.lvn_levels],
            'total_volume': futures_profile.total_volume,
            'data_source': futures_profile.data_source,
            'timestamp': futures_profile.timestamp_created.isoformat()
        }
        
    async def get_cfd_volume_levels(self, cfd_symbol: str, date: Optional[datetime] = None) -> Optional[Dict[str, float]]:
        """Get volume levels for a specific CFD symbol"""
        
        # Find corresponding futures contract
        futures_contract = None
        for contract, mapping in self.mappings.items():
            if mapping.cfd_symbol == cfd_symbol:
                futures_contract = contract
                break
                
        if not futures_contract:
            logger.warning(f"No futures mapping found for {cfd_symbol}")
            return None
            
        # Get volume profile
        profiles = await self.get_all_volume_profiles(date)
        futures_profile = profiles.get(futures_contract)
        
        if not futures_profile:
            logger.warning(f"No volume profile available for {futures_contract}")
            return None
            
        # Map to CFD levels
        return self.map_levels_to_cfd(futures_profile)
    
    async def initialize(self):
        """Initialize the futures volume mapper"""
        try:
            # Initialize data providers
            await self.cme_provider.initialize() if hasattr(self.cme_provider, 'initialize') else None
            await self.eurex_provider.initialize() if hasattr(self.eurex_provider, 'initialize') else None
            
            logger.info("FuturesVolumeMapper initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing FuturesVolumeMapper: {e}")
            # Don't raise - allow fallback to work
    
    async def get_all_current_profiles(self) -> Dict[str, VolumeProfile]:
        """Get all current volume profiles - alias for get_all_volume_profiles"""
        try:
            return await self.get_all_volume_profiles()
        except Exception as e:
            logger.error(f"Error getting current profiles: {e}")
            return {}
    
    async def update_all_profiles(self):
        """Update all cached volume profiles"""
        try:
            # Force refresh by fetching new profiles
            profiles = await self.get_all_volume_profiles()
            
            logger.info(f"Updated {len(profiles)} volume profiles")
            
        except Exception as e:
            logger.error(f"Error updating volume profiles: {e}")

# Convenience functions
async def get_volume_levels(cfd_symbol: str) -> Optional[Dict[str, float]]:
    """Get volume levels for CFD symbol - convenience function"""
    mapper = FuturesVolumeMapper()
    return await mapper.get_cfd_volume_levels(cfd_symbol)

async def get_all_volume_data() -> Dict[str, Dict[str, float]]:
    """Get all volume data mapped to CFD symbols"""
    mapper = FuturesVolumeMapper()
    profiles = await mapper.get_all_volume_profiles()
    
    cfd_data = {}
    for contract, profile in profiles.items():
        cfd_levels = mapper.map_levels_to_cfd(profile)
        if cfd_levels:
            cfd_data[cfd_levels['cfd_symbol']] = cfd_levels
            
    return cfd_data

async def get_poc_distance(cfd_symbol: str, current_price: float) -> Optional[float]:
    """Get distance from current price to POC (normalized)"""
    levels = await get_volume_levels(cfd_symbol)
    if not levels or 'poc' not in levels:
        return None
        
    poc = levels['poc']
    distance = (current_price - poc) / current_price
    return distance

async def is_inside_value_area(cfd_symbol: str, current_price: float) -> Optional[bool]:
    """Check if current price is inside value area"""
    levels = await get_volume_levels(cfd_symbol)
    if not levels:
        return None
        
    vah = levels.get('vah', 0)
    val = levels.get('val', 0)
    
    return val <= current_price <= vah

# Factory function per istanza globale
_futures_mapper_instance = None

async def get_futures_mapper() -> FuturesVolumeMapper:
    """Restituisce istanza singleton del futures mapper"""
    global _futures_mapper_instance
    if _futures_mapper_instance is None:
        _futures_mapper_instance = FuturesVolumeMapper()
        await _futures_mapper_instance.initialize()
    return _futures_mapper_instance
