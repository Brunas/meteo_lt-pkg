"""utils.py"""

from math import radians, sin, cos, sqrt, atan2


def haversine(lat1, lon1, lat2, lon2):
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


def find_nearest_place(latitude, longitude, places):
    """Find the nearest place from a list of places based on the given latitude and longitude."""
    nearest_place = None
    min_distance = float("inf")

    for place in places:
        place_lat = place.latitude
        place_lon = place.longitude
        distance = haversine(latitude, longitude, place_lat, place_lon)

        if distance < min_distance:
            min_distance = distance
            nearest_place = place

    return nearest_place
