"""Chapter 3: the trip intake form, written by hand as A2UI v1.0 messages.

Optional: the agent plans straight from chat. Only the destination is required here.

In Chapter 4 the LLM fills in ``TripFormDefaults`` through a strict-schema tool call.
The layout below stays the same: the model supplies data, this code supplies structure.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .. import messages as m
from ...tools import CATEGORIES

SURFACE_ID = "trip_form"
SUBMIT_ACTION = "plan_trip"

INTEREST_LABELS = {
    "culture": "🏛️ Culture",
    "food": "🍜 Food",
    "outdoors": "🥾 Outdoors",
    "landmarks": "📸 Landmarks",
    "nightlife": "🌙 Nightlife",
}


class TripFormDefaults(BaseModel):
    """Values that pre-fill the form (the user can change all of them)."""

    origin: str = ""
    destination: str = ""
    start_date: str = ""  # ISO date
    end_date: str = ""
    travelers: int = Field(default=2, ge=1, le=8)
    budget: int = Field(default=3000, ge=300, le=20000)
    interests: list[str] = Field(default_factory=lambda: ["culture", "food"])


def build_trip_form(defaults: TripFormDefaults | None = None, *, min_date: str | None = None) -> list[m.Message]:
    d = defaults or TripFormDefaults()
    P = "/trip"  # data model root for this form

    required = lambda path, msg: m.check(m.call("required", value=m.bind(path)), msg)  # noqa: E731

    components = [
        m.column("root", ["header", "route_row", "dates_row", "travelers", "budget", "interests", "submit"]),
        m.column("header", ["title", "subtitle"]),
        m.text("title", "✈️ Plan your trip", variant="h2"),
        m.text("subtitle", "Only the destination is required. Dates and departure city are optional.", variant="caption"),
        # Route
        m.row("route_row", ["origin", "destination"]),
        m.text_field("origin", "From (optional)", m.bind(f"{P}/origin"), weight=1),
        m.text_field("destination", "To", m.bind(f"{P}/destination"), weight=1),
        # Dates
        m.row("dates_row", ["start_date", "end_date"]),
        m.date_input("start_date", "Depart (optional)", m.bind(f"{P}/startDate"), min_=min_date, weight=1),
        m.date_input("end_date", "Return (optional)", m.bind(f"{P}/endDate"), min_=m.bind(f"{P}/startDate"), weight=1),
        # Travelers + budget: the labels show the live value through formatString
        m.slider("travelers", m.fmt(f"Travelers: ${{{P}/travelers}}"), m.bind(f"{P}/travelers"), min_=1, max_=8),
        m.slider("budget", m.fmt(f"Total budget (USD): ${{{P}/budget}}"), m.bind(f"{P}/budget"), min_=500, max_=15000),
        # Interests
        m.choice_picker(
            "interests",
            "Interests",
            [(c, INTEREST_LABELS[c]) for c in CATEGORIES],
            m.bind(f"{P}/interests"),
        ),
        # Submit: the context is read from the data model when the button is clicked
        m.button(
            "submit",
            "submit_label",
            SUBMIT_ACTION,
            context={
                "origin": m.bind(f"{P}/origin"),
                "destination": m.bind(f"{P}/destination"),
                "startDate": m.bind(f"{P}/startDate"),
                "endDate": m.bind(f"{P}/endDate"),
                "travelers": m.bind(f"{P}/travelers"),
                "budget": m.bind(f"{P}/budget"),
                "interests": m.bind(f"{P}/interests"),
            },
            primary=True,
            checks=[
                required(f"{P}/destination", "Where do you want to go?"),
            ],
        ),
        m.text("submit_label", "Plan my trip"),
    ]

    data = {
        "trip": {
            "origin": d.origin,
            "destination": d.destination,
            "startDate": d.start_date,
            "endDate": d.end_date,
            "travelers": d.travelers,
            "budget": d.budget,
            "interests": [i for i in d.interests if i in CATEGORIES],
        }
    }

    return [
        m.create_surface(SURFACE_ID),
        m.update_components(SURFACE_ID, components),
        m.update_data_model(SURFACE_ID, data),
    ]
