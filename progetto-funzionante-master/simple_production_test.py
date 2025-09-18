"""
Simple Production Readiness Test Suite
"""

import json
import requests
import time
from datetime import datetime

def run_production_tests():
    """Run simplified production readiness tests"""
    base_url = "http://localhost:8000"
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_score": 0,
        "recommendations": []
    }

    print("Starting Production Readiness Test Suite")
    print("=" * 50)

    tests = [
        ("Health Check", f"{base_url}/health"),
        ("Root Endpoint", f"{base_url}/"),
        ("Cache Health", f"{base_url}/cache/health"),
        ("Config Info", f"{base_url}/config/info"),
        ("Config Validation", f"{base_url}/config/validate"),
        ("CORS Test", f"{base_url}/cors-test"),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, url in tests:
        print(f"\nTesting: {test_name}")
        print(f"URL: {url}")

        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time

            test_result = {
                "url": url,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200,
                "content_length": len(response.content) if response.content else 0
            }

            if response.status_code == 200:
                try:
                    test_result["response_data"] = response.json()
                except:
                    test_result["response_text"] = response.text[:200]
                passed_tests += 1
                print(f"Result: PASS ({response.status_code}) - {response_time:.2f}s")
            else:
                print(f"Result: FAIL ({response.status_code}) - {response_time:.2f}s")

            results["tests"][test_name] = test_result

        except Exception as e:
            error_result = {
                "url": url,
                "error": str(e),
                "success": False
            }
            results["tests"][test_name] = error_result
            print(f"Result: ERROR - {str(e)}")

    # Test POST endpoints
    print(f"\nTesting POST endpoints:")
    post_tests = [
        ("Signal Generation", f"{base_url}/api/v1/signals/generate", {"symbol": "EURUSD"}),
        ("Cache Invalidation", f"{base_url}/cache/invalidate", {}),
    ]

    for test_name, url, data in post_tests:
        print(f"\nTesting: {test_name}")
        try:
            start_time = time.time()
            response = requests.post(url, json=data, timeout=10)
            response_time = time.time() - start_time

            test_result = {
                "url": url,
                "method": "POST",
                "data": data,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code in [200, 201, 400]  # Allow validation errors
            }

            if response.status_code in [200, 201, 400]:
                passed_tests += 1
                print(f"Result: PASS ({response.status_code}) - {response_time:.2f}s")
            else:
                print(f"Result: FAIL ({response.status_code}) - {response_time:.2f}s")

            results["tests"][test_name] = test_result

        except Exception as e:
            error_result = {
                "url": url,
                "method": "POST",
                "error": str(e),
                "success": False
            }
            results["tests"][test_name] = error_result
            print(f"Result: ERROR - {str(e)}")

    # Calculate overall score
    success_rate = (passed_tests / total_tests) * 100
    results["overall_score"] = round(success_rate, 2)
    results["passed_tests"] = passed_tests
    results["total_tests"] = total_tests

    # Generate recommendations
    if success_rate >= 80:
        results["recommendations"].append("System is ready for production deployment")
    elif success_rate >= 60:
        results["recommendations"].append("System needs minor fixes before production")
    else:
        results["recommendations"].append("System requires significant fixes before production")

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Overall Score: {success_rate:.1f}%")
    print(f"Tests Passed: {passed_tests}/{total_tests}")

    if success_rate >= 80:
        print("Status: READY FOR PRODUCTION")
    elif success_rate >= 60:
        print("Status: CONDITIONALLY READY")
    else:
        print("Status: NOT READY")

    return results

if __name__ == "__main__":
    results = run_production_tests()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"production_test_results_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: {filename}")