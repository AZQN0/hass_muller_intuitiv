import aiohttp
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .const import API_BASE_URL, CLIENT_ID, CLIENT_SECRET, USER_PREFIX, SCOPE

_LOGGER = logging.getLogger(__name__)

class MullerIntuitivAuthError(Exception):
    """Exception for authentication errors."""

class MullerIntuitivApiError(Exception):
    """Exception for general API errors."""

class MullerIntuitivApi:
    """API Client for Muller Intuitiv."""

    def __init__(self, session: aiohttp.ClientSession, token: Optional[str] = None):
        """Initialize the API client."""
        self._session = session
        self._token = token

    def set_token(self, token: str) -> None:
        """Set the access token."""
        self._token = token

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with username and password and get tokens."""
        url = f"{API_BASE_URL}/oauth2/token"
        payload = {
            "client_id": CLIENT_ID,
            "user_prefix": USER_PREFIX,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "scope": SCOPE,
            "username": username,
            "password": password,
        }
        
        async with self._session.post(url, data=payload) as response:
            if response.status != 200:
                _LOGGER.error("Failed to authenticate: %s", await response.text())
                raise MullerIntuitivAuthError("Authentication failed")
            
            data = await response.json()
            self._token = data.get("access_token")
            return data

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token."""
        url = f"{API_BASE_URL}/oauth2/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        async with self._session.post(url, data=payload) as response:
            if response.status != 200:
                _LOGGER.error("Failed to refresh token: %s", await response.text())
                raise MullerIntuitivAuthError("Token refresh failed")
            
            data = await response.json()
            self._token = data.get("access_token")
            return data

    async def _post(self, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a POST request to the API."""
        if not self._token:
            raise MullerIntuitivAuthError("No access token available")

        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json"
        }

        async with self._session.post(url, headers=headers, json=json_data) as response:
            if response.status == 401:
                raise MullerIntuitivAuthError("Unauthorized")
            if response.status != 200:
                _LOGGER.error("API error %s: %s", response.status, await response.text())
                raise MullerIntuitivApiError(f"API request failed with status {response.status}")
            
            return await response.json()

    async def get_homes_data(self) -> Dict[str, Any]:
        """Fetch home data including IDs, modes, and schedules."""
        res = await self._post("/api/homesdata")
        return res.get("body", {}).get("homes", [])[0]

    async def get_home_status(self, home_id: str) -> List[Dict[str, Any]]:
        """Fetch status of all rooms in the home."""
        res = await self._post("/syncapi/v1/homestatus", json_data={"home_id": home_id})
        return res.get("body", {}).get("home", {}).get("rooms", [])

    async def set_room_mode(self, home_id: str, room_id: str, mode: str) -> None:
        """Set the mode for a specific room. (home, hg)."""
        payload = {
            "home": {
                "id": home_id,
                "rooms": [
                    {
                        "id": room_id,
                        "therm_setpoint_mode": mode,
                    }
                ]
            }
        }
        # Based on Jeedom plugin, "home" mode disables boost
        if mode == "home":
            payload["home"]["rooms"][0]["boost"] = False
            
        await self._post("/syncapi/v1/setstate", json_data=payload)

    async def set_room_temperature(self, home_id: str, room_id: str, temperature: float, default_duration_mins: int = 120) -> None:
        """Set a manual temperature override for a room."""
        import time
        end_time = int(time.time()) + (default_duration_mins * 60)
        
        payload = {
            "home": {
                "id": home_id,
                "rooms": [
                    {
                        "id": room_id,
                        "therm_setpoint_mode": "manual",
                        "therm_setpoint_temperature": temperature,
                        "therm_setpoint_end_time": end_time
                    }
                ]
            }
        }
        await self._post("/syncapi/v1/setstate", json_data=payload)

    async def set_home_mode(self, home_id: str, mode: str) -> None:
        """Set the mode for the entire home (schedule, hg, away)."""
        await self._post("/api/setthermmode", json_data={"home_id": home_id, "mode": mode})
