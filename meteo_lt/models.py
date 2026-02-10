"""Models script"""

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from .const import COUNTY_MUNICIPALITIES
from .utils import haversine, normalize_administrative_division


@dataclass
class Coordinates:
    """Coordinates class"""

    latitude: float
    longitude: float


@dataclass
class LocationBase:
    """Base class for locations with coordinates"""

    code: str
    name: str
    coordinates: Coordinates

    @property
    def latitude(self):
        """Latitude from coordinates"""
        return self.coordinates.latitude

    @property
    def longitude(self):
        """Longitude from coordinates"""
        return self.coordinates.longitude


@dataclass
class Place(LocationBase):
    """Places"""

    administrative_division: str = field(metadata={"json_key": "administrativeDivision"})
    country_code: str = field(metadata={"json_key": "countryCode"})
    counties: List[str] = field(init=False)

    def __post_init__(self):
        self.counties = []
        normalized_division = normalize_administrative_division(self.administrative_division)
        for county, municipalities in COUNTY_MUNICIPALITIES.items():
            normalized_municipalities = [normalize_administrative_division(m) for m in municipalities]
            if normalized_division in normalized_municipalities:
                self.counties.append(county)


def find_nearest_location(latitude: float, longitude: float, locations: List[LocationBase]) -> LocationBase:
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


@dataclass
class MeteoWarning:
    """Meteorological Warning (includes both weather and hydrological warnings)"""

    administrative_division: str
    warning_type: str
    severity: str
    headline: Optional[Dict[str, str]] = None  # {"lt": "...", "en": "..."}
    description: Optional[Dict[str, str]] = None  # {"lt": "...", "en": "..."}
    instruction: Optional[Dict[str, str]] = None  # {"lt": "...", "en": "..."}
    category: str = "weather"  # "weather" or "hydro"
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def get_headline(self, language: str = "en") -> Optional[str]:
        """Get headline in specified language, fallback to English if not available"""
        if not self.headline:
            return None
        return self.headline.get(language) or self.headline.get("en")

    def get_description(self, language: str = "en") -> Optional[str]:
        """Get description in specified language, fallback to English if not available"""
        if not self.description:
            return None
        return self.description.get(language) or self.description.get("en")

    def get_instruction(self, language: str = "en") -> Optional[str]:
        """Get instruction in specified language, fallback to English if not available"""
        if not self.instruction:
            return None
        return self.instruction.get(language) or self.instruction.get("en")


@dataclass
class HydroStation(LocationBase):
    """Hydrological station data."""

    water_body: str = field(metadata={"json_key": "waterBody"})


@dataclass
class HydroObservation:
    """Single hydrological observation."""

    observation_datetime: Optional[str] = field(default=None, metadata={"json_key": "observationTimeUtc"})
    water_level: Optional[float] = field(default=None, metadata={"json_key": "waterLevel"})  # cm
    water_temperature: Optional[float] = field(default=None, metadata={"json_key": "waterTemperature"})  # °C
    water_discharge: Optional[float] = field(default=None, metadata={"json_key": "waterDischarge"})  # m3/s


@dataclass
class HydroObservationData:
    """Observation data response."""

    station: HydroStation
    observations_data_range: Optional[dict] = field(default=None, metadata={"json_key": "observationsDataRange"})
    observations: List[HydroObservation] = field(default_factory=list)


@dataclass
class ForecastTimestamp:
    """ForecastTimestamp"""

    datetime: str = field(metadata={"json_key": "forecastTimeUtc"})
    temperature: float = field(metadata={"json_key": "airTemperature"})
    apparent_temperature: float = field(metadata={"json_key": "feelsLikeTemperature"})
    condition_code: str = field(metadata={"json_key": "conditionCode"})
    wind_speed: float = field(metadata={"json_key": "windSpeed"})
    wind_gust_speed: float = field(metadata={"json_key": "windGust"})
    wind_bearing: float = field(metadata={"json_key": "windDirection"})
    cloud_coverage: float = field(metadata={"json_key": "cloudCover"})
    pressure: float = field(metadata={"json_key": "seaLevelPressure"})
    humidity: float = field(metadata={"json_key": "relativeHumidity"})
    precipitation: float = field(metadata={"json_key": "totalPrecipitation"})
    warnings: List[MeteoWarning] = field(default_factory=list, init=False)


@dataclass
class Forecast:
    """Forecast"""

    place: Place
    forecast_created: str = field(metadata={"json_key": "forecastCreationTimeUtc"})
    current_conditions: ForecastTimestamp
    forecast_timestamps: List[ForecastTimestamp] = field(metadata={"json_key": "forecastTimestamps"})

    def __post_init__(self):
        """Post-initialization processing."""

        current_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        # Current conditions are equal to current hour record
        for forecast in self.forecast_timestamps:
            if (
                datetime.fromisoformat(forecast.datetime)
                .astimezone(timezone.utc)
                .replace(minute=0, second=0, microsecond=0)
            ) == current_hour:
                self.current_conditions = forecast
                break

        # Filter out timestamps that are older than current hour
        self.forecast_timestamps = [
            forecast
            for forecast in self.forecast_timestamps
            if (
                datetime.fromisoformat(forecast.datetime)
                .astimezone(timezone.utc)
                .replace(minute=0, second=0, microsecond=0)
            )
            > current_hour
        ]


def from_dict(cls: Type, data: Dict[str, Any]) -> Any:
    """Utility function to convert a dictionary to a dataclass instance."""
    init_args: Dict[str, Any] = {}
    for f in fields(cls):
        if not f.init:
            continue  # Skip fields that are not part of the constructor

        json_key = f.metadata.get("json_key", f.name)
        value = data.get(json_key)

        # Recursively convert nested dataclasses
        if isinstance(value, dict) and hasattr(f.type, "from_dict"):
            value = from_dict(f.type, value)
        elif isinstance(value, list) and hasattr(f.type.__args__[0], "from_dict"):
            value = [from_dict(f.type.__args__[0], item) for item in value]
        elif f.name in ("datetime", "forecast_created", "observation_datetime") and value:
            # Convert datetime to ISO 8601 format
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            value = dt.isoformat()

        init_args[f.name] = value
    return cls(**init_args)


Coordinates.from_dict = classmethod(from_dict)
Place.from_dict = classmethod(from_dict)
ForecastTimestamp.from_dict = classmethod(from_dict)
Forecast.from_dict = classmethod(from_dict)
MeteoWarning.from_dict = classmethod(from_dict)
HydroStation.from_dict = classmethod(from_dict)
HydroObservation.from_dict = classmethod(from_dict)
HydroObservationData.from_dict = classmethod(from_dict)
