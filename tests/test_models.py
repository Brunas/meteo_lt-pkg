"""Models unit tests"""

from datetime import datetime, timedelta
import unittest
from meteo_lt.models import (
    Coordinates,
    Forecast,
    ForecastTimestamp,
    Place,
    get_municipality_county,
)


class TestMeteoLtModels(unittest.TestCase):
    """Models test class"""

    def setUp(self):
        """Set up the test fixtures."""
        self.place = Place(
            code="123",
            name="Sample Place",
            country_code="XX",
            administrative_division="Sample Admin Div",
            coordinates=Coordinates(latitude=54.6872, longitude=25.2797),
        )
        now = datetime.now()
        # Create forecast timestamps for testing
        self.past_timestamp = ForecastTimestamp(
            datetime=(now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            temperature=20,
            apparent_temperature=21,
            condition_code="clear",
            wind_speed=3,
            wind_gust_speed=5,
            wind_bearing=250,
            cloud_coverage=10,
            pressure=1010,
            humidity=50,
            precipitation=0,
        )
        self.future_timestamp_1 = ForecastTimestamp(
            datetime=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
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
        )
        self.future_timestamp_2 = ForecastTimestamp(
            datetime=(now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
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
        )

    def test_current_conditions_with_timestamps(self):
        """Test current_conditions method with forecast timestamps."""
        forecast = Forecast(
            place=self.place,
            forecast_created=(datetime.now() - timedelta(hours=2)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            current_conditions=self.future_timestamp_1,
            forecast_timestamps=[self.future_timestamp_2],
        )
        current_conditions = forecast.current_conditions

        self.assertIsNotNone(current_conditions)
        self.assertEqual(current_conditions.temperature, 27.0)
        self.assertEqual(current_conditions.condition_code, "partly-cloudy")

    def test_current_conditions_no_timestamps(self):
        """Test current_conditions method with no forecast timestamps."""
        forecast = Forecast(
            place=self.place,
            forecast_created=(datetime.now() - timedelta(hours=2)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            current_conditions=None,
            forecast_timestamps=[],
        )
        current_conditions = forecast.current_conditions

        self.assertIsNone(current_conditions)

    def test_coordinates_from_dict(self):
        """Tests coordinates from_dict"""
        data = {"latitude": 54.6872, "longitude": 25.2797}

        coords = Coordinates.from_dict(data)

        self.assertIsInstance(coords, Coordinates)
        self.assertEqual(coords.latitude, 54.6872)
        self.assertEqual(coords.longitude, 25.2797)

    def test_datetime_format(self):
        """Checking ISO 8601 date format"""
        # Create an instance of ForecastTimestamp
        sample_data = {
            "forecastTimeUtc": (datetime.now() + timedelta(hours=2)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "airTemperature": 20.5,
            "feelsLikeTemperature": 21.0,
            "conditionCode": "clear",
            "windSpeed": 5.5,
            "windGust": 7.0,
            "windDirection": 180,
            "cloudCover": 25.0,
            "seaLevelPressure": 1013.25,
            "relativeHumidity": 60.0,
            "totalPrecipitation": 0.0,
        }
        forecast_timestamp = ForecastTimestamp.from_dict(sample_data)

        # Assert that the datetime is in ISO 8601 format
        self.assertEqual(
            forecast_timestamp.datetime,
            sample_data["forecastTimeUtc"].replace(" ", "T") + "+00:00",
        )

    def test_filter_past_timestamps(self):
        """Test that past timestamps are filtered out."""
        forecast = Forecast(
            place=self.place,
            current_conditions=None,
            forecast_created=(datetime.now() - timedelta(hours=2)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            forecast_timestamps=[
                self.past_timestamp,
                self.future_timestamp_1,
                self.future_timestamp_2,
            ],
        )

        # Check that only future timestamps remain
        self.assertIn(self.future_timestamp_1, forecast.forecast_timestamps)
        self.assertIn(self.future_timestamp_2, forecast.forecast_timestamps)
        self.assertNotIn(self.past_timestamp, forecast.forecast_timestamps)

    def test_valid_division(self):
        """Test that valid divisions return the correct county."""
        test_cases = {
            "Alytaus miesto": "Alytaus",
            "Birštono": "Kauno",
            "Klaipėdos rajono": "Klaipėdos",
            "Kalvarijos": "Marijampolės",
            "Panevėžio miesto": "Panevėžio",
            "Joniškio rajono": "Šiaulių",
            "Jurbarko rajono": "Tauragės",
            "Mažeikių rajono": "Telšių",
            "Anykščių rajono": "Utenos",
            "Elektrėnų": "Vilniaus",
        }

        for division, expected_county in test_cases.items():
            with self.subTest(division=division):
                self.assertEqual(
                    get_municipality_county(f"{division} savivaldybė"),
                    f"{expected_county} apskritis",
                )

    def test_invalid_division(self):
        """Test that invalid divisions return 'Unknown county'."""
        invalid_divisions = ["Nonexistent Division", "Fake County", "Imaginary Area"]

        for division in invalid_divisions:
            with self.subTest(division=division):
                self.assertEqual(get_municipality_county(division), "Unknown county")
