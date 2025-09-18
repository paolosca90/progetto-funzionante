#!/usr/bin/env python3
"""
Test dell'AdvancedSignalAnalyzer per verificare che i prezzi siano corretti
"""

import asyncio
import logging
import os
from advanced_signal_analyzer import AdvancedSignalAnalyzer, TimeFrame

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_advanced_analyzer():
    """Test dell'analyzer avanzato"""
    
    print("TESTING ADVANCED SIGNAL ANALYZER")
    print("="*50)
    
    # SECURITY: Use environment variables for API keys
    api_key = os.getenv("OANDA_API_KEY", "your_oanda_api_key_here")
    if api_key == "your_oanda_api_key_here":
        print("ERROR: Please set OANDA_API_KEY environment variable")
        return

    # Inizializza analyzer
    analyzer = AdvancedSignalAnalyzer(oanda_api_key=api_key)
    
    # Test symbols
    test_symbols = ["EUR_USD", "GBP_USD", "XAU_USD"]
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}")
        print("-" * 30)
        
        try:
            # Analizza il simbolo
            analysis = await analyzer.analyze_symbol(symbol, TimeFrame.M15)
            
            if analysis:
                print(f"Analysis completed")
                print(f"   Symbol: {analysis.symbol}")
                print(f"   Direction: {analysis.signal_direction}")
                print(f"   Entry Price: {analysis.entry_price:.5f}")
                print(f"   Stop Loss: {analysis.stop_loss:.5f}")
                print(f"   Take Profit: {analysis.take_profit:.5f}")
                print(f"   Confidence: {analysis.confidence_score:.1f}%")
                print(f"   Risk/Reward: {analysis.risk_reward_ratio:.2f}")
                
                # Verifica che i prezzi siano ragionevoli
                issues = []
                
                # Verifica entry price range per EUR_USD
                if symbol == "EUR_USD":
                    if not (0.5 < analysis.entry_price < 2.0):
                        issues.append(f"EUR_USD entry price fuori range: {analysis.entry_price}")
                        
                # Verifica entry price range per GBP_USD
                elif symbol == "GBP_USD":
                    if not (0.5 < analysis.entry_price < 2.5):
                        issues.append(f"GBP_USD entry price fuori range: {analysis.entry_price}")
                        
                # Verifica entry price range per XAU_USD (Gold)
                elif symbol == "XAU_USD":
                    if not (1000 < analysis.entry_price < 5000):
                        issues.append(f"XAU_USD entry price fuori range: {analysis.entry_price}")
                
                # Verifica logica BUY/SELL
                if analysis.signal_direction == "BUY":
                    if analysis.stop_loss >= analysis.entry_price:
                        issues.append("BUY signal with SL >= entry")
                    if analysis.take_profit <= analysis.entry_price:
                        issues.append("BUY signal with TP <= entry")
                elif analysis.signal_direction == "SELL":
                    if analysis.stop_loss <= analysis.entry_price:
                        issues.append("SELL signal with SL <= entry")
                    if analysis.take_profit >= analysis.entry_price:
                        issues.append("SELL signal with TP >= entry")
                
                if issues:
                    print(f"   ISSUES:")
                    for issue in issues:
                        print(f"      - {issue}")
                else:
                    print(f"   All checks passed")
                    
            else:
                print(f"No analysis returned")
                
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(1)  # Rate limit
    
    print(f"\n{'='*50}")
    print("Advanced analyzer test completed")

if __name__ == "__main__":
    asyncio.run(test_advanced_analyzer())
