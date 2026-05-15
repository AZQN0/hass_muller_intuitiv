"""Constants for the Muller Intuitiv integration."""

DOMAIN = "muller_intuitiv"

# API details
API_BASE_URL = "https://app.muller-intuitiv.net"
# Note: These are public API credentials from the mobile app
CLIENT_ID = "59e604948fe283fd4dc7e355"
CLIENT_SECRET = "rAeWu8Y3YqXEPqRJ4BpFzFG98MRXpCcz"  # nosec B105

# Auth prefixes
USER_PREFIX = "muller"
SCOPE = "read_muller write_muller"

# Configuration keys
CONF_HOME_ID = "home_id"
CONF_ACCESS_TOKEN = "access_token"  # nosec B105
CONF_REFRESH_TOKEN = "refresh_token"  # nosec B105
CONF_EXPIRES_IN = "expires_in"
CONF_EXPIRES_AT = "expires_at"

# Default values
DEFAULT_UPDATE_INTERVAL = 60  # seconds
DEFAULT_MANUAL_DURATION = 120  # minutes
HTTP_TIMEOUT = 30  # seconds
