## Release 0.7.3

Date: `2026-07-12`

### Bug Fixes

- **Per-request timeout on every request** so the configured `30s` timeout applies with an injected `aiohttp` session, not only library-created ones
  - Previously `ClientTimeout(total=30)` was only set on sessions the client created itself, so an externally injected session (e.g. Home Assistant's shared session) would fall back to aiohttp's ~5 minute default, letting a stalled request block setup for minutes
  - Every fetch method now passes `timeout=aiohttp.ClientTimeout(total=TIMEOUT)` on each request
- **Non-2xx hydro responses now raise instead of returning `None`**: removed the dead `if status == 200` branch in the hydro methods (unreachable after `raise_for_status()`); a `2xx`-non-`200` response no longer falls through silently

### Changes

- **Consistent response encoding**: the second warnings request and hydro observation request now set `response.encoding = "utf-8"` like the other requests, so Lithuanian characters decode correctly

## Release 0.7.2

Date: `2026-07-11`

### Bug Fixes

- **Raise for HTTP status per request** so error handling works with an injected `aiohttp` session, not only library-created ones
  - Previously `raise_for_status=True` was only set on sessions the client created itself, so an externally injected session (e.g. Home Assistant's shared session) would parse 4xx/5xx bodies as payloads instead of raising `aiohttp.ClientError`
  - Each fetch method now calls `response.raise_for_status()` on every request

### Maintenance

- Added Python 3.14 to the CI test matrix and bumped the devcontainer base image to `python:3.14-bookworm`

## Release 0.7.1

Date: `2026-02-10`

### New Features

- **Added `headline` field to `MeteoWarning`**: Warnings now include multilingual headline/title text from the API
  - Access via `warning.headline` dictionary: `{"en": "...", "lt": "..."}`
  - Use `warning.get_headline(language="en")` method with automatic fallback to English
  - Example: `"Dangerous freezing rain/drizzle alert for Alytus county"`

## Release 0.7.0

Date: `2026-02-10`

### Breaking Changes

- **`MeteoWarning.description` and `MeteoWarning.instruction` are now dictionaries** containing translations by language code instead of plain strings
  - Old approach: `warning.description` returned a string
  - New approach: `warning.description` returns `Dict[str, str]` like `{"en": "Strong wind", "lt": "Stiprus vėjas"}`
  - Use `warning.get_description(language="en")` to get translated text with automatic fallback to English
  - Use `warning.get_instruction(language="lt")` for instructions with automatic fallback to English
  - Direct dictionary access: `warning.description["lt"]` for Lithuanian text
  - Backward compatibility is handled in the Home Assistant integration

## Release 0.6.2

Date: `2026-02-08`

### Changes

- **Fixed warnings categorization bug**: Weather warnings were incorrectly appearing with `category='hydro'` due to duplicate data in API endpoints
- **Optimized API calls**: Eliminated duplicate warnings fetch (both WEATHER_URL and HYDRO_URL returned identical data)
- **Simplified architecture**: Unified warnings processor - replaced dual processor instances with single processor using method-level category filtering
- Optimized tests

## Release 0.6.1

Date: `2026-02-07`

### Changes

- **Renamed `MeteoWarning.county` field to `administrative_division`** to properly represent both counties (apskritis) for weather warnings and municipalities (savivaldybė) for hydrological warnings
- **Fixed warning area matching** with simple name normalization to handle all scenarios

## Release 0.6.0

Date: `2026-02-06`

### Breaking Changes

- **Minimum Python version bumped from 3.10 to 3.11**

### Bug Fixes

- **Fixed warning enrichment**: Forecast timestamps now properly treated as hourly periods instead of exact points in time
  - A warning active from 23:30 to 11:00 will now correctly apply to all overlapping hourly forecasts
  - Fixed edge cases where warnings starting or ending mid-hour were not matched
- Warnings are **included by default** again in `get_forecast()` calls (was `include_warnings=False`, now `include_warnings=True`)

## Release 0.5.3

Date: `2026-02-06`

### Changes

- Separate `MeteoWarning.instruction` which earlier was appended to the  `MeteoWarning.description`
- Unit test optimization

## Release 0.5.2

Date: `2026-02-05`

### Changes

- Hydro warnings implemented to extend weather warnings

## Release 0.5.1

Date: `2026-01-29`

### Changes

- Hydro observations implemented
- Python code clean-up

## Release 0.5.0

Date: `2026-01-29`

### Changes

- Usual version bumps

## Release 0.4.0

Date: `2025-10-03`

### Changes

- Major code refactoring for weather warnings using [this](https://www.meteo.lt/prognozes/pavojingi-reiskiniai/) and county mapping [here](https://www.infolex.lt/teise/DocumentSinglePart.aspx?AktoId=125125&StrNr=5#)
- Removed not existant country from places, country_code added instead
- websession injection (thanks to [Nojus](https://github.com/xE1H))

## Release 0.3.0

Date: `2025-09-29`

### Changes

- Removed home assistant specific conditions mapping (to be implemented in HASS integration)

## Release 0.2.2

Date: `2024-07-28`

### Changes

- Current hour forecast is current conditions
- Filtering past hours forecasts out - API doesn't do that automatically
- Added forecast_created using forecastCreationTimestampUtc

## Release 0.2.1

Date: `2024-07-28`

### Changes

- Datetime UTC format changed from 'YYYY-MM-DDTHH:mm:SSZ' to 'YYYY-MM-DDTHH:mm:SS+00:00'

## Release 0.2.0

Date: `2024-07-26`

### Changes

- Removed `scipy` and `numpy` in favour of local Haversine method implementation

## Release 0.1.x

Date: `2024-07-26`

### Changes

- Initial version of api.meteo.lt wrapper using `scipy` and `numpy`
