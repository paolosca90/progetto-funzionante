#!/usr/bin/env python3
"""
Test OANDA API connection script
Run this locally or deploy to Railway for connection debugging
"""

import asyncio
import aiohttp
import json
import os
from typing import Optional
from datetime import datetime

class OANDAConnectionTest:
    """Simple test class for OANDA API connection"""

    def __init__(self):
        # Use Railway environment variables
        self.api_key = os.getenv("OANDA_API_KEY")
        self.account_id = os.getenv("OANDA_ACCOUNT_ID", "101-001-37019635-001")
        self.environment = os.getenv("OANDA_ENVIRONMENT", "practice")

        # Set base URL based on environment
        if self.environment.lower() in ["demo", "practice"]:
            self.base_url = "https://api-fxpractice.oanda.com"
        else:
            self.base_url = "https://api-fxtrade.oanda.com"

        self.session: Optional[aiohttp.ClientSession] = None
        print(f"🔧 Testing OANDA {self.environment} environment")
        print(f"🔧 Account: {self.account_id}")
        print(f"🔧 API Key: {self.api_key[:10] if self.api_key else 'None'}...")

    async def connect(self):
        """Establish connection to test basic connectivity"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        print("✅ HTTP session created")

    async def test_basic_authentication(self):
        """Test basic authentication with account endpoint"""
        try:
            print("\n🧪 Testing Account Info API...")

            endpoint = f"/v3/accounts/{self.account_id}"
            url = f"{self.base_url}{endpoint}"

            async with self.session.get(url) as response:
                print(f"🏷️  Response Status: {response.status}")

                if response.status == 200:
                    account_data = await response.json()
                    print("✅ Authentication SUCCESSFUL!")
                    print(f"🆔 Account ID: {account_data['account']['id']}")
                    print(f"💰 Balance: {account_data['account']['balance']} {'USD'}")
                    return True
                elif response.status == 403:
                    error_data = await response.json()
                    print("❌ Authentication FAILED (403 Forbidden)")
                    print(f"📄 Error: {error_data.get('errorMessage', 'Unknown error')}")
                    print("\n🚨 POSSIBLE CAUSES:")
                    print("   • API key is invalid or expired")
                    print("   • Account ID mismatch with API key")
                    print("   • Practice account not authorized for this API key")
                    print("   • IP address blocked by OANDA")
                    return False
                else:
                    error_data = await response.json()
                    print(f"❌ Unexpected status {response.status}: {error_data}")
                    return False

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    async def test_instruments_access(self):
        """Test access to instrument list"""
        try:
            print("\n🧪 Testing Instruments Access...")

            endpoint = f"/v3/accounts/{self.account_id}/instruments"
            url = f"{self.base_url}{endpoint}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    instruments_data = await response.json()
                    instruments = instruments_data.get('instruments', [])
                    print(f"✅ Instruments Access OK - Found {len(instruments)} instruments")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Instruments Access Failed: {error_data}")
                    return False

        except Exception as e:
            print(f"❌ Instruments test error: {e}")
            return False

    async def test_market_prices(self):
        """Test market price retrieval"""
        try:
            print("\n🧪 Testing Market Prices Access...")

            params = {"instruments": "EUR_USD,GBP_USD"}
            url = f"{self.base_url}/v3/pricing"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    prices_data = await response.json()
                    prices = prices_data.get('prices', [])
                    if prices:
                        print(f"✅ Price Access SUCCESSFUL - Retrieved {len(prices)} price(s)")
                        for price in prices[:2]:  # Show first 2
                            print(f"   {price['instrument']}: {price['bids'][0]['price']}/{price['asks'][0]['price']}")
                        return True
                    else:
                        print("✅ Price Access OK but no prices returned")
                        return True
                else:
                    error_data = await response.json()
                    print(f"❌ Price Access Failed: {error_data}")
                    return False

        except Exception as e:
            print(f"❌ Price test error: {e}")
            return False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

async def main():
    """Main test function"""
    print("🚀 OANDA API Connection Test")
    print("=" * 40)

    async with OANDAConnectionTest() as tester:
        # Test authentication
        auth_ok = await tester.test_basic_authentication()

        if auth_ok:
            # If auth works, test additional endpoints
            await tester.test_instruments_access()
            await tester.test_market_prices()
            print("\n✅ All tests passed - OANDA API is working correctly!")
        else:
            print("\n❌ Authentication failed - check API credentials and account setup")

    print("\n" + "=" * 40)
    print("🔚 Test completed")

if __name__ == "__main__":
    asyncio.run(main())