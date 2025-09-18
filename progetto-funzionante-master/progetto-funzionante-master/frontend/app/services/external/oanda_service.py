"""
OANDA Service with Dependency Injection Support

This service provides comprehensive OANDA API integration with:
- Real-time market data fetching
- Trading operations
- Account management
- Risk management
- Performance monitoring
- Connection resilience
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, List, Union, AsyncContextManager
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json
import hmac
import hashlib
import base64
from contextlib import asynccontextmanager

from ..core.config import Settings as CoreSettings
from ..core.dependency_injection import ServiceLifetime
from ..services.logging_service import LoggingService, LogContext, LogLevel
from ..services.config_service import ConfigService
from ..services.cache_service import CacheService
from ..services.http_client_service import HTTPClientService

logger = logging.getLogger(__name__)


class OandaEnvironment(Enum):
    """OANDA environment enumeration"""
    PRACTICE = "practice"
    LIVE = "live"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"


class OrderState(Enum):
    """Order state enumeration"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    TRIGGERED = "TRIGGERED"
    EXPIRED = "EXPIRED"


@dataclass
class OandaCredentials:
    """OANDA API credentials"""
    api_key: str
    account_id: str
    environment: OandaEnvironment
    base_url: str
    streaming_url: str


@dataclass
class MarketData:
    """Market data structure"""
    instrument: str
    time: datetime
    bid: float
    ask: float
    mid: float
    spread: float
    volume: Optional[int] = None


@dataclass
class CandleData:
    """Candle data structure"""
    instrument: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    complete: bool


@dataclass
class Order:
    """Order structure"""
    id: str
    instrument: str
    units: float
    type: OrderType
    state: OrderState
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    created_time: Optional[datetime] = None
    filled_time: Optional[datetime] = None
    expires: Optional[datetime] = None


@dataclass
class Trade:
    """Trade structure"""
    id: str
    instrument: str
    units: float
    price: float
    open_time: datetime
    current_price: float
    unrealized_pl: float
    realized_pl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None


@dataclass
class AccountInfo:
    """Account information structure"""
    id: str
    alias: Optional[str]
    currency: str
    balance: float
    unrealized_pl: float
    realized_pl: float
    margin_used: float
    margin_available: float
    open_trades: int
    open_orders: int
    last_updated: datetime


