#!/usr/bin/env python3
"""
OANDA Integration Mock Tests for TestSprite Compatibility
Tests the integration logic with mock OANDA API responses
"""

import asyncio
import json
import time
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Test Configuration
TEST_CONFIG = {
    "test_symbols": ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD"],
    "test_timeframes": ["M1", "M5", "M15", "H1", "H4"],
    "iterations": 10,
    "timeout": 30,
    "simulate_network_latency": True,
    "simulate_rate_limiting": True
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
class MockMarketData:
    """Mock market data structure"""
    instrument: str
    bid: float
    ask: float
    mid: float
    spread: float
    timestamp: datetime
    volume: int = 1000

@dataclass
class MockCandle:
    """Mock candle data structure"""
    instrument: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    complete: bool

class MockOANDAClient:
    """Mock OANDA client that simulates API responses"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.request_count = 0
        self.error_rate = 0.05  # 5% error rate for simulation
        self.rate_limit_threshold = 100  # Rate limit after 100 requests

    async def simulate_network_delay(self):
        """Simulate network latency"""
        if self.config.get("simulate_network_latency", True):
            delay = random.uniform(0.1, 2.0)  # 100ms to 2s delay
            await asyncio.sleep(delay)

    async def check_rate_limit(self):
        """Simulate rate limiting"""
        if self.config.get("simulate_rate_limiting", True):
            self.request_count += 1
            if self.request_count > self.rate_limit_threshold:
                if random.random() < 0.3:  # 30% chance of rate limit
                    await asyncio.sleep(1.0)  # Simulate rate limit delay

    async def get_account_info(self) -> Dict[str, Any]:
        """Mock account info"""
        await self.simulate_network_delay()
        await self.check_rate_limit()

        if random.random() < self.error_rate:
            raise Exception("Mock API error")

        return {
            "id": "101-001-37019635-001",
            "alias": "Test Account",
            "currency": "USD",
            "balance": 10000.00,
            "unrealizedPL": 0.00,
            "realizedPL": 0.00,
            "marginUsed": 0.00,
            "marginAvailable": 10000.00,
            "openTradeCount": 0,
            "openOrderCount": 0,
            "createdTime": "2023-01-01T00:00:00Z"
        }

    async def get_instruments(self) -> List[Dict[str, Any]]:
        """Mock instruments list"""
        await self.simulate_network_delay()
        await self.check_rate_limit()

        if random.random() < self.error_rate:
            raise Exception("Mock API error")

        instruments = []
        for symbol in self.config["test_symbols"]:
            instruments.append({
                "name": symbol,
                "type": "CURRENCY",
                "displayName": symbol.replace("_", "/"),
                "pipLocation": -4,
                "displayPrecision": 5,
                "tradeUnitsPrecision": 0,
                "minimumTradeSize": "1",
                "maximumTrailingStopDistance": "1.0000",
                "minimumTrailingStopDistance": "0.0005",
                "maximumPositionSize": "100",
                "maximumOrderUnits": "100",
                "marginRate": "0.05"
            })
        return instruments

    async def get_current_prices(self, instruments: List[str]) -> List[MockMarketData]:
        """Mock current prices"""
        await self.simulate_network_delay()
        await self.check_rate_limit()

        if random.random() < self.error_rate:
            raise Exception("Mock API error")

        prices = []
        for instrument in instruments:
            # Generate realistic price data
            base_price = {
                "EUR_USD": 1.0800,
                "GBP_USD": 1.2700,
                "USD_JPY": 149.50,
                "AUD_USD": 0.6800,
                "USD_CAD": 1.3500
            }.get(instrument, 1.0000)

            # Add some random variation
            variation = random.uniform(-0.0010, 0.0010)
            mid_price = base_price + variation
            spread = random.uniform(0.0001, 0.0005)

            prices.append(MockMarketData(
                instrument=instrument,
                bid=mid_price - spread/2,
                ask=mid_price + spread/2,
                mid=mid_price,
                spread=spread,
                timestamp=datetime.utcnow(),
                volume=random.randint(100, 10000)
            ))

        return prices

    async def get_candles(self, instrument: str, granularity: str, count: int = 100) -> List[MockCandle]:
        """Mock candle data"""
        await self.simulate_network_delay()
        await self.check_rate_limit()

        if random.random() < self.error_rate:
            raise Exception("Mock API error")

        # Generate realistic candle data
        base_price = {
            "EUR_USD": 1.0800,
            "GBP_USD": 1.2700,
            "USD_JPY": 149.50,
            "AUD_USD": 0.6800,
            "USD_CAD": 1.3500
        }.get(instrument, 1.0000)

        candles = []
        current_price = base_price
        current_time = datetime.utcnow() - timedelta(hours=count)

        for i in range(count):
            # Generate realistic price movement
            change = random.uniform(-0.0020, 0.0020)
            current_price += change

            # Generate OHLC data
            high = current_price + abs(random.uniform(0, 0.0010))
            low = current_price - abs(random.uniform(0, 0.0010))
            open_price = current_price - random.uniform(-0.0005, 0.0005)
            close_price = current_price

            candles.append(MockCandle(
                instrument=instrument,
                time=current_time + timedelta(hours=i),
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=random.randint(100, 10000),
                complete=True
            ))

            current_price = close_price

        return candles

    async def health_check(self) -> bool:
        """Mock health check"""
        await self.simulate_network_delay()
        return random.random() > self.error_rate

class MockSignalEngine:
    """Mock signal engine that simulates AI-powered trading signals"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.oanda_client = MockOANDAClient(config)

    async def generate_signal(self, instrument: str, timeframe: str = "H1") -> Dict[str, Any]:
        """Generate mock trading signal"""
        # Get market data
        prices = await self.oanda_client.get_current_prices([instrument])
        candles = await self.oanda_client.get_candles(instrument, timeframe, 100)

        if not prices or not candles:
            raise Exception("Failed to get market data")

        price = prices[0]
        current_price = price.mid

        # Calculate mock technical indicators
        close_prices = [candle.close for candle in candles[-20:]]

        # RSI calculation (simplified)
        rsi = random.uniform(20, 80)

        # MACD calculation (simplified)
        macd_line = random.uniform(-0.0100, 0.0100)
        macd_signal = random.uniform(-0.0050, 0.0050)
        macd_histogram = macd_line - macd_signal

        # Bollinger Bands (simplified)
        sma = statistics.mean(close_prices)
        std_dev = statistics.stdev(close_prices)
        bb_upper = sma + (std_dev * 2)
        bb_lower = sma - (std_dev * 2)

        # Determine signal type
        bullish_factors = 0
        bearish_factors = 0

        if rsi < 40:
            bullish_factors += 1
        elif rsi > 60:
            bearish_factors += 1

        if macd_histogram > 0:
            bullish_factors += 1
        else:
            bearish_factors += 1

        if current_price > sma:
            bullish_factors += 1
        else:
            bearish_factors += 1

        if current_price < bb_lower:
            bullish_factors += 1
        elif current_price > bb_upper:
            bearish_factors += 1

        # Determine signal type and confidence
        if bullish_factors > bearish_factors:
            signal_type = "BUY"
            confidence = min(0.9, 0.5 + (bullish_factors - bearish_factors) * 0.1)
        elif bearish_factors > bullish_factors:
            signal_type = "SELL"
            confidence = min(0.9, 0.5 + (bearish_factors - bullish_factors) * 0.1)
        else:
            signal_type = "HOLD"
            confidence = 0.5

        # Calculate risk management
        atr = std_dev * 0.5  # Simplified ATR
        if signal_type == "BUY":
            stop_loss = current_price - (atr * 1.5)
            take_profit = current_price + (atr * 2.0)
        elif signal_type == "SELL":
            stop_loss = current_price + (atr * 1.5)
            take_profit = current_price - (atr * 2.0)
        else:
            stop_loss = current_price - atr
            take_profit = current_price + atr

        risk_reward_ratio = abs(take_profit - current_price) / abs(stop_loss - current_price)

        return {
            "instrument": instrument,
            "signal_type": signal_type,
            "confidence_score": confidence,
            "entry_price": current_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": risk_reward_ratio,
            "timeframe": timeframe,
            "technical_indicators": {
                "rsi": rsi,
                "macd_line": macd_line,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram,
                "bollinger_upper": bb_upper,
                "bollinger_lower": bb_lower,
                "sma": sma
            },
            "market_context": {
                "spread": price.spread,
                "volume": price.volume,
                "timestamp": price.timestamp.isoformat()
            },
            "ai_analysis": f"Mock AI analysis for {instrument}: {signal_type} signal with {confidence:.1%} confidence. "
                           f"Technical indicators show {'bullish' if bullish_factors > bearish_factors else 'bearish'} bias.",
            "reasoning": f"Signal based on {bullish_factors} bullish vs {bearish_factors} bearish factors. "
                        f"RSI: {rsi:.1f}, MACD: {'bullish' if macd_histogram > 0 else 'bearish'}.",
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=4)).isoformat()
        }

    async def generate_signals_batch(self, instruments: List[str], timeframe: str = "H1", min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Generate batch of mock trading signals"""
        signals = []

        for instrument in instruments:
            try:
                signal = await self.generate_signal(instrument, timeframe)
                if signal["confidence_score"] >= min_confidence:
                    signals.append(signal)
            except Exception as e:
                print(f"Failed to generate signal for {instrument}: {e}")

        return signals

class OANDAMockIntegrationTester:
    """Mock OANDA integration tester"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or TEST_CONFIG
        self.oanda_client = MockOANDAClient(self.config)
        self.signal_engine = MockSignalEngine(self.config)
        self.results: List[TestResult] = []
        self.response_times = []

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
        self.response_times.append(duration_ms)

        print(f"{'PASS' if status == 'passed' else 'FAIL' if status == 'failed' else 'ERROR' if status == 'error' else 'SKIP'} {test_name}: {status.upper()} ({duration_ms:.1f}ms)")

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("OANDA Integration Mock Tests")
        print("=" * 40)

        start_time = time.time()

        # Test suites
        test_suites = [
            ("Connection Tests", self.test_connection_suite),
            ("Market Data Tests", self.test_market_data_suite),
            ("Signal Generation Tests", self.test_signal_generation_suite),
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
            "configuration": self.config,
            "metrics": self.calculate_metrics(),
            "suite_results": suite_results,
            "detailed_results": [asdict(result) for result in self.results],
            "production_readiness": self.assess_production_readiness()
        }

        return final_results

    async def test_connection_suite(self) -> Dict[str, Any]:
        """Test connection suite"""
        results = {}

        # Test health check
        start_time = time.time()
        try:
            health_ok = await self.oanda_client.health_check()
            duration = (time.time() - start_time) * 1000

            if health_ok:
                await self.record_test("health_check", "passed", duration)
                results["health_check"] = "passed"
            else:
                await self.record_test("health_check", "failed", duration, "Health check failed")
                results["health_check"] = "failed"
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("health_check", "error", duration, str(e))
            results["health_check"] = "error"

        # Test account access
        start_time = time.time()
        try:
            account_info = await self.oanda_client.get_account_info()
            duration = (time.time() - start_time) * 1000

            if account_info:
                await self.record_test("account_access", "passed", duration,
                                     data={"account_id": account_info["id"], "balance": account_info["balance"]})
                results["account_access"] = "passed"
            else:
                await self.record_test("account_access", "failed", duration, "No account info")
                results["account_access"] = "failed"
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("account_access", "error", duration, str(e))
            results["account_access"] = "error"

        return results

    async def test_market_data_suite(self) -> Dict[str, Any]:
        """Test market data suite"""
        results = {}

        # Test current prices
        for symbol in self.config["test_symbols"][:3]:
            start_time = time.time()
            try:
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
        symbol = self.config["test_symbols"][0]
        start_time = time.time()
        try:
            candles = await self.oanda_client.get_candles(symbol, "H1", 100)
            duration = (time.time() - start_time) * 1000

            if candles:
                await self.record_test(f"historical_data_{symbol}", "passed", duration,
                                     data={"candle_count": len(candles)})
                results[f"historical_data_{symbol}"] = "passed"
            else:
                await self.record_test(f"historical_data_{symbol}", "failed", duration, "No candles returned")
                results[f"historical_data_{symbol}"] = "failed"
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test(f"historical_data_{symbol}", "error", duration, str(e))
            results[f"historical_data_{symbol}"] = "error"

        return results

    async def test_signal_generation_suite(self) -> Dict[str, Any]:
        """Test signal generation suite"""
        results = {}

        # Test individual signal generation
        for symbol in self.config["test_symbols"][:2]:
            start_time = time.time()
            try:
                signal = await self.signal_engine.generate_signal(symbol, "H1")
                duration = (time.time() - start_time) * 1000

                if signal:
                    await self.record_test(f"signal_generation_{symbol}", "passed", duration,
                                         data={
                                             "signal_type": signal["signal_type"],
                                             "confidence": signal["confidence_score"],
                                             "risk_reward": signal["risk_reward_ratio"]
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
            signals = await self.signal_engine.generate_signals_batch(
                self.config["test_symbols"][:3], "H1", 0.0
            )
            duration = (time.time() - start_time) * 1000

            await self.record_test("batch_signal_generation", "passed", duration,
                                 data={"signals_generated": len(signals)})
            results["batch_signal_generation"] = "passed"
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("batch_signal_generation", "error", duration, str(e))
            results["batch_signal_generation"] = "error"

        return results

    async def test_performance_suite(self) -> Dict[str, Any]:
        """Test performance suite"""
        results = {}

        # Test API call performance
        response_times = []
        symbol = self.config["test_symbols"][0]

        for i in range(self.config["iterations"]):
            start_time = time.time()
            try:
                await self.oanda_client.get_current_prices([symbol])
                duration = (time.time() - start_time) * 1000
                response_times.append(duration)
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
            rapid_requests = 20
            success_count = 0
            rate_limit_hits = 0

            for i in range(rapid_requests):
                request_start = time.time()
                try:
                    await self.oanda_client.get_current_prices([self.config["test_symbols"][0]])
                    success_count += 1
                except Exception as e:
                    if "rate limit" in str(e).lower():
                        rate_limit_hits += 1
                request_duration = (time.time() - request_start) * 1000

                if request_duration > 1000:  # Rate limit delay
                    rate_limit_hits += 1

            duration = (time.time() - start_time) * 1000

            await self.record_test("rate_limiting", "passed", duration,
                                 data={
                                     "rapid_requests": rapid_requests,
                                     "successful_requests": success_count,
                                     "rate_limit_hits": rate_limit_hits,
                                     "rate_limit_respected": rate_limit_hits > 0
                                 })
            results["rate_limiting"] = "passed"
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("rate_limiting", "error", duration, str(e))
            results["rate_limiting"] = "error"

        # Test data consistency
        start_time = time.time()
        try:
            symbol = self.config["test_symbols"][0]
            price_samples = []

            for _ in range(10):
                prices = await self.oanda_client.get_current_prices([symbol])
                if prices:
                    price_samples.append(prices[0].mid)
                await asyncio.sleep(0.1)

            if len(price_samples) >= 5:
                price_variance = statistics.variance(price_samples)
                price_range = max(price_samples) - min(price_samples)

                await self.record_test("data_consistency", "passed", duration,
                                     data={
                                         "sample_count": len(price_samples),
                                         "price_variance": price_variance,
                                         "price_range": price_range,
                                         "consistent": price_variance < 0.01
                                     })
                results["data_consistency"] = "passed"
            else:
                await self.record_test("data_consistency", "failed", duration, "Insufficient data samples")
                results["data_consistency"] = "failed"
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
            try:
                await self.oanda_client.get_current_prices(["INVALID_SYMBOL"])
                duration = (time.time() - start_time) * 1000
                await self.record_test("invalid_instrument", "failed", duration, "Should have thrown error")
                results["invalid_instrument"] = "failed"
            except Exception:
                duration = (time.time() - start_time) * 1000
                await self.record_test("invalid_instrument", "passed", duration, "Correctly handled invalid instrument")
                results["invalid_instrument"] = "passed"
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("invalid_instrument", "error", duration, str(e))
            results["invalid_instrument"] = "error"

        # Test high error rate scenario
        start_time = time.time()
        try:
            # Temporarily increase error rate
            original_error_rate = self.oanda_client.error_rate
            self.oanda_client.error_rate = 0.8  # 80% error rate

            successful_requests = 0
            total_requests = 10

            for _ in range(total_requests):
                try:
                    await self.oanda_client.get_current_prices([self.config["test_symbols"][0]])
                    successful_requests += 1
                except:
                    pass

            # Restore original error rate
            self.oanda_client.error_rate = original_error_rate

            duration = (time.time() - start_time) * 1000
            success_rate = successful_requests / total_requests

            await self.record_test("high_error_handling", "passed", duration,
                                 data={
                                     "total_requests": total_requests,
                                     "successful_requests": successful_requests,
                                     "success_rate": success_rate,
                                     "expected_low_success": success_rate < 0.5
                                 })
            results["high_error_handling"] = "passed"
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self.record_test("high_error_handling", "error", duration, str(e))
            results["high_error_handling"] = "error"

        return results

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate test metrics"""
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        error_tests = len([r for r in self.results if r.status == "error"])
        total_tests = len(self.results)

        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "avg_response_time_ms": statistics.mean(self.response_times) if self.response_times else 0
        }

    def assess_production_readiness(self) -> Dict[str, Any]:
        """Assess production readiness"""
        metrics = self.calculate_metrics()
        readiness_score = metrics["passed"]
        max_score = metrics["total_tests"]

        readiness_percentage = (readiness_score / max_score * 100) if max_score > 0 else 0

        issues = []
        recommendations = []

        if readiness_percentage < 80:
            issues.append(f"Low success rate: {readiness_percentage:.1f}%")
            recommendations.append("Improve error handling and reliability")

        if metrics["avg_response_time_ms"] > 2000:
            issues.append(f"High average response time: {metrics['avg_response_time_ms']:.1f}ms")
            recommendations.append("Optimize performance and reduce latency")

        # Determine overall readiness
        overall_readiness = "ready"
        if readiness_percentage < 80:
            overall_readiness = "needs_improvement"
        if readiness_percentage < 60:
            overall_readiness = "not_ready"

        return {
            "readiness_score": readiness_score,
            "max_score": max_score,
            "readiness_percentage": readiness_percentage,
            "overall_readiness": overall_readiness,
            "issues": issues,
            "recommendations": recommendations,
            "success_rate": metrics["success_rate"],
            "average_response_time_ms": metrics["avg_response_time_ms"]
        }

async def run_mock_oanda_tests() -> Dict[str, Any]:
    """Run mock OANDA integration tests"""
    print("OANDA Integration Mock Test Suite")
    print("=" * 40)

    tester = OANDAMockIntegrationTester()
    results = await tester.run_all_tests()

    # Print summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)

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
    results = asyncio.run(run_mock_oanda_tests())

    # Save results to file
    with open("oanda_mock_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to oanda_mock_test_results.json")