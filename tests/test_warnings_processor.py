"""Tests for weather warnings processor"""

# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import patch

import pytest

from meteo_lt import MeteoWarning
from meteo_lt.client import MeteoLtClient
from meteo_lt.models import Coordinates, Forecast, ForecastTimestamp, Place
from meteo_lt.warnings import WarningsProcessor


# Fixtures
@pytest.fixture
def client():
    """Create client for testing"""
    return MeteoLtClient()


@pytest.fixture
def warnings_processor(client):
    """Create warnings processor for testing"""
    return WarningsProcessor(client)


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
                                "description": {"en": "Strong wind up to 20 m/s", "lt": "Stiprus vėjas iki 20 m/s"},
                                "instruction": {"en": "Be careful", "lt": "Būkite atsargūs"},
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }


# Helper functions
def create_alert(
    phenomenon="wind",
    severity="Moderate",
    description_en="Test",
    description_lt="Testas",
    instruction_en="",
    instruction_lt="",
):
    """Create test alert data"""
    return {
        "phenomenon": phenomenon,
        "severity": severity,
        "description": {"en": description_en, "lt": description_lt} if description_lt else {"en": description_en},
        "instruction": {"en": instruction_en, "lt": instruction_lt} if instruction_en or instruction_lt else {},
        "t_from": "2025-09-30T12:00:00Z",
        "t_to": "2025-09-30T18:00:00Z",
    }


def create_warning(
    administrative_division="Test",
    warning_type="wind",
    severity="Moderate",
    description="Test",
    start_time=None,
    end_time=None,
):
    """Create test warning"""
    return MeteoWarning(
        administrative_division=administrative_division,
        warning_type=warning_type,
        severity=severity,
        description=description,
        start_time=start_time,
        end_time=end_time,
    )


def create_forecast(timestamp_datetime="2025-09-30T15:00:00+00:00", with_current=True):
    """Create test forecast"""
    place = Place(
        code="test",
        name="Test",
        country_code="LT",
        administrative_division="Test sav.",
        coordinates=Coordinates(latitude=54.0, longitude=25.0),
    )

    timestamp = ForecastTimestamp(
        datetime=timestamp_datetime,
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

    return Forecast(
        place=place,
        forecast_created="2025-09-30 12:00:00",
        current_conditions=timestamp if with_current else None,
        forecast_timestamps=[timestamp],
    )


# Tests - Parsing
def test_parse_warnings_data(warnings_processor, mock_warnings_data):
    """Test parsing warnings data"""
    warnings = warnings_processor._parse_warnings_data(mock_warnings_data, "weather")

    assert len(warnings) == 1
    assert warnings[0].administrative_division == "Kauno apskritis"
    assert warnings[0].warning_type == "wind"
    assert warnings[0].severity == "Moderate"


@pytest.mark.parametrize("data", [[], {}, None, {"phenomenon_groups": []}])
def test_parse_warnings_data_empty(warnings_processor, data):
    """Test parsing empty or invalid warnings data"""
    warnings = warnings_processor._parse_warnings_data(data, "weather")
    assert warnings == []


def test_create_warning_from_alert(warnings_processor):
    """Test creating warning from alert data"""
    alert = create_alert(description_en="Strong wind", instruction_en="Be careful", instruction_lt="Būkite atsargūs")
    area = {"name": "Kauno apskritis"}
    warning = warnings_processor._create_warning_from_alert(alert, area, "weather")

    assert warning.administrative_division == "Kauno apskritis"
    assert warning.warning_type == "wind"
    assert warning.severity == "Moderate"
    assert warning.description == "Strong wind"
    assert warning.instruction == "Be careful"


@pytest.mark.parametrize("severity", ["Minor", "Moderate", "High", "Extreme"])
def test_create_warning_severity_levels(client, severity):
    """Test creating warnings with different severity levels"""
    processor = WarningsProcessor(client)
    alert = create_alert(severity=severity)
    warning = processor._create_warning_from_alert(alert, {"name": "Test"}, "weather")
    assert warning.severity == severity


@pytest.mark.parametrize(
    "phenomenon,expected_type",
    [
        ("dangerous-wind", "wind"),
        ("wind", "wind"),
        ("severe-dangerous-wind", "dangerous-wind"),
    ],
)
def test_create_warning_phenomenon_prefixes(client, phenomenon, expected_type):
    """Test warning type extraction with various phenomenon prefixes"""
    processor = WarningsProcessor(client)
    alert = create_alert(phenomenon=phenomenon)
    warning = processor._create_warning_from_alert(alert, {"name": "Test"}, "weather")
    assert warning.warning_type == expected_type


def test_create_warning_with_no_instruction(client):
    """Test creating warning when no instruction is provided"""
    processor = WarningsProcessor(client)
    alert = create_alert(description_en="Strong wind")
    warning = processor._create_warning_from_alert(alert, {"name": "Test"}, "weather")

    assert warning.description == "Strong wind"
    assert warning.instruction is None


@pytest.mark.parametrize(
    "description_data,should_skip",
    [
        ({"en": "Wind"}, True),  # No Lithuanian
        ({}, True),  # Empty description
        ({"lt": "Vėjas"}, False),  # Lithuanian only
    ],
)
def test_parse_warnings_with_missing_fields(client, description_data, should_skip):
    """Test parsing warnings with missing or incomplete fields"""
    processor = WarningsProcessor(client)
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
                                "description": description_data,
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

    warnings = processor._parse_warnings_data(data, "weather")
    assert len(warnings) == (0 if should_skip else 1)


def test_parse_warnings_skip_missing_phenomenon(client):
    """Test that warnings without phenomenon are skipped"""
    processor = WarningsProcessor(client)
    data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.county:LT001", "name": "Test"}],
                        "single_alerts": [
                            {
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

    warnings = processor._parse_warnings_data(data, "weather")
    assert len(warnings) == 0


def test_parse_warnings_with_empty_area_groups(client):
    """Test parsing warnings with empty area groups"""
    processor = WarningsProcessor(client)
    data = {"phenomenon_groups": [{"phenomenon_category": "wind", "area_groups": []}]}

    warnings = processor._parse_warnings_data(data, "weather")
    assert len(warnings) == 0


# Tests - Parsing


def test_parse_hydro_warnings_data(client):
    """Test parsing hydrological warnings data"""
    hydro_processor = WarningsProcessor(client)

    hydro_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "hydrological",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.hydro.county:LT001", "name": "Nemunas basin"}],
                        "single_alerts": [
                            create_alert(
                                phenomenon="dangerous-flood",
                                severity="High",
                                description_en="Dangerous flood",
                                description_lt="Pavojingas potvynis",
                                instruction_en="Evacuate",
                                instruction_lt="Evakuotis",
                            )
                        ],
                    }
                ],
            }
        ]
    }

    warnings = hydro_processor._parse_warnings_data(hydro_data, "hydro")

    assert len(warnings) == 1
    assert warnings[0].warning_type == "flood"
    assert warnings[0].category == "hydro"
    assert warnings[0].description == "Dangerous flood"
    assert warnings[0].instruction == "Evacuate"


