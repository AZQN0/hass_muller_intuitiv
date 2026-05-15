"""Integration test for authentication fixes."""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

pytestmark = pytest.mark.enable_socket

# Add the custom component to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from muller_intuitiv.api import (
    MullerIntuitivApi,
    MullerIntuitivAuthError,
    MullerIntuitivConnectionError,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockMullerAPI:
    """Mock Muller Intuitiv API server for testing."""

    def __init__(self):
        self.valid_credentials = {"username": "test_user", "password": "test_pass"}
        self.valid_refresh_token = "valid_refresh_token"
        self.expired_refresh_token = "expired_refresh_token"
        self.invalid_refresh_token = "invalid_refresh_token"

        # Track issued tokens
        self.issued_tokens = {}
        self.token_counter = 0

    async def oauth_token(self, request):
        """Handle OAuth token requests."""
        data = await request.post()
        grant_type = data.get("grant_type")

        logger.info(f"Token request: grant_type={grant_type}")

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
        """Handle password grant authentication."""
        username = data.get("username")
        password = data.get("password")

        logger.info(f"Password grant attempt: username={username}")

        # Simulate invalid credentials
        if (
            username != self.valid_credentials["username"]
            or password != self.valid_credentials["password"]
        ):
            logger.error(f"Invalid credentials: {username}")
            return web.Response(
                status=400,
                text=json.dumps({"error": "invalid_grant"}),
                content_type="application/json",
            )

        # Generate tokens
        self.token_counter += 1
        access_token = f"access_token_{self.token_counter}"
        refresh_token = f"refresh_token_{self.token_counter}"

        self.issued_tokens[access_token] = {
            "refresh_token": refresh_token,
            "issued_at": int(time.time()),
        }

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        logger.info(f"Password grant successful: token={access_token[:10]}...")
        return web.Response(
            status=200, text=json.dumps(response_data), content_type="application/json"
        )

    async def _handle_refresh_token(self, data):
        """Handle refresh token requests."""
        refresh_token = data.get("refresh_token")

        logger.info(f"Refresh token attempt: token={refresh_token}")

        # Simulate expired refresh token
        if refresh_token == self.expired_refresh_token:
            logger.error("Refresh token expired")
            return web.Response(
                status=400,
                text=json.dumps({"error": "invalid_grant"}),
                content_type="application/json",
            )

        # Simulate invalid refresh token
        if refresh_token == self.invalid_refresh_token:
            logger.error("Invalid refresh token")
            return web.Response(
                status=400,
                text=json.dumps({"error": "invalid_grant"}),
                content_type="application/json",
            )

        # Check if it's a valid refresh token we issued
        valid_refresh = False
        for token_info in self.issued_tokens.values():
            if token_info["refresh_token"] == refresh_token:
                valid_refresh = True
                break

        if not valid_refresh and refresh_token != self.valid_refresh_token:
            logger.error(f"Unknown refresh token: {refresh_token}")
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

        response_data = {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        logger.info(f"Refresh token successful: token={access_token[:10]}...")
        return web.Response(
            status=200, text=json.dumps(response_data), content_type="application/json"
        )

    async def api_homesdata(self, request):
        """Mock homes data endpoint."""
        return web.Response(
            status=200,
            text=json.dumps({"body": {"homes": [{"id": "test_home_id", "name": "Test Home"}]}}),
            content_type="application/json",
        )


class AuthIntegrationTest(AioHTTPTestCase):
    """Integration test for authentication functionality."""

    async def get_application(self):
        """Create the test application with mock API."""
        self.mock_api = MockMullerAPI()

        app = web.Application()
        app.router.add_post("/oauth2/token", self.mock_api.oauth_token)
        app.router.add_post("/api/homesdata", self.mock_api.api_homesdata)
        return app

    async def get_api_client(self) -> MullerIntuitivApi:
        """Get an API client configured to use the test server."""
        session = ClientSession()
        # Override the API base URL to point to our test server
        api = MullerIntuitivApi(session)
        # Monkey patch the API_BASE_URL
        import muller_intuitiv.api as api_module

        self.original_base_url = api_module.API_BASE_URL
        api_module.API_BASE_URL = f"http://{self.server.host}:{self.server.port}"
        return api

    async def asyncTearDown(self):
        """Clean up after tests."""
        # Restore original API URL
        if hasattr(self, "original_base_url"):
            import muller_intuitiv.api as api_module

            api_module.API_BASE_URL = self.original_base_url
        await super().asyncTearDown()

    @unittest_run_loop
    async def test_successful_authentication(self):
        """Test successful login with valid credentials."""
        api = await self.get_api_client()

        try:
            result = await api.login("test_user", "test_pass")

            self.assertIn("access_token", result)
            self.assertIn("refresh_token", result)
            self.assertIn("expires_in", result)
            self.assertIn("expires_at", result)
            self.assertEqual(result["expires_in"], 3600)

            logger.info("✅ Successful authentication test passed")

        finally:
            await api._session.close()

    @unittest_run_loop
    async def test_invalid_credentials_error_handling(self):
        """Test error handling for invalid credentials."""
        api = await self.get_api_client()

        try:
            with self.assertRaises(MullerIntuitivAuthError) as context:
                await api.login("wrong_user", "wrong_pass")

            # Verify the error message is user-friendly
            error_msg = str(context.exception)
            self.assertIn("Invalid username or password", error_msg)

            logger.info("✅ Invalid credentials error handling test passed")

        finally:
            await api._session.close()

    @unittest_run_loop
    async def test_successful_token_refresh(self):
        """Test successful token refresh."""
        api = await self.get_api_client()

        try:
            # First login to get a refresh token
            login_result = await api.login("test_user", "test_pass")
            refresh_token = login_result["refresh_token"]

            # Now test token refresh
            refresh_result = await api.refresh_token(refresh_token)

            self.assertIn("access_token", refresh_result)
            self.assertIn("refresh_token", refresh_result)
            self.assertIn("expires_in", refresh_result)
            self.assertIn("expires_at", refresh_result)

            # Tokens should be different
            self.assertNotEqual(login_result["access_token"], refresh_result["access_token"])
            self.assertNotEqual(login_result["refresh_token"], refresh_result["refresh_token"])

            logger.info("✅ Successful token refresh test passed")

        finally:
            await api._session.close()

    @unittest_run_loop
    async def test_expired_refresh_token_error_handling(self):
        """Test error handling for expired refresh token."""
        api = await self.get_api_client()

        try:
            with self.assertRaises(MullerIntuitivAuthError) as context:
                await api.refresh_token("expired_refresh_token")

            # Verify the error message indicates re-authentication is needed
            error_msg = str(context.exception)
            self.assertIn("Refresh token expired - please re-authenticate", error_msg)

            logger.info("✅ Expired refresh token error handling test passed")

        finally:
            await api._session.close()

    @unittest_run_loop
    async def test_invalid_refresh_token_error_handling(self):
        """Test error handling for invalid refresh token."""
        api = await self.get_api_client()

        try:
            with self.assertRaises(MullerIntuitivAuthError) as context:
                await api.refresh_token("invalid_refresh_token")

            # Verify the error message indicates re-authentication is needed
            error_msg = str(context.exception)
            self.assertIn("Refresh token expired - please re-authenticate", error_msg)

            logger.info("✅ Invalid refresh token error handling test passed")

        finally:
            await api._session.close()

    @unittest_run_loop
    async def test_network_error_handling(self):
        """Test network error handling during authentication."""
        # Create API client with invalid URL to simulate network error
        session = ClientSession()
        api = MullerIntuitivApi(session)

        # Override with invalid URL
        import muller_intuitiv.api as api_module

        api_module.API_BASE_URL = "http://nonexistent.invalid"

        try:
            with self.assertRaises(MullerIntuitivConnectionError) as context:
                await api.login("test_user", "test_pass")

            error_msg = str(context.exception)
            self.assertIn("Network error during authentication", error_msg)

            logger.info("✅ Network error handling test passed")

        finally:
            await session.close()


async def run_manual_test():
    """Run a manual test to demonstrate the authentication fixes."""
    print("\n" + "=" * 60)
    print("🧪 MANUAL AUTHENTICATION TEST")
    print("=" * 60)

    # Start a mock server
    mock_api = MockMullerAPI()

    app = web.Application()
    app.router.add_post("/oauth2/token", mock_api.oauth_token)
    app.router.add_post("/api/homesdata", mock_api.api_homesdata)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    await site.start()

    print("🚀 Mock API server started on http://localhost:8080")

    try:
        session = ClientSession()
        api = MullerIntuitivApi(session)

        # Override API base URL
        import muller_intuitiv.api as api_module

        original_url = api_module.API_BASE_URL
        api_module.API_BASE_URL = "http://localhost:8080"

        print("\n📋 Test Cases:")

        # Test 1: Valid credentials
        print("\n1️⃣ Testing valid credentials...")
        try:
            result = await api.login("test_user", "test_pass")
            print(f"   ✅ SUCCESS: Got access token: {result['access_token'][:20]}...")
            print(f"   ✅ Token expires in: {result['expires_in']} seconds")

            # Test token refresh with valid token
            print("\n2️⃣ Testing valid token refresh...")
            refresh_result = await api.refresh_token(result["refresh_token"])
            print(
                f"   ✅ SUCCESS: Refreshed to new token: {refresh_result['access_token'][:20]}..."
            )

        except Exception as e:
            print(f"   ❌ FAILED: {e}")

        # Test 2: Invalid credentials
        print("\n3️⃣ Testing invalid credentials...")
        try:
            await api.login("wrong_user", "wrong_pass")
            print("   ❌ UNEXPECTED: Should have failed!")
        except MullerIntuitivAuthError as e:
            print(f"   ✅ SUCCESS: Got expected error: {e}")
        except Exception as e:
            print(f"   ❌ FAILED: Wrong error type: {e}")

        # Test 3: Expired refresh token
        print("\n4️⃣ Testing expired refresh token...")
        try:
            await api.refresh_token("expired_refresh_token")
            print("   ❌ UNEXPECTED: Should have failed!")
        except MullerIntuitivAuthError as e:
            print(f"   ✅ SUCCESS: Got expected error: {e}")
        except Exception as e:
            print(f"   ❌ FAILED: Wrong error type: {e}")

        # Test 4: Invalid refresh token
        print("\n5️⃣ Testing invalid refresh token...")
        try:
            await api.refresh_token("invalid_refresh_token")
            print("   ❌ UNEXPECTED: Should have failed!")
        except MullerIntuitivAuthError as e:
            print(f"   ✅ SUCCESS: Got expected error: {e}")
        except Exception as e:
            print(f"   ❌ FAILED: Wrong error type: {e}")

        print("\n" + "=" * 60)
        print("🎉 MANUAL TEST COMPLETED")
        print("=" * 60)

        # Restore original URL
        api_module.API_BASE_URL = original_url
        await session.close()

    finally:
        await runner.cleanup()


if __name__ == "__main__":
    # Run manual test if executed directly
    asyncio.run(run_manual_test())
