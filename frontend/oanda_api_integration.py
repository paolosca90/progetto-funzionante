"""
OANDA API Integration Module
Provides real-time market data and trading functionality using OANDA REST API
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
    DEMO = "demo"
    PRACTICE = "practice"  # Alternative name for demo
    LIVE = "live"

class OANDAAPIError(Exception):
    """Custom exception for OANDA API errors"""
    pass

class OANDAConnectionError(OANDAAPIError):
    """Connection-related errors"""
    pass

@dataclass
class MarketData:
    """Market data structure"""
    instrument: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    volume: Optional[int] = None

@dataclass
class CandleData:
    """Candlestick data structure"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class OANDAClient:
    """
    OANDA REST API Client
    Handles authentication, rate limiting, and API communication
    """
    
    def __init__(self, api_key: str, account_id: str, environment: str = "demo"):
        self.api_key = api_key
        self.account_id = account_id
        self.environment = OANDAEnvironment(environment.lower())
        
        # Set base URL based on environment
        if self.environment in [OANDAEnvironment.DEMO, OANDAEnvironment.PRACTICE]:
            self.base_url = "https://api-fxpractice.oanda.com"
            self.stream_url = "https://stream-fxpractice.oanda.com"
        else:
            self.base_url = "https://api-fxtrade.oanda.com"
            self.stream_url = "https://stream-fxtrade.oanda.com"
        
        # HTTP session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        self._is_connected = False
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        logger.info(f"OANDA Client initialized for {environment} environment")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Establish connection to OANDA API"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        
        # Test connection
        try:
            await self.get_account_info()
            self._is_connected = True
            logger.info("✅ Connected to OANDA API successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to OANDA API: {e}")
            raise OANDAConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self):
        """Close connection to OANDA API"""
        if self.session and not self.session.closed:
            await self.session.close()
        self._is_connected = False
        logger.info("Disconnected from OANDA API")
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                           data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to OANDA API with rate limiting"""
        if not self.session or self.session.closed:
            await self.connect()
        
        # Rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=params) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    return await self._handle_response(response)
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, params=params) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    return await self._handle_response(response)
            else:
                raise OANDAAPIError(f"Unsupported HTTP method: {method}")
        
        except aiohttp.ClientError as e:
            logger.error(f"Request error: {e}")
            raise OANDAConnectionError(f"Request failed: {e}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """Handle API response and error checking"""
        try:
            response_data = await response.json()
        except:
            response_data = {"error": await response.text()}
        
        if response.status >= 400:
            error_msg = response_data.get("errorMessage", f"HTTP {response.status}")
            logger.error(f"API error: {error_msg}")
            raise OANDAAPIError(f"API error: {error_msg}")
        
        return response_data
    
    async def get_account_info(self) -> Dict:
        """Get account information"""
        return await self._make_request("GET", f"/v3/accounts/{self.account_id}")
    
    async def get_instruments(self) -> List[Dict]:
        """Get available trading instruments"""
        response = await self._make_request("GET", f"/v3/accounts/{self.account_id}/instruments")
        return response.get("instruments", [])
    
    async def get_prices(self, instruments: List[str]) -> List[MarketData]:
        """Get current prices for multiple instruments"""
        instruments_str = ",".join(instruments)
        params = {"instruments": instruments_str}
        
        response = await self._make_request("GET", "/v3/pricing", params=params)
        prices = []
        
        for price_data in response.get("prices", []):
            if price_data.get("status") == "tradeable":
                bids = price_data.get("bids", [])
                asks = price_data.get("asks", [])
                
                if bids and asks:
                    bid_price = float(bids[0]["price"])
                    ask_price = float(asks[0]["price"])
                    spread = ask_price - bid_price
                    
                    prices.append(MarketData(
                        instrument=price_data["instrument"],
                        bid=bid_price,
                        ask=ask_price,
                        spread=spread,
                        timestamp=datetime.fromisoformat(price_data["time"].replace("Z", "+00:00"))
                    ))
        
        return prices
    
    async def get_candles(self, instrument: str, granularity: str = "H1", 
                         count: int = 100, from_time: Optional[datetime] = None,
                         to_time: Optional[datetime] = None) -> List[CandleData]:
        """Get historical candlestick data"""
        params = {
            "granularity": granularity,
            "count": count
        }
        
        if from_time:
            params["from"] = from_time.isoformat() + "Z"
        if to_time:
            params["to"] = to_time.isoformat() + "Z"
        
        response = await self._make_request("GET", f"/v3/instruments/{instrument}/candles", params=params)
        
        candles = []
        for candle_data in response.get("candles", []):
            if candle_data.get("complete"):
                mid = candle_data["mid"]
                candles.append(CandleData(
                    time=datetime.fromisoformat(candle_data["time"].replace("Z", "+00:00")),
                    open=float(mid["o"]),
                    high=float(mid["h"]),
                    low=float(mid["l"]),
                    close=float(mid["c"]),
                    volume=int(candle_data["volume"])
                ))
        
        return candles
    
    async def get_position_book(self, instrument: str) -> Dict:
        """Get position book data for sentiment analysis"""
        return await self._make_request("GET", f"/v3/instruments/{instrument}/positionBook")
    
    async def get_order_book(self, instrument: str) -> Dict:
        """Get order book data"""
        return await self._make_request("GET", f"/v3/instruments/{instrument}/orderBook")
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._is_connected and self.session and not self.session.closed


# Factory function to create OANDA client
async def create_oanda_client(api_key: Optional[str] = None, 
                             account_id: Optional[str] = None,
                             environment: Optional[str] = None) -> OANDAClient:
    """
    Factory function to create and initialize OANDA client
    """
    # Get from environment variables if not provided
    api_key = api_key or os.getenv("OANDA_API_KEY")
    account_id = account_id or os.getenv("OANDA_ACCOUNT_ID", "101-004-26849219-001")
    environment = environment or os.getenv("OANDA_ENVIRONMENT", "demo")
    
    if not api_key:
        raise OANDAAPIError("OANDA API key is required")
    
    client = OANDAClient(api_key, account_id, environment)
    await client.connect()
    return client


# Utility functions for common operations
async def get_major_pairs_data() -> List[MarketData]:
    """Get data for major currency pairs"""
    major_pairs = [
        "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF",
        "AUD_USD", "USD_CAD", "NZD_USD", "EUR_GBP"
    ]
    
    async with await create_oanda_client() as client:
        return await client.get_prices(major_pairs)


async def get_market_hours_info() -> Dict[str, Any]:
    """Get current market session information"""
    now = datetime.utcnow()
    hour = now.hour
    
    # Market sessions (UTC)
    sessions = {
        "asian": {"start": 21, "end": 6, "active": False},
        "european": {"start": 6, "end": 16, "active": False},
        "us": {"start": 13, "end": 22, "active": False}
    }
    
    # Check active sessions
    if 21 <= hour or hour < 6:
        sessions["asian"]["active"] = True
    if 6 <= hour < 16:
        sessions["european"]["active"] = True
    if 13 <= hour < 22:
        sessions["us"]["active"] = True
    
    # Market overlap periods (higher volatility)
    overlaps = {
        "european_us": 13 <= hour < 16,  # Most active
        "asian_european": 6 <= hour < 8,
        "us_asian": 21 <= hour < 22
    }
    
    return {
        "current_time": now,
        "sessions": sessions,
        "overlaps": overlaps,
        "high_volatility": any(overlaps.values())
    }


if __name__ == "__main__":
    # Test the integration
    async def test_integration():
        try:
            print("Testing OANDA API integration...")
            
            # Test connection
            async with await create_oanda_client() as client:
                print("✅ Connection successful")
                
                # Test account info
                account = await client.get_account_info()
                print(f"✅ Account: {account['account']['id']}")
                
                # Test instruments
                instruments = await client.get_instruments()
                print(f"✅ Available instruments: {len(instruments)}")
                
                # Test prices
                prices = await client.get_prices(["EUR_USD", "GBP_USD"])
                for price in prices:
                    print(f"✅ {price.instrument}: {price.bid}/{price.ask} (spread: {price.spread:.5f})")
                
                # Test market hours
                market_info = await get_market_hours_info()
                print(f"✅ Market info: {market_info['sessions']}")
                
                print("🚀 All tests passed!")
        
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Run test
    asyncio.run(test_integration())