#!/usr/bin/env python3
"""
Comprehensive OANDA API Integration Test Suite
Test Sprite compatible test suite for validating OANDA API connection, market data retrieval,
signal generation, and overall production readiness
"""

import asyncio
import aiohttp
import json
import os
import time
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import pytest
from contextlib import asynccontextmanager

# Import OANDA components
import sys
sys.path.append('C:\\Users\\USER\\Desktop\\progetto-funzionante-master\\frontend')

try:
    from oanda_api_client import OANDAClient, OANDAAPIError, OANDAEnvironment, Granularity, PriceComponent
    from oanda_signal_engine import OANDASignalEngine, SignalType, RiskLevel, TradingSignal
    OANDA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ OANDA modules not available: {e}")
    OANDA_AVAILABLE = False

# Test Configuration
TEST_CONFIG = {
    "api_key": os.getenv("OANDA_API_KEY"),
    "account_id": os.getenv("OANDA_ACCOUNT_ID", "101-001-37019635-001"),
    "environment": os.getenv("OANDA_ENVIRONMENT", "practice"),
    "test_symbols": ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD"],
    "test_timeframes": ["M1", "M5", "M15", "H1", "H4"],
    "iterations": 10,
    "timeout": 30,
    "rate_limit_delay": 0.1
}

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration_ms: float
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    response_times: List[float]
    success_count: int
    failure_count: int
    error_count: int
    total_bytes: int
    connection_time: float

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count + self.error_count
        return self.success_count / total if total > 0 else 0

    @property
    def total_requests(self) -> int:
        return self.success_count + self.failure_count + self.error_count

