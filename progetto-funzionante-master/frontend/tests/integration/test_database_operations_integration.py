"""
Comprehensive integration tests for database operations across multiple services.
Tests data consistency, transaction management, relationships, and multi-service operations.
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List

from models import User, Signal, SignalExecution, OANDAConnection, Subscription, SignalStatusEnum, SignalTypeEnum
from schemas import UserCreate, SignalCreate, SignalExecutionCreate
from app.services.signal_service import SignalService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.repositories.signal_repository import SignalRepository
from app.repositories.user_repository import UserRepository


class TestDatabaseOperationsIntegration:
    """Integration test suite for database operations across services."""

    def test_user_creation_and_validation(self, db_session: Session, test_user_data: Dict[str, Any]):
        """Test complete user creation with validation."""
        # Create user through service
        user_service = UserService(db_session)
        user_data = UserCreate(**test_user_data)

        user = user_service.create_user(user_data)
        assert user.id is not None
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        assert user.is_active is True
        assert user.created_at is not None

        # Verify user can be retrieved
        retrieved_user = user_service.get_user_by_id(user.id)
        assert retrieved_user is not None
        assert retrieved_user.id == user.id

        # Verify user exists in database
        db_user = db_session.query(User).filter(User.id == user.id).first()
        assert db_user is not None
        assert db_user.username == user.username

    def test_user_unique_constraints(self, db_session: Session, test_user_data: Dict[str, Any]):
        """Test database unique constraints for users."""
        user_service = UserService(db_session)
        user_data = UserCreate(**test_user_data)

        # Create first user
        user1 = user_service.create_user(user_data)
        assert user1.id is not None

        # Try to create user with same username (should fail)
        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            user_service.create_user(user_data)

        # Try to create user with same email (should fail)
        duplicate_email_data = test_user_data.copy()
        duplicate_email_data["username"] = "different_username"
        duplicate_user_data = UserCreate(**duplicate_email_data)

        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            user_service.create_user(duplicate_user_data)

    def test_signal_creation_with_user_relationship(self, db_session: Session, user_fixture: User, test_signal_data: Dict[str, Any]):
        """Test signal creation with user relationship."""
        signal_service = SignalService(db_session)
        signal_data = SignalCreate(**test_signal_data)

        signal = signal_service.create_signal(signal_data, user_fixture.id)
        assert signal.id is not None
        assert signal.creator_id == user_fixture.id
        assert signal.symbol == test_signal_data["symbol"]

        # Verify relationship is properly set
        assert signal.creator == user_fixture
        assert signal in user_fixture.signals

        # Verify signal can be retrieved through user
        retrieved_signals = signal_service.get_signals_by_user(user_fixture.id)
        assert len(retrieved_signals) > 0
        assert signal in retrieved_signals

    def test_signal_execution_relationships(self, db_session: Session, signal_fixture: Signal, user_fixture: User):
        """Test signal execution with proper relationships."""
        signal_service = SignalService(db_session)

        execution_data = {
            "signal_id": signal_fixture.id,
            "user_id": user_fixture.id,
            "execution_price": signal_fixture.entry_price,
            "quantity": 1.0,
            "execution_type": "MANUAL"
        }

        execution = signal_service.create_execution(execution_data)
        assert execution.id is not None
        assert execution.signal_id == signal_fixture.id
        assert execution.user_id == user_fixture.id

        # Verify relationships
        assert execution.signal == signal_fixture
        assert execution.user == user_fixture
        assert execution in signal_fixture.executions
        assert execution in user_fixture.executions

    def test_cascade_delete_operations(self, db_session: Session, user_fixture: User):
        """Test cascade delete operations."""
        # Create signal for user
        signal_service = SignalService(db_session)
        test_signal_data = {
            "symbol": "EUR_USD",
            "signal_type": SignalTypeEnum.BUY,
            "entry_price": 1.1234,
            "stop_loss": 1.1200,
            "take_profit": 1.1300
        }
        signal_data = SignalCreate(**test_signal_data)
        signal = signal_service.create_signal(signal_data, user_fixture.id)

        # Create signal execution
        execution_data = {
            "signal_id": signal.id,
            "user_id": user_fixture.id,
            "execution_price": signal.entry_price,
            "quantity": 1.0,
            "execution_type": "MANUAL"
        }
        execution = signal_service.create_execution(execution_data)

        # Verify all records exist
        assert db_session.query(User).filter(User.id == user_fixture.id).first() is not None
        assert db_session.query(Signal).filter(Signal.id == signal.id).first() is not None
        assert db_session.query(SignalExecution).filter(SignalExecution.id == execution.id).first() is not None

        # Delete user (should cascade to related records)
        db_session.delete(user_fixture)
        db_session.commit()

        # Verify cascade deletion
        assert db_session.query(User).filter(User.id == user_fixture.id).first() is None
        assert db_session.query(Signal).filter(Signal.id == signal.id).first() is None
        assert db_session.query(SignalExecution).filter(SignalExecution.id == execution.id).first() is None

    def test_database_transaction_rollback(self, db_session: Session, test_user_data: Dict[str, Any]):
        """Test database transaction rollback on errors."""
        user_service = UserService(db_session)

        initial_user_count = db_session.query(User).count()

        try:
            # Start transaction
            user_data = UserCreate(**test_user_data)
            user = user_service.create_user(user_data)

            # Simulate an error
            raise Exception("Simulated error for rollback test")

        except Exception:
            # Rollback should happen automatically due to test fixture setup
            pass

        # Verify no user was created
        final_user_count = db_session.query(User).count()
        assert final_user_count == initial_user_count

    def test_concurrent_database_operations(self, db_session: Session, test_user_data: Dict[str, Any]):
        """Test concurrent database operations."""
        import threading
        import time

        user_service = UserService(db_session)
        results = []

        def create_user_thread(user_data_suffix: str):
            try:
                modified_data = test_user_data.copy()
                modified_data["username"] = f"concurrent_user_{user_data_suffix}"
                modified_data["email"] = f"concurrent_{user_data_suffix}@test.com"

                user_data_obj = UserCreate(**modified_data)
                user = user_service.create_user(user_data_obj)
                results.append(("success", user.id))
            except Exception as e:
                results.append(("error", str(e)))

        # Create multiple threads for concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all operations succeeded
        successes = [r for r in results if r[0] == "success"]
        errors = [r for r in results if r[0] == "error"]

        assert len(successes) == 5, f"Expected 5 successes, got {len(successes)}"
        assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}"

    def test_signal_status_transitions(self, db_session: Session, signal_fixture: Signal):
        """Test signal status transitions and business logic."""
        signal_service = SignalService(db_session)

        # Verify initial status
        assert signal_fixture.status == SignalStatusEnum.ACTIVE

        # Test status update to CLOSED
        updated_signal = signal_service.update_signal_status(
            signal_fixture.id, SignalStatusEnum.CLOSED
        )
        assert updated_signal.status == SignalStatusEnum.CLOSED

        # Verify database reflects change
        db_signal = db_session.query(Signal).filter(Signal.id == signal_fixture.id).first()
        assert db_signal.status == SignalStatusEnum.CLOSED

        # Test status update to CANCELLED
        updated_signal = signal_service.update_signal_status(
            signal_fixture.id, SignalStatusEnum.CANCELLED
        )
        assert updated_signal.status == SignalStatusEnum.CANCELLED

    def test_oanda_connection_integration(self, db_session: Session, user_fixture: User):
        """Test OANDA connection creation and integration."""
        oanda_connection = OANDAConnection(
            user_id=user_fixture.id,
            account_id="test_oanda_account_123",
            environment="demo",
            account_currency="USD",
            is_active=True,
            connection_status="CONNECTED",
            balance=10000.0,
            equity=10500.0,
            margin_used=1000.0,
            margin_available=9000.0,
            unrealized_pl=500.0,
            auto_trading_enabled=False,
            risk_tolerance="MEDIUM",
            max_position_size=1.0,
            daily_loss_limit=1000.0
        )

        db_session.add(oanda_connection)
        db_session.commit()
        db_session.refresh(oanda_connection)

        # Verify OANDA connection was created
        assert oanda_connection.id is not None
        assert oanda_connection.user_id == user_fixture.id

        # Verify relationship
        assert user_fixture.oanda_connection == oanda_connection

        # Test unique constraint (one OANDA connection per user)
        duplicate_connection = OANDAConnection(
            user_id=user_fixture.id,
            account_id="test_oanda_account_456",
            environment="demo"
        )

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.add(duplicate_connection)
            db_session.commit()

    def test_subscription_management(self, db_session: Session, user_fixture: User):
        """Test subscription creation and management."""
        subscription = Subscription(
            user_id=user_fixture.id,
            plan_name="PREMIUM",
            status="ACTIVE",
            is_active=True,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            payment_status="COMPLETED"
        )

        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)

        # Verify subscription was created
        assert subscription.id is not None
        assert subscription.user_id == user_fixture.id

        # Test subscription status update
        subscription.status = "EXPIRED"
        subscription.is_active = False
        db_session.commit()

        # Verify update
        db_subscription = db_session.query(Subscription).filter(Subscription.id == subscription.id).first()
        assert db_subscription.status == "EXPIRED"
        assert db_subscription.is_active is False

    def test_signal_statistics_and_aggregation(self, db_session: Session, user_fixture: User, multiple_signals_fixture: List[Signal]):
        """Test signal statistics and aggregation queries."""
        signal_service = SignalService(db_session)

        # Test user signal statistics
        stats = signal_service.get_user_signal_statistics(user_fixture.id)
        assert "total_signals" in stats
        assert "active_signals" in stats
        assert "average_reliability" in stats
        assert "recent_signals_count" in stats

        assert stats["total_signals"] >= len(multiple_signals_fixture)
        assert stats["average_reliability"] >= 0

        # Test global signal statistics
        global_stats = signal_service.get_global_signal_statistics()
        assert "total_signals" in global_stats
        assert "active_signals" in global_stats
        assert "average_reliability" in global_stats

    def test_database_index_performance(self, db_session: Session, multiple_signals_fixture: List[Signal]):
        """Test database index performance."""
        import time

        # Test query performance with indexed fields
        start_time = time.time()

        # Query by symbol (indexed)
        signals = db_session.query(Signal).filter(Signal.symbol == "EUR_USD").all()
        symbol_query_time = time.time() - start_time

        # Query by status (indexed)
        start_time = time.time()
        signals = db_session.query(Signal).filter(Signal.status == SignalStatusEnum.ACTIVE).all()
        status_query_time = time.time() - start_time

        # Query by creator (indexed)
        start_time = time.time()
        signals = db_session.query(Signal).filter(Signal.creator_id == multiple_signals_fixture[0].creator_id).all()
        creator_query_time = time.time() - start_time

        # All queries should be fast (under 1 second)
        assert symbol_query_time < 1.0, f"Symbol query too slow: {symbol_query_time:.3f}s"
        assert status_query_time < 1.0, f"Status query too slow: {status_query_time:.3f}s"
        assert creator_query_time < 1.0, f"Creator query too slow: {creator_query_time:.3f}s"

    def test_database_connection_handling(self, db_session: Session):
        """Test database connection handling and error recovery."""
        # Test normal operation
        user_count = db_session.query(User).count()
        assert isinstance(user_count, int)

        # Test session rollback
        try:
            # Create a user
            user = User(
                username="test_session_user",
                email="session@test.com",
                hashed_password="hashed_password",
                is_active=True
            )
            db_session.add(user)

            # Force an error
            raise Exception("Forced error for session testing")

        except Exception:
            # Session should be rolled back by test fixture
            pass

        # Verify user was not created due to rollback
        test_user = db_session.query(User).filter(User.username == "test_session_user").first()
        assert test_user is None

    def test_bulk_database_operations(self, db_session: Session, user_fixture: User):
        """Test bulk database operations."""
        signal_service = SignalService(db_session)

        # Create multiple signals in bulk
        bulk_signals = []
        for i in range(10):
            signal_data = {
                "symbol": f"TEST_{i}",
                "signal_type": SignalTypeEnum.BUY if i % 2 == 0 else SignalTypeEnum.SELL,
                "entry_price": 1.1000 + (i * 0.001),
                "stop_loss": 1.0950 + (i * 0.001),
                "take_profit": 1.1050 + (i * 0.001),
                "creator_id": user_fixture.id,
                "reliability": 70.0 + (i * 2),
                "is_active": True
            }
            bulk_signals.append(Signal(**signal_data))

        # Bulk insert
        db_session.add_all(bulk_signals)
        db_session.commit()

        # Verify all signals were created
        user_signals = signal_service.get_signals_by_user(user_fixture.id)
        assert len(user_signals) >= 10

        # Bulk update
        for signal in user_signals[:5]:
            signal.reliability = 95.0

        db_session.commit()

        # Verify bulk update
        updated_signals = db_session.query(Signal).filter(
            Signal.creator_id == user_fixture.id,
            Signal.reliability == 95.0
        ).all()
        assert len(updated_signals) == 5

    def test_database_constraints_validation(self, db_session: Session, user_fixture: User):
        """Test database constraint validation."""
        # Test NOT NULL constraint
        with pytest.raises(Exception):  # Should raise IntegrityError
            signal = Signal(
                symbol=None,  # NULL value
                signal_type=SignalTypeEnum.BUY,
                entry_price=1.1234,
                creator_id=user_fixture.id
            )
            db_session.add(signal)
            db_session.commit()

        db_session.rollback()

        # Test foreign key constraint
        with pytest.raises(Exception):  # Should raise IntegrityError
            signal = Signal(
                symbol="TEST_SYMBOL",
                signal_type=SignalTypeEnum.BUY,
                entry_price=1.1234,
                creator_id=99999  # Non-existent user ID
            )
            db_session.add(signal)
            db_session.commit()

        db_session.rollback()

        # Test check constraint (if any)
        with pytest.raises(Exception):  # Should raise IntegrityError
            signal = Signal(
                symbol="TEST_SYMBOL",
                signal_type=SignalTypeEnum.BUY,
                entry_price=1.1234,
                reliability=150.0,  # Should be 0-100
                creator_id=user_fixture.id
            )
            db_session.add(signal)
            db_session.commit()

        db_session.rollback()

    def test_signal_expiry_management(self, db_session: Session, user_fixture: User):
        """Test signal expiry and time-based operations."""
        signal_service = SignalService(db_session)

        # Create expired signal
        expired_signal = Signal(
            symbol="EXPIRED_TEST",
            signal_type=SignalTypeEnum.BUY,
            entry_price=1.1234,
            creator_id=user_fixture.id,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            is_active=True
        )

        db_session.add(expired_signal)
        db_session.commit()

        # Create active signal
        active_signal = Signal(
            symbol="ACTIVE_TEST",
            signal_type=SignalTypeEnum.BUY,
            entry_price=1.1234,
            creator_id=user_fixture.id,
            expires_at=datetime.utcnow() + timedelta(hours=1),  # Active
            is_active=True
        )

        db_session.add(active_signal)
        db_session.commit()

        # Test expired signals query
        expired_signals = signal_service.get_expired_signals()
        assert len(expired_signals) >= 1
        assert any(s.id == expired_signal.id for s in expired_signals)

        # Test active signals query
        active_signals = signal_service.get_active_signals()
        assert len(active_signals) >= 1
        assert any(s.id == active_signal.id for s in active_signals)

    def test_database_backup_and_recovery_simulation(self, db_session: Session, user_fixture: User, multiple_signals_fixture: List[Signal]):
        """Test database backup and recovery simulation."""
        # Get current state
        initial_user_count = db_session.query(User).count()
        initial_signal_count = db_session.query(Signal).count()

        # Simulate data backup (export)
        backup_data = {
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "is_active": u.is_active
                }
                for u in db_session.query(User).all()
            ],
            "signals": [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "signal_type": s.signal_type.value,
                    "entry_price": s.entry_price,
                    "creator_id": s.creator_id
                }
                for s in db_session.query(Signal).all()
            ]
        }

        # Verify backup data integrity
        assert len(backup_data["users"]) == initial_user_count
        assert len(backup_data["signals"]) == initial_signal_count

        # Simulate data restoration verification
        # In a real scenario, this would involve importing the backup
        assert backup_data["users"][0]["username"] == user_fixture.username
        assert backup_data["signals"][0]["symbol"] == multiple_signals_fixture[0].symbol

    def test_concurrent_signal_updates(self, db_session: Session, signal_fixture: Signal):
        """Test concurrent signal updates and conflict resolution."""
        import threading
        import time

        results = []

        def update_signal_reliability(reliability: float):
            try:
                # Get fresh signal from database
                signal = db_session.query(Signal).filter(Signal.id == signal_fixture.id).first()
                if signal:
                    signal.reliability = reliability
                    db_session.commit()
                    results.append(("success", reliability))
                else:
                    results.append(("error", "Signal not found"))
            except Exception as e:
                results.append(("error", str(e)))
                db_session.rollback()

        # Create multiple threads for concurrent updates
        threads = []
        for i in range(5):
            reliability = 80.0 + (i * 5.0)
            thread = threading.Thread(target=update_signal_reliability, args=(reliability,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify operations completed (some may succeed, some may have conflicts)
        successes = [r for r in results if r[0] == "success"]
        assert len(successes) > 0

        # Verify final state
        final_signal = db_session.query(Signal).filter(Signal.id == signal_fixture.id).first()
        assert final_signal is not None
        assert final_signal.reliability >= 80.0

    def test_database_performance_under_load(self, db_session: Session, user_fixture: User):
        """Test database performance under load."""
        import time
        import threading

        # Create test data
        signals_to_create = 100
        results = []

        def create_bulk_signals(start_id: int, count: int):
            try:
                start_time = time.time()
                signals = []
                for i in range(count):
                    signal = Signal(
                        symbol=f"BULK_{start_id + i}",
                        signal_type=SignalTypeEnum.BUY,
                        entry_price=1.1000 + (i * 0.001),
                        creator_id=user_fixture.id,
                        reliability=70.0 + (i % 30),
                        is_active=True
                    )
                    signals.append(signal)

                db_session.add_all(signals)
                db_session.commit()
                end_time = time.time()
                results.append(("success", count, end_time - start_time))
            except Exception as e:
                results.append(("error", str(e)))

        # Create multiple threads for concurrent operations
        threads = []
        thread_count = 5
        signals_per_thread = signals_to_create // thread_count

        for i in range(thread_count):
            start_id = i * signals_per_thread
            thread = threading.Thread(target=create_bulk_signals, args=(start_id, signals_per_thread))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all operations succeeded
        successes = [r for r in results if r[0] == "success"]
        assert len(successes) == thread_count

        # Verify total signals created
        final_signal_count = db_session.query(Signal).filter(Signal.creator_id == user_fixture.id).count()
        assert final_signal_count >= signals_to_create

        # Verify performance (each thread should complete in reasonable time)
        for success in successes:
            _, count, execution_time = success
            assert execution_time < 5.0, f"Thread execution too slow: {execution_time:.3f}s"