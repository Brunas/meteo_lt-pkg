"""API Unit tests"""

# pylint: disable=protected-access

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from meteo_lt.api import MeteoLtAPI
from meteo_lt.const import BASE_URL
from meteo_lt.models import (
    Place,
    Coordinates,
    Forecast,
    ForecastTimestamp,
    HydroStation,
    HydroObservationData,
    HydroObservation,
)


class TestMeteoLtAPI(unittest.IsolatedAsyncioTestCase):
    """API test class"""

    async def asyncSetUp(self):
        """Test setup"""
        self.meteo_lt_api = MeteoLtAPI()

    async def asyncTearDown(self):
        """Test teardown"""
        await self.meteo_lt_api.close()

    async def test_get_nearest_place(self):
        """Test nearest place"""
        nearest_place = await self.meteo_lt_api.get_nearest_place(54.97371, 24.00048)
        self.assertIsNotNone(nearest_place)
        self.assertEqual("Lapės", nearest_place.name)
        self.assertEqual("lapes", nearest_place.code)
        self.assertEqual("LT", nearest_place.country_code)
        self.assertEqual("Kauno rajono savivaldybė", nearest_place.administrative_division)
        self.assertEqual(["Kauno apskritis"], nearest_place.counties)
        print(nearest_place)

    async def test_get_forecast(self):
        """Test get forecast"""
        place_code = "lapes"  # Use a real place code
        forecast = await self.meteo_lt_api.get_forecast(place_code)
        self.assertIsNotNone(forecast)
        self.assertIsNotNone(forecast.current_conditions)
        print(forecast)
        print(forecast.current_conditions)

    async def test_session_injection(self):
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
        self.assertIs(api.client._session, mock_session)

        await api.fetch_places()

        mock_session.get.assert_called_once_with(f"{BASE_URL}/places")
        self.assertEqual(len(api.places), 1)
        self.assertEqual(api.places[0].code, "test")

    async def test_context_manager(self):
        """Test async context manager"""
        async with MeteoLtAPI() as api:
            self.assertIsNotNone(api.client._session)
            await api.fetch_places()

    async def test_close(self):
        """Test close method"""
        api = MeteoLtAPI()
        await api.close()

    async def test_get_forecast_with_warnings_by_coordinates(self):
        """Test getting forecast with warnings using coordinates"""
        with (
            patch.object(self.meteo_lt_api, "get_nearest_place") as mock_nearest,
            patch.object(self.meteo_lt_api, "get_forecast") as mock_get_forecast,
        ):
            mock_place = Place(
                code="test_code",
                name="Test",
                country_code="LT",
                administrative_division="Test Admin",
                coordinates=Coordinates(latitude=1.0, longitude=2.0),
            )
            mock_nearest.return_value = mock_place

            mock_forecast = MagicMock()
            mock_get_forecast.return_value = mock_forecast

            result = await self.meteo_lt_api.get_forecast_with_warnings(latitude=1.0, longitude=2.0)

            mock_nearest.assert_called_once_with(1.0, 2.0)
            mock_get_forecast.assert_called_once_with("test_code", include_warnings=True)
            self.assertEqual(result, mock_forecast)

    async def test_get_forecast_with_warnings_missing_coords_error(self):
        """Test error when coordinates are missing for forecast with warnings"""
        # Test with no parameters
        with self.assertRaises(ValueError) as context:
            await self.meteo_lt_api.get_forecast_with_warnings()
        self.assertIn("Either place_code or both latitude and longitude", str(context.exception))

        # Test with only latitude
        with self.assertRaises(ValueError):
            await self.meteo_lt_api.get_forecast_with_warnings(latitude=1.0)

    async def test_get_forecast_without_warnings(self):
        """Test getting forecast without warnings"""
        with patch.object(self.meteo_lt_api.client, "fetch_forecast") as mock_fetch:
            mock_place = Place(
                code="test_code",
                name="Test",
                country_code="LT",
                administrative_division="Test Admin",
                coordinates=Coordinates(latitude=1.0, longitude=2.0),
            )
            mock_timestamp = ForecastTimestamp(
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
            mock_forecast = Forecast(
                place=mock_place,
                forecast_created="2023-01-01 12:00:00",
                current_conditions=mock_timestamp,
                forecast_timestamps=[],
            )
            mock_fetch.return_value = mock_forecast

            result = await self.meteo_lt_api.get_forecast("test_code", include_warnings=False)

            self.assertEqual(result, mock_forecast)

    async def test_get_weather_warnings(self):
        """Test getting weather warnings"""
        with patch.object(self.meteo_lt_api.warnings_processor, "get_weather_warnings") as mock_get:
            mock_warnings = []
            mock_get.return_value = mock_warnings

            result = await self.meteo_lt_api.get_weather_warnings("Test Division")

            self.assertEqual(result, mock_warnings)

    async def test_enrich_forecast_with_warnings_no_forecast(self):
        """Test enriching forecast when forecast is None"""
        await self.meteo_lt_api._enrich_forecast_with_warnings(None)

    async def test_enrich_forecast_with_warnings_no_place(self):
        """Test enriching forecast when place is None"""
        timestamp = ForecastTimestamp(
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
        forecast = Forecast(
            place=None,
            forecast_created="2023-01-01 12:00:00",
            current_conditions=timestamp,
            forecast_timestamps=[],
        )
        await self.meteo_lt_api._enrich_forecast_with_warnings(forecast)

    async def test_enrich_forecast_with_warnings_no_admin_division(self):
        """Test enriching forecast when administrative_division is empty"""
        # Create a place with a valid administrative_division initially
        place = Place(
            code="test_code",
            name="Test",
            country_code="LT",
            administrative_division="Test Admin",
            coordinates=Coordinates(latitude=1.0, longitude=2.0),
        )
        # Then set it to None to simulate the edge case
        place.administrative_division = None

        timestamp = ForecastTimestamp(
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
        forecast = Forecast(
            place=place,
            forecast_created="2023-01-01 12:00:00",
            current_conditions=timestamp,
            forecast_timestamps=[],
        )
        await self.meteo_lt_api._enrich_forecast_with_warnings(forecast)

    async def test_get_hydro_stations(self):
        """Test getting hydro stations"""
        with patch.object(self.meteo_lt_api.client, "fetch_hydro_stations") as mock_fetch:
            mock_stations = []
            mock_fetch.return_value = mock_stations

            result = await self.meteo_lt_api.get_hydro_stations()

            self.assertEqual(result, mock_stations)

    async def test_get_nearest_hydro_station(self):
        """Test getting nearest hydro station"""
        with patch.object(self.meteo_lt_api, "get_hydro_stations") as mock_get:
            mock_station = HydroStation(
                code="test_code",
                name="Test Station",
                water_body="Test Water",
                coordinates=Coordinates(latitude=1.0, longitude=2.0),
            )
            mock_get.return_value = [mock_station]

            result = await self.meteo_lt_api.get_nearest_hydro_station(1.0, 2.0)

            self.assertEqual(result, mock_station)

    async def test_get_nearest_hydro_station_no_stations(self):
        """Test getting nearest hydro station when no stations exist"""
        with patch.object(self.meteo_lt_api, "get_hydro_stations") as mock_get:
            mock_get.return_value = []

            result = await self.meteo_lt_api.get_nearest_hydro_station(1.0, 2.0)

            self.assertIsNone(result)

    async def test_get_hydro_observation_data(self):
        """Test getting hydro observation data"""
        with patch.object(self.meteo_lt_api.client, "fetch_hydro_observation_data") as mock_fetch:
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
            mock_fetch.return_value = mock_obs_data

            result = await self.meteo_lt_api.get_hydro_observation_data("station_1")

            self.assertEqual(result, mock_obs_data)
            mock_fetch.assert_called_once_with("station_1", "measured", "latest")


if __name__ == "__main__":
    unittest.main()