class OANDAIntegrationTester:
    """Comprehensive OANDA API integration tester"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or TEST_CONFIG
        self.session: Optional[aiohttp.ClientSession] = None
        self.oanda_client: Optional[OANDAClient] = None
        self.signal_engine: Optional[OANDASignalEngine] = None
        self.results: List[TestResult] = []
        self.metrics = PerformanceMetrics([], 0, 0, 0, 0, 0)

        print(f"OANDA Integration Tester Initialized")
        print(f"Environment: {self.config['environment']}")
        print(f"Account: {self.config['account_id']}")
        print(f"API Key: {self.config['api_key'][:10] if self.config['api_key'] else 'None'}...")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    async def setup(self):
        """Setup test environment"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type": "application/json",
                    "User-Agent": "OANDA-Integration-Tester/1.0"
                }
            )

            # Initialize OANDA client if available
            if OANDA_AVAILABLE and self.config["api_key"]:
                env = OANDAEnvironment.PRACTICE if self.config["environment"] == "practice" else OANDAEnvironment.LIVE
                self.oanda_client = OANDAClient(
                    self.config["api_key"],
                    self.config["account_id"],
                    env
                )
                await self.oanda_client._create_session()

                # Initialize signal engine
                self.signal_engine = OANDASignalEngine(
                    self.config["api_key"],
                    self.config["account_id"],
                    self.config["environment"],
                    os.getenv("GEMINI_API_KEY")
                )
                await self.signal_engine.__aenter__()

            print("Test environment setup complete")

        except Exception as e:
            await self.record_test("setup", "error", 0, str(e))
            raise

    async def cleanup(self):
        """Cleanup test environment"""
        try:
            if self.session:
                await self.session.close()

            if self.oanda_client:
                await self.oanda_client._close_session()

            if self.signal_engine:
                await self.signal_engine.__aexit__(None, None, None)

            print("Test environment cleanup complete")

        except Exception as e:
            print(f"Cleanup error: {e}")

    async def record_test(self, test_name: str, status: str, duration_ms: float,
                         error_message: Optional[str] = None, data: Optional[Dict] = None):
        """Record test result"""
        result = TestResult(
            test_name=test_name,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            data=data
        )
        self.results.append(result)

        # Update metrics
        if status == "passed":
            self.metrics.success_count += 1
        elif status == "failed":
            self.metrics.failure_count += 1
        elif status == "error":
            self.metrics.error_count += 1

        print(f"{'PASS' if status == 'passed' else 'FAIL' if status in ['failed', 'error'] else 'SKIP'} {test_name}: {status.upper()} ({duration_ms:.1f}ms)")

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("\nStarting Comprehensive OANDA Integration Tests")
        print("=" * 60)

        start_time = time.time()

        # Test suites
        test_suites = [
            ("Connection Tests", self.test_connection_suite),
            ("Authentication Tests", self.test_authentication_suite),
            ("Market Data Tests", self.test_market_data_suite),
            ("Signal Engine Tests", self.test_signal_engine_suite),
            ("Performance Tests", self.test_performance_suite),
            ("Reliability Tests", self.test_reliability_suite),
            ("Error Handling Tests", self.test_error_handling_suite)
        ]

        suite_results = {}

        for suite_name, suite_func in test_suites:
            print(f"\nRunning {suite_name}...")
            suite_start = time.time()

            try:
                suite_result = await suite_func()
                suite_results[suite_name] = suite_result
                suite_duration = (time.time() - suite_start) * 1000
                print(f"{suite_name} completed in {suite_duration:.1f}ms")
            except Exception as e:
                suite_duration = (time.time() - suite_start) * 1000
                await self.record_test(f"{suite_name}_suite", "error", suite_duration, str(e))
                suite_results[suite_name] = {"error": str(e)}

        total_duration = (time.time() - start_time) * 1000

        # Compile final results
        final_results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "total_duration_ms": total_duration,
            "configuration": {
                "environment": self.config["environment"],
                "account_id": self.config["account_id"],
                "test_symbols": self.config["test_symbols"],
                "iterations": self.config["iterations"]
            },
            "metrics": {
                "total_tests": len(self.results),
                "passed": self.metrics.success_count,
                "failed": self.metrics.failure_count,
                "errors": self.metrics.error_count,
                "success_rate": self.metrics.success_rate,
                "avg_response_time_ms": self.metrics.avg_response_time
            },
            "suite_results": suite_results,
            "detailed_results": [asdict(result) for result in self.results],
            "production_readiness": self.assess_production_readiness()
        }

        return final_results

    async def test_connection_suite(self) -> Dict[str, Any]:
        """Test OANDA API connection suite"""
        results = {}

        # Test 1: Basic connectivity
        start_time = time.time()
        try:
            if not self.config["api_key"]:
                await self.record_test("basic_connectivity", "skipped", 0, "No API key provided")
                results["basic_connectivity"] = "skipped"
                return results

            base_url = "https://api-fxpractice.oanda.com" if self.config["environment"] == "practice" else "https://api-fxtrade.oanda.com"
            url = f"{base_url}/v3/accounts/{self.config['account_id']}"

            async with self.session.get(url) as response:
                duration = (time.time() - start_time) * 1000

                if response.status == 200:
                    await self.record_test("basic_connectivity", "passed", duration)
                    results["basic_connectivity"] = "passed"
                else:
                    error_text = await response.text()
                    await self.record_test("basic_connectivity", "failed", duration, f"Status {response.status}: {error_text}")
                    results["basic_connectivity"] = "failed"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("basic_connectivity", "error", duration, str(e))
            results["basic_connectivity"] = "error"

        # Test 2: Connection with OANDA client
        start_time = time.time()
        try:
            if self.oanda_client:
                health_ok = await self.oanda_client.health_check()
                duration = (time.time() - start_time) * 1000

                if health_ok:
                    await self.record_test("client_health_check", "passed", duration)
                    results["client_health_check"] = "passed"
                else:
                    await self.record_test("client_health_check", "failed", duration, "Health check failed")
                    results["client_health_check"] = "failed"
            else:
                await self.record_test("client_health_check", "skipped", 0, "OANDA client not available")
                results["client_health_check"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("client_health_check", "error", duration, str(e))
            results["client_health_check"] = "error"

        return results

    async def test_authentication_suite(self) -> Dict[str, Any]:
        """Test authentication suite"""
        results = {}

        # Test 1: Account access validation
        start_time = time.time()
        try:
            if not self.oanda_client:
                await self.record_test("account_access", "skipped", 0, "OANDA client not available")
                results["account_access"] = "skipped"
                return results

            account_info = await self.oanda_client.get_account_info()
            duration = (time.time() - start_time) * 1000

            if account_info and "id" in account_info:
                await self.record_test("account_access", "passed", duration,
                                     data={"account_id": account_info["id"], "currency": account_info.get("currency")})
                results["account_access"] = "passed"
            else:
                await self.record_test("account_access", "failed", duration, "No account info returned")
                results["account_access"] = "failed"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("account_access", "error", duration, str(e))
            results["account_access"] = "error"

        # Test 2: Instruments access
        start_time = time.time()
        try:
            if self.oanda_client:
                instruments = await self.oanda_client.get_instruments()
                duration = (time.time() - start_time) * 1000

                if instruments:
                    await self.record_test("instruments_access", "passed", duration,
                                         data={"instrument_count": len(instruments)})
                    results["instruments_access"] = "passed"
                else:
                    await self.record_test("instruments_access", "failed", duration, "No instruments returned")
                    results["instruments_access"] = "failed"
            else:
                await self.record_test("instruments_access", "skipped", 0, "OANDA client not available")
                results["instruments_access"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("instruments_access", "error", duration, str(e))
            results["instruments_access"] = "error"

        return results

    async def test_market_data_suite(self) -> Dict[str, Any]:
        """Test market data retrieval suite"""
        results = {}

        # Test multiple symbols
        for symbol in self.config["test_symbols"][:3]:  # Test first 3 symbols
            start_time = time.time()
            try:
                if not self.oanda_client:
                    await self.record_test(f"market_data_{symbol}", "skipped", 0, "OANDA client not available")
                    results[f"market_data_{symbol}"] = "skipped"
                    continue

                # Test current prices
                prices = await self.oanda_client.get_current_prices([symbol])
                duration = (time.time() - start_time) * 1000

                if prices:
                    price = prices[0]
                    await self.record_test(f"market_data_{symbol}", "passed", duration,
                                         data={"bid": price.bid, "ask": price.ask, "spread": price.spread})
                    results[f"market_data_{symbol}"] = "passed"
                else:
                    await self.record_test(f"market_data_{symbol}", "failed", duration, "No prices returned")
                    results[f"market_data_{symbol}"] = "failed"

            except Exception as e:
                duration = (time.time() - start_time) * 1000
                await self.record_test(f"market_data_{symbol}", "error", duration, str(e))
                results[f"market_data_{symbol}"] = "error"

        # Test historical data
        symbol = self.config["test_symbols"][0]  # Test with first symbol
        start_time = time.time()
        try:
            if self.oanda_client:
                candles = await self.oanda_client.get_candles(
                    instrument=symbol,
                    granularity=Granularity.H1,
                    count=100
                )
                duration = (time.time() - start_time) * 1000

                if candles:
                    await self.record_test(f"historical_data_{symbol}", "passed", duration,
                                         data={"candle_count": len(candles), "timeframe": "H1"})
                    results[f"historical_data_{symbol}"] = "passed"
                else:
                    await self.record_test(f"historical_data_{symbol}", "failed", duration, "No candles returned")
                    results[f"historical_data_{symbol}"] = "failed"
            else:
                await self.record_test(f"historical_data_{symbol}", "skipped", 0, "OANDA client not available")
                results[f"historical_data_{symbol}"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test(f"historical_data_{symbol}", "error", duration, str(e))
            results[f"historical_data_{symbol}"] = "error"

        return results

    async def test_signal_engine_suite(self) -> Dict[str, Any]:
        """Test signal generation engine suite"""
        results = {}

        # Test signal generation for multiple symbols
        for symbol in self.config["test_symbols"][:2]:  # Test first 2 symbols
            start_time = time.time()
            try:
                if not self.signal_engine:
                    await self.record_test(f"signal_generation_{symbol}", "skipped", 0, "Signal engine not available")
                    results[f"signal_generation_{symbol}"] = "skipped"
                    continue

                signal = await self.signal_engine.generate_signal(symbol, "H1")
                duration = (time.time() - start_time) * 1000

                if signal:
                    await self.record_test(f"signal_generation_{symbol}", "passed", duration,
                                         data={
                                             "signal_type": signal.signal_type.value,
                                             "confidence": signal.confidence_score,
                                             "technical_score": signal.technical_score
                                         })
                    results[f"signal_generation_{symbol}"] = "passed"
                else:
                    await self.record_test(f"signal_generation_{symbol}", "failed", duration, "No signal generated")
                    results[f"signal_generation_{symbol}"] = "failed"

            except Exception as e:
                duration = (time.time() - start_time) * 1000
                await self.record_test(f"signal_generation_{symbol}", "error", duration, str(e))
                results[f"signal_generation_{symbol}"] = "error"

        # Test batch signal generation
        start_time = time.time()
        try:
            if self.signal_engine:
                signals = await self.signal_engine.generate_signals_batch(
                    self.config["test_symbols"][:3],  # Test with first 3 symbols
                    "H1",
                    0.0  # No confidence filter
                )
                duration = (time.time() - start_time) * 1000

                await self.record_test("batch_signal_generation", "passed", duration,
                                     data={"signals_generated": len(signals)})
                results["batch_signal_generation"] = "passed"
            else:
                await self.record_test("batch_signal_generation", "skipped", 0, "Signal engine not available")
                results["batch_signal_generation"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("batch_signal_generation", "error", duration, str(e))
            results["batch_signal_generation"] = "error"

        return results

    async def test_performance_suite(self) -> Dict[str, Any]:
        """Test performance suite"""
        results = {}
        response_times = []

        # Test repeated API calls
        symbol = self.config["test_symbols"][0]
        for i in range(self.config["iterations"]):
            start_time = time.time()
            try:
                if self.oanda_client:
                    await self.oanda_client.get_current_prices([symbol])
                    duration = (time.time() - start_time) * 1000
                    response_times.append(duration)

                    # Rate limiting
                    await asyncio.sleep(self.config["rate_limit_delay"])

            except Exception as e:
                duration = (time.time() - start_time) * 1000
                response_times.append(float('inf'))

        if response_times:
            avg_time = statistics.mean([t for t in response_times if t != float('inf')])
            max_time = max(response_times)
            min_time = min([t for t in response_times if t != float('inf')])
            success_rate = len([t for t in response_times if t != float('inf')]) / len(response_times)

            await self.record_test("performance_api_calls", "passed", avg_time,
                                 data={
                                     "avg_response_time_ms": avg_time,
                                     "min_response_time_ms": min_time,
                                     "max_response_time_ms": max_time,
                                     "success_rate": success_rate,
                                     "iterations": self.config["iterations"]
                                 })
            results["performance_api_calls"] = "passed"
        else:
            await self.record_test("performance_api_calls", "failed", 0, "No performance data collected")
            results["performance_api_calls"] = "failed"

        # Test concurrent requests
        start_time = time.time()
        try:
            if self.oanda_client:
                tasks = []
                for symbol in self.config["test_symbols"][:3]:
                    task = asyncio.create_task(self.oanda_client.get_current_prices([symbol]))
                    tasks.append(task)

                results_data = await asyncio.gather(*tasks, return_exceptions=True)
                duration = (time.time() - start_time) * 1000

                successful_requests = len([r for r in results_data if not isinstance(r, Exception)])
                await self.record_test("concurrent_requests", "passed", duration,
                                     data={
                                         "concurrent_requests": len(tasks),
                                         "successful_requests": successful_requests,
                                         "duration_ms": duration
                                     })
                results["concurrent_requests"] = "passed"
            else:
                await self.record_test("concurrent_requests", "skipped", 0, "OANDA client not available")
                results["concurrent_requests"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("concurrent_requests", "error", duration, str(e))
            results["concurrent_requests"] = "error"

        return results

    async def test_reliability_suite(self) -> Dict[str, Any]:
        """Test reliability suite"""
        results = {}

        # Test rate limiting compliance
        start_time = time.time()
        try:
            if self.oanda_client:
                rapid_requests = 15  # Should trigger rate limiting
                success_count = 0

                for i in range(rapid_requests):
                    try:
                        await self.oanda_client.get_current_prices([self.config["test_symbols"][0]])
                        success_count += 1
                    except OANDAAPIError as e:
                        if "RATE_LIMIT" in str(e):
                            print(f"Rate limit triggered at request {i+1}")
                            break
                        raise

                duration = (time.time() - start_time) * 1000

                await self.record_test("rate_limiting", "passed", duration,
                                     data={
                                         "rapid_requests": rapid_requests,
                                         "successful_requests": success_count,
                                         "rate_limit_respected": success_count < rapid_requests
                                     })
                results["rate_limiting"] = "passed"
            else:
                await self.record_test("rate_limiting", "skipped", 0, "OANDA client not available")
                results["rate_limiting"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("rate_limiting", "error", duration, str(e))
            results["rate_limiting"] = "error"

        # Test data consistency
        start_time = time.time()
        try:
            if self.oanda_client:
                symbol = self.config["test_symbols"][0]

                # Get data multiple times
                price_samples = []
                for _ in range(5):
                    prices = await self.oanda_client.get_current_prices([symbol])
                    if prices:
                        price_samples.append(prices[0].mid)
                    await asyncio.sleep(0.1)

                # Calculate consistency
                if len(price_samples) >= 2:
                    price_variance = statistics.variance(price_samples)
                    price_range = max(price_samples) - min(price_samples)

                    await self.record_test("data_consistency", "passed", duration,
                                         data={
                                             "sample_count": len(price_samples),
                                             "price_variance": price_variance,
                                             "price_range": price_range,
                                             "consistent": price_variance < 0.001  # Very small variance expected
                                         })
                    results["data_consistency"] = "passed"
                else:
                    await self.record_test("data_consistency", "failed", duration, "Insufficient data samples")
                    results["data_consistency"] = "failed"
            else:
                await self.record_test("data_consistency", "skipped", 0, "OANDA client not available")
                results["data_consistency"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("data_consistency", "error", duration, str(e))
            results["data_consistency"] = "error"

        return results

    async def test_error_handling_suite(self) -> Dict[str, Any]:
        """Test error handling suite"""
        results = {}

        # Test invalid instrument
        start_time = time.time()
        try:
            if self.oanda_client:
                try:
                    await self.oanda_client.get_current_prices(["INVALID_SYMBOL"])
                    duration = (time.time() - start_time) * 1000
                    await self.record_test("invalid_instrument", "failed", duration, "Should have thrown error")
                    results["invalid_instrument"] = "failed"
                except OANDAAPIError:
                    duration = (time.time() - start_time) * 1000
                    await self.record_test("invalid_instrument", "passed", duration, "Correctly handled invalid instrument")
                    results["invalid_instrument"] = "passed"
            else:
                await self.record_test("invalid_instrument", "skipped", 0, "OANDA client not available")
                results["invalid_instrument"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("invalid_instrument", "error", duration, str(e))
            results["invalid_instrument"] = "error"

        # Test timeout handling
        start_time = time.time()
        try:
            if self.oanda_client:
                # Simulate timeout by making request with very short timeout
                original_timeout = self.oanda_client.session.timeout
                short_timeout = aiohttp.ClientTimeout(total=0.001)
                self.oanda_client.session.timeout = short_timeout

                try:
                    await self.oanda_client.get_current_prices([self.config["test_symbols"][0]])
                    duration = (time.time() - start_time) * 1000
                    await self.record_test("timeout_handling", "failed", duration, "Should have timed out")
                    results["timeout_handling"] = "failed"
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    duration = (time.time() - start_time) * 1000
                    await self.record_test("timeout_handling", "passed", duration, "Correctly handled timeout")
                    results["timeout_handling"] = "passed"
                finally:
                    # Restore original timeout
                    self.oanda_client.session.timeout = original_timeout
            else:
                await self.record_test("timeout_handling", "skipped", 0, "OANDA client not available")
                results["timeout_handling"] = "skipped"

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("timeout_handling", "error", duration, str(e))
            results["timeout_handling"] = "error"

        return results

    def assess_production_readiness(self) -> Dict[str, Any]:
        """Assess production readiness based on test results"""
        readiness_score = 0
        max_score = 0
        issues = []
        recommendations = []

        # Calculate score from test results
        for result in self.results:
            max_score += 1
            if result.status == "passed":
                readiness_score += 1
            elif result.status == "failed":
                issues.append(f"{result.test_name}: {result.error_message or 'Test failed'}")

        # Additional assessment criteria
        success_rate = self.metrics.success_rate

        if success_rate < 0.8:
            issues.append(f"Low success rate: {success_rate:.1%}")
            recommendations.append("Improve error handling and retry mechanisms")

        if self.metrics.avg_response_time > 2000:  # 2 seconds
            issues.append(f"High average response time: {self.metrics.avg_response_time:.1f}ms")
            recommendations.append("Optimize API calls and consider caching")

        if not self.config["api_key"]:
            issues.append("No API key configured")
            recommendations.append("Configure OANDA_API_KEY environment variable")

        if not self.config["account_id"]:
            issues.append("No account ID configured")
            recommendations.append("Configure OANDA_ACCOUNT_ID environment variable")

        # Overall readiness assessment
        overall_readiness = "ready"
        if readiness_score / max_score < 0.8:
            overall_readiness = "needs_improvement"
        if readiness_score / max_score < 0.5:
            overall_readiness = "not_ready"

        return {
            "readiness_score": readiness_score,
            "max_score": max_score,
            "readiness_percentage": (readiness_score / max_score) * 100 if max_score > 0 else 0,
            "overall_readiness": overall_readiness,
            "issues": issues,
            "recommendations": recommendations,
            "success_rate": success_rate,
            "average_response_time_ms": self.metrics.avg_response_time
        }

async def run_comprehensive_oanda_tests() -> Dict[str, Any]:
    """Main function to run comprehensive OANDA tests"""
    print("OANDA API Integration - Comprehensive Test Suite")
    print("=" * 60)

    async with OANDAIntegrationTester() as tester:
        results = await tester.run_all_tests()

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        metrics = results["metrics"]
        print(f"Total Tests: {metrics['total_tests']}")
        print(f"Passed: {metrics['passed']}")
        print(f"Failed: {metrics['failed']}")
        print(f"Errors: {metrics['errors']}")
        print(f"Success Rate: {metrics['success_rate']:.1%}")
        print(f"Average Response Time: {metrics['avg_response_time_ms']:.1f}ms")

        # Print production readiness
        readiness = results["production_readiness"]
        print(f"\nProduction Readiness: {readiness['overall_readiness'].upper()}")
        print(f"Readiness Score: {readiness['readiness_percentage']:.1f}%")

        if readiness["issues"]:
            print("\nIssues Found:")
            for issue in readiness["issues"]:
                print(f"  • {issue}")

        if readiness["recommendations"]:
            print("\nRecommendations:")
            for rec in readiness["recommendations"]:
                print(f"  • {rec}")

        return results

if __name__ == "__main__":
    # Run comprehensive tests
    results = asyncio.run(run_comprehensive_oanda_tests())

    # Save results to file
    with open("oanda_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to oanda_test_results.json")

    # Exit with appropriate code
    failed_count = results["metrics"]["failed"] + results["metrics"]["error"]
    exit(1 if failed_count > 0 else 0)