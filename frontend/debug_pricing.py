#!/usr/bin/env python3
"""
Debug script to isolate the pricing calculation bug
"""

import asyncio
import logging
import os
from oanda_api_client import create_oanda_client, Granularity, PriceComponent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_pricing():
    """Test OANDA API pricing directly"""
    
    # Get credentials from environment or use defaults
    api_key = os.getenv('OANDA_API_KEY', 'your-api-key-here')
    account_id = os.getenv('OANDA_ACCOUNT_ID', 'your-account-id-here')
    environment = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    if api_key == 'your-api-key-here':
        print("ERROR: OANDA_API_KEY not set in environment")
        return
    
    if account_id == 'your-account-id-here':
        print("ERROR: OANDA_ACCOUNT_ID not set in environment")
        return
    
    try:
        # Create OANDA client
        client = create_oanda_client(api_key, account_id, environment)
        
        async with client:
            print("Testing OANDA pricing for EUR_USD...")
            
            # Test 1: Get current prices
            print("\n--- Test 1: Current Prices ---")
            current_prices = await client.get_current_prices(["EUR_USD"])
            if current_prices:
                price = current_prices[0]
                print(f"Instrument: {price.instrument}")
                print(f"Bid: {price.bid}")
                print(f"Ask: {price.ask}")
                print(f"Mid: {price.mid}")
                print(f"Spread: {price.spread}")
                print(f"Time: {price.time}")
            else:
                print("ERROR: No current prices returned")
            
            # Test 2: Get candles and check last close price
            print("\n--- Test 2: Recent Candles ---")
            candles = await client.get_candles(
                instrument="EUR_USD",
                granularity=Granularity.H1,
                count=5,
                price_component=PriceComponent.MID
            )
            
            if candles:
                print(f"Got {len(candles)} candles")
                latest = candles[-1]
                print(f"Latest candle:")
                print(f"  Time: {latest.time}")
                print(f"  Open: {latest.open}")
                print(f"  High: {latest.high}")
                print(f"  Low: {latest.low}")
                print(f"  Close: {latest.close}")
                print(f"  Volume: {latest.volume}")
                print(f"  Complete: {latest.complete}")
                
                # Compare with current price
                if current_prices:
                    current_mid = current_prices[0].mid
                    candle_close = latest.close
                    print(f"\nPrice Comparison:")
                    print(f"  Current Mid Price: {current_mid}")
                    print(f"  Latest Candle Close: {candle_close}")
                    print(f"  Difference: {abs(current_mid - candle_close)}")
                    
                    if abs(current_mid - candle_close) > 0.01:
                        print("WARNING: Large difference detected!")
            else:
                print("ERROR: No candles returned")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_pricing())