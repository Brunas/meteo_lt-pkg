# Meteo.Lt Lithuanian weather forecast package

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<a href="https://buymeacoffee.com/pdfdc52z8h" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

MeteoLt-Pkg is a Python library designed to fetch weather data from [`api.meteo.lt`](https://api.meteo.lt/). This library provides convenient methods to interact with the API and obtain weather forecasts and related data. Please visit for more information.

## Installation

You can install the package using pip:

```bash
pip install meteo_lt-pkg
```

## Usage

Initializing the API Client
To start using the library, you need to initialize the `MeteoLtAPI` client:

```python
from meteo_lt import MeteoLtAPI

api_client = MeteoLtAPI()
```

### Fetching Places

To get the list of available places:

```python
import asyncio

async def fetch_places():
    await api_client.fetch_places()
    for place in api_client.places:
        print(place)

asyncio.run(fetch_places())
```

### Getting the Nearest Place

You can find the nearest place using latitude and longitude coordinates:

```python
async def find_nearest_place(latitude, longitude):
    nearest_place = await api_client.get_nearest_place(latitude, longitude)
    print(f"Nearest place: {nearest_place.name}")
 
 # Example coordinates for Vilnius, Lithuania
asyncio.run(find_nearest_place(54.6872, 25.2797)) 
```

Also, if no places are retrieved before, that is done automatically in `get_nearest_place` method.

### Fetching Weather Forecast

To get the weather forecast for a specific place, use the get_forecast method with the place code:

```python
async def fetch_forecast(place_code):
    forecast = await api_client.get_forecast(place_code)
    current_conditions = forecast.current_conditions()
    print(f"Current temperature: {current_conditions.temperature}°C")

# Example place code for Vilnius, Lithuania
asyncio.run(fetch_forecast("vilnius"))  
```

## Data Models

The package includes several data models to represent the API responses:

### Coordinates

Represents geographic coordinates.

```python
from meteo_lt import Coordinates

coords = Coordinates(latitude=54.6872, longitude=25.2797)
print(coords)
```

### Place

Represents a place with associated metadata.

```python
from meteo_lt import Place

place = Place(code="vilnius", name="Vilnius", administrative_division="Vilnius City Municipality", country="LT", coordinates=coords)
print(place.latitude, place.longitude)
```

### ForecastTimestamp

Represents a timestamp within the weather forecast, including various weather parameters.

```python
from meteo_lt import ForecastTimestamp

forecast_timestamp = ForecastTimestamp(
    datetime="2024-07-23T12:00:00Z",
    temperature=25.5,
    apparent_temperature=27.0,
    condition_code="clear",
    wind_speed=5.0,
    wind_gust_speed=8.0,
    wind_bearing=180,
    cloud_coverage=20,
    pressure=1012,
    humidity=60,
    precipitation=0
)
print(forecast_timestamp.condition)
```

### Forecast

Represents the weather forecast for a place, containing multiple forecast timestamps.

```python
from meteo_lt import Forecast

forecast = Forecast(
    place=place,
    forecast_timestamps=[forecast_timestamp]
)
print(forecast.current_conditions().temperature)
```

## Contributing

Contributions are welcome! For major changes please open an issue to discuss or submit a pull request with your changes. If you want to contribute you can use devcontainers in vscode for easiest setup follow [instructions here](.devcontainer/README.md).

***

[commits-shield]: https://img.shields.io/github/commit-activity/y/Brunas/meteo_lt-pkg.svg?style=flat-square
[commits]: https://github.com/Brunas/meteo_lt-pkg/commits/main
[license-shield]: https://img.shields.io/github/license/Brunas/meteo_lt-pkg.svg?style=flat-square
[maintenance-shield]: https://img.shields.io/badge/maintainer-Brunas%20%40Brunas-blue.svg?style=flat-square
[releases-shield]: https://img.shields.io/github/release/Brunas/meteo_lt-pkg.svg?style=flat-square
[releases]: https://github.com/Brunas/meteo_lt-pkg/releases