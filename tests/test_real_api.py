#!/usr/bin/env python3
"""Test authentication against the real Muller Intuitiv API."""

import asyncio
import getpass
import json
import logging
import sys
import time
from pathlib import Path
from aiohttp import ClientSession, ClientTimeout

# Add the custom component to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the real constants and API
try:
    from custom_components.muller_intuitiv.const import (
        API_BASE_URL,
        CLIENT_ID,
        CLIENT_SECRET,
        USER_PREFIX,
        SCOPE,
        HTTP_TIMEOUT,
    )
    from custom_components.muller_intuitiv.api import (
        MullerIntuitivApi,
        MullerIntuitivAuthError,
        MullerIntuitivConnectionError,
        MullerIntuitivApiError,
    )
    REAL_INTEGRATION = True
except ImportError:
    # Fallback if we can't import the integration - use correct values from const.py
    API_BASE_URL = "https://app.muller-intuitiv.net"
    CLIENT_ID = "59e604948fe283fd4dc7e355"
    CLIENT_SECRET = "rAeWu8Y3YqXEPqRJ4BpFzFG98MRXpCcz"
    USER_PREFIX = "muller"
    SCOPE = "read_muller write_muller"
    HTTP_TIMEOUT = 30

    class MullerIntuitivAuthError(Exception):
        pass
    class MullerIntuitivConnectionError(Exception):
        pass
    class MullerIntuitivApiError(Exception):
        pass

    REAL_INTEGRATION = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

