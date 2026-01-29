"""MeteoLt API client for external API calls"""

import json
from typing import List, Optional, Dict, Any

import aiohttp

from .models import (
    Place,
    Forecast,
    HydroStation,
    HydroObservationData,
    HydroObservation,
)
from .const import BASE_URL, WARNINGS_URL, TIMEOUT, ENCODING


class MeteoLtClient:
    """Client for external API calls to meteo.lt"""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self):
        """Async context manager entry"""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=TIMEOUT),
                raise_for_status=True,
            )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        """Async context manager exit"""
        await self.close()

    async def close(self) -> None:
        """Close the client session if we own it"""
        if self._session and self._owns_session:
            await self._session.close()
            self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a session"""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=TIMEOUT),
                raise_for_status=True,
            )
        return self._session

    async def fetch_places(self) -> List[Place]:
        """Gets all places from API"""
        session = await self._get_session()
        async with session.get(f"{BASE_URL}/places") as response:
            response.encoding = ENCODING
            response_json = await response.json()
            return [Place.from_dict(place) for place in response_json]

    async def fetch_forecast(self, place_code: str) -> Forecast:
        """Retrieves forecast data from API"""
        session = await self._get_session()
        async with session.get(f"{BASE_URL}/places/{place_code}/forecasts/long-term") as response:
            response.encoding = ENCODING
            response_json = await response.json()
            return Forecast.from_dict(response_json)

    async def fetch_weather_warnings(self) -> Dict[str, Any]:
        """Fetches raw weather warnings data from meteo.lt JSON API"""
        session = await self._get_session()

        # Get the latest warnings file
        async with session.get(WARNINGS_URL) as response:
            file_list = await response.json()

        if not file_list:
            return []

        # Fetch the latest warnings data
        latest_file_url = file_list[0]  # First file is the most recent
        async with session.get(latest_file_url) as response:
            text_data = await response.text()
            return json.loads(text_data)

    async def fetch_hydro_stations(self) -> List[HydroStation]:
        """Get list of all hydrological stations."""
        session = await self._get_session()
        async with session.get(f"{BASE_URL}/hydro-stations") as resp:
            if resp.status == 200:
                resp.encoding = ENCODING
                response = await resp.json()
                stations = []
                for station_data in response:
                    stations.append(HydroStation.from_dict(station_data))
                return stations
            else:
                raise Exception(f"API returned status {resp.status}")

    async def fetch_hydro_station(self, station_code: str) -> HydroStation:
        """Get information about a specific hydrological station."""
        session = await self._get_session()
        async with session.get(f"{BASE_URL}/hydro-stations/{station_code}") as resp:
            if resp.status == 200:
                resp.encoding = ENCODING
                response = await resp.json()
                return HydroStation.from_dict(response)
            else:
                raise Exception(f"API returned status {resp.status}")

    async def fetch_hydro_observation_data(
        self,
        station_code: str,
        observation_type: str = "measured",
        date: str = "latest",
    ) -> HydroObservationData:
        """Get hydrological observation data for a station."""
        session = await self._get_session()
        async with session.get(
            f"{BASE_URL}/hydro-stations/{station_code}/observations/{observation_type}/{date}"
        ) as resp:
            if resp.status == 200:
                response = await resp.json()
                station = HydroStation.from_dict(response.get("station"))

                observations = []
                for obs_data in response.get("observations", []):
                    observations.append(HydroObservation.from_dict(obs_data))

                return HydroObservationData(
                    station=station,
                    observations_data_range=response.get("observationsDataRange"),
                    observations=observations,
                )
            else:
                raise Exception(f"API returned status {resp.status}")
