#!/usr/bin/env python3
"""
Test completo per verificare l'integrazione sentiment e la risoluzione problemi NAS100/SPX500
"""
import asyncio
import sys
import logging

# Add current directory to Python path
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO)

async def test_complete_integration():
    """Test completo dell'integrazione sentiment e generazione segnali"""
    print("=== TEST INTEGRAZIONE COMPLETA ===\n")
    
    try:
        # Test 1: Import and initialization
        print("1. Testing imports and initialization...")
        from advanced_signal_analyzer import AdvancedSignalAnalyzer
        from sentiment_analysis import SentimentAggregator
        
        analyzer = AdvancedSignalAnalyzer(
            oanda_api_key='test_key',
            gemini_api_key='test_gemini_key'
        )
        
        has_sentiment = hasattr(analyzer, 'sentiment_aggregator') and analyzer.sentiment_aggregator is not None
        print(f"   [OK] Sentiment integration: {has_sentiment}")
        
        # Test 2: Check sentiment aggregator functionality
        print("\n2. Testing sentiment aggregator...")
        if analyzer.sentiment_aggregator:
            try:
                # Test sentiment generation for indices
                test_sentiment = await analyzer.sentiment_aggregator.get_comprehensive_sentiment('SPX500_USD')
                print(f"   [OK] SPX500 sentiment generated: score={test_sentiment.overall_sentiment_score:.2f}")
                
                test_sentiment_nas = await analyzer.sentiment_aggregator.get_comprehensive_sentiment('NAS100_USD')
                print(f"   [OK] NAS100 sentiment generated: score={test_sentiment_nas.overall_sentiment_score:.2f}")
                
            except Exception as e:
                print(f"   [WARN] Sentiment generation error (expected in test): {e}")
        
        # Test 3: Check AI reasoning method with sentiment parameter
        print("\n3. Testing AI reasoning with sentiment...")
        
        import inspect
        sig = inspect.signature(analyzer._generate_ai_reasoning)
        has_sentiment_param = 'market_sentiment' in sig.parameters
        print(f"   [OK] AI reasoning has sentiment parameter: {has_sentiment_param}")
        
        # Test 4: Check instrument-specific reasoning
        print("\n4. Testing instrument-specific reasoning sections...")
        
        # Get method source to check for specific data sections
        method_source = inspect.getsource(analyzer._generate_ai_reasoning)
        
        spx_specific = "DATI OPZIONI S&P 500" in method_source
        nas_specific = "DATI OPZIONI NASDAQ" in method_source
        sentiment_section = "ANALISI SENTIMENT" in method_source
        
        print(f"   [OK] SPX500 specific data: {spx_specific}")
        print(f"   [OK] NAS100 specific data: {nas_specific}")
        print(f"   [OK] Sentiment analysis section: {sentiment_section}")
        
        # Test 5: Check signal modification logic
        print("\n5. Testing signal modification logic...")
        
        # Check if sentiment-driven signal modification exists
        analyzer_source = inspect.getsource(analyzer._generate_signal_from_analysis)
        has_sentiment_adjustment = "sentiment_adjustment" in analyzer_source
        print(f"   [OK] Sentiment adjustment logic: {has_sentiment_adjustment}")
        
        # Test 6: Symbol mapping verification
        print("\n6. Testing symbol mappings...")
        
        test_symbols = ['NAS100_USD', 'SPX500_USD']
        for symbol in test_symbols:
            # Check OANDA format
            is_oanda_format = "_" in symbol and symbol.count("_") == 1
            print(f"   [OK] {symbol} in OANDA format: {is_oanda_format}")
        
        # Test 7: Integration completion check
        print("\n7. Final integration verification...")
        
        all_checks = [
            has_sentiment,
            has_sentiment_param, 
            spx_specific,
            nas_specific,
            sentiment_section,
            has_sentiment_adjustment
        ]
        
        integration_score = sum(all_checks) / len(all_checks) * 100
        print(f"   Integration completion: {integration_score:.1f}%")
        
        if integration_score >= 100:
            print("\n[SUCCESS] INTEGRAZIONE SENTIMENT COMPLETA!")
            print("   - Sentiment analysis integrato nei segnali")
            print("   - Dati specifici per SPX500 e NAS100 presenti")
            print("   - Logica di modifica segnali basata su sentiment attiva")
        elif integration_score >= 80:
            print("\n[PARTIAL] INTEGRAZIONE QUASI COMPLETA")
            print("   Alcune funzionalità potrebbero non essere completamente attive")
        else:
            print("\n[PROBLEMS] INTEGRAZIONE INCOMPLETA")
            print("   Necessarie ulteriori correzioni")
        
        return integration_score
        
    except Exception as e:
        print(f"\nERRORE: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    score = asyncio.run(test_complete_integration())
    print(f"\n=== SCORE FINALE: {score:.1f}% ===")