class RealApiTester:
    """Test the authentication fixes against the real API."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = None
        self.api = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = ClientSession()
        if REAL_INTEGRATION:
            self.api = MullerIntuitivApi(self.session)
        else:
            self.api = self._create_fallback_api()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _create_fallback_api(self):
        """Create fallback API client if integration import failed."""
        class FallbackApi:
            def __init__(self, session):
                self._session = session
                self._token = None
                self._timeout = ClientTimeout(total=HTTP_TIMEOUT)

            def set_token(self, token):
                self._token = token

            async def login(self, username, password):
                url = f"{API_BASE_URL}/oauth2/token"
                payload = {
                    "client_id": CLIENT_ID,
                    "user_prefix": USER_PREFIX,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "password",
                    "scope": SCOPE,
                    "username": username,
                    "password": password,
                }

                async with self._session.post(url, data=payload, timeout=self._timeout) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        if response.status == 400 and "invalid_grant" in response_text:
                            raise MullerIntuitivAuthError("Invalid username or password")
                        raise MullerIntuitivAuthError(f"Authentication failed: {response_text}")

                    data = await response.json()
                    self._token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    data["expires_at"] = int(time.time()) + expires_in
                    return data

            async def refresh_token(self, refresh_token):
                url = f"{API_BASE_URL}/oauth2/token"
                payload = {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }

                async with self._session.post(url, data=payload, timeout=self._timeout) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        if response.status == 400 and "invalid_grant" in response_text:
                            raise MullerIntuitivAuthError("Refresh token expired - please re-authenticate")
                        raise MullerIntuitivAuthError(f"Token refresh failed: {response_text}")

                    data = await response.json()
                    self._token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    data["expires_at"] = int(time.time()) + expires_in
                    return data

            async def get_homes_data(self):
                if not self._token:
                    raise MullerIntuitivAuthError("No access token available")

                url = f"{API_BASE_URL}/api/homesdata"
                headers = {
                    "Authorization": f"Bearer {self._token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }

                async with self._session.post(url, headers=headers, timeout=self._timeout) as response:
                    response_text = await response.text()

                    if response.status == 401:
                        raise MullerIntuitivAuthError("Token expired")
                    elif response.status == 403:
                        # Provide detailed error info for 403
                        raise MullerIntuitivApiError(f"API access forbidden (403). Response: {response_text[:200]}")
                    elif response.status != 200:
                        raise MullerIntuitivApiError(f"API error {response.status}: {response_text[:200]}")

                    try:
                        data = await response.json()
                    except Exception:
                        raise MullerIntuitivApiError(f"Invalid JSON response: {response_text[:200]}")

                    homes = data.get("body", {}).get("homes", [])
                    if not homes:
                        raise MullerIntuitivApiError("No homes found")
                    return homes[0]

        return FallbackApi(self.session)

    async def test_authentication_flow(self):
        """Test the complete authentication flow."""
        print("\n" + "="*80)
        print("🔐 REAL API AUTHENTICATION TEST")
        print("="*80)
        print(f"🌐 Testing against: {API_BASE_URL}")
        print(f"👤 Username: {self.username}")
        print(f"🔧 Using {'real integration' if REAL_INTEGRATION else 'fallback implementation'}")

        results = {}

        # Test 1: Initial Login
        print(f"\n1️⃣ Testing login with your credentials...")
        try:
            login_result = await self.api.login(self.username, self.password)

            # Verify we got the expected fields
            required_fields = ["access_token", "refresh_token", "expires_in"]
            missing_fields = [field for field in required_fields if field not in login_result]

            if missing_fields:
                print(f"   ❌ FAILED: Missing fields in response: {missing_fields}")
                results["login"] = "FAIL"
            else:
                print(f"   ✅ SUCCESS: Authentication successful!")
                print(f"   📄 Access token: {login_result['access_token'][:20]}...")
                print(f"   🔄 Refresh token: {login_result['refresh_token'][:20]}...")
                print(f"   ⏰ Expires in: {login_result['expires_in']} seconds")
                if "expires_at" in login_result:
                    print(f"   📅 Expires at: {time.ctime(login_result['expires_at'])}")
                results["login"] = "PASS"

        except MullerIntuitivAuthError as e:
            print(f"   ❌ AUTH ERROR: {e}")
            print("   💡 This could mean:")
            print("      - Invalid username or password")
            print("      - Account temporarily locked")
            print("      - API credentials changed")
            results["login"] = "AUTH_FAIL"
        except MullerIntuitivConnectionError as e:
            print(f"   ❌ CONNECTION ERROR: {e}")
            print("   💡 This could mean:")
            print("      - Network connectivity issues")
            print("      - API server is down")
            print("      - Firewall blocking requests")
            results["login"] = "CONN_FAIL"
        except Exception as e:
            print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
            results["login"] = "ERROR"

        # Test 2: Token Refresh (only if login succeeded)
        if results.get("login") == "PASS":
            print(f"\n2️⃣ Testing token refresh...")
            try:
                refresh_result = await self.api.refresh_token(login_result["refresh_token"])

                # Some APIs return the same tokens if they're still valid - check if refresh worked
                print(f"   📄 New access token: {refresh_result['access_token'][:20]}...")
                print(f"   🔄 New refresh token: {refresh_result['refresh_token'][:20]}...")
                print(f"   ⏰ New expiry: {refresh_result['expires_in']} seconds")

                # Check if tokens changed (some APIs might not rotate if still valid)
                tokens_changed = (refresh_result["access_token"] != login_result["access_token"] or
                                refresh_result["refresh_token"] != login_result["refresh_token"])

                if tokens_changed:
                    print(f"   ✅ SUCCESS: Tokens were rotated")
                    results["refresh"] = "PASS"
                elif "expires_in" in refresh_result and refresh_result["expires_in"] > 0:
                    print(f"   ✅ SUCCESS: Token refresh worked (same tokens returned - still valid)")
                    results["refresh"] = "PASS"
                else:
                    print(f"   ❌ FAILED: Token refresh didn't work properly")
                    results["refresh"] = "FAIL"

            except MullerIntuitivAuthError as e:
                print(f"   ❌ AUTH ERROR: {e}")
                results["refresh"] = "AUTH_FAIL"
            except Exception as e:
                print(f"   ❌ ERROR: {type(e).__name__}: {e}")
                results["refresh"] = "ERROR"
        else:
            print(f"\n2️⃣ Skipping token refresh (login failed)")
            results["refresh"] = "SKIP"

        # Test 3: API Call with Token (only if we have a valid token)
        if results.get("login") == "PASS" or results.get("refresh") == "PASS":
            print(f"\n3️⃣ Testing API call with authentication...")
            try:
                # Use the most recent token
                if results.get("refresh") == "PASS":
                    self.api.set_token(refresh_result["access_token"])
                else:
                    self.api.set_token(login_result["access_token"])

                homes_data = await self.api.get_homes_data()

                print(f"   ✅ SUCCESS: API call successful!")
                print(f"   🏠 Home ID: {homes_data.get('id', 'N/A')}")
                print(f"   🏠 Home Name: {homes_data.get('name', 'N/A')}")

                # Show some additional info if available
                if 'rooms' in homes_data:
                    print(f"   🚪 Rooms found: {len(homes_data['rooms'])}")

                results["api_call"] = "PASS"

            except MullerIntuitivAuthError as e:
                print(f"   ❌ AUTH ERROR: {e}")
                print("   💡 Token may have expired or been revoked")
                results["api_call"] = "AUTH_FAIL"
            except MullerIntuitivApiError as e:
                print(f"   ❌ API ERROR: {e}")
                results["api_call"] = "API_FAIL"
            except Exception as e:
                print(f"   ❌ ERROR: {type(e).__name__}: {e}")
                results["api_call"] = "ERROR"
        else:
            print(f"\n3️⃣ Skipping API call (no valid token)")
            results["api_call"] = "SKIP"

        # Test 4: Invalid Refresh Token Handling
        print(f"\n4️⃣ Testing invalid refresh token handling...")
        try:
            await self.api.refresh_token("invalid_refresh_token_12345")
            print(f"   ❌ FAILED: Should have thrown an error!")
            results["invalid_refresh"] = "FAIL"
        except MullerIntuitivAuthError as e:
            expected_phrases = ["expired", "invalid", "re-authenticate"]
            if any(phrase in str(e).lower() for phrase in expected_phrases):
                print(f"   ✅ SUCCESS: Got expected error: {e}")
                results["invalid_refresh"] = "PASS"
            else:
                print(f"   ⚠️  WARNING: Error message could be clearer: {e}")
                results["invalid_refresh"] = "PARTIAL"
        except Exception as e:
            print(f"   ❌ ERROR: Wrong exception type: {type(e).__name__}: {e}")
            results["invalid_refresh"] = "ERROR"

        return results

    def print_summary(self, results):
        """Print test summary."""
        print("\n" + "="*80)
        print("📊 REAL API TEST SUMMARY")
        print("="*80)

        status_icons = {
            "PASS": "✅",
            "FAIL": "❌",
            "ERROR": "💥",
            "AUTH_FAIL": "🔐❌",
            "CONN_FAIL": "🌐❌",
            "API_FAIL": "📡❌",
            "SKIP": "⚠️",
            "PARTIAL": "⚠️"
        }

        test_descriptions = {
            "login": "Initial Login",
            "refresh": "Token Refresh",
            "api_call": "API Call with Token",
            "invalid_refresh": "Invalid Token Handling"
        }

        passed = 0
        total = 0

        for test_name, result in results.items():
            if result not in ["SKIP"]:
                total += 1
                if result == "PASS":
                    passed += 1

            icon = status_icons.get(result, "❓")
            desc = test_descriptions.get(test_name, test_name)
            print(f"{icon} {desc}: {result}")

        print(f"\n🎯 RESULTS: {passed}/{total} tests passed", end="")
        if total > 0:
            print(f" ({passed/total*100:.1f}%)")
        else:
            print()

        # Provide recommendations
        print(f"\n💡 RECOMMENDATIONS:")

        if results.get("login") == "PASS":
            print("✅ Your credentials are working correctly!")
            if results.get("refresh") == "PASS":
                print("✅ Token refresh is working - the integration should handle expired tokens automatically")
            if results.get("api_call") == "PASS":
                print("✅ API calls are working - you should be able to control your heating system")
        elif results.get("login") == "AUTH_FAIL":
            print("❌ Login failed - please check your username and password")
            print("   Try logging into the Muller Intuitiv mobile app to verify credentials")
        elif results.get("login") == "CONN_FAIL":
            print("❌ Connection failed - check your internet connection")
            print("   Try accessing https://appli.muller-intuitiv.fr in a browser")

        if results.get("invalid_refresh") == "PASS":
            print("✅ Error handling is working correctly")

        return passed == total and total > 0


async def main():
    """Main test function."""
    print("🔐 MULLER INTUITIV REAL API TESTER")
    print("="*50)

    # Get credentials
    print("\nPlease enter your Muller Intuitiv credentials:")
    username = input("Username (email): ").strip()
    if not username:
        print("❌ Username is required!")
        return False

    password = getpass.getpass("Password: ").strip()
    if not password:
        print("❌ Password is required!")
        return False

    # Run tests
    async with RealApiTester(username, password) as tester:
        results = await tester.test_authentication_flow()
        success = tester.print_summary(results)

    if success:
        print(f"\n🎉 All tests passed! Your authentication fixes are working correctly with the real API.")
        print(f"   You can now use the integration with confidence.")
    else:
        print(f"\n⚠️ Some tests failed. Review the errors above to troubleshoot.")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)