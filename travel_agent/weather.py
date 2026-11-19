"""Open-Meteo weather integration. The tool does not invent measurements."""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import httpx

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
SUPPORTED = {"Bengaluru": (12.97, 77.59), "Chennai": (13.08, 80.27),
             "Hyderabad": (17.39, 78.49), "Mumbai": (19.08, 72.88)}


def india_date(offset=1):
    return (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(days=offset)).date().isoformat()


def simulated_weather(city, date):
    """Clearly fictional deterministic data for offline workflow testing only."""
    samples = {
        "Bengaluru": (27, 25, 15, 0.3), "Chennai": (34, 55, 24, 2.1),
        "Hyderabad": (31, 15, 18, 0.1), "Mumbai": (30, 70, 29, 5.2),
    }
    t, rain, wind, mm = samples[city]
    return {"city": city, "date": date, "temperature_max_c": t,
            "temperature_min_c": t - 7, "rain_probability_max_pct": rain,
            "wind_speed_max_kmh": wind, "precipitation_sum_mm": mm,
            "source": "SIMULATED DEMO DATA — NOT LIVE WEATHER"}


async def get_city_weather(city: str, date: str) -> dict:
    if city not in SUPPORTED:
        raise ValueError(f"Unsupported city: {city}")
    if date not in {india_date(0), india_date(1)}:
        raise ValueError("Only today's and tomorrow's India-local forecasts are supported")
    if os.getenv("WEATHER_MCP_TEST_MODE") == "1":
        return simulated_weather(city, date)
    # Fixed known-city coordinates remove ambiguous geocoding matches. No need for a geocoding call.
    latitude, longitude = SUPPORTED[city]
    params = {
        "latitude": latitude, "longitude": longitude,
        "timezone": "Asia/Kolkata", "forecast_days": 3,
        "daily": ",".join(["temperature_2m_max", "temperature_2m_min",
                           "precipitation_probability_max", "wind_speed_10m_max",
                           "precipitation_sum"]),
    }
    async with httpx.AsyncClient(timeout=18.0) as client:
        response = await client.get(FORECAST, params=params)
        response.raise_for_status()
        body = response.json()
    daily = body.get("daily") or {}
    dates = daily.get("time") or []
    if date not in dates:
        raise RuntimeError(f"Forecast does not include {date}")
    i = dates.index(date)
    keys = {"temperature_max_c": "temperature_2m_max",
            "temperature_min_c": "temperature_2m_min",
            "rain_probability_max_pct": "precipitation_probability_max",
            "wind_speed_max_kmh": "wind_speed_10m_max",
            "precipitation_sum_mm": "precipitation_sum"}
    output = {"city": city, "date": date, "source": "Open-Meteo Forecast API"}
    for field, key in keys.items():
        values = daily.get(key)
        if not isinstance(values, list) or len(values) <= i or values[i] is None:
            raise RuntimeError(f"Missing required forecast field: {key}")
        output[field] = float(values[i])
    return output