# Tests - Area Matching
@pytest.mark.parametrize(
    "admin_division,should_match",
    [
        ("Kauno miesto", True),
        ("Kauno rajono", True),
        ("Vilniaus miesto", False),
    ],
)
def test_warning_affects_area(warnings_processor, admin_division, should_match):
    """Test if warning affects specific administrative division"""
    warning = create_warning(administrative_division="Kauno apskritis")
    assert warnings_processor._warning_affects_area(warning, admin_division) == should_match


def test_warning_affects_area_with_sav_abbreviation(client):
    """Test warning area matching with savivaldybė abbreviations"""
    processor = WarningsProcessor(client)
    warning = create_warning(administrative_division="Vilniaus miesto savivaldybė")

    assert processor._warning_affects_area(warning, "Vilniaus miesto sav.")
    assert processor._warning_affects_area(warning, "Vilniaus miesto")
    assert not processor._warning_affects_area(warning, "Kauno miesto")


# Tests - Timestamp Matching
@pytest.mark.parametrize(
    "timestamp,expected_count",
    [
        ("2025-09-30T15:00:00+00:00", 1),  # Within period (15:00-16:00 hour overlaps with 12:00-18:00 warning)
        ("2025-09-30T12:00:00+00:00", 1),  # Hour starting at warning start (12:00-13:00 overlaps)
        ("2025-09-30T17:00:00+00:00", 1),  # Hour ending at warning end (17:00-18:00 overlaps)
        ("2025-09-30T18:00:00+00:00", 0),  # Hour after warning ends (18:00-19:00, warning ends at 18:00)
        ("2025-09-30T10:00:00+00:00", 0),  # Before period
        ("2025-09-30T11:00:00+00:00", 0),  # Hour before warning starts (11:00-12:00, warning starts at 12:00)
    ],
)
def test_get_warnings_for_timestamp(warnings_processor, timestamp, expected_count):
    """Test getting warnings for specific timestamp (timestamp represents start of 1-hour period)"""
    warnings = [create_warning(start_time="2025-09-30T12:00:00Z", end_time="2025-09-30T18:00:00Z")]

    applicable = warnings_processor._get_warnings_for_timestamp(timestamp, warnings)
    assert len(applicable) == expected_count


