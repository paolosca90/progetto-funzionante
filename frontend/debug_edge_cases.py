#!/usr/bin/env python3
"""
Test per identificare problemi specifici con stop loss e entry price in casi edge
"""

import asyncio
import logging
from oanda_signal_engine import OANDASignalEngine, SignalType
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_edge_cases():
    """Test casi edge specifici"""
    
    # Credenziali
    api_key = "9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286"
    account_id = "101-004-37029911-001"
    environment = "practice"
    
    print("TESTING EDGE CASES FOR SIGNAL PRICING")
    print("="*80)
    
    # Test con strumenti che potrebbero avere problemi
    problematic_cases = [
        # Forex con spread wide
        ("EUR_TRY", "Exotic pair with wide spreads"),
        ("USD_SEK", "Nordic currency"),
        ("USD_NOK", "Nordic currency"),
        ("USD_PLN", "Eastern European"),
        
        # Metalli preziosi in sessioni diverse
        ("XAU_USD", "Gold during different market hours"),
        ("XAG_USD", "Silver volatility test"),
        
        # Indici durante notizie
        ("US30_USD", "Dow Jones high volatility"),
        ("NAS100_USD", "NASDAQ tech volatility"),
        ("SPX500_USD", "S&P 500 standard"),
        
        # Cross pairs complessi
        ("GBP_CHF", "Complex cross pair"),
        ("EUR_NOK", "EUR vs Nordic"),
        ("AUD_NZD", "Commodity currencies"),
    ]
    
    async with OANDASignalEngine(api_key, account_id, environment) as engine:
        print(f"\nTesting {len(problematic_cases)} potentially problematic cases:")
        print("-"*80)
        
        results = []
        
        for i, (instrument, description) in enumerate(problematic_cases, 1):
            try:
                print(f"\n[{i:2d}] {instrument} - {description}")
                
                # Genera più segnali con timeframe diversi
                for tf in ["H1", "H4"]:
                    try:
                        signal = await engine.generate_signal(instrument, tf)
                        
                        if not signal:
                            print(f"   {tf}: No signal generated")
                            continue
                        
                        entry = signal.entry_price
                        stop = signal.stop_loss
                        tp = signal.take_profit
                        signal_type = signal.signal_type.value
                        atr = signal.technical_analysis.atr
                        spread = signal.market_context.spread
                        
                        print(f"   {tf}: {signal_type} | Entry:{entry:.5f} | SL:{stop:.5f} | TP:{tp:.5f}")
                        print(f"       ATR:{atr:.5f} | Spread:{spread:.5f} | R/R:{signal.risk_reward_ratio:.2f}")
                        
                        # Analisi dettagliata
                        stop_distance = abs(entry - stop)
                        tp_distance = abs(tp - entry)
                        
                        # Percentuali
                        stop_pct = (stop_distance / entry) * 100
                        tp_pct = (tp_distance / entry) * 100
                        spread_pct = (spread / entry) * 100
                        atr_pct = (atr / entry) * 100
                        
                        print(f"       Stop: {stop_pct:.3f}% | TP: {tp_pct:.3f}% | Spread: {spread_pct:.4f}% | ATR: {atr_pct:.3f}%")
                        
                        # Identifica problemi potenziali
                        issues = []
                        
                        # Stop loss troppo vicino allo spread
                        if stop_distance < spread * 3:
                            issues.append(f"Stop troppo vicino allo spread ({stop_distance:.5f} vs {spread:.5f})")
                        
                        # ATR troppo piccolo o grande rispetto al prezzo
                        if atr_pct < 0.01:
                            issues.append(f"ATR estremamente piccolo: {atr_pct:.6f}%")
                        elif atr_pct > 5:
                            issues.append(f"ATR estremamente grande: {atr_pct:.2f}%")
                        
                        # R/R fuori dai limiti normali
                        if signal.risk_reward_ratio > 5 or signal.risk_reward_ratio < 0.5:
                            issues.append(f"R/R anomalo: {signal.risk_reward_ratio:.2f}")
                        
                        # Stop loss logica inversa
                        if signal_type == "BUY" and stop >= entry:
                            issues.append("BUY con stop >= entry")
                        elif signal_type == "SELL" and stop <= entry:
                            issues.append("SELL con stop <= entry")
                        
                        # Take profit logica inversa  
                        if signal_type == "BUY" and tp <= entry:
                            issues.append("BUY con TP <= entry")
                        elif signal_type == "SELL" and tp >= entry:
                            issues.append("SELL con TP >= entry")
                        
                        if issues:
                            print(f"       ISSUES: {'; '.join(issues)}")
                            results.append({
                                'instrument': instrument,
                                'timeframe': tf,
                                'issues': issues,
                                'data': {
                                    'entry': entry,
                                    'stop': stop, 
                                    'tp': tp,
                                    'signal_type': signal_type,
                                    'atr': atr,
                                    'spread': spread,
                                    'rr': signal.risk_reward_ratio
                                }
                            })
                        else:
                            print(f"       OK")
                        
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        print(f"   {tf}: ERROR - {e}")
                        
            except Exception as e:
                print(f"   GENERAL ERROR: {e}")
        
        # Report finale
        print("\n" + "="*80)
        print("EDGE CASES ANALYSIS RESULTS")
        print("="*80)
        
        if not results:
            print("No issues found in edge cases testing")
        else:
            print(f"Found {len(results)} potential issues:")
            for result in results:
                print(f"\n{result['instrument']} ({result['timeframe']}):")
                for issue in result['issues']:
                    print(f"  - {issue}")
                print(f"  Data: {result['data']}")

if __name__ == "__main__":
    asyncio.run(test_edge_cases())