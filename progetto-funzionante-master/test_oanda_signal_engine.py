#!/usr/bin/env python3
"""
OANDA Signal Engine Test
Tests the AI-powered signal generation component
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add frontend directory to path
sys.path.append('C:\\Users\\USER\\Desktop\\progetto-funzionante-master\\frontend')

try:
    from oanda_signal_engine import OANDASignalEngine, SignalType, RiskLevel
    from oanda_api_client import OANDAClient, OANDAEnvironment
    OANDA_AVAILABLE = True
except ImportError as e:
    print(f"OANDA modules not available: {e}")
    OANDA_AVAILABLE = False

class OANDASignalEngineTester:
    """Test the OANDA signal engine with mock data"""

    def __init__(self):
        self.api_key = os.getenv("OANDA_API_KEY")
        self.account_id = os.getenv("OANDA_ACCOUNT_ID", "101-001-37019635-001")
        self.environment = os.getenv("OANDA_ENVIRONMENT", "practice")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        print(f"Signal Engine Test Configuration:")
        print(f"  API Key: {'Available' if self.api_key else 'Not Available'}")
        print(f"  Account ID: {self.account_id}")
        print(f"  Environment: {self.environment}")
        print(f"  Gemini API: {'Available' if self.gemini_api_key else 'Not Available'}")

    async def test_signal_engine_logic(self) -> Dict[str, Any]:
        """Test signal engine logic with mock data"""
        print("\nTesting Signal Engine Logic...")

        results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "oanda_available": OANDA_AVAILABLE,
            "tests_run": [],
            "ai_analysis_tests": [],
            "technical_analysis_tests": [],
            "signal_generation_tests": []
        }

        if not OANDA_AVAILABLE:
            results["status"] = "skipped"
            results["message"] = "OANDA modules not available"
            return results

        try:
            # Initialize signal engine
            signal_engine = OANDASignalEngine(
                self.api_key or "mock_key",
                self.account_id,
                self.environment,
                self.gemini_api_key
            )

            if self.api_key:
                # Test with real API if credentials available
                print("Attempting to initialize with real API...")
                try:
                    await signal_engine.__aenter__()
                    results["api_connected"] = True
                except Exception as e:
                    print(f"Failed to connect to real API: {e}")
                    results["api_connected"] = False
                    results["api_error"] = str(e)
            else:
                results["api_connected"] = False
                results["api_error"] = "No API key provided"

            # Test technical analysis calculations
            print("Testing technical analysis calculations...")
            import numpy as np
            import pandas as pd

            # Generate mock price data
            np.random.seed(42)  # For reproducible results
            base_price = 1.0800
            mock_prices = [base_price + np.random.normal(0, 0.001) for _ in range(100)]

            # Test RSI calculation
            from oanda_signal_engine import TechnicalAnalyzer
            rsi = TechnicalAnalyzer.calculate_rsi(np.array(mock_prices))
            print(f"RSI Calculation: {rsi:.2f}")

            # Test MACD calculation
            macd_line, macd_signal, macd_histogram = TechnicalAnalyzer.calculate_macd(np.array(mock_prices))
            print(f"MACD: Line={macd_line:.5f}, Signal={macd_signal:.5f}, Histogram={macd_histogram:.5f}")

            # Test Bollinger Bands
            bb_upper, bb_middle, bb_lower = TechnicalAnalyzer.calculate_bollinger_bands(np.array(mock_prices))
            print(f"Bollinger Bands: Upper={bb_upper:.5f}, Middle={bb_middle:.5f}, Lower={bb_lower:.5f}")

            results["technical_analysis_tests"].append({
                "test": "rsi_calculation",
                "value": rsi,
                "status": "completed"
            })

            results["technical_analysis_tests"].append({
                "test": "macd_calculation",
                "values": {"macd_line": macd_line, "macd_signal": macd_signal, "macd_histogram": macd_histogram},
                "status": "completed"
            })

            results["technical_analysis_tests"].append({
                "test": "bollinger_bands",
                "values": {"upper": bb_upper, "middle": bb_middle, "lower": bb_lower},
                "status": "completed"
            })

            # Test AI analysis if Gemini is available
            if self.gemini_api_key:
                print("Testing AI analysis...")
                try:
                    # Mock market context and technical data
                    mock_technical = type('MockTechnical', (), {
                        'rsi': rsi,
                        'rsi_signal': 'neutral' if 30 <= rsi <= 70 else 'oversold' if rsi < 30 else 'overbought',
                        'macd_trend': 'bullish' if macd_histogram > 0 else 'bearish',
                        'ma_trend': 'bullish',
                        'volatility_level': 'medium',
                        'technical_score': 0.75
                    })()

                    mock_market = type('MockMarket', (), {
                        'market_session': 'London',
                        'session_overlap': True,
                        'spread_quality': 'tight',
                        'volatility_expected': 'high'
                    })()

                    ai_analysis, reasoning = await signal_engine._generate_ai_analysis(
                        "EUR_USD", mock_technical, mock_market, SignalType.BUY
                    )

                    results["ai_analysis_tests"].append({
                        "test": "ai_analysis_generation",
                        "status": "completed",
                        "ai_analysis_length": len(ai_analysis),
                        "reasoning": reasoning
                    })

                    print(f"AI Analysis Generated: {len(ai_analysis)} characters")
                    print(f"Reasoning: {reasoning}")

                except Exception as e:
                    print(f"AI Analysis test failed: {e}")
                    results["ai_analysis_tests"].append({
                        "test": "ai_analysis_generation",
                        "status": "failed",
                        "error": str(e)
                    })
            else:
                print("Skipping AI analysis tests - no Gemini API key")

            # Test signal generation logic
            print("Testing signal generation logic...")
            mock_technical_score = 0.75  # High confidence score

            if mock_technical_score >= signal_engine.confidence_threshold:
                # Determine signal type
                bullish_factors = 3
                bearish_factors = 1

                if bullish_factors > bearish_factors:
                    signal_type = SignalType.BUY
                elif bearish_factors > bullish_factors:
                    signal_type = SignalType.SELL
                else:
                    signal_type = SignalType.HOLD

                results["signal_generation_tests"].append({
                    "test": "signal_type_determination",
                    "status": "completed",
                    "signal_type": signal_type.value,
                    "confidence_score": mock_technical_score,
                    "bullish_factors": bullish_factors,
                    "bearish_factors": bearish_factors
                })

                print(f"Signal Generated: {signal_type.value} with {mock_technical_score:.1%} confidence")
            else:
                results["signal_generation_tests"].append({
                    "test": "signal_type_determination",
                    "status": "skipped",
                    "reason": f"Confidence score {mock_technical_score:.1%} below threshold {signal_engine.confidence_threshold:.1%}"
                })

            # Test risk management calculations
            print("Testing risk management calculations...")
            current_price = 1.0800
            mock_atr = 0.0050  # 50 pips

            if signal_type == SignalType.BUY:
                stop_distance = mock_atr * 1.2
                stop_loss = current_price - stop_distance
                take_profit = current_price + (stop_distance * signal_engine.default_rrr)
            else:
                stop_distance = mock_atr * 1.2
                stop_loss = current_price + stop_distance
                take_profit = current_price - (stop_distance * signal_engine.default_rrr)

            risk_reward_ratio = abs(take_profit - current_price) / abs(stop_loss - current_price)

            results["signal_generation_tests"].append({
                "test": "risk_management_calculation",
                "status": "completed",
                "current_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_reward_ratio": risk_reward_ratio,
                "atr": mock_atr
            })

            print(f"Risk Management: SL={stop_loss:.5f}, TP={take_profit:.5f}, RR={risk_reward_ratio:.2f}")

            # Cleanup
            if results["api_connected"]:
                await signal_engine.__aexit__(None, None, None)

            results["status"] = "completed"
            results["message"] = "Signal engine logic tests completed successfully"

        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Signal engine test failed: {str(e)}"
            print(f"Signal engine test error: {e}")

        return results

    async def test_with_real_symbols(self) -> Dict[str, Any]:
        """Test signal generation with real symbols if API is available"""
        print("\nTesting with Real Symbols (if API available)...")

        results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "real_api_tests": [],
            "symbols_tested": []
        }

        if not self.api_key or not OANDA_AVAILABLE:
            results["status"] = "skipped"
            results["message"] = "API credentials not available"
            return results

        try:
            signal_engine = OANDASignalEngine(
                self.api_key,
                self.account_id,
                self.environment,
                self.gemini_api_key
            )

            async with signal_engine:
                # Test with common forex pairs
                test_symbols = ["EUR_USD", "GBP_USD", "USD_JPY"]

                for symbol in test_symbols:
                    print(f"Testing signal generation for {symbol}...")
                    try:
                        signal = await signal_engine.generate_signal(symbol, "H1")

                        if signal:
                            results["real_api_tests"].append({
                                "symbol": symbol,
                                "status": "success",
                                "signal_type": signal.signal_type.value,
                                "confidence_score": signal.confidence_score,
                                "technical_score": signal.technical_score,
                                "entry_price": signal.entry_price,
                                "stop_loss": signal.stop_loss,
                                "take_profit": signal.take_profit,
                                "risk_reward_ratio": signal.risk_reward_ratio
                            })

                            print(f"  Signal: {signal.signal_type.value}")
                            print(f"  Confidence: {signal.confidence_score:.1%}")
                            print(f"  Entry: {signal.entry_price:.5f}")
                            print(f"  SL: {signal.stop_loss:.5f}")
                            print(f"  TP: {signal.take_profit:.5f}")
                            print(f"  R/R: {signal.risk_reward_ratio:.2f}")
                        else:
                            results["real_api_tests"].append({
                                "symbol": symbol,
                                "status": "no_signal",
                                "message": "No signal generated"
                            })

                            print(f"  No signal generated for {symbol}")

                        results["symbols_tested"].append(symbol)

                    except Exception as e:
                        results["real_api_tests"].append({
                            "symbol": symbol,
                            "status": "error",
                            "error": str(e)
                        })

                        print(f"  Error for {symbol}: {e}")
                        results["symbols_tested"].append(symbol)

            results["status"] = "completed"
            results["message"] = f"Tested {len(results['symbols_tested'])} symbols"

        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Real API test failed: {str(e)}"
            print(f"Real API test error: {e}")

        return results

async def run_signal_engine_tests():
    """Run all signal engine tests"""
    print("OANDA Signal Engine Test Suite")
    print("=" * 40)

    tester = OANDASignalEngineTester()

    # Test signal engine logic
    logic_results = await tester.test_signal_engine_logic()

    # Test with real API if available
    real_results = await tester.test_with_real_symbols()

    # Combine results
    final_results = {
        "test_suite": "OANDA Signal Engine",
        "test_timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "api_key_available": bool(tester.api_key),
            "gemini_api_available": bool(tester.gemini_api_key),
            "environment": tester.environment,
            "account_id": tester.account_id
        },
        "logic_tests": logic_results,
        "real_api_tests": real_results,
        "summary": {
            "total_tests": len(logic_results.get("tests_run", [])) + len(real_results.get("real_api_tests", [])),
            "ai_tests": len(logic_results.get("ai_analysis_tests", [])),
            "technical_tests": len(logic_results.get("technical_analysis_tests", [])),
            "real_symbols_tested": len(real_results.get("symbols_tested", []))
        }
    }

    # Print summary
    print("\n" + "=" * 40)
    print("SIGNAL ENGINE TEST SUMMARY")
    print("=" * 40)

    summary = final_results["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"AI Analysis Tests: {summary['ai_tests']}")
    print(f"Technical Analysis Tests: {summary['technical_tests']}")
    print(f"Real Symbols Tested: {summary['real_symbols_tested']}")
    print(f"Logic Tests Status: {logic_results.get('status', 'unknown')}")
    print(f"Real API Tests Status: {real_results.get('status', 'unknown')}")

    if real_results.get("real_api_tests"):
        successful_signals = len([t for t in real_results["real_api_tests"] if t["status"] == "success"])
        print(f"Successful Signal Generation: {successful_signals}/{len(real_results['real_api_tests'])}")

    return final_results

if __name__ == "__main__":
    results = asyncio.run(run_signal_engine_tests())

    # Save results
    import json
    with open("signal_engine_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to signal_engine_test_results.json")