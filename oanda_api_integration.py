"""
OANDA API Integration Module for High-Frequency Trading Systems
==============================================================

Professional-grade OANDA REST API integration with:
- Real-time price streaming and market data
- Historical price data with multiple timeframes
- Account management and position tracking
- Rate limiting and error handling
- Circuit breaker pattern for reliability
- Configurable retry logic with exponential backoff
- Production-ready logging and monitoring

Author: Backend Performance Architect
Date: September 2025
"""

import os
import asyncio
import aiohttp
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from enum import Enum
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
import time
from functools import wraps
import ssl
from urllib.parse import urljoin
import backoff

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# === ENUMS AND DATA MODELS ===

class OANDAEnvironment(Enum):
    """OANDA API environments"""
    DEMO = "demo"
    LIVE = "live"

class Granularity(Enum):
    """OANDA supported granularities (timeframes)"""
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
    D = "D"        # Daily
    W = "W"        # Weekly
    M = "M"        # Monthly

class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    MARKET_IF_TOUCHED = "MARKET_IF_TOUCHED"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"

@dataclass
class OANDAConfig:
    """OANDA API configuration"""
    api_key: str
    account_id: str
    environment: OANDAEnvironment = OANDAEnvironment.DEMO
    request_timeout: int = 30
    max_retries: int = 3
    rate_limit_per_second: int = 100
    rate_limit_per_minute: int = 6000
    backoff_factor: float = 1.5
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60

@dataclass
class MarketPrice:
    """Market price data"""
    instrument: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    
    @property
    def mid(self) -> float:
        """Mid-point price"""
        return (self.bid + self.ask) / 2.0

