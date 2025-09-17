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

async def test_signal():
    try:
        print('Testing OANDA Signal Engine with real API keys...')
        print('Environment:', os.getenv('OANDA_ENVIRONMENT'))
        print('Account ID:', os.getenv('OANDA_ACCOUNT_ID'))
        print('API Key present:', bool(os.getenv('OANDA_API_KEY')))
        
        async with OANDASignalEngine() as engine:
            print('Engine initialized successfully')
            
            # Test EUR_USD signal generation
            print('\nGenerating EUR_USD signal...')
            signal = await engine.generate_signal('EUR_USD')
            
            if signal:
                print('SUCCESS - Signal Generated:', signal.signal_type.value)
                print('   Instrument:', signal.instrument)
                print('   Entry Price: {:.5f}'.format(signal.entry_price))
                print('   Stop Loss: {:.5f}'.format(signal.stop_loss))
                print('   Take Profit: {:.5f}'.format(signal.take_profit))
                print('   Confidence: {:.1%}'.format(signal.confidence_score))
                print('   Risk Level:', signal.risk_level.value)
                print('   Position Size:', signal.position_size)
                print('   Market Session:', signal.market_session)
                print('   Technical Score: {:.2f}'.format(signal.technical_score))
                print('   Volatility: {:.3%}'.format(signal.volatility))
                print('\nAI Analysis:')
                print('   ', signal.ai_analysis)
                print('\nReasoning:')
                print('   ', signal.reasoning)
            else:
                print('ERROR - No signal generated')
                
    except Exception as e:
        print('ERROR:', str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_signal())