"""
Weather tool.
Uses Nominatim (OpenStreetMap) for geocoding + Open-Meteo for weather.
Both are free and require no API key.
"""

from __future__ import annotations

import re
from typing import Optional

import requests

_TIMEOUT = 8  # seconds


def geocode(city: str) -> tuple[Optional[float], Optional[float]]:
    """Convert a city name to (latitude, longitude) using Nominatim."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "local-ai-agent/1.0"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return None, None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None, None


def get_weather(city: str) -> str:
    """Fetch current weather for a city name and return a formatted string."""
    lat, lon = geocode(city)
    if lat is None:
        return f"Sorry, I couldn't find '{city}'. Try another city name."
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "timezone": "auto",
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        cw = r.json().get("current_weather", {})
        temp = cw.get("temperature", "?")
        wind = cw.get("windspeed", "?")
        code = cw.get("weathercode", -1)
        condition = _weather_description(code)
        return (
            f"🌤 {city.title()}: {temp}°C, {condition}, wind {wind} km/h."
        )
    except Exception as e:
        return f"Weather API error: {e}"


def extract_city(text: str) -> Optional[str]:
    """
    Try to extract a city from phrases like:
    'weather in London', 'temperature of Paris', etc.
    Returns None if no pattern matches (caller should use full text as city).
    """
    patterns = [
        r"(?:weather|forecast|temperature|temp|climate|raining|hot|cold|warm)\s+(?:of|in|for|at)\s+([a-zA-Z ,]+?)(?:\?|$|\.)",
        r"(?:weather|forecast|temperature|temp)\s+([a-zA-Z ,]+?)(?:\?|$|\.)",
        r"(?:in|at|for)\s+([a-zA-Z ,]+?)(?:\?|$|\.)",
    ]
    for pat in patterns:
        m = re.search(pat, text.strip(), re.I)
        if m:
            city = m.group(1).strip()
            # Avoid matching single-word noise like "today"
            if city.lower() not in ("today", "now", "me", "the", "a"):
                return city
    return None


def _weather_description(code: int) -> str:
    """Map Open-Meteo WMO weather code to a short description."""
    table = {
        0: "clear sky",
        1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "moderate drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        71: "light snow", 73: "moderate snow", 75: "heavy snow",
        80: "rain showers", 81: "moderate showers", 82: "heavy showers",
        95: "thunderstorm",
    }
    return table.get(code, "unknown conditions")
