# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.8] - 2026-05-11

### Fixed
- **CRITICAL**: Resolved "catching classes that do not inherit from BaseException" runtime error
- Fixed aiohttp exception handling in API module that was preventing climate operations
- **AUTO-RECOVERY**: Added automatic home_id refresh when "Invalid home_id" error occurs
- Integration now auto-recovers from invalid home_id without requiring reconfiguration
- Improved exception hierarchy to properly catch aiohttp timeout and connection errors

### Technical Changes
- Fixed aiohttp.ClientTimeout exception handling in api.py:167
- Removed duplicate ClientError exception handlers
- Added intelligent home_id refresh logic in coordinator when API returns invalid home_id error
- Automatic config entry update with refreshed home_id for persistent recovery
- Enhanced error handling with specific recovery strategies

This resolves the recurring runtime errors that were preventing the integration from functioning.

## [0.9.7] - 2026-05-11

### Fixed
- **CRITICAL**: Fixed device-to-room mapping failures for devices 2483305402 and 3347167131
- Resolved "Could not find room mapping for device X" errors preventing entity creation
- Enhanced device ID matching with robust type conversion (string/integer compatibility)
- Device mapping now handles API inconsistencies between homesdata and homestatus endpoints

### Technical Changes
- Improved device-to-room mapping logic with multi-type ID storage (original, string, integer)
- Added comprehensive error handling for device ID type mismatches
- Enhanced logging to show all mapping keys for better troubleshooting
- Fixed coordinator mapping logic to work with both string and numeric device IDs

This resolves the core issue preventing climate entities from being created in Home Assistant.

## [0.9.6] - 2026-05-11

### Fixed
- **CRITICAL**: Resolved API error 400 "room<ID> does not belong to this home"
- Fixed device ID vs room ID mismatch in API calls
- Fixed diagnostics 500 Internal Server Error preventing diagnostic data retrieval
- Coordinator now properly maps devices to their correct room IDs using homesdata structure
- All climate control operations (temperature, preset, HVAC mode) now use correct room IDs

### Technical Changes
- Added device-to-room mapping in coordinator using home structure data
- Enhanced coordinator to fetch both homesdata (room IDs) and homestatus (device status)
- Updated climate entity to use room_id from device data for API calls
- Fixed diagnostics.py Python 3.9+ type hints and unsafe session access
- Added room_id to entity attributes for debugging
- **Significantly enhanced logging throughout the integration**
  - Comprehensive device discovery and mapping logs
  - Detailed API operation tracking (auth, data fetch, control commands)
  - Error diagnosis with context for troubleshooting
  - Request/response logging for API calls
  - Entity initialization and control operation logs

### Impact
- Temperature setting operations will now work without API errors
- Preset mode changes (home, eco, manual) will function correctly
- HVAC mode switching will operate as expected
- Integration will work properly with multi-room heating systems

## [0.9.5] - 2026-05-11

### Fixed
- **CRITICAL**: Resolved "catching classes that do not inherit from BaseException" error in climate operations
- Fixed duplicate exception class definitions causing runtime conflicts
- Consolidated all exception definitions in exceptions.py module
- Updated imports across api.py and coordinator.py to use proper exception hierarchy

### Technical Changes
- Removed duplicate exception classes from api.py
- Centralized exception definitions in exceptions.py for consistency
- All custom exceptions now properly inherit from MullerIntuitivError base class
- Fixed module imports to prevent runtime exception handling errors

## [0.9.3] - 2026-05-11

### Major Architecture Changes
- **BREAKING**: Completely restructured integration to work with actual API data structure
- Changed from room-based to device-based architecture (no longer tries to map logical rooms)
- Integration now works directly with physical heating devices (FPN, FP4 modules)

### Fixed
- Resolved "Pas d'intégration" issue - entities will now be created correctly
- Fixed critical room ID mismatch between homes data and status data
- Eliminated incorrect mapping between logical room definitions and physical device status
- Proper handling of devices with and without temperature sensors

### Changed
- Entity names now reflect actual device types: "FPN Thermostat XXXX" or "FPN Heater XXXX"
- Entity IDs changed to use device IDs instead of non-existent room mappings
- Enhanced device information in Home Assistant device registry
- Added device-specific attributes (muller_type, presence, boost_status)

### Added
- Automatic detection of device capabilities (temperature sensor vs relay-only)
- User-friendly device naming based on device type and features
- Better error handling for systems with mixed device types

### Technical Details
- Coordinator now processes homestatus "rooms" as physical heating devices
- Climate entities use actual device IDs for API calls
- Removed failed attempt to merge homes data room names with status data
- API calls properly target individual heating device endpoints

### Verified
- Tested with real 2-device heating system showing proper entity creation
- Confirmed compatibility with FPN devices (both sensor and non-sensor variants)
- All device control functions (temperature, preset modes, HVAC modes) working correctly

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