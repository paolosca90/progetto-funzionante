"""
Factory classes for creating test signal data.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
from decimal import Decimal

from models import Signal, SignalStatusEnum, SignalTypeEnum


class SignalFactory:
    """Factory for creating test signal instances."""

    # Trading symbols for realistic test data
    SYMBOLS = [
        "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD", "USD_CAD", "NZD_USD",
        "EUR_GBP", "EUR_JPY", "GBP_JPY", "AUD_JPY", "EUR_CHF", "GBP_CHF"
    ]

    # Risk levels
    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]

    # Signal sources
    SOURCES = ["OANDA_AI", "MANUAL", "API", "ALGORITHM", "EXTERNAL"]

    # Timeframes
    TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN"]

    # Market sessions
    MARKET_SESSIONS = ["Sydney", "Tokyo", "London", "New York", "Overlap"]

    @staticmethod
    def create_signal_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create signal data dictionary with optional overrides.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with signal data
        """
        symbol = random.choice(SignalFactory.SYMBOLS)
        signal_type = random.choice(list(SignalTypeEnum))
        risk_level = random.choice(SignalFactory.RISK_LEVELS)
        source = random.choice(SignalFactory.SOURCES)
        timeframe = random.choice(SignalFactory.TIMEFRAMES)
        market_session = random.choice(SignalFactory.MARKET_SESSIONS)

        # Generate realistic price data
        base_price = round(random.uniform(0.5, 150.0), 4)
        spread = round(random.uniform(0.0001, 0.0050), 4)
        volatility = round(random.uniform(0.05, 0.5), 2)

        # Calculate entry, stop loss, and take profit
        entry_price = base_price
        if signal_type == SignalTypeEnum.BUY:
            stop_loss = round(base_price * (1 - random.uniform(0.001, 0.005)), 4)
            take_profit = round(base_price * (1 + random.uniform(0.002, 0.01)), 4)
        elif signal_type == SignalTypeEnum.SELL:
            stop_loss = round(base_price * (1 + random.uniform(0.001, 0.005)), 4)
            take_profit = round(base_price * (1 - random.uniform(0.002, 0.01)), 4)
        else:  # HOLD
            stop_loss = round(base_price * (1 - random.uniform(0.002, 0.008)), 4)
            take_profit = round(base_price * (1 + random.uniform(0.002, 0.008)), 4)

        # Calculate risk/reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward_ratio = round(reward / risk if risk > 0 else 2.0, 2)

        # Calculate position size suggestion
        position_size_suggestion = f"{random.uniform(0.01, 1.0):.2f} lots"

        # Generate technical indicators
        rsi = round(random.uniform(20, 80), 1)
        macd_signal = round(random.uniform(-0.01, 0.01), 4)
        technical_score = round(random.uniform(0, 100), 0)

        # Calculate reliability and confidence
        reliability = round(random.uniform(50, 95), 1)
        confidence_score = round(random.uniform(0.5, 0.95), 2)

        # Generate AI analysis text
        analysis_templates = [
            f"Technical analysis for {symbol} on {timeframe} timeframe shows {signal_type.lower()} opportunity with {risk_level.lower()} risk.",
            f"Market conditions indicate {signal_type.lower()} signal for {symbol}. Technical indicators support this move with {confidence_score:.0%} confidence.",
            f"AI analysis identifies {signal_type.lower()} opportunity in {symbol} during {market_session} session. RSI at {rsi} suggests market condition.",
            f"Comprehensive analysis of {symbol} reveals {signal_type.lower()} signal with technical score of {technical_score}.",
            f"Algorithm detected {signal_type.lower()} pattern in {symbol} with {risk_level.lower()} risk profile."
        ]
        ai_analysis = random.choice(analysis_templates)

        default_data = {
            "symbol": symbol,
            "signal_type": signal_type,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "reliability": reliability,
            "status": SignalStatusEnum.ACTIVE,
            "ai_analysis": ai_analysis,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "is_public": random.choice([True, False]),
            "is_active": True,
            "source": source,
            "timeframe": timeframe,
            "risk_reward_ratio": risk_reward_ratio,
            "position_size_suggestion": position_size_suggestion,
            "spread": spread,
            "volatility": volatility,
            "technical_score": technical_score,
            "rsi": rsi,
            "macd_signal": macd_signal,
            "market_session": market_session,
            "expires_at": datetime.utcnow() + timedelta(hours=random.randint(1, 48))
        }

        if overrides:
            default_data.update(overrides)

        return default_data

    @staticmethod
    def create_buy_signal_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a buy signal data dictionary.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with buy signal data
        """
        buy_overrides = {"signal_type": SignalTypeEnum.BUY}
        if overrides:
            buy_overrides.update(overrides)

        return SignalFactory.create_signal_data(buy_overrides)

    @staticmethod
    def create_sell_signal_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a sell signal data dictionary.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with sell signal data
        """
        sell_overrides = {"signal_type": SignalTypeEnum.SELL}
        if overrides:
            sell_overrides.update(overrides)

        return SignalFactory.create_signal_data(sell_overrides)

    @staticmethod
    def create_hold_signal_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a hold signal data dictionary.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with hold signal data
        """
        hold_overrides = {"signal_type": SignalTypeEnum.HOLD}
        if overrides:
            hold_overrides.update(overrides)

        return SignalFactory.create_signal_data(hold_overrides)

    @staticmethod
    def create_high_confidence_signal_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a high confidence signal data dictionary.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with high confidence signal data
        """
        high_confidence_overrides = {
            "confidence_score": round(random.uniform(0.8, 0.95), 2),
            "reliability": round(random.uniform(80, 95), 1),
            "risk_level": "LOW"
        }
        if overrides:
            high_confidence_overrides.update(overrides)

        return SignalFactory.create_signal_data(high_confidence_overrides)

    @staticmethod
    def create_expired_signal_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an expired signal data dictionary.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with expired signal data
        """
        expired_overrides = {
            "expires_at": datetime.utcnow() - timedelta(hours=1),
            "status": SignalStatusEnum.EXPIRED
        }
        if overrides:
            expired_overrides.update(overrides)

        return SignalFactory.create_signal_data(expired_overrides)

    @staticmethod
    def create_signals_batch(count: int, distribution: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
        """
        Create a batch of signal data dictionaries.

        Args:
            count: Number of signals to create
            distribution: Dict with signal type distribution (e.g., {"BUY": 5, "SELL": 3, "HOLD": 2})

        Returns:
            List of signal data dictionaries
        """
        signals = []

        if distribution:
            for signal_type, type_count in distribution.items():
                for _ in range(type_count):
                    signal_data = SignalFactory.create_signal_data({"signal_type": SignalTypeEnum(signal_type)})
                    signals.append(signal_data)
        else:
            for _ in range(count):
                signal_data = SignalFactory.create_signal_data()
                signals.append(signal_data)

        return signals

    @staticmethod
    def create_signal_instance(db_session, creator_id: int, overrides: Optional[Dict[str, Any]] = None) -> Signal:
        """
        Create and persist a Signal instance in the database.

        Args:
            db_session: Database session
            creator_id: ID of the user creating the signal
            overrides: Dictionary of values to override defaults

        Returns:
            Signal instance
        """
        signal_data = SignalFactory.create_signal_data(overrides)
        signal_data["creator_id"] = creator_id

        signal = Signal(**signal_data)
        db_session.add(signal)
        db_session.commit()
        db_session.refresh(signal)

        return signal

    @staticmethod
    def create_signals_batch_instances(db_session, creator_id: int, count: int) -> List[Signal]:
        """
        Create and persist a batch of Signal instances in the database.

        Args:
            db_session: Database session
            creator_id: ID of the user creating the signals
            count: Number of signals to create

        Returns:
            List of Signal instances
        """
        signals_data = SignalFactory.create_signals_batch(count)
        signals = []

        for signal_data in signals_data:
            signal_data["creator_id"] = creator_id
            signal = Signal(**signal_data)
            signals.append(signal)

        db_session.add_all(signals)
        db_session.commit()

        for signal in signals:
            db_session.refresh(signal)

        return signals

    @staticmethod
    def create_signals_for_symbols(db_session, creator_id: int, symbols: List[str]) -> List[Signal]:
        """
        Create signals for specific symbols.

        Args:
            db_session: Database session
            creator_id: ID of the user creating the signals
            symbols: List of symbols to create signals for

        Returns:
            List of Signal instances
        """
        signals = []

        for symbol in symbols:
            signal_data = SignalFactory.create_signal_data({"symbol": symbol})
            signal_data["creator_id"] = creator_id
            signal = Signal(**signal_data)
            signals.append(signal)

        db_session.add_all(signals)
        db_session.commit()

        for signal in signals:
            db_session.refresh(signal)

        return signals