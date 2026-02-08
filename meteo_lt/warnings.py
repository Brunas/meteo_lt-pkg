"""Unified warnings processor for handling weather and hydrological warning-related logic"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from .client import MeteoLtClient
from .const import COUNTY_MUNICIPALITIES, WARNINGS_URL
from .models import Forecast, MeteoWarning
from .utils import normalize_administrative_division

WarningCategory = Literal["weather", "hydro"]


class WarningsProcessor:
    """Processes weather and hydrological warnings data and handles warning-related logic"""

    def __init__(self, client: MeteoLtClient):
        self.client = client

    async def get_weather_warnings(self, administrative_division: str = None) -> List[MeteoWarning]:
        """Fetches weather warnings from meteo.lt JSON API"""
        return await self._get_warnings_by_category("weather", administrative_division)

    async def get_hydro_warnings(self, administrative_division: str = None) -> List[MeteoWarning]:
        """Fetches hydrological warnings from meteo.lt JSON API"""
        return await self._get_warnings_by_category("hydro", administrative_division)

    async def get_all_warnings(self, administrative_division: str = None) -> List[MeteoWarning]:
        """Fetches both weather and hydrological warnings from meteo.lt JSON API"""
        warnings_data = await self.client.fetch_warnings(WARNINGS_URL)
        weather_warnings = self._parse_warnings_data(warnings_data, "weather")
        hydro_warnings = self._parse_warnings_data(warnings_data, "hydro")
        all_warnings = weather_warnings + hydro_warnings

        # Filter by administrative division if specified
        if administrative_division:
            all_warnings = [w for w in all_warnings if self._warning_affects_area(w, administrative_division)]

        return all_warnings

    async def _get_warnings_by_category(
        self, category: WarningCategory, administrative_division: str = None
    ) -> List[MeteoWarning]:
        """Internal method to get warnings filtered by category"""
        warnings_data = await self.client.fetch_warnings(WARNINGS_URL)
        warnings = self._parse_warnings_data(warnings_data, category)

        # Filter by administrative division if specified
        if administrative_division:
            warnings = [w for w in warnings if self._warning_affects_area(w, administrative_division)]

        return warnings

    def _parse_warnings_data(
        self, warnings_data: Optional[Dict[str, Any]], category: WarningCategory
    ) -> List[MeteoWarning]:
        """Parse raw warnings data into MeteoWarning objects filtered by category"""
        warnings = []

        # Handle empty response (list instead of dict)
        if not warnings_data or isinstance(warnings_data, list):
            return warnings

        # Parse the warnings data
        for phenomenon_group in warnings_data.get("phenomenon_groups", []):
            # Filter by phenomenon category based on requested category
            phenomenon_category = phenomenon_group.get("phenomenon_category", "")
            if not self._is_matching_category(phenomenon_category, category):
                continue

            for area_group in phenomenon_group.get("area_groups", []):
                for alert in area_group.get("single_alerts", []):
                    # Skip alerts with no phenomenon or empty descriptions
                    if not alert.get("phenomenon") or not alert.get("description", {}).get("lt"):
                        continue

                    # Create warnings for each area in the group
                    for area in area_group.get("areas", []):
                        warning = self._create_warning_from_alert(alert, area, category)
                        if warning:
                            warnings.append(warning)

        return warnings

    def _is_matching_category(self, phenomenon_category: str, category: WarningCategory) -> bool:
        """Check if phenomenon category matches the requested category type"""
        hydro_categories = {"hydrological", "hydrological-sea"}

        if category == "hydro":
            return phenomenon_category in hydro_categories
        else:  # weather
            return phenomenon_category not in hydro_categories

    def _create_warning_from_alert(
        self, alert: Dict[str, Any], area: Dict[str, Any], category: WarningCategory
    ) -> MeteoWarning:
        """Create a MeteoWarning from alert data"""
        administrative_division = area.get("name", "Unknown")
        phenomenon = alert.get("phenomenon", "")
        severity = alert.get("severity", "Minor")

        warning_type = re.sub(r"^(dangerous|severe|extreme)-", "", phenomenon)

        desc_dict = alert.get("description", {})
        inst_dict = alert.get("instruction", {})

        description = desc_dict.get("en") or desc_dict.get("lt", "")
        instruction = inst_dict.get("en") or inst_dict.get("lt", "") or None

        return MeteoWarning(
            administrative_division=administrative_division,
            warning_type=warning_type,
            severity=severity,
            description=description,
            category=category,
            start_time=alert.get("t_from"),
            end_time=alert.get("t_to"),
            instruction=instruction,
        )

    def _warning_affects_area(self, warning: MeteoWarning, administrative_division: str) -> bool:
        """Check if warning affects the specified municipality."""
        municipality_norm = normalize_administrative_division(administrative_division)
        warning_area_norm = normalize_administrative_division(warning.administrative_division)

        # Direct match: warning is for this specific municipality
        if municipality_norm in warning_area_norm or warning_area_norm in municipality_norm:
            return True

        # County match: warning is for a county that contains this municipality
        if warning.administrative_division in COUNTY_MUNICIPALITIES:
            municipalities_in_county = COUNTY_MUNICIPALITIES[warning.administrative_division]
            municipalities_norm = [normalize_administrative_division(m) for m in municipalities_in_county]
            return any(municipality_norm in m_norm or m_norm in municipality_norm for m_norm in municipalities_norm)

        return False

    def enrich_forecast_with_warnings(self, forecast: Forecast, warnings: List[MeteoWarning]) -> None:
        """Enrich forecast timestamps with relevant warnings"""
        if not warnings:
            return

        # For each forecast timestamp, find applicable warnings
        for timestamp in forecast.forecast_timestamps:
            # Initialize warnings list if it doesn't exist
            if not hasattr(timestamp, "warnings"):
                timestamp.warnings = []
            # Get warnings for this timestamp and extend the list
            applicable_warnings = self._get_warnings_for_timestamp(timestamp.datetime, warnings)
            timestamp.warnings.extend(applicable_warnings)

        # Also add warnings to current conditions if available
        if hasattr(forecast, "current_conditions") and forecast.current_conditions:
            applicable_warnings = self._get_warnings_for_timestamp(forecast.current_conditions.datetime, warnings)
            forecast.current_conditions.warnings.extend(applicable_warnings)

    def _get_warnings_for_timestamp(self, timestamp_str: str, warnings: List[MeteoWarning]) -> List[MeteoWarning]:
        """Get warnings that are active for a specific timestamp"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str).astimezone(timezone.utc)
        except (ValueError, AttributeError):
            return []

        # Forecast timestamp represents an hour starting at this time
        hour_start = timestamp
        hour_end = timestamp + timedelta(hours=1)

        applicable_warnings = []

        for warning in warnings:
            try:
                start_time = datetime.fromisoformat(warning.start_time).astimezone(timezone.utc)
                end_time = datetime.fromisoformat(warning.end_time).astimezone(timezone.utc)
            except (ValueError, AttributeError, TypeError):
                continue

            # Check if warning period overlaps with the hour
            # Warning overlaps if it starts before hour ends AND ends after hour starts
            if start_time < hour_end and end_time > hour_start:
                applicable_warnings.append(warning)

        return applicable_warnings
