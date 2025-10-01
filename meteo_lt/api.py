"""New API class script"""

import json
import re
from datetime import datetime, timezone
from typing import List

import aiohttp

from .models import Place, Forecast, WeatherWarning
from .utils import find_nearest_place
from .const import COUNTY_MUNICIPALITIES


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
        return find_nearest_place(latitude, longitude, self.places)

    async def get_forecast_with_warnings(
        self, latitude=None, longitude=None, place_code=None
    ):
        """Get forecast with weather warnings for a location"""
        if place_code is None:
            if latitude is None or longitude is None:
                raise ValueError(
                    "Either place_code or both latitude and longitude must be provided"
                )
            place = await self.get_nearest_place(latitude, longitude)
            place_code = place.code

        return await self.get_forecast(place_code, include_warnings=True)

    async def get_forecast(self, place_code, include_warnings=True):
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
                forecast = Forecast.from_dict(response_json)

                if include_warnings:
                    await self._enrich_forecast_with_warnings(forecast)

                return forecast

    async def get_weather_warnings(
        self, administrative_division: str = None
    ) -> List[WeatherWarning]:
        """Fetches weather warnings from meteo.lt JSON API"""

        # First get the list of available JSON files
        list_url = (
            "https://www.meteo.lt/app/mu-plugins/Meteo/Components/"
            "WeatherWarningsNew/list_JSON.php"
        )

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
        ) as session:
            # Get the latest warnings file
            async with session.get(list_url) as response:
                await response.raise_for_status()
                file_list = await response.json()

            if not file_list:
                return []

            # Fetch the latest warnings data
            latest_file_url = file_list[0]  # First file is the most recent
            async with session.get(latest_file_url) as response:
                await response.raise_for_status()
                text_data = await response.text()
                warnings_data = json.loads(text_data)

        warnings = []

        # Parse the warnings data
        for phenomenon_group in warnings_data.get("phenomenon_groups", []):
            # Skip hydrological warnings if needed (they're usually for water levels)
            if phenomenon_group.get("phenomenon_category") == "hydrological":
                continue

            for area_group in phenomenon_group.get("area_groups", []):
                for alert in area_group.get("single_alerts", []):
                    # Skip alerts with no phenomenon or empty descriptions
                    if not alert.get("phenomenon") or not alert.get(
                        "description", {}
                    ).get("lt"):
                        continue

                    # Create warnings for each area in the group
                    for area in area_group.get("areas", []):
                        warning = self._create_warning_from_alert(alert, area)
                        if warning:
                            warnings.append(warning)

        # Filter by administrative division if specified
        if administrative_division:
            warnings = [
                w
                for w in warnings
                if self._warning_affects_area(w, administrative_division)
            ]

        return warnings

    def _create_warning_from_alert(self, alert: dict, area: dict) -> WeatherWarning:
        """Create a WeatherWarning from alert data"""
        try:
            county = area.get("name", "Unknown")
            phenomenon = alert.get("phenomenon", "")
            severity = alert.get("severity", "Minor")

            # Clean phenomenon name (remove severity prefixes)
            warning_type = re.sub(r"^(dangerous|severe|extreme)-", "", phenomenon)

            # Get descriptions and instructions
            desc_dict = alert.get("description", {})
            inst_dict = alert.get("instruction", {})

            # Prefer English, fall back to Lithuanian
            description = desc_dict.get("en") or desc_dict.get("lt", "")
            instruction = inst_dict.get("en") or inst_dict.get("lt", "")

            # Combine description and instruction
            full_description = description
            if instruction:
                full_description += f"\n\nRecommendations: {instruction}"

            return WeatherWarning(
                county=county,
                warning_type=warning_type,
                severity=severity,
                description=full_description,
                start_time=alert.get("t_from"),
                end_time=alert.get("t_to"),
            )
        except Exception as e:
            print(f"Error creating warning: {e}")
            return None

    def _warning_affects_area(
        self, warning: WeatherWarning, administrative_division: str
    ) -> bool:
        """Check if warning affects specified administrative division"""
        admin_lower = (
            administrative_division.lower()
            .replace(" savivaldybė", "")
            .replace(" sav.", "")
        )

        # Check if the administrative division matches the warning county
        if admin_lower in warning.county.lower():
            return True

        # Check if the administrative division is in the warning's county municipalities
        if warning.county in COUNTY_MUNICIPALITIES:
            municipalities = COUNTY_MUNICIPALITIES[warning.county]
            for municipality in municipalities:
                mun_clean = (
                    municipality.lower()
                    .replace(" savivaldybė", "")
                    .replace(" sav.", "")
                )
                if admin_lower in mun_clean or mun_clean in admin_lower:
                    return True

        return False

    async def _enrich_forecast_with_warnings(self, forecast: Forecast):
        """Enrich forecast timestamps with relevant weather warnings"""
        try:
            # Get warnings for the forecast location
            warnings = await self.get_weather_warnings(
                forecast.place.administrative_division
            )

            if not warnings:
                return

            # For each forecast timestamp, find applicable warnings
            for timestamp in forecast.forecast_timestamps:
                timestamp.warnings = self._get_warnings_for_timestamp(
                    timestamp.datetime, warnings
                )

            # Also add warnings to current conditions if available
            if hasattr(forecast, "current_conditions") and forecast.current_conditions:
                forecast.current_conditions.warnings = self._get_warnings_for_timestamp(
                    forecast.current_conditions.datetime, warnings
                )

        except Exception as e:
            # Don't fail the entire forecast if warnings can't be fetched
            print(f"Warning: Could not fetch weather warnings: {e}")

    def _get_warnings_for_timestamp(
        self, timestamp_str: str, warnings: List[WeatherWarning]
    ) -> List[WeatherWarning]:
        """Get warnings that are active for a specific timestamp"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str).replace(
                tzinfo=timezone.utc
            )
            applicable_warnings = []

            for warning in warnings:
                if not warning.start_time or not warning.end_time:
                    continue

                try:
                    start_time = datetime.fromisoformat(
                        warning.start_time.replace("Z", "+00:00")
                    )
                    end_time = datetime.fromisoformat(
                        warning.end_time.replace("Z", "+00:00")
                    )

                    # Check if timestamp falls within warning period
                    if start_time <= timestamp <= end_time:
                        applicable_warnings.append(warning)

                except (ValueError, AttributeError):
                    # Skip warnings with invalid time formats
                    continue

            return applicable_warnings

        except (ValueError, AttributeError):
            # Return empty list if timestamp parsing fails
            return []
