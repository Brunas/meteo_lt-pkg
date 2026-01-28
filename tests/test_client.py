"""Tests for MeteoLt API client"""

# pylint: disable=redefined-outer-name

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import aiohttp
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
            "code": "lapės",
            "name": "Lapės",
            "administrativeDivision": "Kauno rajono savivaldybė",
            "countryCode": "LT",
            "coordinates": {"latitude": 54.97371, "longitude": 24.00048},
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
        assert places[0].code == "lapės"
        assert places[0].name == "Lapės"


@pytest.mark.asyncio
async def test_fetch_forecast(client):
    """Test fetching forecast from API"""

    tomorrow_date_string = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    mock_forecast_data = {
        "place": {
            "code": "lapės",
            "name": "Lapės",
            "administrativeDivision": "Kauno rajono savivaldybė",
            "countryCode": "LT",
            "coordinates": {"latitude": 54.97371, "longitude": 24.00048},
        },
        "forecastCreationTimeUtc": f"{tomorrow_date_string} 12:00:00",
        "forecastTimestamps": [
            {
                "forecastTimeUtc": f"{tomorrow_date_string} 15:00:00",
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
            forecast = await client.fetch_forecast("lapės")

        assert forecast.place.code == "lapės"
        assert len(forecast.forecast_timestamps) == 1


@pytest.mark.asyncio
async def test_fetch_weather_warnings(client):
    """Test fetching weather warnings from API"""

    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    tomorrow_date_string = tomorrow.strftime("%Y-%m-%d")
    file_date = tomorrow.strftime("%Y%m%d")

    mock_file_list = [f"https://www.meteo.lt/meteo_jobs/pavojingi_met_reisk_ibl/{file_date}120000-00000001"]

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
                                "t_from": f"{tomorrow_date_string}T12:00:00Z",
                                "t_to": f"{tomorrow_date_string}T18:00:00Z",
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


@pytest.mark.asyncio
async def test_fetch_hydro_stations(client):
    """Test fetching hydro stations"""
    mock_stations_data = [
        {
            "code": "station_1",
            "name": "Station 1",
            "waterBody": "River",
            "coordinates": {"latitude": 54.0, "longitude": 24.0},
        }
    ]

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_stations_data
        mock_response.status = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            stations = await client.fetch_hydro_stations()

        assert len(stations) == 1
        assert stations[0].code == "station_1"
        assert stations[0].name == "Station 1"


@pytest.mark.asyncio
async def test_fetch_hydro_stations_error(client):
    """Test handling error when fetching hydro stations"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception, match="API returned status 500"):
            async with client:
                await client.fetch_hydro_stations()


@pytest.mark.asyncio
async def test_fetch_hydro_station(client):
    """Test fetching a specific hydro station"""
    mock_station_data = {
        "code": "station_1",
        "name": "Station 1",
        "waterBody": "River",
        "coordinates": {"latitude": 54.0, "longitude": 24.0},
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_station_data
        mock_response.status = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            station = await client.fetch_hydro_station("station_1")

        assert station.code == "station_1"
        assert station.name == "Station 1"


@pytest.mark.asyncio
async def test_fetch_hydro_station_error(client):
    """Test handling error when fetching a specific hydro station"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception, match="API returned status 404"):
            async with client:
                await client.fetch_hydro_station("nonexistent")


@pytest.mark.asyncio
async def test_fetch_hydro_observation_data(client):
    """Test fetching hydro observation data"""
    mock_observation_data = {
        "station": {
            "code": "station_1",
            "name": "Station 1",
            "waterBody": "River",
            "coordinates": {"latitude": 54.0, "longitude": 24.0},
        },
        "observationsDataRange": "2023-01-01 to 2023-01-31",
        "observations": [
            {
                "observationTimeUtc": "2023-01-01 12:00:00",
                "waterLevel": 1.5,
                "waterTemperature": 5.0,
                "waterDischarge": 100.0,
            }
        ],
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_observation_data
        mock_response.status = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            obs_data = await client.fetch_hydro_observation_data("station_1")

        assert obs_data.station.code == "station_1"
        assert len(obs_data.observations) == 1
        assert obs_data.observations[0].water_level == 1.5


@pytest.mark.asyncio
async def test_fetch_hydro_observation_data_error(client):
    """Test handling error when fetching hydro observation data"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception, match="API returned status 500"):
            async with client:
                await client.fetch_hydro_observation_data("station_1")


@pytest.mark.asyncio
async def test_client_context_manager(client):
    """Test client as async context manager"""
    async with client:
        assert client._session is not None


@pytest.mark.asyncio
async def test_client_close(client):
    """Test closing client"""
    async with client:
        pass
    # After exiting context, session should be closed
    assert client._session is None


@pytest.mark.asyncio
async def test_client_get_session_creates_session(client):
    """Test that _get_session creates a session if none exists"""
    session = await client._get_session()
    assert session is not None
    assert client._session is not None
    await client.close()


@pytest.mark.asyncio
async def test_client_reuse_existing_session(client):
    """Test that client reuses existing session"""
    session1 = await client._get_session()
    session2 = await client._get_session()
    assert session1 is session2
    await client.close()


@pytest.mark.asyncio
async def test_client_with_external_session():
    """Test client with externally managed session"""
    async with aiohttp.ClientSession() as external_session:
        client = MeteoLtClient(session=external_session)
        assert client._session is external_session
        assert not client._owns_session

        # Client should not close external session
        await client.close()
        # External session should still be usable
        assert not external_session.closed
