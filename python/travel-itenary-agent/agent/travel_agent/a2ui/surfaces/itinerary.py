"""Day-by-day itinerary, built from data the model supplies through ``show_itinerary``.

A2UI ideas shown here:

* **Templates.** Days, activities, stops and tips are lists in the data model. The layout
  is sent once; ``Column(children=template(...))`` repeats a component per item, and
  templates nest (each day's activities).
* **Relative bindings.** Inside a template, ``bind("title")`` reads the current item.
* **Client functions.** ``formatCurrency`` formats the budget in the browser.
* **Data-only refinement.** Changing the plan re-sends just ``updateDataModel``; the
  component tree is identical, so nothing is rebuilt.
* **Actions from templates.** Each stop's "Hotels" button sends that stop's city and nights.
* **Two-way binding.** The "ask for a change" field writes to ``/refine/request``, and the
  button reads it back into its action context.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .. import messages as m

SURFACE_ID = "itinerary"
REFINE_ACTION = "refine_itinerary"
FIND_HOTELS_ACTION = "find_hotels"

Slot = Literal["Morning", "Afternoon", "Evening"]
Kind = Literal["culture", "food", "outdoors", "landmarks", "nightlife", "relax", "travel", "shopping"]

SLOT_ICON = {"Morning": "🌅", "Afternoon": "☀️", "Evening": "🌙"}
KIND_ICON = {
    "culture": "🏛️", "food": "🍜", "outdoors": "🥾", "landmarks": "📸",
    "nightlife": "🍸", "relax": "🧘", "travel": "🚆", "shopping": "🛍️",
}

QUICK_CHANGES = [
    ("relax", "🐢 Slower pace", "Make the pace more relaxed: fewer activities per day and more free time."),
    ("more", "⚡ Pack in more", "Pack in more: add extra activities and hidden gems."),
    ("cheaper", "💸 Cheaper", "Make the trip cheaper: swap paid activities for free or low-cost ones."),
]


# --- what the model fills in (strict schema) --------------------------------------

class Activity(BaseModel):
    slot: Slot
    kind: Kind
    title: str
    description: str = Field(description="One short sentence.")
    est_cost_usd: int = Field(description="Estimated cost per person in USD; 0 if free.")


class Day(BaseModel):
    day: int
    location: str = Field(description="City or area where this day takes place.")
    title: str = Field(description="Short theme for the day, e.g. 'Temples & street food'.")
    activities: list[Activity]


class Stop(BaseModel):
    city: str
    nights: int


class Itinerary(BaseModel):
    destination: str
    title: str
    summary: str
    nights: int
    travelers: int
    stops: list[Stop]
    days: list[Day]
    tips: list[str]
    est_budget_per_person_usd: int


# --- builder -------------------------------------------------------------------------

def _cost_label(usd: int) -> str:
    return "Free" if usd <= 0 else f"~${usd}"


def itinerary_data(it: Itinerary) -> dict:
    route = " → ".join(s.city for s in it.stops) or it.destination
    return {
        "destination": it.destination,
        "title": it.title,
        "summary": it.summary,
        "nights": it.nights,
        "lengthLabel": f"🗓️ {it.nights} night{'s' * (it.nights != 1)} · {len(it.days)} days",
        "routeLabel": f"📍 {route}",
        "travelersLabel": f"👥 {it.travelers} traveler{'s' * (it.travelers != 1)}",
        "budget": it.est_budget_per_person_usd,
        "stops": [
            {"city": s.city, "nights": s.nights, "label": f"{s.city} · {s.nights} night{'s' * (s.nights != 1)}"}
            for s in it.stops
        ],
        "days": [
            {
                "label": f"Day {d.day}",
                "location": f"📍 {d.location}",
                "title": d.title,
                "activities": [
                    {
                        "slot": f"{SLOT_ICON[a.slot]} {a.slot}",
                        "title": f"{KIND_ICON[a.kind]} {a.title}",
                        "description": a.description,
                        "cost": _cost_label(a.est_cost_usd),
                    }
                    for a in d.activities
                ],
            }
            for d in it.days
        ],
        "tips": [{"text": f"• {t}"} for t in it.tips],
    }


def build_components() -> list[m.Component]:
    P = "/itinerary"
    return [
        m.column("root", ["it_header", "it_stops", "it_days", "it_tips", "it_refine"]),
        # Header
        m.card("it_header", "it_header_col"),
        m.column("it_header_col", ["it_title", "it_summary", "it_meta", "it_budget"]),
        m.text("it_title", m.bind(f"{P}/title"), variant="h2"),
        m.text("it_summary", m.bind(f"{P}/summary")),
        m.row("it_meta", ["it_length", "it_route", "it_travelers"], justify="spaceBetween"),
        m.text("it_length", m.bind(f"{P}/lengthLabel"), variant="caption"),
        m.text("it_route", m.bind(f"{P}/routeLabel"), variant="caption"),
        m.text("it_travelers", m.bind(f"{P}/travelersLabel"), variant="caption"),
        m.row("it_budget", ["it_budget_pre", "it_budget_value", "it_budget_post"], align="center"),
        m.text("it_budget_pre", "💰 About", variant="h5"),
        m.text("it_budget_value", m.currency(m.bind(f"{P}/budget"))),
        m.text("it_budget_post", "per person, excluding flights", variant="caption"),
        # Stops: one row per base city, each with its own action
        m.column("it_stops", ["it_stops_title", "it_stops_list"]),
        m.text("it_stops_title", "Where you'll stay", variant="h4"),
        m.column("it_stops_list", m.template("it_stop", f"{P}/stops")),
        m.row("it_stop", ["it_stop_label", "it_stop_btn"], align="center"),
        m.text("it_stop_label", m.bind("label"), weight=1),
        m.button("it_stop_btn", "it_stop_btn_label", FIND_HOTELS_ACTION,
                 {"city": m.bind("city"), "nights": m.bind("nights")}),
        m.text("it_stop_btn_label", "🏨 Find hotels"),
        # Days (nested templates: days → activities)
        m.column("it_days", m.template("it_day", f"{P}/days")),
        m.card("it_day", "it_day_col"),
        m.column("it_day_col", ["it_day_head", "it_day_title", "it_day_divider", "it_acts"]),
        m.row("it_day_head", ["it_day_label", "it_day_loc"], justify="spaceBetween", align="center"),
        m.text("it_day_label", m.bind("label"), variant="h4"),
        m.text("it_day_loc", m.bind("location"), variant="caption"),
        m.text("it_day_title", m.bind("title"), variant="h5"),
        m.divider("it_day_divider"),
        m.column("it_acts", m.template("it_act", "activities")),
        m.row("it_act", ["it_act_slot", "it_act_body", "it_act_cost"], align="start"),
        m.text("it_act_slot", m.bind("slot"), variant="caption"),
        m.column("it_act_body", ["it_act_title", "it_act_desc"], weight=1),
        m.text("it_act_title", m.bind("title")),
        m.text("it_act_desc", m.bind("description"), variant="caption"),
        m.text("it_act_cost", m.bind("cost"), variant="caption"),
        # Tips
        m.card("it_tips", "it_tips_col"),
        m.column("it_tips_col", ["it_tips_title", "it_tips_list"]),
        m.text("it_tips_title", "💡 Good to know", variant="h4"),
        m.column("it_tips_list", m.template("it_tip", f"{P}/tips")),
        m.text("it_tip", m.bind("text"), variant="caption"),
        # Refinement: quick buttons (literal context) + free text (bound context)
        m.card("it_refine", "it_refine_col"),
        m.column("it_refine_col", ["it_refine_title", "it_quick", "it_custom"]),
        m.text("it_refine_title", "Not quite right?", variant="h4"),
        m.row("it_quick", [f"it_q_{key}" for key, _, _ in QUICK_CHANGES]),
        *[
            c
            for key, label, change in QUICK_CHANGES
            for c in (
                m.button(f"it_q_{key}", f"it_q_{key}_label", REFINE_ACTION, {"change": change}),
                m.text(f"it_q_{key}_label", label),
            )
        ],
        m.row("it_custom", ["it_custom_input", "it_custom_btn"], align="end"),
        m.text_field("it_custom_input", "Ask for a change", m.bind("/refine/request"), weight=1),
        m.button("it_custom_btn", "it_custom_btn_label", REFINE_ACTION, {"change": m.bind("/refine/request")},
                 primary=True,
                 checks=[m.check(m.call("required", value=m.bind("/refine/request")), "Type what to change.")]),
        m.text("it_custom_btn_label", "Update plan"),
    ]


def build_itinerary(it: Itinerary) -> list[m.Message]:
    data = itinerary_data(it)
    return [
        m.create_surface(SURFACE_ID),
        m.update_components(SURFACE_ID, build_components()),
        m.update_data_model(SURFACE_ID, data, "/itinerary"),
        m.update_data_model(SURFACE_ID, "", "/refine/request"),
    ]
