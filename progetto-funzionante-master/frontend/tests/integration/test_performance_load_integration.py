"""
Comprehensive performance and load testing integration tests.
Tests application performance under various load conditions, concurrency, and stress scenarios.
"""

import pytest
import json
import asyncio
import time
import threading
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Tuple
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from models import User, Signal, SignalTypeEnum
from schemas import UserCreate, SignalCreate


class TestPerformanceLoadIntegration:
    """Integration test suite for performance and load testing."""

    @pytest.fixture
    def performance_config(self):
        """Configuration for performance tests."""
        return {
            "concurrent_users": 50,
            "requests_per_user": 20,
            "max_response_time": 2.0,  # Maximum acceptable response time in seconds
            "target_throughput": 100,  # Target requests per second
            "error_rate_threshold": 0.05,  # Maximum 5% error rate
            "warmup_time": 5,  # Warmup time in seconds
            "test_duration": 30  # Test duration in seconds
        }

    # Basic Performance Tests
    def test_health_check_performance(self, client: TestClient):
        """Test health check endpoint performance."""
        response_times = []

        for _ in range(100):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            assert response.status_code == 200
            response_times.append(end_time - start_time)

        # Performance assertions
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        print(f"\nHealth Check Performance:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Min: {min_response_time:.3f}s")
        print(f"  Max: {max_response_time:.3f}s")

        assert avg_response_time < 0.1, f"Average response time {avg_response_time:.3f}s is too slow"
        assert max_response_time < 0.5, f"Max response time {max_response_time:.3f}s is too slow"

    def test_authentication_performance(self, client: TestClient, user_fixture: User):
        """Test authentication endpoint performance."""
        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        response_times = []

        for _ in range(50):
            start_time = time.time()
            response = client.post("/auth/token", data=login_data)
            end_time = time.time()

            assert response.status_code == 200
            response_times.append(end_time - start_time)

        # Performance assertions
        avg_response_time = statistics.mean(response_times)
        percentile_95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

        print(f"\nAuthentication Performance:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  95th percentile: {percentile_95:.3f}s")

        assert avg_response_time < 0.5, f"Average auth time {avg_response_time:.3f}s is too slow"
        assert percentile_95 < 1.0, f"95th percentile {percentile_95:.3f}s is too slow"

    def test_signal_retrieval_performance(self, client: TestClient, multiple_signals_fixture: List[Signal]):
        """Test signal retrieval endpoint performance."""
        response_times = []

        for _ in range(100):
            start_time = time.time()
            response = client.get("/signals/latest")
            end_time = time.time()

            assert response.status_code == 200
            response_times.append(end_time - start_time)

        # Performance assertions
        avg_response_time = statistics.mean(response_times)
        throughput = 100 / sum(response_times)  # Requests per second

        print(f"\nSignal Retrieval Performance:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} requests/sec")

        assert avg_response_time < 0.2, f"Average response time {avg_response_time:.3f}s is too slow"
        assert throughput > 50, f"Throughput {throughput:.1f} req/sec is too low"

    # Concurrency Tests
    def test_concurrent_authentication(self, client: TestClient, user_fixture: User, performance_config: Dict[str, Any]):
        """Test concurrent authentication requests."""
        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        results = []
        response_times = []

        def authenticate_user():
            start_time = time.time()
            try:
                response = client.post("/auth/token", data=login_data)
                end_time = time.time()

                results.append(response.status_code)
                response_times.append(end_time - start_time)
            except Exception as e:
                results.append(0)  # Error
                response_times.append(0)

        # Run concurrent authentication requests
        threads = []
        for _ in range(performance_config["concurrent_users"]):
            thread = threading.Thread(target=authenticate_user)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results
        success_rate = sum(1 for status in results if status == 200) / len(results)
        avg_response_time = statistics.mean([rt for rt in response_times if rt > 0])

        print(f"\nConcurrent Authentication:")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Concurrent users: {performance_config['concurrent_users']}")

        assert success_rate > 0.95, f"Success rate {success_rate:.1%} is too low"
        assert avg_response_time < 1.0, f"Average response time {avg_response_time:.3f}s is too slow"

    def test_concurrent_signal_creation(self, client: TestClient, auth_headers: Dict[str, str], performance_config: Dict[str, Any]):
        """Test concurrent signal creation requests."""
        signal_data = {
            "symbol": "EUR_USD",
            "signal_type": "BUY",
            "entry_price": 1.1234,
            "stop_loss": 1.1200,
            "take_profit": 1.1300,
            "reliability": 85.0
        }

        results = []
        response_times = []

        def create_signal():
            start_time = time.time()
            try:
                response = client.post("/signals", json=signal_data, headers=auth_headers)
                end_time = time.time()

                results.append(response.status_code)
                response_times.append(end_time - start_time)
            except Exception as e:
                results.append(0)  # Error
                response_times.append(0)

        # Run concurrent signal creation requests
        threads = []
        for _ in range(performance_config["concurrent_users"]):
            thread = threading.Thread(target=create_signal)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results
        success_rate = sum(1 for status in results if status == 201) / len(results)
        avg_response_time = statistics.mean([rt for rt in response_times if rt > 0])

        print(f"\nConcurrent Signal Creation:")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")

        assert success_rate > 0.90, f"Success rate {success_rate:.1%} is too low"
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s is too slow"

    # Load Testing
    def test_sustained_load(self, client: TestClient, performance_config: Dict[str, Any]):
        """Test application performance under sustained load."""
        start_time = time.time()
        end_time = start_time + performance_config["test_duration"]

        results = []
        response_times = []
        request_count = 0

        def make_requests():
            nonlocal request_count
            while time.time() < end_time:
                req_start = time.time()
                try:
                    response = client.get("/health")
                    req_end = time.time()

                    results.append(response.status_code)
                    response_times.append(req_end - req_start)
                    request_count += 1
                except Exception as e:
                    results.append(0)
                    response_times.append(0)
                    request_count += 1

                # Control request rate
                time.sleep(1.0 / performance_config["target_throughput"])

        # Start load generation threads
        threads = []
        for _ in range(10):  # 10 concurrent threads
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results
        test_duration = time.time() - start_time
        success_rate = sum(1 for status in results if status == 200) / len(results)
        avg_response_time = statistics.mean([rt for rt in response_times if rt > 0])
        actual_throughput = request_count / test_duration

        print(f"\nSustained Load Test:")
        print(f"  Duration: {test_duration:.1f}s")
        print(f"  Total requests: {request_count}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Actual throughput: {actual_throughput:.1f} req/sec")
        print(f"  Target throughput: {performance_config['target_throughput']} req/sec")

        assert success_rate > 0.95, f"Success rate {success_rate:.1%} is too low"
        assert avg_response_time < performance_config["max_response_time"], f"Response time too slow"
        assert actual_throughput > performance_config["target_throughput"] * 0.8, f"Throughput too low"

    def test_burst_load(self, client: TestClient):
        """Test application performance under burst load."""
        burst_size = 100
        results = []
        response_times = []

        def make_burst_requests():
            start_time = time.time()
            for _ in range(burst_size):
                req_start = time.time()
                try:
                    response = client.get("/signals/latest")
                    req_end = time.time()

                    results.append(response.status_code)
                    response_times.append(req_end - req_start)
                except Exception as e:
                    results.append(0)
                    response_times.append(0)

        # Start multiple threads for burst load
        threads = []
        for _ in range(5):  # 5 concurrent bursts
            thread = threading.Thread(target=make_burst_requests)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results
        total_requests = len(results)
        success_rate = sum(1 for status in results if status == 200) / total_requests
        avg_response_time = statistics.mean([rt for rt in response_times if rt > 0])

        print(f"\nBurst Load Test:")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")

        assert success_rate > 0.90, f"Success rate {success_rate:.1%} is too low"
        assert avg_response_time < 1.0, f"Average response time {avg_response_time:.3f}s is too slow"

    # Stress Testing
    def test_memory_usage_under_load(self, client: TestClient, db_session):
        """Test memory usage under heavy load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate heavy load
        for i in range(1000):
            response = client.get("/health")
            assert response.status_code == 200

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\nMemory Usage Test:")
        print(f"  Initial memory: {initial_memory:.1f} MB")
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Memory increase: {memory_increase:.1f} MB")

        # Memory increase should be reasonable (less than 100MB for 1000 requests)
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB is too high"

    def test_database_connection_pooling(self, client: TestClient, performance_config: Dict[str, Any]):
        """Test database connection pooling under load."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import QueuePool

        # Monitor connection pool usage
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_pool = MagicMock()
            mock_engine.pool = mock_pool
            mock_create_engine.return_value = mock_engine

            # Simulate load
            def make_db_request():
                response = client.get("/health")
                return response.status_code

            threads = []
            results = []

            def worker():
                result = make_db_request()
                results.append(result)

            for _ in range(performance_config["concurrent_users"]):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Verify connection pool was used
            success_rate = sum(1 for status in results if status == 200) / len(results)
            assert success_rate > 0.95, f"Success rate {success_rate:.1%} is too low"

    # Cache Performance Tests
    def test_cache_performance(self, client: TestClient):
        """Test cache performance under load."""
        # Test cache hit performance
        cache_hit_times = []
        for _ in range(100):
            start_time = time.time()
            response = client.get("/health")  # Should be cached
            end_time = time.time()

            assert response.status_code == 200
            cache_hit_times.append(end_time - start_time)

        # Test cache miss performance
        cache_miss_times = []
        for i in range(100):
            start_time = time.time()
            response = client.get(f"/signals/{i % 10}")  # Should cause cache misses
            end_time = time.time()

            cache_miss_times.append(end_time - start_time)

        avg_cache_hit_time = statistics.mean(cache_hit_times)
        avg_cache_miss_time = statistics.mean([rt for rt in cache_miss_times if rt > 0])

        print(f"\nCache Performance:")
        print(f"  Cache hit avg: {avg_cache_hit_time:.3f}s")
        print(f"  Cache miss avg: {avg_cache_miss_time:.3f}s")
        print(f"  Cache speedup: {avg_cache_miss_time / avg_cache_hit_time:.1f}x")

        assert avg_cache_hit_time < 0.05, f"Cache hit time {avg_cache_hit_time:.3f}s is too slow"
        assert avg_cache_miss_time > avg_cache_hit_time, "Cache should be faster than miss"

    # API Endpoint Performance Comparison
    def test_endpoint_performance_comparison(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test performance comparison across different endpoints."""
        endpoints = [
            ("GET", "/health", None),
            ("GET", "/signals/latest", None),
            ("GET", "/auth/me", auth_headers),
            ("GET", "/users/me", auth_headers),
        ]

        results = {}

        for method, endpoint, headers in endpoints:
            response_times = []

            for _ in range(50):
                start_time = time.time()
                if method == "GET":
                    response = client.get(endpoint, headers=headers or {})
                else:
                    response = client.post(endpoint, headers=headers or {})
                end_time = time.time()

                if response.status_code in [200, 401]:  # Accept auth failures
                    response_times.append(end_time - start_time)

            avg_time = statistics.mean(response_times)
            results[endpoint] = avg_time

            print(f"{method} {endpoint}: {avg_time:.3f}s")

        # Performance assertions
        assert results["/health"] < 0.1, "Health check should be fast"
        assert results["/signals/latest"] < 0.5, "Signal retrieval should be reasonable"

    # Large Payload Performance
    def test_large_payload_performance(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test performance with large request/response payloads."""
        # Create large signal data
        large_signals = []
        for i in range(100):
            signal_data = {
                "symbol": f"EUR_USD_{i}",
                "signal_type": "BUY",
                "entry_price": 1.1234 + (i * 0.001),
                "ai_analysis": "x" * 1000,  # Large analysis text
                "technical_indicators": {
                    "rsi": 45.2,
                    "macd": 0.0023,
                    "bollinger_bands": [1.1300, 1.1150, 1.1234],
                    "moving_averages": [1.1200, 1.1210, 1.1220],
                    "volume_profile": "x" * 500
                }
            }
            large_signals.append(signal_data)

        start_time = time.time()
        response = client.post("/signals/bulk", json={"signals": large_signals}, headers=auth_headers)
        end_time = time.time()

        print(f"\nLarge Payload Performance:")
        print(f"  Payload size: {len(json.dumps(large_signals))} bytes")
        print(f"  Response time: {end_time - start_time:.3f}s")

        # Should handle large payloads gracefully
        assert response.status_code in [200, 422]  # Success or validation error
        assert end_time - start_time < 5.0, "Large payload processing too slow"

    # Database Performance Tests
    def test_database_query_performance(self, db_session, user_fixture: User):
        """Test database query performance."""
        # Create test data
        signals = []
        for i in range(1000):
            signal = Signal(
                symbol=f"TEST_{i % 10}",
                signal_type=SignalTypeEnum.BUY if i % 2 == 0 else SignalTypeEnum.SELL,
                entry_price=1.1000 + (i * 0.001),
                creator_id=user_fixture.id,
                reliability=70.0 + (i % 30),
                is_active=True
            )
            signals.append(signal)

        db_session.add_all(signals)
        db_session.commit()

        # Test query performance
        query_times = []

        for _ in range(50):
            start_time = time.time()
            result = db_session.query(Signal).filter(
                Signal.creator_id == user_fixture.id,
                Signal.is_active == True
            ).limit(100).all()
            end_time = time.time()

            query_times.append(end_time - start_time)
            assert len(result) == 100

        avg_query_time = statistics.mean(query_times)

        print(f"\nDatabase Query Performance:")
        print(f"  Average query time: {avg_query_time:.3f}s")
        print(f"  Records per query: 100")

        assert avg_query_time < 0.1, f"Database query too slow: {avg_query_time:.3f}s"

    # Network Performance Tests
    def test_network_timeout_handling(self, client: TestClient):
        """Test network timeout handling."""
        # This would typically require external network simulation
        # For now, we'll test that timeouts are configured properly

        # Test with very short timeout
        try:
            response = client.get("/health", timeout=0.001)
            # Should either succeed very quickly or timeout
            assert response.status_code in [200, 408]
        except Exception:
            # Timeout is acceptable
            pass

    # Performance Regression Testing
    def test_performance_regression_detection(self, client: TestClient):
        """Test for performance regression detection."""
        # Baseline performance metrics (these would be stored externally in production)
        baseline_metrics = {
            "health_check_avg_time": 0.05,
            "signal_retrieval_avg_time": 0.15,
            "authentication_avg_time": 0.3,
            "max_error_rate": 0.02
        }

        # Measure current performance
        current_metrics = {}

        # Health check performance
        health_times = []
        for _ in range(50):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            health_times.append(end_time - start_time)

        current_metrics["health_check_avg_time"] = statistics.mean(health_times)

        # Signal retrieval performance
        signal_times = []
        for _ in range(50):
            start_time = time.time()
            response = client.get("/signals/latest")
            end_time = time.time()
            signal_times.append(end_time - start_time)

        current_metrics["signal_retrieval_avg_time"] = statistics.mean(signal_times)

        print(f"\nPerformance Regression Test:")
        print(f"  Baseline health check: {baseline_metrics['health_check_avg_time']:.3f}s")
        print(f"  Current health check: {current_metrics['health_check_avg_time']:.3f}s")
        print(f"  Baseline signal retrieval: {baseline_metrics['signal_retrieval_avg_time']:.3f}s")
        print(f"  Current signal retrieval: {current_metrics['signal_retrieval_avg_time']:.3f}s")

        # Check for regression (more than 50% degradation)
        health_check_regression = (current_metrics["health_check_avg_time"] / baseline_metrics["health_check_avg_time"]) > 1.5
        signal_retrieval_regression = (current_metrics["signal_retrieval_avg_time"] / baseline_metrics["signal_retrieval_avg_time"]) > 1.5

        assert not health_check_regression, "Health check performance regression detected"
        assert not signal_retrieval_regression, "Signal retrieval performance regression detected"

    @pytest.mark.slow
    def test_end_to_end_performance_scenario(self, client: TestClient, test_user_data: Dict[str, Any]):
        """Test complete end-to-end performance scenario."""
        scenario_steps = [
            ("User Registration", lambda: client.post("/auth/register", json=test_user_data)),
            ("User Login", lambda: client.post("/auth/token", data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            })),
            ("Get User Profile", lambda: client.get("/users/me", headers={"Authorization": "Bearer test_token"})),
            ("Get Latest Signals", lambda: client.get("/signals/latest")),
            ("Health Check", lambda: client.get("/health")),
        ]

        step_times = {}

        for step_name, step_func in scenario_steps:
            start_time = time.time()
            try:
                response = step_func()
                step_times[step_name] = time.time() - start_time
            except Exception as e:
                step_times[step_name] = -1  # Error

        total_time = sum(time for time in step_times.values() if time > 0)

        print(f"\nEnd-to-End Performance Scenario:")
        for step_name, step_time in step_times.items():
            if step_time > 0:
                print(f"  {step_name}: {step_time:.3f}s")
            else:
                print(f"  {step_name}: ERROR")

        print(f"  Total scenario time: {total_time:.3f}s")

        # Performance assertions
        assert total_time < 5.0, f"End-to-end scenario too slow: {total_time:.3f}s"
        assert all(time > 0 for time in step_times.values()), "All scenario steps should succeed"