import json

from fastapi.testclient import TestClient

from travel_agent.server import ClientAction, action_to_prompt, app

client = TestClient(app)


def _events(resp):
    return [json.loads(line[5:]) for line in resp.text.splitlines() if line.startswith("data:")]


def _action(name, **context):
    return {"type": "action", "action": {"name": name, "surfaceId": "s", "sourceComponentId": "c", "context": context}}


def test_health():
    assert client.get("/api/health").json()["a2ui"] == "1.0"


def test_start_streams_welcome():
    resp = client.post("/api/turn", json={"sessionId": "t1", "input": {"type": "start"}})
    assert resp.status_code == 200
    events = _events(resp)
    a2ui = [e["message"] for e in events if e["type"] == "a2ui"]
    assert a2ui[0]["createSurface"]["surfaceId"] == "welcome"
    assert events[-1] == {"type": "done"}


def test_start_over_is_handled_without_the_model(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client.post("/api/turn", json={"sessionId": "t4", "input": {"type": "start"}})
    events = _events(client.post("/api/turn", json={"sessionId": "t4", "input": _action("start_over")}))
    a2ui = [e["message"] for e in events if e["type"] == "a2ui"]
    assert a2ui[0] == {"version": "1.0", "deleteSurface": {"surfaceId": "welcome"}}
    assert a2ui[1]["createSurface"]["surfaceId"] == "welcome"
    assert [e["type"] for e in events if e["type"] != "a2ui"] == ["done"]


def test_actions_become_plain_prompts():
    def p(name, **ctx):
        return action_to_prompt(ClientAction(name=name, surfaceId="s", sourceComponentId="c", context=ctx))

    assert p("suggest", prompt="7 nights in Thailand") == "7 nights in Thailand"
    assert p("find_hotels", city="Phuket", nights=3) == "Show me hotels in Phuket for 3 nights."
    assert p("select_hotel", hotelId="HT-LIS-2") == "I selected hotel HT-LIS-2. Show the booking form."
    assert p("refine_itinerary", change="cheaper").startswith("Please adjust the itinerary: cheaper")


def test_text_without_key_reports_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resp = client.post("/api/turn", json={"sessionId": "t2", "input": {"type": "text", "text": "hi"}})
    assert [e["type"] for e in _events(resp)] == ["error", "done"]


def test_rejects_bad_input():
    resp = client.post("/api/turn", json={"sessionId": "t3", "input": {"type": "nope"}})
    assert resp.status_code == 422
