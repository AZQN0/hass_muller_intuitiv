"""Constants for the Muller Intuitiv integration."""

DOMAIN = "muller_intuitiv"

# API details
API_BASE_URL = "https://app.muller-intuitiv.net"
# Note: These are public API credentials from the mobile app
CLIENT_ID = "59e604948fe283fd4dc7e355"
CLIENT_SECRET = "rAeWu8Y3YqXEPqRJ4BpFzFG98MRXpCcz"

# Auth prefixes
USER_PREFIX = "muller"
SCOPE = "read_muller write_muller"

# Configuration keys
CONF_HOME_ID = "home_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EXPIRES_IN = "expires_in"
CONF_EXPIRES_AT = "expires_at"

# Default values
DEFAULT_UPDATE_INTERVAL = 60  # seconds
DEFAULT_MANUAL_DURATION = 120  # minutes
HTTP_TIMEOUT = 30  # seconds

# Device types
DEVICE_TYPE_THERMOSTAT = "thermostat"
DEVICE_TYPE_HEATER = "heater"

# Supported features
SUPPORTED_MULLER_MODES = ["manual", "home", "hg"]
SUPPORTED_HVAC_MODES = ["heat", "off"]

# API endpoints
ENDPOINT_TOKEN = "/oauth2/token"
ENDPOINT_HOMES = "/muller/v1/homes"
ENDPOINT_HOME_STATUS = "/muller/v1/homes/{home_id}/rooms"
ENDPOINT_ROOM_CONTROL = "/muller/v1/homes/{home_id}/rooms/{room_id}/control"
