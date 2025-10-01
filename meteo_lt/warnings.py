"""Weather warnings processor for handling warning-related logic"""

# pylint: disable=W0718

import re
from datetime import datetime, timezone
from typing import List

from .models import Forecast, WeatherWarning
from .const import COUNTY_MUNICIPALITIES
from .client import MeteoLtClient


class WeatherWarningsProcessor:
    """Processes weather warnings data and handles warning-related logic"""

    def __init__(self, client: MeteoLtClient):
        self.client = client

    async def get_weather_warnings(
        self, administrative_division: str = None
    ) -> List[WeatherWarning]:
        """Fetches and processes weather warnings"""
        warnings_data = await self.client.fetch_weather_warnings()
        warnings = self._parse_warnings_data(warnings_data)

        # Filter by administrative division if specified
        if administrative_division:
            warnings = [
                w
                for w in warnings
                if self._warning_affects_area(w, administrative_division)
            ]

        return warnings

    def _parse_warnings_data(self, warnings_data: dict) -> List[WeatherWarning]:
        """Parse raw warnings data into WeatherWarning objects"""
        warnings = []

        # Handle empty response (list instead of dict)
        if not warnings_data or isinstance(warnings_data, list):
            return warnings

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

    def enrich_forecast_with_warnings(
        self, forecast: Forecast, warnings: List[WeatherWarning]
    ):
        """Enrich forecast timestamps with relevant weather warnings"""
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
