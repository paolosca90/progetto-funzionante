#!/usr/bin/env python3
"""
Test del flusso completo: generazione -> salvataggio -> API response
"""

import asyncio
import requests
import json
from datetime import datetime
from oanda_signal_engine import OANDASignalEngine

async def test_full_signal_flow():
    """Test del flusso completo dei segnali"""
    
    print("TESTING FULL SIGNAL FLOW (Generation -> API -> Frontend)")
    print("="*80)
    
    # Credenziali
    api_key = "9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286"
    account_id = "101-004-37029911-001"
    environment = "practice"
    
    # Test instruments that might be problematic
    test_instruments = ["EUR_USD", "GBP_JPY", "XAU_USD", "US30_USD"]
    
    print(f"Testing with {len(test_instruments)} instruments...")
    print("-"*80)
    
    async with OANDASignalEngine(api_key, account_id, environment) as engine:
        for i, instrument in enumerate(test_instruments, 1):
            print(f"\n[{i}] Testing {instrument}")
            
            try:
                # 1. Generate signal directly
                signal = await engine.generate_signal(instrument, "H1")
                
                if not signal:
                    print(f"   ❌ No signal generated")
                    continue
                
                print(f"   ✓ Signal generated: {signal.signal_type.value}")
                print(f"   ✓ Entry: {signal.entry_price:.5f}")
                print(f"   ✓ Stop Loss: {signal.stop_loss:.5f}")
                print(f"   ✓ Take Profit: {signal.take_profit:.5f}")
                print(f"   ✓ R/R: {signal.risk_reward_ratio:.2f}")
                
                # 2. Test API endpoint (assuming server is running on port 8000)
                try:
                    api_url = f"http://127.0.0.1:8000/api/signals/oanda/{instrument}"
                    
                    print(f"   🔍 Testing API: {api_url}")
                    response = requests.get(api_url, timeout=10)
                    
                    if response.status_code == 200:
                        api_data = response.json()
                        print(f"   ✓ API Response OK")
                        
                        if api_data.get('status') == 'success' and api_data.get('data'):
                            signal_data = api_data['data']
                            
                            api_entry = signal_data.get('entry_price')
                            api_stop = signal_data.get('stop_loss')
                            api_tp = signal_data.get('take_profit')
                            
                            print(f"   📊 API Data:")
                            print(f"      Entry: {api_entry}")
                            print(f"      Stop Loss: {api_stop}")
                            print(f"      Take Profit: {api_tp}")
                            
                            # Compare direct signal vs API response
                            if api_entry and api_stop and api_tp:
                                entry_diff = abs(signal.entry_price - api_entry)
                                stop_diff = abs(signal.stop_loss - api_stop)
                                tp_diff = abs(signal.take_profit - api_tp)
                                
                                print(f"   🔍 Differences:")
                                print(f"      Entry diff: {entry_diff:.6f}")
                                print(f"      Stop diff: {stop_diff:.6f}")
                                print(f"      TP diff: {tp_diff:.6f}")
                                
                                # Check for significant differences
                                tolerance = 0.00001  # Very small tolerance
                                issues = []
                                
                                if entry_diff > tolerance:
                                    issues.append(f"Entry price mismatch: {entry_diff:.6f}")
                                if stop_diff > tolerance:
                                    issues.append(f"Stop loss mismatch: {stop_diff:.6f}")
                                if tp_diff > tolerance:
                                    issues.append(f"Take profit mismatch: {tp_diff:.6f}")
                                
                                if issues:
                                    print(f"   ⚠️ ISSUES FOUND:")
                                    for issue in issues:
                                        print(f"      - {issue}")
                                else:
                                    print(f"   ✅ Direct vs API: Perfect match")
                            
                        else:
                            print(f"   ❌ API returned error: {api_data.get('message', 'Unknown error')}")
                    
                    else:
                        print(f"   ❌ API Error: {response.status_code}")
                        if response.text:
                            print(f"      Response: {response.text[:200]}")
                
                except requests.exceptions.RequestException as e:
                    print(f"   ⚠️ API test skipped (server not running): {e}")
                
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
    
    print(f"\n{'='*80}")
    print("FULL FLOW TEST COMPLETED")
    print("Check above output for any mismatches between direct generation and API responses")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_full_signal_flow())