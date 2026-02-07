"""API Unit tests"""

# pylint: disable=protected-access

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from meteo_lt.api import MeteoLtAPI
from meteo_lt.const import BASE_URL
from meteo_lt.models import (
    Coordinates,
    Forecast,
    ForecastTimestamp,
    HydroObservation,
    HydroObservationData,
    HydroStation,
    MeteoWarning,
    Place,
)


@pytest.fixture
def mock_place():
    """Create a mock place"""
    return Place(
        code="test_code",
        name="Test",
        country_code="LT",
        administrative_division="Test Admin",
        coordinates=Coordinates(latitude=1.0, longitude=2.0),
    )


@pytest.fixture
def mock_timestamp():
    """Create a mock forecast timestamp"""
    return ForecastTimestamp(
        datetime="2023-01-01 12:00:00",
        temperature=15.0,
        apparent_temperature=14.0,
        condition_code="clear",
        wind_speed=5.0,
        wind_gust_speed=8.0,
        wind_bearing=180.0,
        cloud_coverage=10,
        pressure=1013.25,
        humidity=65,
        precipitation=0.0,
    )


@pytest.fixture
def mock_forecast(mock_place, mock_timestamp):
    """Create a mock forecast"""
    return Forecast(
        place=mock_place,
        forecast_created="2023-01-01 12:00:00",
        current_conditions=mock_timestamp,
        forecast_timestamps=[],
    )


# Tests - Live API Tests (These hit real API)
@pytest.mark.asyncio
async def test_get_nearest_place():
    """Test nearest place"""
    async with MeteoLtAPI() as api_client:
        nearest_place = await api_client.get_nearest_place(54.97371, 24.00048)

        assert nearest_place is not None
        assert nearest_place.name == "Lapės"
        assert nearest_place.code == "lapes"
        assert nearest_place.country_code == "LT"
        assert nearest_place.administrative_division == "Kauno rajono savivaldybė"
        assert nearest_place.counties == ["Kauno apskritis"]


@pytest.mark.asyncio
async def test_get_forecast():
    """Test get forecast"""
    async with MeteoLtAPI() as api_client:
        forecast = await api_client.get_forecast("lapes")

        assert forecast is not None
        assert forecast.current_conditions is not None


