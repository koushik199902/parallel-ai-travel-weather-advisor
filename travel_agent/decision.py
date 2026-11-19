"""Transparent deterministic scoring. This is a demo heuristic, not a meteorological index."""
from datetime import datetime
from .weather import india_date

CITIES = ("Bengaluru", "Chennai", "Hyderabad", "Mumbai")
ALIASES = {"bangalore": "Bengaluru", "bengaluru": "Bengaluru", "chennai": "Chennai",
           "hyderabad": "Hyderabad", "mumbai": "Mumbai"}


def plan_request(question: str):
    text = question.lower()
    cities = [city for city in CITIES if any(alias in text for alias, target in ALIASES.items() if target == city)]
    if not cities:
        cities = list(CITIES) if "four" in text or "all" in text else []
    if not cities:
        raise ValueError("Name at least one of: Bengaluru, Chennai, Hyderabad, Mumbai")
    if "tomorrow" in text:
        target = india_date(1)
    elif "today" in text:
        target = india_date(0)
    else:
        raise ValueError("Specify today or tomorrow")
    return {"cities": cities, "date": target, "intent": "outdoor weather comparison"}


def score_weather(data: dict):
    """100-point demo suitability scale: rain 45, temp 35, wind 20."""
    rain = max(0.0, min(100.0, float(data["rain_probability_max_pct"])))
    temp = float(data["temperature_max_c"])
    wind = max(0.0, float(data["wind_speed_max_kmh"]))
    rain_points = 45 * (1 - rain / 100)
    temp_points = 35 * max(0, 1 - abs(temp - 25) / 15)
    wind_points = 20 * max(0, 1 - wind / 45)
    return {"city": data["city"], "score": round(rain_points + temp_points + wind_points, 2),
            "rain_points": round(rain_points, 2), "temperature_points": round(temp_points, 2),
            "wind_points": round(wind_points, 2)}


def rank_results(weather_results: list[dict]):
    scores = [score_weather(x["data"]) for x in weather_results if x.get("status") == "ok"]
    return sorted(scores, key=lambda x: (-x["score"], x["city"]))
