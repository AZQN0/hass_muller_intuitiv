#!/usr/bin/env python3
"""Test authentication with your Muller Intuitiv credentials."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.test_real_api import RealApiTester


async def test_with_credentials(username: str, password: str):
    """Test authentication with provided credentials."""
    print(f"🔐 Testing authentication for: {username}")
    print(f"🔒 Password: {'*' * len(password)}")

    async with RealApiTester(username, password) as tester:
        results = await tester.test_authentication_flow()
        success = tester.print_summary(results)

    return success


def main():
    """Main function to run the test."""
    # Check if credentials are provided as arguments
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    elif "MULLER_USERNAME" in os.environ and "MULLER_PASSWORD" in os.environ:
        username = os.environ["MULLER_USERNAME"]
        password = os.environ["MULLER_PASSWORD"]
    else:
        print("❌ Please provide credentials in one of these ways:")
        print("")
        print("1. Command line arguments:")
        print(f"   python3 {sys.argv[0]} your_email@example.com your_password")
        print("")
        print("2. Environment variables:")
        print("   export MULLER_USERNAME=your_email@example.com")
        print("   export MULLER_PASSWORD=your_password")
        print(f"   python3 {sys.argv[0]}")
        print("")
        print("⚠️ Note: Your credentials will be used to test the authentication")
        print("   fixes against the real Muller Intuitiv API.")
        return False

    try:
        success = asyncio.run(test_with_credentials(username, password))
        return success
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
