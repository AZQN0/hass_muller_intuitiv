#!/usr/bin/env python3
"""Standalone debug script to analyze room mapping issue."""

import asyncio
import sys
import json
import aiohttp
import time
import logging

# Constants from const.py
API_BASE_URL = "https://app.muller-intuitiv.net"
CLIENT_ID = "muller_intuitiv_api"
CLIENT_SECRET = "123456"
USER_PREFIX = "par"
SCOPE = "read_write"
HTTP_TIMEOUT = 30

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

class MullerIntuitivApiStandalone:
    """Standalone API Client for Muller Intuitiv."""

    def __init__(self, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self._session = session
        self._token = None
        self._timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)

    def set_token(self, token: str) -> None:
        """Set the access token."""
        self._token = token

    async def login(self, username: str, password: str) -> dict:
        """Authenticate with username and password and get tokens."""
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

        print(f"🔑 Attempting login for username: {username[:3]}***")

        async with self._session.post(url, data=payload, timeout=self._timeout) as response:
            response_text = await response.text()

            if response.status != 200:
                print(f"❌ Authentication failed (status {response.status}): {response_text}")
                raise Exception(f"Authentication failed with status {response.status}")

            data = await response.json()
            self._token = data.get("access_token")

            if not self._token:
                print("❌ No access token received in response")
                raise Exception("No access token in response")

            # Calculate and store expiration timestamp
            expires_in = data.get("expires_in", 3600)  # Default 1 hour
            data["expires_at"] = int(time.time()) + expires_in

            print(f"✅ Login successful, token expires in {expires_in} seconds")
            return data

    async def _post(self, endpoint: str, json_data: dict = None) -> dict:
        """Make a POST request to the API."""
        if not self._token:
            raise Exception("No access token available")

        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json"
        }

        async with self._session.post(url, headers=headers, json=json_data, timeout=self._timeout) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"❌ API error {response.status}: {error_text}")
                raise Exception(f"API request failed with status {response.status}: {error_text}")

            return await response.json()

    async def get_homes_data(self) -> dict:
        """Fetch home data including IDs, modes, and schedules."""
        print("📋 Fetching homes data from /api/homesdata")
        res = await self._post("/api/homesdata")

        homes = res.get("body", {}).get("homes", [])
        if not homes:
            print(f"❌ No homes found in account response: {res}")
            raise Exception("No homes found in account")

        home_data = homes[0]
        print(f"✅ Home data fetched successfully: ID={home_data.get('id')}, Name={home_data.get('name', 'Unknown')}, Rooms={len(home_data.get('rooms', []))}")
        return home_data

    async def get_home_status(self, home_id: str) -> list:
        """Fetch status of all rooms in the home."""
        print(f"🌡️  Fetching home status for home_id: {home_id}")
        res = await self._post("/syncapi/v1/homestatus", json_data={"home_id": home_id})

        rooms = res.get("body", {}).get("home", {}).get("rooms", [])
        print(f"✅ Home status fetched successfully: {len(rooms)} devices found")

        return rooms

