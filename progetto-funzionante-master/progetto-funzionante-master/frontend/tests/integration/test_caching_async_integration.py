"""
Comprehensive integration tests for caching and async operations.
Tests cache service, async database operations, concurrent processing, and performance optimization.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional
from fastapi.testclient import TestClient
import httpx
import redis
from concurrent.futures import ThreadPoolExecutor

from models import User, Signal, SignalStatusEnum, SignalTypeEnum
from app.services.cache_service import CacheService
from app.services.signal_service import SignalService
from app.services.async_database import AsyncDatabaseManager
from app.services.async_http_client import AsyncHTTPClient
from app.services.async_file_service import AsyncFileService
from app.services.async_task_scheduler import AsyncTaskScheduler


class TestCachingAsyncIntegration:
    """Integration test suite for caching and async operations."""

    # Cache Service Tests
    def test_cache_basic_operations(self):
        """Test basic cache service operations."""
        cache_service = CacheService()

        # Test cache set and get
        test_data = {"key": "value", "timestamp": datetime.utcnow().isoformat()}
        result = cache_service.set("test_key", test_data, ttl=60)
        assert result is True

        retrieved_data = cache_service.get("test_key")
        assert retrieved_data == test_data

        # Test cache exists
        assert cache_service.exists("test_key") is True

        # Test cache delete
        result = cache_service.delete("test_key")
        assert result is True

        assert cache_service.exists("test_key") is False
        assert cache_service.get("test_key") is None

    def test_cache_ttl_functionality(self):
        """Test cache time-to-live functionality."""
        cache_service = CacheService()

        # Test short TTL
        cache_service.set("short_ttl", "test_value", ttl=1)

        # Should be available immediately
        assert cache_service.get("short_ttl") == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache_service.get("short_ttl") is None

        # Test long TTL
        cache_service.set("long_ttl", "test_value", ttl=60)

        # Should still be available
        assert cache_service.get("long_ttl") == "test_value"

    def test_cache_batch_operations(self):
        """Test cache batch operations."""
        cache_service = CacheService()

        # Test batch set
        batch_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        result = cache_service.set_many(batch_data, ttl=60)
        assert result is True

        # Test batch get
        retrieved_data = cache_service.get_many(["key1", "key2", "key3", "key4"])
        expected = {"key1": "value1", "key2": "value2", "key3": "value3"}
        assert retrieved_data == expected

        # Test batch delete
        result = cache_service.delete_many(["key1", "key2"])
        assert result is True

        # Verify deletion
        remaining = cache_service.get_many(["key1", "key2", "key3"])
        assert remaining == {"key3": "value3"}

    def test_cache_pattern_operations(self):
        """Test cache pattern-based operations."""
        cache_service = CacheService()

        # Set keys with patterns
        pattern_keys = [
            "signal:EUR_USD:1",
            "signal:EUR_USD:2",
            "signal:GBP_USD:1",
            "user:1:profile",
            "user:1:settings"
        ]

        for key in pattern_keys:
            cache_service.set(key, f"value_for_{key}", ttl=60)

        # Test pattern deletion
        deleted_count = cache_service.delete_pattern("signal:EUR_USD:*")
        assert deleted_count == 2

        # Verify deletion
        remaining_keys = cache_service.get_many(pattern_keys)
        assert len(remaining_keys) == 3  # Only GBP_USD and user keys remain

        # Test pattern retrieval
        matching_keys = cache_service.get_keys("signal:*")
        assert len(matching_keys) == 1  # Only GBP_USD signal remains

    def test_cache_statistics(self):
        """Test cache statistics and metrics."""
        cache_service = CacheService()

        # Perform some operations
        cache_service.set("stats_test", "value", ttl=60)
        cache_service.get("stats_test")  # Hit
        cache_service.get("nonexistent")  # Miss
        cache_service.delete("stats_test")
        cache_service.get("stats_test")  # Miss

        stats = cache_service.get_statistics()
        assert "hits" in stats
        assert "misses" in stats
        assert "total_operations" in stats
        assert "hit_rate" in stats

        # Verify statistics
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["total_operations"] == 3
        assert stats["hit_rate"] == 1/3

    def test_cache_error_handling(self):
        """Test cache service error handling."""
        cache_service = CacheService()

        # Test with invalid TTL
        result = cache_service.set("invalid_ttl", "value", ttl=-1)
        assert result is False

        # Test with None key
        result = cache_service.get(None)
        assert result is None

        # Test with empty key
        result = cache_service.get("")
        assert result is None

    # Async Database Tests
    def test_async_database_operations(self, db_session):
        """Test async database operations."""
        async_db_manager = AsyncDatabaseManager()

        # Test async query
        async def test_query():
            result = await async_db_manager.execute_query(
                "SELECT COUNT(*) as count FROM users"
            )
            return result

        result = asyncio.run(test_query())
        assert isinstance(result, list)

    def test_async_transaction_management(self, db_session):
        """Test async transaction management."""
        async_db_manager = AsyncDatabaseManager()

        async def test_transaction():
            async with async_db_manager.transaction():
                # Execute queries within transaction
                result1 = await async_db_manager.execute_query(
                    "SELECT COUNT(*) as count FROM signals"
                )
                result2 = await async_db_manager.execute_query(
                    "SELECT COUNT(*) as count FROM users"
                )
                return result1, result2

        result1, result2 = asyncio.run(test_transaction())
        assert isinstance(result1, list)
        assert isinstance(result2, list)

    # Async HTTP Client Tests
    def test_async_http_client_operations(self):
        """Test async HTTP client operations."""
        http_client = AsyncHTTPClient()

        mock_response_data = {"message": "success", "data": [1, 2, 3]}

        async def test_get_request():
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_response_data)

                result = await http_client.get("https://api.example.com/test")
                return result

        result = asyncio.run(test_get_request())
        assert result == mock_response_data

    def test_async_http_concurrent_requests(self):
        """Test concurrent async HTTP requests."""
        http_client = AsyncHTTPClient()

        mock_response_data = {"result": "success"}

        async def make_request(url):
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_response_data)

                result = await http_client.get(url)
                return result

        async def test_concurrent_requests():
            urls = [f"https://api.example.com/endpoint{i}" for i in range(5)]
            tasks = [make_request(url) for url in urls]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(test_concurrent_requests())
        assert len(results) == 5
        assert all(result == mock_response_data for result in results)

    def test_async_http_error_handling(self):
        """Test async HTTP client error handling."""
        http_client = AsyncHTTPClient()

        async def test_error_handling():
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.side_effect = httpx.RequestError("Network error")

                result = await http_client.get("https://api.example.com/test")
                return result

        result = asyncio.run(test_error_handling())
        assert "error" in result

    # Async File Service Tests
    def test_async_file_operations(self):
        """Test async file operations."""
        file_service = AsyncFileService()

        test_content = "Test file content"
        test_filename = "test_async_file.txt"

        async def test_file_operations():
            # Test async file write
            write_result = await file_service.write_file_async(test_filename, test_content)
            assert write_result is True

            # Test async file read
            read_result = await file_service.read_file_async(test_filename)
            assert read_result == test_content

            # Test async file delete
            delete_result = await file_service.delete_file_async(test_filename)
            assert delete_result is True

            return True

        result = asyncio.run(test_file_operations())
        assert result is True

    # Async Task Scheduler Tests
    def test_async_task_scheduler(self):
        """Test async task scheduler."""
        scheduler = AsyncTaskScheduler()

        executed_tasks = []

        async def sample_task(task_id):
            executed_tasks.append(task_id)
            return f"Task {task_id} completed"

        async def test_scheduler():
            # Schedule tasks
            task_ids = [f"task_{i}" for i in range(3)]

            for task_id in task_ids:
                await scheduler.schedule_task(
                    sample_task,
                    task_id,
                    delay=0.1
                )

            # Wait for tasks to complete
            await asyncio.sleep(0.5)

            return len(executed_tasks)

        completed_count = asyncio.run(test_scheduler())
        assert completed_count == 3
        assert len(executed_tasks) == 3

    # Integration Tests: Cache with Services
    def test_signal_service_with_cache(self, db_session, mock_cache_service: AsyncMock):
        """Test signal service with cache integration."""
        with patch('app.services.signal_service.cache_service', mock_cache_service):
            signal_service = SignalService(db_session)

            # First call should hit database and cache result
            mock_cache_service.get_cached_signals.return_value = None
            mock_cache_service.cache_signals.return_value = True

            signals = signal_service.get_latest_signals(10)

            # Verify cache was called
            mock_cache_service.get_cached_signals.assert_called_once()
            mock_cache_service.cache_signals.assert_called_once()

    def test_cache_invalidation_on_signal_update(self, db_session, mock_cache_service: AsyncMock):
        """Test cache invalidation on signal update."""
        with patch('app.services.signal_service.cache_service', mock_cache_service):
            signal_service = SignalService(db_session)

            # Update signal status
            mock_cache_service.invalidate_signals_cache.return_value = True

            signal_service.update_signal_status(1, SignalStatusEnum.CLOSED)

            # Verify cache was invalidated
            mock_cache_service.invalidate_signals_cache.assert_called_once()

    # Concurrent Access Tests
    def test_concurrent_cache_access(self):
        """Test concurrent cache access."""
        cache_service = CacheService()
        results = []

        def cache_worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"

                # Set value
                cache_service.set(key, value, ttl=60)

                # Get value
                retrieved = cache_service.get(key)
                results.append(retrieved == value)

        # Run multiple workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)
        assert len(results) == 50  # 5 workers * 10 operations each

    def test_concurrent_async_operations(self):
        """Test concurrent async operations."""
        async_db_manager = AsyncDatabaseManager()

        async def concurrent_queries():
            queries = [
                "SELECT COUNT(*) as count FROM users",
                "SELECT COUNT(*) as count FROM signals",
                "SELECT COUNT(*) as count FROM oanda_connections"
            ]

            tasks = [async_db_manager.execute_query(query) for query in queries]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(concurrent_queries())
        assert len(results) == 3
        assert all(isinstance(result, list) for result in results)

    # Performance Tests
    def test_cache_performance_benchmark(self):
        """Test cache performance benchmark."""
        cache_service = CacheService()

        # Benchmark cache operations
        iterations = 1000

        start_time = time.time()
        for i in range(iterations):
            key = f"benchmark_key_{i}"
            value = f"benchmark_value_{i}"
            cache_service.set(key, value, ttl=60)
        set_time = time.time() - start_time

        start_time = time.time()
        for i in range(iterations):
            key = f"benchmark_key_{i}"
            cache_service.get(key)
        get_time = time.time() - start_time

        print(f"\nCache Performance Benchmark:")
        print(f"  Set operations: {iterations} in {set_time:.3f}s ({iterations/set_time:.0f} ops/sec)")
        print(f"  Get operations: {iterations} in {get_time:.3f}s ({iterations/get_time:.0f} ops/sec)")

        # Performance assertions
        assert set_time < 1.0, f"Cache set performance too slow: {set_time:.3f}s"
        assert get_time < 0.5, f"Cache get performance too slow: {get_time:.3f}s"

    def test_async_performance_benchmark(self):
        """Test async operations performance benchmark."""
        http_client = AsyncHTTPClient()

        async def benchmark_async_requests():
            mock_response = {"result": "success"}

            start_time = time.time()

            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_response)

                tasks = []
                for i in range(100):
                    task = http_client.get(f"https://api.example.com/endpoint{i}")
                    tasks.append(task)

                results = await asyncio.gather(*tasks)

            end_time = time.time()
            return end_time - start_time, len(results)

        execution_time, result_count = asyncio.run(benchmark_async_requests())

        print(f"\nAsync Performance Benchmark:")
        print(f"  {result_count} requests in {execution_time:.3f}s ({result_count/execution_time:.0f} req/sec)")

        # Performance assertions
        assert execution_time < 2.0, f"Async performance too slow: {execution_time:.3f}s"
        assert result_count == 100

    # Memory and Resource Management Tests
    def test_cache_memory_management(self):
        """Test cache memory management."""
        cache_service = CacheService()

        # Add large amount of data
        large_data = {"data": "x" * 1024 * 1024}  # 1MB data

        for i in range(100):
            key = f"large_data_{i}"
            cache_service.set(key, large_data, ttl=60)

        # Verify cache still functions
        assert cache_service.get("large_data_0") == large_data

        # Clear cache
        cache_service.clear()
        assert cache_service.get("large_data_0") is None

    def test_async_resource_cleanup(self):
        """Test async resource cleanup."""
        async_db_manager = AsyncDatabaseManager()
        http_client = AsyncHTTPClient()

        async def test_cleanup():
            # Use resources
            await async_db_manager.execute_query("SELECT 1")

            with patch('httpx.AsyncClient.get'):
                await http_client.get("https://api.example.com/test")

            # Cleanup should happen automatically
            return True

        result = asyncio.run(test_cleanup())
        assert result is True

    # Cache-Database Integration Tests
    def test_cached_database_queries(self, db_session, multiple_signals_fixture: List[Signal]):
        """Test cached database query integration."""
        cache_service = CacheService()
        signal_service = SignalService(db_session)

        # Mock cache integration
        cache_key = f"signals:latest:10"

        # First call - database query
        start_time = time.time()
        signals1 = signal_service.get_latest_signals(10)
        db_time = time.time() - start_time

        # Cache the result
        cache_service.set(cache_key, signals1, ttl=60)

        # Second call - cache hit
        start_time = time.time()
        signals2 = cache_service.get(cache_key)
        cache_time = time.time() - start_time

        print(f"\nCache vs Database Performance:")
        print(f"  Database query: {db_time:.3f}s")
        print(f"  Cache retrieval: {cache_time:.3f}s")
        print(f"  Speedup: {db_time/cache_time:.1f}x")

        # Verify cache is faster
        assert cache_time < db_time, "Cache should be faster than database"
        assert signals2 == signals1, "Cached data should match database data"

    # Async Error Recovery Tests
    def test_async_error_recovery(self):
        """Test async operation error recovery."""
        http_client = AsyncHTTPClient()

        async def test_error_recovery():
            # First call fails
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.side_effect = httpx.RequestError("Network error")

                result1 = await http_client.get("https://api.example.com/test")
                assert "error" in result1

            # Second call succeeds
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json={"result": "success"})

                result2 = await http_client.get("https://api.example.com/test")
                assert result2 == {"result": "success"}

            return True

        result = asyncio.run(test_error_recovery())
        assert result is True

    # Integration with External Services
    def test_cache_with_external_api(self):
        """Test cache integration with external API calls."""
        cache_service = CacheService()
        http_client = AsyncHTTPClient()

        mock_api_response = {"data": "external_api_data"}

        async def test_cached_api_call():
            cache_key = "external_api:test_endpoint"

            # First call - API request
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_api_response)

                result1 = await http_client.get("https://api.example.com/test")
                cache_service.set(cache_key, result1, ttl=60)

            # Second call - cache hit
            result2 = cache_service.get(cache_key)

            # Third call - API request (cache expired)
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_api_response)

                result3 = await http_client.get("https://api.example.com/test")

            return result1, result2, result3

        result1, result2, result3 = asyncio.run(test_cached_api_call())

        assert result1 == mock_api_response
        assert result2 == mock_api_response
        assert result3 == mock_api_response

    # Load Testing for Async Operations
    def test_async_load_testing(self):
        """Test async operations under load."""
        http_client = AsyncHTTPClient()

        async def load_test():
            mock_response = {"result": "success"}

            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_response)

                # Create many concurrent requests
                tasks = []
                for i in range(100):
                    task = http_client.get(f"https://api.example.com/endpoint{i}")
                    tasks.append(task)

                start_time = time.time()
                results = await asyncio.gather(*tasks)
                end_time = time.time()

            return end_time - start_time, len(results)

        execution_time, result_count = asyncio.run(load_test())

        print(f"\nAsync Load Test:")
        print(f"  {result_count} concurrent requests in {execution_time:.3f}s")
        print(f"  Throughput: {result_count/execution_time:.0f} req/sec")

        # Performance assertions
        assert execution_time < 3.0, f"Async load test too slow: {execution_time:.3f}s"
        assert result_count == 100

    # Cache Expiration and Cleanup Tests
    def test_cache_expiration_cleanup(self):
        """Test cache expiration and cleanup."""
        cache_service = CacheService()

        # Set keys with different TTLs
        cache_service.set("short_term", "value1", ttl=1)
        cache_service.set("medium_term", "value2", ttl=5)
        cache_service.set("long_term", "value3", ttl=60)

        # Wait for short term to expire
        time.sleep(1.1)

        # Verify expiration
        assert cache_service.get("short_term") is None
        assert cache_service.get("medium_term") == "value2"
        assert cache_service.get("long_term") == "value3"

        # Test cleanup of expired keys
        cleaned_count = cache_service.cleanup_expired()
        assert cleaned_count >= 1

    # Async Timeout Handling
    def test_async_timeout_handling(self):
        """Test async operation timeout handling."""
        http_client = AsyncHTTPClient()

        async def test_timeout():
            # Simulate slow response
            async def slow_response():
                await asyncio.sleep(2)
                return {"result": "slow_success"}

            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = asyncio.create_task(slow_response())

                # This should timeout
                result = await asyncio.wait_for(
                    http_client.get("https://api.example.com/slow"),
                    timeout=0.5
                )

            return result

        # Should raise timeout error
        with pytest.raises(asyncio.TimeoutError):
            asyncio.run(test_timeout())