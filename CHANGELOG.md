# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [1.0.0] - 2026-05-11

### Added
- Initial implementation
- Support for Muller Intuitiv heating systems
- Climate platform integration
- OAuth2 authentication
- Multi-room support
- Configuration flow for easy setup
- Real-time temperature monitoring
- Temperature control with preset modes

### Features
- **Climate Control**: Full thermostat functionality
- **Multi-room Support**: Automatic discovery of all rooms
- **Preset Modes**: Home, Eco, and Manual temperature settings
- **Real-time Updates**: 60-second update interval
- **Authentication**: Secure OAuth2 token management
- **Device Integration**: Proper Home Assistant device registry support

### Technical Details
- Built with Home Assistant 2024+ compatibility
- Async implementation for optimal performance
- Comprehensive error handling
- Automatic token refresh
- Type-safe code with full type annotations
- HACS compatible structure

---

## Release Notes

### Version 1.0.0

This is the initial release of the Muller Intuitiv Home Assistant integration. The integration provides comprehensive control over your Muller Intuitiv heating system directly from Home Assistant.

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

**Future Plans:**
- Enhanced scheduling features
- Additional sensor entities
- Energy monitoring capabilities
- Mobile app integration improvements

For detailed installation and configuration instructions, see the [README](README.md).