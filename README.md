# Muller Intuitiv Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

A **complete** Home Assistant custom integration for Muller Intuitiv heating systems. This integration exploits **ALL available API data** to provide rich, intuitive control and monitoring with room-based entity names and comprehensive system information.

> **Acknowledgments**: This integration is inspired by the excellent work in the [Jeedom Muller Intuitiv plugin](https://github.com/shun84/jeedom-plugin-mullerintuitiv) by shun84. The API understanding and implementation patterns were adapted from that project.

## ✨ Features (v0.11.0)

### 🏠 **Intelligent Room-Based Entities**
- **Meaningful Names**: `climate.chambre_quentin`, `climate.cuisine` instead of technical IDs
- **Automatic Areas**: Home Assistant area suggestions from room names
- **Room Types**: Bedroom, kitchen, office classification and integration
- **Localized Interface**: Preserves French room names for authentic experience

### 🌡️ **Complete Climate Control**
- **Full Thermostat Control**: Temperature setting with preset modes (Home, Eco, Manual)
- **Real-time Monitoring**: Current and target temperatures with status indicators
- **Multi-room Support**: Automatic discovery and control of all heating zones
- **Enhanced Attributes**: 15+ data points per climate entity including temporal info

### 📊 **Comprehensive Sensor Suite**
- **System Sensors**: Outdoor temperature (🌡️) and WiFi strength (📶) monitoring
- **Per-Room Sensors**: Presence detection (👤), window status (🪟), boost control (🔥)
- **Smart Icons**: Dynamic icons reflecting real-time status
- **Diagnostic Information**: Complete system health and connectivity monitoring

### 🔧 **Professional Device Management**
- **Enhanced Device Registry**: Firmware versions, hardware info, proper hierarchy
- **Automatic Token Refresh**: Seamless authentication with proactive refresh
- **Error Recovery**: Intelligent home ID refresh and connection resilience
- **Device Lifecycle**: Full device availability tracking and management

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add `https://github.com/AZQN0/hass_muller_intuitiv` as an Integration
3. Install the integration through HACS
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/AZQN0/hass_muller_intuitiv/releases)
2. Extract the files
3. Copy the `custom_components/muller_intuitiv` folder to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Configuration

### Adding the Integration

1. In Home Assistant, go to **Configuration** → **Integrations**
2. Click the **+** button to add a new integration
3. Search for "Muller Intuitiv"
4. Enter your Muller Intuitiv credentials:
   - **Username**: Your Muller Intuitiv app username
   - **Password**: Your Muller Intuitiv app password

### Credentials

You'll need the same username and password you use for the official Muller Intuitiv mobile app. The integration will automatically discover your home and active heating devices.

> **Note**: This integration works directly with your **physical heating devices** (FPN, FP4 modules) rather than logical room definitions. Each active heating device becomes a separate climate entity in Home Assistant.

## Usage

### Climate Entities

Each **heating device** in your Muller Intuitiv system will appear as a climate entity in Home Assistant. The integration automatically detects physical heating devices and creates entities with descriptive names:

- **FPN Thermostat XXXX**: Devices with temperature sensors (can read current temperature)
- **FPN Heater XXXX**: Devices without sensors (heating control only)

Each entity provides the following features:

- **Current Temperature**: Real-time temperature reading
- **Target Temperature**: Set your desired temperature
- **HVAC Mode**: Heat or Off
- **Preset Modes**:
  - **Home**: Standard comfort temperature
  - **Eco**: Energy-saving temperature
  - **Manual**: Custom temperature setting

### Automations Example

```yaml
# Turn on eco mode at night
automation:
  - alias: "Night Eco Mode"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: climate.set_preset_mode
      target:
        entity_id: climate.muller_intuitiv_device_3347167131
      data:
        preset_mode: "eco"

# Return to home mode in the morning
  - alias: "Morning Home Mode"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: climate.set_preset_mode
      target:
        entity_id: climate.muller_intuitiv_device_3347167131
      data:
        preset_mode: "home"
```

### Lovelace Card Example

```yaml
# Enhanced v0.11.0 example with room names
type: thermostat
entity: climate.chambre_quentin
name: Chambre Quentin
```

## 📊 Entities Created (v0.11.0)

### Climate Entities (Enhanced)
```yaml
# Room-based climate entities with meaningful names
climate.chambre_quentin         # Chambre Quentin Thermostat
climate.cuisine                 # Cuisine Thermostat
climate.bureau                  # Bureau Thermostat
```

### System Sensors (NEW)
```yaml
sensor.outdoor_temperature      # External temperature (14.4°C)
sensor.wifi_strength            # WiFi signal strength (71%)
```

### Per-Room Sensors (NEW)
```yaml
# Presence detection
sensor.chambre_quentin_presence # Motion detection
sensor.cuisine_presence         # Kitchen activity
sensor.bureau_presence          # Office occupancy

# Window status
sensor.chambre_quentin_window   # Window open/closed
sensor.cuisine_window          # Kitchen window state
sensor.bureau_window           # Office window state

# Boost control
sensor.chambre_quentin_boost_status # Heating boost mode
sensor.cuisine_boost_status        # Kitchen boost status
sensor.bureau_boost_status         # Office boost status
```

