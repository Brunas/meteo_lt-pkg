"""MeteoLt API client for external API calls"""

import json
from typing import List

import aiohttp

from .models import Place, Forecast
from .const import BASE_URL, WARNINGS_URL, TIMEOUT, ENCODING


class MeteoLtClient:
    """Client for external API calls to meteo.lt"""

    async def fetch_places(self) -> List[Place]:
        """Gets all places from API"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            raise_for_status=True,
        ) as session:
            async with session.get(f"{BASE_URL}/places") as response:
                response.encoding = ENCODING
                response_json = await response.json()
                return [Place.from_dict(place) for place in response_json]

    async def fetch_forecast(self, place_code: str) -> Forecast:
        """Retrieves forecast data from API"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            raise_for_status=True,
        ) as session:
            async with session.get(
                f"{BASE_URL}/places/{place_code}/forecasts/long-term"
            ) as response:
                response.encoding = ENCODING
                response_json = await response.json()
                return Forecast.from_dict(response_json)

    async def fetch_weather_warnings(self) -> List[dict]:
        """Fetches raw weather warnings data from meteo.lt JSON API"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            raise_for_status=True,
        ) as session:
            async with session.get(WARNINGS_URL) as response:
                file_list = await response.json()

            if not file_list:
                return []

            # Fetch the latest warnings data
            latest_file_url = file_list[0]  # First file is the most recent
            async with session.get(latest_file_url) as response:
                text_data = await response.text()
                return json.loads(text_data)
