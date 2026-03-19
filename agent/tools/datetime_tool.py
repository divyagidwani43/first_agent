"""
Date & Time tool.
Uses Python's datetime + pytz (bundle includes IANA tz data, works on Windows).
Handles: current time, time in a city, date today, date math ("add 3 days").
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import pytz

# ---------------------------------------------------------------------------
# City / abbreviation → IANA timezone map
# ---------------------------------------------------------------------------

_CITY_TZ: dict[str, str] = {
    # India
    "new delhi": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "jaipur": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",
    "hyderabad": "Asia/Kolkata",
    "kolkata": "Asia/Kolkata",
    "chennai": "Asia/Kolkata",
    "pune": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "ist": "Asia/Kolkata",
    # Asia
    "tokyo": "Asia/Tokyo",
    "japan": "Asia/Tokyo",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "china": "Asia/Shanghai",
    "seoul": "Asia/Seoul",
    "korea": "Asia/Seoul",
    "singapore": "Asia/Singapore",
    "dubai": "Asia/Dubai",
    "uae": "Asia/Dubai",
    "karachi": "Asia/Karachi",
    "lahore": "Asia/Karachi",
    "dhaka": "Asia/Dhaka",
    "kathmandu": "Asia/Kathmandu",
    "colombo": "Asia/Colombo",
    # Europe
    "london": "Europe/London",
    "uk": "Europe/London",
    "paris": "Europe/Paris",
    "france": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "germany": "Europe/Berlin",
    "rome": "Europe/Rome",
    "italy": "Europe/Rome",
    "madrid": "Europe/Madrid",
    "spain": "Europe/Madrid",
    "amsterdam": "Europe/Amsterdam",
    "moscow": "Europe/Moscow",
    "russia": "Europe/Moscow",
    "istanbul": "Europe/Istanbul",
    "turkey": "Europe/Istanbul",
    "oslo": "Europe/Oslo",
    "stockholm": "Europe/Stockholm",
    # Americas
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "est": "America/New_York",
    "boston": "America/New_York",
    "miami": "America/New_York",
    "chicago": "America/Chicago",
    "cst": "America/Chicago",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "pst": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles",
    "toronto": "America/Toronto",
    "canada": "America/Toronto",
    "mexico city": "America/Mexico_City",
    "sao paulo": "America/Sao_Paulo",
    "rio de janeiro": "America/Sao_Paulo",
    "brazil": "America/Sao_Paulo",
    # Africa / Others
    "cairo": "Africa/Cairo",
    "egypt": "Africa/Cairo",
    "sydney": "Australia/Sydney",
    "australia": "Australia/Sydney",
    "utc": "UTC",
    "gmt": "GMT",
}


def _resolve_tz(city: str) -> pytz.BaseTzInfo | None:
    key = city.lower().strip()
    tz_name = _CITY_TZ.get(key)
    if not tz_name:
        return None
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        return None


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_time(city: str | None = None) -> str:
    if not city:
        now = datetime.now()
        return (
            f"🕐 Local time: {now.strftime('%I:%M %p')}  |  "
            f"{now.strftime('%A, %B %d, %Y')}"
        )

    tz = _resolve_tz(city)
    if tz is None:
        return (
            f"Sorry, I don't know the timezone for '{city}'.\n"
            "Try: Tokyo, London, New York, Dubai, Mumbai..."
        )

    now = datetime.now(tz)
    return (
        f"🕐 Time in {city.title()}: {now.strftime('%I:%M %p')}  |  "
        f"{now.strftime('%A, %B %d, %Y')}  ({now.strftime('%Z')})"
    )


def get_date_info(text: str) -> str:
    text_l = text.lower()

    # "add N days to today" / "N days from now/today"
    m = re.search(r"(\d+)\s+days?\s+(?:from\s+(?:now|today)|later)", text_l)
    if not m:
        m = re.search(r"add\s+(\d+)\s+days?\s+to\s+today", text_l)
    if m:
        n = int(m.group(1))
        future = datetime.now() + timedelta(days=n)
        return f"📅 {n} day(s) from today: {future.strftime('%A, %B %d, %Y')}"

    # "N days ago"
    m = re.search(r"(\d+)\s+days?\s+ago", text_l)
    if m:
        n = int(m.group(1))
        past = datetime.now() - timedelta(days=n)
        return f"📅 {n} day(s) ago: {past.strftime('%A, %B %d, %Y')}"

    now = datetime.now()
    return f"📅 Today is {now.strftime('%A, %B %d, %Y')}"


def extract_city_for_time(text: str) -> str | None:
    patterns = [
        r"time\s+(?:in|at|for)\s+([a-zA-Z ]+?)(?:\?|$|\.)",
        r"(?:what(?:'s|\s+is)?(?:\s+the)?|current)\s+time\s+(?:in|at|for)\s+([a-zA-Z ]+?)(?:\?|$|\.)",
        r"what\s+(?:time|day|date)\s+is\s+it\s+in\s+([a-zA-Z ]+?)(?:\?|$|\.)",
        r"what\s+(?:time|day|date)\s+is\s+(?:it\s+)?in\s+([a-zA-Z ]+?)(?:\?|$|\.)",
        r"clock\s+(?:in|for|at)\s+([a-zA-Z ]+?)(?:\?|$|\.)",
    ]
    for pat in patterns:
        m = re.search(pat, text.strip(), re.I)
        if m:
            return m.group(1).strip()
    return None


def handle(text: str) -> str:
    """Main entry point called by the agent controller."""
    text_l = text.lower()

    # Date math queries
    if re.search(r"\d+\s+days?\s+(from|ago|later)|add\s+\d+\s+days?", text_l):
        return get_date_info(text)

    # Time in a city
    city = extract_city_for_time(text)
    if city:
        return get_time(city)

    # Day / date / today queries
    if re.search(r"\b(date|today|day|month|year|what day)\b", text_l):
        return get_date_info(text)

    # Default: local time
    return get_time()
