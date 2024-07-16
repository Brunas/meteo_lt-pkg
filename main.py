import asyncio
from meteo_lt.api import MeteoLtAPI

async def main():
    meteo_lt = MeteoLtAPI()
    await meteo_lt.fetch_places()
    nearest_place = await meteo_lt.get_nearest_place(54.6872, 25.2797)
    forecast = await meteo_lt.get_forecast(nearest_place.code)
    current_conditions = forecast.current_conditions()
    print(f"HASS Condition: {current_conditions}")

if __name__ == "__main__":
    asyncio.run(main())
