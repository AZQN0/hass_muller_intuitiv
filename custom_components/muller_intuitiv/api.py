import aiohttp
import logging
import time
from typing import Any, Dict, List, Optional

from .const import (
    API_BASE_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    DEFAULT_MANUAL_DURATION,
    HTTP_TIMEOUT,
    SCOPE,
    USER_PREFIX,
)
from .exceptions import (
    MullerIntuitivApiError,
    MullerIntuitivAuthError,
    MullerIntuitivConnectionError,
    MullerIntuitivTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


class MullerIntuitivApi:
    """API Client for Muller Intuitiv."""

    def __init__(self, session: aiohttp.ClientSession, token: Optional[str] = None):
        """Initialize the API client."""
        self._session = session
        self._token = token
        self._timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)

    def set_token(self, token: str) -> None:
        """Set the access token."""
        self._token = token

    async def _request_tokens(
        self,
        payload: Dict[str, str],
        *,
        refreshing: bool = False,
    ) -> Dict[str, Any]:
        """Request OAuth tokens and normalize the response."""
        url = f"{API_BASE_URL}/oauth2/token"
        action = "Token refresh" if refreshing else "Authentication"

        try:
            async with self._session.post(url, data=payload, timeout=self._timeout) as response:
                response_text = await response.text()

                if response.status != 200:
                    _LOGGER.error("%s failed with status %d", action, response.status)
                    raise self._auth_error(response.status, response_text, refreshing=refreshing)

                data = await response.json()
                self._token = data.get("access_token")

                if not self._token:
                    _LOGGER.error("No access token received in token response")
                    raise MullerIntuitivAuthError("No access token in response")

                expires_in = data.get("expires_in", 3600)
                data["expires_at"] = int(time.time()) + expires_in
                _LOGGER.debug("%s successful, token expires in %d seconds", action, expires_in)
                return data

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during %s: %s", action.lower(), err)
            raise MullerIntuitivConnectionError(
                f"Network error during {action.lower()}: {err}"
            ) from err

    @staticmethod
    def _auth_error(
        status: int,
        response_text: str,
        *,
        refreshing: bool,
    ) -> MullerIntuitivAuthError:
        """Return a user-facing authentication error for an OAuth response."""
        if refreshing:
            if status == 400:
                if "invalid_grant" in response_text:
                    return MullerIntuitivAuthError(
                        "Refresh token expired - please re-authenticate"
                    )
                if "invalid_client" in response_text:
                    return MullerIntuitivAuthError(
                        "Client authentication failed during token refresh"
                    )
                return MullerIntuitivAuthError("Bad request during token refresh")
            if status == 401:
                return MullerIntuitivAuthError("Unauthorized - refresh token invalid")
            return MullerIntuitivAuthError(f"Token refresh failed with status {status}")

        if status == 400:
            if "invalid_grant" in response_text:
                return MullerIntuitivAuthError("Invalid username or password")
            if "invalid_client" in response_text:
                return MullerIntuitivAuthError("Client authentication failed")
            return MullerIntuitivAuthError("Bad request - check credentials")
        if status == 401:
            return MullerIntuitivAuthError("Unauthorized - invalid credentials")
        return MullerIntuitivAuthError(f"Authentication failed with status {status}")

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with username and password and get tokens."""
        payload = {
            "client_id": CLIENT_ID,
            "user_prefix": USER_PREFIX,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "scope": SCOPE,
            "username": username,
            "password": password,
        }

        _LOGGER.debug("Attempting login for username: %s", username[:3] + "***")

        return await self._request_tokens(payload)

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token."""
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        _LOGGER.debug("Attempting to refresh token")

        return await self._request_tokens(payload, refreshing=True)

    async def _post(self, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a POST request to the API."""
        if not self._token:
            raise MullerIntuitivAuthError("No access token available")

        url = f"{API_BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}

        try:
            async with self._session.post(
                url,
                headers=headers,
                json=json_data,
                timeout=self._timeout,
            ) as response:
                if response.status == 401:
                    raise MullerIntuitivAuthError("Unauthorized")
                if response.status == 403:
                    raise MullerIntuitivAuthError("Forbidden - check credentials")
                if response.status >= 500:
                    raise MullerIntuitivApiError(f"Server error: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("API error %s: %s", response.status, error_text)
                    raise MullerIntuitivApiError(
                        f"API request failed with status {response.status}: {error_text}"
                    )

                return await response.json()
        except (aiohttp.ClientTimeout, aiohttp.ServerTimeoutError) as err:
            _LOGGER.error("Timeout error for %s: %s", url, err)
            raise MullerIntuitivTimeoutError(f"Request timeout for {endpoint}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error for %s: %s", url, err)
            raise MullerIntuitivConnectionError(f"Connection error for {endpoint}") from err

    async def get_homes_data(self) -> Dict[str, Any]:
        """Fetch home data including IDs, modes, and schedules."""
        _LOGGER.debug("Fetching homes data from /api/homesdata")
        res = await self._post("/api/homesdata")

        homes = res.get("body", {}).get("homes", [])
        if not homes:
            _LOGGER.error("No homes found in account response: %s", res)
            raise MullerIntuitivApiError("No homes found in account")

        home_data = homes[0]
        _LOGGER.debug(
            "Home data fetched successfully: ID=%s, Name=%s, Rooms=%d",
            home_data.get("id"),
            home_data.get("name", "Unknown"),
            len(home_data.get("rooms", [])),
        )
        return home_data

    async def get_home_status(self, home_id: str) -> List[Dict[str, Any]]:
        """Fetch status of all rooms in the home."""
        _LOGGER.debug("Fetching home status for home_id: %s", home_id)
        res = await self._post("/syncapi/v1/homestatus", json_data={"home_id": home_id})

        rooms = res.get("body", {}).get("home", {}).get("rooms", [])
        _LOGGER.debug("Home status fetched successfully: %d devices found", len(rooms))

        return rooms

    async def get_home_system_info(self, home_id: str) -> Dict[str, Any]:
        """Fetch complete system information including modules and sensors."""
        _LOGGER.debug("Fetching home system info for home_id: %s", home_id)
        res = await self._post("/syncapi/v1/homestatus", json_data={"home_id": home_id})
        home_data = res.get("body", {}).get("home", {})

        # Extract useful system information
        modules = home_data.get("modules", [])
        system_info = {
            "modules": modules,
            "outdoor_temperature": None,
            "wifi_strength": None,
            "firmware_info": {},
        }

        # Find outdoor temperature and system info from modules
        for module in modules:
            module_type = module.get("type", "")
            module_id = module.get("id", "")

            # NMG modules often contain outdoor temperature and wifi info
            if module_type == "NMG":
                if "outdoor_temperature" in module:
                    system_info["outdoor_temperature"] = module["outdoor_temperature"]
                if "wifi_strength" in module:
                    system_info["wifi_strength"] = module["wifi_strength"]
                if "firmware_revision" in module:
                    system_info["firmware_info"][module_id] = {
                        "firmware_revision": module["firmware_revision"],
                        "hardware_version": module.get("hardware_version"),
                        "type": module_type,
                        "uptime": module.get("uptime"),
                    }

        _LOGGER.debug(
            "System info extracted: outdoor_temp=%s, wifi=%s, modules=%d",
            system_info["outdoor_temperature"],
            system_info["wifi_strength"],
            len(modules),
        )
        return system_info

    async def set_room_mode(self, home_id: str, room_id: str, mode: str) -> None:
        """Set the mode for a specific room. (home, hg)."""
        _LOGGER.info("Setting room mode: home_id=%s, room_id=%s, mode=%s", home_id, room_id, mode)

        payload = {
            "home": {
                "id": home_id,
                "rooms": [
                    {
                        "id": room_id,
                        "therm_setpoint_mode": mode,
                    }
                ],
            }
        }
        # Based on Jeedom plugin, "home" mode disables boost
        if mode == "home":
            payload["home"]["rooms"][0]["boost"] = False
            _LOGGER.debug("Mode 'home' selected, disabling boost")

        _LOGGER.debug("Sending setstate payload: %s", payload)
        await self._post("/syncapi/v1/setstate", json_data=payload)
        _LOGGER.info("Successfully set room %s to mode %s", room_id, mode)

    async def set_room_temperature(
        self,
        home_id: str,
        room_id: str,
        temperature: float,
        default_duration_mins: int = DEFAULT_MANUAL_DURATION,
    ) -> None:
        """Set a manual temperature override for a room."""
        end_time = int(time.time()) + (default_duration_mins * 60)

        _LOGGER.info(
            "Setting room temperature: home_id=%s, room_id=%s, temp=%.1f°C, duration=%d mins",
            home_id,
            room_id,
            temperature,
            default_duration_mins,
        )

        payload = {
            "home": {
                "id": home_id,
                "rooms": [
                    {
                        "id": room_id,
                        "therm_setpoint_mode": "manual",
                        "therm_setpoint_temperature": temperature,
                        "therm_setpoint_end_time": end_time,
                    }
                ],
            }
        }

        _LOGGER.debug("Sending setstate payload: %s", payload)
        await self._post("/syncapi/v1/setstate", json_data=payload)
        _LOGGER.info("Successfully set room %s temperature to %.1f°C", room_id, temperature)

    async def set_home_mode(self, home_id: str, mode: str) -> None:
        """Set the mode for the entire home (schedule, hg, away)."""
        await self._post("/api/setthermmode", json_data={"home_id": home_id, "mode": mode})
