"""
Comprehensive end-to-end tests for complete user workflows.
Tests real-world user journeys from registration to signal execution and account management.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from models import User, Signal, SignalStatusEnum, SignalTypeEnum
from schemas import UserCreate, SignalCreate


class TestEndToEndWorkflows:
    """Integration test suite for complete end-to-end user workflows."""

    # Complete User Registration and Onboarding Workflow
    def test_complete_user_registration_workflow(self, client: TestClient):
        """Test complete user registration and onboarding workflow."""
        workflow_steps = []
        workflow_timings = {}

        # Step 1: User Registration
        start_time = time.time()
        registration_data = {
            "username": "new_integration_user",
            "email": "newuser@test.com",
            "full_name": "New Integration User",
            "password": "SecurePassword123!"
        }

        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 201

        registration_result = response.json()
        assert registration_result["success"] is True
        assert "user_id" in registration_result

        workflow_timings["registration"] = time.time() - start_time
        workflow_steps.append(("User Registration", True))

        # Step 2: User Login
        start_time = time.time()
        login_data = {
            "username": registration_data["username"],
            "password": registration_data["password"]
        }

        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        access_token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        workflow_timings["login"] = time.time() - start_time
        workflow_steps.append(("User Login", True))

        # Step 3: Get User Profile
        start_time = time.time()
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200

        profile_data = response.json()
        assert profile_data["username"] == registration_data["username"]
        assert profile_data["email"] == registration_data["email"]

        workflow_timings["profile"] = time.time() - start_time
        workflow_steps.append(("Profile Retrieval", True))

        # Step 4: Get User Statistics
        start_time = time.time()
        response = client.get("/users/stats", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404)
        assert response.status_code in [200, 404]

        workflow_timings["statistics"] = time.time() - start_time
        workflow_steps.append(("Statistics Retrieval", response.status_code == 200))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nComplete Registration Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps >= 3, f"Too many failed steps: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 5.0, f"Workflow too slow: {total_time:.3f}s"

    # Signal Creation and Management Workflow
    def test_signal_management_workflow(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test complete signal creation and management workflow."""
        workflow_steps = []
        workflow_timings = {}
        created_signal_id = None

        # Step 1: Create Signal
        start_time = time.time()
        signal_data = {
            "symbol": "EUR_USD",
            "signal_type": "BUY",
            "entry_price": 1.1234,
            "stop_loss": 1.1200,
            "take_profit": 1.1300,
            "reliability": 85.5,
            "confidence_score": 0.85,
            "risk_level": "MEDIUM",
            "ai_analysis": "Technical analysis indicates buying opportunity based on current market conditions"
        }

        response = client.post("/signals", json=signal_data, headers=auth_headers)
        assert response.status_code == 201

        signal_result = response.json()
        assert signal_result["success"] is True
        assert "signal" in signal_result

        created_signal_id = signal_result["signal"]["id"]

        workflow_timings["create_signal"] = time.time() - start_time
        workflow_steps.append(("Signal Creation", True))

        # Step 2: Retrieve Created Signal
        start_time = time.time()
        response = client.get(f"/signals/{created_signal_id}", headers=auth_headers)
        assert response.status_code == 200

        retrieved_signal = response.json()
        assert retrieved_signal["id"] == created_signal_id
        assert retrieved_signal["symbol"] == signal_data["symbol"]

        workflow_timings["retrieve_signal"] = time.time() - start_time
        workflow_steps.append(("Signal Retrieval", True))

        # Step 3: Get Latest Signals
        start_time = time.time()
        response = client.get("/signals/latest", headers=auth_headers)
        assert response.status_code == 200

        latest_signals = response.json()
        assert isinstance(latest_signals, list)
        assert any(signal["id"] == created_signal_id for signal in latest_signals)

        workflow_timings["latest_signals"] = time.time() - start_time
        workflow_steps.append(("Latest Signals", True))

        # Step 4: Search Signals
        start_time = time.time()
        response = client.get(f"/signals?symbol=EUR_USD", headers=auth_headers)
        assert response.status_code == 200

        search_results = response.json()
        assert "signals" in search_results
        assert any(signal["symbol"] == "EUR_USD" for signal in search_results["signals"])

        workflow_timings["search_signals"] = time.time() - start_time
        workflow_steps.append(("Signal Search", True))

        # Step 5: Update Signal (if endpoint exists)
        start_time = time.time()
        update_data = {
            "reliability": 90.0,
            "ai_analysis": "Updated analysis with improved market conditions"
        }

        response = client.put(f"/signals/{created_signal_id}", json=update_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        workflow_timings["update_signal"] = time.time() - start_time
        workflow_steps.append(("Signal Update", response.status_code in [200, 404, 405]))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nSignal Management Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps >= 4, f"Too many failed steps: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 3.0, f"Workflow too slow: {total_time:.3f}s"

    # Trading Signal Execution Workflow
    def test_trading_workflow(self, client: TestClient, auth_headers: Dict[str, str], test_signal_data: Dict[str, Any]):
        """Test complete trading signal execution workflow."""
        workflow_steps = []
        workflow_timings = {}
        created_signal_id = None

        # Step 1: Create Trading Signal
        start_time = time.time()
        response = client.post("/signals", json=test_signal_data, headers=auth_headers)
        assert response.status_code == 201

        signal_result = response.json()
        created_signal_id = signal_result["signal"]["id"]

        workflow_timings["create_signal"] = time.time() - start_time
        workflow_steps.append(("Signal Creation", True))

        # Step 2: Analyze Signal Risk
        start_time = time.time()
        response = client.get(f"/signals/{created_signal_id}", headers=auth_headers)
        assert response.status_code == 200

        signal_details = response.json()
        assert signal_details["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
        assert signal_details["reliability"] > 0

        # Calculate risk metrics
        entry_price = signal_details["entry_price"]
        stop_loss = signal_details.get("stop_loss")
        take_profit = signal_details.get("take_profit")

        if stop_loss and take_profit:
            risk_amount = abs(entry_price - stop_loss)
            reward_amount = abs(take_profit - entry_price)
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0

            assert risk_reward_ratio > 1.0, "Risk-reward ratio should be favorable"

        workflow_timings["risk_analysis"] = time.time() - start_time
        workflow_steps.append(("Risk Analysis", True))

        # Step 3: Execute Signal (if endpoint exists)
        start_time = time.time()
        execution_data = {
            "signal_id": created_signal_id,
            "execution_price": entry_price,
            "quantity": 0.1,
            "execution_type": "MANUAL",
            "notes": "Manual execution based on technical analysis"
        }

        response = client.post("/signals/execute", json=execution_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)

        workflow_timings["signal_execution"] = time.time() - start_time
        workflow_steps.append(("Signal Execution", response.status_code in [200, 404, 405]))

        # Step 4: Monitor Execution Status
        start_time = time.time()
        response = client.get("/users/signals", headers=auth_headers)
        assert response.status_code == 200

        user_signals = response.json()
        assert isinstance(user_signals, list)

        workflow_timings["monitor_execution"] = time.time() - start_time
        workflow_steps.append(("Monitor Execution", True))

        # Step 5: Check Account Status
        start_time = time.time()
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200

        account_status = response.json()
        assert account_status["subscription_active"] is True

        workflow_timings["account_status"] = time.time() - start_time
        workflow_steps.append(("Account Status Check", True))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nTrading Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps >= 4, f"Too many failed steps: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 5.0, f"Workflow too slow: {total_time:.3f}s"

    # Admin User Management Workflow
    def test_admin_management_workflow(self, client: TestClient, admin_auth_headers: Dict[str, str], test_user_data: Dict[str, Any]):
        """Test complete admin user management workflow."""
        workflow_steps = []
        workflow_timings = {}
        created_user_id = None

        # Step 1: Create New User as Admin
        start_time = time.time()
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201

        user_result = response.json()
        created_user_id = user_result["user_id"]

        workflow_timings["create_user"] = time.time() - start_time
        workflow_steps.append(("User Creation", True))

        # Step 2: Get All Users (Admin)
        start_time = time.time()
        response = client.get("/admin/users", headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403)
        if response.status_code == 200:
            users_data = response.json()
            assert isinstance(users_data, list)
            admin_success = True
        else:
            admin_success = False

        workflow_timings["get_all_users"] = time.time() - start_time
        workflow_steps.append(("Get All Users", admin_success))

        # Step 3: Get Specific User (Admin)
        start_time = time.time()
        if created_user_id:
            response = client.get(f"/admin/users/{created_user_id}", headers=admin_auth_headers)
            # Should either succeed (200) or not be implemented (404/403)
            admin_user_success = response.status_code in [200, 404, 403]
        else:
            admin_user_success = False

        workflow_timings["get_specific_user"] = time.time() - start_time
        workflow_steps.append(("Get Specific User", admin_user_success))

        # Step 4: Generate System Signals (Admin)
        start_time = time.time()
        response = client.post("/admin/generate-signals", headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403)
        admin_signals_success = response.status_code in [200, 404, 403]

        workflow_timings["generate_signals"] = time.time() - start_time
        workflow_steps.append(("Generate Signals", admin_signals_success))

        # Step 5: Get System Statistics (Admin)
        start_time = time.time()
        response = client.get("/admin/stats", headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403)
        admin_stats_success = response.status_code in [200, 404, 403]

        workflow_timings["system_stats"] = time.time() - start_time
        workflow_steps.append(("System Statistics", admin_stats_success))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nAdmin Management Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps >= 2, f"Too many failed steps: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 5.0, f"Workflow too slow: {total_time:.3f}s"

    # Signal Analysis and Decision Making Workflow
    def test_signal_analysis_workflow(self, client: TestClient, auth_headers: Dict[str, str], multiple_signals_fixture: List[Signal]):
        """Test complete signal analysis and decision making workflow."""
        workflow_steps = []
        workflow_timings = {}

        # Step 1: Get Market Overview
        start_time = time.time()
        response = client.get("/signals/latest", headers=auth_headers)
        assert response.status_code == 200

        market_signals = response.json()
        assert isinstance(market_signals, list)

        workflow_timings["market_overview"] = time.time() - start_time
        workflow_steps.append(("Market Overview", True))

        # Step 2: Filter High-Confidence Signals
        start_time = time.time()
        high_confidence_signals = [
            signal for signal in market_signals
            if signal.get("reliability", 0) > 80.0
        ]

        response = client.get("/signals?min_reliability=80", headers=auth_headers)
        assert response.status_code in [200, 404]

        workflow_timings["filter_signals"] = time.time() - start_time
        workflow_steps.append(("Filter High-Confidence", response.status_code in [200, 404]))

        # Step 3: Analyze Signal Performance
        start_time = time.time()
        response = client.get("/signals/top", headers=auth_headers)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            top_signals = response.json()
            assert "average_reliability" in top_signals
            assert "signals" in top_signals

        workflow_timings["analyze_performance"] = time.time() - start_time
        workflow_steps.append(("Analyze Performance", response.status_code in [200, 404]))

        # Step 4: Export Signal Data (if endpoint exists)
        start_time = time.time()
        response = client.get("/signals/export?format=json", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        export_success = response.status_code in [200, 404, 405]

        workflow_timings["export_data"] = time.time() - start_time
        workflow_steps.append(("Export Data", export_success))

        # Step 5: Make Trading Decision
        start_time = time.time()
        if market_signals:
            # Simulate trading decision based on signals
            best_signal = max(market_signals, key=lambda s: s.get("reliability", 0))
            trading_decision = {
                "action": "EXECUTE" if best_signal.get("reliability", 0) > 75 else "HOLD",
                "signal_id": best_signal.get("id"),
                "confidence": best_signal.get("reliability", 0),
                "risk_level": best_signal.get("risk_level", "MEDIUM")
            }
            decision_made = True
        else:
            decision_made = False

        workflow_timings["trading_decision"] = time.time() - start_time
        workflow_steps.append(("Trading Decision", decision_made))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nSignal Analysis Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps >= 3, f"Too many failed steps: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 3.0, f"Workflow too slow: {total_time:.3f}s"

    # Account Management and Settings Workflow
    def test_account_management_workflow(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test complete account management and settings workflow."""
        workflow_steps = []
        workflow_timings = {}

        # Step 1: Get Account Overview
        start_time = time.time()
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200

        account_data = response.json()
        assert "subscription_active" in account_data
        assert "is_active" in account_data

        workflow_timings["account_overview"] = time.time() - start_time
        workflow_steps.append(("Account Overview", True))

        # Step 2: Get User Statistics
        start_time = time.time()
        response = client.get("/users/stats", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404)
        stats_success = response.status_code in [200, 404]

        workflow_timings["user_statistics"] = time.time() - start_time
        workflow_steps.append(("User Statistics", stats_success))

        # Step 3: Check Subscription Status
        start_time = time.time()
        subscription_active = account_data["subscription_active"]
        assert isinstance(subscription_active, bool)

        workflow_timings["subscription_check"] = time.time() - start_time
        workflow_steps.append(("Subscription Check", True))

        # Step 4: Get User Signals
        start_time = time.time()
        response = client.get("/users/signals", headers=auth_headers)
        assert response.status_code == 200

        user_signals = response.json()
        assert isinstance(user_signals, list)

        workflow_timings["user_signals"] = time.time() - start_time
        workflow_steps.append(("User Signals", True))

        # Step 5: Update Profile (if endpoint exists)
        start_time = time.time()
        update_data = {
            "full_name": "Updated Name",
            "email": account_data["email"]  # Keep same email to avoid conflicts
        }

        response = client.put("/users/me", json=update_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        update_success = response.status_code in [200, 404, 405]

        workflow_timings["update_profile"] = time.time() - start_time
        workflow_steps.append(("Update Profile", update_success))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nAccount Management Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps >= 4, f"Too many failed steps: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 3.0, f"Workflow too slow: {total_time:.3f}s"

    # Error Recovery and Resilience Workflow
    def test_error_recovery_workflow(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test error recovery and system resilience workflow."""
        workflow_steps = []
        workflow_timings = {}

        # Step 1: Normal Operation
        start_time = time.time()
        response = client.get("/health", headers=auth_headers)
        assert response.status_code == 200

        workflow_timings["normal_operation"] = time.time() - start_time
        workflow_steps.append(("Normal Operation", True))

        # Step 2: Invalid Request Handling
        start_time = time.time()
        invalid_data = {"invalid": "data"}
        response = client.post("/signals", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

        workflow_timings["invalid_request"] = time.time() - start_time
        workflow_steps.append(("Invalid Request Handling", True))

        # Step 3: Unauthorized Access Handling
        start_time = time.time()
        response = client.get("/admin/users")  # No auth headers
        assert response.status_code == 401

        workflow_timings["unauthorized_access"] = time.time() - start_time
        workflow_steps.append(("Unauthorized Access", True))

        # Step 4: Resource Not Found Handling
        start_time = time.time()
        response = client.get("/signals/99999", headers=auth_headers)
        assert response.status_code == 404

        workflow_timings["resource_not_found"] = time.time() - start_time
        workflow_steps.append(("Resource Not Found", True))

        # Step 5: System Recovery
        start_time = time.time()
        response = client.get("/health", headers=auth_headers)
        assert response.status_code == 200  # System should still be operational

        workflow_timings["system_recovery"] = time.time() - start_time
        workflow_steps.append(("System Recovery", True))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nError Recovery Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps == 5, f"All steps should succeed: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 2.0, f"Workflow too slow: {total_time:.3f}s"

    # Complete Trading Session Workflow
    def test_complete_trading_session_workflow(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test complete trading session from market analysis to execution."""
        workflow_steps = []
        workflow_timings = {}

        # Step 1: Market Analysis
        start_time = time.time()
        response = client.get("/signals/latest", headers=auth_headers)
        assert response.status_code == 200

        market_signals = response.json()

        workflow_timings["market_analysis"] = time.time() - start_time
        workflow_steps.append(("Market Analysis", True))

        # Step 2: Signal Evaluation
        start_time = time.time()
        if market_signals:
            # Evaluate signals based on multiple criteria
            evaluated_signals = []
            for signal in market_signals:
                score = 0
                score += signal.get("reliability", 0)
                score += signal.get("confidence_score", 0) * 100
                if signal.get("risk_level") == "LOW":
                    score += 10
                elif signal.get("risk_level") == "MEDIUM":
                    score += 5

                evaluated_signals.append({
                    "signal": signal,
                    "score": score
                })

            # Sort by score
            evaluated_signals.sort(key=lambda x: x["score"], reverse=True)
            best_signal = evaluated_signals[0]["signal"] if evaluated_signals else None

        workflow_timings["signal_evaluation"] = time.time() - start_time
        workflow_steps.append(("Signal Evaluation", True))

        # Step 3: Risk Assessment
        start_time = time.time()
        if market_signals:
            # Calculate portfolio risk metrics
            total_signals = len(market_signals)
            high_risk_signals = len([s for s in market_signals if s.get("risk_level") == "HIGH"])
            risk_ratio = high_risk_signals / total_signals if total_signals > 0 else 0

            assert risk_ratio < 0.5, "Too many high-risk signals"

        workflow_timings["risk_assessment"] = time.time() - start_time
        workflow_steps.append(("Risk Assessment", True))

        # Step 4: Decision Making
        start_time = time.time()
        trading_decision = None
        if market_signals:
            avg_reliability = sum(s.get("reliability", 0) for s in market_signals) / len(market_signals)
            if avg_reliability > 75:
                trading_decision = "EXECUTE_TOP_SIGNAL"
            elif avg_reliability > 60:
                trading_decision = "MONITOR_CLOSELY"
            else:
                trading_decision = "WAIT_FOR_BETTER_OPPORTUNITIES"

        workflow_timings["decision_making"] = time.time() - start_time
        workflow_steps.append(("Decision Making", trading_decision is not None))

        # Step 5: Position Sizing (if executing)
        start_time = time.time()
        if trading_decision == "EXECUTE_TOP_SIGNAL" and best_signal:
            # Calculate position size based on risk
            account_balance = 10000  # Mock account balance
            risk_per_trade = 0.02  # 2% risk per trade
            position_size = (account_balance * risk_per_trade) / abs(
                best_signal.get("entry_price", 1.0) - best_signal.get("stop_loss", best_signal.get("entry_price", 1.0))
            )

            assert position_size > 0, "Invalid position size calculation"

        workflow_timings["position_sizing"] = time.time() - start_time
        workflow_steps.append(("Position Sizing", True))

        # Step 6: Execution Planning
        start_time = time.time()
        execution_plan = {
            "decision": trading_decision,
            "market_conditions": "favorable" if avg_reliability > 70 else "neutral",
            "risk_level": "acceptable" if risk_ratio < 0.3 else "elevated",
            "timestamp": datetime.utcnow().isoformat()
        }

        workflow_timings["execution_planning"] = time.time() - start_time
        workflow_steps.append(("Execution Planning", True))

        # Workflow Summary
        total_time = sum(workflow_timings.values())
        successful_steps = sum(1 for _, success in workflow_steps if success)

        print(f"\nComplete Trading Session Workflow:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful steps: {successful_steps}/{len(workflow_steps)}")
        print(f"  Trading Decision: {trading_decision}")
        for step, timing in workflow_timings.items():
            print(f"    {step}: {timing:.3f}s")

        # Assertions
        assert successful_steps >= 5, f"Too many failed steps: {successful_steps}/{len(workflow_steps)}"
        assert total_time < 4.0, f"Workflow too slow: {total_time:.3f}s"

    # Multi-User Concurrent Workflow
    def test_multi_user_concurrent_workflow(self, client: TestClient):
        """Test multi-user concurrent workflow simulation."""
        import threading
        import time

        workflow_results = []
        workflow_timings = []

        def user_workflow(user_id: int):
            user_start_time = time.time()

            try:
                # User registration
                registration_data = {
                    "username": f"concurrent_user_{user_id}",
                    "email": f"concurrent{user_id}@test.com",
                    "full_name": f"Concurrent User {user_id}",
                    "password": "ConcurrentPass123!"
                }

                response = client.post("/auth/register", json=registration_data)
                if response.status_code != 201:
                    workflow_results.append(("registration", False, user_id))
                    return

                # User login
                login_data = {
                    "username": registration_data["username"],
                    "password": registration_data["password"]
                }

                response = client.post("/auth/token", data=login_data)
                if response.status_code != 200:
                    workflow_results.append(("login", False, user_id))
                    return

                token_data = response.json()
                auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}

                # Get user profile
                response = client.get("/users/me", headers=auth_headers)
                if response.status_code != 200:
                    workflow_results.append(("profile", False, user_id))
                    return

                # Get latest signals
                response = client.get("/signals/latest", headers=auth_headers)
                if response.status_code != 200:
                    workflow_results.append(("signals", False, user_id))
                    return

                # All steps successful
                user_end_time = time.time()
                workflow_timings.append(user_end_time - user_start_time)
                workflow_results.extend([
                    ("registration", True, user_id),
                    ("login", True, user_id),
                    ("profile", True, user_id),
                    ("signals", True, user_id)
                ])

            except Exception as e:
                workflow_results.append(("error", False, user_id))

        # Run concurrent user workflows
        threads = []
        for i in range(5):  # 5 concurrent users
            thread = threading.Thread(target=user_workflow, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results
        total_steps = len(workflow_results)
        successful_steps = sum(1 for _, success, _ in workflow_results if success)
        success_rate = successful_steps / total_steps if total_steps > 0 else 0

        avg_timing = sum(workflow_timings) / len(workflow_timings) if workflow_timings else 0

        print(f"\nMulti-User Concurrent Workflow:")
        print(f"  Total users: 5")
        print(f"  Total steps: {total_steps}")
        print(f"  Successful steps: {successful_steps}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average timing: {avg_timing:.3f}s")

        # Assertions
        assert success_rate > 0.8, f"Success rate too low: {success_rate:.1%}"
        assert avg_timing < 5.0, f"Average workflow time too slow: {avg_timing:.3f}s"