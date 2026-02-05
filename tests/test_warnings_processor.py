"""Tests for weather warnings processor"""

# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import patch

import pytest

from meteo_lt import MeteoWarning
from meteo_lt.client import MeteoLtClient
from meteo_lt.warnings import WarningsProcessor
from meteo_lt.models import Place, Coordinates, Forecast, ForecastTimestamp


@pytest.fixture
def client():
    """Create client for testing"""
    return MeteoLtClient()


@pytest.fixture
def warnings_processor(client):
    """Create warnings processor for testing"""
    return WarningsProcessor(client, category="weather")


@pytest.fixture
def mock_warnings_data():
    """Mock warnings JSON data"""
    return {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.lhms.county:LT002", "name": "Kauno apskritis"}],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {
                                    "en": "Strong wind up to 20 m/s",
                                    "lt": "Stiprus vėjas iki 20 m/s",
                                },
                                "instruction": {
                                    "en": "Be careful",
                                    "lt": "Būkite atsargūs",
                                },
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }


def test_parse_warnings_data(warnings_processor, mock_warnings_data):
    """Test parsing warnings data"""
    warnings = warnings_processor._parse_warnings_data(mock_warnings_data)

    assert len(warnings) == 1
    assert warnings[0].county == "Kauno apskritis"
    assert warnings[0].warning_type == "wind"
    assert warnings[0].severity == "Moderate"


def test_parse_warnings_data_empty(warnings_processor):
    """Test parsing empty warnings data"""
    # Test with empty list
    warnings = warnings_processor._parse_warnings_data([])
    assert warnings == []

    # Test with empty dict
    warnings = warnings_processor._parse_warnings_data({})
    assert warnings == []

    # Test with None
    warnings = warnings_processor._parse_warnings_data(None)
    assert warnings == []


def test_create_warning_from_alert(warnings_processor):
    """Test creating warning from alert data"""
    alert = {
        "phenomenon": "wind",
        "severity": "Moderate",
        "description": {"en": "Strong wind", "lt": "Stiprus vėjas"},
        "instruction": {"en": "Be careful", "lt": "Būkite atsargūs"},
        "t_from": "2025-09-30T12:00:00Z",
        "t_to": "2025-09-30T18:00:00Z",
    }

    area = {"name": "Kauno apskritis"}

    warning = warnings_processor._create_warning_from_alert(alert, area)

    assert warning is not None
    assert warning.county == "Kauno apskritis"
    assert warning.warning_type == "wind"
    assert warning.severity == "Moderate"
    assert "Be careful" in warning.description


def test_warning_affects_area(warnings_processor):
    """Test if warning affects specific administrative division"""
    warning = MeteoWarning(
        county="Kauno apskritis",
        warning_type="wind",
        severity="Moderate",
        description="Test warning",
    )

    assert warnings_processor._warning_affects_area(warning, "Kauno miesto")
    assert warnings_processor._warning_affects_area(warning, "Kauno rajono")
    assert not warnings_processor._warning_affects_area(warning, "Vilniaus miesto")


def test_get_warnings_for_timestamp(warnings_processor):
    """Test getting warnings for specific timestamp"""
    warnings = [
        MeteoWarning(
            county="Kauno apskritis",
            warning_type="wind",
            severity="Moderate",
            description="Strong wind",
            start_time="2025-09-30T12:00:00Z",
            end_time="2025-09-30T18:00:00Z",
        )
    ]

    # Test timestamp within warning period
    applicable = warnings_processor._get_warnings_for_timestamp("2025-09-30T15:00:00+00:00", warnings)
    assert len(applicable) == 1
    assert applicable[0].warning_type == "wind"

    # Test timestamp outside warning period
    applicable = warnings_processor._get_warnings_for_timestamp("2025-09-30T20:00:00+00:00", warnings)
    assert len(applicable) == 0

    # Test timestamp before warning period
    applicable = warnings_processor._get_warnings_for_timestamp("2025-09-30T10:00:00+00:00", warnings)
    assert len(applicable) == 0


