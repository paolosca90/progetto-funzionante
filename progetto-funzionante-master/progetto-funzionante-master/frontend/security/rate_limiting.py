"""
Advanced Rate Limiting and DDoS Protection Framework
Production-ready rate limiting with multiple strategies
"""

import time
import asyncio
import hashlib
import json
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
import redis
import logging
import aiohttp
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"

class RateLimitType(Enum):
    """Types of rate limits"""
    IP_BASED = "ip_based"
    USER_BASED = "user_based"
    ENDPOINT_BASED = "endpoint_based"
    GLOBAL = "global"
    API_KEY_BASED = "api_key_based"

@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    name: str
    strategy: RateLimitStrategy
    limit_type: RateLimitType
    requests_per_window: int
    window_seconds: int
    burst_limit: Optional[int] = None
    enabled: bool = True
    priority: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RateLimitState:
    """Rate limit state tracking"""
    current_count: int
    window_start: float
    last_request_time: float
    tokens: float = 0.0
    is_limited: bool = False
    limit_exceeded_count: int = 0

class DDoSMitigation:
    """DDoS mitigation and detection"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.suspicious_ips: Dict[str, Dict[str, Any]] = {}
        self.traffic_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.ddos_thresholds = {
            'requests_per_second': 100,
            'concurrent_connections': 50,
            'error_rate': 0.1,  # 10% error rate
            'bandwidth_mbps': 10
        }

    async def analyze_request(self, request: Request) -> Tuple[bool, str]:
        """Analyze request for DDoS patterns"""
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        endpoint = str(request.url.path)

        # Check IP reputation
        if await self._is_suspicious_ip(client_ip):
            return False, "IP address flagged as suspicious"

        # Analyze traffic patterns
        if await self._detect_ddos_pattern(client_ip, endpoint):
            return False, "DDoS pattern detected"

        # Check rate limits
        if await self._check_global_limits(client_ip):
            return False, "Global rate limit exceeded"

        return True, "Request allowed"

    async def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP address is suspicious"""
        try:
            # Check if IP is in private ranges
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return False

            # Check against known bad IP ranges (simplified)
            bad_ranges = [
                ipaddress.ip_network("45.227.254.0/24"),  # Example bad range
                ipaddress.ip_network("185.220.100.0/24"),  # Example bad range
            ]

            for bad_range in bad_ranges:
                if ip_obj in bad_range:
                    return True

            # Check Redis for cached reputation
            if self.redis_client:
                reputation_key = f"ip_reputation:{ip}"
                reputation = await self.redis_client.get(reputation_key)
                if reputation and float(reputation) < 0.3:
                    return True

        except ValueError:
            return True  # Invalid IP format

        return False

    async def _detect_ddos_pattern(self, ip: str, endpoint: str) -> bool:
        """Detect DDoS traffic patterns"""
        now = time.time()
        pattern_key = f"pattern:{ip}:{endpoint}"

        # Track request timing
        if pattern_key not in self.traffic_patterns:
            self.traffic_patterns[pattern_key] = deque()

        self.traffic_patterns[pattern_key].append(now)

        # Keep only recent requests (last 60 seconds)
        cutoff = now - 60
        while self.traffic_patterns[pattern_key] and self.traffic_patterns[pattern_key][0] < cutoff:
            self.traffic_patterns[pattern_key].popleft()

        # Check for high frequency
        recent_requests = len(self.traffic_patterns[pattern_key])
        if recent_requests > self.ddos_thresholds['requests_per_second']:
            logger.warning(f"High request rate detected from {ip}: {recent_requests} requests in 60 seconds")
            return True

        # Check for timing patterns (regular intervals)
        if len(self.traffic_patterns[pattern_key]) > 10:
            intervals = []
            for i in range(1, len(self.traffic_patterns[pattern_key])):
                interval = self.traffic_patterns[pattern_key][i] - self.traffic_patterns[pattern_key][i-1]
                intervals.append(interval)

            # Check if requests are too regular (bot-like)
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)

                # Low variance suggests bot activity
                if variance < 0.01:  # Very regular intervals
                    logger.warning(f"Bot-like activity detected from {ip}")
                    return True

        return False

    async def _check_global_limits(self, ip: str) -> bool:
        """Check global rate limits"""
        if not self.redis_client:
            return False

        try:
            global_key = f"global_limit:{ip}"
            current = await self.redis_client.get(global_key)

            if current is None:
                await self.redis_client.setex(global_key, 60, 1)
            else:
                current_count = int(current)
                if current_count >= self.ddos_thresholds['requests_per_second']:
                    return True
                await self.redis_client.incr(global_key)

        except Exception as e:
            logger.error(f"Error checking global limits: {e}")

        return False

