#!/usr/bin/env python3
"""
Test sistema in produzione con chiavi OANDA reali
"""
import asyncio
import sys
import logging
import os

sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_production_signals():
    """Test con chiavi OANDA reali di produzione"""
    print("=== TEST PRODUZIONE CON CHIAVI REALI ===\n")
    
    try:
        from advanced_signal_analyzer import AdvancedSignalAnalyzer, TimeFrame
        
        # SECURITY: Use environment variables for API keys
        oanda_key = os.getenv("OANDA_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        if not oanda_key or not gemini_key:
            print("ERROR: Please set OANDA_API_KEY and GEMINI_API_KEY environment variables")
            return
        
        analyzer = AdvancedSignalAnalyzer(
            oanda_api_key=oanda_key,
            gemini_api_key=gemini_key
        )
        
        print("[OK] AdvancedSignalAnalyzer inizializzato con chiavi produzione")
        print(f"   OANDA Key: {oanda_key[:20]}...")
        
        # Test simboli indici
        test_symbols = ['NAS100_USD', 'SPX500_USD']
        
        for symbol in test_symbols:
            print(f"\n[TEST] {symbol} con chiavi reali:")
            
            try:
                analysis = await analyzer.analyze_symbol(symbol, TimeFrame.H1)
                
                if analysis:
                    print(f"   [SUCCESS] Segnale: {analysis.signal_direction} {analysis.confidence_score:.1f}%")
                    print(f"   [PRICE] Entry: {analysis.entry_price:.2f}")
                    print(f"   [PRICE] SL: {analysis.stop_loss:.2f}")
                    print(f"   [PRICE] TP: {analysis.take_profit:.2f}")
                    
                    # Verifica che i prezzi siano realistici
                    is_realistic = analysis.entry_price > 100  # Indici dovrebbero essere > 100
                    different_levels = analysis.entry_price != analysis.stop_loss != analysis.take_profit
                    
                    print(f"   [CHECK] Prezzi realistici: {is_realistic}")
                    print(f"   [CHECK] Livelli differenziati: {different_levels}")
                    
                    if is_realistic and different_levels:
                        print(f"   [SUCCESS] Dati OANDA reali utilizzati")
                    else:
                        print(f"   [FALLBACK] Sistema ha usato dati simulati")
                        
                else:
                    print(f"   [FAIL] Nessun segnale generato")
                    
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                print(f"   [ERROR] {error_type}: {error_msg}")
                
                if "401" in error_msg or "unauthorized" in error_msg.lower():
                    print(f"   [AUTH] ERRORE AUTENTICAZIONE - Chiave OANDA non valida")
                elif "422" in error_msg:
                    print(f"   [DATA] ERRORE 422 - Dati insufficienti (dovrebbe attivare fallback)")
                else:
                    print(f"   [UNKNOWN] Errore non categorizzato")
        
        print(f"\n=== RISULTATI TEST PRODUZIONE ===")
        print("1. Se vedi prezzi realistici (>100) e livelli differenziati = OANDA funziona")
        print("2. Se vedi prezzi identici o bassi (1.00) = Sistema usa fallback") 
        print("3. Errori 401 = Problema autenticazione, NON dovrebbe attivare fallback")
        print("4. Errori 422 = Dati insufficienti, dovrebbe attivare fallback")
        
        return True
        
    except Exception as e:
        print(f"[CRITICAL] ERRORE CRITICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_production_signals())
    if success:
        print("\n[OK] TEST PRODUZIONE COMPLETATO")
    else:
        print("\n[FAIL] TEST PRODUZIONE FALLITO")