### Enhanced Climate Attributes (NEW)
```yaml
# Example climate.chambre_quentin attributes
room_name: "Chambre Quentin"
room_type: "bedroom"
device_id: "3755235792"
room_id: "3755235792"
muller_type: "FPN"
muller_mode: "home"
open_window: false
presence: false
boost_status: "disabled"
setpoint_expires_at: "2026-05-13 15:30:00"  # NEW
anticipating: false                          # NEW
lowering: false                             # NEW
pairing_status: "stop"                      # NEW
reachable: true                             # NEW
last_seen: "2026-05-13 14:25:30"           # NEW
```

### Device Registry Information (Enhanced)
```yaml
# Enhanced device information
Device Name: "Chambre Quentin Thermostat"    # Instead of "FPN Thermostat 5792"
Manufacturer: "Muller"
Model: "Intuitiv FPN"
Software Version: "Rev 185"                  # NEW firmware info
Suggested Area: "Chambre Quentin"           # NEW auto area
Via Device: "Muller Intuitiv System"
```

### Automation Examples with New Entities
```yaml
# Use presence detection for smart heating
automation:
  - alias: "Smart Heating - Bedroom Occupied"
    trigger:
      platform: state
      entity_id: sensor.chambre_quentin_presence
      to: "detected"
    action:
      service: climate.set_preset_mode
      target:
        entity_id: climate.chambre_quentin
      data:
        preset_mode: "home"

  - alias: "Window Open - Reduce Heating"
    trigger:
      platform: state
      entity_id: sensor.chambre_quentin_window
      to: "open"
    action:
      service: climate.set_preset_mode
      target:
        entity_id: climate.chambre_quentin
      data:
        preset_mode: "eco"

  - alias: "Outdoor Temperature Display"
    trigger:
      platform: state
      entity_id: sensor.outdoor_temperature
    action:
      service: notify.mobile_app
      data:
        message: "Outdoor temperature: {{ states('sensor.outdoor_temperature') }}°C"
```

## Troubleshooting

### Common Issues

**Integration not appearing in the list**
- Ensure you've restarted Home Assistant after installation
- Check the logs for any error messages

**Authentication failed**
- Verify your username and password are correct
- Ensure your Muller Intuitiv account is active
- Try logging into the mobile app to confirm credentials

**No heating devices found**
- Make sure your Muller Intuitiv system is properly configured
- Check that heating devices are visible and responding in the mobile app
- Verify that your heating system has active FPN or FP4 devices

### Debug Logging

To enable comprehensive debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.muller_intuitiv: debug
```

After restarting Home Assistant, the logs will show detailed information including:

#### Device Discovery & Mapping
- **Home structure analysis**: Lists all rooms and their associated devices/modules
- **Device-to-room mapping**: Shows how physical devices are mapped to logical rooms
- **Entity creation**: Logs when climate entities are initialized with their device/room IDs

#### API Operations
- **Authentication flow**: Token requests, refresh attempts, and expiration handling
- **Data fetching**: Home structure and device status API calls with response summaries
- **Control commands**: Temperature and mode changes with request/response details

#### Error Diagnosis
- **Mapping failures**: When devices can't be mapped to rooms (with available device lists)
- **API errors**: Detailed error responses with context
- **Room ID mismatches**: Helps diagnose the "room does not belong to home" error

#### Example Log Output
```
INFO [custom_components.muller_intuitiv.coordinator] Starting data update for home 123456789
INFO [custom_components.muller_intuitiv.coordinator] Home data received: 2 rooms found
INFO [custom_components.muller_intuitiv.coordinator] Mapped device 2483305402 to room 987654321 (Living Room)
INFO [custom_components.muller_intuitiv.coordinator] Device status received: 2 devices found
INFO [custom_components.muller_intuitiv.coordinator] Mapping summary: 2 successful, 0 failed out of 2 total devices
INFO [custom_components.muller_intuitiv.climate] Climate entity FPN Thermostat 5402 requesting temperature change to 21.0°C (device_id=2483305402, room_id=987654321)
```

This detailed logging helps troubleshoot device discovery, room mapping, and control operation issues.

## API Rate Limits

The integration updates every 60 seconds by default. This should provide timely updates while respecting the Muller Intuitiv API limits.

## Supported Devices

This integration works with Muller Intuitiv heating systems that are compatible with the official Muller Intuitiv mobile app.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Development

This integration targets Home Assistant `2026.5.1`. Use Python `3.14.2+` for
local validation and see [TESTING.md](TESTING.md) for the full workflow.

Fast offline tests live under `tests/unit/` and `tests/integration/`. Home
Assistant Core fixture tests live under `tests/components/muller_intuitiv/` and
can be run through `scripts/test_ha_core.py` against a matching Core checkout.
Real cloud checks must stay opt-in through the `real_api` pytest marker.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial integration. It is not affiliated with or endorsed by Muller.

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the Home Assistant logs
3. Open an issue on [GitHub](https://github.com/AZQN0/hass_muller_intuitiv/issues)

---

**Star this repo if you find it useful! ⭐**

[commits-shield]: https://img.shields.io/github/commit-activity/y/AZQN0/hass_muller_intuitiv.svg
[commits]: https://github.com/AZQN0/hass_muller_intuitiv/commits/main
[license-shield]: https://img.shields.io/github/license/AZQN0/hass_muller_intuitiv.svg
[releases-shield]: https://img.shields.io/github/release/AZQN0/hass_muller_intuitiv.svg
[releases]: https://github.com/AZQN0/hass_muller_intuitiv/releases
