"""Unified warnings processor for handling weather and hydrological warning-related logic"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from .client import MeteoLtClient
from .const import COUNTY_MUNICIPALITIES, HYDRO_WARNINGS_URL, WARNINGS_URL
from .models import Forecast, MeteoWarning

WarningCategory = Literal["weather", "hydro"]


class WarningsProcessor:
    """Processes weather and hydrological warnings data and handles warning-related logic"""

    def __init__(self, client: MeteoLtClient, category: WarningCategory = "weather"):
        self.client = client
        self.category = category

    async def get_warnings(self, administrative_division: str = None) -> List[MeteoWarning]:
        """Fetches and processes warnings (weather or hydro based on category)"""
        # Determine URL based on category
        warnings_url = HYDRO_WARNINGS_URL if self.category == "hydro" else WARNINGS_URL

        # Fetch warnings data
        warnings_data = await self.client.fetch_warnings(warnings_url)
        warnings = self._parse_warnings_data(warnings_data)

        # Filter by administrative division if specified
        if administrative_division:
            warnings = [w for w in warnings if self._warning_affects_area(w, administrative_division)]

        return warnings

    def _parse_warnings_data(self, warnings_data: Optional[Dict[str, Any]]) -> List[MeteoWarning]:
        """Parse raw warnings data into MeteoWarning objects"""
        warnings = []

        # Handle empty response (list instead of dict)
        if not warnings_data or isinstance(warnings_data, list):
            return warnings

        # Parse the warnings data
        for phenomenon_group in warnings_data.get("phenomenon_groups", []):
            phenomenon_category = phenomenon_group.get("phenomenon_category")

            # Filter based on category
            if self.category == "hydro" and phenomenon_category != "hydrological":
                continue
            if self.category == "weather" and phenomenon_category == "hydrological":
                continue

            for area_group in phenomenon_group.get("area_groups", []):
                for alert in area_group.get("single_alerts", []):
                    # Skip alerts with no phenomenon or empty descriptions
                    if not alert.get("phenomenon") or not alert.get("description", {}).get("lt"):
                        continue

                    # Create warnings for each area in the group
                    for area in area_group.get("areas", []):
                        warning = self._create_warning_from_alert(alert, area)
                        if warning:
                            warnings.append(warning)

        return warnings

    def _create_warning_from_alert(self, alert: Dict[str, Any], area: Dict[str, Any]) -> MeteoWarning:
        """Create a MeteoWarning from alert data"""
        administrative_area = area.get("name", "Unknown")
        phenomenon = alert.get("phenomenon", "")
        severity = alert.get("severity", "Minor")

        warning_type = re.sub(r"^(dangerous|severe|extreme)-", "", phenomenon)

        desc_dict = alert.get("description", {})
        inst_dict = alert.get("instruction", {})

        description = desc_dict.get("en") or desc_dict.get("lt", "")
        instruction = inst_dict.get("en") or inst_dict.get("lt", "") or None

        return MeteoWarning(
            administrative_area=administrative_area,
            warning_type=warning_type,
            severity=severity,
            description=description,
            category=self.category,
            start_time=alert.get("t_from"),
            end_time=alert.get("t_to"),
            instruction=instruction,
        )

    def _warning_affects_area(self, warning: MeteoWarning, administrative_division: str) -> bool:
        """Check if warning affects specified administrative division"""
        admin_lower = administrative_division.lower().replace(" savivaldybė", "").replace(" sav.", "")

        # Check if the administrative division matches the warning area
        if admin_lower in warning.administrative_area.lower():
            return True

        # Check if the administrative division is in the warning area's municipalities
        if warning.administrative_area in COUNTY_MUNICIPALITIES:
            municipalities = COUNTY_MUNICIPALITIES[warning.administrative_area]
            for municipality in municipalities:
                mun_clean = municipality.lower().replace(" savivaldybė", "").replace(" sav.", "")
                if admin_lower in mun_clean or mun_clean in admin_lower:
                    return True

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
            if not hasattr(forecast.current_conditions, "warnings"):
                forecast.current_conditions.warnings = []
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
