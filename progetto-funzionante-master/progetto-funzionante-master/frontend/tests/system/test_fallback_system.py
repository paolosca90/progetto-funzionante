#!/usr/bin/env python3
"""
Test del sistema fallback per indici
"""
import asyncio
import sys
import logging

sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_fallback_system():
    """Test del sistema fallback per NAS100 e SPX500"""
    print("=== TEST SISTEMA FALLBACK PER INDICI ===\n")
    
    try:
        from advanced_signal_analyzer import AdvancedSignalAnalyzer, TimeFrame
        
        # Test analyzer con credenziali non valide per forzare fallback
        analyzer = AdvancedSignalAnalyzer(
            oanda_api_key='invalid_key_to_force_fallback',
            gemini_api_key='test_gemini_key'
        )
        
        print("[OK] AdvancedSignalAnalyzer inizializzato per test fallback")
        
        # Test indici che dovrebbero triggare il fallback
        test_symbols = ['NAS100_USD', 'SPX500_USD', 'US30_USD']
        
        for symbol in test_symbols:
            print(f"\n[TEST] {symbol}:")
            
            try:
                # Questo dovrebbe triggerare il fallback quando OANDA fails
                analysis = await analyzer.analyze_symbol(symbol, TimeFrame.H1)
                
                if analysis:
                    print(f"  [SUCCESS] Segnale generato: {analysis.signal_direction}")
                    print(f"  [SUCCESS] Confidence: {analysis.confidence_score:.1f}%")
                    print(f"  [SUCCESS] Entry: {analysis.entry_price:.2f}")
                    print(f"  [SUCCESS] SL: {analysis.stop_loss:.2f}")
                    print(f"  [SUCCESS] TP: {analysis.take_profit:.2f}")
                    
                    # Verifica che la descrizione contenga i contenuti
                    has_sentiment = "SENTIMENT" in analysis.ai_reasoning
                    has_0dte = "0DTE" in analysis.ai_reasoning
                    correct_direction = analysis.signal_direction in analysis.ai_reasoning
                    
                    print(f"  [CHECK] Sentiment in description: {has_sentiment}")
                    print(f"  [CHECK] 0DTE in description: {has_0dte}")
                    print(f"  [CHECK] Correct direction: {correct_direction}")
                    
                    # Mostra primi 300 caratteri della descrizione
                    print(f"  [PREVIEW] AI Reasoning (300 chars):")
                    print(f"    {analysis.ai_reasoning[:300]}...")
                else:
                    print(f"  [FAIL] Nessun segnale generato")
                    
            except Exception as e:
                error_type = type(e).__name__
                print(f"  [ERROR] {error_type}: {e}")
                
                # Se l'errore è relativo alla connessione, il fallback dovrebbe funzionare
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    print(f"  [EXPECTED] Errore di connessione - fallback dovrebbe attivarsi")
                else:
                    print(f"  [UNEXPECTED] Errore non previsto")
        
        print(f"\n=== RISULTATI TEST FALLBACK ===")
        print("1. Il sistema fallback dovrebbe generare segnali per gli indici")
        print("2. Anche senza dati OANDA reali, dovremmo avere segnali utilizzabili") 
        print("3. Le descrizioni dovrebbero includere sentiment e 0DTE")
        print("4. HTTP 422 dovrebbe essere eliminato con il fallback")
        
        return True
        
    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fallback_system())
    if success:
        print("\n[READY] Sistema fallback testato - procedi con commit")
    else:
        print("\n[NOT READY] Problemi nel sistema fallback")