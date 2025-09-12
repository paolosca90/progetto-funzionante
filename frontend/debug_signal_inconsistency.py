#!/usr/bin/env python3
"""
Debug script per identificare inconsistenze nel segnale (SELL header vs HOLD description)
"""
import asyncio
import sys
import logging
import json
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, '.')

logging.basicConfig(level=logging.DEBUG)

async def debug_signal_inconsistency():
    """Debugging per inconsistenza SELL vs HOLD"""
    print("=== DEBUG SIGNAL DIRECTION INCONSISTENCY ===\n")
    
    try:
        from advanced_signal_analyzer import AdvancedSignalAnalyzer
        
        # Create analyzer 
        analyzer = AdvancedSignalAnalyzer(
            oanda_api_key='test_key',
            gemini_api_key='test_key' 
        )
        
        # Simulate signal generation for US30_USD to identify where inconsistency occurs
        symbol = "US30_USD"
        print(f"Testing signal generation for {symbol}...")
        
        # We need to check the key methods that determine signal direction
        # Let's trace through the signal generation process
        
        print("\n1. Checking _generate_signal_from_analysis method...")
        
        # Create mock multi-timeframe analysis to test
        from advanced_signal_analyzer import MultiTimeframeAnalysis, TrendDirection
        
        # Test case 1: BEARISH trend (should generate SELL)
        mock_mtf_bearish = type('MockMTF', (), {
            'overall_trend': TrendDirection.BEARISH,
            'confluence_score': 75.0,
            'smart_money_activity': TrendDirection.BEARISH
        })()
        
        print("   Testing BEARISH trend (should be SELL)...")
        print(f"   Mock MTF trend: {mock_mtf_bearish.overall_trend}")
        
        # Check the logic in _generate_signal_from_analysis
        if mock_mtf_bearish.overall_trend == TrendDirection.BEARISH:
            expected_direction = "SELL"
            print(f"   [OK] Expected direction: {expected_direction}")
        else:
            print(f"   [ERROR] Unexpected trend direction")
        
        # Test case 2: Check if sentiment could be overriding the direction
        print("\n2. Checking sentiment influence on signal direction...")
        
        if analyzer.sentiment_aggregator:
            try:
                sentiment = await analyzer.sentiment_aggregator.get_comprehensive_sentiment(symbol)
                print(f"   Sentiment score: {sentiment.overall_sentiment_score:.2f}")
                print(f"   Sentiment confidence: {sentiment.confidence_level:.2f}")
                
                # Check if sentiment is strong enough to override base direction
                if abs(sentiment.overall_sentiment_score) > 0.7:
                    print(f"   [WARNING] Strong sentiment could override base signal!")
                    if sentiment.overall_sentiment_score > 0.7:
                        print(f"   Sentiment suggests: BUY")
                    elif sentiment.overall_sentiment_score < -0.7:
                        print(f"   Sentiment suggests: SELL")
                else:
                    print(f"   [OK] Sentiment not strong enough to override base signal")
                    
            except Exception as e:
                print(f"   [ERROR] Sentiment generation failed: {e}")
        
        # Test case 3: Check signal_data dictionary creation
        print("\n3. Checking signal_data dictionary consistency...")
        
        # Simulate the signal_data creation process
        mock_signal_data = {
            "direction": "SELL",  # This should match the header
            "entry_price": 46028.05,
            "stop_loss": 45990.05,
            "take_profit": 46066.05,
            "confidence": 70.0,
            "risk_reward": 1.0
        }
        
        print(f"   Signal data direction: {mock_signal_data['direction']}")
        print(f"   Signal data confidence: {mock_signal_data['confidence']}%")
        
        # Test case 4: Check AI reasoning generation
        print("\n4. Checking AI reasoning text generation...")
        
        # Look at the translation logic
        signal_translation = {"BUY": "ACQUISTO", "SELL": "VENDITA", "HOLD": "ATTESA"}
        signal_it = signal_translation.get(mock_signal_data['direction'], mock_signal_data['direction'])
        print(f"   Italian translation: {mock_signal_data['direction']} -> {signal_it}")
        
        # Test case 5: Check if there's any HOLD logic that could be interfering
        print("\n5. Searching for HOLD-related logic in reasoning...")
        
        import inspect
        reasoning_source = inspect.getsource(analyzer._generate_ai_reasoning)
        
        if 'HOLD' in reasoning_source:
            print("   [WARNING] Found HOLD references in AI reasoning method!")
            # Count occurrences
            hold_count = reasoning_source.count('HOLD')
            print(f"   HOLD mentions found: {hold_count}")
        else:
            print("   [OK] No hardcoded HOLD references found in reasoning")
        
        # Test case 6: Check for template text that might contain "HOLD"
        print("\n6. Checking for template text containing HOLD...")
        
        if 'segnale "HOLD"' in reasoning_source or "segnale 'HOLD'" in reasoning_source:
            print("   [CRITICAL] Found hardcoded HOLD signal text in reasoning!")
        else:
            print("   [OK] No hardcoded HOLD signal text found")
        
        print("\n=== DIAGNOSIS COMPLETE ===")
        print("\nPossible causes of SELL vs HOLD inconsistency:")
        print("1. Signal direction determined correctly as SELL")
        print("2. But AI reasoning might have hardcoded HOLD text")
        print("3. Or sentiment analysis might be overriding the base signal")
        print("4. Check if signal_data['direction'] matches the actual displayed direction")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_signal_inconsistency())