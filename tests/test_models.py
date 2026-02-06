"""Models unit tests"""

from datetime import datetime, timedelta

import pytest

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


# Fixtures
@pytest.fixture
def sample_place():
    """Create a sample place for testing."""
    return Place(
        code="123",
        name="Sample Place",
        country_code="XX",
        administrative_division="Sample Admin Div",
        coordinates=Coordinates(latitude=54.6872, longitude=25.2797),
    )


@pytest.fixture
def sample_timestamps():
    """Create sample forecast timestamps."""
    now = datetime.now()
    return {
        "past": ForecastTimestamp(
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
        ),
        "future_1": ForecastTimestamp(
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
        ),
        "future_2": ForecastTimestamp(
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
        ),
    }


# Tests - Coordinates
def test_coordinates_from_dict():
    """Test coordinates from_dict."""
    data = {"latitude": 54.6872, "longitude": 25.2797}
    coords = Coordinates.from_dict(data)

    assert isinstance(coords, Coordinates)
    assert coords.latitude == 54.6872
    assert coords.longitude == 25.2797


# Tests - Place
@pytest.mark.parametrize(
    "division,expected_counties",
    [
        ("Alytaus miesto", ["Alytaus apskritis"]),
        ("Birštono", ["Kauno apskritis"]),
        ("Klaipėdos rajono", ["Klaipėdos apskritis", "Pietryčių Baltija, Kuršių marios"]),
        ("Kalvarijos", ["Marijampolės apskritis"]),
        ("Panevėžio miesto", ["Panevėžio apskritis"]),
        ("Joniškio rajono", ["Šiaulių apskritis"]),
        ("Jurbarko rajono", ["Tauragės apskritis"]),
        ("Mažeikių rajono", ["Telšių apskritis"]),
        ("Anykščių rajono", ["Utenos apskritis"]),
        ("Elektrėnų", ["Vilniaus apskritis"]),
    ],
)
def test_place_valid_division(division, expected_counties):
    """Test that valid divisions return the correct counties."""
    place = Place(
        code="123",
        name="Sample Place",
        country_code="XX",
        administrative_division=f"{division} savivaldybė",
        coordinates=Coordinates(latitude=1.0, longitude=1.0),
    )
    assert place.counties == expected_counties


@pytest.mark.parametrize(
    "division",
    [
        "Nonexistent Division",
        "Fake County",
        "Imaginary Area",
    ],
)
def test_place_invalid_division(division):
    """Test that invalid divisions return empty counties list."""
    place = Place(
        code="123",
        name="Sample Place",
        country_code="XX",
        administrative_division=f"{division} savivaldybė",
        coordinates=Coordinates(latitude=1.0, longitude=1.0),
    )
    assert place.counties == []


