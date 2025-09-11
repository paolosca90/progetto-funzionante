#!/usr/bin/env python3
"""
Script semplificato per debug generazione segnali OANDA
"""
import asyncio
from oanda_signal_engine import OANDASignalEngine

async def test_signal_generation():
    print("=== TEST GENERAZIONE SEGNALI ===\n")
    
    # Credenziali OANDA UK
    api_key = "9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286"
    account_id = "101-004-37029911-001"
    
    # Inizializza engine
    engine = OANDASignalEngine(api_key, account_id, "practice")
    
    try:
        # Test health check (auto-inizializza il client)
        print("1. Testing health check...")
        health = await engine.health_check()
        print(f"   Health status: {health}")
        
        if not health:
            print("   ERROR: Health check failed")
            return
        
        # Test instrumenti disponibili
        print("\n2. Testing available instruments...")
        instruments = await engine.oanda_client.get_instruments()
        print(f"   Total instruments: {len(instruments)}")
        
        # Filtra per tipologie
        forex = [i.name for i in instruments if "_" in i.name and len(i.name) == 7]
        metals = [i.name for i in instruments if i.name in ['XAU_USD', 'XAG_USD']]  # Solo Gold e Silver
        indices = [i.name for i in instruments if i.name in ['US30_USD', 'NAS100_USD', 'SPX500_USD', 'DE30_EUR']]  # Solo US e DAX
        
        print(f"   Forex: {len(forex)} (esempi: {forex[:3]})")
        print(f"   Metalli: {len(metals)} ({metals})")
        print(f"   Indici: {len(indices)} ({indices})")
        
        # Test generazione segnale per ogni categoria
        print("\n3. Testing signal generation...")
        test_symbols = []
        if forex: test_symbols.append(forex[0])
        if metals: test_symbols.append(metals[0])
        if indices: test_symbols.append(indices[0])
        
        for symbol in test_symbols:
            print(f"   Testing {symbol}...")
            try:
                signal = await engine.generate_signal(symbol)
                if signal:
                    print(f"   OK {symbol}: {signal.signal_type} @ {signal.entry_price} (confidence: {signal.confidence_score*100:.1f}%)")
                else:
                    print(f"   X No signal generated for {symbol}")
            except Exception as e:
                print(f"   X Error generating signal for {symbol}: {e}")
        
        print("\n=== TEST COMPLETATO ===")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_signal_generation())