async def debug_room_mapping(username: str, password: str):
    """Debug the room mapping issue."""

    async with aiohttp.ClientSession() as session:
        api = MullerIntuitivApiStandalone(session)

        try:
            # Login
            print("🔑 Logging in...")
            tokens = await api.login(username, password)
            print(f"✅ Login successful")

            # Get homes data (structure)
            print("\n📋 Getting home structure data...")
            home_data = await api.get_homes_data()
            home_id = home_data.get("id")
            print(f"🏠 Home ID: {home_id}")
            print(f"🏠 Home Name: {home_data.get('name', 'Unknown')}")

            rooms_from_home = home_data.get("rooms", [])
            print(f"📊 Rooms found in home structure: {len(rooms_from_home)}")

            print("\n🔍 HOME STRUCTURE ANALYSIS:")
            device_to_room_map = {}

            for i, room in enumerate(rooms_from_home):
                room_id = room.get("id")
                room_name = room.get("name", "Unknown")
                modules = room.get("modules", [])

                print(f"\n  Room {i+1}:")
                print(f"    ID: {room_id}")
                print(f"    Name: {room_name}")
                print(f"    Modules: {len(modules)}")

                for j, module in enumerate(modules):
                    module_id = module.get("id")
                    module_type = module.get("type", "Unknown")
                    print(f"      Module {j+1}: ID={module_id} (type: {type(module_id)}), Type={module_type}")

                    if module_id:
                        device_to_room_map[module_id] = room_id
                        print(f"      ✅ Mapped device {module_id} -> room {room_id}")

            print(f"\n📍 Device-to-room mapping created: {len(device_to_room_map)} devices")
            print(f"   Mapping: {device_to_room_map}")

            # Get homestatus data (devices)
            print(f"\n🌡️ Getting device status data (homestatus)...")
            devices_data = await api.get_home_status(home_id)
            print(f"🔥 Devices found in homestatus: {len(devices_data)}")

            print("\n🔍 DEVICE STATUS ANALYSIS:")

            mapping_success = 0
            mapping_failures = []

            for i, device in enumerate(devices_data):
                device_id = device.get("id")
                device_name = device.get("name", "Unknown")
                muller_type = device.get("muller_type", "Unknown")

                print(f"\n  Device {i+1}:")
                print(f"    ID: {device_id} (type: {type(device_id)})")
                print(f"    Name: {device_name}")
                print(f"    Type: {muller_type}")

                # Check mapping
                room_id = device_to_room_map.get(device_id)
                if room_id:
                    print(f"    ✅ Successfully mapped to room: {room_id}")
                    mapping_success += 1
                else:
                    print(f"    ❌ MAPPING FAILED - device ID not found in mapping")
                    mapping_failures.append(device_id)

                    print(f"    Available device IDs in mapping: {list(device_to_room_map.keys())}")

                    # Check if ID conversion might be needed
                    str_device_id = str(device_id)
                    int_device_id = None
                    try:
                        int_device_id = int(device_id)
                    except (ValueError, TypeError):
                        pass

                    print(f"    Device ID as string: '{str_device_id}'")
                    print(f"    Device ID as int: {int_device_id}")

                    # Check for close matches
                    for mapped_id in device_to_room_map.keys():
                        str_mapped_id = str(mapped_id)

                        # Direct string comparison
                        if str_device_id == str_mapped_id:
                            print(f"    ⚠️  STRING EXACT MATCH: {mapped_id} == {device_id}")
                        elif str_device_id in str_mapped_id or str_mapped_id in str_device_id:
                            print(f"    ⚠️  String partial match: {mapped_id} vs {device_id}")

                        # Integer comparison
                        try:
                            int_mapped_id = int(mapped_id)
                            if int_device_id and int_device_id == int_mapped_id:
                                print(f"    ⚠️  INTEGER EXACT MATCH: {int_mapped_id} == {int_device_id}")
                        except (ValueError, TypeError):
                            pass

            print(f"\n📊 MAPPING SUMMARY:")
            print(f"   ✅ Successful mappings: {mapping_success}")
            print(f"   ❌ Failed mappings: {len(mapping_failures)}")
            print(f"   Failed device IDs: {mapping_failures}")

            if mapping_failures:
                print(f"\n🔍 DEBUGGING INFO FOR FAILED MAPPINGS:")
                print(f"   Home structure device IDs (modules): {list(device_to_room_map.keys())}")
                print(f"   Device status device IDs: {[d.get('id') for d in devices_data]}")

                # Check data types
                print(f"\n🔍 DATA TYPE ANALYSIS:")
                if device_to_room_map:
                    first_mapped_id = list(device_to_room_map.keys())[0]
                    print(f"   Home structure ID type: {type(first_mapped_id)} = {repr(first_mapped_id)}")

                if devices_data:
                    first_device_id = devices_data[0].get('id')
                    print(f"   Device status ID type: {type(first_device_id)} = {repr(first_device_id)}")

                # Try to fix mapping by converting types
                print(f"\n🔧 ATTEMPTING TYPE CONVERSIONS:")

                # Convert all mapping keys to strings
                string_map = {str(k): v for k, v in device_to_room_map.items()}
                for device_id in mapping_failures:
                    str_device_id = str(device_id)
                    if str_device_id in string_map:
                        print(f"   ✅ FOUND WITH STRING CONVERSION: {device_id} -> {string_map[str_device_id]}")

                # Convert all mapping keys to integers
                int_map = {}
                for k, v in device_to_room_map.items():
                    try:
                        int_k = int(k)
                        int_map[int_k] = v
                    except (ValueError, TypeError):
                        pass

                for device_id in mapping_failures:
                    try:
                        int_device_id = int(device_id)
                        if int_device_id in int_map:
                            print(f"   ✅ FOUND WITH INT CONVERSION: {device_id} -> {int_map[int_device_id]}")
                    except (ValueError, TypeError):
                        pass

            # Show raw data for manual inspection
            print(f"\n📄 RAW DATA SAMPLES:")
            print(f"   Sample home structure room:")
            if rooms_from_home:
                print(json.dumps(rooms_from_home[0], indent=2))

            print(f"\n   Sample device status:")
            if devices_data:
                print(json.dumps(devices_data[0], indent=2))

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python debug_room_mapping_standalone.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    asyncio.run(debug_room_mapping(username, password))