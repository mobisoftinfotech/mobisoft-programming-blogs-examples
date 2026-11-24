"""Live checks against the real model. Run with: uv run pytest -m live"""

import asyncio
import os

import pytest
from agents import Runner

from travel_agent.agent import build_agent
from travel_agent.ui_tools import TurnContext

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="needs OPENAI_API_KEY"),
]


# One loop for the module: the OpenAI client is shared, and asyncio.run() would close its loop.
_LOOP = asyncio.new_event_loop()


def _run(text):
    ctx = TurnContext(open_surfaces=set())
    _LOOP.run_until_complete(Runner.run(build_agent(), text, context=ctx))
    return ctx


def _data(ctx, surface):
    return next(m for m in ctx.outbox if m.get("updateDataModel", {}).get("surfaceId") == surface)["updateDataModel"]["value"]


def test_country_itinerary_without_dates():
    ctx = _run("Prepare me an itinerary for 7 nights and 8 days for Thailand")
    data = _data(ctx, "itinerary")
    assert data["nights"] == 7
    assert len(data["days"]) == 8
    assert len(data["stops"]) >= 2, "a country trip should have several stops"


def test_hotel_request_without_dates():
    ctx = _run("Book a hotel for me in Lisbon for 2 days")
    data = _data(ctx, "hotels")
    assert "Lisbon" in data["title"]
    assert "2 nights" in data["subtitle"]


def test_off_topic_is_blocked_before_the_planner():
    from agents import InputGuardrailTripwireTriggered

    with pytest.raises(InputGuardrailTripwireTriggered) as exc:
        _run("Write a Python function to reverse a linked list")
    assert exc.value.guardrail_result.output.output_info.category == "off_topic"


def test_short_follow_up_is_not_blocked():
    from travel_agent.guardrails import classify

    verdict = _LOOP.run_until_complete(classify([
        {"role": "user", "content": "7 nights in Thailand"},
        {"role": "user", "content": "make it cheaper"},
    ]))
    assert verdict.category == "travel"
