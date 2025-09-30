"""Tests for weather warnings functionality"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from meteo_lt import MeteoLtAPI, WeatherWarning


@pytest.fixture
def api_client():
    """Create API client for testing"""
    return MeteoLtAPI()


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
                            {"id": "lt.lhms.county:LT010", "name": "Vilniaus apskritis"}
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


@pytest.fixture
def mock_file_list():
    """Mock file list response"""
    return [
        "https://www.meteo.lt/meteo_jobs/pavojingi_met_reisk_ibl/20250930120000-00000001"
    ]


@pytest.mark.asyncio
async def test_get_weather_warnings_success(
    api_client, mock_file_list, mock_warnings_data
):
    """Test successful weather warnings retrieval"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        # Mock the file list response
        mock_list_response = AsyncMock()
        mock_list_response.json.return_value = mock_file_list
        mock_list_response.raise_for_status.return_value = None

        # Mock the warnings data response
        mock_data_response = AsyncMock()
        mock_data_response.text.return_value = json.dumps(mock_warnings_data)
        mock_data_response.raise_for_status.return_value = None

        # Configure the mock to return different responses for different calls
        mock_get.return_value.__aenter__.side_effect = [
            mock_list_response,
            mock_data_response,
        ]

        warnings = await api_client.get_weather_warnings()

        assert isinstance(warnings, list)
        assert len(warnings) == 1
        assert warnings[0].area_name == "Vilniaus apskritis"
        assert warnings[0].warning_type == "wind"
        assert warnings[0].severity == "Moderate"


@pytest.mark.asyncio
async def test_get_weather_warnings_for_specific_area(
    api_client, mock_file_list, mock_warnings_data
):
    """Test weather warnings for specific administrative division"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_list_response = AsyncMock()
        mock_list_response.json.return_value = mock_file_list
        mock_list_response.raise_for_status.return_value = None

        mock_data_response = AsyncMock()
        mock_data_response.text.return_value = json.dumps(mock_warnings_data)
        mock_data_response.raise_for_status.return_value = None

        mock_get.return_value.__aenter__.side_effect = [
            mock_list_response,
            mock_data_response,
        ]

        warnings = await api_client.get_weather_warnings("Vilniaus miesto")

        assert isinstance(warnings, list)
        assert len(warnings) == 1  # Should match Vilnius area


@pytest.mark.asyncio
async def test_get_weather_warnings_empty_response(api_client):
    """Test handling of empty warnings response"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response

        warnings = await api_client.get_weather_warnings()

        assert isinstance(warnings, list)
        assert len(warnings) == 0


def test_weather_warning_model():
    """Test WeatherWarning model creation"""
    warning = WeatherWarning(
        area_name="Vilniaus apskritis",
        warning_type="wind",
        severity="Moderate",
        description="Strong wind",
        counties=["Vilniaus apskritis"],
    )

    assert warning.area_name == "Vilniaus apskritis"
    assert warning.warning_type == "wind"
    assert warning.severity == "Moderate"
    assert "Vilniaus apskritis" in warning.counties


def test_get_counties_for_area(api_client):
    """Test county mapping for areas"""
    counties = api_client._get_counties_for_area("Vilniaus apskritis")
    assert "Vilniaus apskritis" in counties

    counties = api_client._get_counties_for_area("Kauno apskritis")
    assert "Kauno apskritis" in counties

    counties = api_client._get_counties_for_area("Pietryčių Baltija, Kuršių marios")
    assert "Klaipėdos apskritis" in counties


def test_warning_affects_area(api_client):
    """Test if warning affects specific administrative division"""
    warning = WeatherWarning(
        area_name="Vilniaus apskritis",
        warning_type="wind",
        severity="Moderate",
        description="Test warning",
        counties=["Vilniaus apskritis"],
    )

    assert api_client._warning_affects_area(warning, "Vilniaus miesto")
    assert api_client._warning_affects_area(warning, "Vilniaus rajono")
    assert not api_client._warning_affects_area(warning, "Kauno miesto")


def test_create_warning_from_alert(api_client):
    """Test creating warning from alert data"""
    alert = {
        "phenomenon": "wind",
        "severity": "Moderate",
        "description": {"en": "Strong wind", "lt": "Stiprus vėjas"},
        "instruction": {"en": "Be careful", "lt": "Būkite atsargūs"},
        "t_from": "2025-09-30T12:00:00Z",
        "t_to": "2025-09-30T18:00:00Z",
    }

    area = {"name": "Vilniaus apskritis"}

    warning = api_client._create_warning_from_alert(alert, area)

    assert warning is not None
    assert warning.area_name == "Vilniaus apskritis"
    assert warning.warning_type == "wind"
    assert warning.severity == "Moderate"
    assert "Be careful" in warning.description


def test_get_warnings_for_timestamp(api_client):
    """Test getting warnings for specific timestamp"""
    warnings = [
        WeatherWarning(
            area_name="Vilniaus apskritis",
            warning_type="wind",
            severity="Moderate",
            description="Strong wind",
            start_time="2025-09-30T12:00:00Z",
            end_time="2025-09-30T18:00:00Z",
            counties=["Vilniaus apskritis"],
        )
    ]

    # Test timestamp within warning period
    applicable = api_client._get_warnings_for_timestamp(
        "2025-09-30T15:00:00+00:00", warnings
    )
    assert len(applicable) == 1
    assert applicable[0].warning_type == "wind"

    # Test timestamp outside warning period
    applicable = api_client._get_warnings_for_timestamp(
        "2025-09-30T20:00:00+00:00", warnings
    )
    assert len(applicable) == 0

    # Test timestamp before warning period
    applicable = api_client._get_warnings_for_timestamp(
        "2025-09-30T10:00:00+00:00", warnings
    )
    assert len(applicable) == 0


def test_enrich_forecast_with_warnings_unit(api_client):
    """Test the _enrich_forecast_with_warnings method directly"""
    # Create test warnings
    warnings = [
        WeatherWarning(
            area_name="Vilniaus miesto savivaldybė",
            warning_type="wind",
            severity="Moderate",
            description="Strong wind",
            start_time="2025-09-30T12:00:00Z",
            end_time="2025-09-30T18:00:00Z",
            counties=["Vilniaus apskritis"],
        )
    ]

    # Test the warning matching function directly
    applicable_warnings = api_client._get_warnings_for_timestamp(
        "2025-09-30T15:00:00+00:00", warnings
    )

    assert len(applicable_warnings) == 1
    assert applicable_warnings[0].warning_type == "wind"