@pytest.mark.asyncio
async def test_get_weather_warnings(warnings_processor, mock_warnings_data):
    """Test getting weather warnings"""
    with patch.object(warnings_processor.client, "fetch_warnings") as mock_fetch:
        mock_fetch.return_value = mock_warnings_data

        warnings = await warnings_processor.get_warnings()

        assert len(warnings) == 1
        assert warnings[0].county == "Kauno apskritis"


@pytest.mark.asyncio
async def test_get_weather_warnings_filtered(warnings_processor, mock_warnings_data):
    """Test getting weather warnings filtered by area"""
    with patch.object(warnings_processor.client, "fetch_warnings") as mock_fetch:
        mock_fetch.return_value = mock_warnings_data

        warnings = await warnings_processor.get_warnings("Kauno miesto")

        assert len(warnings) == 1
        assert warnings[0].county == "Kauno apskritis"

        # Test with non-matching area
        warnings = await warnings_processor.get_warnings("Vilniaus miesto")
        assert len(warnings) == 0


def test_parse_hydro_warnings_data(client):
    """Test parsing hydrological warnings data"""
    hydro_processor = WarningsProcessor(client, category="hydro")

    hydro_warnings_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "hydrological",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.hydro.county:LT001", "name": "Nemunas basin"}],
                        "single_alerts": [
                            {
                                "phenomenon": "dangerous-flood",
                                "severity": "High",
                                "description": {
                                    "en": "Dangerous flood",
                                    "lt": "Pavojingas potvynis",
                                },
                                "instruction": {
                                    "en": "Evacuate",
                                    "lt": "Evakuotis",
                                },
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-10-01T12:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    warnings = hydro_processor._parse_warnings_data(hydro_warnings_data)

    assert len(warnings) == 1
    assert warnings[0].warning_type == "flood"  # 'dangerous-' prefix removed
    assert warnings[0].category == "hydro"
    assert "Evacuate" in warnings[0].description


def test_parse_warnings_filters_weather_from_hydro():
    """Test that hydro processor filters out weather warnings"""
    hydro_processor = WarningsProcessor(MeteoLtClient(), category="hydro")

    mixed_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.county:LT001", "name": "Test"}],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {"en": "Wind", "lt": "Vėjas"},
                                "instruction": {},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            },
            {
                "phenomenon_category": "hydrological",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.hydro:LT001", "name": "River"}],
                        "single_alerts": [
                            {
                                "phenomenon": "flood",
                                "severity": "High",
                                "description": {"en": "Flood", "lt": "Potvynis"},
                                "instruction": {},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            },
        ]
    }

    warnings = hydro_processor._parse_warnings_data(mixed_data)
    assert len(warnings) == 1
    assert warnings[0].warning_type == "flood"


def test_parse_warnings_filters_hydro_from_weather():
    """Test that weather processor filters out hydrological warnings"""
    weather_processor = WarningsProcessor(MeteoLtClient(), category="weather")

    mixed_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.county:LT001", "name": "Test"}],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {"en": "Wind", "lt": "Vėjas"},
                                "instruction": {},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            },
            {
                "phenomenon_category": "hydrological",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.hydro:LT001", "name": "River"}],
                        "single_alerts": [
                            {
                                "phenomenon": "flood",
                                "severity": "High",
                                "description": {"en": "Flood", "lt": "Potvynis"},
                                "instruction": {},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            },
        ]
    }

    warnings = weather_processor._parse_warnings_data(mixed_data)
    assert len(warnings) == 1
    assert warnings[0].warning_type == "wind"


def test_parse_warnings_with_missing_fields(client):
    """Test parsing warnings with missing description fields"""
    processor = WarningsProcessor(client, category="weather")

    incomplete_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.county:LT001", "name": "Test County"}],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {"lt": "Stiprus vėjas"},  # No English
                                "instruction": {"lt": "Būkite atsargūs"},  # No English
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    warnings = processor._parse_warnings_data(incomplete_data)
    assert len(warnings) == 1
    assert "Stiprus vėjas" in warnings[0].description


