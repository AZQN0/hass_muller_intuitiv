#!/usr/bin/env python3
"""Debug script to test API data flow"""

import asyncio
import json
import os
import sys

import aiohttp

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from custom_components.muller_intuitiv.api import MullerIntuitivApi
from custom_components.muller_intuitiv.const import (
    API_BASE_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    HTTP_TIMEOUT,
    SCOPE,
    USER_PREFIX,
)


async def debug_api():
    """Debug API data retrieval"""
    if len(sys.argv) != 3:
        print("Usage: python debug_api_data.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    async with aiohttp.ClientSession() as session:
        api = MullerIntuitivApi(session)

        try:
            print("1. Testing authentication...")
            tokens = await api.login(username, password)
            print(f"✓ Authentication successful")
            print(f"  - Access token: {tokens.get('access_token', 'None')[:20]}...")
            print(f"  - Token type: {tokens.get('token_type', 'None')}")
            print(f"  - Expires in: {tokens.get('expires_in', 'None')} seconds")
            print()

            print("2. Getting homes data...")
            home_data = await api.get_homes_data()
            home_id = home_data.get("id")
            print(f"✓ Home data retrieved")
            print(f"  - Home ID: {home_id}")
            print(f"  - Home name: {home_data.get('name', 'Unknown')}")
            print(f"  - Home keys: {list(home_data.keys())}")
            print()

            print("3. Getting home status (rooms data)...")
            rooms_data = await api.get_home_status(home_id)
            print(f"✓ Rooms data retrieved")
            print(f"  - Number of rooms: {len(rooms_data)}")
            print()

            if rooms_data:
                print("4. Room details:")
                for i, room in enumerate(rooms_data):
                    print(f"  Room {i+1}:")
                    print(f"    - ID: {room.get('id')}")
                    print(f"    - Name: {room.get('name', 'Unknown')}")
                    print(f"    - Current temp: {room.get('therm_measured_temperature')}°C")
                    print(f"    - Target temp: {room.get('therm_setpoint_temperature')}°C")
                    print(f"    - Mode: {room.get('therm_setpoint_mode')}")
                    print(f"    - Open window: {room.get('open_window')}")
                    print(f"    - All keys: {list(room.keys())}")
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
