#!/usr/bin/env python3
"""Debug authentication to see exact API response."""

import asyncio
import json
import sys
import urllib.parse

from aiohttp import ClientSession, ClientTimeout

API_BASE_URL = "https://app.muller-intuitiv.net"
CLIENT_ID = "59e604948fe283fd4dc7e355"
CLIENT_SECRET = "rAeWu8Y3YqXEPqRJ4BpFzFG98MRXpCcz"
USER_PREFIX = "muller"
SCOPE = "read_muller write_muller"


async def debug_auth(username: str, password: str):
    """Debug authentication with detailed logging."""
    print("🔍 DEBUG AUTHENTICATION")
    print("=" * 50)

    session = ClientSession(timeout=ClientTimeout(total=30))

    try:
        url = f"{API_BASE_URL}/oauth2/token"

        # Try different username formats
        username_variants = [
            username,  # Original
            username.lower(),  # Lowercase
            f"{USER_PREFIX}:{username}",  # With prefix
            username.replace("@", "%40"),  # URL encoded @
        ]

        for i, test_username in enumerate(username_variants, 1):
            print(f"\n🧪 Test {i}: Username format: '{test_username}'")

            payload = {
                "client_id": CLIENT_ID,
                "user_prefix": USER_PREFIX,
                "client_secret": CLIENT_SECRET,
                "grant_type": "password",
                "scope": SCOPE,
                "username": test_username,
                "password": password,
            }

            print(f"📤 Request URL: {url}")
            print(f"📤 Payload (password hidden):")
            debug_payload = {k: v if k != "password" else "*" * len(v) for k, v in payload.items()}
            print(json.dumps(debug_payload, indent=2))

            async with session.post(url, data=payload) as response:
                response_text = await response.text()

                print(f"📥 Response Status: {response.status}")
                print(f"📥 Response Headers:")
                for name, value in response.headers.items():
                    print(f"   {name}: {value}")

                print(f"📥 Response Body:")
                try:
                    response_json = json.loads(response_text)
                    print(json.dumps(response_json, indent=2))
                except json.JSONDecodeError:
                    print(response_text)

                if response.status == 200:
                    print(f"✅ SUCCESS with username format: {test_username}")
                    return True
                elif response.status == 400:
                    error_data = json.loads(response_text) if response_text.startswith("{") else {}
                    error = error_data.get("error", "unknown")
                    error_desc = error_data.get("error_description", "No description")
                    print(f"❌ FAILED: {error} - {error_desc}")
                else:
                    print(f"❌ FAILED: HTTP {response.status}")

        print(f"\n🚫 All username formats failed")
        return False

    finally:
        await session.close()


async def test_endpoint_variations():
    """Test different API endpoints that might work."""
    session = ClientSession(timeout=ClientTimeout(total=10))

    endpoints = [
        "https://app.muller-intuitiv.net/oauth2/token",
        "https://app.muller-intuitiv.net/oauth/token",
        "https://app.muller-intuitiv.net/api/oauth2/token",
        "https://api.muller-intuitiv.net/oauth2/token",
    ]

    print(f"\n🔍 TESTING ENDPOINT VARIATIONS")
    print("=" * 50)

    for endpoint in endpoints:
        try:
            print(f"\n🌐 Testing: {endpoint}")
            async with session.post(endpoint, data={"test": "test"}) as response:
                print(f"   Status: {response.status}")
                if response.status != 404:
                    text = await response.text()
                    print(f"   Response: {text[:100]}...")
        except Exception as e:
            print(f"   Error: {e}")

    await session.close()


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 debug_auth.py username password")
        return

    username = sys.argv[1]
    password = sys.argv[2]

    print(f"🔍 Debugging authentication for: {username}")
    print(f"🔒 Password length: {len(password)} characters")

    asyncio.run(debug_auth(username, password))
    asyncio.run(test_endpoint_variations())


if __name__ == "__main__":
    main()
