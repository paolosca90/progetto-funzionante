#!/usr/bin/env python3
"""
Machine Learning Data Storage Module
Gestisce il salvataggio e l'organizzazione dei dati per machine learning
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class MLDataStorage:
    """
    Sistema di archiviazione dati per machine learning
    Salva segnali ad alta affidabilità per training futuri
    """

    def __init__(self, base_path: str = "ml_data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Crea sottodirectory per diversi tipi di dati
        self.signals_path = self.base_path / "signals"
        self.market_data_path = self.base_path / "market_data"
        self.performance_path = self.base_path / "performance"
        
        for path in [self.signals_path, self.market_data_path, self.performance_path]:
            path.mkdir(exist_ok=True)
        
        logger.info(f"ML Data Storage initialized: {self.base_path}")

    def store_high_quality_signal(self, signal_data: Dict) -> bool:
        """
        Archivia segnale ad alta affidabilità (≥70%) per ML
        """
        try:
            reliability = signal_data.get('reliability', 0)
            
            # Verifica soglia ML (70%)
            if reliability < 70:
                return False
            
            # Prepara dati per ML
            ml_record = {
                "timestamp": signal_data.get('timestamp', datetime.now().isoformat()),
                "symbol": signal_data.get('symbol'),
                "signal_type": signal_data.get('signal_type'),
                "reliability": reliability,
                "entry_price": signal_data.get('entry_price'),
                "stop_loss": signal_data.get('stop_loss'),
                "take_profit": signal_data.get('take_profit'),
                "risk_reward": signal_data.get('risk_reward'),
                "timeframe": signal_data.get('timeframe'),
                "technical_scores": signal_data.get('technical_scores', {}),
                "explanation": signal_data.get('explanation'),
                "volume": signal_data.get('volume'),
                "market_conditions": {
                    "volatility": signal_data.get('technical_scores', {}).get('volatility', 0),
                    "trend_strength": signal_data.get('technical_scores', {}).get('trend', 0),
                    "momentum": signal_data.get('technical_scores', {}).get('momentum', 0)
                }
            }
            
            # Nome file basato su timestamp
            timestamp = datetime.now()
            filename = f"signal_{signal_data.get('symbol')}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.signals_path / filename
            
            # Salva il record
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(ml_record, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Segnale ML salvato: {signal_data.get('symbol')} ({reliability}% affidabilità)")
            
            # Aggiorna statistiche
            self._update_ml_stats(signal_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio ML data: {e}")
            return False

    def store_market_context(self, symbol: str, market_data: Dict) -> bool:
        """
        Archivia contesto di mercato per correlazioni ML
        """
        try:
            context_data = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "market_data": market_data,
                "technical_indicators": market_data.get('indicators', {}),
                "price_action": {
                    "open": market_data.get('open'),
                    "high": market_data.get('high'),
                    "low": market_data.get('low'),
                    "close": market_data.get('close'),
                    "volume": market_data.get('volume', 0)
                }
            }
            
            filename = f"market_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.market_data_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Errore salvataggio market context: {e}")
            return False

    def get_ml_dataset(self, symbol: Optional[str] = None, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Recupera dataset ML per training/analisi
        """
        try:
            records = []
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for filepath in self.signals_path.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Filtra per simbolo se specificato
                    if symbol and data.get('symbol') != symbol:
                        continue
                    
                    # Filtra per data
                    timestamp = datetime.fromisoformat(data.get('timestamp', '1970-01-01')).timestamp()
                    if timestamp < cutoff_date:
                        continue
                    
                    records.append(data)
                    
                except Exception as e:
                    logger.warning(f"Errore lettura file ML {filepath}: {e}")
            
            if not records:
                return None
            
            df = pd.DataFrame(records)
            logger.info(f"Dataset ML caricato: {len(df)} record per {symbol or 'tutti i simboli'}")
            
            return df
            
        except Exception as e:
            logger.error(f"Errore caricamento dataset ML: {e}")
            return None

    def get_ml_stats(self) -> Dict:
        """
        Recupera statistiche dei dati ML
        """
        try:
            stats_file = self.base_path / "ml_stats.json"
            
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return {
                "total_signals": 0,
                "signals_by_symbol": {},
                "avg_reliability": 0,
                "last_updated": None
            }
            
        except Exception as e:
            logger.error(f"Errore lettura stats ML: {e}")
            return {}

    def _update_ml_stats(self, signal_data: Dict):
        """
        Aggiorna statistiche ML
        """
        try:
            stats = self.get_ml_stats()
            
            # Aggiorna contatori
            stats["total_signals"] = stats.get("total_signals", 0) + 1
            
            symbol = signal_data.get('symbol')
            if symbol:
                symbol_stats = stats.get("signals_by_symbol", {})
                symbol_stats[symbol] = symbol_stats.get(symbol, 0) + 1
                stats["signals_by_symbol"] = symbol_stats
            
            # Aggiorna timestamp
            stats["last_updated"] = datetime.now().isoformat()
            
            # Salva stats aggiornate
            stats_file = self.base_path / "ml_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Errore aggiornamento stats ML: {e}")

    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Pulizia dati ML vecchi per gestire spazio disco
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for filepath in self.signals_path.glob("*.json"):
                file_time = filepath.stat().st_mtime
                if file_time < cutoff_date:
                    filepath.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🧹 Puliti {deleted_count} file ML obsoleti (>{days_to_keep} giorni)")
                
        except Exception as e:
            logger.error(f"Errore pulizia dati ML: {e}")

# Istanza globale
ml_storage = MLDataStorage()

def get_ml_storage() -> MLDataStorage:
    """Ottieni l'istanza globale del storage ML"""
    return ml_storage