"""Mock travel data tools. Plain functions, so they're easy to unit-test.

`travel_agent.agent` wraps them as OpenAI function tools.
"""

from .attractions import CATEGORIES, Attraction, get_attractions
from .flights import Flight, search_flights
from .hotels import Hotel, search_hotels
from .weather import DayWeather, get_weather

__all__ = [
    "CATEGORIES",
    "Attraction",
    "DayWeather",
    "Flight",
    "Hotel",
    "get_attractions",
    "get_weather",
    "search_flights",
    "search_hotels",
]
