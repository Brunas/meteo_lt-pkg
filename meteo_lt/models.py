"""Models script"""

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import List


@dataclass
class Coordinates:
    """Coordinates class"""

    latitude: float
    longitude: float


@dataclass
class Place:
    """Places"""

    code: str
    name: str
    administrative_division: str = field(
        metadata={"json_key": "administrativeDivision"}
    )
    country_code: str = field(metadata={"json_key": "countryCode"})
    coordinates: Coordinates
    county: str = field(init=False)

    @property
    def latitude(self):
        """Latitude from coordinates"""
        return self.coordinates.latitude

    @property
    def longitude(self):
        """Longitude from coordinates"""
        return self.coordinates.longitude

    def __post_init__(self):
        self.county = get_municipality_county(self.administrative_division)


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
    condition: str = field(init=False)

    def __post_init__(self):
        self.condition = map_condition(self.condition_code)


@dataclass
class Forecast:
    """Forecast"""

    place: Place
    forecast_created: str = field(metadata={"json_key": "forecastCreationTimeUtc"})
    current_conditions: ForecastTimestamp
    forecast_timestamps: List[ForecastTimestamp] = field(
        metadata={"json_key": "forecastTimestamps"}
    )

    def __post_init__(self):
        """Post-initialization processing."""

        current_hour = datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )
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


def from_dict(cls, data: dict):
    """Utility function to convert a dictionary to a dataclass instance."""
    init_args = {}
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
        elif f.name in ("datetime", "forecast_created"):
            # Convert datetime to ISO 8601 format
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
            value = dt.isoformat()

        init_args[f.name] = value
    return cls(**init_args)


Coordinates.from_dict = classmethod(from_dict)
Place.from_dict = classmethod(from_dict)
ForecastTimestamp.from_dict = classmethod(from_dict)
Forecast.from_dict = classmethod(from_dict)


def map_condition(api_condition):
    """Condition code mapping"""
    condition_mapping = {
        "clear": "sunny",
        "partly-cloudy": "partlycloudy",
        "cloudy-with-sunny-intervals": "partlycloudy",
        "cloudy": "cloudy",
        "thunder": "lightning",
        "isolated-thunderstorms": "lightning-rainy",
        "thunderstorms": "lightning-rainy",
        "heavy-rain-with-thunderstorms": "lightning-rainy",
        "light-rain": "rainy",
        "rain": "rainy",
        "heavy-rain": "pouring",
        "light-sleet": "snowy-rainy",
        "sleet": "snowy-rainy",
        "freezing-rain": "snowy-rainy",
        "hail": "hail",
        "light-snow": "snowy",
        "snow": "snowy",
        "heavy-snow": "snowy",
        "fog": "fog",
        None: "exceptional",  # For null or undefined conditions
    }

    # Default to 'exceptional' if the condition is not found in the mapping
    return condition_mapping.get(api_condition, "exceptional")


def get_municipality_county(municipality: str) -> str:
    """Return the county for a given administrative division."""
    # Define the county to administrative divisions mapping
    # https://www.infolex.lt/teise/DocumentSinglePart.aspx?AktoId=125125&StrNr=5#
    county_municipalities = {
        "Alytaus": [
            "Alytaus miesto",
            "Alytaus rajono",
            "Druskininkų",
            "Lazdijų rajono",
            "Varėnos rajono",
        ],
        "Kauno": [
            "Birštono",
            "Jonavos rajono",
            "Kaišiadorių rajono",
            "Kauno miesto",
            "Kauno rajono",
            "Kėdainių rajono",
            "Prienų rajono",
            "Raseinių rajono",
        ],
        "Klaipėdos": [
            "Klaipėdos rajono",
            "Klaipėdos miesto",
            "Kretingos rajono",
            "Neringos",
            "Palangos miesto",
            "Skuodo rajono",
            "Šilutės rajono",
        ],
        "Marijampolės": [
            "Kalvarijos",
            "Kazlų Rūdos",
            "Marijampolės",
            "Šakių rajono",
            "Vilkaviškio rajono",
        ],
        "Panevėžio": [
            "Biržų rajono",
            "Kupiškio rajono",
            "Panevėžio miesto",
            "Panevėžio rajono",
            "Pasvalio rajono",
            "Rokiškio rajono",
        ],
        "Šiaulių": [
            "Joniškio rajono",
            "Kelmės rajono",
            "Pakruojo rajono",
            "Akmenės rajono",
            "Radviliškio rajono",
            "Šiaulių miesto",
            "Šiaulių rajono",
        ],
        "Tauragės": ["Jurbarko rajono", "Pagėgių", "Šilalės rajono", "Tauragės rajono"],
        "Telšių": ["Mažeikių rajono", "Plungės rajono", "Rietavo", "Telšių rajono"],
        "Utenos": [
            "Anykščių rajono",
            "Ignalinos rajono",
            "Molėtų rajono",
            "Utenos rajono",
            "Visagino",
            "Zarasų rajono",
        ],
        "Vilniaus": [
            "Elektrėnų",
            "Šalčininkų rajono",
            "Širvintų rajono",
            "Švenčionių rajono",
            "Trakų rajono",
            "Ukmergės rajono",
            "Vilniaus miesto",
            "Vilniaus rajono",
        ],
    }
    for county, municipalities in county_municipalities.items():
        if municipality.replace(" savivaldybė", "") in municipalities:
            return f"{county} apskritis"

    return "Unknown county"
