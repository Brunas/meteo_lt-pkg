"""Unit tests"""

import unittest
from unittest.mock import AsyncMock, MagicMock
from meteo_lt.api import MeteoLtAPI


class TestMeteoLtAPI(unittest.IsolatedAsyncioTestCase):
    """API test class"""

    async def asyncSetUp(self):
        """Test setup"""
        self.meteo_lt_api = MeteoLtAPI()

    async def test_get_nearest_place(self):
        """Test nearest place"""
        nearest_place = await self.meteo_lt_api.get_nearest_place(54.6872, 25.2797)
        self.assertIsNotNone(nearest_place)
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
        mock_response.json = AsyncMock(return_value=[
            {"code": "test", "name": "Test", "latitude": 1.0, "longitude": 2.0}
        ])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = MeteoLtAPI(session=mock_session)
        self.assertIs(api._session, mock_session)

        await api.fetch_places()

        mock_session.get.assert_called_once_with(f"{MeteoLtAPI.BASE_URL}/places")
        self.assertEqual(len(api.places), 1)
        self.assertEqual(api.places[0].code, "test")


if __name__ == "__main__":
    unittest.main()
