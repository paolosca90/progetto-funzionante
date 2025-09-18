"""
Test data seeding for realistic scenarios.
Provides comprehensive test data factories and seeding utilities for integration tests.
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from factory import Factory, Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from models import (
    Base, User, Signal, SignalExecution, OANDAConnection, Subscription,
    SignalStatusEnum, SignalTypeEnum
)
from schemas import UserCreate, SignalCreate


class UserFactory(SQLAlchemyModelFactory):
    """Factory for creating realistic User test data."""
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    username = Faker("user_name")
    email = Faker("email")
    full_name = Faker("name")
    hashed_password = "hashed_test_password"
    is_active = True
    is_admin = False
    subscription_active = True
    created_at = Faker("date_time_this_year")
    trial_end = Faker("date_time_this_month", end_datetime="+30d")


class SignalFactory(SQLAlchemyModelFactory):
    """Factory for creating realistic Signal test data."""
    class Meta:
        model = Signal
        sqlalchemy_session_persistence = "commit"

    symbol = Faker("currency_code")
    signal_type = Faker("random_element", elements=list(SignalTypeEnum))
    entry_price = Faker("pyfloat", min_value=0.5, max_value=2.0)
    stop_loss = Faker("pyfloat", min_value=0.4, max_value=1.9)
    take_profit = Faker("pyfloat", min_value=0.6, max_value=2.1)
    reliability = Faker("pyfloat", min_value=60.0, max_value=95.0)
    confidence_score = Faker("pyfloat", min_value=0.6, max_value=0.95)
    risk_level = Faker("random_element", elements=["LOW", "MEDIUM", "HIGH"])
    status = SignalStatusEnum.ACTIVE
    is_public = True
    is_active = True
    created_at = Faker("date_time_this_month")
    expires_at = Faker("date_time_this_month", end_datetime="+48h")
    source = Faker("random_element", elements=["OANDA_AI", "MANUAL", "API", "ALGORITHM"])
    timeframe = Faker("random_element", elements=["M1", "M5", "M15", "H1", "H4", "D1"])
    ai_analysis = Faker("paragraph", nb_sentences=3)
    risk_reward_ratio = Faker("pyfloat", min_value=1.5, max_value=3.0)
    position_size_suggestion = Faker("pyfloat", min_value=0.01, max_value=1.0)
    spread = Faker("pyfloat", min_value=0.0001, max_value=0.005)
    volatility = Faker("pyfloat", min_value=0.1, max_value=0.5)
    technical_score = Faker("pyfloat", min_value=50.0, max_value=90.0)
    rsi = Faker("pyfloat", min_value=20.0, max_value=80.0)
    macd_signal = Faker("pyfloat", min_value=-0.01, max_value=0.01)
    market_session = Faker("random_element", elements=["London", "New York", "Tokyo", "Sydney", "Overlap"])


class OANDAConnectionFactory(SQLAlchemyModelFactory):
    """Factory for creating realistic OANDA connection test data."""
    class Meta:
        model = OANDAConnection
        sqlalchemy_session_persistence = "commit"

    account_id = Faker("numerify", text="###-###-######-###")
    environment = Faker("random_element", elements=["demo", "live"])
    account_currency = Faker("currency_code")
    is_active = True
    connection_status = Faker("random_element", elements=["CONNECTED", "DISCONNECTED", "ERROR"])
    balance = Faker("pyfloat", min_value=1000.0, max_value=100000.0)
    equity = Faker("pyfloat", min_value=1000.0, max_value=100000.0)
    margin_used = Faker("pyfloat", min_value=0.0, max_value=50000.0)
    margin_available = Faker("pyfloat", min_value=500.0, max_value=95000.0)
    unrealized_pl = Faker("pyfloat", min_value=-5000.0, max_value=5000.0)
    auto_trading_enabled = Faker("boolean")
    risk_tolerance = Faker("random_element", elements=["LOW", "MEDIUM", "HIGH"])
    max_position_size = Faker("pyfloat", min_value=0.1, max_value=10.0)
    daily_loss_limit = Faker("pyfloat", min_value=100.0, max_value=5000.0)
    created_at = Faker("date_time_this_year")
    updated_at = Faker("date_time_this_month")


class SubscriptionFactory(SQLAlchemyModelFactory):
    """Factory for creating realistic Subscription test data."""
    class Meta:
        model = Subscription
        sqlalchemy_session_persistence = "commit"

    plan_name = Faker("random_element", elements=["TRIAL", "BASIC", "PREMIUM", "ENTERPRISE"])
    status = Faker("random_element", elements=["ACTIVE", "EXPIRED", "CANCELLED"])
    is_active = True
    start_date = Faker("date_time_this_year")
    end_date = Faker("date_time_this_month", end_datetime="+365d")
    payment_status = Faker("random_element", elements=["PENDING", "COMPLETED", "FAILED", "REFUNDED"])
    last_payment_date = Faker("date_time_this_month")


class TestDataSeeder:
    """Comprehensive test data seeder for realistic scenarios."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.factories = {
            'user': UserFactory,
            'signal': SignalFactory,
            'oanda_connection': OANDAConnectionFactory,
            'subscription': SubscriptionFactory
        }

    def create_realistic_user_dataset(self, count: int = 50) -> List[User]:
        """Create a realistic dataset of users with varying characteristics."""
        users = []

        # Create different user profiles
        user_profiles = [
            {"is_admin": True, "subscription_active": True, "count": 2},  # Admin users
            {"is_admin": False, "subscription_active": True, "count": 20},  # Active subscribers
            {"is_admin": False, "subscription_active": False, "count": 15},  # Inactive users
            {"is_admin": False, "subscription_active": True, "is_active": False, "count": 3},  # Deactivated users
            {"is_admin": False, "subscription_active": False, "trial_end": datetime.utcnow() - timedelta(days=1), "count": 10},  # Expired trial users
        ]

        for profile in user_profiles:
            for _ in range(profile["count"]):
                user_data = profile.copy()
                user_data.pop("count", None)

                user = UserFactory(**user_data)
                users.append(user)

        return users

    def create_realistic_signal_dataset(self, users: List[User], signals_per_user: int = 10) -> List[Signal]:
        """Create a realistic dataset of signals with various characteristics."""
        signals = []

        # Signal characteristics based on market conditions
        signal_profiles = [
            {
                "name": "high_confidence_buys",
                "signal_type": SignalTypeEnum.BUY,
                "reliability_range": (80.0, 95.0),
                "confidence_range": (0.8, 0.95),
                "risk_level": "LOW",
                "weight": 0.3
            },
            {
                "name": "moderate_risk_signals",
                "signal_type": None,  # Random
                "reliability_range": (65.0, 80.0),
                "confidence_range": (0.65, 0.8),
                "risk_level": "MEDIUM",
                "weight": 0.5
            },
            {
                "name": "high_risk_opportunities",
                "signal_type": None,  # Random
                "reliability_range": (50.0, 70.0),
                "confidence_range": (0.5, 0.7),
                "risk_level": "HIGH",
                "weight": 0.2
            }
        ]

        for user in users:
            for _ in range(signals_per_user):
                # Select signal profile based on weights
                profile = self._weighted_choice(signal_profiles)

                # Create signal with profile characteristics
                signal_data = {
                    "creator_id": user.id,
                    "signal_type": profile["signal_type"] or self._random_signal_type(),
                    "reliability": self._random_float(*profile["reliability_range"]),
                    "confidence_score": self._random_float(*profile["confidence_range"]),
                    "risk_level": profile["risk_level"],
                }

                signal = SignalFactory(**signal_data)
                signals.append(signal)

        return signals

    def create_realistic_market_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Create realistic market data for given symbols."""
        market_data = {}

        base_prices = {
            "EUR_USD": 1.1234,
            "GBP_USD": 1.3456,
            "USD_JPY": 110.45,
            "USD_CHF": 0.9234,
            "AUD_USD": 0.7567,
            "USD_CAD": 1.2543,
            "NZD_USD": 0.6890
        }

        for symbol in symbols:
            base_price = base_prices.get(symbol, 1.0)

            # Add realistic market variation
            variation = 0.001  # 0.1% variation
            current_price = base_price + (self._random_float(-variation, variation) * base_price)

            market_data[symbol] = {
                "price": current_price,
                "bid": current_price - 0.0001,
                "ask": current_price + 0.0001,
                "spread": 0.0001 + self._random_float(0, 0.0004),
                "timestamp": datetime.utcnow().isoformat(),
                "volume": self._random_int(100, 5000),
                "daily_high": current_price * (1 + self._random_float(0, 0.002)),
                "daily_low": current_price * (1 - self._random_float(0, 0.002)),
                "daily_change": self._random_float(-0.01, 0.01),
                "volatility": self._random_float(0.1, 0.5),
            }

        return market_data

    def create_realistic_oanda_connections(self, users: List[User]) -> List[OANDAConnection]:
        """Create realistic OANDA connections for users."""
        connections = []

        # Only create connections for active subscribers
        active_users = [u for u in users if u.subscription_active and u.is_active]

        for user in active_users:
            # 70% of active users have OANDA connections
            if self._random_float(0, 1) < 0.7:
                connection = OANDAConnectionFactory(user_id=user.id)
                connections.append(connection)

        return connections

    def create_realistic_subscriptions(self, users: List[User]) -> List[Subscription]:
        """Create realistic subscription data for users."""
        subscriptions = []

        subscription_plans = [
            {"plan_name": "TRIAL", "weight": 0.3, "duration_days": 30},
            {"plan_name": "BASIC", "weight": 0.4, "duration_days": 90},
            {"plan_name": "PREMIUM", "weight": 0.25, "duration_days": 365},
            {"plan_name": "ENTERPRISE", "weight": 0.05, "duration_days": 365},
        ]

        for user in users:
            if not user.subscription_active:
                continue

            # Select plan based on weights
            plan = self._weighted_choice(subscription_plans)

            subscription_data = {
                "user_id": user.id,
                "plan_name": plan["plan_name"],
                "start_date": datetime.utcnow() - timedelta(days=self._random_int(1, plan["duration_days"] - 1)),
                "end_date": datetime.utcnow() + timedelta(days=self._random_int(1, plan["duration_days"])),
                "status": "ACTIVE",
                "is_active": True,
                "payment_status": "COMPLETED"
            }

            subscription = SubscriptionFactory(**subscription_data)
            subscriptions.append(subscription)

        return subscriptions

    def create_historical_signal_data(self, users: List[User], days_back: int = 30) -> List[Signal]:
        """Create historical signal data for analysis."""
        historical_signals = []

        for user in users:
            if not user.subscription_active:
                continue

            # Create varying number of signals per day
            signals_per_day = self._random_int(1, 5)

            for day_offset in range(days_back):
                signal_date = datetime.utcnow() - timedelta(days=day_offset)

                for _ in range(signals_per_day):
                    # Random hour during trading hours
                    trading_hour = self._random_int(0, 23)
                    signal_timestamp = signal_date.replace(
                        hour=trading_hour,
                        minute=self._random_int(0, 59),
                        second=self._random_int(0, 59)
                    )

                    signal_data = {
                        "creator_id": user.id,
                        "created_at": signal_timestamp,
                        "expires_at": signal_timestamp + timedelta(hours=self._random_int(1, 48)),
                        "signal_type": self._random_signal_type(),
                        "reliability": self._random_float(50.0, 90.0),
                        "status": self._random_signal_status(),
                    }

                    signal = SignalFactory(**signal_data)
                    historical_signals.append(signal)

        return historical_signals

    def create_signal_executions(self, signals: List[Signal], users: List[User]) -> List[SignalExecution]:
        """Create realistic signal execution data."""
        executions = []

        for signal in signals:
            # 30% of signals get executed
            if self._random_float(0, 1) < 0.3:
                # Random user execution (not necessarily the creator)
                executing_user = self._random_choice(users)

                execution_data = {
                    "signal_id": signal.id,
                    "user_id": executing_user.id,
                    "execution_price": signal.entry_price + self._random_float(-0.001, 0.001),
                    "quantity": self._random_float(0.1, 2.0),
                    "execution_type": self._random_choice(["MANUAL", "AUTO"]),
                    "executed_at": signal.created_at + timedelta(minutes=self._random_int(1, 1440)),
                    "current_price": signal.entry_price + self._random_float(-0.01, 0.01),
                    "unrealized_pnl": self._random_float(-100.0, 100.0),
                    "realized_pnl": None if self._random_float(0, 1) < 0.7 else self._random_float(-50.0, 50.0)
                }

                execution = SignalExecution(**execution_data)
                executions.append(execution)

        return executions

    def seed_comprehensive_test_data(self) -> Dict[str, Any]:
        """Seed comprehensive test data for integration testing."""
        print("Seeding comprehensive test data...")

        # Create users
        print("  Creating users...")
        users = self.create_realistic_user_dataset(100)

        # Create subscriptions
        print("  Creating subscriptions...")
        subscriptions = self.create_realistic_subscriptions(users)

        # Create signals
        print("  Creating signals...")
        signals = self.create_realistic_signal_dataset(users, signals_per_user=15)

        # Create historical signals
        print("  Creating historical signals...")
        historical_signals = self.create_historical_signal_data(users, days_back=30)

        # Create OANDA connections
        print("  Creating OANDA connections...")
        oanda_connections = self.create_realistic_oanda_connections(users)

        # Create signal executions
        print("  Creating signal executions...")
        signal_executions = self.create_signal_executions(signals, users)

        # Commit all changes
        self.db_session.commit()

        print(f"  Created {len(users)} users")
        print(f"  Created {len(subscriptions)} subscriptions")
        print(f"  Created {len(signals)} current signals")
        print(f"  Created {len(historical_signals)} historical signals")
        print(f"  Created {len(oanda_connections)} OANDA connections")
        print(f"  Created {len(signal_executions)} signal executions")

        return {
            "users": users,
            "subscriptions": subscriptions,
            "signals": signals + historical_signals,
            "oanda_connections": oanda_connections,
            "signal_executions": signal_executions
        }

    def create_market_scenario_data(self, scenario: str) -> Dict[str, Any]:
        """Create test data for specific market scenarios."""
        scenarios = {
            "bull_market": {
                "signal_distribution": {"BUY": 0.7, "SELL": 0.2, "HOLD": 0.1},
                "reliability_boost": 5.0,
                "price_trend": "up"
            },
            "bear_market": {
                "signal_distribution": {"BUY": 0.2, "SELL": 0.7, "HOLD": 0.1},
                "reliability_boost": 5.0,
                "price_trend": "down"
            },
            "sideways_market": {
                "signal_distribution": {"BUY": 0.3, "SELL": 0.3, "HOLD": 0.4},
                "reliability_boost": 0.0,
                "price_trend": "flat"
            },
            "high_volatility": {
                "signal_distribution": {"BUY": 0.4, "SELL": 0.4, "HOLD": 0.2},
                "reliability_boost": -5.0,
                "volatility_multiplier": 2.0
            }
        }

        return scenarios.get(scenario, scenarios["sideways_market"])

    def create_performance_test_data(self, scale_factor: int = 1) -> Dict[str, Any]:
        """Create large-scale test data for performance testing."""
        print(f"Creating performance test data (scale factor: {scale_factor})...")

        # Calculate dataset sizes
        user_count = 1000 * scale_factor
        signals_per_user = 20 * scale_factor

        # Create large datasets efficiently
        batch_size = 1000
        all_users = []

        # Create users in batches
        for batch_start in range(0, user_count, batch_size):
            batch_users = []
            for _ in range(min(batch_size, user_count - batch_start)):
                user = UserFactory()
                batch_users.append(user)

            self.db_session.add_all(batch_users)
            self.db_session.commit()
            all_users.extend(batch_users)

            print(f"  Created {len(all_users)} users...")

        # Create signals in batches
        all_signals = []
        for user_batch_start in range(0, len(all_users), batch_size):
            user_batch = all_users[user_batch_start:user_batch_start + batch_size]

            for user in user_batch:
                for _ in range(signals_per_user):
                    signal = SignalFactory(creator_id=user.id)
                    all_signals.append(signal)

                # Commit in batches
                if len(all_signals) >= batch_size:
                    self.db_session.add_all(all_signals[-batch_size:])
                    self.db_session.commit()

            print(f"  Created {len(all_signals)} signals...")

        # Final commit for remaining signals
        if all_signals:
            self.db_session.add_all(all_signals)
            self.db_session.commit()

        print(f"Performance test data created:")
        print(f"  Users: {len(all_users)}")
        print(f"  Signals: {len(all_signals)}")

        return {
            "users": all_users,
            "signals": all_signals
        }

    def create_edge_case_test_data(self) -> Dict[str, Any]:
        """Create test data for edge cases and boundary conditions."""
        edge_cases = {}

        # Users with extreme characteristics
        edge_cases["extreme_users"] = [
            UserFactory(username="user_with_max_signals"),
            UserFactory(username="user_no_subscription", subscription_active=False),
            UserFactory(username="user_expired_trial", trial_end=datetime.utcnow() - timedelta(days=1)),
            UserFactory(username="user_deactivated", is_active=False),
            UserFactory(username="user_admin", is_admin=True),
        ]

        # Signals with extreme values
        edge_cases["extreme_signals"] = [
            SignalFactory(reliability=100.0, confidence_score=1.0),
            SignalFactory(reliability=0.0, confidence_score=0.0),
            SignalFactory(entry_price=0.0001),  # Very low price
            SignalFactory(entry_price=9999.99),  # Very high price
            SignalFactory(expires_at=datetime.utcnow() - timedelta(days=1)),  # Already expired
            SignalFactory(expires_at=datetime.utcnow() + timedelta(days=365)),  # Long expiry
        ]

        # OANDA connections with edge cases
        edge_cases["extreme_connections"] = [
            OANDAConnectionFactory(balance=0.0),
            OANDAConnectionFactory(balance=1000000.0),
            OANDAConnectionFactory(margin_used=999999.0),
            OANDAConnectionFactory(is_active=False),
            OANDAConnectionFactory(connection_status="ERROR"),
        ]

        self.db_session.add_all(edge_cases["extreme_users"])
        self.db_session.add_all(edge_cases["extreme_signals"])
        self.db_session.add_all(edge_cases["extreme_connections"])
        self.db_session.commit()

        return edge_cases

    # Helper methods
    def _random_float(self, min_val: float, max_val: float) -> float:
        """Generate random float in range."""
        import random
        return random.uniform(min_val, max_val)

    def _random_int(self, min_val: int, max_val: int) -> int:
        """Generate random integer in range."""
        import random
        return random.randint(min_val, max_val)

    def _random_choice(self, choices: List) -> Any:
        """Generate random choice from list."""
        import random
        return random.choice(choices)

    def _random_signal_type(self) -> SignalTypeEnum:
        """Generate random signal type."""
        return self._random_choice(list(SignalTypeEnum))

    def _random_signal_status(self) -> SignalStatusEnum:
        """Generate random signal status."""
        return self._random_choice(list(SignalStatusEnum))

    def _weighted_choice(self, choices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make weighted choice from list of dictionaries with 'weight' key."""
        import random
        weights = [choice["weight"] for choice in choices]
        return random.choices(choices, weights=weights)[0]


