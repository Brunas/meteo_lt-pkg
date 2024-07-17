"""Models unit tests"""

import unittest
from meteo_lt.models import Coordinates, Forecast, ForecastTimestamp, Place

class TestMeteoLtModels(unittest.TestCase):
    """Models test class"""

    def setUp(self):
        """Set up the test fixtures."""
        self.place = Place(
            code="123",
            name="Sample Place",
            country="Sample Country",
            administrative_division="Sample Admin Div",
            coordinates=Coordinates(latitude=54.6872, longitude=25.2797),
        )
        self.forecast_timestamps = [
            ForecastTimestamp(
                datetime="2024-07-17T14:00:00+0000",
                temperature=27,
                apparent_temperature=27.9,
                condition_code="partly-cloudy",
                wind_speed=2,
                wind_gust_speed=5,
                wind_bearing=300,
                cloud_coverage=28,
                pressure=1016,
                humidity=58,
                precipitation=0,
            ),
            ForecastTimestamp(
                datetime="2024-07-17T15:00:00+0000",
                temperature=29,
                apparent_temperature=30.9,
                condition_code="clear",
                wind_speed=2,
                wind_gust_speed=5,
                wind_bearing=300,
                cloud_coverage=28,
                pressure=1016,
                humidity=58,
                precipitation=0,
            ),
        ]

    def test_current_conditions_with_timestamps(self):
        """Test current_conditions method with forecast timestamps."""
        forecast = Forecast(
            place=self.place, forecast_timestamps=self.forecast_timestamps
        )
        current_conditions = forecast.current_conditions()

        self.assertIsNotNone(current_conditions)
        self.assertEqual(current_conditions.temperature, 27.0)
        self.assertEqual(current_conditions.condition_code, "partly-cloudy")

    def test_current_conditions_no_timestamps(self):
        """Test current_conditions method with no forecast timestamps."""
        forecast = Forecast(place=self.place, forecast_timestamps=[])
        current_conditions = forecast.current_conditions()

        self.assertIsNone(current_conditions)

    def test_coordinates_from_dict(self):
        """Tests coordinates from_dict"""
        data = {"latitude": 54.6872, "longitude": 25.2797}

        coords = Coordinates.from_dict(data)

        assert isinstance(coords, Coordinates)
        assert coords.latitude == 54.6872
        assert coords.longitude == 25.2797