def test_get_warnings_for_timestamp_boundary_times(client):
    """Test warning time matching at exact boundaries"""
    processor = WarningsProcessor(client, category="weather")

    warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Test",
        start_time="2025-09-30T12:00:00Z",
        end_time="2025-09-30T18:00:00Z",
    )

    # Exact start time should match
    result = processor._get_warnings_for_timestamp("2025-09-30T12:00:00+00:00", [warning])
    assert len(result) == 1

    # Exact end time should match
    result = processor._get_warnings_for_timestamp("2025-09-30T18:00:00+00:00", [warning])
    assert len(result) == 1


def test_get_warnings_for_timestamp_invalid_format(client):
    """Test warning time matching with invalid timestamp format"""
    processor = WarningsProcessor(client, category="weather")

    warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Test",
        start_time="2025-09-30T12:00:00Z",
        end_time="2025-09-30T18:00:00Z",
    )

    # Invalid timestamp format should return empty list
    result = processor._get_warnings_for_timestamp("invalid-date", [warning])
    assert len(result) == 0


def test_get_warnings_for_timestamp_with_missing_times(client):
    """Test warning time matching when warning has missing times"""
    processor = WarningsProcessor(client, category="weather")

    warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Test",
        # No start/end times
    )

    result = processor._get_warnings_for_timestamp("2025-09-30T15:00:00+00:00", [warning])
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_warnings_with_hydro_category(client):
    """Test getting hydrological warnings with category filter"""
    hydro_processor = WarningsProcessor(client, category="hydro")

    hydro_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "hydrological",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.hydro:LT001", "name": "Nemunas"}],
                        "single_alerts": [
                            {
                                "phenomenon": "severe-flood",
                                "severity": "High",
                                "description": {"en": "Severe flood", "lt": "Pavojingas potvynis"},
                                "instruction": {"en": "Evacuate", "lt": "Evakuotis"},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-10-01T12:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    with patch.object(hydro_processor.client, "fetch_warnings") as mock_fetch:
        mock_fetch.return_value = hydro_data

        warnings = await hydro_processor.get_warnings()

        assert len(warnings) == 1
        assert warnings[0].category == "hydro"
        assert warnings[0].warning_type == "flood"


def test_create_warning_severity_levels(client):
    """Test creating warnings with different severity levels"""
    processor = WarningsProcessor(client, category="weather")

    severities = ["Minor", "Moderate", "High", "Extreme"]
    for severity in severities:
        alert = {
            "phenomenon": "wind",
            "severity": severity,
            "description": {"en": f"{severity} wind", "lt": "V\u0117jas"},
            "instruction": {},
            "t_from": "2025-09-30T12:00:00Z",
            "t_to": "2025-09-30T18:00:00Z",
        }

        area = {"name": "Test County"}
        warning = processor._create_warning_from_alert(alert, area)

        assert warning.severity == severity


def test_create_warning_phenomenon_prefixes(client):
    """Test warning type extraction with various phenomenon prefixes"""
    processor = WarningsProcessor(client, category="weather")

    test_cases = [
        ("dangerous-wind", "wind"),
        ("severe-frost", "frost"),
        ("extreme-heat", "heat"),
        ("wind", "wind"),
        ("severe-dangerous-wind", "dangerous-wind"),  # Only first prefix removed
    ]

    for phenomenon, expected_type in test_cases:
        alert = {
            "phenomenon": phenomenon,
            "severity": "Moderate",
            "description": {"en": "Test", "lt": "Testas"},
            "instruction": {},
            "t_from": "2025-09-30T12:00:00Z",
            "t_to": "2025-09-30T18:00:00Z",
        }

        area = {"name": "Test County"}
        warning = processor._create_warning_from_alert(alert, area)

        assert warning.warning_type == expected_type


def test_enrich_forecast_with_warnings_and_current_conditions(client):
    """Test enriching forecast that includes current conditions"""
    processor = WarningsProcessor(client, category="weather")

    current_ts = ForecastTimestamp(
        datetime="2023-01-01T12:00:00",
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

    forecast_ts = ForecastTimestamp(
        datetime="2023-01-01T15:00:00",
        temperature=17.0,
        apparent_temperature=16.0,
        condition_code="clear",
        wind_speed=6.0,
        wind_gust_speed=9.0,
        wind_bearing=180.0,
        cloud_coverage=10,
        pressure=1013.25,
        humidity=60,
        precipitation=0.0,
    )

    forecast = Forecast(
        place=Place(
            code="test",
            name="Test",
            country_code="LT",
            administrative_division="Test Admin",
            coordinates=Coordinates(latitude=1.0, longitude=2.0),
        ),
        forecast_created="2023-01-01T12:00:00",
        current_conditions=current_ts,
        forecast_timestamps=[forecast_ts],
    )

    warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Test",
        start_time="2023-01-01T10:00:00Z",
        end_time="2023-01-01T14:00:00Z",
    )

    processor.enrich_forecast_with_warnings(forecast, [warning])

    # Check that warnings were added to current conditions
    assert hasattr(forecast.current_conditions, "warnings")
    assert isinstance(forecast.current_conditions.warnings, list)


def test_enrich_forecast_without_current_conditions(client):
    """Test enriching forecast when current conditions are None"""
    processor = WarningsProcessor(client, category="weather")

    forecast_ts = ForecastTimestamp(
        datetime="2023-01-01T15:00:00",
        temperature=17.0,
        apparent_temperature=16.0,
        condition_code="clear",
        wind_speed=6.0,
        wind_gust_speed=9.0,
        wind_bearing=180.0,
        cloud_coverage=10,
        pressure=1013.25,
        humidity=60,
        precipitation=0.0,
    )

    forecast = Forecast(
        place=Place(
            code="test",
            name="Test",
            country_code="LT",
            administrative_division="Test Admin",
            coordinates=Coordinates(latitude=1.0, longitude=2.0),
        ),
        forecast_created="2023-01-01T12:00:00",
        current_conditions=None,
        forecast_timestamps=[forecast_ts],
    )

    warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Test",
        start_time="2023-01-01T10:00:00Z",
        end_time="2023-01-01T14:00:00Z",
    )

    # Should not raise an exception
    processor.enrich_forecast_with_warnings(forecast, [warning])


def test_create_warning_with_no_instruction(client):
    """Test creating warning when no instruction is provided"""
    processor = WarningsProcessor(client, category="weather")

    alert = {
        "phenomenon": "wind",
        "severity": "Moderate",
        "description": {"en": "Strong wind", "lt": "Stiprus v\u0117jas"},
        "instruction": {},  # Empty instruction
        "t_from": "2025-09-30T12:00:00Z",
        "t_to": "2025-09-30T18:00:00Z",
    }

    area = {"name": "Test County"}
    warning = processor._create_warning_from_alert(alert, area)

    assert warning.description == "Strong wind"
    assert "Recommendations" not in warning.description


def test_parse_warnings_with_empty_area_groups(client):
    """Test parsing warnings with empty area groups"""
    processor = WarningsProcessor(client, category="weather")

    data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [],  # Empty area groups
            }
        ]
    }

    warnings = processor._parse_warnings_data(data)
    assert len(warnings) == 0


