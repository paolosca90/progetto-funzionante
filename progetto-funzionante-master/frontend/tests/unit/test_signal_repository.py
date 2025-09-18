"""
Unit tests for SignalRepository.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from models import Signal, SignalStatusEnum, SignalTypeEnum, SignalExecution
from schemas import SignalCreate
from app.repositories.signal_repository import SignalRepository
from app.core.pagination import PaginatedResponse, PaginationParams
from tests.factories.signal_factory import SignalFactory
from tests.factories.user_factory import UserFactory


class TestSignalRepository:
    """Test cases for SignalRepository functionality."""

    @pytest.mark.unit
    def test_signal_repository_init(self, db_session):
        """Test SignalRepository initialization."""
        repo = SignalRepository(db_session)
        assert repo.db == db_session
        assert repo.model == Signal

    @pytest.mark.unit
    def test_get_latest_signals(self, signal_repository_fixture, user_fixture):
        """Test get latest active signals."""
        # Arrange
        signals = SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 3
        )

        # Act
        result = signal_repository_fixture.get_latest_signals(limit=5)

        # Assert
        assert len(result) <= 5
        for signal in result:
            assert signal.is_active is True
            assert signal.status == SignalStatusEnum.ACTIVE

    @pytest.mark.unit
    def test_get_latest_signals_paginated(self, signal_repository_fixture, user_fixture):
        """Test get latest signals with pagination."""
        # Arrange
        signals = SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 10
        )

        # Act
        result = signal_repository_fixture.get_latest_signals_paginated(page=1, per_page=5)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) <= 5
        assert result.page == 1
        assert result.per_page == 5

    @pytest.mark.unit
    def test_get_signals_by_symbol(self, signal_repository_fixture, user_fixture):
        """Test get signals by specific symbol."""
        # Arrange
        symbol = "EUR_USD"
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 3
        )

        # Create signals for specific symbol
        symbol_signals = SignalFactory.create_signals_for_symbols(
            signal_repository_fixture.db, user_fixture.id, [symbol, "GBP_USD"]
        )

        # Act
        result = signal_repository_fixture.get_signals_by_symbol(symbol, limit=10)

        # Assert
        assert len(result) >= 1
        for signal in result:
            assert signal.symbol == symbol
            assert signal.is_active is True

    @pytest.mark.unit
    def test_get_signals_by_symbol_paginated(self, signal_repository_fixture, user_fixture):
        """Test get signals by symbol with pagination."""
        # Arrange
        symbol = "EUR_USD"
        SignalFactory.create_signals_for_symbols(
            signal_repository_fixture.db, user_fixture.id, [symbol, symbol, "GBP_USD"]
        )

        # Act
        result = signal_repository_fixture.get_signals_by_symbol_paginated(
            symbol, page=1, per_page=2
        )

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.page == 1
        assert result.per_page == 2
        for signal in result.items:
            assert signal.symbol == symbol

    @pytest.mark.unit
    def test_get_signals_by_user(self, signal_repository_fixture, user_fixture):
        """Test get signals created by specific user."""
        # Arrange
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 5
        )

        # Act
        result = signal_repository_fixture.get_signals_by_user(user_fixture.id, limit=10)

        # Assert
        assert len(result) >= 1
        for signal in result:
            assert signal.creator_id == user_fixture.id

    @pytest.mark.unit
    def test_get_public_signals(self, signal_repository_fixture, user_fixture):
        """Test get public signals."""
        # Arrange
        # Create mix of public and private signals
        public_signals = SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 2
        )
        private_signals = SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 2
        )

        # Make some signals private
        for signal in private_signals:
            signal.is_public = False
            signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_public_signals(limit=10)

        # Assert
        for signal in result:
            assert signal.is_public is True
            assert signal.is_active is True

    @pytest.mark.unit
    def test_get_top_signals(self, signal_repository_fixture, user_fixture):
        """Test get top performing signals by reliability."""
        # Arrange
        # Create signals with different reliability scores
        signal_data_high = SignalFactory.create_signal_data({"reliability": 95.0})
        signal_data_medium = SignalFactory.create_signal_data({"reliability": 75.0})
        signal_data_low = SignalFactory.create_signal_data({"reliability": 55.0})

        for data in [signal_data_high, signal_data_medium, signal_data_low]:
            data["creator_id"] = user_fixture.id
            signal = Signal(**data)
            signal_repository_fixture.db.add(signal)

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_top_signals(limit=5)

        # Assert
        assert len(result) >= 1
        # Check if results are ordered by reliability (descending)
        for i in range(len(result) - 1):
            assert result[i].reliability >= result[i + 1].reliability

    @pytest.mark.unit
    def test_get_signals_by_source(self, signal_repository_fixture, user_fixture):
        """Test get signals by source."""
        # Arrange
        source = "OANDA_AI"
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 3
        )

        # Update signals to have specific source
        signals = signal_repository_fixture.db.query(Signal).all()
        for signal in signals:
            signal.source = source

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_signals_by_source(source, limit=10)

        # Assert
        for signal in result:
            assert signal.source == source
            assert signal.is_active is True

    @pytest.mark.unit
    def test_get_signals_by_risk_level(self, signal_repository_fixture, user_fixture):
        """Test get signals by risk level."""
        # Arrange
        risk_level = "HIGH"
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 3
        )

        # Update signals to have specific risk level
        signals = signal_repository_fixture.db.query(Signal).all()
        for signal in signals:
            signal.risk_level = risk_level

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_signals_by_risk_level(risk_level, limit=10)

        # Assert
        for signal in result:
            assert signal.risk_level == risk_level
            assert signal.is_active is True

    @pytest.mark.unit
    def test_get_signals_by_type(self, signal_repository_fixture, user_fixture):
        """Test get signals by type."""
        # Arrange
        signal_type = SignalTypeEnum.BUY
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 3
        )

        # Update signals to have specific type
        signals = signal_repository_fixture.db.query(Signal).all()
        for signal in signals:
            signal.signal_type = signal_type

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_signals_by_type(signal_type, limit=10)

        # Assert
        for signal in result:
            assert signal.signal_type == signal_type
            assert signal.is_active is True

    @pytest.mark.unit
    def test_get_signals_by_date_range(self, signal_repository_fixture, user_fixture):
        """Test get signals within date range."""
        # Arrange
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 3
        )

        # Define date range
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow() + timedelta(days=1)

        # Act
        result = signal_repository_fixture.get_signals_by_date_range(start_date, end_date, limit=10)

        # Assert
        for signal in result:
            assert start_date <= signal.created_at <= end_date

    @pytest.mark.unit
    def test_get_expired_signals(self, signal_repository_fixture, user_fixture):
        """Test get expired signals."""
        # Arrange
        # Create expired signal
        expired_signal_data = SignalFactory.create_expired_signal_data()
        expired_signal_data["creator_id"] = user_fixture.id
        expired_signal = Signal(**expired_signal_data)
        signal_repository_fixture.db.add(expired_signal)

        # Create active signal
        active_signal_data = SignalFactory.create_signal_data()
        active_signal_data["creator_id"] = user_fixture.id
        active_signal = Signal(**active_signal_data)
        signal_repository_fixture.db.add(active_signal)

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_expired_signals()

        # Assert
        assert len(result) >= 1
        for signal in result:
            assert signal.expires_at <= datetime.utcnow()
            assert signal.status == SignalStatusEnum.ACTIVE

    @pytest.mark.unit
    def test_close_signal(self, signal_repository_fixture, signal_fixture):
        """Test close a signal."""
        # Act
        result = signal_repository_fixture.close_signal(signal_fixture)

        # Assert
        assert result.status == SignalStatusEnum.CLOSED
        assert result == signal_fixture  # Same object instance

    @pytest.mark.unit
    def test_cancel_signal(self, signal_repository_fixture, signal_fixture):
        """Test cancel a signal."""
        # Act
        result = signal_repository_fixture.cancel_signal(signal_fixture)

        # Assert
        assert result.status == SignalStatusEnum.CANCELLED
        assert result == signal_fixture  # Same object instance

    @pytest.mark.unit
    def test_update_reliability(self, signal_repository_fixture, signal_fixture):
        """Test update signal reliability."""
        # Arrange
        new_reliability = 90.5

        # Act
        result = signal_repository_fixture.update_reliability(signal_fixture, new_reliability)

        # Assert
        assert result.reliability == new_reliability
        assert result == signal_fixture  # Same object instance

    @pytest.mark.unit
    def test_get_signal_statistics(self, signal_repository_fixture, user_fixture):
        """Test get overall signal statistics."""
        # Arrange
        # Create signals with different types
        buy_signal_data = SignalFactory.create_buy_signal_data()
        sell_signal_data = SignalFactory.create_sell_signal_data()
        hold_signal_data = SignalFactory.create_hold_signal_data()

        for data in [buy_signal_data, sell_signal_data, hold_signal_data]:
            data["creator_id"] = user_fixture.id
            signal = Signal(**data)
            signal_repository_fixture.db.add(signal)

        # Create closed signal
        closed_signal_data = SignalFactory.create_signal_data()
        closed_signal_data["creator_id"] = user_fixture.id
        closed_signal_data["status"] = SignalStatusEnum.CLOSED
        closed_signal = Signal(**closed_signal_data)
        signal_repository_fixture.db.add(closed_signal)

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_signal_statistics()

        # Assert
        assert isinstance(result, dict)
        assert "total_signals" in result
        assert "active_signals" in result
        assert "closed_signals" in result
        assert "average_reliability" in result
        assert "buy_signals" in result
        assert "sell_signals" in result
        assert "hold_signals" in result

        assert result["total_signals"] >= 4
        assert result["buy_signals"] >= 1
        assert result["sell_signals"] >= 1
        assert result["hold_signals"] >= 1

    @pytest.mark.unit
    def test_get_signals_by_timeframe(self, signal_repository_fixture, user_fixture):
        """Test get signals by timeframe."""
        # Arrange
        timeframe = "H1"
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 3
        )

        # Update signals to have specific timeframe
        signals = signal_repository_fixture.db.query(Signal).all()
        for signal in signals:
            signal.timeframe = timeframe

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_signals_by_timeframe(timeframe, limit=10)

        # Assert
        for signal in result:
            assert signal.timeframe == timeframe
            assert signal.is_active is True

    @pytest.mark.unit
    def test_get_recent_signals_count(self, signal_repository_fixture, user_fixture):
        """Test get count of recent signals."""
        # Arrange
        hours = 24
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 2
        )

        # Act
        result = signal_repository_fixture.get_recent_signals_count(hours)

        # Assert
        assert result >= 2

    @pytest.mark.unit
    def test_search_signals_by_symbol(self, signal_repository_fixture, user_fixture):
        """Test search signals by symbol."""
        # Arrange
        search_term = "EUR"
        SignalFactory.create_signals_for_symbols(
            signal_repository_fixture.db, user_fixture.id, ["EUR_USD", "EUR_GBP", "GBP_USD"]
        )

        # Act
        result = signal_repository_fixture.search_signals(search_term, limit=10)

        # Assert
        assert len(result) >= 2  # Should find EUR_USD and EUR_GBP
        for signal in result:
            assert "EUR" in signal.symbol

    @pytest.mark.unit
    def test_search_signals_by_analysis(self, signal_repository_fixture, user_fixture):
        """Test search signals by AI analysis content."""
        # Arrange
        search_term = "technical"
        signals = SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 2
        )

        # Update signals to contain search term in analysis
        for signal in signals:
            signal.ai_analysis = "Technical analysis shows buying opportunity"

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.search_signals(search_term, limit=10)

        # Assert
        assert len(result) >= 2
        for signal in result:
            assert "technical" in signal.ai_analysis.lower()

    @pytest.mark.unit
    def test_search_signals_paginated(self, signal_repository_fixture, user_fixture):
        """Test search signals with pagination."""
        # Arrange
        search_term = "EUR"
        SignalFactory.create_signals_for_symbols(
            signal_repository_fixture.db, user_fixture.id, ["EUR_USD", "EUR_GBP", "GBP_USD"]
        )

        # Act
        result = signal_repository_fixture.search_signals_paginated(search_term, page=1, per_page=2)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.page == 1
        assert result.per_page == 2
        assert len(result.items) <= 2

    @pytest.mark.unit
    def test_get_high_confidence_signals(self, signal_repository_fixture, user_fixture):
        """Test get high confidence signals."""
        # Arrange
        min_confidence = 0.8
        high_conf_signal = SignalFactory.create_signal_instance(
            signal_repository_fixture.db, user_fixture.id,
            {"confidence_score": 0.85, "is_active": True, "status": SignalStatusEnum.ACTIVE}
        )
        low_conf_signal = SignalFactory.create_signal_instance(
            signal_repository_fixture.db, user_fixture.id,
            {"confidence_score": 0.75, "is_active": True, "status": SignalStatusEnum.ACTIVE}
        )

        # Act
        result = signal_repository_fixture.get_high_confidence_signals(min_confidence, limit=10)

        # Assert
        for signal in result:
            assert signal.confidence_score >= min_confidence
            assert signal.is_active is True
            assert signal.status == SignalStatusEnum.ACTIVE

    @pytest.mark.unit
    def test_get_signals_with_executions(self, signal_repository_fixture, user_fixture):
        """Test get signals that have executions."""
        # Arrange
        signal = SignalFactory.create_signal_instance(signal_repository_fixture.db, user_fixture.id)

        # Create execution
        execution = SignalExecution(
            signal_id=signal.id,
            user_id=user_fixture.id,
            execution_price=signal.entry_price,
            quantity=0.1
        )
        signal_repository_fixture.db.add(execution)
        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.get_signals_with_executions(limit=10)

        # Assert
        assert len(result) >= 1
        for signal in result:
            assert len(signal.executions) > 0

    @pytest.mark.unit
    def test_bulk_close_expired_signals(self, signal_repository_fixture, user_fixture):
        """Test bulk close expired signals."""
        # Arrange
        # Create expired signals
        expired_count = 3
        for _ in range(expired_count):
            expired_signal_data = SignalFactory.create_expired_signal_data()
            expired_signal_data["creator_id"] = user_fixture.id
            expired_signal = Signal(**expired_signal_data)
            signal_repository_fixture.db.add(expired_signal)

        # Create active signal
        active_signal_data = SignalFactory.create_signal_data()
        active_signal_data["creator_id"] = user_fixture.id
        active_signal = Signal(**active_signal_data)
        signal_repository_fixture.db.add(active_signal)

        signal_repository_fixture.db.commit()

        # Act
        result = signal_repository_fixture.bulk_close_expired_signals()

        # Assert
        assert result == expired_count

        # Verify signals were closed
        closed_signals = signal_repository_fixture.db.query(Signal).filter(
            Signal.status == SignalStatusEnum.CLOSED
        ).all()
        assert len(closed_signals) >= expired_count

    @pytest.mark.unit
    def test_get_signals_with_advanced_pagination(self, signal_repository_fixture, user_fixture):
        """Test get signals with advanced filtering and pagination."""
        # Arrange
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 5
        )

        # Create signals with different properties
        high_conf_signal = SignalFactory.create_signal_instance(
            signal_repository_fixture.db, user_fixture.id,
            {"confidence_score": 0.9, "risk_level": "LOW", "symbol": "EUR_USD"}
        )
        medium_conf_signal = SignalFactory.create_signal_instance(
            signal_repository_fixture.db, user_fixture.id,
            {"confidence_score": 0.7, "risk_level": "MEDIUM", "symbol": "GBP_USD"}
        )

        filters = {
            "min_confidence": 0.8,
            "risk_level": "LOW",
            "symbol": "EUR_USD"
        }

        # Act
        result = signal_repository_fixture.get_signals_with_advanced_pagination(
            filters=filters, page=1, per_page=10
        )

        # Assert
        assert isinstance(result, PaginatedResponse)
        for signal in result.items:
            assert signal.confidence_score >= 0.8
            assert signal.risk_level == "LOW"
            assert signal.symbol == "EUR_USD"

    @pytest.mark.unit
    def test_stream_all_signals(self, signal_repository_fixture, user_fixture):
        """Test stream all signals in batches."""
        # Arrange
        batch_size = 2
        SignalFactory.create_signals_batch_instances(
            signal_repository_fixture.db, user_fixture.id, 5
        )

        # Act
        stream_result = signal_repository_fixture.stream_all_signals(batch_size=batch_size)

        # Assert
        # Verify it returns a generator/iterator
        assert hasattr(stream_result, '__iter__')

        # Test consuming the stream
        signals_consumed = 0
        for batch in stream_result:
            signals_consumed += len(batch)
            if signals_consumed >= 3:  # Test partial consumption
                break

        assert signals_consumed > 0