class TokenBucket:
    """Token bucket rate limiting algorithm"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from bucket"""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

class SlidingWindowCounter:
    """Sliding window rate limiting algorithm"""

    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # seconds
        self.max_requests = max_requests
        self.requests = deque()

    def add_request(self) -> bool:
        """Add a request to the window"""
        now = time.time()

        # Remove old requests
        cutoff = now - self.window_size
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        # Check limit
        if len(self.requests) >= self.max_requests:
            return False

        self.requests.append(now)
        return True

class AdaptiveRateLimiter:
    """Adaptive rate limiting based on system load and behavior"""

    def __init__(self, base_limits: Dict[str, int], redis_client: Optional[redis.Redis] = None):
        self.base_limits = base_limits
        self.redis_client = redis_client
        self.current_limits = base_limits.copy()
        self.system_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'active_connections': 0,
            'error_rate': 0.0
        }

    async def update_limits(self, metrics: Dict[str, float]):
        """Update rate limits based on system metrics"""
        self.system_metrics.update(metrics)

        # Adaptive logic
        if self.system_metrics['cpu_usage'] > 80:
            # Reduce limits when CPU is high
            for key in self.current_limits:
                self.current_limits[key] = int(self.base_limits[key] * 0.5)
        elif self.system_metrics['cpu_usage'] < 30:
            # Increase limits when system is healthy
            for key in self.current_limits:
                self.current_limits[key] = int(self.base_limits[key] * 1.2)
        else:
            # Normal limits
            self.current_limits = self.base_limits.copy()

    async def check_limit(self, key: str, weight: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed"""
        current_limit = self.current_limits.get(key, self.base_limits.get(key, 100))

        if not self.redis_client:
            return True, {"limit": current_limit, "remaining": current_limit}

        try:
            limit_key = f"adaptive_limit:{key}"
            current = await self.redis_client.get(limit_key)

            if current is None:
                await self.redis_client.setex(limit_key, 60, weight)
                remaining = current_limit - weight
            else:
                current_count = int(current)
                if current_count + weight > current_limit:
                    return False, {
                        "limit": current_limit,
                        "remaining": 0,
                        "reset_time": time.time() + 60
                    }
                await self.redis_client.incrby(limit_key, weight)
                remaining = current_limit - (current_count + weight)

            return True, {"limit": current_limit, "remaining": remaining}

        except Exception as e:
            logger.error(f"Error checking adaptive limit: {e}")
            return True, {"limit": current_limit, "remaining": current_limit}

class RateLimiter:
    """Main rate limiting system"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.ddos_mitigation = DDoSMitigation(redis_client)
        self.adaptive_limiter = AdaptiveRateLimiter(
            base_limits={
                'default': 1000,  # requests per hour
                'auth': 5,        # auth requests per minute
                'api': 100,       # API requests per minute
                'sensitive': 10   # sensitive operations per minute
            },
            redis_client=redis_client
        )

        # Default rate limiting rules
        self.rules = [
            RateLimitRule(
                name="global_ip_limit",
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit_type=RateLimitType.IP_BASED,
                requests_per_window=1000,
                window_seconds=3600  # 1 hour
            ),
            RateLimitRule(
                name="auth_limit",
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                limit_type=RateLimitType.USER_BASED,
                requests_per_window=5,
                window_seconds=60,  # 1 minute
                burst_limit=10
            ),
            RateLimitRule(
                name="api_limit",
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit_type=RateLimitType.ENDPOINT_BASED,
                requests_per_window=100,
                window_seconds=60  # 1 minute
            ),
            RateLimitRule(
                name="sensitive_operations",
                strategy=RateLimitStrategy.FIXED_WINDOW,
                limit_type=RateLimitType.USER_BASED,
                requests_per_window=10,
                window_seconds=60  # 1 minute
            )
        ]

        # Token buckets for IP-based limiting
        self.ip_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}

    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed based on rate limits"""
        client_ip = request.client.host
        endpoint = str(request.url.path)
        method = request.method

        # First, check DDoS mitigation
        ddos_allowed, ddos_reason = await self.ddos_mitigation.analyze_request(request)
        if not ddos_allowed:
            logger.warning(f"DDoS protection triggered for {client_ip}: {ddos_reason}")
            return False, {"error": ddos_reason, "type": "ddos_protection"}

        # Check all applicable rules
        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check rule conditions
            if not self._check_rule_conditions(rule, request, method, endpoint):
                continue

            # Generate limit key
            limit_key = self._generate_limit_key(rule, client_ip, user_id, api_key, endpoint)

            # Check limit based on strategy
            allowed, limit_info = await self._check_rule_limit(rule, limit_key, client_ip)

            if not allowed:
                logger.warning(f"Rate limit exceeded for {limit_key}: {rule.name}")
                return False, {
                    "error": "Rate limit exceeded",
                    "rule": rule.name,
                    "type": "rate_limit",
                    "limit_info": limit_info
                }

        # Check adaptive limits
        adaptive_key = self._get_adaptive_key(endpoint, method)
        adaptive_allowed, adaptive_info = await self.adaptive_limiter.check_limit(adaptive_key)

        if not adaptive_allowed:
            logger.warning(f"Adaptive rate limit exceeded for {adaptive_key}")
            return False, {
                "error": "Rate limit exceeded",
                "type": "adaptive_limit",
                "limit_info": adaptive_info
            }

        return True, {"message": "Request allowed"}

    def _check_rule_conditions(self, rule: RateLimitRule, request: Request, method: str, endpoint: str) -> bool:
        """Check if rule conditions are met"""
        conditions = rule.conditions

        # Method condition
        if 'methods' in conditions:
            if method not in conditions['methods']:
                return False

        # Endpoint pattern condition
        if 'endpoint_patterns' in conditions:
            patterns = conditions['endpoint_patterns']
            if not any(pattern in endpoint for pattern in patterns):
                return False

        # User agent condition
        if 'user_agents' in conditions:
            user_agent = request.headers.get("user-agent", "")
            if not any(agent in user_agent for agent in conditions['user_agents']):
                return False

        return True

    def _generate_limit_key(
        self,
        rule: RateLimitRule,
        client_ip: str,
        user_id: Optional[str],
        api_key: Optional[str],
        endpoint: str
    ) -> str:
        """Generate rate limit key based on rule type"""
        if rule.limit_type == RateLimitType.IP_BASED:
            return f"rate_limit:{rule.name}:ip:{client_ip}"
        elif rule.limit_type == RateLimitType.USER_BASED and user_id:
            return f"rate_limit:{rule.name}:user:{user_id}"
        elif rule.limit_type == RateLimitType.API_KEY_BASED and api_key:
            return f"rate_limit:{rule.name}:api_key:{api_key}"
        elif rule.limit_type == RateLimitType.ENDPOINT_BASED:
            return f"rate_limit:{rule.name}:endpoint:{endpoint}"
        elif rule.limit_type == RateLimitType.GLOBAL:
            return f"rate_limit:{rule.name}:global"
        else:
            return f"rate_limit:{rule.name}:default"

    def _get_adaptive_key(self, endpoint: str, method: str) -> str:
        """Get adaptive limit key based on endpoint"""
        if endpoint.startswith("/auth"):
            return "auth"
        elif endpoint.startswith("/api/"):
            return "api"
        elif any(sensitive in endpoint for sensitive in ["/admin", "/settings", "/profile"]):
            return "sensitive"
        else:
            return "default"

    async def _check_rule_limit(
        self,
        rule: RateLimitRule,
        limit_key: str,
        client_ip: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check specific rule limit"""
        if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._check_token_bucket_limit(rule, limit_key, client_ip)
        elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._check_sliding_window_limit(rule, limit_key)
        elif rule.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._check_fixed_window_limit(rule, limit_key)
        else:
            return True, {}

    async def _check_token_bucket_limit(
        self,
        rule: RateLimitRule,
        limit_key: str,
        client_ip: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check token bucket limit"""
        if limit_key not in self.ip_buckets:
            self.ip_buckets[limit_key] = TokenBucket(
                capacity=rule.requests_per_window,
                refill_rate=rule.requests_per_window / rule.window_seconds
            )

        bucket = self.ip_buckets[limit_key]
        allowed = bucket.consume()

        if not allowed:
            return False, {
                "limit": rule.requests_per_window,
                "remaining": 0,
                "reset_time": time.time() + rule.window_seconds,
                "strategy": "token_bucket"
            }

        return True, {
            "limit": rule.requests_per_window,
            "remaining": int(bucket.tokens),
            "strategy": "token_bucket"
        }

    async def _check_sliding_window_limit(
        self,
        rule: RateLimitRule,
        limit_key: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check sliding window limit"""
        if limit_key not in self.sliding_windows:
            self.sliding_windows[limit_key] = SlidingWindowCounter(
                window_size=rule.window_seconds,
                max_requests=rule.requests_per_window
            )

        window = self.sliding_windows[limit_key]
        allowed = window.add_request()

        if not allowed:
            return False, {
                "limit": rule.requests_per_window,
                "remaining": 0,
                "reset_time": time.time() + rule.window_seconds,
                "strategy": "sliding_window"
            }

        return True, {
            "limit": rule.requests_per_window,
            "remaining": rule.requests_per_window - len(window.requests),
            "strategy": "sliding_window"
        }

    async def _check_fixed_window_limit(
        self,
        rule: RateLimitRule,
        limit_key: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check fixed window limit"""
        if not self.redis_client:
            return True, {}

        try:
            now = int(time.time())
            window_start = (now // rule.window_seconds) * rule.window_seconds
            window_key = f"{limit_key}:{window_start}"

            current = await self.redis_client.get(window_key)
            if current is None:
                await self.redis_client.setex(window_key, rule.window_seconds, 1)
                remaining = rule.requests_per_window - 1
            else:
                current_count = int(current)
                if current_count >= rule.requests_per_window:
                    return False, {
                        "limit": rule.requests_per_window,
                        "remaining": 0,
                        "reset_time": window_start + rule.window_seconds,
                        "strategy": "fixed_window"
                    }
                await self.redis_client.incr(window_key)
                remaining = rule.requests_per_window - (current_count + 1)

            return True, {
                "limit": rule.requests_per_window,
                "remaining": remaining,
                "reset_time": window_start + rule.window_seconds,
                "strategy": "fixed_window"
            }

        except Exception as e:
            logger.error(f"Error checking fixed window limit: {e}")
            return True, {}

    def add_rule(self, rule: RateLimitRule):
        """Add a new rate limiting rule"""
        self.rules.append(rule)
        # Sort by priority
        self.rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_name: str):
        """Remove a rate limiting rule"""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def get_limit_info(self, limit_key: str) -> Dict[str, Any]:
        """Get current limit information"""
        info = {}

        # Check token bucket
        if limit_key in self.ip_buckets:
            bucket = self.ip_buckets[limit_key]
            info["token_bucket"] = {
                "tokens": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate
            }

        # Check sliding window
        if limit_key in self.sliding_windows:
            window = self.sliding_windows[limit_key]
            info["sliding_window"] = {
                "current_count": len(window.requests),
                "max_requests": window.max_requests,
                "window_size": window.window_size
            }

        return info

    async def cleanup_expired_limits(self):
        """Clean up expired limit data"""
        now = time.time()

        # Clean up old token buckets
        expired_buckets = []
        for key, bucket in self.ip_buckets.items():
            if now - bucket.last_refill > 3600:  # 1 hour inactive
                expired_buckets.append(key)

        for key in expired_buckets:
            del self.ip_buckets[key]

        # Clean up old sliding windows
        expired_windows = []
        for key, window in self.sliding_windows.items():
            if window.requests and now - window.requests[-1] > 3600:  # 1 hour inactive
                expired_windows.append(key)

        for key in expired_windows:
            del self.sliding_windows[key]

# FastAPI middleware for rate limiting
class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, limiter: RateLimiter):
        self.limiter = limiter

    async def __call__(self, request: Request, call_next):
        # Extract user information (would need to be implemented based on auth system)
        user_id = request.headers.get("X-User-ID")
        api_key = request.headers.get("X-API-Key")

        # Check rate limits
        allowed, limit_info = await self.limiter.check_rate_limit(request, user_id, api_key)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": limit_info.get("error", "Rate limit exceeded"),
                    "limit_info": limit_info,
                    "retry_after": limit_info.get("reset_time", time.time() + 60) - time.time()
                },
                headers={
                    "X-RateLimit-Limit": str(limit_info.get("limit", 0)),
                    "X-RateLimit-Remaining": str(limit_info.get("remaining", 0)),
                    "X-RateLimit-Reset": str(int(limit_info.get("reset_time", time.time() + 60))),
                    "Retry-After": str(int(limit_info.get("reset_time", time.time() + 60) - time.time()))
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add rate limit headers
        if "limit_info" in limit_info:
            response.headers["X-RateLimit-Limit"] = str(limit_info["limit_info"].get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = str(limit_info["limit_info"].get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(int(limit_info["limit_info"].get("reset_time", time.time() + 60)))

        return response

# Decorator for rate limiting endpoints
def rate_limit(
    requests: int,
    window_seconds: int,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    limit_type: RateLimitType = RateLimitType.ENDPOINT_BASED
):
    """Decorator for rate limiting specific endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would need to be integrated with the rate limiting system
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Global rate limiter instance
rate_limiter = RateLimiter()

# Create middleware instance
rate_limit_middleware = RateLimitMiddleware(rate_limiter)