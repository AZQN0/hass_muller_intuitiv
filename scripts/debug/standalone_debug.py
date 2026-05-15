#!/usr/bin/env python3
"""Standalone debug script to test API data flow"""

import asyncio
import json
import sys
import time

import aiohttp

# Constants from the integration (CORRECTED)
API_BASE_URL = "https://app.muller-intuitiv.net"
CLIENT_ID = "59e604948fe283fd4dc7e355"
CLIENT_SECRET = "rAeWu8Y3YqXEPqRJ4BpFzFG98MRXpCcz"
SCOPE = "read_muller write_muller"
USER_PREFIX = "muller"
HTTP_TIMEOUT = 30


class MullerIntuitivAuthError(Exception):
    """Exception for authentication errors."""


class MullerIntuitivApiError(Exception):
    """Exception for general API errors."""


async def debug_api():
    """Debug API data retrieval"""
    if len(sys.argv) != 3:
        print("Usage: python standalone_debug.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)

    async with aiohttp.ClientSession() as session:
        try:
            print("1. Testing authentication...")

            # Login
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

            async with session.post(url, data=payload, timeout=timeout) as response:
                response_text = await response.text()

                if response.status != 200:
                    print(f"❌ Authentication failed (status {response.status}): {response_text}")
                    return

                tokens = await response.json()
                access_token = tokens.get("access_token")

                if not access_token:
                    print("❌ No access token received")
                    return

            print(f"✓ Authentication successful")
            print(f"  - Access token: {access_token[:20]}...")
            print(f"  - Token type: {tokens.get('token_type', 'None')}")
            print(f"  - Expires in: {tokens.get('expires_in', 'None')} seconds")
            print()

            # Headers for authenticated requests
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            print("2. Getting homes data...")
            url = f"{API_BASE_URL}/api/homesdata"
            async with session.post(url, headers=headers, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Homes data request failed (status {response.status}): {error_text}")
                    return

                homes_response = await response.json()
                print(f"✓ Homes data retrieved")
                print(f"  - Response structure: {json.dumps(homes_response, indent=2)}")

                homes = homes_response.get("body", {}).get("homes", [])
                if not homes:
                    print("❌ No homes found in response!")
                    return

                home_data = homes[0]
                home_id = home_data.get("id")
                print(f"  - Home ID: {home_id}")
                print(f"  - Home name: {home_data.get('name', 'Unknown')}")
                print()

            print("3. Getting home status (rooms data)...")
            url = f"{API_BASE_URL}/syncapi/v1/homestatus"
            payload = {"home_id": home_id}

            async with session.post(
                url, headers=headers, json=payload, timeout=timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Home status request failed (status {response.status}): {error_text}")
                    return

                status_response = await response.json()
                print(f"✓ Home status retrieved")
                print(f"  - Response structure: {json.dumps(status_response, indent=2)}")

                rooms_data = status_response.get("body", {}).get("home", {}).get("rooms", [])
                print(f"  - Number of rooms: {len(rooms_data)}")
                print()

                if rooms_data:
                    print("4. Detailed room analysis:")
                    for i, room in enumerate(rooms_data):
                        print(f"  🏠 Room {i+1} - Complete Data Structure:")
                        print(f"     📋 Full JSON: {json.dumps(room, indent=8, default=str)}")
                        print()
                        print(f"     🔑 Key Analysis:")
                        print(
                            f"        - ID: {room.get('id')} ({'✅' if room.get('id') else '❌'})"
                        )
                        print(
                            f"        - Name: {room.get('name', 'Unknown')} ({'✅' if room.get('name') else '❌'})"
                        )
                        print(
                            f"        - Current temp: {room.get('therm_measured_temperature')}°C ({'✅' if room.get('therm_measured_temperature') is not None else '❌'})"
                        )
                        print(
                            f"        - Target temp: {room.get('therm_setpoint_temperature')}°C ({'✅' if room.get('therm_setpoint_temperature') is not None else '❌'})"
                        )
                        print(
                            f"        - Mode: {room.get('therm_setpoint_mode')} ({'✅' if room.get('therm_setpoint_mode') else '❌'})"
                        )
                        print(
                            f"        - Open window: {room.get('open_window')} ({'✅' if 'open_window' in room else '❌'})"
                        )
                        print()
                        print(f"     📊 All available keys ({len(room.keys())} total):")
                        for key in sorted(room.keys()):
                            value = room[key]
                            value_type = type(value).__name__
                            print(f"        - {key}: {value} ({value_type})")
                        print()
                        print("     " + "=" * 60)
                        print()

                    print("5. Integration compatibility check:")
                    required_keys = [
                        "id",
                        "name",
                        "therm_measured_temperature",
                        "therm_setpoint_temperature",
                        "therm_setpoint_mode",
                    ]

                    for room in rooms_data:
                        room_name = room.get("name", f"Room {room.get('id', '?')}")
                        print(f"  🏠 {room_name}:")
                        all_good = True
                        for key in required_keys:
                            has_key = key in room and room[key] is not None
                            status = "✅" if has_key else "❌"
                            print(f"    {status} {key}: {room.get(key, 'MISSING')}")
                            if not has_key:
                                all_good = False

                        print(
                            f"  🎯 Room compatibility: {'✅ GOOD' if all_good else '❌ ISSUES FOUND'}"
                        )
                        print()

                else:
                    print("❌ No rooms found!")
                    print("This might be why Home Assistant shows 'Pas d'intégration'")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_api())