@dataclass
class OHLCV:
    """OHLCV candlestick data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    complete: bool = True

@dataclass
class AccountInfo:
    """Account information"""
    id: str
    currency: str
    balance: float
    unrealized_pl: float
    realized_pl: float
    margin_used: float
    margin_available: float
    margin_rate: float
    nav: float
    last_transaction_id: str
    open_trade_count: int
    open_position_count: int

@dataclass
class Position:
    """Position information"""
    instrument: str
    long_units: float
    short_units: float
    net_units: float
    unrealized_pl: float
    margin_used: float

# === EXCEPTIONS ===

class OANDAAPIError(Exception):
    """Base OANDA API exception"""
    pass

class OANDAConnectionError(OANDAAPIError):
    """Connection-related errors"""
    pass

class OANDARateLimitError(OANDAAPIError):
    """Rate limit exceeded"""
    pass

class OANDAAuthenticationError(OANDAAPIError):
    """Authentication errors"""
    pass

class OANDACircuitBreakerError(OANDAAPIError):
    """Circuit breaker is open"""
    pass

# === RATE LIMITER ===

class RateLimiter:
    """Thread-safe rate limiter with sliding window"""
    
    def __init__(self, max_calls_per_second: int = 100, max_calls_per_minute: int = 6000):
        self.max_calls_per_second = max_calls_per_second
        self.max_calls_per_minute = max_calls_per_minute
        self.calls_per_second = []
        self.calls_per_minute = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit token"""
        async with self._lock:
            now = time.time()
            
            # Clean old entries
            self.calls_per_second = [t for t in self.calls_per_second if now - t < 1.0]
            self.calls_per_minute = [t for t in self.calls_per_minute if now - t < 60.0]
            
            # Check rate limits
            if len(self.calls_per_second) >= self.max_calls_per_second:
                sleep_time = 1.0 - (now - self.calls_per_second[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            if len(self.calls_per_minute) >= self.max_calls_per_minute:
                sleep_time = 60.0 - (now - self.calls_per_minute[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            # Record this call
            now = time.time()
            self.calls_per_second.append(now)
            self.calls_per_minute.append(now)

# === CIRCUIT BREAKER ===

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker pattern for API resilience"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if (time.time() - self.last_failure_time) > self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise OANDACircuitBreakerError("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    logger.info("Circuit breaker reset to CLOSED")
                return result
            
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise e

# === MAIN OANDA CLIENT ===

class OANDAClient:
    """
    Professional OANDA API client for high-frequency trading systems
    
    Features:
    - Async/await support for high performance
    - Built-in rate limiting and circuit breaker
    - Comprehensive error handling and retry logic
    - Real-time price streaming
    - Historical data with multiple timeframes
    - Position and account management
    """
    
    def __init__(self, config: OANDAConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(
            config.rate_limit_per_second, 
            config.rate_limit_per_minute
        )
        self.circuit_breaker = CircuitBreaker(
            config.circuit_breaker_failure_threshold,
            config.circuit_breaker_recovery_timeout
        )
        
        # API URLs
        if config.environment == OANDAEnvironment.LIVE:
            self.api_url = "https://api-fxtrade.oanda.com"
            self.stream_url = "https://stream-fxtrade.oanda.com"
        else:
            self.api_url = "https://api-fxpractice.oanda.com"
            self.stream_url = "https://stream-fxpractice.oanda.com"
        
        self._connected = False
        self._stream_tasks = []
        
        logger.info(f"OANDA Client initialized for {config.environment.value} environment")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Initialize HTTP session and validate connection"""
        if self._connected:
            return
        
        # Create SSL context for secure connections
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # Configure HTTP session with optimizations
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=50,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=ssl_context
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_headers()
        )
        
        # Validate connection
        await self._validate_connection()
        self._connected = True
        logger.info("OANDA API connection established")
    
    async def disconnect(self):
        """Close HTTP session and cleanup"""
        if not self._connected:
            return
        
        # Cancel streaming tasks
        for task in self._stream_tasks:
            if not task.cancelled():
                task.cancel()
        
        if self._stream_tasks:
            await asyncio.gather(*self._stream_tasks, return_exceptions=True)
        
        # Close session
        if self.session:
            await self.session.close()
            self.session = None
        
        self._connected = False
        logger.info("OANDA API connection closed")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OANDA-HFT-Client/1.0"
        }
    
    async def _validate_connection(self):
        """Validate API connection and credentials"""
        try:
            # Handle account discovery for demo accounts
            if self.config.account_id == "DISCOVER":
                await self._discover_account_id()
            
            account_info = await self.get_account_info()
            logger.info(f"Connection validated for account: {account_info.id}")
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            raise OANDAConnectionError(f"Failed to validate connection: {e}")
    
    async def _discover_account_id(self):
        """Discover account ID for demo accounts"""
        try:
            endpoint = "/v3/accounts"
            response = await self._make_request("GET", endpoint)
            
            accounts = response.get("accounts", [])
            if not accounts:
                raise OANDAAPIError("No accounts found")
            
            # Use the first available account
            account_id = accounts[0]["id"]
            self.config.account_id = account_id
            logger.info(f"Discovered account ID: {account_id}")
            
        except Exception as e:
            logger.error(f"Failed to discover account ID: {e}")
            raise OANDAConnectionError(f"Failed to discover account ID: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, OANDARateLimitError),
        max_tries=3,
        factor=1.5
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        stream: bool = False
    ) -> Union[Dict, aiohttp.ClientResponse]:
        """Make HTTP request with error handling and retries"""
        if not self._connected:
            await self.connect()
        
        await self.rate_limiter.acquire()
        
        url = urljoin(self.stream_url if stream else self.api_url, endpoint)
        
        try:
            async def _request():
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=self._get_headers()
                ) as response:
                    await self._handle_response_errors(response)
                    
                    if stream:
                        return response
                    else:
                        return await response.json()
            
            return await self.circuit_breaker.call(_request)
        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise OANDAConnectionError(f"HTTP client error: {e}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def _handle_response_errors(self, response: aiohttp.ClientResponse):
        """Handle HTTP response errors"""
        if response.status == 200:
            return
        
        error_text = await response.text()
        
        if response.status == 401:
            raise OANDAAuthenticationError(f"Authentication failed: {error_text}")
        elif response.status == 429:
            retry_after = response.headers.get('Retry-After', '60')
            raise OANDARateLimitError(f"Rate limit exceeded. Retry after {retry_after}s")
        elif response.status >= 500:
            raise OANDAConnectionError(f"Server error {response.status}: {error_text}")
        else:
            raise OANDAAPIError(f"API error {response.status}: {error_text}")
    
    # === ACCOUNT METHODS ===
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information"""
        endpoint = f"/v3/accounts/{self.config.account_id}"
        response = await self._make_request("GET", endpoint)
        
        account_data = response["account"]
        return AccountInfo(
            id=account_data["id"],
            currency=account_data["currency"],
            balance=float(account_data["balance"]),
            unrealized_pl=float(account_data["unrealizedPL"]),
            realized_pl=float(account_data["pl"]),
            margin_used=float(account_data["marginUsed"]),
            margin_available=float(account_data["marginAvailable"]),
            margin_rate=float(account_data["marginRate"]),
            nav=float(account_data["NAV"]),
            last_transaction_id=account_data["lastTransactionID"],
            open_trade_count=int(account_data["openTradeCount"]),
            open_position_count=int(account_data["openPositionCount"])
        )
    
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        endpoint = f"/v3/accounts/{self.config.account_id}/positions"
        response = await self._make_request("GET", endpoint)
        
        positions = []
        for pos_data in response["positions"]:
            if float(pos_data["long"]["units"]) != 0 or float(pos_data["short"]["units"]) != 0:
                positions.append(Position(
                    instrument=pos_data["instrument"],
                    long_units=float(pos_data["long"]["units"]),
                    short_units=float(pos_data["short"]["units"]),
                    net_units=float(pos_data["long"]["units"]) + float(pos_data["short"]["units"]),
                    unrealized_pl=float(pos_data["unrealizedPL"]),
                    margin_used=float(pos_data["marginUsed"])
                ))
        
        return positions
    
    # === MARKET DATA METHODS ===
    
    async def get_instruments(self) -> List[Dict[str, Any]]:
        """Get available trading instruments"""
        endpoint = f"/v3/accounts/{self.config.account_id}/instruments"
        response = await self._make_request("GET", endpoint)
        return response["instruments"]
    
    async def get_current_prices(self, instruments: List[str]) -> List[MarketPrice]:
        """Get current bid/ask prices for instruments"""
        params = {"instruments": ",".join(instruments)}
        endpoint = f"/v3/accounts/{self.config.account_id}/pricing"
        
        response = await self._make_request("GET", endpoint, params=params)
        
        prices = []
        for price_data in response["prices"]:
            if price_data["status"] == "tradeable":
                prices.append(MarketPrice(
                    instrument=price_data["instrument"],
                    bid=float(price_data["bids"][0]["price"]),
                    ask=float(price_data["asks"][0]["price"]),
                    spread=float(price_data["asks"][0]["price"]) - float(price_data["bids"][0]["price"]),
                    timestamp=datetime.fromisoformat(price_data["time"].replace('Z', '+00:00'))
                ))
        
        return prices
    
    async def get_candles(
        self, 
        instrument: str,
        granularity: Granularity = Granularity.H1,
        count: int = 500,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        price: str = "M"  # M=Mid, B=Bid, A=Ask
    ) -> pd.DataFrame:
        """
        Get historical candle data
        
        Args:
            instrument: Trading instrument (e.g., "EUR_USD")
            granularity: Candle granularity
            count: Maximum number of candles (500 max)
            from_time: Start time (optional)
            to_time: End time (optional)
            price: Price type (M=Mid, B=Bid, A=Ask)
        
        Returns:
            DataFrame with OHLCV data
        """
        endpoint = f"/v3/instruments/{instrument}/candles"
        
        params = {
            "granularity": granularity.value,
            "price": price
        }
        
        if count:
            params["count"] = min(count, 5000)  # OANDA max is 5000
        if from_time:
            params["from"] = from_time.isoformat()
        if to_time:
            params["to"] = to_time.isoformat()
        
        response = await self._make_request("GET", endpoint, params=params)
        
        # Convert to DataFrame
        candles_data = []
        for candle in response["candles"]:
            if candle["complete"]:
                candles_data.append({
                    "timestamp": datetime.fromisoformat(candle["time"].replace('Z', '+00:00')),
                    "open": float(candle[price.lower()]["o"]),
                    "high": float(candle[price.lower()]["h"]),
                    "low": float(candle[price.lower()]["l"]),
                    "close": float(candle[price.lower()]["c"]),
                    "volume": int(candle["volume"])
                })
        
        if not candles_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(candles_data)
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        
        logger.info(f"Retrieved {len(df)} candles for {instrument} at {granularity.value}")
        return df
    
    # === STREAMING METHODS ===
    
    async def stream_prices(
        self,
        instruments: List[str],
        callback: callable,
        snapshot: bool = True
    ):
        """
        Stream real-time prices
        
        Args:
            instruments: List of instruments to stream
            callback: Async function called for each price update
            snapshot: Include initial snapshot
        """
        endpoint = "/v3/accounts/{}/pricing/stream".format(self.config.account_id)
        params = {
            "instruments": ",".join(instruments),
            "snapshot": str(snapshot).lower()
        }
        
        response = await self._make_request("GET", endpoint, params=params, stream=True)
        
        async def _stream_reader():
            try:
                async for line in response.content:
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        
                        if data["type"] == "PRICE":
                            price = MarketPrice(
                                instrument=data["instrument"],
                                bid=float(data["bids"][0]["price"]),
                                ask=float(data["asks"][0]["price"]),
                                spread=float(data["asks"][0]["price"]) - float(data["bids"][0]["price"]),
                                timestamp=datetime.fromisoformat(data["time"].replace('Z', '+00:00'))
                            )
                            await callback(price)
                        elif data["type"] == "HEARTBEAT":
                            logger.debug(f"Heartbeat: {data['time']}")
            
            except asyncio.CancelledError:
                logger.info("Price streaming cancelled")
            except Exception as e:
                logger.error(f"Error in price streaming: {e}")
                raise
        
        task = asyncio.create_task(_stream_reader())
        self._stream_tasks.append(task)
        logger.info(f"Started price streaming for {instruments}")
        
        return task
    
    # === UTILITY METHODS ===
    
    def normalize_instrument(self, symbol: str) -> str:
        """
        Convert MT5-style symbols to OANDA format
        
        Examples:
        EURUSD -> EUR_USD
        XAUUSD -> XAU_USD
        US500 -> SPX500_USD
        """
        # Common symbol mappings
        symbol_map = {
            # Forex pairs
            "EURUSD": "EUR_USD",
            "GBPUSD": "GBP_USD", 
            "USDJPY": "USD_JPY",
            "USDCHF": "USD_CHF",
            "AUDUSD": "AUD_USD",
            "USDCAD": "USD_CAD",
            "NZDUSD": "NZD_USD",
            "EURGBP": "EUR_GBP",
            "EURJPY": "EUR_JPY",
            "GBPJPY": "GBP_JPY",
            
            # Metals
            "XAUUSD": "XAU_USD",
            "XAGUSD": "XAG_USD",
            
            # Indices (OANDA CFDs)
            "US30": "US30_USD",
            "NAS100": "NAS100_USD", 
            "SPX500": "SPX500_USD",
            "US500": "SPX500_USD",  # Alias
            "GER30": "DE30_EUR",
            "UK100": "UK100_GBP",
            "JPN225": "JP225_USD"
        }
        
        return symbol_map.get(symbol, symbol)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            start_time = time.time()
            account_info = await self.get_account_info()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "connected": self._connected,
                "account_id": account_info.id,
                "environment": self.config.environment.value,
                "response_time_ms": round(response_time * 1000, 2),
                "circuit_breaker_state": self.circuit_breaker.state.value,
                "failure_count": self.circuit_breaker.failure_count
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": self._connected,
                "circuit_breaker_state": self.circuit_breaker.state.value,
                "failure_count": self.circuit_breaker.failure_count
            }

# === HIGH-LEVEL TRADING INTERFACE ===

class OANDAMarketDataProvider:
    """
    High-level interface for market data compatible with existing signal engine
    """
    
    def __init__(self, oanda_client: OANDAClient):
        self.client = oanda_client
        self._price_cache = {}
        self._cache_expiry = {}
    
    async def get_real_time_price(self, symbol: str) -> Optional[float]:
        """Get real-time price compatible with signal engine"""
        try:
            instrument = self.client.normalize_instrument(symbol)
            prices = await self.client.get_current_prices([instrument])
            
            if prices:
                price = prices[0].mid
                self._price_cache[symbol] = price
                self._cache_expiry[symbol] = time.time() + 5  # Cache for 5 seconds
                return price
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {e}")
            
            # Return cached price if recent
            if (symbol in self._price_cache and 
                symbol in self._cache_expiry and 
                time.time() < self._cache_expiry[symbol]):
                return self._price_cache[symbol]
            
            return None
    
    async def get_market_data(
        self, 
        symbol: str, 
        timeframe: str = 'H1', 
        count: int = 500
    ) -> Optional[pd.DataFrame]:
        """Get historical market data compatible with signal engine"""
        try:
            instrument = self.client.normalize_instrument(symbol)
            
            # Convert timeframe
            granularity_map = {
                'M1': Granularity.M1,
                'M5': Granularity.M5,
                'M15': Granularity.M15,
                'M30': Granularity.M30,
                'H1': Granularity.H1,
                'H4': Granularity.H4,
                'D1': Granularity.D
            }
            
            granularity = granularity_map.get(timeframe, Granularity.H1)
            
            df = await self.client.get_candles(
                instrument=instrument,
                granularity=granularity,
                count=min(count, 5000)
            )
            
            if df.empty:
                return None
            
            # Rename columns to match MT5 format expected by signal engine
            df = df.rename(columns={'timestamp': 'time'})
            df['tick_volume'] = df['volume']  # OANDA volume as tick volume
            df['spread'] = 0  # Not available in OANDA historical data
            df['real_volume'] = df['volume']
            
            return df
        
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None

# === FACTORY FUNCTION ===

def create_oanda_client(
    api_key: Optional[str] = None,
    account_id: Optional[str] = None,
    environment: str = "demo"
) -> OANDAClient:
    """
    Factory function to create OANDA client from environment variables or parameters
    
    Environment variables:
    - OANDA_API_KEY: API key
    - OANDA_ACCOUNT_ID: Account ID  
    - OANDA_ENVIRONMENT: 'demo' or 'live'
    """
    
    # Get configuration from environment or parameters
    api_key = api_key or os.getenv("OANDA_API_KEY", "b4354e4855d53550bc6eac7e5bb8ac2b-66726ffbb3e3eb85e007a6dbda5d0b18")
    account_id = account_id or os.getenv("OANDA_ACCOUNT_ID")
    environment = environment or os.getenv("OANDA_ENVIRONMENT", "demo")
    
    if not api_key:
        raise ValueError("OANDA API key not provided. Set OANDA_API_KEY environment variable or pass api_key parameter.")
    
    # For demo environment, we'll extract account ID from API key if not provided
    if not account_id:
        if environment.lower() == "demo":
            # For demo accounts, we need to discover the account ID via API
            logger.info("Account ID not provided for demo environment - will discover via API")
            account_id = "DISCOVER"  # Special flag to discover account ID
        else:
            raise ValueError("OANDA account ID not provided. Set OANDA_ACCOUNT_ID environment variable or pass account_id parameter.")
    
    config = OANDAConfig(
        api_key=api_key,
        account_id=account_id,
        environment=OANDAEnvironment(environment.lower())
    )
    
    return OANDAClient(config)

# === EXAMPLE USAGE ===

async def example_usage():
    """Example of how to use the OANDA API integration"""
    
    # Create client
    client = create_oanda_client()
    
    async with client:
        # Get account info
        account = await client.get_account_info()
        print(f"Account: {account.id}, Balance: {account.balance} {account.currency}")
        
        # Get current prices
        prices = await client.get_current_prices(["EUR_USD", "GBP_USD"])
        for price in prices:
            print(f"{price.instrument}: {price.bid}/{price.ask} (spread: {price.spread:.5f})")
        
        # Get historical data
        df = await client.get_candles("EUR_USD", Granularity.H1, count=100)
        print(f"Retrieved {len(df)} candles")
        print(df.tail())
        
        # Market data provider example
        provider = OANDAMarketDataProvider(client)
        real_time_price = await provider.get_real_time_price("EURUSD")
        print(f"Real-time EURUSD: {real_time_price}")
        
        market_data = await provider.get_market_data("EURUSD", "H1", 100)
        if market_data is not None:
            print(f"Market data shape: {market_data.shape}")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())