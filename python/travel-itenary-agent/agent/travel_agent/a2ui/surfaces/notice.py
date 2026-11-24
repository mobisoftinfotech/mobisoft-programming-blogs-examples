"""Out-of-scope notice: what the agent shows instead of answering a non-travel question.

A guardrail answer is still generative UI: a friendly card that says why, lists what the
agent *can* do, and offers one-tap travel requests (one tailored to what the user asked).
Each tone (off-topic, unsafe, injection) is the same layout with different data and icon.
"""

from __future__ import annotations

from typing import Literal

from .. import messages as m
from .welcome import SUGGEST_ACTION

SURFACE_ID = "notice"
DISMISS_ACTION = "dismiss_notice"

Kind = Literal["off_topic", "unsafe", "prompt_injection"]

COPY: dict[str, tuple[str, str, str]] = {
    # kind: (icon, title, message template)
    "off_topic": (
        "info",
        "That's outside my travel desk",
        "I'm Wanderly, a travel-planning assistant, so I can't help with {topic}. "
        "I'd love to help you plan a trip, though!",
    ),
    "unsafe": (
        "warning",
        "I can't help with that",
        "That request isn't something I can assist with. I'm happy to help with safe, legal travel plans.",
    ),
    "prompt_injection": (
        "lock",
        "Let's stay on track",
        "I can't change how I work or share my instructions, but I can plan your next trip.",
    ),
}

CAPABILITIES = [
    "🗺️ Day-by-day itineraries for any country or city, with no dates needed",
    "🏨 Hotel options for any number of nights",
    "🛎️ Booking a stay and sending a confirmation",
    "✏️ Adjusting a plan: slower, cheaper, more food, more nature…",
]

DEFAULT_SUGGESTIONS = [
    ("🇹🇭 7 nights in Thailand", "Prepare me an itinerary for 7 nights and 8 days in Thailand"),
    ("🏨 Hotel in Lisbon, 2 nights", "Book a hotel for me in Lisbon for 2 days"),
]


def build_notice(kind: Kind, topic: str = "", suggestion: str = "") -> list[m.Message]:
    icon, title, template = COPY[kind]
    suggestions = list(DEFAULT_SUGGESTIONS)
    if suggestion and kind == "off_topic":
        suggestions.insert(0, (f"✨ {suggestion}", suggestion))
    P = "/notice"
    components = [
        m.card("root", "n_col"),
        m.column("n_col", ["n_head", "n_msg", "n_asked", "n_divider", "n_can_title", "n_can_list",
                           "n_try_title", "n_try_list", "n_actions"]),
        m.row("n_head", ["n_icon", "n_title"], align="center"),
        m.icon("n_icon", icon),
        m.text("n_title", m.bind(f"{P}/title"), variant="h3"),
        m.text("n_msg", m.bind(f"{P}/message")),
        m.text("n_asked", m.fmt(f"You asked about: ${{{P}/topic}}"), variant="caption"),
        m.divider("n_divider"),
        m.text("n_can_title", "Here's what I can do", variant="h5"),
        m.column("n_can_list", m.template("n_can_item", f"{P}/capabilities")),
        m.text("n_can_item", m.bind("text"), variant="caption"),
        m.text("n_try_title", "Try one of these", variant="h5"),
        m.column("n_try_list", m.template("n_try_btn", f"{P}/suggestions")),
        m.button("n_try_btn", "n_try_label", SUGGEST_ACTION, {"prompt": m.bind("prompt")}),
        m.text("n_try_label", m.bind("label")),
        m.row("n_actions", ["n_dismiss"], justify="end", align="center"),
        m.button("n_dismiss", "n_dismiss_label", DISMISS_ACTION, borderless=True),
        m.text("n_dismiss_label", "Dismiss"),
    ]
    data = {
        "kind": kind,
        "title": title,
        "message": template.format(topic=topic or "that"),
        "topic": topic or "something outside travel",
        "capabilities": [{"text": c} for c in CAPABILITIES],
        "suggestions": [{"label": lbl[:70], "prompt": p[:300]} for lbl, p in suggestions],
    }
    return [
        m.create_surface(SURFACE_ID),
        m.update_components(SURFACE_ID, components),
        m.update_data_model(SURFACE_ID, data, P),
    ]
