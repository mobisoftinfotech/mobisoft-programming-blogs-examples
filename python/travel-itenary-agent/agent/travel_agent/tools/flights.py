"""Mock flight search."""

from __future__ import annotations

from pydantic import BaseModel

from ._data import city_profile, parse_date, seeded_rng

AIRLINES = ["SkyWays", "Atlas Air", "Northwind", "BlueJet", "Meridian"]


class Flight(BaseModel):
    id: str
    airline: str
    origin: str
    destination: str
    depart_date: str
    depart_time: str
    duration_hours: float
    stops: int
    price_per_person: int


def search_flights(origin: str, destination: str, depart_date: str, travelers: int = 1) -> list[Flight]:
    """Return 3 deterministic mock flight options, cheapest first."""
    parse_date(depart_date)
    src, dst = city_profile(origin), city_profile(destination)
    rng = seeded_rng("flights", src["airport"], dst["airport"], depart_date)
    base = rng.randint(180, 650)
    flights = []
    for i in range(3):
        stops = [0, 1, 1][i]
        flights.append(
            Flight(
                id=f"FL-{src['airport']}{dst['airport']}-{i + 1}",
                airline=rng.choice(AIRLINES),
                origin=src["airport"],
                destination=dst["airport"],
                depart_date=depart_date,
                depart_time=f"{rng.randint(6, 21):02d}:{rng.choice(['00', '15', '30', '45'])}",
                duration_hours=round(rng.uniform(2, 13) + stops * 2.5, 1),
                stops=stops,
                price_per_person=base + rng.randint(-60, 220) - stops * 70,
            )
        )
    return sorted(flights, key=lambda f: f.price_per_person)
