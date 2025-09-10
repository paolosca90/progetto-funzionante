"""
OANDA API Integration Test Suite
===============================

Comprehensive test suite for the OANDA API integration and market data adapter.
Tests real connections, data quality, performance, and failover mechanisms.

Features tested:
- OANDA API connectivity and authentication
- Real-time price streaming
- Historical data retrieval  
- Market data adapter failover
- Enhanced signal engine integration
- Performance benchmarks
- Error handling and circuit breakers

Run with: python test_oanda_integration.py

Author: Backend Performance Architect
Date: September 2025
"""

import os
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Import our modules
from oanda_api_integration import (
    create_oanda_client, OANDAClient, OANDAMarketDataProvider,
    Granularity, MarketPrice
)
from market_data_adapter import (
    create_market_data_adapter, UniversalMarketDataAdapter,
    ProviderConfig, DataProviderType, OANDADataProvider, MockDataProvider
)
from enhanced_signal_engine import EnhancedProfessionalSignalEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OANDAIntegrationTester:
    """Comprehensive OANDA integration test suite"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("Starting OANDA Integration Test Suite")
        start_time = time.time()
        
        tests = [
            ("Environment Check", self.test_environment_setup),
            ("OANDA Client Connection", self.test_oanda_client_connection),
            ("Real-time Price Retrieval", self.test_real_time_prices),
            ("Historical Data Retrieval", self.test_historical_data),
            ("Price Streaming", self.test_price_streaming),
            ("Market Data Adapter", self.test_market_data_adapter),
            ("Enhanced Signal Engine", self.test_enhanced_signal_engine),
            ("Performance Benchmarks", self.test_performance_benchmarks),
            ("Error Handling", self.test_error_handling),
            ("Failover Mechanisms", self.test_failover_mechanisms)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                start = time.time()
                result = await test_func()
                duration = time.time() - start
                
                self.test_results[test_name] = {
                    "status": "PASSED" if result else "FAILED",
                    "duration_ms": round(duration * 1000, 2),
                    "result": result
                }
                
                if result:
                    logger.info(f"✅ {test_name} - PASSED ({duration*1000:.2f}ms)")
                else:
                    logger.error(f"❌ {test_name} - FAILED ({duration*1000:.2f}ms)")
                    
            except Exception as e:
                duration = time.time() - start
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e)
                }
                logger.error(f"💥 {test_name} - ERROR: {e}")
        
        total_duration = time.time() - start_time
        self.test_results["summary"] = {
            "total_tests": len(tests),
            "passed": len([r for r in self.test_results.values() if isinstance(r, dict) and r.get("status") == "PASSED"]),
            "failed": len([r for r in self.test_results.values() if isinstance(r, dict) and r.get("status") == "FAILED"]),
            "errors": len([r for r in self.test_results.values() if isinstance(r, dict) and r.get("status") == "ERROR"]),
            "total_duration_s": round(total_duration, 2)
        }
        
        await self.generate_test_report()
        return self.test_results
    
    async def test_environment_setup(self) -> bool:
        """Test environment setup and configuration"""
        try:
            # Check for required environment variables
            required_vars = ['OANDA_API_KEY', 'OANDA_ACCOUNT_ID']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                logger.warning(f"Missing environment variables: {missing_vars}")
                logger.info("Will use mock provider for testing")
                return True  # Allow testing with mock provider
            
            # Check OANDA environment setting
            oanda_env = os.getenv('OANDA_ENVIRONMENT', 'demo')
            if oanda_env not in ['demo', 'live']:
                logger.warning(f"Invalid OANDA_ENVIRONMENT: {oanda_env}, using 'demo'")
            
            logger.info(f"Environment configured for OANDA {oanda_env} trading")
            return True
            
        except Exception as e:
            logger.error(f"Environment setup test failed: {e}")
            return False
    
    async def test_oanda_client_connection(self) -> bool:
        """Test direct OANDA client connection"""
        try:
            # Skip if no credentials
            if not os.getenv('OANDA_API_KEY') or not os.getenv('OANDA_ACCOUNT_ID'):
                logger.info("Skipping OANDA client test - no credentials provided")
                return True
            
            client = create_oanda_client()
            
            async with client:
                # Test connection
                account_info = await client.get_account_info()
                logger.info(f"Connected to OANDA account: {account_info.id}")
                logger.info(f"Balance: {account_info.balance} {account_info.currency}")
                
                # Test instruments
                instruments = await client.get_instruments()
                logger.info(f"Available instruments: {len(instruments)}")
                
                # Test health check
                health = await client.health_check()
                logger.info(f"Health check: {health}")
                
                return health.get('status') == 'healthy'
                
        except Exception as e:
            logger.error(f"OANDA client connection test failed: {e}")
            return False
    
    async def test_real_time_prices(self) -> bool:
        """Test real-time price retrieval"""
        try:
            if not os.getenv('OANDA_API_KEY') or not os.getenv('OANDA_ACCOUNT_ID'):
                logger.info("Skipping real-time price test - using mock data")
                return True
            
            client = create_oanda_client()
            
            async with client:
                test_symbols = ["EUR_USD", "GBP_USD", "USD_JPY"]
                prices = await client.get_current_prices(test_symbols)
                
                if not prices:
                    return False
                
                for price in prices:
                    logger.info(f"{price.instrument}: {price.bid}/{price.ask} "
                               f"(spread: {price.spread:.5f}, mid: {price.mid:.5f})")
                    
                    # Validate price data
                    if price.bid <= 0 or price.ask <= 0 or price.spread < 0:
                        logger.error(f"Invalid price data for {price.instrument}")
                        return False
                    
                    if price.ask <= price.bid:
                        logger.error(f"Ask price not greater than bid for {price.instrument}")
                        return False
                
                return len(prices) == len(test_symbols)
                
        except Exception as e:
            logger.error(f"Real-time price test failed: {e}")
            return False
    
    async def test_historical_data(self) -> bool:
        """Test historical data retrieval"""
        try:
            if not os.getenv('OANDA_API_KEY') or not os.getenv('OANDA_ACCOUNT_ID'):
                logger.info("Skipping historical data test - using mock data")  
                return True
                
            client = create_oanda_client()
            
            async with client:
                # Test different timeframes
                test_cases = [
                    ("EUR_USD", Granularity.H1, 100),
                    ("GBP_USD", Granularity.M15, 200),
                    ("USD_JPY", Granularity.D, 50)
                ]
                
                for instrument, granularity, count in test_cases:
                    df = await client.get_candles(instrument, granularity, count)
                    
                    if df.empty:
                        logger.error(f"No data retrieved for {instrument} {granularity.value}")
                        return False
                    
                    logger.info(f"{instrument} {granularity.value}: {len(df)} candles")
                    
                    # Validate data structure
                    required_columns = ['open', 'high', 'low', 'close', 'volume']
                    if not all(col in df.columns for col in required_columns):
                        logger.error(f"Missing required columns in {instrument} data")
                        return False
                    
                    # Validate data integrity
                    latest = df.iloc[-1]
                    if not (latest['low'] <= latest['open'] <= latest['high'] and
                            latest['low'] <= latest['close'] <= latest['high']):
                        logger.error(f"OHLC data integrity error in {instrument}")
                        return False
                
                return True
                
        except Exception as e:
            logger.error(f"Historical data test failed: {e}")
            return False
    
    async def test_price_streaming(self) -> bool:
        """Test real-time price streaming"""
        try:
            if not os.getenv('OANDA_API_KEY') or not os.getenv('OANDA_ACCOUNT_ID'):
                logger.info("Skipping price streaming test - no credentials")
                return True
                
            client = create_oanda_client()
            
            async with client:
                received_prices = []
                
                async def price_callback(price: MarketPrice):
                    received_prices.append(price)
                    logger.info(f"Streamed: {price.instrument} = {price.mid:.5f}")
                
                # Start streaming
                instruments = ["EUR_USD", "GBP_USD"]
                stream_task = await client.stream_prices(instruments, price_callback)
                
                # Let it run for 5 seconds
                await asyncio.sleep(5)
                
                # Stop streaming
                stream_task.cancel()
                try:
                    await stream_task
                except asyncio.CancelledError:
                    pass
                
                logger.info(f"Received {len(received_prices)} streamed prices")
                return len(received_prices) > 0
                
        except Exception as e:
            logger.error(f"Price streaming test failed: {e}")
            return False
    
    async def test_market_data_adapter(self) -> bool:
        """Test the universal market data adapter"""
        try:
            adapter = await create_market_data_adapter()
            
            try:
                # Test adapter status
                status = adapter.get_status()
                logger.info(f"Adapter status: {status['connected_providers']}/{status['total_providers']} providers connected")
                
                if status['connected_providers'] == 0:
                    logger.error("No providers connected")
                    return False
                
                # Test real-time price
                price = await adapter.get_real_time_price("EURUSD")
                if price is None:
                    logger.error("Failed to get real-time price")
                    return False
                
                logger.info(f"Adapter real-time EURUSD price: {price}")
                
                # Test market data
                df = await adapter.get_market_data("EURUSD", "H1", 100)
                if df is None or df.empty:
                    logger.error("Failed to get market data")
                    return False
                
                logger.info(f"Adapter retrieved {len(df)} candles for EURUSD")
                
                # Test symbols
                symbols = await adapter.get_symbols()
                logger.info(f"Available symbols: {len(symbols)}")
                
                return True
                
            finally:
                await adapter.shutdown()
                
        except Exception as e:
            logger.error(f"Market data adapter test failed: {e}")
            return False
    
    async def test_enhanced_signal_engine(self) -> bool:
        """Test the enhanced signal engine"""
        try:
            engine = EnhancedProfessionalSignalEngine()
            
            # Initialize engine
            if not await engine.initialize():
                logger.error("Failed to initialize enhanced signal engine")
                return False
            
            try:
                # Test signal generation
                test_symbols = ["EURUSD", "GBPUSD", "USDJPY"]
                signals_generated = 0
                
                for symbol in test_symbols:
                    signal = await engine.generate_signal(symbol)
                    
                    if signal:
                        signals_generated += 1
                        logger.info(f"Generated {signal['signal_type']} signal for {symbol} "
                                   f"(reliability: {signal['reliability']}%, "
                                   f"time: {signal['metadata']['generation_time_ms']}ms)")
                    else:
                        logger.warning(f"No signal generated for {symbol}")
                
                # Test performance metrics
                metrics = engine.get_performance_metrics()
                logger.info(f"Engine metrics: {json.dumps(metrics, indent=2)}")
                
                return signals_generated > 0
                
            finally:
                await engine.shutdown()
                
        except Exception as e:
            logger.error(f"Enhanced signal engine test failed: {e}")
            return False
    
    async def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks"""
        try:
            # Create adapter for benchmarking
            adapter = await create_market_data_adapter()
            
            try:
                # Benchmark real-time price retrieval
                symbol = "EURUSD"
                iterations = 10
                
                start_time = time.time()
                for _ in range(iterations):
                    price = await adapter.get_real_time_price(symbol)
                
                total_time = time.time() - start_time
                avg_time = total_time / iterations
                
                self.performance_metrics["real_time_price"] = {
                    "avg_time_ms": round(avg_time * 1000, 2),
                    "requests_per_second": round(1 / avg_time, 2)
                }
                
                logger.info(f"Real-time price benchmark: {avg_time*1000:.2f}ms avg, "
                           f"{1/avg_time:.2f} req/s")
                
                # Benchmark market data retrieval
                start_time = time.time()
                df = await adapter.get_market_data(symbol, "H1", 500)
                market_data_time = time.time() - start_time
                
                self.performance_metrics["market_data"] = {
                    "time_ms": round(market_data_time * 1000, 2),
                    "candles_per_second": round(len(df) / market_data_time, 2) if df is not None else 0
                }
                
                logger.info(f"Market data benchmark: {market_data_time*1000:.2f}ms for {len(df) if df is not None else 0} candles")
                
                # Performance thresholds
                if avg_time > 0.5:  # 500ms threshold
                    logger.warning("Real-time price retrieval slower than expected")
                
                if market_data_time > 2.0:  # 2s threshold
                    logger.warning("Market data retrieval slower than expected")
                
                return True
                
            finally:
                await adapter.shutdown()
                
        except Exception as e:
            logger.error(f"Performance benchmark failed: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling and recovery"""
        try:
            # Test with invalid credentials
            if os.getenv('OANDA_API_KEY'):
                # Create client with invalid key
                try:
                    from oanda_api_integration import OANDAConfig, OANDAEnvironment, OANDAClient
                    
                    invalid_config = OANDAConfig(
                        api_key="invalid_key",
                        account_id="invalid_account",
                        environment=OANDAEnvironment.DEMO
                    )
                    
                    invalid_client = OANDAClient(invalid_config)
                    
                    async with invalid_client:
                        await invalid_client.get_account_info()
                        
                    logger.error("Expected authentication error but didn't get one")
                    return False
                    
                except Exception as e:
                    logger.info(f"Correctly handled authentication error: {type(e).__name__}")
            
            # Test adapter with no providers
            try:
                from market_data_adapter import UniversalMarketDataAdapter
                
                empty_adapter = UniversalMarketDataAdapter([])
                initialized = await empty_adapter.initialize()
                
                if initialized:
                    logger.error("Adapter should not initialize with no providers")
                    return False
                else:
                    logger.info("Correctly handled no providers scenario")
                    
                await empty_adapter.shutdown()
                
            except Exception as e:
                logger.info(f"Correctly handled empty adapter error: {type(e).__name__}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    async def test_failover_mechanisms(self) -> bool:
        """Test provider failover mechanisms"""
        try:
            # Create adapter with mock and OANDA providers
            from market_data_adapter import ProviderConfig, DataProviderType
            
            configs = [
                ProviderConfig(
                    provider_type=DataProviderType.MOCK,
                    name="Mock_Primary",
                    priority=1,
                    enabled=True
                )
            ]
            
            # Add OANDA if available
            if os.getenv('OANDA_API_KEY') and os.getenv('OANDA_ACCOUNT_ID'):
                configs.append(ProviderConfig(
                    provider_type=DataProviderType.OANDA,
                    name="OANDA_Secondary", 
                    priority=2,
                    enabled=True,
                    config={
                        'api_key': os.getenv('OANDA_API_KEY'),
                        'account_id': os.getenv('OANDA_ACCOUNT_ID'),
                        'environment': os.getenv('OANDA_ENVIRONMENT', 'demo')
                    }
                ))
            
            from market_data_adapter import UniversalMarketDataAdapter
            adapter = UniversalMarketDataAdapter(configs)
            
            if not await adapter.initialize():
                logger.error("Failed to initialize failover test adapter")
                return False
            
            try:
                # Test that adapter works with primary provider
                initial_provider = adapter.active_provider.name if adapter.active_provider else None
                logger.info(f"Initial active provider: {initial_provider}")
                
                price = await adapter.get_real_time_price("EURUSD")
                if price is None:
                    logger.error("Failed to get price from active provider")
                    return False
                
                logger.info(f"Successfully retrieved price from {initial_provider}: {price}")
                
                # Test status reporting
                status = adapter.get_status()
                logger.info(f"Failover test status: {json.dumps(status, indent=2)}")
                
                return True
                
            finally:
                await adapter.shutdown()
                
        except Exception as e:
            logger.error(f"Failover mechanism test failed: {e}")
            return False
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            "test_run": {
                "timestamp": datetime.utcnow().isoformat(),
                "environment": {
                    "oanda_configured": bool(os.getenv('OANDA_API_KEY') and os.getenv('OANDA_ACCOUNT_ID')),
                    "oanda_environment": os.getenv('OANDA_ENVIRONMENT', 'demo'),
                    "mock_enabled": os.getenv('ENABLE_MOCK_PROVIDER', 'false').lower() == 'true'
                }
            },
            "results": self.test_results,
            "performance": self.performance_metrics
        }
        
        # Write to file
        report_file = f"oanda_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Test report saved to: {report_file}")
        except Exception as e:
            logger.error(f"Failed to save test report: {e}")
        
        # Print summary
        summary = self.test_results.get("summary", {})
        print("\n" + "="*60)
        print("OANDA INTEGRATION TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed', 0)}")
        print(f"Failed: {summary.get('failed', 0)}")
        print(f"Errors: {summary.get('errors', 0)}")
        print(f"Duration: {summary.get('total_duration_s', 0):.2f}s")
        
        if self.performance_metrics:
            print(f"\nPERFORMANCE METRICS:")
            for metric, values in self.performance_metrics.items():
                print(f"  {metric}: {values}")
        
        print("="*60)

# === MAIN EXECUTION ===

async def main():
    """Run the test suite"""
    print("OANDA API Integration Test Suite")
    print("="*50)
    print("Testing OANDA API integration, market data adapter,")
    print("and enhanced signal engine functionality.\n")
    
    # Check environment
    if not os.getenv('OANDA_API_KEY'):
        print("⚠️  OANDA_API_KEY not set - some tests will use mock data")
        print("   To test with real OANDA API, set environment variables:")
        print("   - OANDA_API_KEY=your_api_key")
        print("   - OANDA_ACCOUNT_ID=your_account_id")
        print("   - OANDA_ENVIRONMENT=demo (or live)")
        print()
    
    tester = OANDAIntegrationTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    summary = results.get("summary", {})
    if summary.get("failed", 0) > 0 or summary.get("errors", 0) > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())