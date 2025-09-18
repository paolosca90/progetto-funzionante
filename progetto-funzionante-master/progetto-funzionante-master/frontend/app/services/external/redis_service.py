"""
Redis Service with Dependency Injection Support

This service provides comprehensive Redis integration with:
- Connection pooling and management
- Cache operations
- Pub/Sub messaging
- Rate limiting
- Session management
- Performance monitoring
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union, Callable, AsyncContextManager
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import aioredis
from aioredis import Redis, ConnectionPool
from contextlib import asynccontextmanager

from ..core.config import Settings as CoreSettings
from ..core.dependency_injection import ServiceLifetime
from ..services.logging_service import LoggingService, LogContext, LogLevel
from ..services.config_service import ConfigService

logger = logging.getLogger(__name__)


class RedisConnectionError(Exception):
    """Redis connection error"""
    pass


class RedisOperationError(Exception):
    """Redis operation error"""
    pass


@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 10
    retry_on_timeout: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    health_check_interval: int = 30
    client_name: str = "ai_trading_system"


@dataclass
class RedisMetrics:
    """Redis performance metrics"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    connection_count: int = 0
    memory_usage: int = 0
    keyspace_hits: int = 0
    keyspace_misses: int = 0
    last_health_check: Optional[datetime] = None


class RedisService:
    """Enhanced Redis service with dependency injection support"""

    def __init__(self, settings: CoreSettings, logging_service: LoggingService, config_service: ConfigService):
        self.settings = settings
        self.logging_service = logging_service
        self.config_service = config_service

        # Redis components
        self.config: Optional[RedisConfig] = None
        self._redis: Optional[Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None
        self._pubsub: Optional[aioredis.PubSub] = None

        # Metrics
        self._metrics = RedisMetrics()
        self._response_times: List[float] = []
        self._max_response_times = 1000

        # Health monitoring
        self._healthy = False
        self._last_health_check = 0.0
        self._health_check_interval = 30.0  # 30 seconds

        # Subscriptions
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._subscription_task: Optional[asyncio.Task] = None

        # Initialize service
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Initialize Redis service"""
        try:
            # Load configuration
            self._load_config()

            # Create connection pool
            self._create_connection_pool()

            # Create Redis client
            self._create_redis_client()

            # Validate connection
            self._validate_connection()

            # Start health monitoring
            self._start_health_monitoring()

            logger.info("Redis service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis service: {e}")
            raise

    def _load_config(self) -> None:
        """Load Redis configuration"""
        redis_config = self.config_service.get_redis_config()

        url = redis_config.get('redis_url')
        if not url:
            raise ValueError("Redis URL not configured")

        self.config = RedisConfig(
            url=url,
            password=redis_config.get('redis_password'),
            db=redis_config.get('redis_db', 0),
            max_connections=redis_config.get('redis_max_connections', 10),
            retry_on_timeout=redis_config.get('redis_retry_on_timeout', True),
            socket_timeout=redis_config.get('redis_timeout', 5.0),
            socket_connect_timeout=redis_config.get('redis_timeout', 5.0),
            client_name="ai_trading_system"
        )

    def _create_connection_pool(self) -> None:
        """Create Redis connection pool"""
        if not self.config:
            raise RuntimeError("Redis configuration not loaded")

        try:
            self._connection_pool = ConnectionPool.from_url(
                self.config.url,
                db=self.config.db,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                client_name=self.config.client_name,
                health_check_interval=self.config.health_check_interval,
                decode_responses=True  # Automatically decode responses
            )

            logger.info(f"Redis connection pool created with {self.config.max_connections} connections")

        except Exception as e:
            logger.error(f"Failed to create Redis connection pool: {e}")
            raise

    def _create_redis_client(self) -> None:
        """Create Redis client"""
        if not self._connection_pool:
            raise RuntimeError("Redis connection pool not created")

        try:
            self._redis = Redis(connection_pool=self._connection_pool)
            logger.info("Redis client created successfully")

        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            raise

    def _validate_connection(self) -> None:
        """Validate Redis connection"""
        try:
            if not self._redis:
                raise RuntimeError("Redis client not created")

            # Test connection
            response = asyncio.run(self._redis.ping())
            if response:
                self._healthy = True
                self._last_health_check = time.time()
                logger.info("Redis connection validated successfully")
            else:
                raise RedisConnectionError("Redis ping failed")

        except Exception as e:
            self._healthy = False
            logger.error(f"Redis connection validation failed: {e}")
            raise

    def _start_health_monitoring(self) -> None:
        """Start health monitoring"""
        asyncio.create_task(self._health_monitor())

    async def _health_monitor(self) -> None:
        """Monitor Redis health"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._check_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Redis health monitor error: {e}")

    async def _check_health(self) -> None:
        """Check Redis health"""
        try:
            if not self._redis:
                self._healthy = False
                return

            # Perform health check
            start_time = time.time()
            await self._redis.ping()
            response_time = time.time() - start_time

            # Get Redis info
            info = await self._redis.info()

            # Update metrics
            self._metrics.last_health_check = datetime.now()
            self._metrics.memory_usage = int(info.get('used_memory', 0))
            self._metrics.keyspace_hits = int(info.get('keyspace_hits', 0))
            self._metrics.keyspace_misses = int(info.get('keyspace_misses', 0))

            self._healthy = True

        except Exception as e:
            self._healthy = False
            logger.error(f"Redis health check failed: {e}")

    # Basic Redis operations
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            value = await self._redis.get(key)
            self._metrics.successful_operations += 1

            # Try to parse JSON
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return None

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis GET operation failed: {e}")
            raise RedisOperationError(f"GET operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)

            if ttl:
                result = await self._redis.setex(key, ttl, value)
            else:
                result = await self._redis.set(key, value)

            self._metrics.successful_operations += 1
            return bool(result)

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis SET operation failed: {e}")
            raise RedisOperationError(f"SET operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            result = await self._redis.delete(key)
            self._metrics.successful_operations += 1
            return result > 0

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis DELETE operation failed: {e}")
            raise RedisOperationError(f"DELETE operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            result = await self._redis.exists(key)
            self._metrics.successful_operations += 1
            return bool(result)

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis EXISTS operation failed: {e}")
            raise RedisOperationError(f"EXISTS operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    # Advanced Redis operations
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field value"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            value = await self._redis.hget(key, field)
            self._metrics.successful_operations += 1

            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return None

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis HGET operation failed: {e}")
            raise RedisOperationError(f"HGET operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field value"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)

            result = await self._redis.hset(key, field, value)
            self._metrics.successful_operations += 1
            return True

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis HSET operation failed: {e}")
            raise RedisOperationError(f"HSET operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields and values"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            result = await self._redis.hgetall(key)
            self._metrics.successful_operations += 1

            # Try to parse JSON values
            parsed_result = {}
            for field, value in result.items():
                try:
                    parsed_result[field] = json.loads(value)
                except json.JSONDecodeError:
                    parsed_result[field] = value

            return parsed_result

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis HGETALL operation failed: {e}")
            raise RedisOperationError(f"HGETALL operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    # List operations
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            # Serialize values if they're not strings
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)

            result = await self._redis.lpush(key, *serialized_values)
            self._metrics.successful_operations += 1
            return result

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis LPUSH operation failed: {e}")
            raise RedisOperationError(f"LPUSH operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from the right of a list"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            value = await self._redis.rpop(key)
            self._metrics.successful_operations += 1

            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return None

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis RPOP operation failed: {e}")
            raise RedisOperationError(f"RPOP operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    # Set operations
    async def sadd(self, key: str, *values: Any) -> int:
        """Add values to a set"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            # Serialize values if they're not strings
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)

            result = await self._redis.sadd(key, *serialized_values)
            self._metrics.successful_operations += 1
            return result

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis SADD operation failed: {e}")
            raise RedisOperationError(f"SADD operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def smembers(self, key: str) -> List[Any]:
        """Get all members of a set"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            result = await self._redis.smembers(key)
            self._metrics.successful_operations += 1

            # Try to parse JSON values
            parsed_result = []
            for value in result:
                try:
                    parsed_result.append(json.loads(value))
                except json.JSONDecodeError:
                    parsed_result.append(value)

            return parsed_result

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis SMEMBERS operation failed: {e}")
            raise RedisOperationError(f"SMEMBERS operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    # Pub/Sub operations
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            # Serialize message if it's not a string
            if not isinstance(message, str):
                message = json.dumps(message)

            result = await self._redis.publish(channel, message)
            self._metrics.successful_operations += 1
            return result

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis PUBLISH operation failed: {e}")
            raise RedisOperationError(f"PUBLISH operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def subscribe(self, channel: str, callback: Callable[[str, Any], None]) -> None:
        """Subscribe to channel"""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []

        self._subscriptions[channel].append(callback)

        # Start subscription task if not already running
        if not self._subscription_task:
            self._subscription_task = asyncio.create_task(self._subscription_listener())

    async def unsubscribe(self, channel: str, callback: Callable) -> None:
        """Unsubscribe from channel"""
        if channel in self._subscriptions and callback in self._subscriptions[channel]:
            self._subscriptions[channel].remove(callback)

            # Remove channel if no more subscribers
            if not self._subscriptions[channel]:
                del self._subscriptions[channel]

    async def _subscription_listener(self) -> None:
        """Listen for subscription messages"""
        if not self._redis:
            return

        try:
            async with self._redis.pubsub() as pubsub:
                await pubsub.subscribe(*self._subscriptions.keys())

                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        channel = message['channel']
                        data = message['data']

                        # Try to parse JSON
                        try:
                            parsed_data = json.loads(data)
                        except json.JSONDecodeError:
                            parsed_data = data

                        # Notify callbacks
                        if channel in self._subscriptions:
                            for callback in self._subscriptions[channel]:
                                try:
                                    callback(channel, parsed_data)
                                except Exception as e:
                                    logger.error(f"Error in subscription callback: {e}")

        except Exception as e:
            logger.error(f"Redis subscription listener error: {e}")
        finally:
            self._subscription_task = None

    # Utility methods
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            result = await self._redis.keys(pattern)
            self._metrics.successful_operations += 1
            return result

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis KEYS operation failed: {e}")
            raise RedisOperationError(f"KEYS operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set key expiration"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            result = await self._redis.expire(key, ttl)
            self._metrics.successful_operations += 1
            return bool(result)

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis EXPIRE operation failed: {e}")
            raise RedisOperationError(f"EXPIRE operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    async def ttl(self, key: str) -> int:
        """Get key time to live"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        start_time = time.time()
        self._metrics.total_operations += 1

        try:
            result = await self._redis.ttl(key)
            self._metrics.successful_operations += 1
            return result

        except Exception as e:
            self._metrics.failed_operations += 1
            self.logging_service.log_error(f"Redis TTL operation failed: {e}")
            raise RedisOperationError(f"TTL operation failed: {e}")

        finally:
            self._update_response_time(time.time() - start_time)

    # Pipeline operations
    @asynccontextmanager
    async def pipeline(self) -> AsyncContextManager[aioredis.Redis]:
        """Create Redis pipeline"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        try:
            async with self._redis.pipeline() as pipe:
                yield pipe
        except Exception as e:
            logger.error(f"Redis pipeline error: {e}")
            raise

    # Metrics and monitoring
    def _update_response_time(self, response_time: float) -> None:
        """Update response time metrics"""
        self._response_times.append(response_time)
        if len(self._response_times) > self._max_response_times:
            self._response_times.pop(0)

        if self._response_times:
            self._metrics.average_response_time = sum(self._response_times) / len(self._response_times)

    def get_metrics(self) -> RedisMetrics:
        """Get Redis metrics"""
        return self._metrics

    def is_healthy(self) -> bool:
        """Check if Redis is healthy"""
        return self._healthy

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            if not self._redis:
                return {'status': 'unhealthy', 'error': 'Redis client not initialized'}

            # Test connection
            start_time = time.time()
            await self._redis.ping()
            response_time = time.time() - start_time

            # Get Redis info
            info = await self._redis.info()

            return {
                'status': 'healthy',
                'response_time': response_time,
                'memory_usage': int(info.get('used_memory', 0)),
                'connected_clients': int(info.get('connected_clients', 0)),
                'total_commands_processed': int(info.get('total_commands_processed', 0)),
                'keyspace_hits': int(info.get('keyspace_hits', 0)),
                'keyspace_misses': int(info.get('keyspace_misses', 0)),
                'uptime_seconds': int(info.get('uptime_in_seconds', 0)),
                'last_health_check': self._metrics.last_health_check.isoformat() if self._metrics.last_health_check else None
            }

        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache keys matching pattern"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")

        try:
            keys = await self._redis.keys(pattern)
            if keys:
                deleted = await self._redis.delete(*keys)
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Redis cache clear failed: {e}")
            raise RedisOperationError(f"Cache clear failed: {e}")

    async def __dispose__(self) -> None:
        """Dispose Redis service resources"""
        # Stop subscription listener
        if self._subscription_task:
            self._subscription_task.cancel()
            try:
                await self._subscription_task
            except asyncio.CancelledError:
                pass

        # Close Redis connection
        if self._redis:
            await self._redis.close()

        # Close connection pool
        if self._connection_pool:
            await self._connection_pool.disconnect()

        logger.info("Redis service disposed")


# Factory function for creating Redis service
async def create_redis_service(settings: CoreSettings,
                             logging_service: LoggingService,
                             config_service: ConfigService) -> RedisService:
    """Create and initialize Redis service"""
    service = RedisService(
        settings=settings,
        logging_service=logging_service,
        config_service=config_service
    )
    return service