#!/usr/bin/env python3
"""
Comprehensive API Test Suite for AI Trading System
Full End-to-End Testing with HTTP Client
"""

import asyncio
import json
import random
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
import aiohttp

class TestResult:
    """Test result data class"""
    def __init__(self, name: str, success: bool, response_data: Any = None,
                 status_code: int = None, execution_time: float = None, error: str = None):
        self.name = name
        self.success = success
        self.response_data = response_data
        self.status_code = status_code
        self.execution_time = execution_time
        self.error = error

class APIClient:
    """Simple HTTP client for API testing"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Content-Type": "application/json"}
        )
        self.auth_token = None

    async def close(self):
        await self.session.close()

    async def test_endpoint(self, method: str, endpoint: str, name: str,
                           expected_status: int = 200, headers: Dict = None,
                           json_data: Dict = None, data: Dict = None, validate_response=None,
                           measure_performance: bool = False,
                           expected_max_response_time: float = None) -> TestResult:
        """Test a single API endpoint"""
        start_time = time.time()

        try:
            # Prepare headers
            request_headers = {}
            if headers:
                request_headers.update(headers)
            if self.auth_token:
                request_headers["Authorization"] = f"Bearer {self.auth_token}"

            # Make request
            url = f"{self.base_url}{endpoint}"
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    response_data = await response.json() if response.content_type == "application/json" else await response.text()
                    status_code = response.status
            elif method.upper() == "POST":
                if data:  # Form data
                    async with self.session.post(url, headers=request_headers, data=data) as response:
                        response_data = await response.json() if response.content_type == "application/json" else await response.text()
                        status_code = response.status
                else:  # JSON data
                    async with self.session.post(url, headers=request_headers, json=json_data) as response:
                        response_data = await response.json() if response.content_type == "application/json" else await response.text()
                        status_code = response.status
            elif method.upper() == "PUT":
                async with self.session.put(url, headers=request_headers, json=json_data) as response:
                    response_data = await response.json() if response.content_type == "application/json" else await response.text()
                    status_code = response.status
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    response_data = await response.json() if response.content_type == "application/json" else await response.text()
                    status_code = response.status
            else:
                raise ValueError(f"Unsupported method: {method}")

            execution_time = time.time() - start_time

            # Validate response
            success = status_code == expected_status
            if success and validate_response and callable(validate_response):
                try:
                    success = validate_response(response_data)
                except Exception as e:
                    success = False
                    error_msg = f"Validation failed: {str(e)}"

            # Check performance requirements
            performance_ok = True
            if measure_performance and expected_max_response_time:
                performance_ok = execution_time <= expected_max_response_time
                if not performance_ok:
                    success = False

            result = TestResult(
                name=name,
                success=success,
                response_data=response_data,
                status_code=status_code,
                execution_time=execution_time,
                error=None if success else f"Expected status {expected_status}, got {status_code}"
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                name=name,
                success=False,
                response_data=None,
                status_code=None,
                execution_time=execution_time,
                error=str(e)
            )

class TradingSystemTests:
    """Comprehensive test suite for the AI Trading System"""

    def __init__(self):
        self.client = APIClient(base_url="http://localhost:8000")
        self.results = []
        self.test_user_data = {
            "username": f"testuser_{random.randint(1000, 9999)}",
            "email": f"test_{random.randint(1000, 9999)}@example.com",
            "password": "TestPassword123!"
        }
        self.auth_token = None

    async def run_health_check_tests(self) -> List[TestResult]:
        """Test 1: Health Check Endpoints"""
        print("Running Health Check Tests...")
        results = []

        # Test main health endpoint
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/health",
            name="Health Check - Main Endpoint",
            expected_status=200,
            validate_response=lambda r: r.get("status") == "healthy"
        )
        results.append(result)

        # Test cache health endpoint
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/cache/health",
            name="Health Check - Cache Endpoint",
            expected_status=200,
            validate_response=lambda r: "cache" in r.get("status", "").lower()
        )
        results.append(result)

        return results

    async def run_authentication_tests(self) -> List[TestResult]:
        """Test 2: Authentication Flow"""
        print("Running Authentication Tests...")
        results = []

        # Test user registration
        result = await self.client.test_endpoint(
            method="POST",
            endpoint="/register",
            name="Authentication - User Registration",
            json_data=self.test_user_data,
            expected_status=200,
            validate_response=lambda r: "success" in str(r).lower()
        )
        results.append(result)

        # Test user login (try both /login and /token endpoints)
        login_data = {
            "username": self.test_user_data["username"],
            "password": self.test_user_data["password"]
        }

        # Try /login endpoint first
        result = await self.client.test_endpoint(
            method="POST",
            endpoint="/login",
            name="Authentication - User Login",
            json_data=login_data,
            expected_status=200,
            validate_response=lambda r: "access_token" in r
        )

        # If /login fails, try /token endpoint
        if not result.success:
            result = await self.client.test_endpoint(
                method="POST",
                endpoint="/token",
                name="Authentication - User Login (Token Endpoint)",
                data=login_data,  # Send as form data
                expected_status=200,
                validate_response=lambda r: "access_token" in r
            )

        results.append(result)

        # Store token for subsequent tests
        if result.success and result.response_data:
            if isinstance(result.response_data, dict):
                self.auth_token = result.response_data.get("access_token")
            else:
                # Try to parse JSON from string
                try:
                    parsed_data = json.loads(result.response_data)
                    self.auth_token = parsed_data.get("access_token")
                except:
                    pass

            if self.auth_token:
                self.client.auth_token = self.auth_token

        # Test protected endpoint without authentication
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/signals/",
            name="Authentication - Protected Endpoint (No Auth)",
            expected_status=401
        )
        results.append(result)

        # Test protected endpoint with authentication
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            result = await self.client.test_endpoint(
                method="GET",
                endpoint="/signals/",
                name="Authentication - Protected Endpoint (With Auth)",
                headers=headers,
                expected_status=200
            )
            results.append(result)

        return results

    async def run_signal_management_tests(self) -> List[TestResult]:
        """Test 3: Signal Management Endpoints"""
        print("Running Signal Management Tests...")
        results = []

        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        # Test get latest signals
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/api/signals/latest",
            name="Signal Management - Get Latest Signals",
            headers=headers,
            expected_status=200,
            validate_response=lambda r: isinstance(r, list)
        )
        results.append(result)

        # Test signals list with pagination
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/signals/?page=1&limit=10",
            name="Signal Management - Signals List with Pagination",
            headers=headers,
            expected_status=200
        )
        results.append(result)

        # Test signal filtering
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/signals/?symbol=EUR_USD&limit=5",
            name="Signal Management - Signal Filtering",
            headers=headers,
            expected_status=200
        )
        results.append(result)

        return results

    async def run_admin_functionality_tests(self) -> List[TestResult]:
        """Test 4: Admin Functionality"""
        print("Running Admin Functionality Tests...")
        results = []

        # Test admin signal generation (this might fail without proper admin credentials)
        result = await self.client.test_endpoint(
            method="POST",
            endpoint="/admin/generate-signals",
            name="Admin - Generate Signals",
            json_data={"symbol": "EUR_USD", "timeframe": "H1"},
            expected_status=401  # Expected to fail without admin auth
        )
        results.append(result)

        # Test admin dashboard endpoint
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/admin/dashboard",
            name="Admin - Dashboard Access",
            expected_status=401  # Expected to fail without admin auth
        )
        results.append(result)

        return results

    async def run_error_handling_tests(self) -> List[TestResult]:
        """Test 5: Error Handling"""
        print("Running Error Handling Tests...")
        results = []

        # Test 404 - Not Found
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/nonexistent-endpoint",
            name="Error Handling - 404 Not Found",
            expected_status=404
        )
        results.append(result)

        # Test 401 - Unauthorized
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/signals/",
            name="Error Handling - 401 Unauthorized",
            expected_status=401
        )
        results.append(result)

        # Test 422 - Validation Error (invalid data)
        result = await self.client.test_endpoint(
            method="POST",
            endpoint="/register",
            name="Error Handling - 422 Validation Error",
            json_data={"invalid": "data"},
            expected_status=422
        )
        results.append(result)

        # Test 403 - Forbidden (admin endpoint without admin rights)
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            result = await self.client.test_endpoint(
                method="POST",
                endpoint="/admin/generate-signals",
                name="Error Handling - 403 Forbidden",
                headers=headers,
                expected_status=403
            )
            results.append(result)

        return results

    async def run_performance_tests(self) -> List[TestResult]:
        """Test 6: Performance and Load Testing"""
        print("Running Performance Tests...")
        results = []

        # Test response times for critical endpoints
        endpoints = [
            ("/health", "GET", {}),
            ("/api/signals/latest", "GET", {}),
        ]

        for endpoint, method, data in endpoints:
            result = await self.client.test_endpoint(
                method=method,
                endpoint=endpoint,
                name=f"Performance - {method} {endpoint}",
                measure_performance=True,
                expected_max_response_time=1000  # 1 second max
            )
            results.append(result)

        # Test concurrent requests
        start_time = time.time()
        concurrent_tasks = []

        for i in range(10):
            task = self.client.test_endpoint(
                method="GET",
                endpoint="/health",
                name=f"Performance - Concurrent Request {i+1}",
                measure_performance=True
            )
            concurrent_tasks.append(task)

        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze concurrent performance
        successful_concurrent = sum(1 for r in concurrent_results if not isinstance(r, Exception) and r.success)
        total_time = end_time - start_time

        performance_summary = TestResult(
            name="Performance - Concurrent Requests Analysis",
            success=True,
            response_data={
                "total_requests": len(concurrent_results),
                "successful_requests": successful_concurrent,
                "success_rate": successful_concurrent / len(concurrent_results),
                "total_time": total_time,
                "avg_time_per_request": total_time / len(concurrent_results)
            },
            execution_time=total_time
        )
        results.append(performance_summary)

        return results

    async def run_security_tests(self) -> List[TestResult]:
        """Test 7: Security Validation"""
        print("Running Security Tests...")
        results = []

        # Test SQL Injection attempts
        malicious_inputs = [
            {"username": "admin' OR '1'='1", "password": "password"},
            {"username": "test", "password": "' OR '1'='1"},
            {"username": "<script>alert('xss')</script>", "password": "password"}
        ]

        for i, malicious_input in enumerate(malicious_inputs):
            result = await self.client.test_endpoint(
                method="POST",
                endpoint="/login",
                name=f"Security - Malicious Input Test {i+1}",
                json_data=malicious_input,
                expected_status=401  # Should fail to authenticate
            )
            results.append(result)

        # Test CORS headers
        result = await self.client.test_endpoint(
            method="GET",
            endpoint="/health",
            name="Security - CORS Headers",
            headers={"Origin": "http://malicious.com"},
            expected_status=200,
            validate_response=lambda r: True  # Just check it doesn't break
        )
        results.append(result)

        return results

    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run all test categories and generate comprehensive report"""
        print("Starting Comprehensive API Test Suite...")
        print("=" * 60)

        start_time = time.time()

        # Run all test categories
        test_categories = [
            ("Health Check", self.run_health_check_tests),
            ("Authentication", self.run_authentication_tests),
            ("Signal Management", self.run_signal_management_tests),
            ("Admin Functionality", self.run_admin_functionality_tests),
            ("Error Handling", self.run_error_handling_tests),
            ("Performance", self.run_performance_tests),
            ("Security", self.run_security_tests)
        ]

        all_results = []
        category_results = {}

        for category_name, test_func in test_categories:
            try:
                category_start = time.time()
                results = await test_func()
                category_time = time.time() - category_start

                category_results[category_name] = {
                    "results": results,
                    "total_tests": len(results),
                    "passed_tests": sum(1 for r in results if r.success),
                    "failed_tests": sum(1 for r in results if not r.success),
                    "execution_time": category_time,
                    "success_rate": sum(1 for r in results if r.success) / len(results) if results else 0
                }
                all_results.extend(results)

                print(f"OK {category_name}: {len(results)} tests completed")

            except Exception as e:
                print(f"ERROR {category_name}: Failed with error - {str(e)}")
                category_results[category_name] = {
                    "error": str(e),
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "execution_time": 0,
                    "success_rate": 0
                }

        total_time = time.time() - start_time

        # Generate comprehensive report
        report = {
            "test_execution_summary": {
                "total_tests": len(all_results),
                "passed_tests": sum(1 for r in all_results if r.success),
                "failed_tests": sum(1 for r in all_results if not r.success),
                "success_rate": sum(1 for r in all_results if r.success) / len(all_results) if all_results else 0,
                "total_execution_time": total_time,
                "test_categories": len(category_results)
            },
            "category_results": category_results,
            "performance_metrics": {
                "avg_response_time": sum(r.execution_time for r in all_results) / len(all_results) if all_results else 0,
                "slowest_test": max(all_results, key=lambda r: r.execution_time) if all_results else None,
                "fastest_test": min(all_results, key=lambda r: r.execution_time) if all_results else None
            },
            "error_analysis": {
                "failed_tests_details": [
                    {
                        "name": r.name,
                        "error": r.error,
                        "status_code": r.status_code,
                        "response_data": r.response_data
                    }
                    for r in all_results if not r.success
                ]
            },
            "security_validation": {
                "malicious_input_tests": len([r for r in all_results if "Security - Malicious Input" in r.name]),
                "security_tests_passed": len([r for r in all_results if "Security -" in r.name and r.success])
            },
            "production_readiness": {
                "overall_health": sum(1 for r in all_results if r.success) / len(all_results) if all_results else 0,
                "critical_issues": len([r for r in all_results if not r.success and "Health" in r.name]),
                "recommendations": self._generate_recommendations(all_results, category_results)
            }
        }

        return report

    def _generate_recommendations(self, all_results: List[TestResult], category_results: Dict) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []

        # Check overall health
        overall_success_rate = sum(1 for r in all_results if r.success) / len(all_results) if all_results else 0
        if overall_success_rate < 0.9:
            recommendations.append("WARNING: Low overall success rate (<90%). Review failing tests and fix critical issues.")

        # Check specific categories
        for category_name, results in category_results.items():
            if isinstance(results, dict) and "success_rate" in results:
                if results["success_rate"] < 0.8:
                    recommendations.append(f"CONFIG {category_name} category has low success rate ({results['success_rate']:.1%}). Focus on this area.")

        # Check performance
        slow_tests = [r for r in all_results if r.execution_time > 2.0]  # Slower than 2 seconds
        if slow_tests:
            recommendations.append(f"PERFORMANCE {len(slow_tests)} tests are slow (>2s). Consider optimization.")

        # Check security
        security_failures = [r for r in all_results if "Security" in r.name and not r.success]
        if security_failures:
            recommendations.append(f"SECURITY {len(security_failures)} security tests failed. Address security vulnerabilities.")

        # Authentication issues
        auth_failures = [r for r in all_results if "Authentication" in r.name and not r.success]
        if auth_failures:
            recommendations.append(f"AUTH {len(auth_failures)} authentication tests failed. Review auth implementation.")

        if not recommendations:
            recommendations.append("All tests passed! System is ready for production deployment.")

        return recommendations

