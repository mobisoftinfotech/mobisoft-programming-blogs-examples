"""Mock hotel search.

Dates are optional: "a hotel in Lisbon for 2 nights" is a complete request.
Pass ``nights`` alone (flexible dates) or ``check_in`` + ``check_out``.
"""

from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel

from ._data import city_profile, parse_date, seeded_rng

STYLES = [("Boutique", 1.25), ("Comfort", 1.0), ("Budget", 0.6), ("Luxury", 2.1)]


class Hotel(BaseModel):
    id: str
    name: str
    city: str
    neighborhood: str
    stars: int
    rating: float
    price_per_night: int
    nights: int
    total_price: int
    check_in: str = ""  # empty = flexible dates
    check_out: str = ""


def search_hotels(
    city: str,
    check_in: str | None = None,
    check_out: str | None = None,
    travelers: int = 1,
    nights: int | None = None,
) -> list[Hotel]:
    """Return 4 deterministic mock hotels for the stay, cheapest first."""
    if check_in and check_out:
        start, end = parse_date(check_in), parse_date(check_out)
        nights = (end - start).days
        if nights <= 0:
            raise ValueError("check_out must be after check_in")
    elif check_in and nights:
        check_out = (parse_date(check_in) + timedelta(days=nights)).isoformat()
    elif not nights or nights <= 0:
        raise ValueError("Give either check_in + check_out, or a positive number of nights")
    profile = city_profile(city)
    rng = seeded_rng("hotels", profile["name"], check_in or "", nights)
    rooms = max(1, (travelers + 1) // 2)
    hotels = []
    for i, (style, factor) in enumerate(STYLES):
        nightly = int(profile["hotel_base_per_night"] * factor * rooms + rng.randint(-15, 25))
        hotels.append(
            Hotel(
                id=f"HT-{profile['airport']}-{i + 1}",
                name=f"{style} {rng.choice(['House', 'Suites', 'Inn', 'Residence'])} {profile['neighborhoods'][i % 4]}",
                city=profile["name"],
                neighborhood=profile["neighborhoods"][i % 4],
                stars={"Budget": 2, "Comfort": 3, "Boutique": 4, "Luxury": 5}[style],
                rating=round(rng.uniform(7.6, 9.6), 1),
                price_per_night=nightly,
                nights=nights,
                total_price=nightly * nights,
                check_in=check_in or "",
                check_out=check_out or "",
            )
        )
    return sorted(hotels, key=lambda h: h.price_per_night)
