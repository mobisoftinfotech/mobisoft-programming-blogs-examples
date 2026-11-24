"""Mock points-of-interest lookup."""

from __future__ import annotations

from pydantic import BaseModel

from ._data import city_profile

CATEGORIES = ("culture", "food", "outdoors", "landmarks", "nightlife")


class Attraction(BaseModel):
    name: str
    category: str
    duration_hours: float
    cost_per_person: int
    indoor: bool


def get_attractions(city: str, interests: list[str] | None = None) -> list[Attraction]:
    """Return attractions for a city, those matching the interests first."""
    wanted = {i.lower() for i in (interests or [])}
    items = [
        Attraction(
            name=a["name"],
            category=a["category"],
            duration_hours=a["hours"],
            cost_per_person=a["cost"],
            indoor=a["indoor"],
        )
        for a in city_profile(city)["attractions"]
    ]
    return sorted(items, key=lambda a: (a.category not in wanted, a.name))
