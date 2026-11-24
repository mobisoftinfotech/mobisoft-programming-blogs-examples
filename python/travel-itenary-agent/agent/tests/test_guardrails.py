"""Guardrail logic without calling a model (the classifier is faked)."""

import asyncio
from types import SimpleNamespace

import pytest

from travel_agent import guardrails
from travel_agent.guardrails import ScopeVerdict, classifier_prompt, travel_scope
from travel_agent.ui_tools import TurnContext, render_itinerary, render_notice

from .samples import thailand


def _check(text, monkeypatch, category, from_ui=False):
    async def fake_classify(items):
        return ScopeVerdict(category=category, topic="t", suggestion="s")

    monkeypatch.setattr(guardrails, "classify", fake_classify)
    ctx = SimpleNamespace(context=TurnContext(open_surfaces=set(), from_ui=from_ui))
    return asyncio.run(travel_scope.guardrail_function(ctx, None, text))


@pytest.mark.parametrize("category,blocked", [
    ("travel", False), ("small_talk", False), ("off_topic", True), ("unsafe", True), ("prompt_injection", True),
])
def test_tripwire_by_category(monkeypatch, category, blocked):
    assert _check("anything", monkeypatch, category).tripwire_triggered is blocked


def test_ui_clicks_skip_the_classifier(monkeypatch):
    out = _check("I selected hotel HT-LIS-2", monkeypatch, "off_topic", from_ui=True)
    assert out.tripwire_triggered is False and out.output_info is None


def test_guardrail_runs_before_the_planner():
    assert travel_scope.run_in_parallel is False


def test_classifier_sees_recent_history_for_follow_ups():
    items = [
        {"role": "user", "content": "7 nights in Thailand"},
        {"role": "assistant", "content": [{"type": "output_text", "text": "Here you go"}]},
        {"role": "user", "content": [{"type": "input_text", "text": "make it cheaper"}]},
    ]
    prompt = classifier_prompt(items)
    assert "- 7 nights in Thailand" in prompt
    assert prompt.endswith("LATEST user message:\nmake it cheaper")
    assert classifier_prompt("hi") == "LATEST user message:\nhi"


def test_notice_closes_when_a_travel_answer_arrives():
    ctx = TurnContext(open_surfaces=set())
    render_notice(ctx, "off_topic", "maths homework", "Plan a trip to Greece")
    ctx.drain()
    render_itinerary(ctx, thailand())
    assert {"version": "1.0", "deleteSurface": {"surfaceId": "notice"}} in ctx.drain()
    assert ctx.open_surfaces == {"itinerary"}
