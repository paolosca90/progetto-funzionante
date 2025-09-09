#!/usr/bin/env python3
"""
Automatic Trading Module for ML Data Collection
Esegue automaticamente trade basati sui segnali per raccogliere dati di performance
"""

import os
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
from pathlib import Path
import time

# Configure logging
logger = logging.getLogger(__name__)

class AutoTrader:
    """
    Sistema di trading automatico per raccolta dati ML
    Esegue trade sui segnali ad alta affidabilità per learning
    """

    def __init__(self):
        self.is_connected = False
        self.account_info = None
        self.active_trades = {}  # Track delle posizioni aperte
        self.trade_history = []  # Storico dei trade per ML
        self.ml_data_path = Path("ml_data/trades")
        self.ml_data_path.mkdir(parents=True, exist_ok=True)
        
        # Parametri trading
        self.risk_percentage = 1.0  # Rischio dell'1% del balance per trade
        self.max_spread = 30  # Spread massimo in points
        self.slippage = 10  # Slippage permesso
        
        logger.info("AutoTrader inizializzato per ML data collection")

    def connect_mt5(self) -> bool:
        """Connette a MetaTrader 5"""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Verifica account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Nessun account MT5 connesso")
                return False
            
            self.account_info = account_info._asdict()
            self.is_connected = True
            
            logger.info(f"✅ AutoTrader connesso a MT5")
            logger.info(f"   Account: {account_info.login}")
            logger.info(f"   Server: {account_info.server}")
            logger.info(f"   Balance: ${account_info.balance}")
            logger.info(f"   Equity: ${account_info.equity}")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore connessione AutoTrader MT5: {e}")
            return False

    def execute_signal_trade(self, signal_data: Dict) -> Optional[Dict]:
        """
        Esegue automaticamente un trade basato su un segnale ML
        Solo per segnali ad alta affidabilità (≥70%) su account demo
        REGOLE: 
        - Un trade per asset alla volta
        - Solo in orari di mercato
        - Tracking completo TP/SL
        """
        try:
            if not self.is_connected:
                if not self.connect_mt5():
                    return None
            
            # Verifica che sia account demo
            if not self._is_demo_account():
                logger.warning("🚫 AutoTrader funziona solo su account DEMO per sicurezza")
                return None
            
            # Verifica orari di mercato
            if not self._is_market_open():
                logger.info("🕐 Trading automatico sospeso: mercati chiusi (weekend/festivi)")
                return None
            
            reliability = signal_data.get('reliability', 0)
            if reliability < 70:
                logger.info(f"Segnale {signal_data.get('symbol')} non eseguito (affidabilità {reliability}% < 70%)")
                return None
            
            symbol = signal_data.get('symbol')
            
            # REGOLA: Un trade per asset - controlla se già aperto
            if self._has_active_trade_for_symbol(symbol):
                logger.info(f"⚠️ Trade già attivo per {symbol} - segnale ignorato")
                return None
            
            symbol = signal_data.get('symbol')
            signal_type = signal_data.get('signal_type')
            entry_price = signal_data.get('entry_price', 0)
            stop_loss = signal_data.get('stop_loss', 0)
            take_profit = signal_data.get('take_profit', 0)
            
            # Verifica simbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Simbolo {symbol} non trovato su MT5")
                return None
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"Impossibile selezionare simbolo {symbol}")
                    return None
            
            # Determina tipo operazione
            if signal_type.upper() == "BUY":
                trade_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            elif signal_type.upper() == "SELL":
                trade_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                logger.info(f"Segnale HOLD per {symbol} - nessun trade eseguito")
                return None
            
            # Verifica spread
            spread = symbol_info.spread
            if spread > self.max_spread:
                logger.warning(f"Spread troppo alto per {symbol}: {spread} points")
                return None
            
            # Calcola TP/SL intelligenti basati su volatilità e market structure
            smart_sl, smart_tp = self._calculate_smart_stops(symbol, price, signal_type.upper(), stop_loss, take_profit)
            
            # Calcola volume basato su rischio dell'1%
            volume = self._calculate_risk_based_volume(symbol, price, smart_sl)
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": trade_type,
                "price": price,
                "sl": smart_sl,
                "tp": smart_tp,
                "deviation": self.slippage,
                "magic": 987654321,  # Magic number per identificare trade ML
                "comment": f"ML_AUTO_{reliability}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Debug logging per troubleshoot invalid stops
            logger.info(f"🔧 DEBUG Trade Request per {symbol}:")
            logger.info(f"   Price: {price}")
            logger.info(f"   SL: {stop_loss} (distance: {abs(price-stop_loss) if stop_loss > 0 else 0})")
            logger.info(f"   TP: {take_profit} (distance: {abs(price-take_profit) if take_profit > 0 else 0})")
            logger.info(f"   Symbol info: spread={symbol_info.spread}, stops_level={getattr(symbol_info, 'stops_level', 'N/A')}")
            
            # Esegue il trade
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Trade fallito per {symbol}: {result.retcode} - {result.comment}")
                return None
            
            # Trade eseguito con successo
            trade_data = {
                "ticket": result.order,
                "symbol": symbol,
                "signal_type": signal_type,
                "volume": volume,
                "open_price": result.price,
                "sl": stop_loss,
                "tp": take_profit,
                "reliability": reliability,
                "open_time": datetime.now().isoformat(),
                "signal_data": signal_data,
                "spread": spread,
                "magic": request["magic"]
            }
            
            # Salva nei trade attivi
            self.active_trades[result.order] = trade_data
            
            # Log del successo
            logger.info(f"🎯 Trade ML eseguito: {signal_type} {symbol}")
            logger.info(f"   Ticket: {result.order}")
            logger.info(f"   Volume: {volume}")
            logger.info(f"   Prezzo: {result.price}")
            logger.info(f"   Affidabilità: {reliability}%")
            
            return trade_data
            
        except Exception as e:
            logger.error(f"Errore esecuzione trade automatico: {e}")
            return None

    def check_and_close_trades(self) -> List[Dict]:
        """
        Controlla trade aperti e raccoglie risultati per ML
        """
        if not self.is_connected:
            return []
        
        closed_trades = []
        
        try:
            # Get posizioni aperte
            positions = mt5.positions_get()
            if positions is None:
                positions = []
            
            # Controlla trade attivi
            active_tickets = list(self.active_trades.keys())
            position_tickets = [pos.ticket for pos in positions]
            
            # Trova trade chiusi
            for ticket in active_tickets:
                if ticket not in position_tickets:
                    # Trade è stato chiuso
                    trade_data = self.active_trades[ticket]
                    
                    # Ottieni dettagli chiusura da history
                    if mt5.history_deals_get(ticket=ticket):
                        deals = mt5.history_deals_get(ticket=ticket)
                        if deals and len(deals) >= 2:  # Open + close
                            close_deal = deals[-1]  # Ultimo deal = chiusura
                            
                            # Calcola risultati
                            trade_result = self._calculate_trade_result(trade_data, close_deal)
                            closed_trades.append(trade_result)
                            
                            # Salva per ML
                            self._save_ml_trade_data(trade_result)
                            
                            logger.info(f"📊 Trade ML chiuso: {trade_result['symbol']}")
                            logger.info(f"   Ticket: {ticket}")
                            logger.info(f"   P&L: ${trade_result['profit']:.2f}")
                            logger.info(f"   Durata: {trade_result['duration_minutes']} min")
                    
                    # Rimuovi dai trade attivi
                    del self.active_trades[ticket]
            
            return closed_trades
            
        except Exception as e:
            logger.error(f"Errore controllo trade chiusi: {e}")
            return []

    def _is_demo_account(self) -> bool:
        """Verifica se l'account è demo per sicurezza"""
        if not self.account_info:
            return False
        
        # Controlla se è account demo
        # Di solito gli account demo hanno trade_mode = ACCOUNT_TRADE_MODE_DEMO
        account_info = mt5.account_info()
        if account_info:
            return account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
        
        return False

    def _calculate_trade_result(self, trade_data: Dict, close_deal) -> Dict:
        """Calcola risultati del trade per ML"""
        open_time = datetime.fromisoformat(trade_data['open_time'])
        close_time = datetime.fromtimestamp(close_deal.time)
        duration = close_time - open_time
        
        return {
            **trade_data,
            "close_price": close_deal.price,
            "close_time": close_time.isoformat(),
            "duration_minutes": int(duration.total_seconds() / 60),
            "profit": close_deal.profit,
            "was_profitable": close_deal.profit > 0,
            "hit_sl": abs(close_deal.price - trade_data['sl']) < 0.0001 if trade_data['sl'] > 0 else False,
            "hit_tp": abs(close_deal.price - trade_data['tp']) < 0.0001 if trade_data['tp'] > 0 else False,
            "signal_accuracy": self._calculate_signal_accuracy(trade_data, close_deal)
        }

    def _calculate_signal_accuracy(self, trade_data: Dict, close_deal) -> float:
        """Calcola accuratezza del segnale per ML feedback"""
        signal_type = trade_data['signal_type'].upper()
        open_price = trade_data['open_price']
        close_price = close_deal.price
        
        if signal_type == "BUY":
            return ((close_price - open_price) / open_price) * 100
        elif signal_type == "SELL":
            return ((open_price - close_price) / open_price) * 100
        else:
            return 0.0

    def _has_active_trade_for_symbol(self, symbol: str) -> bool:
        """Verifica se esiste già un trade attivo per questo simbolo"""
        for trade_data in self.active_trades.values():
            if trade_data.get('symbol') == symbol:
                return True
        return False

    def _is_market_open(self) -> bool:
        """Verifica se i mercati sono aperti (no weekend)"""
        now = datetime.now()
        
        # Forex aperto dalla domenica sera al venerdì sera
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        if weekday == 5:  # Saturday - chiuso
            return False
        elif weekday == 6:  # Sunday
            # Aperto dalle 22:00 di domenica
            return now.hour >= 22
        elif weekday == 4:  # Friday  
            # Chiude alle 22:00 di venerdì
            return now.hour < 22
        else:
            # Lunedì-Giovedì sempre aperto
            return True

    def _save_ml_trade_data(self, trade_result: Dict):
        """Salva risultati trade per machine learning"""
        try:
            filename = f"trade_{trade_result['ticket']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.ml_data_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trade_result, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Errore salvataggio trade ML data: {e}")

    def get_ml_trading_stats(self) -> Dict:
        """Ottieni statistiche trading per ML"""
        try:
            trade_files = list(self.ml_data_path.glob("trade_*.json"))
            
            if not trade_files:
                return {
                    "total_trades": 0,
                    "profitable_trades": 0,
                    "total_profit": 0,
                    "win_rate": 0,
                    "avg_duration_minutes": 0
                }
            
            trades = []
            for file in trade_files:
                with open(file, 'r', encoding='utf-8') as f:
                    trades.append(json.load(f))
            
            profitable = [t for t in trades if t.get('was_profitable', False)]
            total_profit = sum(t.get('profit', 0) for t in trades)
            avg_duration = sum(t.get('duration_minutes', 0) for t in trades) / len(trades) if trades else 0
            
            return {
                "total_trades": len(trades),
                "profitable_trades": len(profitable),
                "total_profit": round(total_profit, 2),
                "win_rate": round((len(profitable) / len(trades) * 100), 1) if trades else 0,
                "avg_duration_minutes": round(avg_duration, 1)
            }
            
        except Exception as e:
            logger.error(f"Errore calcolo stats ML trading: {e}")
            return {}

    def cleanup_old_trade_data(self, days_to_keep: int = 30):
        """Pulizia dati trade obsoleti"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for filepath in self.ml_data_path.glob("trade_*.json"):
                file_time = filepath.stat().st_mtime
                if file_time < cutoff_date:
                    filepath.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🧹 Puliti {deleted_count} file trade ML obsoleti")
                
        except Exception as e:
            logger.error(f"Errore pulizia trade data: {e}")

    def _calculate_smart_stops(self, symbol: str, entry_price: float, signal_type: str, suggested_sl: float, suggested_tp: float) -> tuple:
        """
        Calcola stop loss e take profit intelligenti basati su:
        - Volatilità ATR del simbolo
        - Stops level minimi di MT5
        - Market structure professionale
        - Risk/Reward ratio ottimale (1:2 minimo)
        """
        try:
            # Ottieni info simbolo da MT5
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                # Fallback ai valori suggeriti se simbolo non trovato
                return suggested_sl, suggested_tp
            
            # Parametri del simbolo
            point = symbol_info.point
            stops_level = getattr(symbol_info, 'stops_level', 0)
            min_distance = stops_level * point if stops_level > 0 else (50 * point)  # Minimo 50 points se non specificato
            
            # Calcola ATR estimate professionale per il simbolo
            atr_estimate = self._get_atr_for_symbol(symbol, entry_price)
            
            # Strategia professionale: SL basato su ATR, TP 2:1 ratio
            if signal_type == "BUY":
                # BUY: SL sotto entry, TP sopra entry
                sl_distance = max(atr_estimate * 1.2, min_distance)  # 1.2x ATR o minimo MT5
                tp_distance = sl_distance * 2.0  # Risk/Reward 1:2
                
                smart_sl = round(entry_price - sl_distance, symbol_info.digits)
                smart_tp = round(entry_price + tp_distance, symbol_info.digits)
                
            elif signal_type == "SELL":
                # SELL: SL sopra entry, TP sotto entry  
                sl_distance = max(atr_estimate * 1.2, min_distance)  # 1.2x ATR o minimo MT5
                tp_distance = sl_distance * 2.0  # Risk/Reward 1:2
                
                smart_sl = round(entry_price + sl_distance, symbol_info.digits)
                smart_tp = round(entry_price - tp_distance, symbol_info.digits)
            else:
                return 0, 0  # HOLD - no stops
            
            # Verifica che i livelli rispettino i requisiti MT5
            if signal_type == "BUY":
                actual_sl_distance = entry_price - smart_sl
                actual_tp_distance = smart_tp - entry_price
            else:  # SELL
                actual_sl_distance = smart_sl - entry_price
                actual_tp_distance = entry_price - smart_tp
            
            # Assicura che rispetti il minimum distance
            if actual_sl_distance < min_distance or actual_tp_distance < min_distance:
                logger.warning(f"⚠️ Adjusting stops for {symbol} minimum distance: {min_distance}")
                # Usa valori conservativi se troppo stretti
                if signal_type == "BUY":
                    smart_sl = round(entry_price - (min_distance * 1.5), symbol_info.digits)
                    smart_tp = round(entry_price + (min_distance * 3.0), symbol_info.digits)
                else:
                    smart_sl = round(entry_price + (min_distance * 1.5), symbol_info.digits)
                    smart_tp = round(entry_price - (min_distance * 3.0), symbol_info.digits)
            
            logger.info(f"🎯 Smart Stops per {symbol}:")
            logger.info(f"   SL: {smart_sl} (distance: {abs(entry_price - smart_sl):.5f})")
            logger.info(f"   TP: {smart_tp} (distance: {abs(smart_tp - entry_price):.5f})")
            logger.info(f"   R/R: {abs(smart_tp - entry_price) / abs(entry_price - smart_sl):.1f}:1")
            
            return smart_sl, smart_tp
            
        except Exception as e:
            logger.error(f"Errore calcolo smart stops: {e}")
            # Fallback ai valori suggeriti
            return suggested_sl, suggested_tp

    def _calculate_risk_based_volume(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        """
        Calcola il volume basato sul rischio dell'1% del balance
        Formula: Volume = (Risk Amount) / (Stop Loss Distance in USD * Contract Size)
        """
        try:
            if not self.account_info:
                # Fallback a volume minimo se non abbiamo info account
                return 0.01
            
            # Rischio massimo: 1% del balance
            balance = self.account_info.get('balance', 1000)  # Default 1000 se non disponibile
            risk_amount = balance * (self.risk_percentage / 100)
            
            # Se non abbiamo stop loss, usa volume minimo per sicurezza
            if stop_loss == 0 or stop_loss is None:
                return 0.01
            
            # Calcola distanza stop loss
            sl_distance = abs(entry_price - stop_loss)
            if sl_distance == 0:
                return 0.01
            
            # Ottieni info simbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return 0.01
            
            # Calcola il valore per pip/point
            if symbol_info.trade_contract_size > 0:
                # Per la maggior parte degli strumenti
                pip_value = symbol_info.trade_contract_size * sl_distance
                volume = risk_amount / pip_value
            else:
                # Fallback per simboli senza contract size
                volume = 0.01
            
            # Limiti di sicurezza
            min_volume = symbol_info.volume_min if symbol_info.volume_min > 0 else 0.01
            max_volume = min(symbol_info.volume_max if symbol_info.volume_max > 0 else 100, balance / 1000)  # Massimo basato su balance
            
            # Arrotonda al volume step
            volume_step = symbol_info.volume_step if symbol_info.volume_step > 0 else 0.01
            volume = round(volume / volume_step) * volume_step
            
            # Applica limiti
            volume = max(min_volume, min(volume, max_volume))
            
            logger.info(f"💰 Volume calcolato per {symbol}:")
            logger.info(f"   Balance: ${balance}")
            logger.info(f"   Risk amount (1%): ${risk_amount:.2f}")
            logger.info(f"   SL distance: {sl_distance:.5f}")
            logger.info(f"   Volume calcolato: {volume}")
            
            return volume
            
        except Exception as e:
            logger.error(f"Errore calcolo volume basato su risk: {e}")
            # Fallback a volume minimo
            return 0.01

    def _get_atr_for_symbol(self, symbol: str, price: float) -> float:
        """Calcola ATR estimate per il simbolo"""
        # ATR professionali per intraday trading
        atr_values = {
            # Forex Major Pairs
            "EURUSD": 0.0015,  # ~15 pips
            "GBPUSD": 0.0020,  # ~20 pips  
            "USDJPY": 0.15,    # ~15 pips (JPY)
            "USDCHF": 0.0012,  # ~12 pips
            "AUDUSD": 0.0018,  # ~18 pips
            "USDCAD": 0.0016,  # ~16 pips
            "NZDUSD": 0.0020,  # ~20 pips
            "EURJPY": 0.18,    # ~18 pips (JPY)
            "GBPJPY": 0.25,    # ~25 pips (JPY)
            
            # Commodities
            "XAUUSD": 8.0,     # Gold: ~$8 range tipico per intraday
            
            # US Indices  
            "US30": 80.0,      # Dow Jones: ~80 points
            "NAS100": 50.0,    # NASDAQ: ~50 points
            "SPX500": 15.0,    # S&P500: ~15 points
        }
        
        if symbol in atr_values:
            return atr_values[symbol]
        else:
            # Default basato sul tipo di asset
            if "JPY" in symbol:
                return 0.16  # ~16 pips per JPY pairs
            elif symbol.startswith("XAU") or "GOLD" in symbol:
                return 8.0   # Gold default
            elif any(idx in symbol for idx in ["US30", "NAS100", "SPX500", "US500"]):
                return 50.0  # Indices default
            else:
                return 0.0016  # ~16 pips per non-JPY forex

    def disconnect(self):
        """Disconnette da MT5"""
        if self.is_connected:
            mt5.shutdown()
            self.is_connected = False
            logger.info("AutoTrader disconnesso da MT5")

# Istanza globale
auto_trader = AutoTrader()

def get_auto_trader() -> AutoTrader:
    """Ottieni l'istanza globale dell'auto trader"""
    return auto_trader