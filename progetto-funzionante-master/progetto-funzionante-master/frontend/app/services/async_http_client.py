"""
Async HTTP Client Service for External API Integration
Implements high-performance async HTTP operations with connection pooling,
circuit breaking, retry logic, and comprehensive error handling.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)

class HttpMethod(Enum):
    """HTTP Methods supported by the async client"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Circuit open, fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

@dataclass
class TimeoutConfig:
    """Configuration for timeout handling"""
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    pool_timeout: float = 5.0

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: tuple = (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)

@dataclass
class HttpClientMetrics:
    """Metrics for HTTP client performance monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    circuit_breaker_trips: int = 0
    retries: int = 0
    average_response_time: float = 0.0
    last_response_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

class AsyncCircuitBreaker:
    """Circuit breaker implementation for async HTTP calls"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.success_count = 0
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise httpx.ConnectError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.config.expected_exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 3:  # Success threshold
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if (self.state == CircuitState.CLOSED and
                self.failure_count >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "success_count": self.success_count
        }

class AsyncHttpClient:
    """
    High-performance async HTTP client with comprehensive features:
    - Connection pooling and keep-alive
    - Circuit breaker pattern
    - Retry logic with exponential backoff
    - Timeout handling
    - Request/response logging
    - Metrics collection
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_config: Optional[TimeoutConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        enable_metrics: bool = True
    ):
        self.base_url = base_url
        self.timeout_config = timeout_config or TimeoutConfig()
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.enable_metrics = enable_metrics

        # Configure httpx client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=base_url,
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
                keepalive_expiry=30.0
            ),
            timeout=httpx.Timeout(
                connect=self.timeout_config.connect_timeout,
                read=self.timeout_config.read_timeout,
                write=self.timeout_config.write_timeout,
                pool=self.timeout_config.pool_timeout
            ),
            follow_redirects=True,
            http2=True
        )

        # Initialize circuit breakers for different services
        self.circuit_breakers: Dict[str, AsyncCircuitBreaker] = {}
        self.metrics = HttpClientMetrics()

    def _get_circuit_breaker(self, service: str = "default") -> AsyncCircuitBreaker:
        """Get or create circuit breaker for a service"""
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = AsyncCircuitBreaker(self.circuit_breaker_config)
        return self.circuit_breakers[service]

    def _update_metrics(self, success: bool, response_time: float, is_timeout: bool = False):
        """Update client metrics"""
        if not self.enable_metrics:
            return

        self.metrics.total_requests += 1
        self.metrics.last_response_time = response_time

        # Update average response time
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            weight = 0.1  # 10% weight for new measurements
            self.metrics.average_response_time = (
                (1 - weight) * self.metrics.average_response_time +
                weight * response_time
            )

        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            if is_timeout:
                self.metrics.timeout_requests += 1

    def _add_retry_decorator(self, func):
        """Add retry decorator to async function"""
        return retry(
            stop=stop_after_attempt(self.retry_config.max_attempts),
            wait=wait_exponential(
                base=self.retry_config.base_delay,
                exp=self.retry_config.exponential_base,
                max=self.retry_config.max_delay,
                multiplier=self.retry_config.jitter
            ),
            retry=retry_if_exception_type((
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError
            ))
        )(func)

    async def request(
        self,
        method: HttpMethod,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        service: str = "default",
        **kwargs
    ) -> httpx.Response:
        """
        Make async HTTP request with circuit breaker and retry logic

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            json_data: JSON payload
            data: Raw data payload
            service: Service name for circuit breaker
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: For HTTP-related errors
            Exception: For other errors
        """
        start_time = time.time()
        circuit_breaker = self._get_circuit_breaker(service)

        async def _make_request():
            try:
                response = await self.client.request(
                    method=method.value,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data,
                    **kwargs
                )
                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                self.metrics.retries += 1
                raise httpx.TimeoutException(f"Request timeout: {e}")
            except httpx.NetworkError as e:
                self.metrics.retries += 1
                raise httpx.NetworkError(f"Network error: {e}")
            except httpx.HTTPStatusError as e:
                self.metrics.retries += 1
                raise e

        # Apply retry decorator
        retry_request = self._add_retry_decorator(_make_request)

        try:
            # Execute with circuit breaker protection
            response = await circuit_breaker.call(retry_request)

            # Update metrics
            response_time = time.time() - start_time
            self._update_metrics(True, response_time)

            logger.debug(f"HTTP {method.value} {url} - {response.status_code} - {response_time:.3f}s")
            return response

        except Exception as e:
            response_time = time.time() - start_time
            is_timeout = isinstance(e, httpx.TimeoutException)
            self._update_metrics(False, response_time, is_timeout)

            if isinstance(e, httpx.TimeoutException):
                logger.error(f"HTTP timeout for {method.value} {url}: {e}")
            elif isinstance(e, httpx.HTTPStatusError):
                logger.error(f"HTTP error for {method.value} {url}: {e}")
            else:
                logger.error(f"HTTP request failed for {method.value} {url}: {e}")

            raise

    # Convenience methods
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request"""
        return await self.request(HttpMethod.GET, url, **kwargs)

    async def post(self, url: str, json_data: Optional[Dict] = None, **kwargs) -> httpx.Response:
        """POST request"""
        return await self.request(HttpMethod.POST, url, json_data=json_data, **kwargs)

    async def put(self, url: str, json_data: Optional[Dict] = None, **kwargs) -> httpx.Response:
        """PUT request"""
        return await self.request(HttpMethod.PUT, url, json_data=json_data, **kwargs)

    async def patch(self, url: str, json_data: Optional[Dict] = None, **kwargs) -> httpx.Response:
        """PATCH request"""
        return await self.request(HttpMethod.PATCH, url, json_data=json_data, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE request"""
        return await self.request(HttpMethod.DELETE, url, **kwargs)

    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET request returning JSON"""
        response = await self.get(url, **kwargs)
        return response.json()

    async def post_json(self, url: str, json_data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """POST request returning JSON"""
        response = await self.post(url, json_data=json_data, **kwargs)
        return response.json()

    # Batch operations
    async def batch_requests(
        self,
        requests: List[Dict[str, Any]],
        max_concurrency: int = 10,
        raise_exceptions: bool = False
    ) -> List[Union[httpx.Response, Exception]]:
        """
        Execute multiple HTTP requests concurrently with controlled concurrency

        Args:
            requests: List of request dictionaries with method, url, and other params
            max_concurrency: Maximum number of concurrent requests
            raise_exceptions: Whether to raise exceptions on failures

        Returns:
            List of responses or exceptions
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        results = []

        async def _execute_single_request(request_data):
            async with semaphore:
                try:
                    return await self.request(**request_data)
                except Exception as e:
                    if raise_exceptions:
                        raise
                    return e

        tasks = [_execute_single_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=not raise_exceptions)
        return results

    # Streaming operations
    async def stream_response(self, method: HttpMethod, url: str, **kwargs) -> AsyncGenerator[bytes, None]:
        """Stream response data"""
        async with self.client.stream(method.value, url, **kwargs) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk

    # Health check and metrics
    async def health_check(self, service_url: str = "https://httpbin.org/get") -> Dict[str, Any]:
        """Perform health check of HTTP client"""
        try:
            start_time = time.time()
            response = await self.get(service_url, timeout=5.0)
            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "response_time": response_time,
                "status_code": response.status_code,
                "circuit_breakers": {
                    name: cb.get_state()
                    for name, cb in self.circuit_breakers.items()
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breakers": {
                    name: cb.get_state()
                    for name, cb in self.circuit_breakers.items()
                }
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "timeout_requests": self.metrics.timeout_requests,
            "retries": self.metrics.retries,
            "success_rate": round(self.metrics.success_rate, 2),
            "error_rate": round(self.metrics.error_rate, 2),
            "average_response_time": round(self.metrics.average_response_time * 1000, 2),  # Convert to ms
            "last_response_time": round(self.metrics.last_response_time * 1000, 2),
            "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
            "circuit_breakers": {
                name: cb.get_state()
                for name, cb in self.circuit_breakers.items()
            }
        }

    def reset_metrics(self):
        """Reset client metrics"""
        self.metrics = HttpClientMetrics()
        for cb in self.circuit_breakers.values():
            cb.failure_count = 0
            cb.state = CircuitState.CLOSED

    @asynccontextmanager
    async def get_client(self):
        """Get httpx client for manual operations"""
        try:
            yield self.client
        except Exception as e:
            logger.error(f"HTTP client error: {e}")
            raise

    async def close(self):
        """Close HTTP client and cleanup resources"""
        try:
            await self.client.aclose()
            logger.info("HTTP client closed successfully")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")

# Global HTTP client instances for different services
http_clients: Dict[str, AsyncHttpClient] = {}

def get_http_client(service_name: str = "default", **kwargs) -> AsyncHttpClient:
    """Get or create HTTP client for a specific service"""
    if service_name not in http_clients:
        http_clients[service_name] = AsyncHttpClient(**kwargs)
    return http_clients[service_name]

# Initialize function
async def init_http_clients():
    """Initialize HTTP clients for external services"""
    try:
        # Initialize OANDA HTTP client
        oanda_client = get_http_client(
            "oanda",
            base_url=settings.OANDA_API_URL,
            timeout_config=TimeoutConfig(connect=15.0, read=60.0),
            retry_config=RetryConfig(max_attempts=5, base_delay=2.0),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=10,
                recovery_timeout=120.0
            )
        )

        # Initialize general API client
        api_client = get_http_client(
            "api",
            timeout_config=TimeoutConfig(connect=10.0, read=30.0),
            retry_config=RetryConfig(max_attempts=3),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60.0
            )
        )

        logger.info("HTTP clients initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize HTTP clients: {e}")
        return False

# Cleanup function
async def cleanup_http_clients():
    """Cleanup all HTTP clients"""
    for client in http_clients.values():
        await client.close()
    http_clients.clear()
    logger.info("HTTP clients cleaned up successfully")