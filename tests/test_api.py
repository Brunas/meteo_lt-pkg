"""Unit tests"""
import unittest
from meteo_lt.api import MeteoLtAPI

class TestMeteoLtAPI(unittest.IsolatedAsyncioTestCase):
    """API test class"""
    async def asyncSetUp(self):
        """Test setup"""
        self.meteo_lt_api = MeteoLtAPI()
        await self.meteo_lt_api.fetch_places()

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
        print(forecast)

if __name__ == "__main__":
    unittest.main()
