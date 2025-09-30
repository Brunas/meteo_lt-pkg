"""Unit tests"""

import unittest
from meteo_lt.api import MeteoLtAPI


class TestMeteoLtAPI(unittest.IsolatedAsyncioTestCase):
    """API test class"""

    async def asyncSetUp(self):
        """Test setup"""
        self.meteo_lt_api = MeteoLtAPI()

    async def test_get_nearest_place(self):
        """Test nearest place"""
        nearest_place = await self.meteo_lt_api.get_nearest_place(54.97371, 24.00048)
        self.assertIsNotNone(nearest_place)
        self.assertEqual("Lapės", nearest_place.name)
        self.assertEqual("lapes", nearest_place.code)
        self.assertEqual("LT", nearest_place.country_code)
        self.assertEqual(
            "Kauno rajono savivaldybė", nearest_place.administrative_division
        )
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


if __name__ == "__main__":
    unittest.main()
