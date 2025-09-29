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
