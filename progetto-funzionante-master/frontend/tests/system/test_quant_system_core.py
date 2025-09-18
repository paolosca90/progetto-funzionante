"""
Test Core Components del Quant Adaptive System
"""

import asyncio
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_data_ingestion():
    """Test data ingestion components"""
    print("\n=== TEST DATA INGESTION ===")
    
    try:
        from quant_adaptive_system.data_ingestion.market_context import CBOEDataProvider, MarketContext
        print("[OK] CBOEDataProvider import SUCCESS")
        
        # Test data provider initialization (without actual network calls)
        provider = CBOEDataProvider()
        print("[OK] CBOEDataProvider instantiation SUCCESS")
        
        # Test data structures
        context = MarketContext(
            timestamp=datetime.utcnow(),
            spx_0dte_share=0.4,
            spy_0dte_share=0.35,
            combined_0dte_share=0.45,
            put_call_ratio=1.1,
            gamma_exposure=0.25,
            regime="NORMAL",
            volatility_regime="MEDIUM",
            pinning_risk=0.3,
            key_levels=[4500.0, 4600.0],
            max_pain=4550.0,
            gamma_wall=4580.0
        )
        print(f"[OK] MarketContext creation SUCCESS: {context.regime}")
        
    except Exception as e:
        print(f"[FAIL] Data Ingestion Test FAILED: {e}")
        return False
    
    try:
        from quant_adaptive_system.data_ingestion.futures_volmap import VolumeProfile, VolumeLevel
        print("[OK] Volume Profile structures import SUCCESS")
        
        # Test volume profile structure
        volume_level = VolumeLevel(price=4550.0, volume=1000, percentage=15.5)
        profile = VolumeProfile(
            contract="ES",
            session_date=datetime.utcnow(),
            session_type="RTH",
            poc=4555.0,
            vah=4570.0,
            val=4540.0,
            session_high=4580.0,
            session_low=4520.0,
            session_close=4560.0,
            total_volume=50000,
            volume_levels=[volume_level],
            value_area_volume_pct=70.0,
            hvn_levels=[4555.0],
            lvn_levels=[4530.0],
            timestamp_created=datetime.utcnow(),
            data_source="CME_TEST"
        )
        print(f"[OK] VolumeProfile creation SUCCESS: POC={profile.poc}")
        
    except Exception as e:
        print(f"[FAIL] Volume Profile Test FAILED: {e}")
        return False
    
    return True

async def test_signal_intelligence():
    """Test signal intelligence components"""
    print("\n=== TEST SIGNAL INTELLIGENCE ===")
    
    try:
        from quant_adaptive_system.signal_intelligence.signal_outcomes import (
            SignalSnapshot, TechnicalFeatures, SignalType, SignalOutcome
        )
        print("[OK] Signal Intelligence imports SUCCESS")
        
        # Test signal snapshot creation
        tech_features = TechnicalFeatures(
            mtf_rsi_1m=65.0,
            mtf_rsi_5m=58.0,
            confluence_score=0.75,
            signal_strength=0.8
        )
        
        signal = SignalSnapshot(
            signal_id="TEST_001",
            timestamp=datetime.utcnow(),
            instrument="EUR_USD",
            signal_type=SignalType.BUY,
            entry_price=1.0850,
            stop_loss=1.0820,
            take_profit=1.0920,
            current_price=1.0850,
            risk_reward_ratio=2.33,
            position_size_suggested=0.02,
            atr_stop_multiplier=2.0,
            technical_features=tech_features,
            volume_features=None,  # Simplified for test
            market_context=None,   # Simplified for test
            ai_reasoning="Test signal for system validation",
            confidence_score=0.75,
            key_factors=["RSI divergence", "Support level bounce"]
        )
        
        print(f"[OK] SignalSnapshot creation SUCCESS: {signal.signal_type.value} {signal.instrument}")
        
    except Exception as e:
        print(f"[FAIL] Signal Intelligence Test FAILED: {e}")
        return False
    
    return True

async def test_regime_detection():
    """Test regime detection components"""
    print("\n=== TEST REGIME DETECTION ===")
    
    try:
        from quant_adaptive_system.regime_detection.market_regimes import RegimeType, RegimeData
        print("[OK] Regime Detection imports SUCCESS")
        
        # Test regime data structure
        regime = RegimeData(
            regime_type=RegimeType.STRONG_TREND,
            confidence=0.85,
            detected_at=datetime.utcnow(),
            key_factors=["Volume breakout", "Momentum divergence"],
            market_conditions={"volatility": "elevated", "volume": "high"},
            volatility_score=0.7,
            trend_strength=0.9
        )
        
        print(f"[OK] RegimeData creation SUCCESS: {regime.regime_type.value} (confidence: {regime.confidence})")
        
    except Exception as e:
        print(f"[FAIL] Regime Detection Test FAILED: {e}")
        return False
    
    try:
        from quant_adaptive_system.regime_detection.policy import PolicyType, PolicyParameters
        print("[OK] Policy Management imports SUCCESS")
        
        # Test policy parameters
        params = PolicyParameters(
            max_position_size=0.02,
            risk_reward_min=2.0,
            min_confidence=0.7,
            confluence_required=3
        )
        
        print(f"[OK] PolicyParameters creation SUCCESS: max_size={params.max_position_size}")
        
    except Exception as e:
        print(f"[FAIL] Policy Management Test FAILED: {e}")
        return False
    
    return True