def test_get_warnings_for_timestamp_with_timezone_offset(warnings_processor):
    """Test warning time matching with timezone offset timestamps

    Warning: 2026-02-05 23:30 UTC to 2026-02-06 11:00 UTC
    Timestamps represent hourly periods, so warning should match any hour it overlaps with.
    """
    warnings = [create_warning(start_time="2026-02-05T23:30:00Z", end_time="2026-02-06T11:00:00Z")]

    # 2026-02-06 02:30+02:00 = 2026-02-06 00:30 UTC (hour 00:00-01:00) → overlaps
    inside = warnings_processor._get_warnings_for_timestamp("2026-02-06T02:30:00+02:00", warnings)
    # 2026-02-06 01:00+02:00 = 2026-02-05 23:00 UTC (hour 23:00-00:00) → overlaps (warning starts at 23:30)
    also_inside = warnings_processor._get_warnings_for_timestamp("2026-02-06T01:00:00+02:00", warnings)
    # 2026-02-05 22:00+02:00 = 2026-02-05 20:00 UTC (hour 20:00-21:00) → no overlap
    outside = warnings_processor._get_warnings_for_timestamp("2026-02-05T22:00:00+02:00", warnings)

    assert len(inside) == 1
    assert len(also_inside) == 1
    assert len(outside) == 0


@pytest.mark.parametrize("timestamp", ["invalid-date", ""])
def test_get_warnings_for_timestamp_invalid_format(warnings_processor, timestamp):
    """Test warning time matching with invalid timestamp format"""
    warnings = [create_warning(start_time="2025-09-30T12:00:00Z", end_time="2025-09-30T18:00:00Z")]
    result = warnings_processor._get_warnings_for_timestamp(timestamp, warnings)
    assert len(result) == 0


def test_get_warnings_for_timestamp_with_missing_times(client):
    """Test warning time matching when warning has missing times"""
    processor = WarningsProcessor(client)
    warning = create_warning()  # No start/end times

    result = processor._get_warnings_for_timestamp("2025-09-30T15:00:00+00:00", [warning])
    assert len(result) == 0


def test_get_warnings_for_timestamp_with_invalid_warning_times(client):
    """Test handling warnings with invalid start/end times"""
    processor = WarningsProcessor(client)

    valid_warning = create_warning(start_time="2025-09-30T12:00:00Z", end_time="2025-09-30T18:00:00Z")
    invalid_warning = create_warning(warning_type="storm", start_time="not-a-valid-date", end_time="also-invalid")

    result = processor._get_warnings_for_timestamp("2025-09-30T15:00:00+00:00", [valid_warning, invalid_warning])
    assert len(result) == 1
    assert result[0].warning_type == "wind"


# Tests - Async API
@pytest.mark.asyncio
async def test_get_weather_warnings(warnings_processor, mock_warnings_data):
    """Test getting weather warnings"""
    with patch.object(warnings_processor.client, "fetch_warnings") as mock_fetch:
        mock_fetch.return_value = mock_warnings_data
        warnings = await warnings_processor.get_weather_warnings()

        assert len(warnings) == 1
        assert warnings[0].administrative_division == "Kauno apskritis"


@pytest.mark.asyncio
async def test_get_weather_warnings_filtered(warnings_processor, mock_warnings_data):
    """Test getting weather warnings filtered by area"""
    with patch.object(warnings_processor.client, "fetch_warnings") as mock_fetch:
        mock_fetch.return_value = mock_warnings_data

        warnings = await warnings_processor.get_weather_warnings("Kauno miesto")
        assert len(warnings) == 1

        warnings = await warnings_processor.get_weather_warnings("Vilniaus miesto")
        assert len(warnings) == 0


@pytest.mark.asyncio
async def test_get_warnings_with_hydro_category(client):
    """Test getting hydrological warnings with category filter"""
    hydro_processor = WarningsProcessor(client)

    hydro_data = {
        "phenomenon_groups": [
            {
                "phenomenon_category": "hydrological",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.hydro:LT001", "name": "Nemunas"}],
                        "single_alerts": [
                            create_alert(
                                phenomenon="severe-flood",
                                severity="High",
                                description_en="Severe flood",
                                description_lt="Pavojingas potvynis",
                                instruction_en="Evacuate",
                                instruction_lt="Evakuotis",
                            )
                        ],
                    }
                ],
            }
        ]
    }

    with patch.object(hydro_processor.client, "fetch_warnings") as mock_fetch:
        mock_fetch.return_value = hydro_data
        warnings = await hydro_processor.get_hydro_warnings()

        assert len(warnings) == 1
        assert warnings[0].category == "hydro"
        assert warnings[0].warning_type == "flood"


