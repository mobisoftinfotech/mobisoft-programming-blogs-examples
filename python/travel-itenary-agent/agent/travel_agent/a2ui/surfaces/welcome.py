"""The start screen: one-tap example requests.

Shows a *templated* list: one Button per item in ``/welcome/suggestions``.
Each button's action context reads ``prompt`` relative to its own item.
"""

from __future__ import annotations

from .. import messages as m

SURFACE_ID = "welcome"
SUGGEST_ACTION = "suggest"

SUGGESTIONS = [
    ("🇹🇭  7 nights & 8 days in Thailand", "Prepare me an itinerary for 7 nights and 8 days in Thailand"),
    ("🏨  Book a hotel in Lisbon for 2 nights", "Book a hotel for me in Lisbon for 2 days"),
    ("🗼  Romantic weekend in Paris", "Plan a romantic 2-night weekend in Paris for two"),
    ("🍣  5-day food trip to Tokyo", "Plan a 5 day food-focused trip to Tokyo"),
]


def build_welcome() -> list[m.Message]:
    components = [
        m.column("root", ["w_title", "w_sub", "w_list", "w_hint"]),
        m.text("w_title", "Where to next? 🌍", variant="h2"),
        m.text("w_sub", "No dates or departure city needed. Tap an idea or just type in the chat.", variant="caption"),
        m.column("w_list", m.template("w_item", "/welcome/suggestions")),
        m.button("w_item", "w_item_label", SUGGEST_ACTION, {"prompt": m.bind("prompt")}),
        m.text("w_item_label", m.bind("label")),
        m.text("w_hint", "Everything on this side is A2UI: JSON sent by the agent, drawn by the client's own components.",
               variant="caption"),
    ]
    data = {"welcome": {"suggestions": [{"label": lbl, "prompt": p} for lbl, p in SUGGESTIONS]}}
    return [
        m.create_surface(SURFACE_ID),
        m.update_components(SURFACE_ID, components),
        m.update_data_model(SURFACE_ID, data),
    ]
