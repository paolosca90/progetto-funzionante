#!/usr/bin/env python3
"""
Verifica i dati dei segnali salvati nel database per identificare problemi
"""

import asyncio
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/trading_signals")

def check_database_signals():
    """Controlla i segnali nel database per problemi"""
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            print("CHECKING DATABASE SIGNALS FOR PRICING ISSUES")
            print("="*80)
            
            # Query per recuperare segnali recenti
            query = text("""
                SELECT 
                    id,
                    symbol,
                    signal_type,
                    entry_price,
                    stop_loss,
                    take_profit,
                    risk_reward_ratio,
                    created_at,
                    source
                FROM signals 
                WHERE created_at >= NOW() - INTERVAL '7 days'
                ORDER BY created_at DESC
                LIMIT 50
            """)
            
            result = db.execute(query)
            signals = result.fetchall()
            
            print(f"Found {len(signals)} signals from last 7 days")
            print("-"*80)
            
            issues_found = []
            
            for signal in signals:
                signal_id = signal[0]
                symbol = signal[1]
                signal_type = signal[2]
                entry_price = signal[3]
                stop_loss = signal[4]
                take_profit = signal[5]
                risk_reward = signal[6] or 0
                created_at = signal[7]
                source = signal[8]
                
                print(f"\nSignal {signal_id} - {symbol} ({signal_type}) - {source}")
                print(f"   Entry: {entry_price}")
                print(f"   Stop Loss: {stop_loss}")
                print(f"   Take Profit: {take_profit}")
                print(f"   R/R: {risk_reward}")
                print(f"   Created: {created_at}")
                
                # Controlli di validità
                signal_issues = []
                
                # 1. Valori nulli o zero
                if not entry_price or entry_price <= 0:
                    signal_issues.append("Entry price invalido")
                if not stop_loss or stop_loss <= 0:
                    signal_issues.append("Stop loss invalido")
                if not take_profit or take_profit <= 0:
                    signal_issues.append("Take profit invalido")
                
                # 2. Logica BUY/SELL
                if signal_type == 'BUY' and stop_loss and entry_price:
                    if stop_loss >= entry_price:
                        signal_issues.append(f"BUY: Stop loss ({stop_loss}) >= entry ({entry_price})")
                    if take_profit and take_profit <= entry_price:
                        signal_issues.append(f"BUY: Take profit ({take_profit}) <= entry ({entry_price})")
                        
                elif signal_type == 'SELL' and stop_loss and entry_price:
                    if stop_loss <= entry_price:
                        signal_issues.append(f"SELL: Stop loss ({stop_loss}) <= entry ({entry_price})")
                    if take_profit and take_profit >= entry_price:
                        signal_issues.append(f"SELL: Take profit ({take_profit}) >= entry ({entry_price})")
                
                # 3. Distanze anomale
                if entry_price and stop_loss and take_profit:
                    stop_distance = abs(entry_price - stop_loss)
                    tp_distance = abs(take_profit - entry_price)
                    
                    # Percentuali
                    stop_pct = (stop_distance / entry_price) * 100
                    tp_pct = (tp_distance / entry_price) * 100
                    
                    if stop_pct > 10:  # Stop loss > 10%
                        signal_issues.append(f"Stop loss troppo largo: {stop_pct:.2f}%")
                    elif stop_pct < 0.01:  # Stop loss < 0.01%
                        signal_issues.append(f"Stop loss troppo stretto: {stop_pct:.4f}%")
                    
                    if tp_pct > 20:  # Take profit > 20%
                        signal_issues.append(f"Take profit troppo lontano: {tp_pct:.2f}%")
                    elif tp_pct < 0.01:  # Take profit < 0.01%
                        signal_issues.append(f"Take profit troppo vicino: {tp_pct:.4f}%")
                    
                    # R/R ratio check
                    if stop_distance > 0:
                        calculated_rr = tp_distance / stop_distance
                        if abs(calculated_rr - risk_reward) > 0.5:
                            signal_issues.append(f"R/R mismatch: stored={risk_reward:.2f}, calculated={calculated_rr:.2f}")
                
                if signal_issues:
                    print("   ISSUES FOUND:")
                    for issue in signal_issues:
                        print(f"      - {issue}")
                    issues_found.append({
                        'id': signal_id,
                        'symbol': symbol,
                        'issues': signal_issues
                    })
                else:
                    print("   OK")
            
            # Report finale
            print("\n" + "="*80)
            print("DATABASE ANALYSIS SUMMARY")
            print("="*80)
            print(f"Total signals checked: {len(signals)}")
            print(f"Signals with issues: {len(issues_found)}")
            print(f"Success rate: {((len(signals) - len(issues_found)) / len(signals) * 100):.1f}%")
            
            if issues_found:
                print(f"\nISSUES BY SYMBOL:")
                symbol_issues = {}
                for issue in issues_found:
                    symbol = issue['symbol']
                    if symbol not in symbol_issues:
                        symbol_issues[symbol] = 0
                    symbol_issues[symbol] += 1
                
                for symbol, count in sorted(symbol_issues.items()):
                    print(f"   {symbol}: {count} issues")
            
    except Exception as e:
        print(f"Database connection error: {e}")
        print("Trying with different connection parameters...")
        
        # Try alternative connection
        try:
            # For Railway PostgreSQL
            alt_url = "postgresql://postgres:vJhzOvxCWxRdbVyDOTQlCPrZqxeEyfyp@autorack.proxy.rlwy.net:48439/railway"
            engine = create_engine(alt_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            with SessionLocal() as db:
                # Simple test query
                result = db.execute(text("SELECT COUNT(*) FROM signals"))
                count = result.scalar()
                print(f"Connected to Railway DB - Found {count} total signals")
                
        except Exception as e2:
            print(f"Alternative connection also failed: {e2}")

if __name__ == "__main__":
    check_database_signals()