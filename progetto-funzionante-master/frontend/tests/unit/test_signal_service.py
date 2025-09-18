"""
Unit tests for SignalService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta

from models import Signal, User, SignalStatusEnum, SignalTypeEnum
from schemas import SignalCreate, TopSignalsResponse
from app.services.signal_service import SignalService
from tests.factories.signal_factory import SignalFactory
from tests.factories.user_factory import UserFactory


class TestSignalService:
    """Test cases for SignalService functionality."""

    @pytest.mark.unit
    def test_signal_service_init(self, db_session):
        """Test SignalService initialization."""
        service = SignalService(db_session)
        assert service.db == db_session
        assert service.signal_repository is not None
        assert service.cache_enabled is True

    @pytest.mark.unit
    async def test_create_signal_success(self, signal_service_fixture, user_fixture, test_signal_data):
        """Test successful signal creation."""
        # Arrange
        signal_create = SignalCreate(**test_signal_data)

        # Act
        result = signal_service_fixture.create_signal(signal_create, user_fixture.id)

        # Assert
        assert result is not None
        assert result.symbol == test_signal_data["symbol"]
        assert result.signal_type == test_signal_data["signal_type"]
        assert result.creator_id == user_fixture.id
        assert result.expires_at is not None

        # Verify cache invalidation was called
        signal_service_fixture.signal_repository.cache_service.invalidate_signals_cache.assert_called_once()

    @pytest.mark.unit
    async def test_create_signal_with_default_expiration(self, signal_service_fixture, user_fixture):
        """Test signal creation with default expiration time."""
        # Arrange
        signal_data = SignalFactory.create_signal_data()
        signal_data.pop("expires_at", None)  # Remove expiration to test default
        signal_create = SignalCreate(**signal_data)

        # Act
        result = signal_service_fixture.create_signal(signal_create, user_fixture.id)

        # Assert
        assert result is not None
        assert result.expires_at is not None
        # Default expiration should be 24 hours from creation
        expected_expiration = datetime.utcnow() + timedelta(hours=24)
        assert abs((result.expires_at - expected_expiration).total_seconds()) < 60  # Within 1 minute

    @pytest.mark.unit
    async def test_get_latest_signals_cache_hit(self, signal_service_fixture):
        """Test get_latest_signals with cache hit."""
        # Arrange
        limit = 10
        cached_signals_data = [
            {
                "id": 1,
                "symbol": "EUR_USD",
                "signal_type": "BUY",
                "entry_price": 1.1234,
                "status": "ACTIVE",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "creator_id": 1
            }
        ]

        signal_service_fixture.signal_repository.cache_service.get_cached_signals.return_value = cached_signals_data

        # Act
        result = await signal_service_fixture.get_latest_signals(limit)

        # Assert
        assert len(result) == 1
        assert result[0].symbol == "EUR_USD"
        assert result[0].signal_type == SignalTypeEnum.BUY
        # Verify database was not called due to cache hit
        signal_service_fixture.signal_repository.get_latest_signals.assert_not_called()

    @pytest.mark.unit
    async def test_get_latest_signals_cache_miss(self, signal_service_fixture):
        """Test get_latest_signals with cache miss."""
        # Arrange
        limit = 10
        mock_signal = MagicMock()
        mock_signal.id = 1
        mock_signal.symbol = "EUR_USD"
        mock_signal.signal_type = SignalTypeEnum.BUY
        mock_signal.status = SignalStatusEnum.ACTIVE
        mock_signal.is_active = True
        mock_signal.created_at = datetime.utcnow()
        mock_signal.creator_id = 1

        signal_service_fixture.signal_repository.cache_service.get_cached_signals.return_value = None
        signal_service_fixture.signal_repository.get_latest_signals.return_value = [mock_signal]

        # Act
        result = await signal_service_fixture.get_latest_signals(limit)

        # Assert
        assert len(result) == 1
        assert result[0].symbol == "EUR_USD"
        # Verify cache was populated
        signal_service_fixture.signal_repository.cache_service.cache_signals.assert_called_once()

    @pytest.mark.unit
    async def test_get_signals_by_symbol(self, signal_service_fixture):
        """Test get signals by symbol with caching."""
        # Arrange
        symbol = "EUR_USD"
        limit = 5
        mock_signal = MagicMock()
        mock_signal.id = 1
        mock_signal.symbol = symbol
        mock_signal.signal_type = SignalTypeEnum.BUY
        mock_signal.status = SignalStatusEnum.ACTIVE
        mock_signal.is_active = True
        mock_signal.created_at = datetime.utcnow()
        mock_signal.creator_id = 1

        signal_service_fixture.signal_repository.cache_service.get_cached_signals.return_value = None
        signal_service_fixture.signal_repository.get_signals_by_symbol.return_value = [mock_signal]

        # Act
        result = await signal_service_fixture.get_signals_by_symbol(symbol, limit)

        # Assert
        assert len(result) == 1
        assert result[0].symbol == symbol
        signal_service_fixture.signal_repository.get_signals_by_symbol.assert_called_once_with(symbol, limit)

    @pytest.mark.unit
    def test_get_user_signals(self, signal_service_fixture, user_fixture):
        """Test get user signals."""
        # Arrange
        limit = 10
        mock_signal = MagicMock()
        mock_signal.id = 1
        mock_signal.creator_id = user_fixture.id

        signal_service_fixture.signal_repository.get_signals_by_user.return_value = [mock_signal]

        # Act
        result = signal_service_fixture.get_user_signals(user_fixture.id, limit)

        # Assert
        assert len(result) == 1
        assert result[0].creator_id == user_fixture.id
        signal_service_fixture.signal_repository.get_signals_by_user.assert_called_once_with(user_fixture.id, limit)

    @pytest.mark.unit
    def test_get_public_signals(self, signal_service_fixture):
        """Test get public signals."""
        # Arrange
        limit = 20
        mock_signal = MagicMock()
        mock_signal.is_public = True
        mock_signal.is_active = True

        signal_service_fixture.signal_repository.get_public_signals.return_value = [mock_signal]

        # Act
        result = signal_service_fixture.get_public_signals(limit)

        # Assert
        assert len(result) == 1
        signal_service_fixture.signal_repository.get_public_signals.assert_called_once_with(limit)

    @pytest.mark.unit
    async def test_get_top_signals(self, signal_service_fixture):
        """Test get top signals with statistics."""
        # Arrange
        limit = 5
        mock_signal = MagicMock()
        mock_signal.id = 1
        mock_signal.reliability = 90.0

        mock_stats = {
            "total_signals": 100,
            "average_reliability": 75.5
        }

        signal_service_fixture.signal_repository.cache_service.get_cached_signal_statistics.return_value = mock_stats
        signal_service_fixture.signal_repository.get_top_signals.return_value = [mock_signal]

        # Act
        result = await signal_service_fixture.get_top_signals(limit)

        # Assert
        assert isinstance(result, TopSignalsResponse)
        assert len(result.signals) == 1
        assert result.total_count == 100
        assert result.average_reliability == 75.5

    @pytest.mark.unit
    def test_get_signals_by_source(self, signal_service_fixture):
        """Test get signals by source."""
        # Arrange
        source = "OANDA_AI"
        limit = 15
        mock_signal = MagicMock()
        mock_signal.source = source

        signal_service_fixture.signal_repository.get_signals_by_source.return_value = [mock_signal]

        # Act
        result = signal_service_fixture.get_signals_by_source(source, limit)

        # Assert
        assert len(result) == 1
        assert result[0].source == source
        signal_service_fixture.signal_repository.get_signals_by_source.assert_called_once_with(source, limit)

    @pytest.mark.unit
    def test_get_signals_by_risk_level(self, signal_service_fixture):
        """Test get signals by risk level."""
        # Arrange
        risk_level = "HIGH"
        limit = 10
        mock_signal = MagicMock()
        mock_signal.risk_level = risk_level

        signal_service_fixture.signal_repository.get_signals_by_risk_level.return_value = [mock_signal]

        # Act
        result = signal_service_fixture.get_signals_by_risk_level(risk_level, limit)

        # Assert
        assert len(result) == 1
        assert result[0].risk_level == risk_level
        signal_service_fixture.signal_repository.get_signals_by_risk_level.assert_called_once_with(risk_level, limit)

    @pytest.mark.unit
    def test_get_signals_by_type_valid(self, signal_service_fixture):
        """Test get signals by type with valid signal type."""
        # Arrange
        signal_type = "BUY"
        limit = 10
        mock_signal = MagicMock()
        mock_signal.signal_type = SignalTypeEnum.BUY

        signal_service_fixture.signal_repository.get_signals_by_type.return_value = [mock_signal]

        # Act
        result = signal_service_fixture.get_signals_by_type(signal_type, limit)

        # Assert
        assert len(result) == 1
        assert result[0].signal_type == SignalTypeEnum.BUY
        signal_service_fixture.signal_repository.get_signals_by_type.assert_called_once_with(SignalTypeEnum.BUY, limit)

    @pytest.mark.unit
    def test_get_signals_by_type_invalid(self, signal_service_fixture):
        """Test get signals by type with invalid signal type."""
        # Arrange
        signal_type = "INVALID_TYPE"
        limit = 10

        # Act
        result = signal_service_fixture.get_signals_by_type(signal_type, limit)

        # Assert
        assert result == []
        signal_service_fixture.signal_repository.get_signals_by_type.assert_not_called()

    @pytest.mark.unit
    def test_get_signal_by_id_found(self, signal_service_fixture):
        """Test get signal by ID when signal exists."""
        # Arrange
        signal_id = 1
        mock_signal = MagicMock()
        mock_signal.id = signal_id

        signal_service_fixture.signal_repository.get.return_value = mock_signal

        # Act
        result = signal_service_fixture.get_signal_by_id(signal_id)

        # Assert
        assert result is not None
        assert result.id == signal_id
        signal_service_fixture.signal_repository.get.assert_called_once_with(signal_id)

    @pytest.mark.unit
    def test_get_signal_by_id_not_found(self, signal_service_fixture):
        """Test get signal by ID when signal doesn't exist."""
        # Arrange
        signal_id = 999
        signal_service_fixture.signal_repository.get.return_value = None

        # Act
        result = signal_service_fixture.get_signal_by_id(signal_id)

        # Assert
        assert result is None
        signal_service_fixture.signal_repository.get.assert_called_once_with(signal_id)

    @pytest.mark.unit
    async def test_close_signal_success(self, signal_service_fixture, user_fixture, signal_fixture):
        """Test successful signal closure by owner."""
        # Arrange
        signal_fixture.creator_id = user_fixture.id
        updated_signal = MagicMock()
        signal_service_fixture.signal_repository.close_signal.return_value = updated_signal

        # Act
        result = signal_service_fixture.close_signal(signal_fixture.id, user_fixture)

        # Assert
        assert result == updated_signal
        signal_service_fixture.signal_repository.close_signal.assert_called_once()
        signal_service_fixture.signal_repository.cache_service.invalidate_signals_cache.assert_called_once()

    @pytest.mark.unit
    async def test_close_signal_not_found(self, signal_service_fixture, user_fixture):
        """Test signal closure when signal doesn't exist."""
        # Arrange
        signal_service_fixture.signal_repository.get.return_value = None

        # Act
        result = signal_service_fixture.close_signal(999, user_fixture)

        # Assert
        assert result is None

    @pytest.mark.unit
    async def test_close_signal_unauthorized(self, signal_service_fixture, user_fixture, signal_fixture):
        """Test signal closure when user is not authorized."""
        # Arrange
        signal_fixture.creator_id = user_fixture.id + 1  # Different user
        user_fixture.is_admin = False
        signal_service_fixture.signal_repository.get.return_value = signal_fixture

        # Act
        result = signal_service_fixture.close_signal(signal_fixture.id, user_fixture)

        # Assert
        assert result is None
        signal_service_fixture.signal_repository.close_signal.assert_not_called()

    @pytest.mark.unit
    async def test_cancel_signal_success(self, signal_service_fixture, user_fixture, signal_fixture):
        """Test successful signal cancellation."""
        # Arrange
        signal_fixture.creator_id = user_fixture.id
        updated_signal = MagicMock()
        signal_service_fixture.signal_repository.cancel_signal.return_value = updated_signal

        # Act
        result = signal_service_fixture.cancel_signal(signal_fixture.id, user_fixture)

        # Assert
        assert result == updated_signal
        signal_service_fixture.signal_repository.cancel_signal.assert_called_once()
        signal_service_fixture.signal_repository.cache_service.invalidate_signals_cache.assert_called_once()

    @pytest.mark.unit
    async def test_update_signal_reliability_success(self, signal_service_fixture, user_fixture, signal_fixture):
        """Test successful signal reliability update."""
        # Arrange
        reliability = 85.5
        signal_fixture.creator_id = user_fixture.id
        updated_signal = MagicMock()
        signal_service_fixture.signal_repository.update_reliability.return_value = updated_signal

        # Act
        result = signal_service_fixture.update_signal_reliability(signal_fixture.id, reliability, user_fixture)

        # Assert
        assert result == updated_signal
        signal_service_fixture.signal_repository.update_reliability.assert_called_once_with(signal_fixture, reliability)

    @pytest.mark.unit
    async def test_update_signal_reliability_invalid_score(self, signal_service_fixture, user_fixture, signal_fixture):
        """Test signal reliability update with invalid score."""
        # Arrange
        invalid_reliability = 150.0  # Outside 0-100 range
        signal_fixture.creator_id = user_fixture.id

        # Act
        result = signal_service_fixture.update_signal_reliability(signal_fixture.id, invalid_reliability, user_fixture)

        # Assert
        assert result is None
        signal_service_fixture.signal_repository.update_reliability.assert_not_called()

    @pytest.mark.unit
    async def test_get_signal_statistics_cache_hit(self, signal_service_fixture):
        """Test get signal statistics with cache hit."""
        # Arrange
        cached_stats = {"total_signals": 100, "average_reliability": 75.5}
        signal_service_fixture.signal_repository.cache_service.get_cached_signal_statistics.return_value = cached_stats

        # Act
        result = await signal_service_fixture.get_signal_statistics()

        # Assert
        assert result == cached_stats
        signal_service_fixture.signal_repository.get_signal_statistics.assert_not_called()

    @pytest.mark.unit
    async def test_get_signal_statistics_cache_miss(self, signal_service_fixture):
        """Test get signal statistics with cache miss."""
        # Arrange
        db_stats = {"total_signals": 100, "average_reliability": 75.5}
        signal_service_fixture.signal_repository.cache_service.get_cached_signal_statistics.return_value = None
        signal_service_fixture.signal_repository.get_signal_statistics.return_value = db_stats

        # Act
        result = await signal_service_fixture.get_signal_statistics()

        # Assert
        assert result == db_stats
        signal_service_fixture.signal_repository.cache_service.cache_signal_statistics.assert_called_once_with(db_stats, ttl=600)

    @pytest.mark.unit
    def test_search_signals(self, signal_service_fixture):
        """Test signal search functionality."""
        # Arrange
        search_term = "EUR_USD"
        limit = 10
        mock_signal = MagicMock()
        mock_signal.symbol = "EUR_USD"

        signal_service_fixture.signal_repository.search_signals.return_value = [mock_signal]

        # Act
        result = signal_service_fixture.search_signals(search_term, limit)

        # Assert
        assert len(result) == 1
        assert result[0].symbol == "EUR_USD"
        signal_service_fixture.signal_repository.search_signals.assert_called_once_with(search_term, limit)

    @pytest.mark.unit
    def test_get_high_confidence_signals(self, signal_service_fixture):
        """Test get high confidence signals."""
        # Arrange
        min_confidence = 0.8
        limit = 10
        mock_signal = MagicMock()
        mock_signal.confidence_score = 0.85

        signal_service_fixture.signal_repository.get_high_confidence_signals.return_value = [mock_signal]

        # Act
        result = signal_service_fixture.get_high_confidence_signals(min_confidence, limit)

        # Assert
        assert len(result) == 1
        signal_service_fixture.signal_repository.get_high_confidence_signals.assert_called_once_with(min_confidence, limit)

    @pytest.mark.unit
    def test_get_recent_signals_count(self, signal_service_fixture):
        """Test get recent signals count."""
        # Arrange
        hours = 24
        expected_count = 5
        signal_service_fixture.signal_repository.get_recent_signals_count.return_value = expected_count

        # Act
        result = signal_service_fixture.get_recent_signals_count(hours)

        # Assert
        assert result == expected_count
        signal_service_fixture.signal_repository.get_recent_signals_count.assert_called_once_with(hours)

    @pytest.mark.unit
    async def test_cleanup_expired_signals(self, signal_service_fixture):
        """Test cleanup of expired signals."""
        # Arrange
        expected_count = 3
        signal_service_fixture.signal_repository.bulk_close_expired_signals.return_value = expected_count

        # Act
        result = signal_service_fixture.cleanup_expired_signals()

        # Assert
        assert result == expected_count
        signal_service_fixture.signal_repository.bulk_close_expired_signals.assert_called_once()
        signal_service_fixture.signal_repository.cache_service.invalidate_signals_cache.assert_called_once()

    @pytest.mark.unit
    def test_generate_signal_report(self, signal_service_fixture, signal_fixture):
        """Test signal report generation."""
        # Arrange
        days = 30
        signal_fixture.created_at = datetime.utcnow() - timedelta(days=15)
        signal_fixture.signal_type = SignalTypeEnum.BUY
        signal_fixture.reliability = 85.0
        signal_fixture.confidence_score = 0.85

        signals_in_range = [signal_fixture]
        stats = {"total_signals": 50, "average_reliability": 75.0}

        with patch.object(signal_service_fixture, 'get_signals_by_date_range', return_value=signals_in_range):
            with patch.object(signal_service_fixture, 'get_signal_statistics', return_value=stats):
                # Act
                result = signal_service_fixture.generate_signal_report(days)

        # Assert
        assert result["period_days"] == days
        assert result["total_signals"] == 1
        assert result["buy_signals"] == 1
        assert result["sell_signals"] == 0
        assert result["hold_signals"] == 0
        assert result["average_confidence"] == 0.85
        assert result["average_reliability"] == 85.0
        assert "EUR_USD" in result["signals_by_symbol"]

    @pytest.mark.unit
    def test_signal_to_dict_conversion(self, signal_service_fixture, signal_fixture):
        """Test Signal object to dictionary conversion."""
        # Act
        result = signal_service_fixture._signal_to_dict(signal_fixture)

        # Assert
        assert isinstance(result, dict)
        assert result["id"] == signal_fixture.id
        assert result["symbol"] == signal_fixture.symbol
        assert result["signal_type"] == signal_fixture.signal_type.value
        assert result["entry_price"] == signal_fixture.entry_price
        assert result["creator_id"] == signal_fixture.creator_id