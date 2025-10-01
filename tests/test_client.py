"""Tests for MeteoLt API client"""

# pylint: disable=W0621

import json
from unittest.mock import AsyncMock, patch

import pytest

from meteo_lt.client import MeteoLtClient


@pytest.fixture
def client():
    """Create client for testing"""
    return MeteoLtClient()


@pytest.mark.asyncio
async def test_fetch_places(client):
    """Test fetching places from API"""
    mock_places_data = [
        {
            "code": "vilnius",
            "name": "Vilnius",
            "administrativeDivision": "Vilniaus miesto savivaldybė",
            "countryCode": "LT",
            "coordinates": {"latitude": 54.6872, "longitude": 25.2797},
        }
    ]

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_places_data
        mock_response.raise_for_status.return_value = None
        mock_response.encoding = "utf-8"
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            places = await client.fetch_places()

        assert len(places) == 1
        assert places[0].code == "vilnius"
        assert places[0].name == "Vilnius"


@pytest.mark.asyncio
async def test_fetch_forecast(client):
    """Test fetching forecast from API"""
    mock_forecast_data = {
        "place": {
            "code": "vilnius",
            "name": "Vilnius",
            "administrativeDivision": "Vilniaus miesto savivaldybė",
            "countryCode": "LT",
            "coordinates": {"latitude": 54.6872, "longitude": 25.2797},
        },
        "forecastCreationTimeUtc": "2025-10-01 12:00:00",
        "forecastTimestamps": [
            {
                "forecastTimeUtc": "2025-10-01 15:00:00",
                "airTemperature": 15.0,
                "feelsLikeTemperature": 14.0,
                "conditionCode": "clear",
                "windSpeed": 5.0,
                "windGust": 8.0,
                "windDirection": 180.0,
                "cloudCover": 10,
                "seaLevelPressure": 1013.25,
                "relativeHumidity": 65,
                "totalPrecipitation": 0.0,
            }
        ],
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_forecast_data
        mock_response.raise_for_status.return_value = None
        mock_response.encoding = "utf-8"
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            forecast = await client.fetch_forecast("vilnius")

        assert forecast.place.code == "vilnius"
        assert len(forecast.forecast_timestamps) == 1


@pytest.mark.asyncio
async def test_fetch_weather_warnings(client):
    """Test fetching weather warnings from API"""
    mock_file_list = [
        "https://www.meteo.lt/meteo_jobs/pavojingi_met_reisk_ibl/20251001120000-00000001"
    ]

    mock_warnings_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"name": "Kauno apskritis"}],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {"lt": "Stiprus vėjas"},
                                "t_from": "2025-10-01T12:00:00Z",
                                "t_to": "2025-10-01T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        # Mock the file list response
        mock_list_response = AsyncMock()
        mock_list_response.json.return_value = mock_file_list
        mock_list_response.raise_for_status.return_value = None

        # Mock the warnings data response
        mock_data_response = AsyncMock()
        mock_data_response.text.return_value = json.dumps(mock_warnings_data)
        mock_data_response.raise_for_status.return_value = None

        mock_get.return_value.__aenter__.side_effect = [
            mock_list_response,
            mock_data_response,
        ]

        async with client:
            warnings_data = await client.fetch_weather_warnings()

        assert isinstance(warnings_data, dict)
        assert "phenomenon_groups" in warnings_data


@pytest.mark.asyncio
async def test_fetch_weather_warnings_empty(client):
    """Test handling empty warnings response"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            warnings_data = await client.fetch_weather_warnings()

        assert warnings_data == []
