"""Tests for multilingual warning support"""

from meteo_lt.models import MeteoWarning


def test_meteo_warning_multilingual_properties():
    """Test MeteoWarning with multilingual translations"""
    warning = MeteoWarning(
        administrative_division="Vilniaus miesto sav.",
        warning_type="wind",
        severity="Moderate",
        category="weather",
        start_time="2026-02-10T12:00:00Z",
        end_time="2026-02-10T18:00:00Z",
        description={
            "en": "Strong wind expected",
            "lt": "Tikėtinas stiprus vėjas",
        },
        instruction={
            "en": "Secure loose objects",
            "lt": "Pritvirtinkite laisvus daiktus",
        },
    )

    # Test translation dictionaries
    assert warning.description["en"] == "Strong wind expected"
    assert warning.description["lt"] == "Tikėtinas stiprus vėjas"
    assert warning.instruction["en"] == "Secure loose objects"
    assert warning.instruction["lt"] == "Pritvirtinkite laisvus daiktus"


def test_meteo_warning_partial_translations():
    """Test warning with only description translations"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="rain",
        severity="Minor",
        category="weather",
        description={"en": "Rain expected", "lt": "Tikėtinas lietus"},
    )

    # Check description translations exist
    assert warning.description["en"] == "Rain expected"
    assert warning.description["lt"] == "Tikėtinas lietus"

    # Check instruction is None
    assert warning.instruction is None


def test_meteo_warning_no_translations():
    """Test warning without any translations"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="snow",
        severity="Severe",
        category="weather",
    )

    # Should work without translations
    assert warning.description is None
    assert warning.instruction is None


def test_meteo_warning_instruction_only_translations():
    """Test warning with only instruction translations"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="storm",
        severity="Extreme",
        category="weather",
        instruction={
            "en": "Seek shelter immediately",
            "lt": "Nedelsiant ieškokite prieglobsčio",
        },
    )

    assert warning.description is None
    assert warning.instruction["en"] == "Seek shelter immediately"
    assert warning.instruction["lt"] == "Nedelsiant ieškokite prieglobsčio"


def test_meteo_warning_empty_strings_filtered():
    """Test that empty strings are filtered in translations"""
    # Empty strings should be filtered by the warnings processor,
    # but if they exist in the model, they're preserved
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="fog",
        severity="Moderate",
        category="weather",
        description={
            "en": "Dense fog expected",
            "lt": "",  # Empty string present
        },
    )

    # Empty string is present (not filtered at model level)
    assert "lt" in warning.description
    assert warning.description["lt"] == ""


def test_meteo_warning_all_fields():
    """Test warning with all fields populated"""
    warning = MeteoWarning(
        administrative_division="Vilniaus apskritis",
        warning_type="thunderstorm",
        severity="Severe",
        category="weather",
        start_time="2026-02-10T14:00:00Z",
        end_time="2026-02-10T20:00:00Z",
        description={
            "en": "Severe thunderstorms with hail expected",
            "lt": "Tikėtini stiprūs perkūnijos su kruša",
        },
        instruction={
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

    # Verify all translations
    assert warning.description["en"] == "Severe thunderstorms with hail expected"
    assert warning.description["lt"] == "Tikėtini stiprūs perkūnijos su kruša"
    assert warning.instruction["en"] == "Seek shelter immediately. Avoid open areas."
    assert warning.instruction["lt"] == "Nedelsiant ieškokite prieglobsčio. Venkite atvirų vietų."


def test_get_description_method():
    """Test get_description convenience method with language fallback"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="wind",
        severity="Moderate",
        category="weather",
        description={
            "en": "Strong wind expected",
            "lt": "Tikėtinas stiprus vėjas",
        },
    )

    # Get specific language
    assert warning.get_description("en") == "Strong wind expected"
    assert warning.get_description("lt") == "Tikėtinas stiprus vėjas"

    # Default to English when no language specified
    assert warning.get_description() == "Strong wind expected"

    # Fallback to English when requested language not available
    assert warning.get_description("fr") == "Strong wind expected"
    assert warning.get_description("de") == "Strong wind expected"


def test_get_instruction_method():
    """Test get_instruction convenience method with language fallback"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="storm",
        severity="Extreme",
        category="weather",
        instruction={
            "en": "Seek shelter immediately",
            "lt": "Nedelsiant ieškokite prieglobsčio",
        },
    )

    # Get specific language
    assert warning.get_instruction("en") == "Seek shelter immediately"
    assert warning.get_instruction("lt") == "Nedelsiant ieškokite prieglobsčio"

    # Default to English when no language specified
    assert warning.get_instruction() == "Seek shelter immediately"

    # Fallback to English when requested language not available
    assert warning.get_instruction("fr") == "Seek shelter immediately"
    assert warning.get_instruction("de") == "Seek shelter immediately"


def test_get_methods_with_none_values():
    """Test get methods when description/instruction are None"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="fog",
        severity="Minor",
        category="weather",
    )

    # Should return None when fields are None
    assert warning.get_description() is None
    assert warning.get_description("en") is None
    assert warning.get_description("lt") is None
    assert warning.get_instruction() is None
    assert warning.get_instruction("en") is None
    assert warning.get_instruction("lt") is None


def test_get_methods_with_missing_english():
    """Test fallback behavior when English translation is missing"""
    warning = MeteoWarning(
        administrative_division="Test area",
        warning_type="rain",
        severity="Minor",
        category="weather",
        description={
            "lt": "Tikėtinas lietus",
            "ru": "Ожидается дождь",
        },
        instruction={
            "lt": "Būkite atsargūs",
        },
    )

    # When English is not available, fallback returns None (no English to fall back to)
    assert warning.get_description("en") is None
    assert warning.get_instruction("en") is None

    # But Lithuanian is available
    assert warning.get_description("lt") == "Tikėtinas lietus"
    assert warning.get_instruction("lt") == "Būkite atsargūs"

    # Default call (no param) tries English first, gets None if not available
    assert warning.get_description() is None
    assert warning.get_instruction() is None

    # Other languages that don't exist also return None (no English to fall back to)
    assert warning.get_description("fr") is None
    assert warning.get_instruction("de") is None
