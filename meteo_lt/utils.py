"""utils.py"""

from math import atan2, cos, radians, sin, sqrt


def normalize_administrative_division(name: str) -> str:
    """Normalize administrative division name to handle different formats."""
    return (
        name.lower()
        .replace(" savivaldybė", "")
        .replace(" sav.", "")
        .replace(" miesto", " m.")
        .replace(" rajono", " r.")
        .strip()
    )


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