# Tests - Forecast Enrichment
def test_enrich_forecast_with_warnings_and_current_conditions(client):
    """Test enriching forecast that includes current conditions"""
    processor = WarningsProcessor(client)
    forecast = create_forecast()
    warning = create_warning(start_time="2025-09-30T10:00:00Z", end_time="2025-09-30T14:00:00Z")

    processor.enrich_forecast_with_warnings(forecast, [warning])

    assert hasattr(forecast.current_conditions, "warnings")
    assert isinstance(forecast.current_conditions.warnings, list)


def test_enrich_forecast_without_current_conditions(client):
    """Test enriching forecast when current conditions are None"""
    processor = WarningsProcessor(client)
    forecast = create_forecast(with_current=False)
    warning = create_warning(start_time="2025-09-30T10:00:00Z", end_time="2025-09-30T14:00:00Z")

    # Should not raise an exception
    processor.enrich_forecast_with_warnings(forecast, [warning])


def test_enrich_forecast_with_empty_warnings(client):
    """Test enriching forecast with empty warnings list"""
    processor = WarningsProcessor(client)
    forecast = create_forecast()

    processor.enrich_forecast_with_warnings(forecast, [])

    if hasattr(forecast.current_conditions, "warnings"):
        assert forecast.current_conditions.warnings == []


def test_enrich_forecast_extends_existing_warnings(client):
    """Test that warnings are extended (not replaced) on current_conditions"""
    processor = WarningsProcessor(client)
    forecast = create_forecast()

    # Pre-populate with existing warning
    existing_warning = create_warning(warning_type="rain", severity="Low", description="Existing warning")
    forecast.current_conditions.warnings = [existing_warning]

    new_warning = create_warning(start_time="2025-09-30T12:00:00Z", end_time="2025-09-30T18:00:00Z")
    processor.enrich_forecast_with_warnings(forecast, [new_warning])

    # Should have both warnings
    assert len(forecast.current_conditions.warnings) == 2
    assert forecast.current_conditions.warnings[0].warning_type == "rain"
    assert forecast.current_conditions.warnings[1].warning_type == "wind"


def test_enrich_forecast_initializes_warnings_attribute(client):
    """Test that warnings list is initialized when attribute doesn't exist"""
    processor = WarningsProcessor(client)
    # Create forecast without current conditions to test timestamp initialization (line 144)
    forecast_no_current = create_forecast(timestamp_datetime="2027-09-30T15:00:00+00:00", with_current=False)

    # Remove warnings attribute from timestamps to force initialization
    for ts in forecast_no_current.forecast_timestamps:
        if hasattr(ts, "warnings"):
            delattr(ts, "warnings")

    warning = create_warning(start_time="2027-09-30T12:00:00Z", end_time="2027-09-30T18:00:00Z")
    processor.enrich_forecast_with_warnings(forecast_no_current, [warning])

    # Verify timestamps have warnings initialized (line 144 covered)
    if forecast_no_current.forecast_timestamps:
        assert hasattr(forecast_no_current.forecast_timestamps[0], "warnings")
        assert isinstance(forecast_no_current.forecast_timestamps[0].warnings, list)

    # Test current_conditions initialization (line 152)
    # Since current_conditions and forecast_timestamps[0] are the same object,
    # we need to add warnings back to timestamp then remove from current_conditions
    forecast_with_current = create_forecast(timestamp_datetime="2027-09-30T15:00:00+00:00", with_current=True)
    # Ensure timestamp has warnings attribute
    if forecast_with_current.forecast_timestamps:
        forecast_with_current.forecast_timestamps[0].warnings = []
    # Now remove from current_conditions (different code path since it's checking hasattr)
    if hasattr(forecast_with_current.current_conditions, "warnings"):
        del forecast_with_current.current_conditions.warnings

    processor.enrich_forecast_with_warnings(forecast_with_current, [warning])
    # Should have initialized warnings on current_conditions (line 152 covered)
    assert hasattr(forecast_with_current.current_conditions, "warnings")


def test_enrich_forecast_timestamps_with_matching_warnings(client):
    """Test that warnings are added to forecast_timestamps when they match"""
    processor = WarningsProcessor(client)
    forecast = create_forecast(timestamp_datetime="2026-09-30T15:00:00+00:00", with_current=False)
    warning = create_warning(start_time="2026-09-30T12:00:00Z", end_time="2026-09-30T18:00:00Z")

    processor.enrich_forecast_with_warnings(forecast, [warning])

    assert hasattr(forecast.forecast_timestamps[0], "warnings")
    assert len(forecast.forecast_timestamps[0].warnings) == 1
    assert forecast.forecast_timestamps[0].warnings[0].warning_type == "wind"
