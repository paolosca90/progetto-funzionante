#!/usr/bin/env python3
"""
Test script per identificare i problemi specifici con NASDAQ e SP500
"""
import asyncio
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

async def test_nas_spx_issues():
    """Test specifico per NAS100_USD e SPX500_USD"""
    print("=== TESTING NASDAQ E SP500 ISSUES ===\n")
    
    try:
        # Test 1: Import modules
        print("1. Testing imports...")
        from advanced_signal_analyzer import AdvancedSignalAnalyzer
        print("   [OK] AdvancedSignalAnalyzer imported")
        
        # Test 2: Check if sentiment analysis is being used
        try:
            analyzer = AdvancedSignalAnalyzer(
                oanda_api_key="test_key", 
                gemini_api_key="test_key"
            )
            has_sentiment = hasattr(analyzer, 'sentiment_aggregator') and analyzer.sentiment_aggregator is not None
            print(f"   [INFO] Sentiment analysis available: {has_sentiment}")
        except Exception as e:
            print(f"   [WARN] Could not initialize analyzer: {e}")
        
        # Test 3: Check OANDA symbol mapping
        print("\n2. Testing symbol mappings...")
        test_symbols = ['NAS100_USD', 'SPX500_USD', 'US30_USD', 'DE30_EUR']
        
        for symbol in test_symbols:
            print(f"   Testing {symbol}:")
            
            # Check if it's in the OANDA format
            if "_" in symbol:
                print(f"     [OK] Symbol in OANDA format: {symbol}")
            else:
                print(f"     [WARN] Symbol not in OANDA format: {symbol}")
            
            # Test instrument-specific data sections
            if 'NAS100' in symbol:
                print(f"     [INFO] Should show NASDAQ-specific data")
            elif 'SPX500' in symbol:
                print(f"     [INFO] Should show S&P 500-specific data")
        
        # Test 4: Check advanced signal analyzer reasoning sections  
        print("\n3. Testing AI reasoning sections...")
        
        # Look for the specific sections that handle different instrument types
        from advanced_signal_analyzer import AdvancedSignalAnalyzer
        import inspect
        
        # Get the _generate_ai_reasoning method source
        method_source = inspect.getsource(AdvancedSignalAnalyzer._generate_ai_reasoning)
        
        if "NAS100" in method_source:
            print("   [OK] NASDAQ-specific reasoning found in AI method")
        else:
            print("   [WARN] No NASDAQ-specific reasoning found")
            
        if "SPX500" in method_source:
            print("   [OK] S&P 500-specific reasoning found in AI method") 
        else:
            print("   [WARN] No S&P 500-specific reasoning found")
        
        # Test 5: Check sentiment integration
        print("\n4. Testing sentiment integration...")
        
        if "market_sentiment" in method_source:
            print("   [OK] Sentiment integration found in AI reasoning")
        else:
            print("   [WARN] No sentiment integration found")
            
        # Test 6: Look for old/outdated descriptions
        print("\n5. Checking for outdated signal descriptions...")
        
        # Check if the description still uses old patterns
        if "format_sentiment_for_signal" in method_source:
            print("   [OK] New sentiment formatting found")
        else:
            print("   [WARN] Old sentiment formatting may be in use")
        
        print("\n=== TESTING COMPLETED ===")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_nas_spx_issues())