# Tests - Session Management
@pytest.mark.asyncio
async def test_session_injection():
    """Test that injected session is actually used"""
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(
        return_value=[
            {
                "code": "test",
                "name": "Test",
                "administrativeDivision": "Test savivaldybė",
                "countryCode": "LT",
                "coordinates": {"latitude": 1.0, "longitude": 2.0},
            }
        ]
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)

    api = MeteoLtAPI(session=mock_session)
    assert api.client._session is mock_session

    await api.fetch_places()

    mock_session.get.assert_called_once_with(f"{BASE_URL}/places")
    assert len(api.places) == 1
    assert api.places[0].code == "test"


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager"""
    async with MeteoLtAPI() as api:
        assert api.client._session is not None
        await api.fetch_places()


@pytest.mark.asyncio
async def test_close():
    """Test close method"""
    api = MeteoLtAPI()
    await api.close()


# Tests - Forecast with Warnings
@pytest.mark.asyncio
async def test_get_forecast_with_warnings_by_coordinates(mock_place, mock_forecast):
    """Test getting forecast with warnings using coordinates"""
    async with MeteoLtAPI() as api_client:
        with (
            patch.object(api_client, "get_nearest_place") as mock_nearest,
            patch.object(api_client, "get_forecast") as mock_get_forecast,
        ):
            mock_nearest.return_value = mock_place
            mock_get_forecast.return_value = mock_forecast

            result = await api_client.get_forecast_with_warnings(latitude=1.0, longitude=2.0)

            mock_nearest.assert_called_once_with(1.0, 2.0)
            mock_get_forecast.assert_called_once_with("test_code", include_warnings=True)
            assert result == mock_forecast


@pytest.mark.parametrize(
    "kwargs,error_message",
    [
        ({}, "Either place_code or both latitude and longitude"),
        ({"latitude": 1.0}, "Either place_code or both latitude and longitude"),
        ({"longitude": 2.0}, "Either place_code or both latitude and longitude"),
    ],
)
@pytest.mark.asyncio
async def test_get_forecast_with_warnings_missing_params(kwargs, error_message):
    """Test error when required parameters are missing"""
    async with MeteoLtAPI() as api_client:
        with pytest.raises(ValueError, match=error_message):
            await api_client.get_forecast_with_warnings(**kwargs)


@pytest.mark.parametrize("include_warnings", [True, False])
@pytest.mark.asyncio
async def test_get_forecast_with_and_without_warnings(mock_forecast, include_warnings):
    """Test getting forecast with and without warnings"""
    async with MeteoLtAPI() as api_client:
        with (
            patch.object(api_client.client, "fetch_forecast") as mock_fetch,
            patch.object(api_client, "_enrich_forecast_with_warnings") as mock_enrich,
        ):
            mock_fetch.return_value = mock_forecast

            result = await api_client.get_forecast("test_code", include_warnings=include_warnings)

            mock_fetch.assert_called_once()
            assert result == mock_forecast

            if include_warnings:
                mock_enrich.assert_called_once_with(mock_forecast)
            else:
                mock_enrich.assert_not_called()


# Tests - Warnings
@pytest.mark.asyncio
async def test_get_weather_warnings():
    """Test getting weather warnings"""
    async with MeteoLtAPI() as api_client:
        with patch.object(api_client.warnings_processor, "get_warnings") as mock_get:
            mock_warnings = []
            mock_get.return_value = mock_warnings

            result = await api_client.get_weather_warnings("Test Division")

            assert result == mock_warnings


@pytest.mark.asyncio
async def test_get_hydro_warnings():
    """Test fetching hydrological warnings"""
    async with MeteoLtAPI() as api_client:
        mock_warnings = [
            MagicMock(administrative_division="Kauno apskritis", warning_type="flood", severity="High"),
        ]

        with patch.object(api_client.hydro_warnings_processor, "get_warnings") as mock_get:
            mock_get.return_value = mock_warnings

            result = await api_client.get_hydro_warnings("Kauno apskritis")

            assert result == mock_warnings
            mock_get.assert_called_once_with("Kauno apskritis")


@pytest.mark.asyncio
async def test_get_all_warnings():
    """Test fetching all warnings (weather and hydro combined)"""
    async with MeteoLtAPI() as api_client:
        weather_warnings = [MagicMock(warning_type="wind")]
        hydro_warnings = [MagicMock(warning_type="flood")]

        with (
            patch.object(api_client.warnings_processor, "get_warnings") as mock_weather,
            patch.object(api_client.hydro_warnings_processor, "get_warnings") as mock_hydro,
        ):
            mock_weather.return_value = weather_warnings
            mock_hydro.return_value = hydro_warnings

            result = await api_client.get_all_warnings()

            assert len(result) == 2
            assert result[0].warning_type == "wind"
            assert result[1].warning_type == "flood"


# Tests - Enrich Forecast Edge Cases
@pytest.mark.parametrize(
    "forecast_data",
    [
        None,  # No forecast
        {"place": None, "admin_div": "Test"},  # No place
        {"place": "valid", "admin_div": None},  # No admin division
    ],
)
@pytest.mark.asyncio
async def test_enrich_forecast_with_warnings_edge_cases(mock_timestamp, forecast_data):
    """Test enriching forecast edge cases"""
    async with MeteoLtAPI() as api_client:
        if forecast_data is None:
            forecast = None
        elif forecast_data["place"] is None:
            forecast = Forecast(
                place=None,
                forecast_created="2023-01-01 12:00:00",
                current_conditions=mock_timestamp,
                forecast_timestamps=[],
            )
        else:
            place = Place(
                code="test",
                name="Test",
                country_code="LT",
                administrative_division="Test Admin",
                coordinates=Coordinates(latitude=1.0, longitude=2.0),
            )
            place.administrative_division = forecast_data["admin_div"]
            forecast = Forecast(
                place=place,
                forecast_created="2023-01-01 12:00:00",
                current_conditions=mock_timestamp,
                forecast_timestamps=[],
            )

        # Should not raise exception
        await api_client._enrich_forecast_with_warnings(forecast)


@pytest.mark.asyncio
async def test_enrich_forecast_with_warnings_valid_data(mock_timestamp):
    """Test enriching forecast with warnings when all data is valid"""
    async with MeteoLtAPI() as api_client:
        place = Place(
            code="test_code",
            name="Test",
            country_code="LT",
            administrative_division="Kauno rajono savivaldybė",
            coordinates=Coordinates(latitude=1.0, longitude=2.0),
        )

        forecast = Forecast(
            place=place,
            forecast_created="2023-01-01 12:00:00",
            current_conditions=mock_timestamp,
            forecast_timestamps=[mock_timestamp],
        )

        mock_warning = MeteoWarning(
            administrative_division="Kauno apskritis",
            warning_type="wind",
            severity="Moderate",
            description="Test warning",
            start_time="2023-01-01T10:00:00Z",
            end_time="2023-01-01T14:00:00Z",
        )

        with patch.object(api_client, "get_all_warnings") as mock_get_warnings:
            mock_get_warnings.return_value = [mock_warning]

            await api_client._enrich_forecast_with_warnings(forecast)

            mock_get_warnings.assert_called_once_with("Kauno rajono savivaldybė")


# Tests - Hydro Functions
@pytest.mark.asyncio
async def test_get_hydro_stations():
    """Test getting hydro stations"""
    async with MeteoLtAPI() as api_client:
        with patch.object(api_client.client, "fetch_hydro_stations") as mock_fetch:
            mock_stations = []
            mock_fetch.return_value = mock_stations

            result = await api_client.fetch_hydro_stations()

            assert result == mock_stations


@pytest.mark.asyncio
async def test_get_nearest_hydro_station():
    """Test getting nearest hydro station"""
    async with MeteoLtAPI() as api_client:
        mock_station = HydroStation(
            code="test_code",
            name="Test Station",
            water_body="Test Water",
            coordinates=Coordinates(latitude=1.0, longitude=2.0),
        )

        with patch.object(api_client, "fetch_hydro_stations") as mock_get:
            mock_get.return_value = [mock_station]

            result = await api_client.get_nearest_hydro_station(1.0, 2.0)

            assert result == mock_station


@pytest.mark.asyncio
async def test_get_nearest_hydro_station_no_stations():
    """Test getting nearest hydro station when no stations exist"""
    async with MeteoLtAPI() as api_client:
        with patch.object(api_client, "fetch_hydro_stations") as mock_get:
            mock_get.return_value = []

            result = await api_client.get_nearest_hydro_station(1.0, 2.0)

            assert result is None


@pytest.mark.asyncio
async def test_get_hydro_observation_data():
    """Test getting hydro observation data"""
    async with MeteoLtAPI() as api_client:
        mock_station = HydroStation(
            code="station_1",
            name="Station 1",
            water_body="River",
            coordinates=Coordinates(latitude=54.0, longitude=24.0),
        )
        mock_observation = HydroObservation(
            observation_datetime="2023-01-01 12:00:00",
            water_level=1.5,
            water_temperature=5.0,
            water_discharge=100.0,
        )
        mock_obs_data = HydroObservationData(
            station=mock_station,
            observations_data_range="2023-01-01 to 2023-01-31",
            observations=[mock_observation],
        )

        with patch.object(api_client.client, "fetch_hydro_observation_data") as mock_fetch:
            mock_fetch.return_value = mock_obs_data

            result = await api_client.get_hydro_observation_data("station_1")

            assert result == mock_obs_data
            mock_fetch.assert_called_once_with("station_1", "measured", "latest")
