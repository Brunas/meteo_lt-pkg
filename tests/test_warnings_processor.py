"""Tests for weather warnings processor"""

# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import patch

import pytest

from meteo_lt import WeatherWarning
from meteo_lt.client import MeteoLtClient
from meteo_lt.warnings import WeatherWarningsProcessor


@pytest.fixture
def client():
    """Create client for testing"""
    return MeteoLtClient()


@pytest.fixture
def warnings_processor(client):
    """Create warnings processor for testing"""
    return WeatherWarningsProcessor(client)


@pytest.fixture
def mock_warnings_data():
    """Mock warnings JSON data"""
    return {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [
                            {"id": "lt.lhms.county:LT002", "name": "Kauno apskritis"}
                        ],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {
                                    "en": "Strong wind up to 20 m/s",
                                    "lt": "Stiprus vėjas iki 20 m/s",
                                },
                                "instruction": {
                                    "en": "Be careful",
                                    "lt": "Būkite atsargūs",
                                },
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }


def test_parse_warnings_data(warnings_processor, mock_warnings_data):
    """Test parsing warnings data"""
    warnings = warnings_processor._parse_warnings_data(mock_warnings_data)

    assert len(warnings) == 1
    assert warnings[0].county == "Kauno apskritis"
    assert warnings[0].warning_type == "wind"
    assert warnings[0].severity == "Moderate"


def test_parse_warnings_data_empty(warnings_processor):
    """Test parsing empty warnings data"""
    # Test with empty list
    warnings = warnings_processor._parse_warnings_data([])
    assert warnings == []

    # Test with empty dict
    warnings = warnings_processor._parse_warnings_data({})
    assert warnings == []

    # Test with None
    warnings = warnings_processor._parse_warnings_data(None)
    assert warnings == []


def test_create_warning_from_alert(warnings_processor):
    """Test creating warning from alert data"""
    alert = {
        "phenomenon": "wind",
        "severity": "Moderate",
        "description": {"en": "Strong wind", "lt": "Stiprus vėjas"},
        "instruction": {"en": "Be careful", "lt": "Būkite atsargūs"},
        "t_from": "2025-09-30T12:00:00Z",
        "t_to": "2025-09-30T18:00:00Z",
    }

    area = {"name": "Kauno apskritis"}

    warning = warnings_processor._create_warning_from_alert(alert, area)

    assert warning is not None
    assert warning.county == "Kauno apskritis"
    assert warning.warning_type == "wind"
    assert warning.severity == "Moderate"
    assert "Be careful" in warning.description


def test_warning_affects_area(warnings_processor):
    """Test if warning affects specific administrative division"""
    warning = WeatherWarning(
        county="Kauno apskritis",
        warning_type="wind",
        severity="Moderate",
        description="Test warning",
    )

    assert warnings_processor._warning_affects_area(warning, "Kauno miesto")
    assert warnings_processor._warning_affects_area(warning, "Kauno rajono")
    assert not warnings_processor._warning_affects_area(warning, "Vilniaus miesto")


def test_get_warnings_for_timestamp(warnings_processor):
    """Test getting warnings for specific timestamp"""
    warnings = [
        WeatherWarning(
            county="Kauno apskritis",
            warning_type="wind",
            severity="Moderate",
            description="Strong wind",
            start_time="2025-09-30T12:00:00Z",
            end_time="2025-09-30T18:00:00Z",
        )
    ]

    # Test timestamp within warning period
    applicable = warnings_processor._get_warnings_for_timestamp(
        "2025-09-30T15:00:00+00:00", warnings
    )
    assert len(applicable) == 1
    assert applicable[0].warning_type == "wind"

    # Test timestamp outside warning period
    applicable = warnings_processor._get_warnings_for_timestamp(
        "2025-09-30T20:00:00+00:00", warnings
    )
    assert len(applicable) == 0

    # Test timestamp before warning period
    applicable = warnings_processor._get_warnings_for_timestamp(
        "2025-09-30T10:00:00+00:00", warnings
    )
    assert len(applicable) == 0


@pytest.mark.asyncio
async def test_get_weather_warnings(warnings_processor, mock_warnings_data):
    """Test getting weather warnings"""
    with patch.object(
        warnings_processor.client, "fetch_weather_warnings"
    ) as mock_fetch:
        mock_fetch.return_value = mock_warnings_data

        warnings = await warnings_processor.get_weather_warnings()

        assert len(warnings) == 1
        assert warnings[0].county == "Kauno apskritis"


@pytest.mark.asyncio
async def test_get_weather_warnings_filtered(warnings_processor, mock_warnings_data):
    """Test getting weather warnings filtered by area"""
    with patch.object(
        warnings_processor.client, "fetch_weather_warnings"
    ) as mock_fetch:
        mock_fetch.return_value = mock_warnings_data

        warnings = await warnings_processor.get_weather_warnings("Kauno miesto")

        assert len(warnings) == 1
        assert warnings[0].county == "Kauno apskritis"

        # Test with non-matching area
        warnings = await warnings_processor.get_weather_warnings("Vilniaus miesto")
        assert len(warnings) == 0
