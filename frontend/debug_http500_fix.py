#!/usr/bin/env python3
"""
Debug script per identificare la causa degli errori HTTP 500 per NAS100 e SPX500
"""
import asyncio
import sys
import logging
import traceback
from datetime import datetime

# Add current directory to Python path  
sys.path.insert(0, '.')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_http500_errors():
    """Debug specifico per errori HTTP 500 su NAS100 e SPX500"""
    print("=== DEBUG HTTP 500 ERRORS - NAS100/SPX500 ===\n")
    
    try:
        # Test 1: Symbol mapping verification
        print("1. Testing symbol mappings...")
        from main import get_oanda_symbol, get_frontend_symbol, create_unified_symbol_mappings
        
        test_frontend_symbols = ['NAS100', 'SPX500', 'US30', 'DE30']
        
        for frontend_symbol in test_frontend_symbols:
            oanda_symbol = get_oanda_symbol(frontend_symbol)
            back_to_frontend = get_frontend_symbol(oanda_symbol)
            
            print(f"   {frontend_symbol} -> {oanda_symbol} -> {back_to_frontend}")
            
            if back_to_frontend.upper() == frontend_symbol.upper():
                print(f"   [OK] Round-trip mapping successful")
            else:
                print(f"   [ERROR] Round-trip mapping failed!")
        
        # Test 2: Advanced Signal Analyzer initialization
        print("\n2. Testing AdvancedSignalAnalyzer initialization...")
        
        from advanced_signal_analyzer import AdvancedSignalAnalyzer, TimeFrame
        
        try:
            analyzer = AdvancedSignalAnalyzer(
                oanda_api_key='test_key',
                gemini_api_key='test_key'
            )
            print("   [OK] AdvancedSignalAnalyzer created successfully")
            
            has_sentiment = hasattr(analyzer, 'sentiment_aggregator') and analyzer.sentiment_aggregator is not None
            print(f"   [INFO] Sentiment aggregator available: {has_sentiment}")
            
        except Exception as e:
            print(f"   [ERROR] AdvancedSignalAnalyzer initialization failed: {e}")
            traceback.print_exc()
            return
        
        # Test 3: Symbol analysis for problematic indices
        print("\n3. Testing symbol analysis for NAS100_USD and SPX500_USD...")
        
        problem_symbols = ['NAS100_USD', 'SPX500_USD']
        
        for symbol in problem_symbols:
            print(f"\n   Testing {symbol}:")
            
            try:
                # Try to analyze the symbol (this is what causes HTTP 500)
                print("      Attempting analyze_symbol...")
                
                # This will fail without real OANDA connection, but we can catch specific errors
                advanced_analysis = await analyzer.analyze_symbol(symbol, TimeFrame.H1)
                print(f"      [UNEXPECTED] Analysis completed: {advanced_analysis}")
                
            except Exception as e:
                print(f"      [ERROR] Analysis failed: {type(e).__name__}: {e}")
                
                # Check for specific error types that might cause HTTP 500
                if "OANDA" in str(e) or "api" in str(e).lower():
                    print(f"      [INFO] OANDA API error (expected in test environment)")
                elif "sentiment" in str(e).lower():
                    print(f"      [CRITICAL] Sentiment analysis error!")
                elif "timeframe" in str(e).lower():
                    print(f"      [CRITICAL] Timeframe data error!")
                elif "insufficient" in str(e).lower():
                    print(f"      [CRITICAL] Insufficient market data error!")
                else:
                    print(f"      [CRITICAL] Unknown error type!")
                    traceback.print_exc()
        
        # Test 4: Check if indices have different requirements than forex
        print("\n4. Testing index-specific requirements...")
        
        # Check if there are any index-specific validations or requirements
        print("   Checking for index-specific logic in AdvancedSignalAnalyzer...")
        
        import inspect
        analyzer_source = inspect.getsource(analyzer.analyze_symbol)
        
        if 'NAS100' in analyzer_source or 'SPX500' in analyzer_source:
            print("   [FOUND] Index-specific code in analyze_symbol method")
        else:
            print("   [INFO] No index-specific code found")
        
        # Test 5: Check OANDA instrument availability simulation
        print("\n5. Simulating OANDA instrument availability...")
        
        # In production, these symbols need to be available from OANDA
        # Check if there are any validation issues
        
        expected_oanda_symbols = ['NAS100_USD', 'SPX500_USD', 'US30_USD', 'DE30_EUR']
        
        for symbol in expected_oanda_symbols:
            # Basic validation
            is_valid_format = "_" in symbol and len(symbol.split("_")) == 2
            is_index = any(idx in symbol for idx in ['NAS100', 'SPX500', 'US30', 'DE30'])
            
            print(f"   {symbol}: format_valid={is_valid_format}, is_index={is_index}")
        
        print("\n=== DIAGNOSIS SUMMARY ===")
        print("Possible causes of HTTP 500 errors:")
        print("1. OANDA API connection issues in production")
        print("2. Sentiment analysis initialization failures")  
        print("3. Insufficient market data for indices")
        print("4. Timeframe data issues specific to indices")
        print("5. Index-specific validation failures")
        
        print("\nRecommendations:")
        print("1. Check production OANDA API credentials and connectivity")
        print("2. Verify sentiment analysis module is properly deployed")
        print("3. Add better error handling for insufficient market data")
        print("4. Implement index-specific fallback logic")
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_http500_errors())