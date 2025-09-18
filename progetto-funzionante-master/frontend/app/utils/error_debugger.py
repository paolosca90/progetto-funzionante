"""
Error Debugging and Replay Tools
Debug errors, replay scenarios, and analyze error patterns
"""

import json
import hashlib
import pickle
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import traceback
import asyncio
import uuid

from app.core.sentry_config import sentry_config, ErrorSeverity, ErrorCategory
from config.settings import settings


class DebugAction(Enum):
    """Debug action types"""
    REPLAY_REQUEST = "replay_request"
    SIMULATE_ERROR = "simulate_error"
    ANALYZE_PATTERN = "analyze_pattern"
    INSPECT_STATE = "inspect_state"
    TEST_FIX = "test_fix"


@dataclass
class ErrorContext:
    """Error context for debugging"""
    error_id: str
    error_type: str
    error_message: str
    timestamp: str
    request_data: Dict[str, Any]
    user_context: Dict[str, Any]
    system_state: Dict[str, Any]
    stack_trace: str
    environment: str
    session_id: str


@dataclass
class DebugSession:
    """Debug session information"""
    session_id: str
    created_at: str
    error_context: ErrorContext
    actions: List[Dict[str, Any]]
    findings: List[str]
    recommendations: List[str]
    status: str = "active"


