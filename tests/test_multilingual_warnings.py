"""Tests for multilingual warning support"""

from meteo_lt.models import MeteoWarning


def test_meteo_warning_multilingual_properties():
    """Test MeteoWarning with multilingual translations"""
    warning = MeteoWarning(
        administrative_division="Vilniaus miesto sav.",
        warning_type="wind",
        severity="Moderate",
        description="Strong wind expected",
        category="weather",
        start_time="2026-02-10T12:00:00Z",
        end_time="2026-02-10T18:00:00Z",
        instruction="Secure loose objects",
        description_translations={
            "en": "Strong wind expected",
            "lt": "Tikėtinas stiprus vėjas",
        },
        instruction_translations={
            "en": "Secure loose objects",
            "lt": "Pritvirtinkite laisvus daiktus",
        },
    )

    # Test backward compatibility (default fields)
    assert warning.description == "Strong wind expected"
    assert warning.instruction == "Secure loose objects"

    # Test English translations
    assert warning.get_description("en") == "Strong wind expected"
    assert warning.get_instruction("en") == "Secure loose objects"

    # Test Lithuanian translations
    assert warning.get_description("lt") == "Tikėtinas stiprus vėjas"
    assert warning.get_instruction("lt") == "Pritvirtinkite laisvus daiktus"

    # Test available languages
    assert set(warning.available_languages) == {"en", "lt"}


def test_meteo_warning_fallback_to_default():
    """Test that missing translations fall back to default"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="rain",
        severity="Minor",
        description="Default rain description",
        category="weather",
        instruction="Default instruction",
        description_translations={"en": "Rain expected"},
        # No instruction_translations - should fallback
    )

    # Requesting language not in translations should fallback to default
    assert warning.get_description("fr") == "Default rain description"
    assert warning.get_instruction("lt") == "Default instruction"


def test_meteo_warning_no_translations():
    """Test warning without any translations (backward compatibility)"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="snow",
        severity="Severe",
        description="Heavy snow",
        category="weather",
        instruction="Stay indoors",
    )

    # Should work without translations
    assert warning.get_description("en") == "Heavy snow"
    assert warning.get_instruction("lt") == "Stay indoors"
    assert warning.available_languages == []


def test_meteo_warning_partial_translations():
    """Test warning with only some fields translated"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="storm",
        severity="Extreme",
        description="Dangerous storm",
        category="weather",
        description_translations={
            "en": "Dangerous storm approaching",
            "lt": "Artėja pavojinga audra",
        },
        # No instruction_translations
    )

    assert warning.get_description("en") == "Dangerous storm approaching"
    assert warning.get_description("lt") == "Artėja pavojinga audra"
    assert warning.get_instruction("en") is None
    assert warning.available_languages == ["en", "lt"]


def test_meteo_warning_empty_strings_in_model():
    """Test that model handles empty string translations"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="fog",
        severity="Moderate",
        description="Fog expected",
        category="weather",
        description_translations={
            "en": "Dense fog expected",
            "lt": "",  # Empty string present
        },
    )

    # Model doesn't filter empty strings - that happens during parsing
    assert "lt" in warning.description_translations
    # But empty string is returned when requested
    assert warning.get_description("lt") == ""
    # available_languages includes language even if empty
    assert set(warning.available_languages) == {"en", "lt"}


def test_meteo_warning_all_fields():
    """Test warning with all fields populated"""
    warning = MeteoWarning(
        administrative_division="Vilniaus apskritis",
        warning_type="thunderstorm",
        severity="Severe",
        description="Severe thunderstorms expected",
        category="weather",
        start_time="2026-02-10T14:00:00Z",
        end_time="2026-02-10T20:00:00Z",
        instruction="Seek shelter immediately",
        description_translations={
            "en": "Severe thunderstorms with hail expected",
            "lt": "Tikėtini stiprūs perkūnijos su kruša",
        },
        instruction_translations={
            "en": "Seek shelter immediately. Avoid open areas.",
            "lt": "Nedelsiant ieškokite prieglobsčio. Venkite atvirų vietų.",
        },
    )

    # Verify all fields
    assert warning.administrative_division == "Vilniaus apskritis"
    assert warning.warning_type == "thunderstorm"
    assert warning.severity == "Severe"
    assert warning.category == "weather"
    assert warning.start_time == "2026-02-10T14:00:00Z"
    assert warning.end_time == "2026-02-10T20:00:00Z"

    # Verify all translations work
    assert warning.get_description("en") == "Severe thunderstorms with hail expected"
    assert warning.get_description("lt") == "Tikėtini stiprūs perkūnijos su kruša"
    assert warning.get_instruction("en") == "Seek shelter immediately. Avoid open areas."
    assert warning.get_instruction("lt") == "Nedelsiant ieškokite prieglobsčio. Venkite atvirų vietų."

    # Verify language list
    assert set(warning.available_languages) == {"en", "lt"}
