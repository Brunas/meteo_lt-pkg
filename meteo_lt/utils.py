"""utils.py"""

from math import radians, sin, cos, sqrt, atan2
from typing import TypeVar, List

LocationT = TypeVar("LocationT")  # Type variable for location objects with latitude/longitude


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth's surface."""
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6371  # Radius of Earth in kilometers
    return r * c


def find_nearest_location(latitude: float, longitude: float, locations: List[LocationT]) -> LocationT:
    """Find the nearest location from a list of locations based on the given latitude and longitude."""
    nearest_location = None
    min_distance = float("inf")

    for location in locations:
        location_lat = location.latitude
        location_lon = location.longitude
        distance = haversine(latitude, longitude, location_lat, location_lon)

        if distance < min_distance:
            min_distance = distance
            nearest_location = location

    return nearest_location
