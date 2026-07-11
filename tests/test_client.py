"""Tests for MeteoLt API client"""

# pylint: disable=redefined-outer-name

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from meteo_lt.client import MeteoLtClient
from meteo_lt.const import WARNINGS_URL


@pytest.fixture
def client():
    """Create client for testing"""
    return MeteoLtClient()


@pytest.fixture
def tomorrow_date():
    """Get tomorrow's date string"""
    return (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")


# Tests - Places
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
        mock_response.raise_for_status = MagicMock()
        mock_response.encoding = "utf-8"
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            places = await client.fetch_places()

        assert len(places) == 1
        assert places[0].code == "lapės"
        assert places[0].name == "Lapės"


# Tests - Forecast
@pytest.mark.asyncio
async def test_fetch_forecast(client, tomorrow_date):
    """Test fetching forecast from API"""
    mock_forecast_data = {
        "place": {
            "code": "lapės",
            "name": "Lapės",
            "administrativeDivision": "Kauno rajono savivaldybė",
            "countryCode": "LT",
            "coordinates": {"latitude": 54.97371, "longitude": 24.00048},
        },
        "forecastCreationTimeUtc": f"{tomorrow_date} 12:00:00",
        "forecastTimestamps": [
            {
                "forecastTimeUtc": f"{tomorrow_date} 15:00:00",
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
        mock_response.raise_for_status = MagicMock()
        mock_response.encoding = "utf-8"
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            forecast = await client.fetch_forecast("lapės")

        assert forecast.place.code == "lapės"
        assert len(forecast.forecast_timestamps) == 1


# Tests - Weather Warnings
@pytest.mark.asyncio
async def test_fetch_weather_warnings(client, tomorrow_date):
    """Test fetching weather warnings from API"""
    file_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y%m%d")
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
                                "t_from": f"{tomorrow_date}T12:00:00Z",
                                "t_to": f"{tomorrow_date}T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_list_response = AsyncMock()
        mock_list_response.json.return_value = mock_file_list
        mock_list_response.raise_for_status = MagicMock()

        mock_data_response = AsyncMock()
        mock_data_response.text.return_value = json.dumps(mock_warnings_data)
        mock_data_response.raise_for_status = MagicMock()

        mock_get.return_value.__aenter__.side_effect = [mock_list_response, mock_data_response]

        async with client:
            warnings_data = await client.fetch_warnings(WARNINGS_URL)

        assert isinstance(warnings_data, dict)
        assert "phenomenon_groups" in warnings_data


@pytest.mark.asyncio
async def test_fetch_weather_warnings_empty(client):
    """Test handling empty warnings response"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            warnings_data = await client.fetch_warnings(WARNINGS_URL)

        assert warnings_data == []


# Tests - Hydro Stations
@pytest.mark.asyncio
async def test_fetch_hydro_stations(client):
    """Test fetching hydro stations"""
    mock_data = [
        {
            "code": "station_1",
            "name": "Station 1",
            "waterBody": "River",
            "coordinates": {"latitude": 54.0, "longitude": 24.0},
        }
    ]

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_data
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            stations = await client.fetch_hydro_stations()

        assert len(stations) == 1
        assert stations[0].code == "station_1"


@pytest.mark.asyncio
async def test_fetch_hydro_station(client):
    """Test fetching a specific hydro station"""
    mock_data = {
        "code": "station_1",
        "name": "Station 1",
        "waterBody": "River",
        "coordinates": {"latitude": 54.0, "longitude": 24.0},
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_data
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            station = await client.fetch_hydro_station("station_1")

        assert station.code == "station_1"


# Tests - Hydro Observations
@pytest.mark.asyncio
async def test_fetch_hydro_observation_data(client):
    """Test fetching hydro observation data"""
    mock_data = {
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
        mock_response.json.return_value = mock_data
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response

        async with client:
            obs_data = await client.fetch_hydro_observation_data("station_1")

        assert obs_data.station.code == "station_1"
        assert len(obs_data.observations) == 1
        assert obs_data.observations[0].water_level == 1.5


# Tests - Error Handling
@pytest.mark.parametrize(
    "method_name,args,status_code",
    [
        ("fetch_hydro_stations", (), 500),
        ("fetch_hydro_station", ("station_1",), 404),
        ("fetch_hydro_observation_data", ("station_1",), 500),
    ],
)
@pytest.mark.asyncio
async def test_hydro_api_errors(client, method_name, args, status_code):
    """Test error handling for hydro API methods"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = status_code
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception, match=f"API returned status {status_code}"):
            async with client:
                method = getattr(client, method_name)
                await method(*args)


# Tests - Injected Session Error Handling
@pytest.mark.parametrize(
    "method_name,args",
    [
        ("fetch_forecast", ("lapės",)),
        ("fetch_places", ()),
    ],
)
@pytest.mark.asyncio
async def test_injected_session_raises_for_http_error(method_name, args):
    """A 500 must raise even when the session has no session-level raise_for_status.

    This mirrors the Home Assistant scenario, where the shared aiohttp session is
    injected via ``MeteoLtClient(session=...)`` and is created without
    ``raise_for_status=True``. Errors must still propagate as ``aiohttp.ClientError``
    instead of being parsed as payloads.
    """
    error = aiohttp.ClientResponseError(
        request_info=AsyncMock(),
        history=(),
        status=500,
        message="Internal Server Error",
    )

    async with aiohttp.ClientSession() as external_session:
        client = MeteoLtClient(session=external_session)

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.raise_for_status = MagicMock(side_effect=error)
            mock_get.return_value.__aenter__.return_value = mock_response

            method = getattr(client, method_name)
            with pytest.raises(aiohttp.ClientResponseError):
                await method(*args)


# Tests - Session Management
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
        assert not external_session.closed