def test_parse_warnings_skip_missing_description(client):
    """Test that warnings without Lithuanian description are skipped"""
    processor = WarningsProcessor(client, category="weather")

    data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.county:LT001", "name": "Test"}],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {"en": "Wind"},  # No Lithuanian
                                "instruction": {},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    warnings = processor._parse_warnings_data(data)
    assert len(warnings) == 0  # Should be skipped


def test_parse_warnings_skip_missing_phenomenon(client):
    """Test that warnings without phenomenon are skipped"""
    processor = WarningsProcessor(client, category="weather")

    data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.county:LT001", "name": "Test"}],
                        "single_alerts": [
                            {
                                # Missing phenomenon
                                "severity": "Moderate",
                                "description": {"en": "Test", "lt": "Testas"},
                                "instruction": {},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    warnings = processor._parse_warnings_data(data)
    assert len(warnings) == 0  # Should be skipped


def test_warning_affects_area_with_sav_abbreviation(client):
    """Test warning area matching with savivaldybė abbreviations"""
    processor = WarningsProcessor(client, category="weather")

    warning = MeteoWarning(
        county="Vilniaus miesto savivaldybė",
        warning_type="wind",
        severity="Moderate",
        description="Test",
    )

    # Test with abbreviation
    assert processor._warning_affects_area(warning, "Vilniaus miesto sav.")
    # Test with full name variant
    assert processor._warning_affects_area(warning, "Vilniaus miesto")
    # Test non-matching
    assert not processor._warning_affects_area(warning, "Kauno miesto")


def test_enrich_forecast_with_empty_warnings(client):
    """Test enriching forecast with empty warnings list"""
    processor = WarningsProcessor(client, category="weather")

    place = Place(
        code="test",
        name="Test",
        country_code="LT",
        administrative_division="Test sav.",
        coordinates=Coordinates(latitude=54.0, longitude=25.0),
    )

    timestamp = ForecastTimestamp(
        datetime="2025-09-30T15:00:00+00:00",
        temperature=15.0,
        apparent_temperature=14.0,
        condition_code="clear",
        wind_speed=5.0,
        wind_gust_speed=8.0,
        wind_bearing=180.0,
        cloud_coverage=10,
        pressure=1013.0,
        humidity=65,
        precipitation=0.0,
    )

    forecast = Forecast(
        place=place,
        forecast_created="2025-09-30 12:00:00",
        current_conditions=timestamp,
        forecast_timestamps=[timestamp],
    )

    # Test with empty warnings list
    processor.enrich_forecast_with_warnings(forecast, [])

    # Should not add warnings attribute or should be empty
    if hasattr(timestamp, "warnings"):
        assert timestamp.warnings == []


def test_enrich_forecast_with_current_conditions_and_warnings(client):
    """Test enriching forecast with current_conditions that receives warnings"""
    processor = WarningsProcessor(client, category="weather")

    place = Place(
        code="test",
        name="Test",
        country_code="LT",
        administrative_division="Test sav.",
        coordinates=Coordinates(latitude=54.0, longitude=25.0),
    )

    timestamp = ForecastTimestamp(
        datetime="2025-09-30T15:00:00+00:00",
        temperature=15.0,
        apparent_temperature=14.0,
        condition_code="clear",
        wind_speed=5.0,
        wind_gust_speed=8.0,
        wind_bearing=180.0,
        cloud_coverage=10,
        pressure=1013.0,
        humidity=65,
        precipitation=0.0,
    )

    forecast = Forecast(
        place=place,
        forecast_created="2025-09-30 12:00:00",
        current_conditions=timestamp,
        forecast_timestamps=[],
    )

    warning = MeteoWarning(
        county="Test sav.",
        warning_type="wind",
        severity="Moderate",
        description="Test warning",
        start_time="2025-09-30T12:00:00Z",
        end_time="2025-09-30T18:00:00Z",
    )

    processor.enrich_forecast_with_warnings(forecast, [warning])

    # Current conditions should have the warning
    assert hasattr(forecast.current_conditions, "warnings")
    assert len(forecast.current_conditions.warnings) == 1
    assert forecast.current_conditions.warnings[0].warning_type == "wind"


def test_enrich_forecast_extends_existing_warnings_on_current_conditions(client):
    """Test that warnings are extended (not replaced) on current_conditions"""
    processor = WarningsProcessor(client, category="weather")

    place = Place(
        code="test",
        name="Test",
        country_code="LT",
        administrative_division="Test sav.",
        coordinates=Coordinates(latitude=54.0, longitude=25.0),
    )

    timestamp = ForecastTimestamp(
        datetime="2025-09-30T15:00:00+00:00",
        temperature=15.0,
        apparent_temperature=14.0,
        condition_code="clear",
        wind_speed=5.0,
        wind_gust_speed=8.0,
        wind_bearing=180.0,
        cloud_coverage=10,
        pressure=1013.0,
        humidity=65,
        precipitation=0.0,
    )

    # Pre-populate warnings on current_conditions
    existing_warning = MeteoWarning(
        county="Test sav.",
        warning_type="rain",
        severity="Low",
        description="Existing warning",
    )
    timestamp.warnings = [existing_warning]

    forecast = Forecast(
        place=place,
        forecast_created="2025-09-30 12:00:00",
        current_conditions=timestamp,
        forecast_timestamps=[],
    )

    new_warning = MeteoWarning(
        county="Test sav.",
        warning_type="wind",
        severity="Moderate",
        description="New warning",
        start_time="2025-09-30T12:00:00Z",
        end_time="2025-09-30T18:00:00Z",
    )

    processor.enrich_forecast_with_warnings(forecast, [new_warning])

    # Should have both warnings now
    assert len(forecast.current_conditions.warnings) == 2
    assert forecast.current_conditions.warnings[0].warning_type == "rain"
    assert forecast.current_conditions.warnings[1].warning_type == "wind"


def test_enrich_forecast_timestamps_with_matching_warnings(client):
    """Test that warnings are added to forecast_timestamps when they match"""
    processor = WarningsProcessor(client, category="weather")

    place = Place(
        code="test",
        name="Test",
        country_code="LT",
        administrative_division="Test sav.",
        coordinates=Coordinates(latitude=54.0, longitude=25.0),
    )

    # Create forecast timestamp that falls within warning period (use future date)
    forecast_ts = ForecastTimestamp(
        datetime="2026-09-30T15:00:00+00:00",
        temperature=15.0,
        apparent_temperature=14.0,
        condition_code="clear",
        wind_speed=5.0,
        wind_gust_speed=8.0,
        wind_bearing=180.0,
        cloud_coverage=10,
        pressure=1013.0,
        humidity=65,
        precipitation=0.0,
    )

    forecast = Forecast(
        place=place,
        forecast_created="2026-09-30 12:00:00",
        current_conditions=None,
        forecast_timestamps=[forecast_ts],
    )

    warning = MeteoWarning(
        county="Test sav.",
        warning_type="wind",
        severity="Moderate",
        description="Test warning",
        start_time="2026-09-30T12:00:00Z",
        end_time="2026-09-30T18:00:00Z",
    )

    processor.enrich_forecast_with_warnings(forecast, [warning])

    # Forecast timestamp should have the warning
    assert len(forecast.forecast_timestamps) > 0
    assert hasattr(forecast.forecast_timestamps[0], "warnings")
    assert len(forecast.forecast_timestamps[0].warnings) == 1
    assert forecast.forecast_timestamps[0].warnings[0].warning_type == "wind"


def test_get_warnings_for_timestamp_with_invalid_warning_times(client):
    """Test handling warnings with invalid start/end times"""
    processor = WarningsProcessor(client, category="weather")

    # Create warnings with invalid time formats
    valid_warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Valid warning",
        start_time="2025-09-30T12:00:00Z",
        end_time="2025-09-30T18:00:00Z",
    )

    invalid_warning = MeteoWarning(
        county="Test",
        warning_type="storm",
        severity="High",
        description="Invalid warning",
        start_time="not-a-valid-date",
        end_time="also-invalid",
    )

    warnings = [valid_warning, invalid_warning]

    # Should only return the valid warning
    result = processor._get_warnings_for_timestamp("2025-09-30T15:00:00+00:00", warnings)
    assert len(result) == 1
    assert result[0].warning_type == "wind"


def test_get_warnings_for_timestamp_with_attribute_error(client):
    """Test handling warnings when start_time/end_time cause AttributeError"""
    processor = WarningsProcessor(client, category="weather")

    # Create a warning where start_time might not have .replace method
    warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Test",
    )
    # Manually set invalid time types that could cause AttributeError
    warning.start_time = None
    warning.end_time = None

    result = processor._get_warnings_for_timestamp("2025-09-30T15:00:00+00:00", [warning])
    assert len(result) == 0


def test_get_warnings_for_timestamp_with_invalid_timestamp_param(client):
    """Test _get_warnings_for_timestamp when timestamp parameter itself is invalid"""
    processor = WarningsProcessor(client, category="weather")

    warning = MeteoWarning(
        county="Test",
        warning_type="wind",
        severity="Moderate",
        description="Test",
        start_time="2025-09-30T12:00:00Z",
        end_time="2025-09-30T18:00:00Z",
    )

    # Test with completely invalid timestamp
    result = processor._get_warnings_for_timestamp("not-a-valid-timestamp", [warning])
    assert len(result) == 0

    # Test with empty string timestamp
    result = processor._get_warnings_for_timestamp("", [warning])
    assert len(result) == 0
