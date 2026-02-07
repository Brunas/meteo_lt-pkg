"""Tests for utility functions"""

import pytest

from meteo_lt.utils import haversine, normalize_administrative_division


class TestNormalizeAdministrativeDivision:
    """Tests for normalize_administrative_division function"""

    @pytest.mark.parametrize(
        "input_name,expected",
        [
            ("Vilniaus miesto savivaldybė", "vilniaus m."),
            ("Birštono savivaldybė", "birštono"),
            ("MARIJAMPOLĖS SAVIVALDYBĖ", "marijampolės"),
            ("Kauno m. sav.", "kauno m."),
            ("Klaipėdos r. sav.", "klaipėdos r."),
            ("Vilniaus miesto", "vilniaus m."),
            ("Šiaulių miesto", "šiaulių m."),
            ("Kauno rajono", "kauno r."),
            ("Alytaus rajono", "alytaus r."),
            ("Panevėžio rajono savivaldybė", "panevėžio r."),
            ("  Vilniaus miesto  ", "vilniaus m."),
            ("  Plungės rajono  ", "plungės r."),
            ("\tKauno m. sav.\t", "kauno m."),
            ("vilniaus m.", "vilniaus m."),
            ("kauno r.", "kauno r."),
            ("Vilniaus apskritis", "vilniaus apskritis"),
            ("Kauno Apskritis", "kauno apskritis"),
        ],
    )
    def test_normalization(self, input_name, expected):
        """Test normalization with various input formats"""
        assert normalize_administrative_division(input_name) == expected

    def test_idempotent(self):
        """Test that applying normalization twice produces same result"""
        input_name = "Vilniaus miesto savivaldybė"
        normalized_once = normalize_administrative_division(input_name)
        normalized_twice = normalize_administrative_division(normalized_once)
        assert normalized_once == normalized_twice

    def test_empty_string(self):
        """Test handling of empty string"""
        assert normalize_administrative_division("") == ""

    def test_preserves_municipality_names(self):
        """Test that simple municipality names without qualifiers are preserved"""
        assert normalize_administrative_division("Birštonas") == "birštonas"
        assert normalize_administrative_division("Druskininkai") == "druskininkai"
        assert normalize_administrative_division("Palanga") == "palanga"


class TestHaversine:
    """Tests for haversine distance calculation function"""

    @pytest.mark.parametrize(
        "lat1,lon1,lat2,lon2,min_km,max_km,description",
        [
            # Same point
            (54.6872, 25.2797, 54.6872, 25.2797, 0, 0, "same point"),
            # Lithuanian cities
            (54.6872, 25.2797, 54.8985, 23.9036, 90, 94, "Vilnius to Kaunas"),
            (54.6872, 25.2797, 55.7033, 21.1443, 284, 288, "Vilnius to Klaipėda"),
            # International
            (40.7128, -74.0060, 51.5074, -0.1278, 5550, 5600, "New York to London"),
            # Antipodal points (opposite sides)
            (0, 0, 0, 180, 19900, 20100, "antipodal points"),
            # Equator distance (1 degree ≈ 111 km)
            (0, 0, 0, 1, 110, 112, "1 degree on equator"),
        ],
    )
    def test_distance_calculations(self, lat1, lon1, lat2, lon2, min_km, max_km, description):
        """Test distance calculations between various points"""
        distance = haversine(lat1, lon1, lat2, lon2)
        assert min_km <= distance <= max_km, f"Failed for {description}: {distance} not in [{min_km}, {max_km}]"

    def test_symmetry(self):
        """Test that distance from A to B equals distance from B to A"""
        lat1, lon1 = 54.6872, 25.2797
        lat2, lon2 = 54.8985, 23.9036
        distance_ab = haversine(lat1, lon1, lat2, lon2)
        distance_ba = haversine(lat2, lon2, lat1, lon1)
        assert distance_ab == distance_ba
