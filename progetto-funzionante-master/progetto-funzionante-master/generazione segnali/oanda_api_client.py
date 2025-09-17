"""
OANDA API Client v2.0
Official OANDA v20 REST API Integration
Based on official documentation: https://developer.oanda.com/rest-live-v20/
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os
from decimal import Decimal

# Setup logging
logger = logging.getLogger(__name__)

class OANDAEnvironment(Enum):
    """OANDA Environment Types"""
    PRACTICE = "practice"  # fxPractice
    LIVE = "live"          # fxTrade

class Granularity(Enum):
    """OANDA Candlestick Granularities"""
    S5 = "S5"      # 5 seconds
    S10 = "S10"    # 10 seconds
    S15 = "S15"    # 15 seconds
    S30 = "S30"    # 30 seconds
    M1 = "M1"      # 1 minute
    M2 = "M2"      # 2 minutes
    M4 = "M4"      # 4 minutes
    M5 = "M5"      # 5 minutes
    M10 = "M10"    # 10 minutes
    M15 = "M15"    # 15 minutes
    M30 = "M30"    # 30 minutes
    H1 = "H1"      # 1 hour
    H2 = "H2"      # 2 hours
    H3 = "H3"      # 3 hours
    H4 = "H4"      # 4 hours
    H6 = "H6"      # 6 hours
    H8 = "H8"      # 8 hours
    H12 = "H12"    # 12 hours
    D = "D"        # 1 day
    W = "W"        # 1 week
    M = "M"        # 1 month

class PriceComponent(Enum):
    """Price components for candlestick data"""
    BID = "B"      # Bid prices
    ASK = "A"      # Ask prices
    MID = "M"      # Mid prices (default)

class OANDAAPIError(Exception):
    """Custom exception for OANDA API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code

@dataclass
class OANDAPrice:
    """OANDA Price Data Structure"""
    instrument: str
    time: datetime
    bid: float
    ask: float
    spread: float
    
    @property
    def mid(self) -> float:
        """Calculate mid price"""
        return (self.bid + self.ask) / 2

