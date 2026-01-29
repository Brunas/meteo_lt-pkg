"""Main API class script"""

from typing import List, Optional

from .models import (
    Forecast,
    Place,
    WeatherWarning,
    HydroStation,
    HydroObservationData,
)
from .utils import find_nearest_location
from .client import MeteoLtClient
from .warnings import WeatherWarningsProcessor


class MeteoLtAPI:
    """Main API class that orchestrates external API calls and warning processing"""

    def __init__(self, session=None):
        self.places = []
        self.client = MeteoLtClient(session)
        self.warnings_processor = WeatherWarningsProcessor(self.client)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[object],
    ) -> None:
        """Async context manager exit"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        """Close the API client and cleanup resources"""
        await self.client.close()

    async def fetch_places(self) -> None:
        """Gets all places from API"""
        self.places = await self.client.fetch_places()

    async def get_nearest_place(self, latitude: float, longitude: float) -> Optional[Place]:
        """Finds nearest place using provided coordinates"""
        if not self.places:
            await self.fetch_places()
        return find_nearest_location(latitude, longitude, self.places)

    async def get_forecast_with_warnings(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        place_code: Optional[str] = None,
    ) -> Forecast:
        """Get forecast with weather warnings for a location"""
        if place_code is None:
            if latitude is None or longitude is None:
                raise ValueError("Either place_code or both latitude and longitude must be provided")
            place = await self.get_nearest_place(latitude, longitude)
            place_code = place.code

        return await self.get_forecast(place_code, include_warnings=True)

    async def get_forecast(self, place_code: str, include_warnings: bool = True) -> Forecast:
        """Retrieves forecast data from API"""
        forecast = await self.client.fetch_forecast(place_code)

        if include_warnings:
            await self._enrich_forecast_with_warnings(forecast)

        return forecast

    async def get_weather_warnings(self, administrative_division: str = None) -> List[WeatherWarning]:
        """Fetches weather warnings from meteo.lt JSON API"""
        return await self.warnings_processor.get_weather_warnings(administrative_division)

    async def _enrich_forecast_with_warnings(self, forecast: Forecast) -> None:
        """Enrich forecast timestamps with relevant weather warnings"""
        if not forecast or not forecast.place or not forecast.place.administrative_division:
            return

        warnings = await self.get_weather_warnings(forecast.place.administrative_division)

        if warnings:
            self.warnings_processor.enrich_forecast_with_warnings(forecast, warnings)

    async def get_hydro_stations(self) -> List[HydroStation]:
        """Get list of all hydrological stations"""
        return await self.client.fetch_hydro_stations()

    async def get_nearest_hydro_station(self, latitude: float, longitude: float) -> Optional[HydroStation]:
        """Find the nearest hydrological station to given coordinates"""
        stations = await self.get_hydro_stations()
        if not stations:
            return None
        return find_nearest_location(latitude, longitude, stations)

    async def get_hydro_observation_data(
        self,
        station_code: str,
        observation_type: str = "measured",
        date: str = "latest",
    ) -> HydroObservationData:
        """Get hydrological observation data for a station"""
        return await self.client.fetch_hydro_observation_data(station_code, observation_type, date)