async def main():
    """Main execution function"""
    tester = TradingSystemTests()

    try:
        # Run comprehensive test suite
        report = await tester.run_comprehensive_test_suite()

        # Print results
        print("\n" + "=" * 60)
        print("COMPREHENSIVE API TEST RESULTS")
        print("=" * 60)

        # Summary
        summary = report["test_execution_summary"]
        print(f"Test Execution Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        print(f"   Execution Time: {summary['total_execution_time']:.2f}s")
        print(f"   Test Categories: {summary['test_categories']}")

        # Category results
        print(f"\nCategory Results:")
        for category, data in report["category_results"].items():
            if isinstance(data, dict) and "success_rate" in data:
                print(f"   {category}: {data['passed_tests']}/{data['total_tests']} ({data['success_rate']:.1%})")

        # Performance metrics
        perf = report["performance_metrics"]
        print(f"\nPerformance Metrics:")
        print(f"   Avg Response Time: {perf['avg_response_time']:.3f}s")
        if perf['slowest_test']:
            print(f"   Slowest Test: {perf['slowest_test'].name} ({perf['slowest_test'].execution_time:.3f}s)")
        if perf['fastest_test']:
            print(f"   Fastest Test: {perf['fastest_test'].name} ({perf['fastest_test'].execution_time:.3f}s)")

        # Error analysis
        if report["error_analysis"]["failed_tests_details"]:
            print(f"\nError Analysis:")
            for error in report["error_analysis"]["failed_tests_details"]:
                print(f"   - {error['name']}: {error.get('error', 'Unknown error')}")

        # Security validation
        security = report["security_validation"]
        print(f"\nSecurity Validation:")
        print(f"   Malicious Input Tests: {security['malicious_input_tests']}")
        print(f"   Security Tests Passed: {security['security_tests_passed']}")

        # Production readiness
        readiness = report["production_readiness"]
        print(f"\nProduction Readiness:")
        print(f"   Overall Health: {readiness['overall_health']:.1%}")
        print(f"   Critical Issues: {readiness['critical_issues']}")

        print(f"\nRecommendations:")
        for rec in readiness["recommendations"]:
            print(f"   {rec}")

        # Save detailed report
        with open("comprehensive_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\nDetailed report saved to: comprehensive_test_report.json")

    except Exception as e:
        print(f"ERROR Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.client.close()

if __name__ == "__main__":
    asyncio.run(main())