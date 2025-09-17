#!/usr/bin/env python3
"""
Verifica finale che i problemi con stop loss e entry price siano risolti
"""

import asyncio
import sys
sys.path.append('.')

from oanda_signal_engine import OANDASignalEngine
from main import get_frontend_symbol, get_oanda_symbol

async def final_verification():
    """Verifica finale che i problemi siano risolti"""
    
    print("FINAL VERIFICATION - Signal Pricing Issues Fixed")
    print("="*80)
    
    # Credenziali
    api_key = "9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286"
    account_id = "101-004-37029911-001"
    environment = "practice"
    
    # Test con alcuni asset rappresentativi di ogni categoria
    test_instruments = [
        ("EUR_USD", "Major Forex"),
        ("GBP_JPY", "Cross Pair"),  
        ("XAU_USD", "Precious Metal"),
        ("US30_USD", "Index"),
        ("NAS100_USD", "Tech Index")
    ]
    
    print(f"Testing {len(test_instruments)} representative instruments after mapping fixes...")
    print("-"*80)
    
    async with OANDASignalEngine(api_key, account_id, environment) as engine:
        all_good = True
        
        for i, (oanda_instrument, category) in enumerate(test_instruments, 1):
            print(f"\n[{i}] {oanda_instrument} ({category})")
            
            try:
                # 1. Test symbol mapping consistency
                frontend_symbol = get_frontend_symbol(oanda_instrument)
                back_to_oanda = get_oanda_symbol(frontend_symbol)
                
                print(f"   Mapping: {oanda_instrument} -> {frontend_symbol} -> {back_to_oanda}")
                
                if back_to_oanda != oanda_instrument:
                    print(f"   ERROR: Mapping inconsistency!")
                    all_good = False
                    continue
                
                # 2. Generate signal
                signal = await engine.generate_signal(oanda_instrument, "H1")
                
                if not signal:
                    print(f"   ERROR: No signal generated")
                    all_good = False
                    continue
                
                # 3. Verify pricing logic
                entry = signal.entry_price
                stop = signal.stop_loss
                tp = signal.take_profit
                signal_type = signal.signal_type.value
                
                print(f"   Signal: {signal_type}")
                print(f"   Entry: {entry:.5f}")
                print(f"   Stop Loss: {stop:.5f}")
                print(f"   Take Profit: {tp:.5f}")
                print(f"   R/R: {signal.risk_reward_ratio:.2f}")
                
                # 4. Validate pricing logic
                issues = []
                
                # Basic validation
                if entry <= 0 or stop <= 0 or tp <= 0:
                    issues.append("Invalid prices (zero or negative)")
                
                # Direction logic validation
                if signal_type == "BUY":
                    if stop >= entry:
                        issues.append(f"BUY signal with stop loss ({stop:.5f}) >= entry ({entry:.5f})")
                    if tp <= entry:
                        issues.append(f"BUY signal with take profit ({tp:.5f}) <= entry ({entry:.5f})")
                elif signal_type == "SELL":
                    if stop <= entry:
                        issues.append(f"SELL signal with stop loss ({stop:.5f}) <= entry ({entry:.5f})")
                    if tp >= entry:
                        issues.append(f"SELL signal with take profit ({tp:.5f}) >= entry ({entry:.5f})")
                
                # Risk/reward validation
                if signal.risk_reward_ratio <= 0 or signal.risk_reward_ratio > 10:
                    issues.append(f"Invalid R/R ratio: {signal.risk_reward_ratio:.2f}")
                
                # Distance validation
                stop_distance = abs(entry - stop)
                tp_distance = abs(tp - entry)
                stop_pct = (stop_distance / entry) * 100
                tp_pct = (tp_distance / entry) * 100
                
                if stop_pct > 10:
                    issues.append(f"Stop loss too wide: {stop_pct:.2f}%")
                elif stop_pct < 0.001:
                    issues.append(f"Stop loss too tight: {stop_pct:.4f}%")
                
                if tp_pct > 20:
                    issues.append(f"Take profit too far: {tp_pct:.2f}%")
                elif tp_pct < 0.001:
                    issues.append(f"Take profit too close: {tp_pct:.4f}%")
                
                if issues:
                    print(f"   ISSUES FOUND:")
                    for issue in issues:
                        print(f"      - {issue}")
                    all_good = False
                else:
                    print(f"   OK: All validations passed")
                
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"   ERROR: {e}")
                all_good = False
        
        # Summary
        print(f"\n{'='*80}")
        print("FINAL VERIFICATION RESULTS")
        print("="*80)
        
        if all_good:
            print("SUCCESS: All signal pricing issues have been resolved!")
            print("- Symbol mapping is now consistent")
            print("- Stop loss and take profit logic is correct")
            print("- Entry prices are properly calculated")
            print("- Risk/reward ratios are reasonable")
        else:
            print("ISSUES STILL PRESENT: Some problems remain")
            print("Check the detailed output above for specific issues")
        
        print("="*80)
        return all_good

if __name__ == "__main__":
    success = asyncio.run(final_verification())
    exit(0 if success else 1)