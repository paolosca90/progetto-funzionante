#!/usr/bin/env python3
"""
Test rapido per verificare che SL/TP non siano troppo vicini
"""

import asyncio
import logging
import os
from advanced_signal_analyzer import AdvancedSignalAnalyzer, TimeFrame

# Disable verbose logging
logging.basicConfig(level=logging.WARNING)

async def test_sl_tp_distances():
    """Test rapido delle distanze SL/TP"""

    print("TESTING SL/TP DISTANCES")
    print("="*40)

    # SECURITY: Use environment variables for API keys
    api_key = os.getenv("OANDA_API_KEY", "your_oanda_api_key_here")
    if api_key == "your_oanda_api_key_here":
        print("ERROR: Please set OANDA_API_KEY environment variable")
        return

    analyzer = AdvancedSignalAnalyzer(oanda_api_key=api_key)
    
    # Test symbols
    symbols = ["EUR_USD", "GBP_USD", "AUD_USD"]
    
    for symbol in symbols:
        print(f"\n{symbol}:")
        
        try:
            analysis = await analyzer.analyze_symbol(symbol, TimeFrame.M15)
            
            if analysis and analysis.signal_direction != "HOLD":
                entry = analysis.entry_price
                sl = analysis.stop_loss
                tp = analysis.take_profit
                
                # Calculate distances as percentages
                sl_pct = abs(entry - sl) / entry * 100
                tp_pct = abs(tp - entry) / entry * 100
                
                print(f"   Entry: {entry:.5f}")
                print(f"   SL: {sl:.5f} ({sl_pct:.3f}%)")
                print(f"   TP: {tp:.5f} ({tp_pct:.3f}%)")
                print(f"   R/R: {analysis.risk_reward_ratio:.2f}")
                
                # Check if distances are reasonable
                if sl_pct < 0.5 or tp_pct < 1.0:
                    print(f"   WARNING: Distances too small!")
                else:
                    print(f"   OK: Reasonable distances")
            else:
                print(f"   HOLD signal")
                
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print(f"\n{'='*40}")

if __name__ == "__main__":
    asyncio.run(test_sl_tp_distances())
