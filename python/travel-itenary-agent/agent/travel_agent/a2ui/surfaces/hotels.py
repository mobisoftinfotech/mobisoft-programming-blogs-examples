"""Hotel options: one card per hotel, each with its own "Select" button.

The card is a *template* over ``/hotels/items``. The Select button's action context
binds ``id`` relative to its card, so one component definition serves every hotel.
"""

from __future__ import annotations

from .. import messages as m
from ...tools import Hotel

SURFACE_ID = "hotels"
SELECT_ACTION = "select_hotel"


def _rating_word(r: float) -> str:
    return "Exceptional" if r >= 9.3 else "Excellent" if r >= 8.8 else "Very good" if r >= 8.2 else "Good"


def hotels_data(city: str, hotels: list[Hotel], travelers: int) -> dict:
    nights = hotels[0].nights if hotels else 0
    when = f"{hotels[0].check_in} → {hotels[0].check_out}" if hotels and hotels[0].check_in else "flexible dates"
    return {
        "title": f"🏨 Hotels in {city}",
        "subtitle": f"{nights} night{'s' * (nights != 1)} · {travelers} guest{'s' * (travelers != 1)} · {when}",
        "items": [
            {
                "id": h.id,
                "name": h.name,
                "stars": "★" * h.stars + "☆" * (5 - h.stars),
                "area": f"📍 {h.neighborhood}",
                "rating": f"{h.rating} · {_rating_word(h.rating)}",
                "nightly": f"${h.price_per_night} / night",
                "total": h.total_price,
                "totalNote": f"total for {h.nights} night{'s' * (h.nights != 1)}",
            }
            for h in hotels
        ],
    }


def build_hotels(city: str, hotels: list[Hotel], travelers: int) -> list[m.Message]:
    P = "/hotels"
    components = [
        m.column("root", ["h_title", "h_sub", "h_list"]),
        m.text("h_title", m.bind(f"{P}/title"), variant="h3"),
        m.text("h_sub", m.bind(f"{P}/subtitle"), variant="caption"),
        m.column("h_list", m.template("h_card", f"{P}/items")),
        m.card("h_card", "h_row"),
        m.row("h_row", ["h_info", "h_price", "h_select"], align="center"),
        m.column("h_info", ["h_name", "h_stars", "h_area", "h_rating"], weight=2),
        m.text("h_name", m.bind("name"), variant="h4"),
        m.text("h_stars", m.bind("stars")),
        m.text("h_area", m.bind("area"), variant="caption"),
        m.text("h_rating", m.bind("rating"), variant="caption"),
        m.column("h_price", ["h_nightly", "h_total", "h_total_note"], align="end", weight=1),
        m.text("h_nightly", m.bind("nightly")),
        m.text("h_total", m.currency(m.bind("total"))),
        m.text("h_total_note", m.bind("totalNote"), variant="caption"),
        m.button("h_select", "h_select_label", SELECT_ACTION, {"hotelId": m.bind("id")}, primary=True),
        m.text("h_select_label", "Select"),
    ]
    return [
        m.create_surface(SURFACE_ID),
        m.update_components(SURFACE_ID, components),
        m.update_data_model(SURFACE_ID, hotels_data(city, hotels, travelers), P),
    ]
