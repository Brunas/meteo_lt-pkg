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

## Quick Start

Here's a quick example to get you started:

```python
import asyncio
from meteo_lt import MeteoLtAPI

async def quick_example():
    async with MeteoLtAPI() as api:
        # Get current weather for Vilnius
        forecast = await api.get_forecast("vilnius")
        current = forecast.current_conditions

        print(f"Current temperature in Vilnius: {current.temperature}°C")
        print(f"Condition: {current.condition_code}")
        print(f"Wind: {current.wind_speed} m/s")

        # Check for weather warnings
        warnings = await api.get_weather_warnings("Vilniaus miesto")
        if warnings:
            print(f"Active warnings: {len(warnings)}")
            for warning in warnings:
                print(f"   - {warning.warning_type}: {warning.severity}")
        else:
            print("No active weather warnings")

asyncio.run(quick_example())
```

## Usage

### Basic Usage (Recommended)

The recommended way to use the library is with the `async with` context manager, which ensures proper cleanup of HTTP sessions:

```python
import asyncio
from meteo_lt import MeteoLtAPI

async def main():
    async with MeteoLtAPI() as api:
        # Get weather forecast for Vilnius
        forecast = await api.get_forecast("vilnius")
        print(f"Current temperature in {forecast.place.name}: {forecast.current_conditions.temperature}°C")

        # Get weather warnings for Vilnius
        warnings = await api.get_weather_warnings("Vilniaus miesto")
        print(f"Active warnings: {len(warnings)}")
        for warning in warnings:
            print(f"- {warning.warning_type}: {warning.description}")

asyncio.run(main())
```

### Alternative Usage

If you prefer not to use the context manager, make sure to call `close()` to properly cleanup resources:

```python
async def alternative_usage():
    api = MeteoLtAPI()
    try:
        forecast = await api.get_forecast("kaunas")
        print(f"Temperature: {forecast.current_conditions.temperature}°C")
    finally:
        await api.close()  # Important: prevents session warnings

asyncio.run(alternative_usage())
```

### Fetching Places

To get the list of available places:

```python
async def fetch_places():
    async with MeteoLtAPI() as api:
        await api.fetch_places()
        for place in api.places:
            print(f"{place.name} ({place.code})")

asyncio.run(fetch_places())
```

### Getting the Nearest Place

You can find the nearest place using latitude and longitude coordinates:

```python
async def find_nearest_place():
    async with MeteoLtAPI() as api:
        # Example coordinates for Vilnius, Lithuania
        nearest_place = await api.get_nearest_place(54.6872, 25.2797)
        print(f"Nearest place: {nearest_place.name}")

asyncio.run(find_nearest_place())
```

> **NOTE**: If no places are retrieved before, that is done automatically in `get_nearest_place` method.

### Fetching Weather Forecast

To get the weather forecast for a specific place:

```python
async def fetch_forecast():
    async with MeteoLtAPI() as api:
        # Get forecast for Vilnius
        forecast = await api.get_forecast("vilnius")

        # Current conditions
        current = forecast.current_conditions
        print(f"Current temperature: {current.temperature}°C")
        print(f"Feels like: {current.apparent_temperature}°C")
        print(f"Condition: {current.condition_code}")

        # Future forecasts
        print(f"\nNext 24 hours:")
        for timestamp in forecast.forecast_timestamps[:24]:
            print(f"{timestamp.datetime}: {timestamp.temperature}°C")

asyncio.run(fetch_forecast())
```

> **NOTE**: `current_conditions` is the current hour record from the `forecast_timestamps` array. Also, `forecast_timestamps` array has past time records filtered out due to `api.meteo.lt` not doing that automatically.

### Fetching Weather Forecast with Warnings

To get weather forecast enriched with warnings:

```python
async def fetch_forecast_with_warnings():
    async with MeteoLtAPI() as api:
        # Get forecast with warnings using coordinates
        forecast = await api.get_forecast_with_warnings(
            latitude=54.6872,
            longitude=25.2797
        )

        print(f"Forecast for {forecast.place.name}")
        print(f"Current temperature: {forecast.current_conditions.temperature}°C")

        # Check for warnings in current conditions
        if forecast.current_conditions.warnings:
            print("Current warnings:")
            for warning in forecast.current_conditions.warnings:
                print(f"- {warning.warning_type}: {warning.severity}")

asyncio.run(fetch_forecast_with_warnings())
```

### Fetching Weather Warnings

To get weather warnings for Lithuania or specific administrative areas:

```python
async def fetch_warnings():
    async with MeteoLtAPI() as api:
        # Get all weather warnings
        warnings = await api.get_weather_warnings()
        print(f"Total active warnings: {len(warnings)}")

        for warning in warnings:
            print(f"Warning: {warning.warning_type} in {warning.county}")
            print(f"Severity: {warning.severity}")
            print(f"Description: {warning.description}")
            print(f"Active: {warning.start_time} to {warning.end_time}")
            print("-" * 50)

async def fetch_warnings_for_area():
    async with MeteoLtAPI() as api:
        # Get warnings for specific administrative division
        vilnius_warnings = await api.get_weather_warnings("Vilniaus miesto")
        print(f"Warnings for Vilnius: {len(vilnius_warnings)}")

        for warning in vilnius_warnings:
            print(f"- {warning.warning_type} ({warning.severity})")

asyncio.run(fetch_warnings())
asyncio.run(fetch_warnings_for_area())
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
    datetime="2024-07-23T12:00:00+00:00",
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
    forecast_created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    forecast_timestamps=[forecast_timestamp]
)
print(forecast.current_conditions().temperature)
```

### WeatherWarning

Represents a weather warning for a specific area.

```python
from meteo_lt import WeatherWarning

warning = WeatherWarning(
    county="Vilniaus apskritis",
    warning_type="frost",
    severity="Moderate",
    description="Ground surface frost 0-5 degrees in many places",
    start_time="2024-07-23T12:00:00Z",
    end_time="2024-07-23T18:00:00Z"
)
print(f"Warning for {warning.county}: {warning.description}")
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