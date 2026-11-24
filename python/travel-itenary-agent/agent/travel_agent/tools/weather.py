"""Mock weather 'forecast' based on monthly climate normals."""

from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel

from ._data import city_profile, parse_date, seeded_rng


class DayWeather(BaseModel):
    date: str
    high_c: int
    low_c: int
    condition: str  # "sunny" | "cloudy" | "rain"


def get_weather(city: str, start_date: str, end_date: str) -> list[DayWeather]:
    """Return one deterministic weather entry per day in [start_date, end_date]."""
    start, end = parse_date(start_date), parse_date(end_date)
    if end < start:
        raise ValueError("end_date must not be before start_date")
    if (end - start).days > 30:
        raise ValueError("Weather is limited to 31 days")
    profile = city_profile(city)
    days = []
    d = start
    while d <= end:
        rng = seeded_rng("weather", profile["name"], d.isoformat())
        high = profile["monthly_high_c"][d.month - 1] + rng.randint(-3, 3)
        rain_chance = profile["monthly_rain_days"][d.month - 1] / 30
        roll = rng.random()
        condition = "rain" if roll < rain_chance else ("cloudy" if roll < rain_chance + 0.3 else "sunny")
        days.append(DayWeather(date=d.isoformat(), high_c=high, low_c=high - rng.randint(5, 9), condition=condition))
        d += timedelta(days=1)
    return days
