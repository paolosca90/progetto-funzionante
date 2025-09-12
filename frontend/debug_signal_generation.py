#!/usr/bin/env python3
"""
Debug script per verificare la generazione di segnali OANDA
"""
import asyncio
import logging
from oanda_signal_engine import OANDASignalEngine
from oanda_api_client import OANDAClient, OANDAEnvironment

# Setup logging per vedere i dettagli
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def debug_signal_generation():
    """Test completo della generazione segnali"""
    print("=== DEBUG GENERAZIONE SEGNALI OANDA ===\n")
    
    # Credenziali OANDA UK
    api_key = "9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286"
    account_id = "101-004-37029911-001"
    
    print(f"API Key: {api_key[:20]}...")
    print(f"Account ID: {account_id}")
    print(f"Environment: PRACTICE\n")
    
    # Inizializza signal engine
    signal_engine = OANDASignalEngine(
        api_key=api_key,
        account_id=account_id,
        environment="practice"
    )
    
    try:
        # Test connessione OANDA  
        print("1. TESTING OANDA CONNECTION...")
        
        # Trigger auto-initialization by calling health_check
        health_status = await signal_engine.health_check()
        print(f"   Health status: {health_status}")
        
        if signal_engine.oanda_client:
            account_info = await signal_engine.oanda_client.get_account_info()
            print(f"   [OK] Account currency: {account_info.get('currency', 'N/A')}")
            print(f"   [OK] Account balance: {account_info.get('balance', 'N/A')}")
        else:
            print("   [FAIL] OANDA client not initialized properly")
            return
            
        # Test strumenti disponibili
        print(f"\n2. TESTING AVAILABLE INSTRUMENTS...")
        instruments = await signal_engine.oanda_client.get_instruments()
        print(f"   [OK] Total instruments: {len(instruments)}")
        
        # Categorizza strumenti
        forex_instruments = [inst.name for inst in instruments if "_" in inst.name and len(inst.name) == 7]
        metal_instruments = [inst.name for inst in instruments if inst.name.startswith(('XAU', 'XAG', 'XPT', 'XPD'))]
        index_instruments = [inst.name for inst in instruments if any(idx in inst.name for idx in ['US30', 'NAS100', 'SPX500', 'UK100', 'DE30', 'FR40', 'JP225'])]
        
        print(f"   [OK] Forex pairs: {len(forex_instruments)}")
        print(f"     Examples: {forex_instruments[:5]}")
        print(f"   [OK] Metals: {len(metal_instruments)}")
        print(f"     Found: {metal_instruments}")
        print(f"   [OK] Indices: {len(index_instruments)}")
        print(f"     Found: {index_instruments}")
        
        # Test pricing per categoria
        print(f"\n3. TESTING PRICING DATA...")
        
        # Test forex
        if forex_instruments:
            test_forex = forex_instruments[0]  # EUR_USD o simile
            print(f"   Testing {test_forex}...")
            try:
                prices = await signal_engine.oanda_client.get_current_prices([test_forex])
                if prices:
                    price = prices[0]
                    print(f"   [OK] {test_forex}: bid={price.bid}, ask={price.ask}, mid={price.mid}")
                else:
                    print(f"   [FAIL] No pricing data for {test_forex}")
            except Exception as e:
                print(f"   [FAIL] Error getting {test_forex} price: {e}")
            
        # Test metalli
        if metal_instruments:
            test_metal = metal_instruments[0]
            print(f"   Testing {test_metal}...")
            try:
                prices = await signal_engine.oanda_client.get_current_prices([test_metal])
                if prices:
                    price = prices[0]
                    print(f"   [OK] {test_metal}: bid={price.bid}, ask={price.ask}, mid={price.mid}")
                else:
                    print(f"   [FAIL] No pricing data for {test_metal}")
            except Exception as e:
                print(f"   [FAIL] Error getting {test_metal} price: {e}")
            
            # Test indici
            if index_instruments:
                test_index = index_instruments[0]
                print(f"   Testing {test_index}...")
                try:
                    prices = await signal_engine.oanda_client.get_current_prices([test_index])
                    if prices:
                        price = prices[0]
                        print(f"   [OK] {test_index}: bid={price.bid}, ask={price.ask}, mid={price.mid}")
                    else:
                        print(f"   [FAIL] No pricing data for {test_index}")
                except Exception as e:
                    print(f"   [FAIL] Error getting {test_index} price: {e}")
            
            # Test generazione segnale singolo
            print(f"\n4. TESTING SIGNAL GENERATION...")
            test_instruments = []
            if forex_instruments: test_instruments.append(forex_instruments[0])
            if metal_instruments: test_instruments.append(metal_instruments[0])  
            if index_instruments: test_instruments.append(index_instruments[0])
            
            for instrument in test_instruments[:3]:  # Test max 3 per velocità
                print(f"   Testing signal generation for {instrument}...")
                try:
                    signal = await signal_engine.generate_signal(instrument)
                    if signal:
                        print(f"   [OK] {instrument}: {signal.signal_type} at {signal.entry_price}, confidence: {signal.confidence_score}%")
                    else:
                        print(f"   [FAIL] No signal generated for {instrument}")
                except Exception as e:
                    print(f"   [FAIL] Error generating signal for {instrument}: {e}")
            
            print(f"\n=== DEBUG COMPLETATO ===")
            
    except Exception as e:
        print(f"ERRORE GENERALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_signal_generation())