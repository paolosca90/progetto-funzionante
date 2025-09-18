import asyncio
import os
from oanda_signal_engine import OANDASignalEngine

# SECURITY: Hardcoded API keys removed for security
# Set environment variables instead:
# os.environ['OANDA_API_KEY'] = 'your_oanda_api_key'
# os.environ['OANDA_ACCOUNT_ID'] = 'your_account_id'
# os.environ['OANDA_ENVIRONMENT'] = 'practice'
# os.environ['GEMINI_API_KEY'] = 'your_gemini_api_key'

if not all([os.environ.get('OANDA_API_KEY'), os.environ.get('OANDA_ACCOUNT_ID'), os.environ.get('GEMINI_API_KEY')]):
    print('ERROR: Please set OANDA_API_KEY, OANDA_ACCOUNT_ID, and GEMINI_API_KEY environment variables')
    exit(1)

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