# Tests - Forecast
def test_current_conditions_with_timestamps(sample_place, sample_timestamps):
    """Test current_conditions with forecast timestamps."""
    forecast = Forecast(
        place=sample_place,
        forecast_created=(datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        current_conditions=sample_timestamps["future_1"],
        forecast_timestamps=[sample_timestamps["future_2"]],
    )

    assert forecast.current_conditions is not None
    assert forecast.current_conditions.temperature == 27.0
    assert forecast.current_conditions.condition_code == "partly-cloudy"


def test_current_conditions_no_timestamps(sample_place):
    """Test current_conditions with no forecast timestamps."""
    forecast = Forecast(
        place=sample_place,
        forecast_created=(datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        current_conditions=None,
        forecast_timestamps=[],
    )

    assert forecast.current_conditions is None


def test_filter_past_timestamps(sample_place, sample_timestamps):
    """Test that past timestamps are filtered out."""
    forecast = Forecast(
        place=sample_place,
        current_conditions=None,
        forecast_created=(datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        forecast_timestamps=[
            sample_timestamps["past"],
            sample_timestamps["future_1"],
            sample_timestamps["future_2"],
        ],
    )

    assert sample_timestamps["future_1"] in forecast.forecast_timestamps
    assert sample_timestamps["future_2"] in forecast.forecast_timestamps
    assert sample_timestamps["past"] not in forecast.forecast_timestamps


# Tests - ForecastTimestamp
def test_datetime_format():
    """Test ISO 8601 date format conversion."""
    sample_data = {
        "forecastTimeUtc": (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
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

    assert forecast_timestamp.datetime == sample_data["forecastTimeUtc"].replace(" ", "T") + "+00:00"


# Tests - HydroStation
def test_hydro_station_creation():
    """Test HydroStation creation and properties."""
    station = HydroStation(
        code="station_001",
        name="River Station",
        water_body="Nemunas River",
        coordinates=Coordinates(latitude=54.5, longitude=24.5),
    )

    assert station.code == "station_001"
    assert station.name == "River Station"
    assert station.water_body == "Nemunas River"
    assert station.latitude == 54.5
    assert station.longitude == 24.5


def test_hydro_station_from_dict():
    """Test HydroStation from_dict conversion."""
    data = {
        "code": "station_002",
        "name": "Lake Station",
        "waterBody": "Galvė Lake",
        "coordinates": {"latitude": 54.2, "longitude": 25.8},
    }
    station = HydroStation.from_dict(data)

    assert isinstance(station, HydroStation)
    assert station.code == "station_002"
    assert station.name == "Lake Station"
    assert station.latitude == 54.2
    assert station.longitude == 25.8


def test_hydro_station_coordinates_properties():
    """Test that HydroStation inherits location base properties."""
    station = HydroStation(
        code="station_006",
        name="Property Test Station",
        water_body="Property Test River",
        coordinates=Coordinates(latitude=55.1, longitude=23.9),
    )

    assert station.latitude == 55.1
    assert station.longitude == 23.9


# Tests - HydroObservation
@pytest.mark.parametrize("all_fields", [True, False])
def test_hydro_observation_creation(all_fields):
    """Test HydroObservation creation with all or partial fields."""
    if all_fields:
        observation = HydroObservation(
            observation_datetime="2023-01-01 12:00:00",
            water_level=125.5,
            water_temperature=8.3,
            water_discharge=50.2,
        )
        assert observation.observation_datetime == "2023-01-01 12:00:00"
        assert observation.water_level == 125.5
        assert observation.water_temperature == 8.3
        assert observation.water_discharge == 50.2
    else:
        observation = HydroObservation(
            observation_datetime="2023-01-01 12:00:00",
            water_level=125.5,
        )
        assert observation.observation_datetime == "2023-01-01 12:00:00"
        assert observation.water_level == 125.5
        assert observation.water_temperature is None
        assert observation.water_discharge is None


def test_hydro_observation_from_dict():
    """Test HydroObservation from_dict conversion."""
    data = {
        "observationTimeUtc": "2023-01-01 14:00:00",
        "waterLevel": 130.2,
        "waterTemperature": 7.5,
        "waterDischarge": 55.8,
    }
    observation = HydroObservation.from_dict(data)

    assert isinstance(observation, HydroObservation)
    assert observation is not None


# Tests - HydroObservationData
def test_hydro_observation_data_creation():
    """Test HydroObservationData creation."""
    station = HydroStation(
        code="station_003",
        name="Test Station",
        water_body="Test River",
        coordinates=Coordinates(latitude=54.0, longitude=24.0),
    )
    observations = [
        HydroObservation(
            observation_datetime="2023-01-01 12:00:00",
            water_level=120.0,
            water_temperature=5.0,
            water_discharge=40.0,
        ),
        HydroObservation(
            observation_datetime="2023-01-01 13:00:00",
            water_level=121.5,
            water_temperature=5.2,
            water_discharge=41.0,
        ),
    ]

    obs_data = HydroObservationData(
        station=station,
        observations_data_range="2023-01-01 to 2023-01-31",
        observations=observations,
    )

    assert obs_data.station == station
    assert obs_data.observations_data_range == "2023-01-01 to 2023-01-31"
    assert len(obs_data.observations) == 2
    assert obs_data.observations[0].water_level == 120.0
    assert obs_data.observations[1].water_level == 121.5


def test_hydro_observation_data_empty_observations():
    """Test HydroObservationData with no observations."""
    station = HydroStation(
        code="station_004",
        name="Empty Station",
        water_body="Empty River",
        coordinates=Coordinates(latitude=54.1, longitude=24.1),
    )

    obs_data = HydroObservationData(
        station=station,
        observations_data_range="2023-01-01 to 2023-01-31",
        observations=[],
    )

    assert obs_data.station == station
    assert len(obs_data.observations) == 0


def test_hydro_observation_data_from_dict():
    """Test HydroObservationData from_dict conversion."""
    data = {
        "station": {
            "code": "station_005",
            "name": "API Station",
            "waterBody": "API River",
            "coordinates": {"latitude": 54.3, "longitude": 24.3},
        },
        "observationsDataRange": "2023-01-01 to 2023-01-31",
        "observations": [
            {
                "observationTimeUtc": "2023-01-01 12:00:00",
                "waterLevel": 125.0,
                "waterTemperature": 6.0,
                "waterDischarge": 45.0,
            },
            {
                "observationTimeUtc": "2023-01-01 13:00:00",
                "waterLevel": 124.8,
                "waterTemperature": 6.1,
                "waterDischarge": 44.8,
            },
        ],
    }

    obs_data = HydroObservationData.from_dict(data)

    assert isinstance(obs_data, HydroObservationData)
    assert obs_data.station.code == "station_005"
    assert obs_data.station.name == "API Station"
    assert len(obs_data.observations) == 2
    assert obs_data.observations[0] is not None


# Tests - MeteoWarning
@pytest.mark.parametrize(
    "category,warning_type,severity,instruction",
    [
        ("weather", "wind", "Moderate", "Stay indoors"),
        ("weather", "storm", "High", None),
        ("hydro", "flood", "Extreme", "Evacuate immediately"),
        ("weather", "rain", "Minor", None),
    ],
)
def test_meteo_warning_creation(category, warning_type, severity, instruction):
    """Test MeteoWarning creation with various configurations."""
    kwargs = {
        "county": "Test County",
        "warning_type": warning_type,
        "severity": severity,
        "description": f"Test {warning_type} warning",
        "category": category,
    }

    if instruction:
        kwargs["instruction"] = instruction
        kwargs["start_time"] = "2025-09-30T12:00:00Z"
        kwargs["end_time"] = "2025-09-30T18:00:00Z"

    warning = MeteoWarning(**kwargs)

    assert warning.category == category
    assert warning.warning_type == warning_type
    assert warning.severity == severity
    assert warning.instruction == instruction

    if instruction:
        assert warning.start_time == "2025-09-30T12:00:00Z"
        assert warning.end_time == "2025-09-30T18:00:00Z"
    else:
        assert warning.start_time is None
        assert warning.end_time is None


def test_meteo_warning_default_category():
    """Test MeteoWarning default category is 'weather'."""
    warning = MeteoWarning(
        county="Test County",
        warning_type="wind",
        severity="Low",
        description="Test warning",
    )

    assert warning.category == "weather"
    assert warning.start_time is None
    assert warning.end_time is None
    assert warning.instruction is None
