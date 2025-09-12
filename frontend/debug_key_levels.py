#!/usr/bin/env python3
"""
Debug key levels extraction
"""
import asyncio
import logging
import sys

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def debug_key_levels():
    """Debug perché non vengono estratti key levels"""
    try:
        from advanced_signal_analyzer import AdvancedSignalAnalyzer, TimeFrame
        
        analyzer = AdvancedSignalAnalyzer(
            oanda_api_key='9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286',
            gemini_api_key='test_key'
        )
        
        print("[DEBUG] Testing key levels extraction for NAS100_USD")
        
        analysis = await analyzer.analyze_symbol('NAS100_USD', TimeFrame.H1)
        
        print(f"[RESULT] Signal: {analysis.signal_direction}")
        print(f"[RESULT] Entry: {analysis.entry_price:.2f}")
        print(f"[RESULT] SL: {analysis.stop_loss:.2f}")
        print(f"[RESULT] TP: {analysis.take_profit:.2f}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_key_levels())
    print(f"[DONE] Debug completed: {success}")