"""Shared helpers for the mock travel data.

All mock tools are deterministic: the same inputs always produce the same output.
That keeps tests stable and lets tutorial readers see exactly what the screenshots show.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date
from functools import cache
from importlib import resources
from typing import Any


@cache
def _cities() -> dict[str, dict[str, Any]]:
    raw = resources.files("travel_agent.data").joinpath("cities.json").read_text("utf-8")
    return json.loads(raw)


def known_cities() -> list[str]:
    return [c["name"] for c in _cities().values()]


def city_profile(name: str) -> dict[str, Any]:
    """Return the curated profile for a showcase city, or a generated generic one."""
    key = name.strip().lower()
    if key in _cities():
        return _cities()[key]
    rng = seeded_rng("city", key)
    title = name.strip().title() or "Somewhere"
    return {
        "name": title,
        "country": "",
        "airport": (key.replace(" ", "")[:3] or "XXX").upper(),
        "currency": "USD",
        "hotel_base_per_night": rng.randint(90, 220),
        "monthly_high_c": [rng.randint(5, 30) for _ in range(12)],
        "monthly_rain_days": [rng.randint(2, 12) for _ in range(12)],
        "neighborhoods": ["Old Town", "City Center", "Riverside", "Arts District"],
        "attractions": [
            {"name": f"{title} old town walking tour", "category": "culture", "hours": 2.5, "cost": 0, "indoor": False},
            {"name": f"{title} history museum", "category": "culture", "hours": 2, "cost": 15, "indoor": True},
            {"name": "Local market food tasting", "category": "food", "hours": 2, "cost": 35, "indoor": False},
            {"name": "Regional cooking class", "category": "food", "hours": 3, "cost": 80, "indoor": True},
            {"name": "Scenic viewpoint hike", "category": "outdoors", "hours": 3, "cost": 0, "indoor": False},
            {"name": "City park & botanical garden", "category": "outdoors", "hours": 2, "cost": 5, "indoor": False},
            {"name": "Main square & cathedral", "category": "landmarks", "hours": 1.5, "cost": 0, "indoor": False},
            {"name": "Live music bar", "category": "nightlife", "hours": 2.5, "cost": 25, "indoor": True},
        ],
    }


def seeded_rng(*parts: object) -> random.Random:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def parse_date(value: str) -> date:
    """Parse an ISO date (YYYY-MM-DD). Raises ValueError with a helpful message."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Expected an ISO date like 2026-05-14, got {value!r}") from exc