@dataclass
class OANDACandle:
    """OANDA Candlestick Data Structure"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    complete: bool
    
    @classmethod
    def from_oanda_response(cls, candle_data: Dict[str, Any], price_component: str = "mid") -> 'OANDACandle':
        """Create OANDACandle from OANDA API response"""
        time_str = candle_data["time"]
        # Parse OANDA datetime format (RFC3339)
        time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        
        price_data = candle_data[price_component]
        
        return cls(
            time=time,
            open=float(price_data["o"]),
            high=float(price_data["h"]),
            low=float(price_data["l"]),
            close=float(price_data["c"]),
            volume=int(candle_data.get("volume", 0)),
            complete=bool(candle_data.get("complete", True))
        )

@dataclass
class OANDAInstrument:
    """OANDA Instrument Information"""
    name: str
    type: str
    display_name: str
    pip_location: int
    display_precision: int
    trade_units_precision: int
    minimum_trade_size: float
    maximum_trailing_stop_distance: float
    minimum_trailing_stop_distance: float
    maximum_position_size: float
    maximum_order_units: float
    margin_rate: float

class OANDAClient:
    """
    OANDA v20 REST API Client
    Official implementation following OANDA documentation
    """
    
    # Official OANDA endpoints
    ENDPOINTS = {
        OANDAEnvironment.PRACTICE: "https://api-fxpractice.oanda.com",
        OANDAEnvironment.LIVE: "https://api-fxtrade.oanda.com"
    }
    
    # Rate limits (as per OANDA documentation)
    RATE_LIMIT_REQUESTS_PER_SECOND = 120
    RATE_LIMIT_CONNECTIONS_PER_SECOND = 2
    
    def __init__(self, api_key: str, account_id: str, environment: OANDAEnvironment = OANDAEnvironment.PRACTICE):
        """
        Initialize OANDA Client
        
        Args:
            api_key: OANDA API access token
            account_id: OANDA account ID
            environment: PRACTICE or LIVE
        """
        self.api_key = api_key
        self.account_id = account_id
        self.environment = environment
        self.base_url = self.ENDPOINTS[environment]
        
        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        
        logger.info(f"OANDA Client initialized for {environment.value} environment")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
    
    async def _create_session(self):
        """Create aiohttp session with proper headers"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AI-Trading-System/1.0"
        }
        
        # Connection timeout and limits following OANDA recommendations
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=10,  # Total connection pool size
            limit_per_host=5,  # Connections per host
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=connector
        )
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _rate_limit(self):
        """Implement rate limiting as per OANDA guidelines"""
        current_time = asyncio.get_event_loop().time()
        
        # Reset counter every second
        if current_time - self._last_request_time >= 1.0:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we need to wait
        if self._request_count >= self.RATE_LIMIT_REQUESTS_PER_SECOND:
            wait_time = 1.0 - (current_time - self._last_request_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._last_request_time = asyncio.get_event_loop().time()
        
        self._request_count += 1
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to OANDA API with proper error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary
            
        Raises:
            OANDAAPIError: If API request fails
        """
        if not self.session:
            await self._create_session()
        
        # Apply rate limiting
        await self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            ) as response:
                
                response_text = await response.text()
                
                # Log request for debugging
                logger.debug(f"OANDA {method} {endpoint} -> {response.status}")
                
                if response.status == 200:
                    return json.loads(response_text)
                elif response.status == 401:
                    raise OANDAAPIError("Invalid API key or unauthorized access", response.status, "UNAUTHORIZED")
                elif response.status == 400:
                    raise OANDAAPIError(f"Bad request: {response_text}", response.status, "BAD_REQUEST")
                elif response.status == 404:
                    raise OANDAAPIError(f"Not found: {endpoint}", response.status, "NOT_FOUND")
                elif response.status == 429:
                    raise OANDAAPIError("Rate limit exceeded", response.status, "RATE_LIMIT")
                else:
                    raise OANDAAPIError(f"API error: {response_text}", response.status, "API_ERROR")
                    
        except aiohttp.ClientError as e:
            raise OANDAAPIError(f"Connection error: {str(e)}", None, "CONNECTION_ERROR")
        except json.JSONDecodeError as e:
            raise OANDAAPIError(f"Invalid JSON response: {str(e)}", None, "JSON_ERROR")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        endpoint = f"/v3/accounts/{self.account_id}"
        response = await self._make_request("GET", endpoint)
        return response.get("account", {})
    
    async def get_instruments(self) -> List[OANDAInstrument]:
        """Get available instruments"""
        endpoint = f"/v3/accounts/{self.account_id}/instruments"
        response = await self._make_request("GET", endpoint)
        
        instruments = []
        for instrument_data in response.get("instruments", []):
            instruments.append(OANDAInstrument(
                name=instrument_data["name"],
                type=instrument_data["type"],
                display_name=instrument_data["displayName"],
                pip_location=instrument_data["pipLocation"],
                display_precision=instrument_data["displayPrecision"],
                trade_units_precision=instrument_data["tradeUnitsPrecision"],
                minimum_trade_size=float(instrument_data["minimumTradeSize"]),
                maximum_trailing_stop_distance=float(instrument_data["maximumTrailingStopDistance"]),
                minimum_trailing_stop_distance=float(instrument_data["minimumTrailingStopDistance"]),
                maximum_position_size=float(instrument_data["maximumPositionSize"]),
                maximum_order_units=float(instrument_data["maximumOrderUnits"]),
                margin_rate=float(instrument_data["marginRate"])
            ))
        
        return instruments
    
    async def get_current_prices(self, instruments: List[str]) -> List[OANDAPrice]:
        """
        Get current prices for instruments
        
        Args:
            instruments: List of instrument names (e.g., ["EUR_USD", "GBP_USD"])
            
        Returns:
            List of OANDAPrice objects
        """
        if not instruments:
            return []
        
        # OANDA API accepts comma-separated instruments
        instruments_param = ",".join(instruments)
        
        endpoint = f"/v3/accounts/{self.account_id}/pricing"
        params = {"instruments": instruments_param}
        
        response = await self._make_request("GET", endpoint, params=params)
        
        prices = []
        for price_data in response.get("prices", []):
            # Parse datetime
            time_str = price_data["time"]
            time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            
            # Extract bid/ask prices
            bids = price_data.get("bids", [])
            asks = price_data.get("asks", [])
            
            if bids and asks:
                bid_price = float(bids[0]["price"])
                ask_price = float(asks[0]["price"])
                
                prices.append(OANDAPrice(
                    instrument=price_data["instrument"],
                    time=time,
                    bid=bid_price,
                    ask=ask_price,
                    spread=ask_price - bid_price
                ))
        
        return prices
    
    async def get_candles(
        self,
        instrument: str,
        granularity: Granularity = Granularity.H1,
        count: int = 500,
        price_component: PriceComponent = PriceComponent.MID,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None
    ) -> List[OANDACandle]:
        """
        Get candlestick data for instrument
        
        Args:
            instrument: Instrument name (e.g., "EUR_USD")
            granularity: Time granularity
            count: Number of candles (max 5000)
            price_component: Price component (bid/ask/mid)
            from_time: Start time (optional)
            to_time: End time (optional)
            
        Returns:
            List of OANDACandle objects
        """
        endpoint = f"/v3/instruments/{instrument}/candles"
        
        params = {
            "granularity": granularity.value,
            "price": price_component.value
        }
        
        # Use either count or time range, not both
        if from_time and to_time:
            params["from"] = from_time.isoformat() + "Z"
            params["to"] = to_time.isoformat() + "Z"
        else:
            params["count"] = min(count, 5000)  # OANDA limit
        
        response = await self._make_request("GET", endpoint, params=params)
        
        candles = []
        price_key = {
            PriceComponent.BID: "bid",
            PriceComponent.ASK: "ask", 
            PriceComponent.MID: "mid"
        }[price_component]
        
        for candle_data in response.get("candles", []):
            candles.append(OANDACandle.from_oanda_response(candle_data, price_key))
        
        return candles
    
    def normalize_instrument(self, symbol: str) -> str:
        """
        Normalize instrument symbol to OANDA format
        
        Examples:
            EURUSD -> EUR_USD
            EUR_USD -> EUR_USD (unchanged)
            eurusd -> EUR_USD
            US30 -> US30_USD
            NAS100 -> NAS100_USD
        """
        symbol = symbol.upper().strip()
        
        # If already in OANDA format, return as-is
        if "_" in symbol:
            return symbol
        
        # OANDA UK Index mappings
        index_mappings = {
            "US30": "US30_USD",      # Dow Jones
            "NAS100": "NAS100_USD",  # NASDAQ 100
            "SPX500": "SPX500_USD",  # S&P 500
            "UK100": "UK100_GBP",    # FTSE 100
            "DE30": "DE30_EUR",      # DAX
            "FR40": "FR40_EUR",      # CAC 40
            "JP225": "JP225_USD",    # Nikkei 225
            "AUS200": "AU200_AUD",   # ASX 200
            "HK33": "HK33_HKD",      # Hang Seng
            "CN50": "CN50_USD",      # China A50
            "IN50": "IN50_USD",      # India 50
            "TWIX": "TWIX_USD",      # Taiwan Index
            "NL25": "NL25_EUR",      # AEX
            "CH20": "CH20_CHF",      # SMI
            "SG30": "SG30_SGD"       # Singapore 30
        }
        
        # OANDA UK Metals mappings
        metals_mappings = {
            "GOLD": "XAU_USD",       # Gold
            "XAUUSD": "XAU_USD",     # Gold alternative
            "SILVER": "XAG_USD",     # Silver  
            "PLATINUM": "XPT_USD",   # Platinum
            "XPTUSD": "XPT_USD",     # Platinum alternative
            "PALLADIUM": "XPD_USD",  # Palladium
            "XPDUSD": "XPD_USD"      # Palladium alternative
        }
        
        # Check index mappings first
        if symbol in index_mappings:
            return index_mappings[symbol]
        
        # Check metals mappings
        if symbol in metals_mappings:
            return metals_mappings[symbol]
        
        # Convert 6-character forex format to OANDA format
        if len(symbol) == 6 and symbol.isalpha():
            return f"{symbol[:3]}_{symbol[3:]}"
        
        # If other format, return as-is and let OANDA handle validation
        return symbol

    async def health_check(self) -> bool:
        """
        Check if OANDA API is accessible
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            await self.get_account_info()
            return True
        except OANDAAPIError:
            return False

# Factory function for easy client creation
def create_oanda_client(api_key: str, account_id: str, environment: str = "practice") -> OANDAClient:
    """
    Factory function to create OANDA client
    
    Args:
        api_key: OANDA API key
        account_id: OANDA account ID  
        environment: "practice" or "live"
        
    Returns:
        Configured OANDAClient instance
    """
    env = OANDAEnvironment.PRACTICE if environment.lower() == "practice" else OANDAEnvironment.LIVE
    return OANDAClient(api_key, account_id, env)