"""The server streams A2UI produced by a UI tool in the middle of a turn.

The model run is faked, so this runs without an API key.
"""

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from travel_agent import server
from travel_agent.ui_tools import render_hotels


class FakeStreamedRun:
    """Mimics RunResultStreaming: the 'model' calls show_hotels, then says one sentence."""

    def __init__(self, ctx):
        self.ctx = ctx

    async def stream_events(self):
        yield SimpleNamespace(type="run_item_stream_event", name="tool_called",
                              item=SimpleNamespace(raw_item=SimpleNamespace(name="show_hotels")))
        render_hotels(self.ctx, city="Lisbon", nights=2, travelers=None)
        yield SimpleNamespace(type="run_item_stream_event", name="tool_output", item=None)
        yield SimpleNamespace(type="raw_response_event",
                              data=server.ResponseTextDeltaEvent.model_construct(delta="Pick one!"))


def _events(resp):
    return [json.loads(line[5:]) for line in resp.text.splitlines() if line.startswith("data:")]


def test_hotel_request_without_dates_streams_cards(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(server.Runner, "run_streamed",
                        lambda agent, text, session, context: FakeStreamedRun(context))
    client = TestClient(server.app)

    client.post("/api/turn", json={"sessionId": "ui1", "input": {"type": "start"}})
    events = _events(client.post("/api/turn", json={
        "sessionId": "ui1", "input": {"type": "text", "text": "book a hotel for me lisbon for 2 days"}}))

    types = [e["type"] for e in events]
    assert events[0] == {"type": "status", "text": "🛡️ Checking your request…"}
    assert {"type": "status", "text": "🏨 Finding hotels…"} in events
    assert types.index("a2ui") < types.index("text"), "UI should arrive before the reply text"
    a2ui = [e["message"] for e in events if e["type"] == "a2ui"]
    assert a2ui[0] == {"version": "1.0", "deleteSurface": {"surfaceId": "welcome"}}
    assert a2ui[1]["createSurface"]["surfaceId"] == "hotels"
    assert types[-1] == "done"

    # The hotels are remembered for the session, so "Select" can refer to them by id.
    assert any(k.startswith("HT-LIS-") for k in server.sessions.get("ui1").memory["hotels"])


class BlockedRun:
    """Mimics a run whose input guardrail tripped before the planner started."""

    def __init__(self, verdict):
        self.verdict = verdict

    async def stream_events(self):
        from agents import GuardrailFunctionOutput, InputGuardrailResult, InputGuardrailTripwireTriggered

        from travel_agent.guardrails import travel_scope

        raise InputGuardrailTripwireTriggered(InputGuardrailResult(
            guardrail=travel_scope,
            output=GuardrailFunctionOutput(output_info=self.verdict, tripwire_triggered=True)))
        yield  # pragma: no cover  (makes this an async generator)


def test_off_topic_message_gets_the_notice_surface(monkeypatch):
    from travel_agent.guardrails import ScopeVerdict

    verdict = ScopeVerdict(category="off_topic", topic="fixing Python code",
                           suggestion="Plan a 3-day tech trip to San Francisco")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(server.Runner, "run_streamed", lambda agent, text, session, context: BlockedRun(verdict))
    client = TestClient(server.app)

    client.post("/api/turn", json={"sessionId": "g1", "input": {"type": "start"}})
    events = _events(client.post("/api/turn", json={
        "sessionId": "g1", "input": {"type": "text", "text": "fix my python code"}}))

    a2ui = [e["message"] for e in events if e["type"] == "a2ui"]
    assert a2ui[0] == {"version": "1.0", "deleteSurface": {"surfaceId": "welcome"}}
    assert a2ui[1]["createSurface"]["surfaceId"] == "notice"
    data = next(m for m in a2ui if "updateDataModel" in m)["updateDataModel"]["value"]
    assert data["topic"] == "fixing Python code"
    assert data["suggestions"][0]["prompt"] == "Plan a 3-day tech trip to San Francisco"
    assert any(e["type"] == "text" and "travel" in e["delta"] for e in events)
    assert not any(e["type"] == "error" for e in events)

    # Dismiss is handled locally: notice goes, welcome comes back.
    events = _events(client.post("/api/turn", json={"sessionId": "g1", "input": {"type": "action", "action": {
        "name": "dismiss_notice", "surfaceId": "notice", "sourceComponentId": "n_dismiss", "context": {}}}}))
    a2ui = [e["message"] for e in events if e["type"] == "a2ui"]
    assert a2ui[0] == {"version": "1.0", "deleteSurface": {"surfaceId": "notice"}}
    assert a2ui[1]["createSurface"]["surfaceId"] == "welcome"
