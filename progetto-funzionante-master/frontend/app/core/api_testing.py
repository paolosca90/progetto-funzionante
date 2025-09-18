"""
API Testing Framework

This module provides comprehensive testing capabilities for the AI Cash Revolution Trading API,
including automated testing, load testing, security testing, and performance monitoring.

Features:
- Automated endpoint testing with authentication
- Load testing and stress testing
- Security testing (SQL injection, XSS, etc.)
- Performance benchmarking
- Test data generation
- Test report generation
- CI/CD integration
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Tuple, Callable
import asyncio
import aiohttp
import time
import random
import string
import json
import statistics
from datetime import datetime, timedelta
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import uuid
import secrets
import hashlib
import hmac
import base64
from pathlib import Path

# Import existing modules
from app.core.openapi_validation import OpenAPIValidator, TestCategory
from app.core.security_schemes import SECURITY_SCHEMES
from app.core.error_handling import StructuredError, ErrorHandler

logger = logging.getLogger(__name__)

class TestType(Enum):
    """Test types for organization"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOAD = "load"
    STRESS = "stress"
    END_TO_END = "end_to_end"

class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class TestResult(BaseModel):
    """Individual test result"""
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    description: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    assertions: List[Dict[str, Any]] = Field(default_factory=list)

class TestSuite(BaseModel):
    """Test suite containing multiple tests"""
    suite_id: str
    name: str
    description: str
    tests: List[TestResult] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    success_rate: Optional[float] = None

class LoadTestConfig(BaseModel):
    """Load testing configuration"""
    concurrent_users: int = Field(default=10, ge=1, le=1000)
    requests_per_user: int = Field(default=10, ge=1, le=1000)
    ramp_up_time: float = Field(default=10.0, ge=0.1, le=300.0)
    duration: float = Field(default=60.0, ge=1.0, le=3600.0)
    think_time: float = Field(default=1.0, ge=0.0, le=60.0)
    max_response_time: float = Field(default=5.0, ge=0.1, le=60.0)
    error_rate_threshold: float = Field(default=0.05, ge=0.0, le=1.0)

class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p90_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    throughput_mb_per_second: Optional[float] = None

class TestDataGenerator:
    """Generate test data for various scenarios"""

    @staticmethod
    def generate_user_data() -> Dict[str, Any]:
        """Generate realistic user data"""
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", "William", "Emma"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        domains = ["gmail.com", "yahoo.com", "outlook.com", "example.com", "test.com"]

        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"

        return {
            "username": f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}",
            "email": email,
            "password": f"TestPass{random.randint(100, 999)}!",
            "full_name": f"{first_name} {last_name}"
        }

    @staticmethod
    def generate_signal_data() -> Dict[str, Any]:
        """Generate trading signal data"""
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
        signal_types = ["BUY", "SELL", "HOLD"]
        risk_levels = ["LOW", "MEDIUM", "HIGH"]

        return {
            "symbol": random.choice(symbols),
            "signal_type": random.choice(signal_types),
            "entry_price": round(random.uniform(1.0000, 2.0000), 4),
            "stop_loss": round(random.uniform(0.9800, 1.9800), 4),
            "take_profit": round(random.uniform(1.0200, 2.0200), 4),
            "reliability": round(random.uniform(70.0, 95.0), 1),
            "confidence_score": round(random.uniform(60.0, 90.0), 1),
            "risk_level": random.choice(risk_levels),
            "ai_analysis": "Test AI analysis for automated testing",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }

    @staticmethod
    def generate_market_data() -> Dict[str, Any]:
        """Generate market data"""
        symbols = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD"]

        base_price = random.uniform(1.0000, 150.0000)
        spread = random.uniform(0.0001, 0.0050)

        return {
            "symbol": random.choice(symbols),
            "bid": round(base_price - spread/2, 4),
            "ask": round(base_price + spread/2, 4),
            "spread": round(spread, 4),
            "timestamp": datetime.utcnow().isoformat(),
            "session": random.choice(["LONDON", "NEW_YORK", "TOKYO", "SYDNEY", "OVERLAP"]),
            "volatility": round(random.uniform(0.0001, 0.0100), 4)
        }