class ErrorDebugger:
    """
    Comprehensive error debugging system
    - Error context capture and preservation
    - Request replay capabilities
    - Error pattern analysis
    - Debug session management
    - Interactive debugging tools
    """

    def __init__(self):
        self.error_contexts: Dict[str, ErrorContext] = {}
        self.debug_sessions: Dict[str, DebugSession] = {}
        self.replay_history: List[Dict[str, Any]] = []
        self.pattern_analyzer = ErrorPatternAnalyzer()
        self.lock = asyncio.Lock()

    async def capture_error_context(self, error: Exception, request_data: Dict[str, Any] = None,
                                 user_context: Dict[str, Any] = None) -> str:
        """Capture comprehensive error context for debugging"""
        error_id = f"error_{int(datetime.now(UTC).timestamp() * 1000)}_{hash(str(error)) % 10000}"

        # Capture system state
        system_state = await self._capture_system_state()

        # Create error context
        context = ErrorContext(
            error_id=error_id,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.now(UTC).isoformat(),
            request_data=request_data or {},
            user_context=user_context or {},
            system_state=system_state,
            stack_trace=traceback.format_exc(),
            environment=settings.environment.value,
            session_id=str(uuid.uuid4())
        )

        async with self.lock:
            self.error_contexts[error_id] = context

        # Analyze error pattern
        self.pattern_analyzer.analyze_error(context)

        # Log to Sentry for debugging
        if sentry_config.initialized:
            sentry_config.capture_message(
                f"Error context captured for debugging: {error_id}",
                level=ErrorSeverity.INFO,
                category=ErrorCategory.SYSTEM,
                tags={"debug_context": "captured", "error_id": error_id},
                extra_data=asdict(context)
            )

        logging.info(f"Error context captured: {error_id}")
        return error_id

    async def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state"""
        state = {
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": settings.environment.value,
            "version": settings.version,
            "memory_usage": self._get_memory_usage(),
            "cpu_usage": self._get_cpu_usage(),
            "database_status": await self._get_database_status(),
            "cache_status": await self._get_cache_status(),
            "active_requests": self._get_active_requests(),
            "recent_errors": self._get_recent_errors()
        }
        return state

    def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage information"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
        except ImportError:
            return {"percent": 0.0}

    def _get_cpu_usage(self) -> float:
        """Get CPU usage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0

    async def _get_database_status(self) -> Dict[str, Any]:
        """Get database status"""
        try:
            # This would connect to your actual database
            return {"status": "connected", "connections": 5, "max_connections": 20}
        except Exception:
            return {"status": "error", "error": "Connection failed"}

    async def _get_cache_status(self) -> Dict[str, Any]:
        """Get cache status"""
        try:
            # This would connect to your actual cache
            return {"status": "connected", "hit_rate": 0.85, "memory_usage": 0.3}
        except Exception:
            return {"status": "error", "error": "Connection failed"}

    def _get_active_requests(self) -> int:
        """Get number of active requests"""
        # This would track actual active requests
        return 0

    def _get_recent_errors(self) -> List[Dict[str, Any]]:
        """Get recent error information"""
        return []

    async def create_debug_session(self, error_id: str) -> str:
        """Create a debug session for an error"""
        async with self.lock:
            if error_id not in self.error_contexts:
                raise ValueError(f"Error context not found: {error_id}")

            error_context = self.error_contexts[error_id]
            session_id = f"debug_{uuid.uuid4()}"

            session = DebugSession(
                session_id=session_id,
                created_at=datetime.now(UTC).isoformat(),
                error_context=error_context,
                actions=[],
                findings=[],
                recommendations=[]
            )

            self.debug_sessions[session_id] = session

            # Initial analysis
            await self._analyze_error_in_session(session_id)

            logging.info(f"Debug session created: {session_id}")
            return session_id

    async def _analyze_error_in_session(self, session_id: str) -> None:
        """Analyze error in debug session"""
        async with self.lock:
            session = self.debug_sessions.get(session_id)
            if not session:
                return

        try:
            # Analyze error type and message
            analysis = await self._analyze_error_type(session.error_context)

            # Check for similar errors
            similar_errors = self.pattern_analyzer.find_similar_errors(session.error_context)

            # Generate recommendations
            recommendations = await self._generate_recommendations(session.error_context, similar_errors)

            async with self.lock:
                session.findings.extend(analysis["findings"])
                session.recommendations.extend(recommendations)

        except Exception as e:
            logging.error(f"Error analyzing debug session {session_id}: {e}")

    async def _analyze_error_type(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Analyze specific error type"""
        findings = []

        error_type = error_context.error_type.lower()
        error_message = error_context.error_message.lower()

        # Common error patterns
        if "timeout" in error_type or "timeout" in error_message:
            findings.append("Timeout error detected - check network connectivity and service responsiveness")
        elif "connection" in error_type or "connection" in error_message:
            findings.append("Connection error detected - verify database/service availability")
        elif "authentication" in error_type or "unauthorized" in error_message:
            findings.append("Authentication error - check token validity and permissions")
        elif "validation" in error_type or "invalid" in error_message:
            findings.append("Validation error - check input data format and constraints")
        elif "not found" in error_message or "404" in error_message:
            findings.append("Resource not found - check resource existence and permissions")

        return {"findings": findings}

    async def _generate_recommendations(self, error_context: ErrorContext, similar_errors: List[str]) -> List[str]:
        """Generate debugging recommendations"""
        recommendations = []

        # Basic recommendations based on error type
        error_type = error_context.error_type

        if error_type in ["ValueError", "TypeError"]:
            recommendations.append("Validate input data types and ranges")
        elif error_type in ["ConnectionError", "TimeoutError"]:
            recommendations.append("Implement retry logic with exponential backoff")
        elif error_type in ["AuthenticationError"]:
            recommendations.append("Refresh authentication tokens and check permissions")
        elif error_type in ["DatabaseError"]:
            recommendations.append("Check database connection and query optimization")

        # Pattern-based recommendations
        if len(similar_errors) > 5:
            recommendations.append(f"Recurring error pattern detected - {len(similar_errors)} similar errors found")

        # System state recommendations
        if error_context.system_state.get("memory_usage", {}).get("percent", 0) > 90:
            recommendations.append("High memory usage detected - optimize memory usage")

        return recommendations

    async def replay_request(self, session_id: str, modifications: Dict[str, Any] = None) -> Dict[str, Any]:
        """Replay request with optional modifications"""
        async with self.lock:
            session = self.debug_sessions.get(session_id)
            if not session:
                raise ValueError(f"Debug session not found: {session_id}")

        # Create replay context
        original_request = session.error_context.request_data.copy()
        modified_request = original_request.copy()

        # Apply modifications
        if modifications:
            modified_request.update(modifications)

        replay_id = str(uuid.uuid4())
        replay_result = {
            "replay_id": replay_id,
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "original_request": original_request,
            "modified_request": modified_request,
            "modifications": modifications or {},
            "result": None,
            "error": None,
            "execution_time": None
        }

        try:
            # Replay the request (this would be implemented based on your application logic)
            start_time = datetime.now(UTC)
            result = await self._execute_replay(modified_request, session.error_context)
            end_time = datetime.now(UTC)

            replay_result.update({
                "result": result,
                "execution_time": (end_time - start_time).total_seconds(),
                "status": "success"
            })

            # Add to session actions
            action = {
                "type": "replay_request",
                "timestamp": datetime.now(UTC).isoformat(),
                "replay_id": replay_id,
                "modifications": modifications or {},
                "result": "success",
                "execution_time": replay_result["execution_time"]
            }

        except Exception as e:
            replay_result.update({
                "error": str(e),
                "stack_trace": traceback.format_exc(),
                "status": "error"
            })

            action = {
                "type": "replay_request",
                "timestamp": datetime.now(UTC).isoformat(),
                "replay_id": replay_id,
                "modifications": modifications or {},
                "result": "failed",
                "error": str(e)
            }

        # Store replay result
        self.replay_history.append(replay_result)

        # Add to session
        async with self.lock:
            session.actions.append(action)

        return replay_result

    async def _execute_replay(self, request_data: Dict[str, Any], error_context: ErrorContext) -> Dict[str, Any]:
        """Execute replay request (mock implementation)"""
        # This is a mock implementation - in production, you'd actually replay the request
        await asyncio.sleep(0.1)  # Simulate processing time

        # Simulate different outcomes based on error type
        if "timeout" in error_context.error_type.lower():
            await asyncio.sleep(2)  # Simulate timeout
            raise TimeoutError("Request timeout during replay")

        return {"status": "success", "data": "Replay completed successfully"}

    async def simulate_error(self, session_id: str, error_type: str, error_message: str) -> Dict[str, Any]:
        """Simulate an error condition"""
        async with self.lock:
            session = self.debug_sessions.get(session_id)
            if not session:
                raise ValueError(f"Debug session not found: {session_id}")

        simulation_id = str(uuid.uuid4())
        simulation_result = {
            "simulation_id": simulation_id,
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "result": None,
            "error": None
        }

        try:
            # Simulate the error
            if error_type == "ValueError":
                raise ValueError(error_message)
            elif error_type == "ConnectionError":
                raise ConnectionError(error_message)
            elif error_type == "TimeoutError":
                raise TimeoutError(error_message)
            else:
                raise Exception(error_message)

        except Exception as e:
            simulation_result.update({
                "error": str(e),
                "stack_trace": traceback.format_exc(),
                "result": "error_simulated"
            })

            # Add to session actions
            action = {
                "type": "simulate_error",
                "timestamp": datetime.now(UTC).isoformat(),
                "simulation_id": simulation_id,
                "error_type": error_type,
                "error_message": error_message,
                "result": "simulated"
            }

            async with self.lock:
                session.actions.append(action)

        return simulation_result

    async def inspect_state(self, session_id: str, component: str = None) -> Dict[str, Any]:
        """Inspect system state"""
        async with self.lock:
            session = self.debug_sessions.get(session_id)
            if not session:
                raise ValueError(f"Debug session not found: {session_id}")

        inspection_id = str(uuid.uuid4())
        current_state = await self._capture_system_state()

        inspection_result = {
            "inspection_id": inspection_id,
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "component": component,
            "state": current_state,
            "comparison": self._compare_states(session.error_context.system_state, current_state)
        }

        # Add to session actions
        action = {
            "type": "inspect_state",
            "timestamp": datetime.now(UTC).isoformat(),
            "inspection_id": inspection_id,
            "component": component,
            "state_comparison": inspection_result["comparison"]
        }

        async with self.lock:
            session.actions.append(action)

        return inspection_result

    def _compare_states(self, original_state: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Compare system states"""
        comparison = {
            "timestamp_diff": None,
            "memory_change": None,
            "cpu_change": None,
            "database_status_change": None,
            "cache_status_change": None
        }

        try:
            # Compare memory usage
            if "memory_usage" in original_state and "memory_usage" in current_state:
                original_mem = original_state["memory_usage"].get("percent", 0)
                current_mem = current_state["memory_usage"].get("percent", 0)
                comparison["memory_change"] = current_mem - original_mem

            # Compare CPU usage
            if "cpu_usage" in original_state and "cpu_usage" in current_state:
                comparison["cpu_change"] = current_state["cpu_usage"] - original_state["cpu_usage"]

            # Compare database status
            if "database_status" in original_state and "database_status" in current_state:
                comparison["database_status_change"] = (
                    original_state["database_status"]["status"] != current_state["database_status"]["status"]
                )

            # Compare cache status
            if "cache_status" in original_state and "cache_status" in current_state:
                comparison["cache_status_change"] = (
                    original_state["cache_status"]["status"] != current_state["cache_status"]["status"]
                )

        except Exception as e:
            logging.error(f"Error comparing states: {e}")

        return comparison

    async def get_debug_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get debug session information"""
        async with self.lock:
            session = self.debug_sessions.get(session_id)
            if not session:
                return None

            return asdict(session)

    async def list_debug_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent debug sessions"""
        async with self.lock:
            sessions = list(self.debug_sessions.values())

        # Sort by creation time and limit
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        return [asdict(session) for session in sessions[:limit]]

    async def close_debug_session(self, session_id: str) -> bool:
        """Close debug session"""
        async with self.lock:
            if session_id not in self.debug_sessions:
                return False

            session = self.debug_sessions[session_id]
            session.status = "closed"

        logging.info(f"Debug session closed: {session_id}")
        return True

    async def export_debug_session(self, session_id: str) -> Dict[str, Any]:
        """Export debug session data"""
        session = await self.get_debug_session(session_id)
        if not session:
            raise ValueError(f"Debug session not found: {session_id}")

        # Get related replay history
        related_replays = [r for r in self.replay_history if r.get("session_id") == session_id]

        export_data = {
            "session": session,
            "related_replays": related_replays,
            "export_timestamp": datetime.now(UTC).isoformat(),
            "version": settings.version
        }

        return export_data


class ErrorPatternAnalyzer:
    """Analyze error patterns and provide insights"""

    def __init__(self):
        self.error_patterns: Dict[str, List[ErrorContext]] = {}
        self.pattern_signatures: Dict[str, str] = {}

    def analyze_error(self, error_context: ErrorContext) -> None:
        """Analyze error and update patterns"""
        # Create pattern signature
        signature = self._create_pattern_signature(error_context)

        # Group by signature
        if signature not in self.error_patterns:
            self.error_patterns[signature] = []

        self.error_patterns[signature].append(error_context)
        self.pattern_signatures[error_context.error_id] = signature

    def _create_pattern_signature(self, error_context: ErrorContext) -> str:
        """Create signature for pattern matching"""
        # Simple signature based on error type and key request attributes
        signature_parts = [
            error_context.error_type,
            error_context.environment,
            str(error_context.request_data.get("method", "")),
            str(error_context.request_data.get("path", ""))
        ]

        return hashlib.md5("|".join(signature_parts).encode()).hexdigest()

    def find_similar_errors(self, error_context: ErrorContext, threshold: int = 5) -> List[str]:
        """Find similar errors"""
        signature = self._create_pattern_signature(error_context)
        similar_errors = []

        if signature in self.error_patterns:
            for context in self.error_patterns[signature]:
                if context.error_id != error_context.error_id:
                    similar_errors.append(context.error_id)

        return similar_errors[:threshold]

    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get error pattern summary"""
        summary = {
            "total_patterns": len(self.error_patterns),
            "total_errors": sum(len(patterns) for patterns in self.error_patterns.values()),
            "top_patterns": []
        }

        # Get top patterns by frequency
        pattern_counts = [(signature, len(patterns)) for signature, patterns in self.error_patterns.items()]
        pattern_counts.sort(key=lambda x: x[1], reverse=True)

        for signature, count in pattern_counts[:10]:
            if self.error_patterns[signature]:
                sample_error = self.error_patterns[signature][0]
                summary["top_patterns"].append({
                    "signature": signature,
                    "count": count,
                    "error_type": sample_error.error_type,
                    "environment": sample_error.environment,
                    "recent_occurrence": max(ctx.timestamp for ctx in self.error_patterns[signature])
                })

        return summary


# Global error debugger instance
error_debugger = ErrorDebugger()