class OandaService:
    """Enhanced OANDA service with dependency injection support"""

    def __init__(self,
                 settings: CoreSettings,
                 logging_service: LoggingService,
                 config_service: ConfigService,
                 cache_service: CacheService,
                 http_client_service: HTTPClientService):
        self.settings = settings
        self.logging_service = logging_service
        self.config_service = config_service
        self.cache_service = cache_service
        self.http_client_service = http_client_service

        # OANDA components
        self.credentials: Optional[OandaCredentials] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._account_info: Optional[AccountInfo] = None
        self._last_account_update: float = 0
        self._account_update_interval: float = 30.0  # 30 seconds

        # Rate limiting
        self._rate_limiter = asyncio.Semaphore(10)  # 10 concurrent requests
        self._request_timestamps: List[float] = []
        self._max_requests_per_second = 10

        # Performance monitoring
        self._metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_request_time': 0.0
        }

        # Market data streaming
        self._streaming_active = False
        self._streaming_task: Optional[asyncio.Task] = None
        self._price_callbacks: List[Callable[[MarketData], None]] = []

        # Initialize service
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Initialize OANDA service"""
        try:
            # Load credentials from configuration
            self._load_credentials()

            # Create HTTP session
            self._create_session()

            # Validate connection
            self._validate_connection()

            logger.info("OANDA service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OANDA service: {e}")
            raise

    def _load_credentials(self) -> None:
        """Load OANDA credentials from configuration"""
        oanda_config = self.config_service.get_oanda_config()

        api_key = oanda_config.get('oanda_api_key')
        account_id = oanda_config.get('oanda_account_id')
        environment = oanda_config.get('oanda_environment', 'demo')

        if not api_key or not account_id:
            raise ValueError("OANDA API key and account ID are required")

        # Determine URLs based on environment
        if environment.lower() in ['practice', 'demo']:
            base_url = "https://api-fxpractice.oanda.com/v3"
            streaming_url = "https://stream-fxpractice.oanda.com/v3"
            env = OandaEnvironment.PRACTICE
        else:
            base_url = "https://api-fxtrade.oanda.com/v3"
            streaming_url = "https://stream-fxtrade.oanda.com/v3"
            env = OandaEnvironment.LIVE

        self.credentials = OandaCredentials(
            api_key=api_key,
            account_id=account_id,
            environment=env,
            base_url=base_url,
            streaming_url=streaming_url
        )

        logger.info(f"OANDA credentials loaded for {environment} environment")

    def _create_session(self) -> None:
        """Create HTTP session with authentication"""
        if not self.credentials:
            raise RuntimeError("OANDA credentials not loaded")

        headers = {
            'Authorization': f'Bearer {self.credentials.api_key}',
            'Content-Type': 'application/json',
            'Accept-Datetime-Format': 'RFC3339'
        }

        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
        )

    def _validate_connection(self) -> None:
        """Validate OANDA connection"""
        try:
            account_info = asyncio.run(self.get_account_info())
            if account_info:
                logger.info("OANDA connection validated successfully")
            else:
                raise RuntimeError("Failed to get account information")
        except Exception as e:
            logger.error(f"OANDA connection validation failed: {e}")
            raise

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to OANDA API"""
        if not self._session or not self.credentials:
            raise RuntimeError("OANDA service not initialized")

        start_time = time.time()

        # Rate limiting
        async with self._rate_limiter:
            await self._enforce_rate_limit()

            url = f"{self.credentials.base_url}{endpoint}"

            try:
                self._metrics['total_requests'] += 1
                self._metrics['last_request_time'] = start_time

                if method.upper() == 'GET':
                    response = await self._session.get(url)
                elif method.upper() == 'POST':
                    response = await self._session.post(url, json=data)
                elif method.upper() == 'PUT':
                    response = await self._session.put(url, json=data)
                elif method.upper() == 'DELETE':
                    response = await self._session.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Update metrics
                response_time = time.time() - start_time
                self._update_response_time_metrics(response_time)

                if response.status == 200:
                    self._metrics['successful_requests'] += 1
                    result = await response.json()
                    return result
                else:
                    self._metrics['failed_requests'] += 1
                    error_text = await response.text()
                    logger.error(f"OANDA API error: {response.status} - {error_text}")
                    return None

            except Exception as e:
                self._metrics['failed_requests'] += 1
                logger.error(f"OANDA API request failed: {e}")
                return None

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting"""
        current_time = time.time()
        self._request_timestamps = [t for t in self._request_timestamps if current_time - t < 1.0]

        if len(self._request_timestamps) >= self._max_requests_per_second:
            sleep_time = 1.0 - (current_time - self._request_timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self._request_timestamps.append(current_time)

    def _update_response_time_metrics(self, response_time: float) -> None:
        """Update response time metrics"""
        total_requests = self._metrics['successful_requests'] + self._metrics['failed_requests']
        if total_requests > 0:
            current_avg = self._metrics['average_response_time']
            new_avg = (current_avg * (total_requests - 1) + response_time) / total_requests
            self._metrics['average_response_time'] = new_avg

    # Account management methods
    async def get_account_info(self, force_refresh: bool = False) -> Optional[AccountInfo]:
        """Get account information"""
        current_time = time.time()

        # Use cached data if available and not stale
        if not force_refresh and self._account_info and (current_time - self._last_account_update) < self._account_update_interval:
            return self._account_info

        # Check cache first
        cache_key = f"oanda_account_{self.credentials.account_id}"
        cached_data = await self.cache_service.get(cache_key)
        if cached_data and not force_refresh:
            try:
                self._account_info = AccountInfo(**cached_data)
                self._last_account_update = current_time
                return self._account_info
            except Exception as e:
                logger.warning(f"Failed to parse cached account info: {e}")

        # Fetch fresh data
        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}')
        if response and 'account' in response:
            account_data = response['account']
            self._account_info = AccountInfo(
                id=account_data['id'],
                alias=account_data.get('alias'),
                currency=account_data['currency'],
                balance=float(account_data['balance']),
                unrealized_pl=float(account_data['unrealizedPL']),
                realized_pl=float(account_data['realizedPL']),
                margin_used=float(account_data['marginUsed']),
                margin_available=float(account_data['marginAvailable']),
                open_trades=account_data['openTradeCount'],
                open_orders=account_data['openOrderCount'],
                last_updated=datetime.now()
            )

            # Cache the result
            await self.cache_service.set(cache_key, asdict(self._account_info), ttl=60)
            self._last_account_update = current_time

            return self._account_info

        return None

    async def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """Get account summary"""
        return await self._make_request('GET', f'/accounts/{self.credentials.account_id}/summary')

    async def get_account_instruments(self, instruments: Optional[List[str]] = None) -> Optional[List[Dict[str, Any]]]:
        """Get account instruments"""
        params = {}
        if instruments:
            params['instruments'] = ','.join(instruments)

        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}/instruments', params)
        return response.get('instruments') if response else None

    # Market data methods
    async def get_pricing(self, instruments: List[str]) -> Optional[Dict[str, Any]]:
        """Get current pricing for instruments"""
        params = {
            'instruments': ','.join(instruments),
            'includeHomeConversions': 'false'
        }

        return await self._make_request('GET', f'/accounts/{self.credentials.account_id}/pricing', params)

    async def get_candles(self, instrument: str,
                         granularity: str = 'H1',
                         count: int = 100,
                         from_time: Optional[datetime] = None,
                         to_time: Optional[datetime] = None) -> Optional[List[CandleData]]:
        """Get candle data for an instrument"""
        params = {
            'price': 'M',  # Mid price
            'granularity': granularity,
            'count': count
        }

        if from_time:
            params['from'] = from_time.isoformat()
        if to_time:
            params['to'] = to_time.isoformat()

        # Check cache first
        cache_key = f"oanda_candles_{instrument}_{granularity}_{count}"
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            try:
                candles = [CandleData(**candle) for candle in cached_data]
                return candles
            except Exception as e:
                logger.warning(f"Failed to parse cached candles: {e}")

        # Fetch fresh data
        response = await self._make_request('GET', f'/instruments/{instrument}/candles', params)
        if response and 'candles' in response:
            candles = []
            for candle_data in response['candles']:
                candle = CandleData(
                    instrument=instrument,
                    time=datetime.fromisoformat(candle_data['time'].replace('Z', '+00:00')),
                    open=float(candle_data['mid']['o']),
                    high=float(candle_data['mid']['h']),
                    low=float(candle_data['mid']['l']),
                    close=float(candle_data['mid']['c']),
                    volume=candle_data['volume'],
                    complete=candle_data['complete']
                )
                candles.append(candle)

            # Cache the result
            await self.cache_service.set(cache_key, [asdict(candle) for candle in candles], ttl=300)

            return candles

        return None

    # Order management methods
    async def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new order"""
        return await self._make_request('POST', f'/accounts/{self.credentials.account_id}/orders', order_data)

    async def get_orders(self, state: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get orders"""
        params = {}
        if state:
            params['state'] = state

        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}/orders', params)
        return response.get('orders') if response else None

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get specific order"""
        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}/orders/{order_id}')
        return response.get('order') if response else None

    async def cancel_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Cancel an order"""
        return await self._make_request('PUT', f'/accounts/{self.credentials.account_id}/orders/{order_id}/cancel')

    async def replace_order(self, order_id: str, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Replace an order"""
        return await self._make_request('PUT', f'/accounts/{self.credentials.account_id}/orders/{order_id}', order_data)

    # Trade management methods
    async def get_trades(self, state: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get trades"""
        params = {}
        if state:
            params['state'] = state

        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}/trades', params)
        return response.get('trades') if response else None

    async def get_trade(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Get specific trade"""
        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}/trades/{trade_id}')
        return response.get('trade') if response else None

    async def close_trade(self, trade_id: str, units: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Close a trade"""
        data = {}
        if units:
            data['units'] = str(units)

        return await self._make_request('PUT', f'/accounts/{self.credentials.account_id}/trades/{trade_id}/close', data)

    async def update_trade(self, trade_id: str, trade_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a trade"""
        return await self._make_request('PUT', f'/accounts/{self.credentials.account_id}/trades/{trade_id}', trade_data)

    # Position management methods
    async def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """Get all positions"""
        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}/positions')
        return response.get('positions') if response else None

    async def get_position(self, instrument: str) -> Optional[Dict[str, Any]]:
        """Get position for specific instrument"""
        response = await self._make_request('GET', f'/accounts/{self.credentials.account_id}/positions/{instrument}')
        return response.get('position') if response else None

    async def close_position(self, instrument: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Close position for specific instrument"""
        return await self._make_request('PUT', f'/accounts/{self.credentials.account_id}/positions/{instrument}/close', data)

    # Streaming methods
    async def start_price_streaming(self, instruments: List[str]) -> None:
        """Start streaming price data"""
        if self._streaming_active:
            return

        self._streaming_active = True
        self._streaming_task = asyncio.create_task(self._stream_prices(instruments))

    async def stop_price_streaming(self) -> None:
        """Stop streaming price data"""
        self._streaming_active = False
        if self._streaming_task:
            self._streaming_task.cancel()
            try:
                await self._streaming_task
            except asyncio.CancelledError:
                pass

    async def _stream_prices(self, instruments: List[str]) -> None:
        """Stream price data"""
        if not self._session or not self.credentials:
            return

        url = f"{self.credentials.streaming_url}/accounts/{self.credentials.account_id}/pricing/stream"
        params = {
            'instruments': ','.join(instruments),
            'includeHomeConversions': 'false'
        }

        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    async for line in response.content:
                        if not self._streaming_active:
                            break

                        try:
                            data = json.loads(line.decode('utf-8').strip())
                            if 'type' in data and data['type'] == 'PRICE':
                                price_data = self._parse_price_data(data)
                                if price_data:
                                    await self._notify_price_callbacks(price_data)
                        except Exception as e:
                            logger.warning(f"Error parsing streaming data: {e}")
                else:
                    logger.error(f"Price streaming failed: {response.status}")

        except Exception as e:
            logger.error(f"Price streaming error: {e}")
        finally:
            self._streaming_active = False

    def _parse_price_data(self, data: Dict[str, Any]) -> Optional[MarketData]:
        """Parse price data from streaming response"""
        try:
            return MarketData(
                instrument=data['instrument'],
                time=datetime.fromisoformat(data['time'].replace('Z', '+00:00')),
                bid=float(data['bids'][0]['price']),
                ask=float(data['asks'][0]['price']),
                mid=(float(data['bids'][0]['price']) + float(data['asks'][0]['price'])) / 2,
                spread=float(data['asks'][0]['price']) - float(data['bids'][0]['price'])
            )
        except Exception as e:
            logger.warning(f"Error parsing price data: {e}")
            return None

    async def _notify_price_callbacks(self, price_data: MarketData) -> None:
        """Notify price callbacks with new data"""
        for callback in self._price_callbacks:
            try:
                callback(price_data)
            except Exception as e:
                logger.warning(f"Error in price callback: {e}")

    def add_price_callback(self, callback: Callable[[MarketData], None]) -> None:
        """Add callback for price updates"""
        self._price_callbacks.append(callback)

    def remove_price_callback(self, callback: Callable[[MarketData], None]) -> None:
        """Remove price callback"""
        if callback in self._price_callbacks:
            self._price_callbacks.remove(callback)

    # Utility methods
    async def get_available_instruments(self) -> List[str]:
        """Get list of available instruments"""
        response = await self.get_account_instruments()
        if response:
            return [instrument['name'] for instrument in response]
        return []

    async def is_market_open(self, instrument: str) -> Optional[bool]:
        """Check if market is open for instrument"""
        pricing = await self.get_pricing([instrument])
        if pricing and 'prices' in pricing and pricing['prices']:
            return pricing['prices'][0].get('tradeable', False)
        return None

    async def get_spread(self, instrument: str) -> Optional[float]:
        """Get current spread for instrument"""
        pricing = await self.get_pricing([instrument])
        if pricing and 'prices' in pricing and pricing['prices']:
            price = pricing['prices'][0]
            if 'bids' in price and 'asks' in price and price['bids'] and price['asks']:
                return float(price['asks'][0]['price']) - float(price['bids'][0]['price'])
        return None

    # Performance and monitoring
    def get_metrics(self) -> Dict[str, Any]:
        """Get OANDA service metrics"""
        return {
            'total_requests': self._metrics['total_requests'],
            'successful_requests': self._metrics['successful_requests'],
            'failed_requests': self._metrics['failed_requests'],
            'success_rate': self._metrics['successful_requests'] / max(self._metrics['total_requests'], 1),
            'average_response_time': self._metrics['average_response_time'],
            'last_request_time': self._metrics['last_request_time'],
            'streaming_active': self._streaming_active,
            'price_callbacks_count': len(self._price_callbacks)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            account_info = await self.get_account_info()
            if account_info:
                return {
                    'status': 'healthy',
                    'account_id': account_info.id,
                    'currency': account_info.currency,
                    'balance': account_info.balance,
                    'last_updated': account_info.last_updated.isoformat()
                }
            else:
                return {'status': 'unhealthy', 'error': 'Failed to get account info'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def __dispose__(self) -> None:
        """Dispose OANDA service resources"""
        # Stop streaming
        await self.stop_price_streaming()

        # Close HTTP session
        if self._session:
            await self._session.close()

        # Clear callbacks
        self._price_callbacks.clear()

        logger.info("OANDA service disposed")


# Factory function for creating OANDA service
async def create_oanda_service(settings: CoreSettings,
                             logging_service: LoggingService,
                             config_service: ConfigService,
                             cache_service: CacheService,
                             http_client_service: HTTPClientService) -> OandaService:
    """Create and initialize OANDA service"""
    service = OandaService(
        settings=settings,
        logging_service=logging_service,
        config_service=config_service,
        cache_service=cache_service,
        http_client_service=http_client_service
    )
    return service