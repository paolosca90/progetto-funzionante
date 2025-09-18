from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import asyncio

from models import User, Signal, OANDAConnection, SignalTypeEnum
from app.repositories.signal_repository import SignalRepository
from app.services.cache_service import cache_service

# OANDA imports
try:
    from oanda_signal_engine import OANDASignalEngine, SignalType as OANDASignalType, RiskLevel, create_signal_engine
    from oanda_api_client import OANDAClient, OANDAAPIError, create_oanda_client
    OANDA_AVAILABLE = True
except ImportError:
    OANDA_AVAILABLE = False

logger = logging.getLogger(__name__)


class OANDAService:
    """Service for OANDA trading integration."""

    def __init__(self, db: Session):
        self.db = db
        self.signal_repository = SignalRepository(db)
        self._oanda_client = None
        self._signal_engine = None

    @property
    def oanda_client(self) -> Optional[OANDAClient]:
        """Get or create OANDA client."""
        if not OANDA_AVAILABLE:
            return None

        if self._oanda_client is None:
            try:
                self._oanda_client = create_oanda_client()
            except Exception as e:
                logger.error(f"Failed to create OANDA client: {e}")
                return None

        return self._oanda_client

    @property
    def signal_engine(self) -> Optional[OANDASignalEngine]:
        """Get or create OANDA signal engine."""
        if not OANDA_AVAILABLE:
            return None

        if self._signal_engine is None:
            try:
                self._signal_engine = create_signal_engine()
            except Exception as e:
                logger.error(f"Failed to create OANDA signal engine: {e}")
                return None

        return self._signal_engine

    def check_oanda_health(self) -> Dict[str, Any]:
        """Check OANDA API health and connectivity."""
        if not OANDA_AVAILABLE:
            return {
                "available": False,
                "status": "OANDA integration not available",
                "error": "OANDA modules not imported"
            }

        if not self.oanda_client:
            return {
                "available": False,
                "status": "Failed to create OANDA client",
                "error": "Client initialization failed"
            }

        try:
            # Test connection by getting account info
            account_info = self.oanda_client.get_account_summary()
            return {
                "available": True,
                "status": "Connected",
                "account_id": account_info.get("id"),
                "currency": account_info.get("currency"),
                "balance": account_info.get("balance"),
                "environment": self.oanda_client.environment
            }
        except Exception as e:
            return {
                "available": False,
                "status": "Connection failed",
                "error": str(e)
            }

    def generate_signal(self, symbol: str, user_id: int) -> Optional[Signal]:
        """
        Generate a trading signal for a specific symbol.

        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            user_id: ID of user requesting the signal

        Returns:
            Generated signal or None if failed
        """
        if not OANDA_AVAILABLE or not self.signal_engine:
            logger.error("OANDA signal engine not available")
            return None

        try:
            # Generate signal using OANDA engine
            oanda_signal = self.signal_engine.generate_signal(symbol)

            if not oanda_signal:
                logger.warning(f"No signal generated for {symbol}")
                return None

            # Convert OANDA signal to database signal
            signal_type = self._convert_signal_type(oanda_signal.signal_type)

            # Create signal in database
            signal_data = {
                "symbol": symbol,
                "signal_type": signal_type,
                "entry_price": oanda_signal.entry_price,
                "stop_loss": oanda_signal.stop_loss,
                "take_profit": oanda_signal.take_profit,
                "reliability": oanda_signal.confidence_score * 100,  # Convert to percentage
                "ai_analysis": oanda_signal.ai_commentary,
                "confidence_score": oanda_signal.confidence_score,
                "risk_level": oanda_signal.risk_level.value,
                "source": "OANDA_AI",
                "timeframe": oanda_signal.timeframe or "H1",
                "risk_reward_ratio": oanda_signal.risk_reward_ratio,
                "position_size_suggestion": oanda_signal.position_size,
                "spread": getattr(oanda_signal, 'spread', 0.0),
                "volatility": getattr(oanda_signal, 'volatility', 0.0),
                "technical_score": getattr(oanda_signal, 'technical_score', 0.0),
                "rsi": getattr(oanda_signal, 'rsi', None),
                "macd_signal": getattr(oanda_signal, 'macd_signal', None),
                "market_session": getattr(oanda_signal, 'market_session', None),
                "creator_id": user_id,
                "is_public": True,
                "is_active": True,
                "created_at": datetime.utcnow()
            }

            signal = self.signal_repository.create(signal_data)
            logger.info(f"Generated OANDA signal for {symbol}: {signal.id}")
            return signal

        except Exception as e:
            logger.error(f"Failed to generate signal for {symbol}: {e}")
            return None

    def batch_generate_signals(self, symbols: List[str], user_id: int) -> List[Signal]:
        """
        Generate signals for multiple symbols.

        Args:
            symbols: List of trading symbols
            user_id: ID of user requesting the signals

        Returns:
            List of generated signals
        """
        signals = []
        for symbol in symbols:
            signal = self.generate_signal(symbol, user_id)
            if signal:
                signals.append(signal)

        return signals

    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current market data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Market data dictionary or None if failed
        """
        if not OANDA_AVAILABLE or not self.oanda_client:
            return None

        try:
            # Convert symbol to OANDA format
            oanda_symbol = self._convert_to_oanda_symbol(symbol)

            # Get current price
            price_data = self.oanda_client.get_latest_candles(oanda_symbol, count=1)
            if not price_data:
                return None

            latest_candle = price_data[0]

            return {
                "symbol": symbol,
                "bid": latest_candle.bid.c,
                "ask": latest_candle.ask.c,
                "spread": latest_candle.ask.c - latest_candle.bid.c,
                "timestamp": latest_candle.time,
                "volume": latest_candle.volume
            }

        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None

    def connect_user_account(self, user: User, account_id: str, environment: str = "demo") -> bool:
        """
        Connect user's OANDA account.

        Args:
            user: User object
            account_id: OANDA account ID
            environment: 'demo' or 'live'

        Returns:
            True if connection successful
        """
        if not OANDA_AVAILABLE or not self.oanda_client:
            return False

        try:
            # Validate account access
            account_info = self.oanda_client.get_account_summary(account_id)
            if not account_info:
                return False

            # Create or update OANDA connection
            connection = self.db.query(OANDAConnection).filter(
                OANDAConnection.user_id == user.id
            ).first()

            if connection:
                # Update existing connection
                connection.account_id = account_id
                connection.environment = environment
                connection.connection_status = "CONNECTED"
                connection.last_connected = datetime.utcnow()
                connection.balance = float(account_info.get("balance", 0))
                connection.equity = float(account_info.get("NAV", 0))
                connection.account_currency = account_info.get("currency", "USD")
            else:
                # Create new connection
                connection = OANDAConnection(
                    user_id=user.id,
                    account_id=account_id,
                    environment=environment,
                    connection_status="CONNECTED",
                    last_connected=datetime.utcnow(),
                    balance=float(account_info.get("balance", 0)),
                    equity=float(account_info.get("NAV", 0)),
                    account_currency=account_info.get("currency", "USD"),
                    is_active=True
                )
                self.db.add(connection)

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to connect OANDA account for user {user.id}: {e}")
            return False

    def get_user_connection(self, user: User) -> Optional[OANDAConnection]:
        """Get user's OANDA connection."""
        return self.db.query(OANDAConnection).filter(
            OANDAConnection.user_id == user.id
        ).first()

    def calculate_position_size(
        self,
        symbol: str,
        account_balance: float,
        risk_percentage: float,
        stop_loss_pips: float
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on risk management.

        Args:
            symbol: Trading symbol
            account_balance: Account balance
            risk_percentage: Risk percentage (e.g., 0.02 for 2%)
            stop_loss_pips: Stop loss in pips

        Returns:
            Position size calculation details
        """
        try:
            # Get pip value for the symbol
            pip_value = self._get_pip_value(symbol, account_balance)

            # Calculate position size
            risk_amount = account_balance * risk_percentage
            position_size = risk_amount / (stop_loss_pips * pip_value)

            return {
                "symbol": symbol,
                "account_balance": account_balance,
                "risk_percentage": risk_percentage,
                "risk_amount": risk_amount,
                "stop_loss_pips": stop_loss_pips,
                "pip_value": pip_value,
                "position_size": round(position_size, 5),
                "max_loss": risk_amount
            }

        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            return {"error": str(e)}

    def _convert_signal_type(self, oanda_signal_type: OANDASignalType) -> SignalTypeEnum:
        """Convert OANDA signal type to database enum."""
        mapping = {
            OANDASignalType.BUY: SignalTypeEnum.BUY,
            OANDASignalType.SELL: SignalTypeEnum.SELL,
            OANDASignalType.HOLD: SignalTypeEnum.HOLD
        }
        return mapping.get(oanda_signal_type, SignalTypeEnum.HOLD)

    def _convert_to_oanda_symbol(self, symbol: str) -> str:
        """Convert frontend symbol to OANDA format."""
        # This should use the symbol mapping from main.py
        # For now, simple conversion
        if "/" in symbol:
            return symbol.replace("/", "_")
        elif len(symbol) == 6 and symbol.isalpha():
            return f"{symbol[:3]}_{symbol[3:]}"
        return symbol

    def _get_pip_value(self, symbol: str, account_balance: float) -> float:
        """Calculate pip value for position sizing."""
        # Simplified pip value calculation
        # In a real implementation, this would be more sophisticated
        if "JPY" in symbol:
            return 0.01  # JPY pairs have different pip values
        else:
            return 0.0001  # Standard pip value for most pairs