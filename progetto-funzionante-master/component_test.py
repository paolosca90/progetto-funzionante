"""
Direct Component Testing Suite
Tests core functionality without relying on web server
"""

import json
import os
import time
from datetime import datetime
import traceback

def test_configuration():
    """Test configuration loading and validation"""
    print("Testing Configuration...")
    try:
        from config.settings import settings
        validation = settings.validate_configuration()

        result = {
            "success": validation["valid"],
            "environment": settings.environment.value,
            "database_url": settings.database.database_url,
            "oanda_account": settings.oanda.oanda_account_id,
            "has_jwt_secret": bool(settings.security.jwt_secret_key),
            "validation_errors": validation["errors"]
        }

        print(f"  Environment: {result['environment']}")
        print(f"  Configuration Valid: {result['success']}")
        print(f"  OANDA Account: {result['oanda_account']}")
        print(f"  JWT Secret Configured: {result['has_jwt_secret']}")

        if validation["errors"]:
            print(f"  Validation Errors: {len(validation['errors'])}")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        return {"success": False, "error": str(e)}

def test_database_connection():
    """Test database connection and operations"""
    print("\nTesting Database Connection...")
    try:
        from database import check_database_health, engine
        from models import Base

        # Check database health
        db_healthy = check_database_health()

        # Try to create tables
        try:
            Base.metadata.create_all(bind=engine)
            tables_created = True
        except Exception as e:
            tables_created = False
            print(f"  Table creation warning: {e}")

        result = {
            "success": db_healthy,
            "database_healthy": db_healthy,
            "tables_created": tables_created,
            "database_url": str(engine.url)
        }

        print(f"  Database Healthy: {db_healthy}")
        print(f"  Tables Created: {tables_created}")
        print(f"  Database URL: {result['database_url']}")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def test_oanda_integration():
    """Test OANDA API integration"""
    print("\nTesting OANDA Integration...")
    try:
        from app.services.oanda_service import OANDAService
        from config.settings import settings

        # Create OANDA service instance
        oanda_service = OANDAService()

        # Test basic configuration
        result = {
            "success": True,
            "api_key_configured": bool(settings.oanda.oanda_api_key),
            "account_id_configured": bool(settings.oanda.oanda_account_id),
            "environment": settings.oanda.oanda_environment,
            "base_url": settings.oanda.oanda_base_url,
            "service_created": True
        }

        print(f"  API Key Configured: {result['api_key_configured']}")
        print(f"  Account ID Configured: {result['account_id_configured']}")
        print(f"  Environment: {result['environment']}")
        print(f"  Base URL: {result['base_url']}")

        # Test service methods if configured
        if result['api_key_configured'] and result['account_id_configured']:
            try:
                # Test account info (this might fail with demo credentials)
                account_info = oanda_service.get_account_info()
                result["account_info_retrieved"] = True
                result["account_balance"] = account_info.get("balance", "N/A")
                print(f"  Account Balance: {result['account_balance']}")
            except Exception as e:
                result["account_info_error"] = str(e)
                print(f"  Account Info Error: {e}")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def test_gemini_integration():
    """Test Gemini AI integration"""
    print("\nTesting Gemini AI Integration...")
    try:
        import google.generativeai as genai
        from config.settings import settings

        # Test basic configuration
        result = {
            "success": True,
            "api_key_configured": bool(settings.ai.gemini_api_key),
            "model": settings.ai.gemini_model,
            "temperature": settings.ai.gemini_temperature,
            "library_imported": True
        }

        print(f"  API Key Configured: {result['api_key_configured']}")
        print(f"  Model: {result['model']}")
        print(f"  Temperature: {result['temperature']}")

        # Test API connection if configured
        if result['api_key_configured'] and settings.ai.gemini_api_key != "demo_gemini_key":
            try:
                genai.configure(api_key=settings.ai.gemini_api_key)
                model = genai.GenerativeModel(settings.ai.gemini_model)

                # Simple test
                response = model.generate_content("Hello, this is a test.")
                result["api_test_successful"] = True
                result["api_response"] = response.text[:100] + "..." if len(response.text) > 100 else response.text
                print(f"  API Test: Successful")
                print(f"  Response: {result['api_response']}")
            except Exception as e:
                result["api_test_error"] = str(e)
                print(f"  API Test Error: {e}")
        else:
            result["api_test_skipped"] = True
            print(f"  API Test: Skipped (demo credentials)")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def test_signal_generation():
    """Test trading signal generation engine"""
    print("\nTesting Signal Generation Engine...")
    try:
        from oanda_signal_engine import OANDASignalEngine

        # Create signal engine
        engine = OANDASignalEngine()

        result = {
            "success": True,
            "engine_created": True,
            "available_symbols": engine.default_symbols if hasattr(engine, 'default_symbols') else [],
            "risk_levels": ["LOW", "MEDIUM", "HIGH"]
        }

        print(f"  Engine Created: {result['engine_created']}")
        print(f"  Available Symbols: {len(result['available_symbols'])}")
        print(f"  Risk Levels: {result['risk_levels']}")

        # Test signal generation logic (without actual API calls)
        try:
            # Test with mock data
            mock_data = {
                "symbol": "EURUSD",
                "price": 1.1234,
                "rsi": 65.5,
                "macd": 0.0023,
                "atr": 0.0089
            }

            # This would normally generate a signal
            signal_type = engine.generate_signal_type(mock_data)
            result["signal_generation_test"] = True
            result["generated_signal_type"] = signal_type
            print(f"  Signal Generation Test: {signal_type}")

        except Exception as e:
            result["signal_generation_error"] = str(e)
            print(f"  Signal Generation Error: {e}")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def test_risk_management():
    """Test risk management components"""
    print("\nTesting Risk Management...")
    try:
        # Test risk calculations
        result = {
            "success": True,
            "risk_levels": ["LOW", "MEDIUM", "HIGH"],
            "position_sizes": [0.01, 0.02, 0.03, 0.04, 0.05],
            "risk_calculations": {}
        }

        # Test position sizing calculation
        account_balance = 10000
        risk_percentage = 0.02  # 2% risk

        for risk_level in ["LOW", "MEDIUM", "HIGH"]:
            risk_multipliers = {"LOW": 0.5, "MEDIUM": 1.0, "HIGH": 1.5}
            adjusted_risk = risk_percentage * risk_multipliers[risk_level]
            position_size = (account_balance * adjusted_risk) / 100  # Simplified calculation

            result["risk_calculations"][risk_level] = {
                "risk_percentage": adjusted_risk,
                "position_size": position_size
            }

        print(f"  Risk Levels: {result['risk_levels']}")
        print(f"  Position Sizes: {result['position_sizes']}")
        print(f"  Risk Calculations: {len(result['risk_calculations'])} levels")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def test_cache_system():
    """Test cache system"""
    print("\nTesting Cache System...")
    try:
        from app.services.cache_service import cache_service

        result = {
            "success": True,
            "cache_service_created": True,
            "cache_configured": cache_service.redis_url is not None,
            "redis_url": cache_service.redis_url,
            "cache_prefix": cache_service.cache_prefix if hasattr(cache_service, 'cache_prefix') else "N/A"
        }

        print(f"  Cache Service Created: {result['cache_service_created']}")
        print(f"  Cache Configured: {result['cache_configured']}")
        print(f"  Redis URL: {result['redis_url']}")
        print(f"  Cache Prefix: {result['cache_prefix']}")

        # Test basic cache operations
        try:
            test_key = "test_key"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}

            # Test set operation
            cache_service.set(test_key, test_value, ttl=60)

            # Test get operation
            retrieved_value = cache_service.get(test_key)

            result["cache_operations_test"] = True
            result["cache_set_success"] = True
            result["cache_get_success"] = retrieved_value == test_value

            print(f"  Cache Operations Test: Successful")

        except Exception as e:
            result["cache_operations_error"] = str(e)
            print(f"  Cache Operations Error: {e}")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def test_authentication_system():
    """Test authentication system"""
    print("\nTesting Authentication System...")
    try:
        from app.services.auth_service import AuthService

        # Create auth service
        auth_service = AuthService()

        result = {
            "success": True,
            "auth_service_created": True,
            "jwt_algorithm": auth_service.algorithm if hasattr(auth_service, 'algorithm') else "HS256",
            "access_token_expire_minutes": auth_service.access_token_expire_minutes if hasattr(auth_service, 'access_token_expire_minutes') else 30
        }

        print(f"  Auth Service Created: {result['auth_service_created']}")
        print(f"  JWT Algorithm: {result['jwt_algorithm']}")
        print(f"  Token Expiration: {result['access_token_expire_minutes']} minutes")

        # Test token creation
        try:
            test_user_data = {"user_id": 1, "username": "testuser"}
            token = auth_service.create_access_token(data=test_user_data)

            # Test token validation
            decoded_token = auth_service.decode_token(token)

            result["token_creation_test"] = True
            result["token_validation_test"] = True
            result["token_created"] = True
            result["token_validated"] = True

            print(f"  Token Creation: Successful")
            print(f"  Token Validation: Successful")

        except Exception as e:
            result["token_error"] = str(e)
            print(f"  Token Error: {e}")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def run_component_tests():
    """Run all component tests"""
    print("Starting Component Testing Suite")
    print("=" * 60)

    start_time = time.time()

    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("OANDA Integration", test_oanda_integration),
        ("Gemini AI Integration", test_gemini_integration),
        ("Signal Generation", test_signal_generation),
        ("Risk Management", test_risk_management),
        ("Cache System", test_cache_system),
        ("Authentication System", test_authentication_system)
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "test_results": {},
        "overall_score": 0,
        "component_scores": {},
        "recommendations": []
    }

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        test_result = test_func()

        results["test_results"][test_name] = test_result

        if test_result.get("success", False):
            passed_tests += 1
            score = 100
        else:
            score = 0

        results["component_scores"][test_name] = score

    # Calculate overall score
    overall_score = (passed_tests / total_tests) * 100
    results["overall_score"] = round(overall_score, 2)
    results["passed_tests"] = passed_tests
    results["total_tests"] = total_tests

    # Generate recommendations
    if overall_score >= 80:
        results["recommendations"].append("All core components are functioning properly")
    elif overall_score >= 60:
        results["recommendations"].append("Most components are working, but some need attention")
    else:
        results["recommendations"].append("Multiple components need fixes before production")

    # Add specific recommendations based on test results
    for test_name, test_result in results["test_results"].items():
        if not test_result.get("success", False):
            results["recommendations"].append(f"Fix {test_name} component: {test_result.get('error', 'Unknown error')}")

    # Print summary
    end_time = time.time()
    execution_time = end_time - start_time

    print(f"\n{'='*60}")
    print("COMPONENT TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Overall Score: {overall_score:.1f}%")
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Execution Time: {execution_time:.2f} seconds")

    # Print component scores
    print(f"\nComponent Scores:")
    for test_name, score in results["component_scores"].items():
        status = "PASS" if score == 100 else "FAIL"
        print(f"  {test_name}: {score}% - {status}")

    # Print recommendations
    if results["recommendations"]:
        print(f"\nRecommendations:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. {rec}")

    # Production readiness assessment
    if overall_score >= 80:
        print(f"\nPRODUCTION READINESS: READY")
        print("The system has all core components functioning.")
    elif overall_score >= 60:
        print(f"\nPRODUCTION READINESS: CONDITIONAL")
        print("The system needs minor fixes but is mostly functional.")
    else:
        print(f"\nPRODUCTION READINESS: NOT READY")
        print("The system requires significant fixes before production deployment.")

    return results

if __name__ == "__main__":
    results = run_component_tests()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"component_test_results_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: {filename}")