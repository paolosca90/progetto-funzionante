import asyncio
import os
from oanda_signal_engine import OANDASignalEngine

# Set environment variables
os.environ['OANDA_API_KEY'] = '4618cdf696d08a4151d17a77fdb4b2d3-9252ffc76f12c40ffed367fecbe381ff'
os.environ['OANDA_ACCOUNT_ID'] = '101-001-37019635-001'
os.environ['OANDA_ENVIRONMENT'] = 'practice'
os.environ['GEMINI_API_KEY'] = 'AIzaSyAM0JZCXlxkhN_3shsVIEOfBOcKnqSWG38'

async def test_60_percent_threshold():
    try:
        print('Testing 60% probability threshold for HOLD signals...')
        
        # Test multiple pairs to find different confidence levels
        pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'NZD_USD', 'EUR_GBP']
        
        async with OANDASignalEngine() as engine:
            for pair in pairs:
                try:
                    print(f'\n--- Testing {pair} ---')
                    signal = await engine.generate_signal(pair)
                    
                    if signal:
                        confidence_percent = signal.confidence_score * 100
                        print(f'Signal: {signal.signal_type.value}')
                        print(f'Confidence: {confidence_percent:.1f}% (Technical: {signal.technical_score:.2f})')
                        
                        if signal.signal_type.value == 'HOLD':
                            print(f'>>> HOLD because confidence < 60%')
                            print(f'>>> Reasoning: {signal.reasoning}')
                        else:
                            print(f'>>> {signal.signal_type.value} signal with confidence >= 60%')
                            
                        # Show AI analysis
                        print(f'AI Analysis: {signal.ai_analysis[:100]}...')
                        
                except Exception as e:
                    print(f'Error with {pair}: {e}')
                    
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_60_percent_threshold())