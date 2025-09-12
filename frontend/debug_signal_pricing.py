#!/usr/bin/env python3
"""
Debug script per testare i calcoli di stop loss e entry price per tutti gli asset
"""

import asyncio
import logging
import os
from datetime import datetime
from oanda_signal_engine import OANDASignalEngine, SignalType
from oanda_api_client import create_oanda_client

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_signal_pricing():
    """Testa i prezzi dei segnali per tutti gli asset"""
    
    # Configurazione OANDA (using same credentials as debug scripts)
    api_key = "9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286"
    account_id = "101-004-37029911-001"
    environment = "practice"
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"TESTING SIGNAL PRICING")
    print(f"   Environment: {environment}")
    print(f"   Account: {account_id}")
    print(f"   Time: {datetime.now()}")
    print("="*80)
    
    # Lista completa degli asset da testare
    instruments = [
        # Major forex pairs
        "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD", "NZD_USD", "EUR_GBP",
        # Cross pairs and exotics
        "EUR_AUD", "EUR_CHF", "GBP_JPY", "AUD_JPY", "EUR_JPY", "GBP_AUD", 
        "USD_CHF", "CHF_JPY", "AUD_CAD", "CAD_JPY", "EUR_CAD", "GBP_CAD",
        # Precious Metals
        "XAU_USD", "XAG_USD",
        # Major Indices
        "US30_USD", "NAS100_USD", "SPX500_USD", "DE30_EUR"
    ]
    
    async with OANDASignalEngine(api_key, account_id, environment, gemini_api_key) as engine:
        print(f"\n1. ENGINE INITIALIZATION")
        health = await engine.health_check()
        print(f"   Health check: {'OK' if health else 'FAILED'}")
        
        if not health:
            print("Engine health check failed - aborting")
            return
        
        print(f"\n2. TESTING ALL INSTRUMENTS ({len(instruments)} total)")
        print("-" * 80)
        
        issues_found = []
        successful_signals = []
        
        for i, instrument in enumerate(instruments, 1):
            try:
                print(f"\n[{i:2d}/{len(instruments)}] Testing {instrument}")
                
                # Genera segnale
                signal = await engine.generate_signal(instrument, "H1")
                
                if not signal:
                    print(f"   FAILED: Signal generation failed for {instrument}")
                    issues_found.append(f"{instrument}: Signal generation failed")
                    continue
                
                # Analizza i prezzi
                entry_price = signal.entry_price
                stop_loss = signal.stop_loss  
                take_profit = signal.take_profit
                signal_type = signal.signal_type.value
                
                print(f"   Signal: {signal_type}")
                print(f"   Entry: {entry_price:.5f}")
                print(f"   Stop Loss: {stop_loss:.5f}")
                print(f"   Take Profit: {take_profit:.5f}")
                print(f"   R/R Ratio: {signal.risk_reward_ratio:.2f}")
                print(f"   ATR: {signal.technical_analysis.atr:.5f}")
                print(f"   Spread: {signal.market_context.spread:.5f}")
                
                # Controlli di validità
                issues = []
                
                # 1. Check se i prezzi sono validi (non zero, non negativi)
                if entry_price <= 0:
                    issues.append("Entry price non valido (<=0)")
                if stop_loss <= 0:
                    issues.append("Stop loss non valido (<=0)")
                if take_profit <= 0:
                    issues.append("Take profit non valido (<=0)")
                
                # 2. Check logica dei prezzi per BUY/SELL
                if signal_type == "BUY":
                    if stop_loss >= entry_price:
                        issues.append(f"BUY: Stop loss ({stop_loss:.5f}) dovrebbe essere < entry ({entry_price:.5f})")
                    if take_profit <= entry_price:
                        issues.append(f"BUY: Take profit ({take_profit:.5f}) dovrebbe essere > entry ({entry_price:.5f})")
                elif signal_type == "SELL":
                    if stop_loss <= entry_price:
                        issues.append(f"SELL: Stop loss ({stop_loss:.5f}) dovrebbe essere > entry ({entry_price:.5f})")
                    if take_profit >= entry_price:
                        issues.append(f"SELL: Take profit ({take_profit:.5f}) dovrebbe essere < entry ({entry_price:.5f})")
                
                # 3. Check se le distanze sono ragionevoli (non troppo strette/larghe)
                stop_distance = abs(entry_price - stop_loss)
                profit_distance = abs(take_profit - entry_price)
                
                # Distanza stop loss dovrebbe essere ragionevole rispetto al prezzo
                stop_pct = (stop_distance / entry_price) * 100
                if stop_pct < 0.01:  # Meno di 0.01%
                    issues.append(f"Stop loss troppo stretto: {stop_pct:.4f}%")
                elif stop_pct > 10:  # Più di 10%
                    issues.append(f"Stop loss troppo largo: {stop_pct:.2f}%")
                
                # 4. Check risk/reward ratio
                if signal.risk_reward_ratio <= 0:
                    issues.append("Risk/reward ratio non valido (<=0)")
                elif signal.risk_reward_ratio < 0.5:
                    issues.append(f"Risk/reward ratio troppo basso: {signal.risk_reward_ratio:.2f}")
                elif signal.risk_reward_ratio > 10:
                    issues.append(f"Risk/reward ratio troppo alto: {signal.risk_reward_ratio:.2f}")
                
                # 5. Check ATR sanity
                atr_pct = (signal.technical_analysis.atr / entry_price) * 100
                if atr_pct < 0.001:  # ATR troppo piccolo
                    issues.append(f"ATR troppo piccolo: {atr_pct:.6f}%")
                elif atr_pct > 5:  # ATR troppo grande
                    issues.append(f"ATR troppo grande: {atr_pct:.2f}%")
                
                if issues:
                    print(f"   WARNING: ISSUES FOUND:")
                    for issue in issues:
                        print(f"      - {issue}")
                    issues_found.extend([f"{instrument}: {issue}" for issue in issues])
                else:
                    print(f"   OK: All checks passed")
                    successful_signals.append(instrument)
                
                # Piccola pausa per rispettare i rate limits
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"   ERROR: {e}")
                issues_found.append(f"{instrument}: Exception - {str(e)}")
                continue
        
        # Report finale
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80)
        print(f"Successful signals: {len(successful_signals)}/{len(instruments)}")
        print(f"Issues found: {len(issues_found)}")
        
        if successful_signals:
            print(f"\nWORKING CORRECTLY:")
            for instr in successful_signals:
                print(f"   - {instr}")
        
        if issues_found:
            print(f"\nISSUES DETECTED:")
            for issue in issues_found:
                print(f"   - {issue}")
        
        print(f"\nSUCCESS RATE: {(len(successful_signals)/len(instruments)*100):.1f}%")

if __name__ == "__main__":
    asyncio.run(test_signal_pricing())