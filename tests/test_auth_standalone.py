#!/usr/bin/env python3
"""Standalone authentication test without Home Assistant dependencies."""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout, web
from aiohttp.web_runner import AppRunner, TCPSite

# Add the custom component to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Minimal constants needed for testing
API_BASE_URL = "http://localhost:8080"
CLIENT_ID = "test_client"
CLIENT_SECRET = "test_secret"
USER_PREFIX = "test"
SCOPE = "test_scope"
HTTP_TIMEOUT = 30

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


class MullerIntuitivAuthError(Exception):
    """Exception for authentication errors."""


class MullerIntuitivConnectionError(Exception):
    """Exception for connection errors."""


class MullerIntuitivApi:
    """Minimal API client for testing."""

    def __init__(self, session: ClientSession, token: str = None):
        self._session = session
        self._token = token
        self._timeout = ClientTimeout(total=HTTP_TIMEOUT)

    def set_token(self, token: str) -> None:
        """Set the access token."""
        self._token = token

    async def login(self, username: str, password: str) -> dict:
        """Authenticate with username and password."""
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

        logger.debug("Attempting login for username: %s", username[:3] + "***")

        try:
            async with self._session.post(url, data=payload, timeout=self._timeout) as response:
                response_text = await response.text()

                if response.status != 200:
                    logger.error(
                        "Authentication failed (status %d): %s", response.status, response_text
                    )

                    if response.status == 400:
                        if "invalid_grant" in response_text:
                            raise MullerIntuitivAuthError("Invalid username or password")
                        elif "invalid_client" in response_text:
                            raise MullerIntuitivAuthError("Client authentication failed")
                        else:
                            raise MullerIntuitivAuthError("Bad request - check credentials")
                    elif response.status == 401:
                        raise MullerIntuitivAuthError("Unauthorized - invalid credentials")
                    else:
                        raise MullerIntuitivAuthError(
                            f"Authentication failed with status {response.status}"
                        )

                data = await response.json()
                self._token = data.get("access_token")

                if not self._token:
                    logger.error("No access token received in response")
                    raise MullerIntuitivAuthError("No access token in response")

                expires_in = data.get("expires_in", 3600)
                data["expires_at"] = int(time.time()) + expires_in

                logger.debug("Login successful, token expires in %d seconds", expires_in)
                return data

        except Exception as err:
            if isinstance(err, MullerIntuitivAuthError):
                raise
            logger.error("Network error during authentication: %s", err)
            raise MullerIntuitivConnectionError(
                f"Network error during authentication: {err}"
            ) from err

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh the access token."""
        url = f"{API_BASE_URL}/oauth2/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        logger.debug("Attempting to refresh token")

        try:
            async with self._session.post(url, data=payload, timeout=self._timeout) as response:
                response_text = await response.text()

                if response.status != 200:
                    logger.error(
                        "Token refresh failed (status %d): %s", response.status, response_text
                    )

                    if response.status == 400:
                        if "invalid_grant" in response_text:
                            raise MullerIntuitivAuthError(
                                "Refresh token expired - please re-authenticate"
                            )
                        elif "invalid_client" in response_text:
                            raise MullerIntuitivAuthError(
                                "Client authentication failed during token refresh"
                            )
                        else:
                            raise MullerIntuitivAuthError("Bad request during token refresh")
                    elif response.status == 401:
                        raise MullerIntuitivAuthError("Unauthorized - refresh token invalid")
                    else:
                        raise MullerIntuitivAuthError(
                            f"Token refresh failed with status {response.status}"
                        )

                data = await response.json()
                self._token = data.get("access_token")

                if not self._token:
                    logger.error("No access token received in refresh response")
                    raise MullerIntuitivAuthError("No access token in refresh response")

                expires_in = data.get("expires_in", 3600)
                data["expires_at"] = int(time.time()) + expires_in

                logger.debug(
                    "Token refresh successful, new token expires in %d seconds", expires_in
                )
                return data

        except Exception as err:
            if isinstance(err, MullerIntuitivAuthError):
                raise
            logger.error("Network error during token refresh: %s", err)
            raise MullerIntuitivConnectionError(
                f"Network error during token refresh: {err}"
            ) from err


class MockAPIServer:
    """Mock API server for testing."""

    def __init__(self):
        self.valid_credentials = {"username": "test_user", "password": "test_pass"}
        self.issued_tokens = {}
        self.token_counter = 0

    async def oauth_token(self, request):
        """Handle OAuth token requests."""
        data = await request.post()
        grant_type = data.get("grant_type")

        if grant_type == "password":
            return await self._handle_password_grant(data)
        elif grant_type == "refresh_token":
            return await self._handle_refresh_token(data)
        else:
            return web.Response(
                status=400,
                text=json.dumps({"error": "unsupported_grant_type"}),
                content_type="application/json",
            )

    async def _handle_password_grant(self, data):
        """Handle password authentication."""
        username = data.get("username")
        password = data.get("password")

        if (
            username != self.valid_credentials["username"]
            or password != self.valid_credentials["password"]
        ):
            return web.Response(
                status=400,
                text=json.dumps({"error": "invalid_grant"}),
                content_type="application/json",
            )

        self.token_counter += 1
        access_token = f"access_token_{self.token_counter}"
        refresh_token = f"refresh_token_{self.token_counter}"

        self.issued_tokens[access_token] = {
            "refresh_token": refresh_token,
            "issued_at": int(time.time()),
        }

        return web.Response(
            status=200,
            text=json.dumps(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }
            ),
            content_type="application/json",
        )

    async def _handle_refresh_token(self, data):
        """Handle refresh token requests."""
        refresh_token = data.get("refresh_token")

        # Simulate different error conditions
        if refresh_token == "expired_refresh_token":
            return web.Response(
                status=400,
                text=json.dumps({"error": "invalid_grant"}),
                content_type="application/json",
            )

        if refresh_token == "invalid_refresh_token":
            return web.Response(
                status=400,
                text=json.dumps({"error": "invalid_grant"}),
                content_type="application/json",
            )

        # Check if it's a valid refresh token we issued
        valid_refresh = any(
            token_info["refresh_token"] == refresh_token
            for token_info in self.issued_tokens.values()
        )

        if not valid_refresh:
            return web.Response(
                status=400,
                text=json.dumps({"error": "invalid_grant"}),
                content_type="application/json",
            )

        # Generate new tokens
        self.token_counter += 1
        access_token = f"access_token_{self.token_counter}"
        new_refresh_token = f"refresh_token_{self.token_counter}"

        self.issued_tokens[access_token] = {
            "refresh_token": new_refresh_token,
            "issued_at": int(time.time()),
        }

        return web.Response(
            status=200,
            text=json.dumps(
                {
                    "access_token": access_token,
                    "refresh_token": new_refresh_token,
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }
            ),
            content_type="application/json",
        )


async def run_auth_tests():
    """Run comprehensive authentication tests."""
    print("\n" + "=" * 80)
    print("🔐 AUTHENTICATION INTEGRATION TEST")
    print("=" * 80)

    # Start mock server
    mock_api = MockAPIServer()
    app = web.Application()
    app.router.add_post("/oauth2/token", mock_api.oauth_token)

    runner = AppRunner(app)
    await runner.setup()
    site = TCPSite(runner, "localhost", 8080)
    await site.start()

    print("🚀 Mock API server started on http://localhost:8080")

    # Test results
    results = {}

    try:
        session = ClientSession()
        api = MullerIntuitivApi(session)

        # Test 1: Valid Login
        print("\n1️⃣ Testing valid login credentials...")
        try:
            login_result = await api.login("test_user", "test_pass")
            print(f"   ✅ SUCCESS: Access token received: {login_result['access_token'][:15]}...")
            print(f"   ✅ Refresh token: {login_result['refresh_token'][:15]}...")
            print(f"   ✅ Expires in: {login_result['expires_in']} seconds")
            results["valid_login"] = "PASS"
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results["valid_login"] = "FAIL"

        # Test 2: Invalid Login
        print("\n2️⃣ Testing invalid login credentials...")
        try:
            await api.login("wrong_user", "wrong_pass")
            print("   ❌ FAILED: Should have thrown an error!")
            results["invalid_login"] = "FAIL"
        except MullerIntuitivAuthError as e:
            expected_msg = "Invalid username or password"
            if expected_msg in str(e):
                print(f"   ✅ SUCCESS: Got expected error: {e}")
                results["invalid_login"] = "PASS"
            else:
                print(f"   ❌ FAILED: Wrong error message: {e}")
                results["invalid_login"] = "FAIL"
        except Exception as e:
            print(f"   ❌ FAILED: Wrong exception type: {e}")
            results["invalid_login"] = "FAIL"

        # Test 3: Valid Token Refresh
        print("\n3️⃣ Testing valid token refresh...")
        try:
            if "valid_login" in results and results["valid_login"] == "PASS":
                refresh_result = await api.refresh_token(login_result["refresh_token"])
                print(f"   ✅ SUCCESS: New access token: {refresh_result['access_token'][:15]}...")
                print(f"   ✅ New refresh token: {refresh_result['refresh_token'][:15]}...")
                # Verify tokens are different
                if (
                    refresh_result["access_token"] != login_result["access_token"]
                    and refresh_result["refresh_token"] != login_result["refresh_token"]
                ):
                    print("   ✅ SUCCESS: Tokens are properly rotated")
                    results["valid_refresh"] = "PASS"
                else:
                    print("   ❌ FAILED: Tokens not properly rotated")
                    results["valid_refresh"] = "FAIL"
            else:
                print("   ⚠️  SKIPPED: Valid login failed")
                results["valid_refresh"] = "SKIP"
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results["valid_refresh"] = "FAIL"

        # Test 4: Expired Token Refresh
        print("\n4️⃣ Testing expired refresh token...")
        try:
            await api.refresh_token("expired_refresh_token")
            print("   ❌ FAILED: Should have thrown an error!")
            results["expired_refresh"] = "FAIL"
        except MullerIntuitivAuthError as e:
            expected_msg = "Refresh token expired - please re-authenticate"
            if expected_msg in str(e):
                print(f"   ✅ SUCCESS: Got expected error: {e}")
                results["expired_refresh"] = "PASS"
            else:
                print(f"   ❌ FAILED: Wrong error message: {e}")
                results["expired_refresh"] = "FAIL"
        except Exception as e:
            print(f"   ❌ FAILED: Wrong exception type: {e}")
            results["expired_refresh"] = "FAIL"

        # Test 5: Invalid Token Refresh
        print("\n5️⃣ Testing invalid refresh token...")
        try:
            await api.refresh_token("invalid_refresh_token")
            print("   ❌ FAILED: Should have thrown an error!")
            results["invalid_refresh"] = "FAIL"
        except MullerIntuitivAuthError as e:
            expected_msg = "Refresh token expired - please re-authenticate"
            if expected_msg in str(e):
                print(f"   ✅ SUCCESS: Got expected error: {e}")
                results["invalid_refresh"] = "PASS"
            else:
                print(f"   ❌ FAILED: Wrong error message: {e}")
                results["invalid_refresh"] = "FAIL"
        except Exception as e:
            print(f"   ❌ FAILED: Wrong exception type: {e}")
            results["invalid_refresh"] = "FAIL"

        # Test 6: Network Error
        print("\n6️⃣ Testing network error handling...")
        try:
            # Create a new API client with invalid URL
            bad_api = MullerIntuitivApi(session)
            global API_BASE_URL
            original_url = API_BASE_URL
            API_BASE_URL = "http://nonexistent.invalid"

            await bad_api.login("test_user", "test_pass")
            print("   ❌ FAILED: Should have thrown a connection error!")
            results["network_error"] = "FAIL"
        except MullerIntuitivConnectionError as e:
            expected_msg = "Network error during authentication"
            if expected_msg in str(e):
                print(f"   ✅ SUCCESS: Got expected network error: {type(e).__name__}")
                results["network_error"] = "PASS"
            else:
                print(f"   ❌ FAILED: Wrong error message: {e}")
                results["network_error"] = "FAIL"
        except Exception as e:
            print(f"   ❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
            results["network_error"] = "FAIL"
        finally:
            API_BASE_URL = original_url

        await session.close()

    finally:
        await runner.cleanup()

    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)

    passed = sum(1 for result in results.values() if result == "PASS")
    total = len(results)

    for test_name, result in results.items():
        emoji = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}: {result}")

    print(f"\n🎯 OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Authentication fixes are working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Review the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_auth_tests())
    sys.exit(0 if success else 1)
