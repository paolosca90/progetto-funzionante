#!/usr/bin/env python3
"""
Test che verifica il corretto funzionamento dei mapping unificati
"""

import sys
sys.path.append('.')

from main import get_frontend_symbol, get_oanda_symbol

def test_unified_mapping():
    """Test dei mapping unificati"""
    
    print("TESTING UNIFIED SYMBOL MAPPING")
    print("="*50)
    
    # Test cases: tuples of (oanda_format, expected_frontend_format)
    test_cases = [
        # Forex pairs
        ('EUR_USD', 'EURUSD'),
        ('GBP_JPY', 'GBPJPY'), 
        ('USD_CAD', 'USDCAD'),
        
        # Metals
        ('XAU_USD', 'GOLD'),
        ('XAG_USD', 'SILVER'),
        
        # Indices
        ('US30_USD', 'US30'),
        ('NAS100_USD', 'NAS100'),
        ('SPX500_USD', 'SPX500'),
        ('DE30_EUR', 'DE30'),
        
        # Edge cases - symbols not in mapping should use fallback
        ('EUR_SEK', 'EURSEK'),  # Should use fallback (remove underscore)
    ]
    
    print("1. OANDA -> Frontend conversion:")
    all_passed = True
    
    for oanda_symbol, expected_frontend in test_cases:
        result = get_frontend_symbol(oanda_symbol)
        status = "OK" if result == expected_frontend else "FAIL"
        
        print(f"   {oanda_symbol:12} -> {result:10} (expected {expected_frontend:10}) {status}")
        
        if result != expected_frontend:
            all_passed = False
    
    print("\n2. Frontend -> OANDA conversion:")
    
    for oanda_symbol, frontend_symbol in test_cases:
        result = get_oanda_symbol(frontend_symbol)
        status = "OK" if result == oanda_symbol else "FAIL"
        
        print(f"   {frontend_symbol:12} -> {result:12} (expected {oanda_symbol:12}) {status}")
        
        if result != oanda_symbol:
            all_passed = False
    
    print("\n3. Round-trip test:")
    
    for oanda_symbol, _ in test_cases:
        frontend = get_frontend_symbol(oanda_symbol)
        back_to_oanda = get_oanda_symbol(frontend)
        status = "OK" if back_to_oanda == oanda_symbol else "FAIL"
        
        print(f"   {oanda_symbol:12} -> {frontend:10} -> {back_to_oanda:12} {status}")
        
        if back_to_oanda != oanda_symbol:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("ALL TESTS PASSED - Mapping functions work correctly")
    else:
        print("SOME TESTS FAILED - Check mapping implementation")
    print(f"{'='*50}")
    
    return all_passed

if __name__ == "__main__":
    success = test_unified_mapping()
    exit(0 if success else 1)