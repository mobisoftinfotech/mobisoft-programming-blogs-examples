"""Builder tests + a golden file.

The golden file (tests/golden/trip_form.json) is also loaded by the client's vitest
suite, which runs it through the real A2UI MessageProcessor. That checks the Python
output against the official v1.0 schema.

Regenerate after an intentional change:  UPDATE_GOLDEN=1 uv run pytest
"""

import json
import os
from pathlib import Path

import pytest

from travel_agent.a2ui import messages as m
from travel_agent.a2ui.surfaces.trip_form import SUBMIT_ACTION, SURFACE_ID, TripFormDefaults, build_trip_form

GOLDEN = Path(__file__).parent / "golden" / "trip_form.json"


def _components(msgs):
    return msgs[1]["updateComponents"]["components"]


def test_every_message_has_version():
    assert all(msg["version"] == "1.0" for msg in build_trip_form())


def test_message_order_and_surface():
    msgs = build_trip_form()
    assert [next(k for k in msg if k != "version") for msg in msgs] == [
        "createSurface",
        "updateComponents",
        "updateDataModel",
    ]
    assert {next(v for k, v in msg.items() if k != "version")["surfaceId"] for msg in msgs} == {SURFACE_ID}


def test_tree_is_closed():
    """Every referenced child exists, every component is reachable from root."""
    comps = {c["id"]: c for c in _components(build_trip_form())}
    assert "root" in comps

    def refs(c):
        out = list(c.get("children", []))
        out += [c[k] for k in ("child",) if k in c]
        return out

    seen, stack = set(), ["root"]
    while stack:
        cid = stack.pop()
        assert cid in comps, f"missing component {cid}"
        if cid not in seen:
            seen.add(cid)
            stack.extend(refs(comps[cid]))
    assert seen == set(comps), f"unreachable: {set(comps) - seen}"


def test_submit_sends_bound_context():
    submit = next(c for c in _components(build_trip_form()) if c["id"] == "submit")
    event = submit["action"]["event"]
    assert event["name"] == SUBMIT_ACTION
    assert event["context"]["destination"] == {"@path": "/trip/destination"}


def test_defaults_prefill_data_model_and_drop_unknown_interests():
    msgs = build_trip_form(TripFormDefaults(destination="Lisbon", interests=["food", "golf"]))
    trip = msgs[2]["updateDataModel"]["value"]["trip"]
    assert trip["destination"] == "Lisbon"
    assert trip["interests"] == ["food"]


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        m.update_components("s", [m.text("a", "x"), m.text("a", "y")])


def test_golden():
    actual = build_trip_form(min_date="2027-01-01")
    if os.getenv("UPDATE_GOLDEN") or not GOLDEN.exists():
        GOLDEN.write_text(json.dumps(actual, indent=2, ensure_ascii=False) + "\n", encoding="utf_8")
    assert actual == json.loads(GOLDEN.read_text(encoding="utf_8"))
