# Muller Intuitiv Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

A Home Assistant custom integration for Muller Intuitiv heating systems. This integration allows you to monitor and control your Muller Intuitiv thermostats directly from Home Assistant.

## Features

- 🌡️ **Climate Control**: Full thermostat control with temperature setting and preset modes
- 📊 **Real-time Monitoring**: Current and target temperature readings
- 🏠 **Multiple Rooms**: Support for multi-room heating systems
- ⚡ **Preset Modes**: Home, Eco, and Manual temperature control
- 🔄 **Automatic Token Refresh**: Seamless authentication management
- 🪟 **Open Window Detection**: Monitor window status for each room

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add `https://github.com/yourusername/hass_muller_intuitiv` as an Integration
3. Install the integration through HACS
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/yourusername/hass_muller_intuitiv/releases)
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

You'll need the same username and password you use for the official Muller Intuitiv mobile app. The integration will automatically discover your home and rooms.

## Usage

### Climate Entities

Each room in your Muller Intuitiv system will appear as a climate entity in Home Assistant with the following features:

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
        entity_id: climate.living_room
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
        entity_id: climate.living_room
      data:
        preset_mode: "home"
```

### Lovelace Card Example

```yaml
type: thermostat
entity: climate.living_room
name: Living Room
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

**No rooms found**
- Make sure your Muller Intuitiv system is properly configured
- Check that rooms are visible in the mobile app

### Debug Logging

To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.muller_intuitiv: debug
```

## API Rate Limits

The integration updates every 60 seconds by default. This should provide timely updates while respecting the Muller Intuitiv API limits.

## Supported Devices

This integration works with Muller Intuitiv heating systems that are compatible with the official Muller Intuitiv mobile app.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial integration. It is not affiliated with or endorsed by Muller.

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the Home Assistant logs
3. Open an issue on [GitHub](https://github.com/yourusername/hass_muller_intuitiv/issues)

---

**Star this repo if you find it useful! ⭐**

[commits-shield]: https://img.shields.io/github/commit-activity/y/yourusername/hass_muller_intuitiv.svg
[commits]: https://github.com/yourusername/hass_muller_intuitiv/commits/main
[license-shield]: https://img.shields.io/github/license/yourusername/hass_muller_intuitiv.svg
[releases-shield]: https://img.shields.io/github/release/yourusername/hass_muller_intuitiv.svg
[releases]: https://github.com/yourusername/hass_muller_intuitiv/releases