# Pytest fixtures for test data seeding
@pytest.fixture
def test_data_seeder(db_session: Session) -> TestDataSeeder:
    """Create test data seeder instance."""
    return TestDataSeeder(db_session)


@pytest.fixture
def realistic_test_data(db_session: Session, test_data_seeder: TestDataSeeder) -> Dict[str, Any]:
    """Create realistic test data for integration tests."""
    return test_data_seeder.seed_comprehensive_test_data()


@pytest.fixture
def performance_test_data(db_session: Session, test_data_seeder: TestDataSeeder) -> Dict[str, Any]:
    """Create performance test data."""
    return test_data_seeder.create_performance_test_data(scale_factor=1)


@pytest.fixture
def edge_case_test_data(db_session: Session, test_data_seeder: TestDataSeeder) -> Dict[str, Any]:
    """Create edge case test data."""
    return test_data_seeder.create_edge_case_test_data()


@pytest.fixture
def market_scenario_data(db_session: Session, test_data_seeder: TestDataSeeder) -> Dict[str, Any]:
    """Create market scenario test data."""
    # Create base users and signals
    users = test_data_seeder.create_realistic_user_dataset(50)
    signals = test_data_seeder.create_realistic_signal_dataset(users, signals_per_user=10)

    # Apply scenario-specific modifications
    scenario = test_data_seeder.create_market_scenario_data("bull_market")

    # Modify signals based on scenario
    for signal in signals:
        # Apply signal type distribution
        signal_type = test_data_seeder._weighted_choice([
            {"type": SignalTypeEnum.BUY, "weight": scenario["signal_distribution"]["BUY"]},
            {"type": SignalTypeEnum.SELL, "weight": scenario["signal_distribution"]["SELL"]},
            {"type": SignalTypeEnum.HOLD, "weight": scenario["signal_distribution"]["HOLD"]}
        ])
        signal.signal_type = signal_type["type"]

        # Apply reliability boost
        signal.reliability = min(100.0, signal.reliability + scenario["reliability_boost"])

    db_session.commit()

    return {
        "users": users,
        "signals": signals,
        "scenario": scenario
    }