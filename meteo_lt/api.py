"""Main API class script"""

import aiohttp
from scipy.spatial import KDTree
import numpy as np

from .models import Place, Forecast


class MeteoLtAPI:
    """Main API class"""

    BASE_URL = "https://api.meteo.lt/v1"
    TIMEOUT = 30
    ENCODING = "utf-8"

    def __init__(self):
        self.places = []

    async def fetch_places(self):
        """Gets all places from API"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
        ) as session:
            async with session.get(f"{self.BASE_URL}/places") as response:
                response.raise_for_status()
                response.encoding = self.ENCODING
                response_json = await response.json()
                self.places = [Place.from_dict(place) for place in response_json]

    async def get_nearest_place(self, latitude, longitude):
        """Finds nearest place using provided coordinates"""
        if not self.places:
            await self.fetch_places()
        coordinates = np.array(
            [[place.latitude, place.longitude] for place in self.places]
        )
        tree = KDTree(coordinates)
        _, idx = tree.query([latitude, longitude])
        return self.places[idx]

    async def get_forecast(self, place_code):
        """Retrieves forecast data from API"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
        ) as session:
            async with session.get(
                f"{self.BASE_URL}/places/{place_code}/forecasts/long-term"
            ) as response:
                response.raise_for_status()
                response.encoding = self.ENCODING
                response_json = await response.json()
                return Forecast.from_dict(response_json)