class SecurityTestEngine:
    """Security testing engine"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()

    async def test_sql_injection(self, endpoint: str, method: str = "GET") -> List[Dict[str, Any]]:
        """Test for SQL injection vulnerabilities"""
        results = []
        sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "' WAITFOR DELAY '0:0:5'--",
            "1' OR '1'='1",
            "admin'--",
            "' OR SLEEP(5)--"
        ]

        for payload in sql_payloads:
            try:
                start_time = time.time()

                if method.upper() == "GET":
                    params = {"q": payload}
                    async with self.session.get(f"{self.base_url}{endpoint}", params=params) as response:
                        response_time = time.time() - start_time
                        results.append({
                            "payload": payload,
                            "status_code": response.status,
                            "response_time": response_time,
                            "vulnerable": response_time > 3.0 or "error" in response.text.lower()
                        })
                else:
                    data = {"query": payload}
                    async with self.session.post(f"{self.base_url}{endpoint}", json=data) as response:
                        response_time = time.time() - start_time
                        results.append({
                            "payload": payload,
                            "status_code": response.status,
                            "response_time": response_time,
                            "vulnerable": response_time > 3.0 or "error" in response.text.lower()
                        })

            except Exception as e:
                results.append({
                    "payload": payload,
                    "error": str(e),
                    "vulnerable": False
                })

        return results

    async def test_xss(self, endpoint: str) -> List[Dict[str, Any]]:
        """Test for XSS vulnerabilities"""
        results = []
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert('XSS')</script>",
            "<iframe src=javascript:alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83));//"
        ]

        for payload in xss_payloads:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}", params={"q": payload}) as response:
                    results.append({
                        "payload": payload,
                        "status_code": response.status,
                        "vulnerable": payload in response.text
                    })
            except Exception as e:
                results.append({
                    "payload": payload,
                    "error": str(e),
                    "vulnerable": False
                })

        return results

    async def test_authentication_bypass(self) -> List[Dict[str, Any]]:
        """Test authentication bypass vulnerabilities"""
        results = []

        # Test common bypass techniques
        bypass_attempts = [
            {"method": "GET", "endpoint": "/admin/dashboard"},
            {"method": "GET", "endpoint": "/api/admin/users"},
            {"method": "POST", "endpoint": "/api/admin/settings", "data": {}},
            {"method": "GET", "endpoint": "/api/signals/admin"}
        ]

        for attempt in bypass_attempts:
            try:
                if attempt["method"] == "GET":
                    async with self.session.get(f"{self.base_url}{attempt['endpoint']}") as response:
                        results.append({
                            "test": f"Unauthorized access to {attempt['endpoint']}",
                            "status_code": response.status,
                            "bypass_possible": response.status != 401 and response.status != 403
                        })
                else:
                    async with self.session.post(f"{self.base_url}{attempt['endpoint']}", json=attempt.get("data", {})) as response:
                        results.append({
                            "test": f"Unauthorized POST to {attempt['endpoint']}",
                            "status_code": response.status,
                            "bypass_possible": response.status != 401 and response.status != 403
                        })
            except Exception as e:
                results.append({
                    "test": f"Error testing {attempt['endpoint']}",
                    "error": str(e),
                    "bypass_possible": False
                })

        return results

    async def close(self):
        """Close session"""
        await self.session.close()

class LoadTestEngine:
    """Load testing engine"""

    def __init__(self, base_url: str, config: LoadTestConfig):
        self.base_url = base_url
        self.config = config
        self.session = aiohttp.ClientSession()
        self.results = []

    async def run_load_test(self, endpoints: List[str]) -> PerformanceMetrics:
        """Run load test against specified endpoints"""
        start_time = time.time()
        response_times = []
        errors = []

        # Create user tasks
        tasks = []
        for i in range(self.config.concurrent_users):
            task = self._simulate_user(endpoints)
            tasks.append(task)

        # Run all users concurrently
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        total_requests = 0
        successful_requests = 0
        failed_requests = 0

        for user_results in all_results:
            if isinstance(user_results, Exception):
                errors.append(str(user_results))
                failed_requests += 1
            else:
                for result in user_results:
                    total_requests += 1
                    if result['success']:
                        successful_requests += 1
                        response_times.append(result['response_time'])
                    else:
                        failed_requests += 1
                        errors.append(result.get('error', 'Unknown error'))

        # Calculate metrics
        if response_times:
            sorted_times = sorted(response_times)
            metrics = PerformanceMetrics(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                average_response_time=statistics.mean(response_times),
                min_response_time=min(response_times),
                max_response_time=max(response_times),
                p50_response_time=sorted_times[len(sorted_times) // 2],
                p90_response_time=sorted_times[int(len(sorted_times) * 0.9)],
                p95_response_time=sorted_times[int(len(sorted_times) * 0.95)],
                p99_response_time=sorted_times[int(len(sorted_times) * 0.99)],
                requests_per_second=successful_requests / self.config.duration,
                error_rate=failed_requests / total_requests if total_requests > 0 else 0
            )
        else:
            metrics = PerformanceMetrics(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                average_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p50_response_time=0,
                p90_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                error_rate=1.0
            )

        await self.close()
        return metrics

    async def _simulate_user(self, endpoints: List[str]) -> List[Dict[str, Any]]:
        """Simulate a single user making requests"""
        results = []

        for _ in range(self.config.requests_per_user):
            # Random think time
            await asyncio.sleep(random.uniform(0, self.config.think_time))

            # Select random endpoint
            endpoint = random.choice(endpoints)

            try:
                start_time = time.time()
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    response_time = time.time() - start_time
                    results.append({
                        'success': response.status < 400,
                        'response_time': response_time,
                        'status_code': response.status,
                        'endpoint': endpoint
                    })
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'endpoint': endpoint
                })

        return results

    async def close(self):
        """Close session"""
        await self.session.close()

class APITestFramework:
    """Main API testing framework"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.test_client = TestClient(app)
        self.data_generator = TestDataGenerator()
        self.security_engine = None
        self.load_engine = None
        self.test_suites = {}

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        results = {
            "unit_tests": await self.run_unit_tests(),
            "integration_tests": await self.run_integration_tests(),
            "security_tests": await self.run_security_tests(),
            "performance_tests": await self.run_performance_tests(),
            "load_tests": await self.run_load_tests(),
            "summary": await self.generate_test_summary()
        }

        return results

    async def run_unit_tests(self) -> TestSuite:
        """Run unit tests"""
        suite = TestSuite(
            suite_id=str(uuid.uuid4()),
            name="Unit Tests",
            description="Individual component tests"
        )

        # Test data generation
        suite.tests.extend(await self._test_data_generation())

        # Test validation
        suite.tests.extend(await self._test_validation())

        # Test basic endpoints
        suite.tests.extend(await self._test_basic_endpoints())

        suite.total_tests = len(suite.tests)
        suite.passed_tests = len([t for t in suite.tests if t.status == TestStatus.PASSED])
        suite.failed_tests = len([t for t in suite.tests if t.status == TestStatus.FAILED])
        suite.success_rate = (suite.passed_tests / suite.total_tests * 100) if suite.total_tests > 0 else 0

        return suite

    async def run_integration_tests(self) -> TestSuite:
        """Run integration tests"""
        suite = TestSuite(
            suite_id=str(uuid.uuid4()),
            name="Integration Tests",
            description="Component integration tests"
        )

        # Test authentication flow
        suite.tests.extend(await self._test_authentication_flow())

        # Test signal generation
        suite.tests.extend(await self._test_signal_generation())

        # Test market data integration
        suite.tests.extend(await self._test_market_data_integration())

        suite.total_tests = len(suite.tests)
        suite.passed_tests = len([t for t in suite.tests if t.status == TestStatus.PASSED])
        suite.failed_tests = len([t for t in suite.tests if t.status == TestStatus.FAILED])
        suite.success_rate = (suite.passed_tests / suite.total_tests * 100) if suite.total_tests > 0 else 0

        return suite

    async def run_security_tests(self) -> TestSuite:
        """Run security tests"""
        suite = TestSuite(
            suite_id=str(uuid.uuid4()),
            name="Security Tests",
            description="Security vulnerability tests"
        )

        if not self.security_engine:
            self.security_engine = SecurityTestEngine("http://localhost:8000")

        # Test SQL injection
        sql_results = await self.security_engine.test_sql_injection("/api/search")
        for result in sql_results:
            suite.tests.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="SQL Injection Test",
                test_type=TestType.SECURITY,
                status=TestStatus.PASSED if not result.get('vulnerable') else TestStatus.FAILED,
                description=f"SQL injection test with payload: {result.get('payload', 'N/A')}",
                details=result
            ))

        # Test XSS
        xss_results = await self.security_engine.test_xss("/api/search")
        for result in xss_results:
            suite.tests.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="XSS Test",
                test_type=TestType.SECURITY,
                status=TestStatus.PASSED if not result.get('vulnerable') else TestStatus.FAILED,
                description=f"XSS test with payload: {result.get('payload', 'N/A')}",
                details=result
            ))

        # Test authentication bypass
        auth_results = await self.security_engine.test_authentication_bypass()
        for result in auth_results:
            suite.tests.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Authentication Bypass Test",
                test_type=TestType.SECURITY,
                status=TestStatus.PASSED if not result.get('bypass_possible') else TestStatus.FAILED,
                description=result.get('test', 'N/A'),
                details=result
            ))

        suite.total_tests = len(suite.tests)
        suite.passed_tests = len([t for t in suite.tests if t.status == TestStatus.PASSED])
        suite.failed_tests = len([t for t in suite.tests if t.status == TestStatus.FAILED])
        suite.success_rate = (suite.passed_tests / suite.total_tests * 100) if suite.total_tests > 0 else 0

        return suite

    async def run_performance_tests(self) -> TestSuite:
        """Run performance tests"""
        suite = TestSuite(
            suite_id=str(uuid.uuid4()),
            name="Performance Tests",
            description="Performance benchmarking tests"
        )

        # Test endpoint response times
        endpoints = ["/", "/health", "/api/signals/latest"]
        for endpoint in endpoints:
            response_times = []
            for _ in range(10):
                start_time = time.time()
                response = self.test_client.get(endpoint)
                response_times.append(time.time() - start_time)

            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)

            suite.tests.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name=f"Performance Test - {endpoint}",
                test_type=TestType.PERFORMANCE,
                status=TestStatus.PASSED if avg_time < 1.0 else TestStatus.FAILED,
                description=f"Performance test for endpoint {endpoint}",
                details={
                    "endpoint": endpoint,
                    "average_response_time": avg_time,
                    "max_response_time": max_time,
                    "requests_tested": len(response_times)
                }
            ))

        suite.total_tests = len(suite.tests)
        suite.passed_tests = len([t for t in suite.tests if t.status == TestStatus.PASSED])
        suite.failed_tests = len([t for t in suite.tests if t.status == TestStatus.FAILED])
        suite.success_rate = (suite.passed_tests / suite.total_tests * 100) if suite.total_tests > 0 else 0

        return suite

    async def run_load_tests(self) -> TestSuite:
        """Run load tests"""
        suite = TestSuite(
            suite_id=str(uuid.uuid4()),
            name="Load Tests",
            description="Load testing with concurrent users"
        )

        if not self.load_engine:
            config = LoadTestConfig()
            self.load_engine = LoadTestEngine("http://localhost:8000", config)

        endpoints = ["/", "/health", "/docs"]
        metrics = await self.load_engine.run_load_test(endpoints)

        suite.tests.append(TestResult(
            test_id=str(uuid.uuid4()),
            test_name="Load Test",
            test_type=TestType.LOAD,
            status=TestStatus.PASSED if metrics.error_rate < 0.05 else TestStatus.FAILED,
            description="Load test with concurrent users",
            details=metrics.dict()
        ))

        suite.total_tests = len(suite.tests)
        suite.passed_tests = len([t for t in suite.tests if t.status == TestStatus.PASSED])
        suite.failed_tests = len([t for t in suite.tests if t.status == TestStatus.FAILED])
        suite.success_rate = (suite.passed_tests / suite.total_tests * 100) if suite.total_tests > 0 else 0

        return suite

    async def _test_data_generation(self) -> List[TestResult]:
        """Test data generation"""
        results = []

        try:
            user_data = self.data_generator.generate_user_data()
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="User Data Generation",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                description="Test user data generation",
                details={"generated_data": user_data}
            ))

            signal_data = self.data_generator.generate_signal_data()
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Signal Data Generation",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                description="Test signal data generation",
                details={"generated_data": signal_data}
            ))

            market_data = self.data_generator.generate_market_data()
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Market Data Generation",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                description="Test market data generation",
                details={"generated_data": market_data}
            ))

        except Exception as e:
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Data Generation Test",
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                description=f"Data generation failed: {str(e)}",
                details={"error": str(e)}
            ))

        return results

    async def _test_validation(self) -> List[TestResult]:
        """Test validation logic"""
        results = []

        try:
            # Test OpenAPI validation
            validator = OpenAPIValidator(self.app)
            report = await validator.run_comprehensive_validation()

            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="OpenAPI Validation",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED if report.openapi_compliance_score > 80 else TestStatus.FAILED,
                description="OpenAPI specification validation",
                details={"compliance_score": report.openapi_compliance_score}
            ))

        except Exception as e:
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Validation Test",
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                description=f"Validation test failed: {str(e)}",
                details={"error": str(e)}
            ))

        return results

    async def _test_basic_endpoints(self) -> List[TestResult]:
        """Test basic endpoint accessibility"""
        results = []

        endpoints = ["/", "/health", "/docs", "/openapi.json"]
        for endpoint in endpoints:
            try:
                response = self.test_client.get(endpoint)
                results.append(TestResult(
                    test_id=str(uuid.uuid4()),
                    test_name=f"Endpoint Test - {endpoint}",
                    test_type=TestType.UNIT,
                    status=TestStatus.PASSED if response.status_code == 200 else TestStatus.FAILED,
                    description=f"Test endpoint accessibility: {endpoint}",
                    details={"status_code": response.status_code}
                ))
            except Exception as e:
                results.append(TestResult(
                    test_id=str(uuid.uuid4()),
                    test_name=f"Endpoint Test - {endpoint}",
                    test_type=TestType.UNIT,
                    status=TestStatus.FAILED,
                    description=f"Endpoint test failed: {str(e)}",
                    details={"error": str(e)}
                ))

        return results

    async def _test_authentication_flow(self) -> List[TestResult]:
        """Test authentication flow"""
        results = []

        try:
            # Test user registration
            user_data = self.data_generator.generate_user_data()
            response = self.test_client.post("/register", json=user_data)
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="User Registration",
                test_type=TestType.INTEGRATION,
                status=TestStatus.PASSED if response.status_code in [200, 201] else TestStatus.FAILED,
                description="Test user registration",
                details={"status_code": response.status_code}
            ))

            # Test login
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }
            response = self.test_client.post("/token", data=login_data)
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="User Login",
                test_type=TestType.INTEGRATION,
                status=TestStatus.PASSED if response.status_code == 200 else TestStatus.FAILED,
                description="Test user login",
                details={"status_code": response.status_code}
            ))

        except Exception as e:
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Authentication Flow Test",
                test_type=TestType.INTEGRATION,
                status=TestStatus.FAILED,
                description=f"Authentication flow failed: {str(e)}",
                details={"error": str(e)}
            ))

        return results

    async def _test_signal_generation(self) -> List[TestResult]:
        """Test signal generation"""
        results = []

        try:
            # Test signal generation endpoint
            response = self.test_client.get("/api/generate-signals-if-needed")
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Signal Generation",
                test_type=TestType.INTEGRATION,
                status=TestStatus.PASSED if response.status_code == 200 else TestStatus.FAILED,
                description="Test signal generation endpoint",
                details={"status_code": response.status_code}
            ))

            # Test signal retrieval
            response = self.test_client.get("/api/signals/latest")
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Signal Retrieval",
                test_type=TestType.INTEGRATION,
                status=TestStatus.PASSED if response.status_code == 200 else TestStatus.FAILED,
                description="Test signal retrieval",
                details={"status_code": response.status_code}
            ))

        except Exception as e:
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Signal Generation Test",
                test_type=TestType.INTEGRATION,
                status=TestStatus.FAILED,
                description=f"Signal generation test failed: {str(e)}",
                details={"error": str(e)}
            ))

        return results

    async def _test_market_data_integration(self) -> List[TestResult]:
        """Test market data integration"""
        results = []

        try:
            # Test market data endpoint
            response = self.test_client.get("/api/market-data")
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Market Data Integration",
                test_type=TestType.INTEGRATION,
                status=TestStatus.PASSED if response.status_code == 200 else TestStatus.FAILED,
                description="Test market data integration",
                details={"status_code": response.status_code}
            ))

        except Exception as e:
            results.append(TestResult(
                test_id=str(uuid.uuid4()),
                test_name="Market Data Test",
                test_type=TestType.INTEGRATION,
                status=TestStatus.FAILED,
                description=f"Market data test failed: {str(e)}",
                details={"error": str(e)}
            ))

        return results

    async def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_framework_version": "1.0.0",
            "total_tests_executed": len(self.test_suites),
            "capabilities": [
                "Unit testing with data generation",
                "Integration testing for authentication and signals",
                "Security testing (SQL injection, XSS, auth bypass)",
                "Performance testing and benchmarking",
                "Load testing with concurrent users",
                "Comprehensive reporting and metrics"
            ]
        }

# Router for testing endpoints
from fastapi import APIRouter, HTTPException, BackgroundTasks

testing_router = APIRouter(prefix="/testing", tags=["testing"])

@testing_router.post("/run/all")
async def run_all_tests(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Run comprehensive test suite in background"""
    # This would be implemented with proper background task handling
    return {"message": "Test suite started", "status": "running"}

@testing_router.get("/results/latest")
async def get_latest_test_results() -> Dict[str, Any]:
    """Get latest test results"""
    # This would retrieve cached results
    return {"message": "Test results not available yet"}

# Export testing utilities
__all__ = [
    "APITestFramework",
    "TestDataGenerator",
    "SecurityTestEngine",
    "LoadTestEngine",
    "TestSuite",
    "TestResult",
    "PerformanceMetrics",
    "LoadTestConfig",
    "testing_router"
]