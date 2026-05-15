#!/usr/bin/env python3
"""Minimal authentication test to debug the issue."""

import asyncio
import json
import sys

from aiohttp import ClientSession, ClientTimeout


async def test_minimal_auth(username: str, password: str):
    """Minimal test to see exact API behavior."""
    session = ClientSession(timeout=ClientTimeout(total=30))

    try:
        url = "https://app.muller-intuitiv.net/oauth2/token"

        payload = {
            "client_id": "59e604948fe283fd4dc7e355",
            "user_prefix": "muller",
            "client_secret": "rAeWu8Y3YqXEPqRJ4BpFzFG98MRXpCcz",
            "grant_type": "password",
            "scope": "read_muller write_muller",
            "username": username,
            "password": password,
        }

        print("🔐 MINIMAL AUTH TEST")
        print("=" * 40)
        print(f"URL: {url}")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password)}")

        async with session.post(url, data=payload) as response:
            text = await response.text()

            print(f"\nStatus: {response.status}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {text}")

            if response.status == 200:
                try:
                    data = json.loads(text)
                    print("\n✅ SUCCESS!")
                    print(f"Access Token: {data.get('access_token', 'N/A')[:20]}...")
                    print(f"Refresh Token: {data.get('refresh_token', 'N/A')[:20]}...")
                    print(f"Expires In: {data.get('expires_in', 'N/A')}")
                    return True
                except json.JSONDecodeError:
                    print("❌ Invalid JSON response")
                    return False
            else:
                print("❌ FAILED")
                return False

    finally:
        await session.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 minimal_auth_test.py username password")
        sys.exit(1)

    success = asyncio.run(test_minimal_auth(sys.argv[1], sys.argv[2]))
    print(f"\n{'SUCCESS' if success else 'FAILED'}")
