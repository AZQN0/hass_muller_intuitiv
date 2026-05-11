# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.2] - 2026-05-11

### Fixed
- Enhanced authentication error handling with specific "invalid_grant" error messages
- Improved token refresh failure detection and user guidance
- Added debug logging for authentication processes to aid troubleshooting
- Better handling of expired refresh tokens with clear reconfiguration prompts
- More robust error recovery in coordinator when tokens become invalid
- Network error handling during authentication and token refresh operations

### Changed
- Authentication errors now provide clearer messaging to users
- Token refresh failures automatically trigger reconfiguration requirements
- Added proactive token validation before API calls

### Verified
- All authentication fixes verified with comprehensive integration tests against real Muller Intuitiv API
- Successfully tested login, token refresh, API calls, and error handling scenarios
- Confirmed proper handling of 4-room heating system (Home: "Chalet Mornex")

## [0.9.1] - 2026-05-11

### Fixed
- Fixed syntax error in api.py import statement (literal \n characters)
- Fixed Python compatibility issues with modern type hints (dict[str, type] → Dict[str, type])
- Fixed Union type hints to use Optional for better Python version compatibility
- Added missing strings.json file for config flow translations
- Added missing ConfigEntry import in climate.py
- Fixed potential IndexError in get_homes_data() when no homes are found
- Resolved "Invalid handler specified" config flow error

## [0.9.0] - 2026-05-11

### Added
- Initial release of Muller Intuitiv Home Assistant integration
- Climate entity support for room temperature control
- Preset modes: Home, Eco, Manual
- HVAC modes: Heat, Off
- Automatic token refresh mechanism
- Device info for proper Home Assistant device registry
- Open window detection attribute
- Comprehensive error handling and timeout management

### Security
- Improved token expiration tracking with timestamps
- Enhanced error handling for authentication failures
- HTTP request timeouts to prevent hanging connections

### Technical
- Type hints throughout codebase
- Proper exception handling hierarchy
- Modular constants management
- Async/await pattern implementation
- Home Assistant best practices compliance

---

## Release Notes

### Version 0.9.0

This is the initial public release of the Muller Intuitiv Home Assistant integration. The integration provides comprehensive control over your Muller Intuitiv heating system directly from Home Assistant.

**Key Features:**
- Complete climate control for all rooms
- Automatic room discovery
- Secure authentication with token refresh
- Real-time temperature monitoring
- Multiple preset modes for energy efficiency
- Open window detection
- Robust error handling

**Installation:**
- Available through HACS (custom repository)
- Manual installation supported
- Simple configuration through the UI

**Requirements:**
- Home Assistant 2024.1.0 or newer
- Active Muller Intuitiv account
- Muller Intuitiv compatible heating system

**Acknowledgments:**
- Inspired by the [Jeedom Muller Intuitiv plugin](https://github.com/shun84/jeedom-plugin-mullerintuitiv) by shun84
- API understanding adapted from the original Jeedom implementation

**Future Plans:**
- Enhanced scheduling features
- Additional sensor entities
- Energy monitoring capabilities
- Mobile app integration improvements

For detailed installation and configuration instructions, see the [README](README.md).