#!/usr/bin/env python3
"""Debug script to analyze room mapping issue."""

import asyncio
import json
import sys

import aiohttp

from custom_components.muller_intuitiv.api import MullerIntuitivApi


async def debug_room_mapping(username: str, password: str):
    """Debug the room mapping issue."""

    async with aiohttp.ClientSession() as session:
        api = MullerIntuitivApi(session)

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

            print("\n🔍 Home structure analysis:")
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
                    print(f"      Module {j+1}: ID={module_id}, Type={module_type}")

                    if module_id:
                        device_to_room_map[module_id] = room_id
                        print(f"      ✅ Mapped device {module_id} -> room {room_id}")

            print(f"\n📍 Device-to-room mapping created: {len(device_to_room_map)} devices")
            print(f"   Mapping: {device_to_room_map}")

            # Get homestatus data (devices)
            print(f"\n🌡️  Getting device status data (homestatus)...")
            devices_data = await api.get_home_status(home_id)
            print(f"🔥 Devices found in homestatus: {len(devices_data)}")

            print("\n🔍 Device status analysis:")

            mapping_success = 0
            mapping_failures = []

            for i, device in enumerate(devices_data):
                device_id = device.get("id")
                device_name = device.get("name", "Unknown")
                muller_type = device.get("muller_type", "Unknown")

                print(f"\n  Device {i+1}:")
                print(f"    ID: {device_id}")
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

                    # Show potential issues
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
                        if str_device_id in str_mapped_id or str_mapped_id in str_device_id:
                            print(f"    ⚠️  Potential match found: {mapped_id} vs {device_id}")

                        try:
                            int_mapped_id = int(mapped_id)
                            if int_device_id and int_device_id == int_mapped_id:
                                print(f"    ⚠️  Integer match found: {int_mapped_id}")
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
                    print(
                        f"   Home structure ID type: {type(first_mapped_id)} ({repr(first_mapped_id)})"
                    )

                if devices_data:
                    first_device_id = devices_data[0].get("id")
                    print(
                        f"   Device status ID type: {type(first_device_id)} ({repr(first_device_id)})"
                    )

                # Raw data dump for analysis
                print(f"\n📄 RAW DATA DUMP:")
                print(f"   Home structure raw data:")
                print(json.dumps(home_data, indent=2))
                print(f"\n   Device status raw data:")
                print(json.dumps(devices_data, indent=2))

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python debug_room_mapping.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    asyncio.run(debug_room_mapping(username, password))
