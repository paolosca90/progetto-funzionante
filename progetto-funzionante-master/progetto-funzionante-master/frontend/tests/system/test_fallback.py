import asyncio
import os
from oanda_signal_engine import OANDASignalEngine

# Test fallback without API keys
if 'OANDA_API_KEY' in os.environ:
    del os.environ['OANDA_API_KEY']

async def test_fallback():
    try:
        print('Testing fallback mechanism without API keys...')
        
        async with OANDASignalEngine() as engine:
            print('This should not print - engine should fail to initialize')
            
    except Exception as e:
        print(f'Expected error caught: {e}')
        
        # Now test the fallback signal generation
        print('\nTesting direct fallback signal generation...')
        engine = OANDASignalEngine()
        
        # Test the fallback signal method directly
        fallback_signal = await engine._generate_fallback_signal('EUR_USD', 'H1')
        
        print('SUCCESS - Fallback signal generated:')
        print(f'   Signal Type: {fallback_signal.signal_type.value}')
        print(f'   AI Analysis: {fallback_signal.ai_analysis}')
        print(f'   Reasoning: {fallback_signal.reasoning}')
        print(f'   Confidence: {fallback_signal.confidence_score:.1%}')

if __name__ == "__main__":
    asyncio.run(test_fallback())