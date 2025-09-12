"""
Test delle migliorie al sistema di generazione segnali
"""

import asyncio
from datetime import datetime
from dataclasses import dataclass

# Mock simple data structures for testing
@dataclass
class MockTimeFrame:
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"

async def test_signal_improvements():
    """Test the improvements made to signal generation"""
    
    print("=== TEST MIGLIORIE SEGNALI TRADING ===\n")
    
    try:
        from advanced_signal_analyzer import AdvancedSignalAnalyzer
        
        # Initialize analyzer (with dummy keys for testing)
        analyzer = AdvancedSignalAnalyzer("dummy_oanda", "dummy_gemini")
        
        # Test different instruments
        test_instruments = [
            ("AUD_USD", "Forex"),
            ("SPX500_USD", "Indice US"),
            ("XAU_USD", "Metallo prezioso"),
            ("DE30_EUR", "Indice Europeo")
        ]
        
        for symbol, category in test_instruments:
            print(f"[TEST] TESTING {symbol} ({category}):")
            
            try:
                # Generate signal analysis
                result = await analyzer.analyze_symbol(symbol, MockTimeFrame.H1)
                
                if result:
                    print(f"[OK] Segnale generato: {result.signal_direction}")
                    print(f"   Entry: {result.entry_price:.5f}")
                    print(f"   Stop Loss: {result.stop_loss:.5f}")
                    print(f"   Take Profit: {result.take_profit:.5f}")
                    print(f"   Confidence: {result.confidence_score:.1f}%")
                    
                    # Calculate distances for validation
                    if result.entry_price and result.stop_loss:
                        if 'USD' in symbol and 'JPY' not in symbol:
                            # Regular pairs - 4 decimal places
                            sl_pips = abs(result.entry_price - result.stop_loss) / 0.0001
                            if result.take_profit:
                                tp_pips = abs(result.take_profit - result.entry_price) / 0.0001
                                rr = tp_pips / sl_pips if sl_pips > 0 else 0
                                print(f"   Distanze: SL {sl_pips:.1f} pips, TP {tp_pips:.1f} pips")
                                print(f"   Risk/Reward: 1:{rr:.2f}")
                        
                    # Check AI analysis language
                    if result.ai_reasoning:
                        if "ANALISI STRUTTURA DI MERCATO" in result.ai_reasoning:
                            print(f"   [OK] AI in italiano")
                        else:
                            print(f"   [FAIL] AI ancora in inglese")
                            
                        # For indices, check 0DTE data
                        if any(idx in symbol for idx in ['SPX500', 'US30', 'NAS100', 'DE30']):
                            if "0DTE" in result.ai_reasoning or "OPZIONI" in result.ai_reasoning:
                                print(f"   [OK] Dati 0DTE inclusi")
                            else:
                                print(f"   [FAIL] Dati 0DTE mancanti")
                                
                        # Show sample of analysis
                        preview = result.ai_reasoning[:300].replace('\n', ' ')
                        print(f"   Anteprima: {preview}...")
                else:
                    print(f"   [FAIL] Nessun segnale generato")
                    
            except Exception as e:
                print(f"   [FAIL] Errore: {e}")
            
            print()  # Empty line between tests
        
        print("=== TEST COMPLETATO ===")
        
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
    except Exception as e:
        print(f"[FAIL] General error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_signal_improvements())