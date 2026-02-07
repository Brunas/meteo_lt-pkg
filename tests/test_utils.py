"""Tests for utility functions"""

import pytest

from meteo_lt.models import Coordinates, Place, find_nearest_location
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


class TestFindNearestLocation:
    """Tests for find_nearest_location function"""

    @pytest.fixture
    def lithuanian_cities(self):
        """Fixture providing three Lithuanian city Place objects"""
        return [
            Place(
                code="vilnius",
                name="Vilnius",
                coordinates=Coordinates(latitude=54.6872, longitude=25.2797),
                administrative_division="Vilnius",
                country_code="LT",
            ),
            Place(
                code="kaunas",
                name="Kaunas",
                coordinates=Coordinates(latitude=54.8985, longitude=23.9036),
                administrative_division="Kaunas",
                country_code="LT",
            ),
            Place(
                code="klaipeda",
                name="Klaipėda",
                coordinates=Coordinates(latitude=55.7033, longitude=21.1443),
                administrative_division="Klaipėda",
                country_code="LT",
            ),
        ]

    def test_single_location(self):
        """Test with single location in list"""
        location = Place(
            code="test",
            name="Test",
            coordinates=Coordinates(latitude=54.6872, longitude=25.2797),
            administrative_division="Vilnius",
            country_code="LT",
        )
        nearest = find_nearest_location(54.7, 25.3, [location])
        assert nearest == location

    @pytest.mark.parametrize(
        "query_lat,query_lon,expected_code",
        [
            (54.7, 25.3, "vilnius"),  # Point closer to Vilnius
            (54.9, 23.9, "kaunas"),  # Point closer to Kaunas
            (55.7, 21.2, "klaipeda"),  # Point closer to Klaipėda
        ],
    )
    def test_finds_closest_location(self, lithuanian_cities, query_lat, query_lon, expected_code):
        """Test that function finds the closest location"""
        nearest = find_nearest_location(query_lat, query_lon, lithuanian_cities)
        assert nearest.code == expected_code

    def test_exact_match(self):
        """Test with coordinates exactly matching a location"""
        location1 = Place(
            code="loc1",
            name="Location 1",
            coordinates=Coordinates(latitude=54.0, longitude=25.0),
            administrative_division="Test1",
            country_code="LT",
        )
        location2 = Place(
            code="loc2",
            name="Location 2",
            coordinates=Coordinates(latitude=55.0, longitude=26.0),
            administrative_division="Test2",
            country_code="LT",
        )

        nearest = find_nearest_location(54.0, 25.0, [location1, location2])
        assert nearest == location1

    def test_multiple_locations_different_distances(self):
        """Test with multiple locations at varying distances"""
        locations = [
            Place(
                code=f"loc{i}",
                name=f"Location {i}",
                coordinates=Coordinates(latitude=54.0 + i * 0.5, longitude=25.0 + i * 0.5),
                administrative_division=f"Test{i}",
                country_code="LT",
            )
            for i in range(5)
        ]

        # Query point closest to location index 2
        nearest = find_nearest_location(55.0, 26.0, locations)
        assert nearest.code == "loc2"

    def test_order_independence(self):
        """Test that order of locations in list doesn't affect result"""
        loc1 = Place(
            code="loc1",
            name="Location 1",
            coordinates=Coordinates(latitude=54.0, longitude=25.0),
            administrative_division="Test1",
            country_code="LT",
        )
        loc2 = Place(
            code="loc2",
            name="Location 2",
            coordinates=Coordinates(latitude=55.0, longitude=26.0),
            administrative_division="Test2",
            country_code="LT",
        )

        nearest1 = find_nearest_location(54.1, 25.1, [loc1, loc2])
        nearest2 = find_nearest_location(54.1, 25.1, [loc2, loc1])
        assert nearest1 == nearest2 == loc1
