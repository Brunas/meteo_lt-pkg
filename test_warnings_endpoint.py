"""Script to test the warnings endpoint and show what data comes from the URL"""

import asyncio
import json

from meteo_lt import MeteoLtAPI


async def test_warnings_endpoint():
    """Test the warnings endpoint and display the raw data"""

    async with MeteoLtAPI() as api:
        print("=" * 80)
        print("WARNINGS ENDPOINT TEST")
        print("=" * 80)
        print(
            f"URL: {api.warnings_processor.client._session._base_url if hasattr(api.warnings_processor.client._session, '_base_url') else 'https://www.meteo.lt/app/mu-plugins/Meteo/Components/WeatherWarningsNew/list_JSON.php'}"
        )
        print()

        # Fetch raw warnings data
        from meteo_lt.const import WARNINGS_URL

        print(f"Fetching from: {WARNINGS_URL}")
        print()

        # Get warnings using the client
        warnings_data = await api.warnings_processor.client.fetch_warnings(WARNINGS_URL)

        print("=" * 80)
        print("RAW DATA STRUCTURE:")
        print("=" * 80)
        print(json.dumps(warnings_data, indent=2, ensure_ascii=False))
        print()

        # Get processed warnings
        print("=" * 80)
        print("PROCESSED WARNINGS (ALL):")
        print("=" * 80)
        all_warnings = await api.warnings_processor.get_all_warnings()
        print(f"Total warnings found: {len(all_warnings)}")
        print()

        for i, warning in enumerate(all_warnings, 1):
            print(f"\n--- Warning {i} ---")
            print(f"Category: {warning.category}")
            print(f"Warning Type: {warning.warning_type}")
            print(f"Severity: {warning.severity}")
            print(f"Area: {warning.administrative_division}")
            desc = warning.get_description("lt") if warning.description else "N/A"
            print(f"Description (LT): {desc[:100] if desc != 'N/A' else 'N/A'}...")
            print(f"Start: {warning.start_time}")
            print(f"End: {warning.end_time}")

        print()
        print("=" * 80)
        print("WEATHER WARNINGS ONLY:")
        print("=" * 80)
        weather_warnings = await api.warnings_processor.get_weather_warnings()
        print(f"Weather warnings: {len(weather_warnings)}")

        print()
        print("=" * 80)
        print("HYDRO WARNINGS ONLY:")
        print("=" * 80)
        hydro_warnings = await api.warnings_processor.get_hydro_warnings()
        print(f"Hydrological warnings: {len(hydro_warnings)}")


if __name__ == "__main__":
    asyncio.run(test_warnings_endpoint())
