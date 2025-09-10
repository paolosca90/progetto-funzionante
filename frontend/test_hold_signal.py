import asyncio
import os
from oanda_signal_engine import OANDASignalEngine

# Set environment variables
os.environ['OANDA_API_KEY'] = '4618cdf696d08a4151d17a77fdb4b2d3-9252ffc76f12c40ffed367fecbe381ff'
os.environ['OANDA_ACCOUNT_ID'] = '101-001-37019635-001'
os.environ['OANDA_ENVIRONMENT'] = 'practice'
os.environ['GEMINI_API_KEY'] = 'AIzaSyAM0JZCXlxkhN_3shsVIEOfBOcKnqSWG38'

async def test_multiple_signals():
    try:
        print('Testing multiple currency pairs to find HOLD signals...')
        
        pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD']
        
        async with OANDASignalEngine() as engine:
            for pair in pairs:
                try:
                    print(f'\n--- Testing {pair} ---')
                    signal = await engine.generate_signal(pair)
                    
                    if signal:
                        print(f'Signal: {signal.signal_type.value}')
                        print(f'Confidence: {signal.confidence_score:.1%}')
                        print(f'AI Analysis: {signal.ai_analysis}')
                        
                        if signal.signal_type.value == 'HOLD':
                            print('FOUND HOLD SIGNAL! Message in Italian:')
                            print(f'>>> {signal.ai_analysis}')
                            
                except Exception as e:
                    print(f'Error with {pair}: {e}')
                    
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multiple_signals())