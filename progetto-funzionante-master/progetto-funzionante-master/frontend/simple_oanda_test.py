#!/usr/bin/env python3
"""
Simple OANDA API connection test
Windows-compatible version without unicode characters
"""

import asyncio
import aiohttp
import json
import os
from typing import Optional

class OANDAConnectionTest:
    """Simple test class for OANDA API connection"""

    def __init__(self):
        self.api_key = os.getenv("OANDA_API_KEY")
        self.account_id = os.getenv("OANDA_ACCOUNT_ID", "101-001-37019635-001")
        self.environment = os.getenv("OANDA_ENVIRONMENT", "practice")

        if self.environment.lower() in ["demo", "practice"]:
            self.base_url = "https://api-fxpractice.oanda.com"
        else:
            self.base_url = "https://api-fxtrade.oanda.com"

        self.session: Optional[aiohttp.ClientSession] = None

        print("OANDA API Connection Test")
        print("Environment:", self.environment)
        print("Account:", self.account_id)
        print("API Key (first 10):", self.api_key[:10] if self.api_key else "None")

    async def connect(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        print("HTTP session created")

    async def test_basic_authentication(self):
        """Test basic authentication with account endpoint"""
        try:
            print("\nTesting Account Info API...")

            endpoint = f"/v3/accounts/{self.account_id}"
            url = f"{self.base_url}{endpoint}"

            async with self.session.get(url) as response:
                print(f"Response Status: {response.status}")

                if response.status == 200:
                    account_data = await response.json()
                    print("Authentication SUCCESSFUL!")
                    print("Account ID:", account_data['account']['id'])
                    balance = float(account_data['account']['balance'])
                    print(f"Balance: {balance} USD")
                    return True
                elif response.status == 403:
                    error_data = await response.json()
                    print("Authentication FAILED (403 Forbidden)")
                    error_msg = error_data.get('errorMessage', 'Unknown error')
                    print("Error:", error_msg)
                    return False
                else:
                    error_data = await response.json()
                    print(f"Unexpected status {response.status}:", error_data)
                    return False

        except Exception as e:
            print("Connection error:", e)
            return False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

async def main():
    async with OANDAConnectionTest() as tester:
        auth_ok = await tester.test_basic_authentication()

        if auth_ok:
            print("\nAll tests passed - OANDA API is working!")

async def simple_test():
    """Simplified synchronous test"""
    api_key = os.getenv("OANDA_API_KEY")
    account_id = os.getenv("OANDA_ACCOUNT_ID", "101-001-37019635-001")
    environment = os.getenv("OANDA_ENVIRONMENT", "practice")

    if environment.lower() in ["demo", "practice"]:
        base_url = "https://api-fxpractice.oanda.com"
    else:
        base_url = "https://api-fxtrade.oanda.com"

    url = f"{base_url}/v3/accounts/{account_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("Testing OANDA API connection...")
    print("Environment:", environment)
    print("Account:", account_id)
    print("API Key:", "*" * 20 if api_key else "none")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(url, headers=headers) as response:
                print("Status code:", response.status)

                if response.status == 200:
                    data = await response.json()
                    print("SUCCESS: Account ID =", data['account']['id'])
                    print("Account balance =", data['account']['balance'])

                elif response.status == 403:
                    error_data = await response.json()
                    print("FAILED: 403 Forbidden")
                    print("Error:", error_data.get('errorMessage', 'Unknown'))
                    print("\nPOSSIBLE CAUSES:")
                    print("1. API key is invalid or expired")
                    print("2. Account ID doesn't match API key")
                    print("3. Account is not authorized for practice environment")
                    print("4. IP address may be blocked by OANDA")

                else:
                    print("Error:", await response.json())

    except Exception as e:
        print("Exception occurred:", e)

if __name__ == "__main__":
    asyncio.run(simple_test())