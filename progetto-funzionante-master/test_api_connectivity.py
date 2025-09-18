#!/usr/bin/env python3
"""
API Connectivity Test Script
"""

import os
import sys
import requests
import time
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    env_vars = {}

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value

    return env_vars

def test_oanda_connectivity():
    """Test OANDA API connectivity"""
    print("Testing OANDA API Connectivity")
    print("=" * 40)

    env_vars = load_env_file()
    api_key = env_vars.get('OANDA_API_KEY', '')
    account_id = env_vars.get('OANDA_ACCOUNT_ID', '')
    environment = env_vars.get('OANDA_ENVIRONMENT', 'demo')

    if api_key == 'test_key' or not api_key:
        print("FAILED: OANDA API key not configured")
        return False

    if account_id == 'test_account' or not account_id:
        print("FAILED: OANDA Account ID not configured")
        return False

    # OANDA API endpoints
    if environment == 'demo':
        base_url = "https://api-fxpractice.oanda.com/v3"
    elif environment == 'live':
        base_url = "https://api-fxtrade.oanda.com/v3"
    else:  # practice environment
        base_url = "https://api-fxpractice.oanda.com/v3"

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        # Test account endpoint
        print(f"Testing account endpoint for {account_id}...")
        start_time = time.time()

        response = requests.get(f"{base_url}/accounts/{account_id}", headers=headers, timeout=10)
        response_time = time.time() - start_time

        if response.status_code == 200:
            print(f"SUCCESS: Account data retrieved in {response_time:.2f}s")
            account_data = response.json()
            print(f"Account: {account_data.get('account', {}).get('displayName', 'N/A')}")
            print(f"Balance: {account_data.get('account', {}).get('balance', 'N/A')}")
            return True
        else:
            print(f"FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"FAILED: Connection error - {e}")
        return False

def test_gemini_connectivity():
    """Test Gemini API connectivity"""
    print("\nTesting Gemini API Connectivity")
    print("=" * 40)

    env_vars = load_env_file()
    api_key = env_vars.get('GEMINI_API_KEY', '')

    if api_key == 'test_gemini_key' or not api_key:
        print("FAILED: Gemini API key not configured")
        return False

    # Test Gemini API with gemini-1.5-flash model (updated model)
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "contents": [{
            "parts": [{
                "text": "Hello, this is a test message."
            }]
        }],
        "generationConfig": {
            "maxOutputTokens": 50
        }
    }

    try:
        print("Testing Gemini content generation...")
        start_time = time.time()

        response = requests.post(f"{url}?key={api_key}", headers=headers, json=data, timeout=10)
        response_time = time.time() - start_time

        if response.status_code == 200:
            print(f"SUCCESS: Gemini API responded in {response_time:.2f}s")
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"Generated text: {text[:100]}...")
            return True
        else:
            print(f"FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"FAILED: Connection error - {e}")
        return False

def test_fastapi_health():
    """Test FastAPI health endpoint"""
    print("\nTesting FastAPI Health Endpoint")
    print("=" * 40)

    try:
        # Try localhost:8000 first
        print("Testing localhost:8000...")
        response = requests.get("http://localhost:8000/health", timeout=5)

        if response.status_code == 200:
            print("SUCCESS: FastAPI health check passed")
            health_data = response.json()
            print(f"Status: {health_data.get('status', 'N/A')}")
            return True
        else:
            print(f"FAILED: HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException:
        # Try port 8001 as fallback
        try:
            print("Testing localhost:8001...")
            response = requests.get("http://localhost:8001/health", timeout=5)

            if response.status_code == 200:
                print("SUCCESS: FastAPI health check passed")
                health_data = response.json()
                print(f"Status: {health_data.get('status', 'N/A')}")
                return True
            else:
                print(f"FAILED: HTTP {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"FAILED: Cannot connect to FastAPI server - {e}")
            return False

def main():
    """Main test function"""
    print("API Connectivity Test Suite")
    print("=" * 50)

    results = {
        'oanda': test_oanda_connectivity(),
        'gemini': test_gemini_connectivity(),
        'fastapi': test_fastapi_health()
    }

    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)

    success_count = sum(results.values())
    total_count = len(results)

    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test.upper():<10}: {status}")

    print(f"\nOverall: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("SUCCESS: All connectivity tests passed!")
        print("Your AI Trading System is ready for production!")
    else:
        print("WARNING: Some tests failed. Please check the issues above.")
        print("Run 'python quick_setup.py' to configure your API credentials.")

if __name__ == "__main__":
    main()