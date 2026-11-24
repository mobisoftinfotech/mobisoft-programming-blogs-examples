"""Builder tests + golden files for every surface.

The golden files are also loaded by the client's vitest suite, which runs them through
the real A2UI v1.0 MessageProcessor and renderer.

Regenerate after an intentional change:  UPDATE_GOLDEN=1 uv run pytest
"""

import json
import os
from datetime import date
from pathlib import Path

import pytest

from travel_agent import tools
from travel_agent.a2ui.surfaces import booking, hotels, itinerary, notice, welcome
from travel_agent.ui_tools import TurnContext, render_confirmation, render_hotels

from .samples import thailand

GOLDEN = Path(__file__).parent / "golden"


def _lisbon_hotels():
    return tools.search_hotels("Lisbon", nights=2, travelers=2)


def _confirmation():
    ctx = TurnContext(open_surfaces=set(), today=date(2027, 1, 1))
    render_hotels(ctx, city="Lisbon", nights=2, travelers=2)
    hotel_id = next(iter(ctx.hotels))
    ctx.drain()
    render_confirmation(ctx, hotel_id=hotel_id, guest_name="Ana Silva", email="ana@example.com", guests=2,
                        check_in=None, breakfast=True)
    return ctx.drain()


SURFACES = {
    "welcome": welcome.build_welcome,
    "itinerary": lambda: itinerary.build_itinerary(thailand()),
    "hotels": lambda: hotels.build_hotels("Lisbon", _lisbon_hotels(), 2),
    "booking_form": lambda: booking.build_booking_form(_lisbon_hotels()[0], 2),
    "booking_confirmed": _confirmation,
    "notice": lambda: notice.build_notice("off_topic", "fixing Python code", "Plan a 3-day tech trip to San Francisco"),
}


def _components(msgs):
    return [c for msg in msgs if "updateComponents" in msg for c in msg["updateComponents"]["components"]]


def _refs(c):
    children = c.get("children", [])
    out = [children["componentId"]] if isinstance(children, dict) else list(children)
    return out + [c["child"]] if "child" in c else out


@pytest.mark.parametrize("name", SURFACES)
def test_every_message_has_version(name):
    assert all(msg["version"] == "1.0" for msg in SURFACES[name]())


@pytest.mark.parametrize("name", SURFACES)
def test_tree_is_closed(name):
    """Every referenced child (static or template) exists, and every component is reachable."""
    comps = {c["id"]: c for c in _components(SURFACES[name]())}
    seen, stack = set(), ["root"]
    while stack:
        cid = stack.pop()
        assert cid in comps, f"missing component {cid}"
        if cid not in seen:
            seen.add(cid)
            stack.extend(_refs(comps[cid]))
    assert seen == set(comps), f"unreachable: {set(comps) - seen}"


def test_itinerary_uses_nested_templates():
    comps = {c["id"]: c for c in _components(SURFACES["itinerary"]())}
    assert comps["it_days"]["children"] == {"componentId": "it_day", "path": "/itinerary/days"}
    assert comps["it_acts"]["children"] == {"componentId": "it_act", "path": "activities"}, "relative path"
    assert comps["it_stop_btn"]["action"]["event"]["context"] == {"city": {"@path": "city"}, "nights": {"@path": "nights"}}


def test_itinerary_data():
    data = itinerary.itinerary_data(thailand())
    assert data["lengthLabel"] == "🗓️ 7 nights · 3 days"
    assert data["routeLabel"] == "📍 Bangkok → Chiang Mai → Phuket"
    assert data["days"][1]["activities"][0]["title"] == "🏛️ Grand Palace & Wat Pho"
    assert data["days"][0]["activities"][0]["cost"] == "Free"


def test_hotel_cards_select_by_id():
    msgs = SURFACES["hotels"]()
    items = next(m for m in msgs if "updateDataModel" in m)["updateDataModel"]["value"]["items"]
    assert len(items) == 4 and all(i["id"].startswith("HT-LIS-") for i in items)
    select = next(c for c in _components(msgs) if c["id"] == "h_select")
    assert select["action"]["event"] == {"name": "select_hotel", "context": {"hotelId": {"@path": "id"}}}


def test_confirmation_replaces_root_and_closes_hotels():
    msgs = _confirmation()
    assert any(m.get("deleteSurface", {}).get("surfaceId") == "hotels" for m in msgs)
    root = next(c for c in _components(msgs) if c["id"] == "root")
    assert root["child"] == "c_col"


@pytest.mark.parametrize("name", SURFACES)
def test_golden(name):
    path = GOLDEN / f"{name}.json"
    actual = SURFACES[name]()
    if os.getenv("UPDATE_GOLDEN") or not path.exists():
        path.write_text(json.dumps(actual, indent=2, ensure_ascii=False) + "\n", encoding="utf_8")
    assert actual == json.loads(path.read_text(encoding="utf_8"))


def test_notice_tones_share_one_layout():
    layouts = {k: _components(notice.build_notice(k, "x", "y")) for k in ("off_topic", "unsafe", "prompt_injection")}
    icons = {k: next(c for c in v if c["id"] == "n_icon")["name"] for k, v in layouts.items()}
    assert icons == {"off_topic": "info", "unsafe": "warning", "prompt_injection": "lock"}
    unsafe = next(m for m in notice.build_notice("unsafe", "x", "y") if "updateDataModel" in m)
    assert len(unsafe["updateDataModel"]["value"]["suggestions"]) == 2, "no tailored suggestion for unsafe asks"


# --- A2UI v1.0 rules enforced by the helpers -------------------------------------------

def test_v1_bindings_and_calls_use_at_keys():
    from travel_agent.a2ui import messages as m

    assert m.bind("/a") == {"@path": "/a"}
    assert m.currency(m.bind("total"))["@call"] == "formatCurrency"


def test_headings_become_markdown():
    from travel_agent.a2ui import messages as m

    assert m.text("t", "Hello", variant="h2") == {"id": "t", "component": "Text", "text": "## Hello"}
    bound = m.text("t", m.bind("/x/title"), variant="h3")["text"]
    assert bound == {"@call": "formatString", "args": {"value": "### ${/x/title}"}, "returnType": "string"}
    assert m.text("t", "small", variant="caption")["variant"] == "caption"


def test_hyphenated_ids_are_rejected():
    from travel_agent.a2ui import messages as m

    with pytest.raises(ValueError, match="identifiers"):
        m.update_components("s", [m.text("it-title", "x")])
