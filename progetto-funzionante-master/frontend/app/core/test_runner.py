"""
Test Runner and Validation Interface

This module provides a comprehensive test runner interface for the AI Cash Revolution Trading API,
including automated test execution, real-time monitoring, and interactive validation tools.

Features:
- Automated test execution with multiple test suites
- Real-time test monitoring and progress tracking
- Interactive test configuration and execution
- Test result visualization and reporting
- CI/CD integration capabilities
- Scheduled test execution
- Test data management
- Performance monitoring
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import yaml
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Import existing modules
from app.core.openapi_validation import OpenAPIValidator, TestReport, TestCategory
from app.core.api_testing import (
    APITestFramework, TestSuite, TestResult, TestType, LoadTestConfig
)

logger = logging.getLogger(__name__)

class TestExecutionMode(Enum):
    """Test execution modes"""
    MANUAL = "manual"
    AUTOMATED = "automated"
    SCHEDULED = "scheduled"
    CONTINUOUS = "continuous"

class TestRunnerConfig(BaseModel):
    """Test runner configuration"""
    execution_mode: TestExecutionMode = TestExecutionMode.MANUAL
    test_suites: List[str] = Field(default_factory=list)
    max_execution_time: int = Field(default=3600, ge=60, le=86400)
    parallel_execution: bool = True
    stop_on_failure: bool = False
    generate_report: bool = True
    notify_on_completion: bool = False
    retry_failed_tests: bool = False
    max_retries: int = Field(default=3, ge=0, le=10)

class TestExecutionStatus(BaseModel):
    """Test execution status"""
    execution_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    total_tests: int = 0
    completed_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    current_test: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None

class TestScheduler:
    """Test scheduler for automated and scheduled testing"""

    def __init__(self):
        self.scheduled_tests = {}
        self.running_tasks = {}

    async def schedule_test(
        self,
        name: str,
        config: TestRunnerConfig,
        schedule: str,
        app: FastAPI
    ) -> str:
        """Schedule a test to run at specified intervals"""
        schedule_id = str(uuid.uuid4())
        self.scheduled_tests[schedule_id] = {
            "name": name,
            "config": config,
            "schedule": schedule,
            "last_run": None,
            "next_run": self._calculate_next_run(schedule),
            "enabled": True
        }

        # Start background task for scheduled execution
        task = asyncio.create_task(self._run_scheduled_test(schedule_id, app))
        self.running_tasks[schedule_id] = task

        return schedule_id

    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time based on schedule"""
        # Simple schedule parsing (can be enhanced with cron-like syntax)
        if schedule.startswith("every "):
            parts = schedule.split()
            if len(parts) >= 3:
                interval = int(parts[1])
                unit = parts[2]

                if unit.startswith("minute"):
                    return datetime.utcnow() + timedelta(minutes=interval)
                elif unit.startswith("hour"):
                    return datetime.utcnow() + timedelta(hours=interval)
                elif unit.startswith("day"):
                    return datetime.utcnow() + timedelta(days=interval)

        # Default: run every hour
        return datetime.utcnow() + timedelta(hours=1)

    async def _run_scheduled_test(self, schedule_id: str, app: FastAPI):
        """Run scheduled test"""
        while schedule_id in self.scheduled_tests:
            scheduled_test = self.scheduled_tests[schedule_id]

            if not scheduled_test["enabled"]:
                await asyncio.sleep(60)  # Check every minute
                continue

            # Check if it's time to run
            if datetime.utcnow() >= scheduled_test["next_run"]:
                try:
                    # Run the test
                    runner = TestRunner(app)
                    await runner.run_tests(scheduled_test["config"])

                    # Update schedule
                    scheduled_test["last_run"] = datetime.utcnow()
                    scheduled_test["next_run"] = self._calculate_next_run(scheduled_test["schedule"])

                except Exception as e:
                    logger.error(f"Scheduled test {schedule_id} failed: {str(e)}")

            await asyncio.sleep(60)  # Check every minute

    def stop_scheduled_test(self, schedule_id: str):
        """Stop a scheduled test"""
        if schedule_id in self.scheduled_tests:
            self.scheduled_tests[schedule_id]["enabled"] = False

        if schedule_id in self.running_tasks:
            self.running_tasks[schedule_id].cancel()
            del self.running_tasks[schedule_id]

