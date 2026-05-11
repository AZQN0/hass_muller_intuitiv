# Muller Intuitiv Integration for Home Assistant

## Overview

The Muller Intuitiv integration allows you to integrate your Muller Intuitiv heating system with Home Assistant. Control room temperatures, monitor heating status, and create automations for your smart home heating management.

## What's New in v1.0.0

- **Complete Climate Control**: Full thermostat functionality for all rooms
- **Automatic Discovery**: Automatically finds and sets up all rooms in your system
- **Secure Authentication**: OAuth2 authentication with automatic token refresh
- **Real-time Monitoring**: Live temperature readings and heating status
- **Preset Modes**: Energy-efficient preset modes (Home, Eco, Manual)
- **Device Integration**: Proper Home Assistant device registry support
- **Robust Error Handling**: Comprehensive error management and recovery

## Features

### 🌡️ Climate Control
- Set target temperatures for individual rooms
- Switch between heating modes (Heat/Off)
- Use preset modes for optimal energy efficiency

### 📊 Real-time Monitoring
- Current room temperatures
- Target temperature settings
- Heating system status
- Open window detection

### 🏠 Multi-room Support
- Automatic discovery of all rooms
- Individual control for each room
- Unified device management

### ⚙️ Smart Automation
- Create heating schedules
- Energy-saving automations
- Occupancy-based temperature control
- Weather-responsive heating

## Prerequisites

- Muller Intuitiv heating system
- Active Muller Intuitiv mobile app account
- Home Assistant 2024.1.0 or newer
- Internet connection for cloud API access

## Quick Setup

1. **Install via HACS**: Add as a custom repository or install manually
2. **Add Integration**: Go to Settings → Devices & Services → Add Integration
3. **Enter Credentials**: Use your Muller Intuitiv app username and password
4. **Automatic Setup**: The integration will discover your home and rooms automatically

## Configuration

No YAML configuration required! The integration uses the Home Assistant UI configuration flow for easy setup.

After setup, climate entities will be created for each room:
- `climate.room_name` - Climate control entity
- Device info with manufacturer and model details
- Automatic icon assignment based on entity type

## Supported Services

The integration provides standard Home Assistant climate services:

- `climate.set_temperature` - Set target temperature
- `climate.set_preset_mode` - Change preset mode
- `climate.set_hvac_mode` - Change heating mode
- `climate.turn_on` / `climate.turn_off` - Basic on/off control

## Example Automations

### Energy Saving Night Mode
```yaml
automation:
  - alias: "Night Energy Saving"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: climate.set_preset_mode
      target:
        entity_id: all
      data:
        preset_mode: "eco"
```

### Morning Comfort Mode
```yaml
automation:
  - alias: "Morning Warmup"
    trigger:
      platform: time
      at: "06:30:00"
    condition:
      condition: state
      entity_id: binary_sensor.workday_sensor
      state: "on"
    action:
      service: climate.set_preset_mode
      target:
        entity_id: climate.living_room
      data:
        preset_mode: "home"
```

## Advanced Features

### Token Management
- Automatic token refresh (no user intervention required)
- Secure credential storage
- Connection retry logic

### Error Recovery
- Automatic reconnection on network issues
- Graceful handling of API rate limits
- Comprehensive logging for troubleshooting

### Performance
- Optimized update intervals (60 seconds)
- Efficient API usage
- Minimal resource consumption

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify username/password are correct
- Check if account is active in mobile app
- Ensure internet connectivity

**No Rooms Found**
- Confirm rooms are set up in mobile app
- Check Home Assistant logs for errors
- Restart integration if needed

**Connection Timeouts**
- Check internet connection stability
- Review Home Assistant network settings
- Enable debug logging for more details

### Debug Logging

Enable detailed logging by adding to `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.muller_intuitiv: debug
```

## Support & Community

- **Documentation**: [GitHub Repository](https://github.com/AZQN0/hass_muller_intuitiv)
- **Issues**: [Report bugs](https://github.com/AZQN0/hass_muller_intuitiv/issues)
- **Discussions**: [Community Forum](https://community.home-assistant.io/)

## Legal

This integration is not affiliated with Muller. Muller Intuitiv is a trademark of Muller. Use at your own risk.

---

**Enjoy smart heating control with Home Assistant! 🏠🌡️**