async def test_risk_management():
    """Test risk management components"""
    print("\n=== TEST RISK MANAGEMENT ===")
    
    try:
        from quant_adaptive_system.risk_management.adaptive_sizing import (
            PositionSizeCalculation, RiskLevel, RiskMetrics
        )
        print("[OK] Risk Management imports SUCCESS")
        
        # Test position size calculation structure
        calc = PositionSizeCalculation(
            instrument="EUR_USD",
            signal_id="TEST_001",
            recommended_size=0.018,
            max_size_allowed=0.025,
            risk_level=RiskLevel.NORMAL,
            kelly_fraction=0.05,
            kelly_adjusted=0.045,
            calculation_reason="Normal market conditions"
        )
        
        print(f"[OK] PositionSizeCalculation SUCCESS: {calc.risk_level.value} - size={calc.recommended_size}")
        
        # Test risk metrics
        metrics = RiskMetrics(
            total_exposure=0.06,
            daily_var=0.015,
            max_drawdown=0.03
        )
        
        print(f"[OK] RiskMetrics creation SUCCESS: exposure={metrics.total_exposure}")
        
    except Exception as e:
        print(f"[FAIL] Risk Management Test FAILED: {e}")
        return False
    
    return True

async def test_reporting():
    """Test reporting components"""
    print("\n=== TEST REPORTING ===")
    
    try:
        from quant_adaptive_system.reporting.metrics_engine import (
            PerformanceMetrics, ComprehensiveReport, AlertLevel
        )
        print("[OK] Reporting imports SUCCESS")
        
        # Test performance metrics
        perf = PerformanceMetrics(
            total_trades=150,
            winning_trades=95,
            losing_trades=55,
            win_rate=63.33,
            total_return=0.24,
            sharpe_ratio=1.45,
            max_drawdown=0.08,
            profit_factor=1.85
        )
        
        print(f"[OK] PerformanceMetrics SUCCESS: win_rate={perf.win_rate}%, sharpe={perf.sharpe_ratio}")
        
    except Exception as e:
        print(f"[FAIL] Reporting Test FAILED: {e}")
        return False
    
    return True

async def test_database_operations():
    """Test database operations"""
    print("\n=== TEST DATABASE OPERATIONS ===")
    
    try:
        import aiosqlite
        import tempfile
        import os
        
        # Create temporary database
        temp_db = tempfile.mktemp(suffix='.db')
        
        async with aiosqlite.connect(temp_db) as db:
            # Create test table
            await db.execute("""
                CREATE TABLE test_signals (
                    id INTEGER PRIMARY KEY,
                    signal_id TEXT,
                    outcome TEXT,
                    r_multiple REAL,
                    timestamp TEXT
                )
            """)
            
            # Insert test data
            await db.execute("""
                INSERT INTO test_signals (signal_id, outcome, r_multiple, timestamp)
                VALUES (?, ?, ?, ?)
            """, ("TEST_001", "TP_HIT", 2.1, datetime.utcnow().isoformat()))
            
            await db.commit()
            
            # Query test data
            cursor = await db.execute("SELECT COUNT(*) FROM test_signals")
            count = await cursor.fetchone()
            
            print(f"[OK] Database operations SUCCESS: {count[0]} record(s) created")
        
        # Cleanup
        if os.path.exists(temp_db):
            os.remove(temp_db)
            
    except Exception as e:
        print(f"[FAIL] Database Test FAILED: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("QUANT ADAPTIVE SYSTEM - CORE COMPONENTS TEST")
    print("=" * 60)
    
    tests = [
        ("Data Ingestion", test_data_ingestion()),
        ("Signal Intelligence", test_signal_intelligence()),
        ("Regime Detection", test_regime_detection()),
        ("Risk Management", test_risk_management()),
        ("Reporting", test_reporting()),
        ("Database Operations", test_database_operations())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        prefix = "[OK]" if result else "[FAIL]"
        print(f"{prefix} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\nALL TESTS PASSED - Quant System core components are working!")
    else:
        print(f"\n{total-passed} test(s) failed - Check logs for details")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