class TestRunner:
    """Main test runner interface"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.framework = APITestFramework(app)
        self.validator = OpenAPIValidator(app)
        self.scheduler = TestScheduler()
        self.executions = {}
        self.websocket_connections = []

    async def run_tests(self, config: TestRunnerConfig) -> str:
        """Run tests with specified configuration"""
        execution_id = str(uuid.uuid4())

        # Initialize execution status
        self.executions[execution_id] = TestExecutionStatus(
            execution_id=execution_id,
            status="running",
            start_time=datetime.utcnow()
        )

        # Run tests in background
        asyncio.create_task(self._execute_tests(execution_id, config))

        return execution_id

    async def _execute_tests(self, execution_id: str, config: TestRunnerConfig):
        """Execute tests with configuration"""
        try:
            status = self.executions[execution_id]
            results = {}

            # Update progress
            await self._update_progress(execution_id, "Starting test execution", 0.1)

            # Run OpenAPI validation
            if not config.test_suites or "openapi" in config.test_suites:
                await self._update_progress(execution_id, "Running OpenAPI validation", 0.2)
                openapi_report = await self.validator.run_comprehensive_validation()
                results["openapi"] = openapi_report.dict()

            # Run comprehensive tests
            if not config.test_suites or "comprehensive" in config.test_suites:
                await self._update_progress(execution_id, "Running comprehensive tests", 0.5)
                comprehensive_results = await self.framework.run_comprehensive_tests()
                results["comprehensive"] = comprehensive_results

            # Run specific test suites
            for suite_name in config.test_suites:
                if suite_name in ["unit", "integration", "security", "performance", "load"]:
                    await self._update_progress(execution_id, f"Running {suite_name} tests", 0.7)
                    suite_method = getattr(self.framework, f"run_{suite_name}_tests")
                    suite = await suite_method()
                    results[suite_name] = suite.dict()

            # Generate report
            if config.generate_report:
                await self._update_progress(execution_id, "Generating test report", 0.9)
                report = await self._generate_test_report(execution_id, results)
                results["report"] = report

            # Update final status
            status.status = "completed"
            status.end_time = datetime.utcnow()
            status.duration = (status.end_time - status.start_time).total_seconds()
            status.progress = 1.0

            # Notify websocket clients
            await self._notify_websocket_clients(execution_id, "completed", results)

        except Exception as e:
            status = self.executions[execution_id]
            status.status = "failed"
            status.end_time = datetime.utcnow()
            status.duration = (status.end_time - status.start_time).total_seconds()
            status.error_message = str(e)

            logger.error(f"Test execution {execution_id} failed: {str(e)}")

            # Notify websocket clients
            await self._notify_websocket_clients(execution_id, "failed", {"error": str(e)})

    async def _update_progress(self, execution_id: str, message: str, progress: float):
        """Update execution progress"""
        if execution_id in self.executions:
            status = self.executions[execution_id]
            status.current_test = message
            status.progress = progress
            status.completed_tests = int(progress * status.total_tests)

        # Notify websocket clients
        await self._notify_websocket_clients(execution_id, "progress", {"message": message, "progress": progress})

    async def _notify_websocket_clients(self, execution_id: str, event_type: str, data: Any):
        """Notify connected websocket clients"""
        message = {
            "execution_id": execution_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        # Send to all connected clients
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(message, cls=PlotlyJSONEncoder))
            except:
                disconnected.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)

    async def _generate_test_report(self, execution_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {},
            "details": results,
            "visualizations": {}
        }

        # Generate summary statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for suite_name, suite_data in results.items():
            if suite_name != "openapi" and suite_name != "report":
                if isinstance(suite_data, dict) and "total_tests" in suite_data:
                    total_tests += suite_data["total_tests"]
                    passed_tests += suite_data["passed_tests"]
                    failed_tests += suite_data["failed_tests"]

        report["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "execution_duration": self.executions[execution_id].duration
        }

        # Generate visualizations
        report["visualizations"] = await self._generate_visualizations(results)

        return report

    async def _generate_visualizations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test result visualizations"""
        visualizations = {}

        try:
            # Test results pie chart
            total_passed = sum(suite.get("passed_tests", 0) for suite in results.values() if isinstance(suite, dict))
            total_failed = sum(suite.get("failed_tests", 0) for suite in results.values() if isinstance(suite, dict))

            if total_passed > 0 or total_failed > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=["Passed", "Failed"],
                    values=[total_passed, total_failed],
                    marker=dict(colors=["#2ecc71", "#e74c3c"])
                )])
                fig.update_layout(title="Test Results Overview")
                visualizations["results_pie_chart"] = fig.to_dict()

            # Test suite performance bar chart
            suite_names = []
            suite_scores = []

            for suite_name, suite_data in results.items():
                if suite_name not in ["openapi", "report"] and isinstance(suite_data, dict):
                    if "success_rate" in suite_data:
                        suite_names.append(suite_name.title())
                        suite_scores.append(suite_data["success_rate"])

            if suite_names and suite_scores:
                fig = go.Figure(data=[go.Bar(
                    x=suite_names,
                    y=suite_scores,
                    marker_color=["#3498db", "#9b59b6", "#f39c12", "#e67e22", "#1abc9c"]
                )])
                fig.update_layout(
                    title="Test Suite Performance",
                    xaxis_title="Test Suite",
                    yaxis_title="Success Rate (%)",
                    yaxis=dict(range=[0, 100])
                )
                visualizations["suite_performance"] = fig.to_dict()

            # OpenAPI compliance gauge
            if "openapi" in results and isinstance(results["openapi"], dict):
                compliance_score = results["openapi"].get("openapi_compliance_score", 0)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=compliance_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "OpenAPI Compliance Score"},
                    gauge={'axis': {'range': [None, 100]},
                           'bar': {'color': "darkblue"},
                           'steps': [
                               {'range': [0, 50], 'color': "lightgray"},
                               {'range': [50, 80], 'color': "gray"}],
                           'threshold': {'line': {'color': "red", 'width': 4},
                                       'thickness': 0.75, 'value': 90}}
                ))
                visualizations["compliance_gauge"] = fig.to_dict()

        except Exception as e:
            logger.error(f"Failed to generate visualizations: {str(e)}")
            visualizations["error"] = str(e)

        return visualizations

    def get_execution_status(self, execution_id: str) -> Optional[TestExecutionStatus]:
        """Get execution status"""
        return self.executions.get(execution_id)

    def get_all_executions(self) -> List[TestExecutionStatus]:
        """Get all execution statuses"""
        return list(self.executions.values())

    async def connect_websocket(self, websocket: WebSocket):
        """Connect websocket for real-time updates"""
        await websocket.accept()
        self.websocket_connections.append(websocket)

    def disconnect_websocket(self, websocket: WebSocket):
        """Disconnect websocket"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)

# Router for test runner endpoints
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

test_runner_router = APIRouter(prefix="/test-runner", tags=["test-runner"])

# Global test runner instance
test_runner = None

def get_test_runner() -> TestRunner:
    """Get test runner instance"""
    global test_runner
    if test_runner is None:
        from main import app
        test_runner = TestRunner(app)
    return test_runner

@test_runner_router.post("/execute")
async def execute_tests(
    config: TestRunnerConfig,
    runner: TestRunner = Depends(get_test_runner)
) -> Dict[str, str]:
    """Execute tests with specified configuration"""
    execution_id = await runner.run_tests(config)
    return {"execution_id": execution_id, "status": "started"}

@test_runner_router.get("/status/{execution_id}")
async def get_execution_status(
    execution_id: str,
    runner: TestRunner = Depends(get_test_runner)
) -> TestExecutionStatus:
    """Get execution status"""
    status = runner.get_execution_status(execution_id)
    if not status:
        raise HTTPException(status_code=404, detail="Execution not found")
    return status

@test_runner_router.get("/executions")
async def get_all_executions(
    runner: TestRunner = Depends(get_test_runner)
) -> List[TestExecutionStatus]:
    """Get all execution statuses"""
    return runner.get_all_executions()

@test_runner_router.get("/report/{execution_id}")
async def get_test_report(
    execution_id: str,
    runner: TestRunner = Depends(get_test_runner)
) -> Dict[str, Any]:
    """Get test report for execution"""
    status = runner.get_execution_status(execution_id)
    if not status:
        raise HTTPException(status_code=404, detail="Execution not found")

    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Execution not completed")

    # This would retrieve the stored report
    return {"execution_id": execution_id, "status": "completed"}

@test_runner_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    runner = get_test_runner()
    await runner.connect_websocket(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        runner.disconnect_websocket(websocket)

@test_runner_router.get("/dashboard", response_class=HTMLResponse)
async def test_dashboard():
    """Test dashboard interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Test Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
            .progress { width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; }
            .progress-bar { height: 100%; background-color: #4CAF50; border-radius: 10px; }
            .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background-color: #0056b3; }
            .status { padding: 5px 10px; border-radius: 4px; display: inline-block; }
            .status.running { background-color: #ffc107; }
            .status.completed { background-color: #28a745; }
            .status.failed { background-color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>API Test Dashboard</h1>

            <div class="card">
                <h2>Test Execution</h2>
                <button class="btn" onclick="runTests()">Run Tests</button>
                <div id="execution-status"></div>
                <div class="progress">
                    <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
                </div>
                <div id="current-test"></div>
            </div>

            <div class="card">
                <h2>Test Results</h2>
                <div id="test-results"></div>
                <div id="visualizations"></div>
            </div>

            <div class="card">
                <h2>Recent Executions</h2>
                <div id="recent-executions"></div>
            </div>
        </div>

        <script>
            let socket;
            let currentExecution = null;

            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/test-runner/ws`;
                socket = new WebSocket(wsUrl);

                socket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };

                socket.onclose = function() {
                    setTimeout(connectWebSocket, 1000);
                };
            }

            function handleWebSocketMessage(data) {
                if (data.event_type === 'progress') {
                    updateProgress(data.data.progress, data.data.message);
                } else if (data.event_type === 'completed') {
                    showResults(data.data);
                } else if (data.event_type === 'failed') {
                    showError(data.data);
                }
            }

            function updateProgress(progress, message) {
                document.getElementById('progress-bar').style.width = (progress * 100) + '%';
                document.getElementById('current-test').textContent = message;
            }

            function showResults(results) {
                document.getElementById('execution-status').innerHTML =
                    '<span class="status completed">Completed</span>';

                // Display results
                const resultsDiv = document.getElementById('test-results');
                resultsDiv.innerHTML = '<h3>Test Results</h3>';

                if (results.report && results.report.summary) {
                    const summary = results.report.summary;
                    resultsDiv.innerHTML += `
                        <p>Total Tests: ${summary.total_tests}</p>
                        <p>Passed: ${summary.passed_tests}</p>
                        <p>Failed: ${summary.failed_tests}</p>
                        <p>Success Rate: ${summary.success_rate.toFixed(2)}%</p>
                        <p>Duration: ${summary.execution_duration.toFixed(2)}s</p>
                    `;
                }

                // Display visualizations
                if (results.report && results.report.visualizations) {
                    const vizDiv = document.getElementById('visualizations');
                    vizDiv.innerHTML = '<h3>Visualizations</h3>';

                    for (const [key, viz] of Object.entries(results.report.visualizations)) {
                        if (key !== 'error') {
                            const containerId = `viz-${key}`;
                            vizDiv.innerHTML += `<div id="${containerId}"></div>`;
                            Plotly.newPlot(containerId, viz.data, viz.layout);
                        }
                    }
                }
            }

            function showError(error) {
                document.getElementById('execution-status').innerHTML =
                    '<span class="status failed">Failed</span>';
                document.getElementById('current-test').textContent =
                    'Error: ' + (error.error || 'Unknown error');
            }

            async function runTests() {
                const config = {
                    execution_mode: 'manual',
                    test_suites: ['openapi', 'comprehensive'],
                    max_execution_time: 3600,
                    parallel_execution: true,
                    stop_on_failure: false,
                    generate_report: true
                };

                try {
                    const response = await fetch('/test-runner/execute', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(config)
                    });

                    const result = await response.json();
                    currentExecution = result.execution_id;

                    document.getElementById('execution-status').innerHTML =
                        '<span class="status running">Running</span>';

                    // Poll for status
                    pollExecutionStatus(result.execution_id);
                } catch (error) {
                    console.error('Failed to start tests:', error);
                }
            }

            async function pollExecutionStatus(executionId) {
                try {
                    const response = await fetch(`/test-runner/status/${executionId}`);
                    const status = await response.json();

                    if (status.status === 'completed') {
                        const reportResponse = await fetch(`/test-runner/report/${executionId}`);
                        const report = await reportResponse.json();
                        showResults(report);
                    } else if (status.status === 'failed') {
                        showError({error: status.error_message});
                    }
                } catch (error) {
                    console.error('Error polling status:', error);
                }
            }

            // Initialize
            connectWebSocket();
        </script>
    </body>
    </html>
    """

# Export test runner utilities
__all__ = [
    "TestRunner",
    "TestRunnerConfig",
    "TestExecutionStatus",
    "TestScheduler",
    "TestExecutionMode",
    "test_runner_router"
]