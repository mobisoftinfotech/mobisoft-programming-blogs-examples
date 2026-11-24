"""HTTP API that streams A2UI messages and agent text over Server-Sent Events.

Start: a welcome surface with one-tap example requests.
The agent's UI tools (show_itinerary, show_hotels, ...) stream A2UI messages mid-turn.
Actions from the UI become agent turns, except pure UI ones (cancel, start over),
which the server handles itself.

    uv run travel-server            # http://127.0.0.1:8000

Protocol (kept small on purpose):

    POST /api/turn   {"sessionId": "...", "input": <Input>}
      Input = {"type": "start"}                       -> show the welcome surface
            | {"type": "text",   "text": "..."}        -> chat with the agent
            | {"type": "action", "action": {...}}      -> an A2UI action from the client

    Response: text/event-stream, one JSON object per `data:` line
      {"type": "a2ui",   "message": <A2UI v1.0 message>}
      {"type": "status", "text": "Searching flights…"}
      {"type": "text",   "delta": "..."}               (streamed agent text)
      {"type": "error",  "message": "..."}
      {"type": "done"}
"""

from __future__ import annotations

import json
import logging
import os
from collections import OrderedDict
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal

from agents import InputGuardrailTripwireTriggered, Runner, SQLiteSession
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .agent import build_agent
from .a2ui import A2UI_VERSION
from .a2ui.surfaces import booking, hotels, itinerary, notice, trip_form, welcome
from .config import settings
from .guardrails import ScopeVerdict
from .ui_tools import TurnContext, render_notice, render_welcome

log = logging.getLogger("travel_agent")

TOOL_STATUS = {
    "search_flights": "✈️ Searching flights…",
    "search_hotels": "🏨 Finding hotels…",
    "get_attractions": "🗺️ Looking up things to do…",
    "get_weather": "🌤️ Checking the weather…",
    "show_trip_form": "📝 Preparing your trip form…",
    "show_itinerary": "🗺️ Drawing your itinerary…",
    "show_hotels": "🏨 Finding hotels…",
    "show_booking_form": "🛎️ Preparing the booking form…",
    "confirm_booking": "✅ Confirming your booking…",
    "show_out_of_scope": "🧭 Steering back to travel…",
}

NOTICE_REPLY = {
    "off_topic": "That's outside what I can help with. I'm all about travel. Here are some ideas instead.",
    "unsafe": "Sorry, I can't help with that. I'm happy to plan a safe trip for you.",
    "prompt_injection": "I'll stick to travel planning. Here's what I can do for you.",
}


# --- request models -------------------------------------------------------------

class StartInput(BaseModel):
    type: Literal["start"]


class TextInput(BaseModel):
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=4000)


class ClientAction(BaseModel):
    """The action payload emitted by the A2UI renderer (v1.0)."""

    name: str = Field(max_length=100)
    surfaceId: str = Field(max_length=100)
    sourceComponentId: str = Field(max_length=100)
    timestamp: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


class ActionInput(BaseModel):
    type: Literal["action"]
    action: ClientAction


class TurnRequest(BaseModel):
    sessionId: str = Field(min_length=1, max_length=100)
    input: Annotated[StartInput | TextInput | ActionInput, Field(discriminator="type")]


# --- sessions (in-memory; swap for Redis/DB in production) ------------------------

class SessionState:
    """Everything we remember about one browser tab."""

    def __init__(self, session_id: str) -> None:
        self.history = SQLiteSession(session_id)  # conversation memory for the agent
        self.open_surfaces: set[str] = set()  # A2UI surfaces the client currently has
        self.memory: dict[str, Any] = {}  # e.g. hotels shown, so actions can refer to them by id

    def context(self) -> TurnContext:
        return TurnContext(open_surfaces=self.open_surfaces, memory=self.memory)


class SessionStore:
    def __init__(self, max_sessions: int = 500) -> None:
        self._sessions: OrderedDict[str, SessionState] = OrderedDict()
        self._max = max_sessions

    def get(self, session_id: str) -> SessionState:
        if session_id in self._sessions:
            self._sessions.move_to_end(session_id)
        else:
            self._sessions[session_id] = SessionState(session_id)
            if len(self._sessions) > self._max:
                self._sessions.popitem(last=False)
        return self._sessions[session_id]


sessions = SessionStore()


# --- turn handling ------------------------------------------------------------------

def _event(payload: dict[str, Any]) -> dict[str, str]:
    return {"event": "message", "data": json.dumps(payload, ensure_ascii=False)}


def action_to_prompt(action: ClientAction) -> str:
    """Turn an A2UI action into a message the LLM can understand.

    An action is a structured user message: the button says *what*, the context says *with what*.
    """
    c = action.context
    match action.name:
        case welcome.SUGGEST_ACTION:
            return str(c.get("prompt", ""))[:500] or "Suggest a trip for me"
        case trip_form.SUBMIT_ACTION:
            return f"I submitted the trip form. Plan my trip with these details (JSON): {json.dumps(c, ensure_ascii=False)}"
        case itinerary.REFINE_ACTION:
            return f"Please adjust the itinerary: {str(c.get('change', ''))[:500]}"
        case itinerary.FIND_HOTELS_ACTION:
            return f"Show me hotels in {str(c.get('city', ''))[:60]} for {c.get('nights', 2)} nights."
        case hotels.SELECT_ACTION:
            return f"I selected hotel {str(c.get('hotelId', ''))[:40]}. Show the booking form."
        case booking.CONFIRM_ACTION:
            return f"Confirm my booking with these details (JSON): {json.dumps(c, ensure_ascii=False)}"
    return f"I triggered the UI action '{action.name}' with context {json.dumps(c, ensure_ascii=False)}"


# Actions that only change the UI: no need to wake the model.
LOCAL_ACTIONS = {booking.CANCEL_ACTION, notice.DISMISS_ACTION, "start_over"}


def handle_local_action(action: ClientAction, ctx: TurnContext) -> None:
    if action.name == booking.CANCEL_ACTION:
        ctx.close(booking.SURFACE_ID)
    elif action.name == notice.DISMISS_ACTION:
        ctx.close(notice.SURFACE_ID)
        if not ctx.open_surfaces:
            render_welcome(ctx)
    elif action.name == "start_over":
        ctx.close(*sorted(ctx.open_surfaces))
        render_welcome(ctx)


def _a2ui_events(ctx: TurnContext) -> list[dict[str, str]]:
    return [_event({"type": "a2ui", "message": msg}) for msg in ctx.drain()]


async def run_agent(text: str, session_id: str, *, from_ui: bool = False) -> AsyncIterator[dict[str, str]]:
    if not os.getenv("OPENAI_API_KEY"):
        yield _event({"type": "error", "message": "OPENAI_API_KEY is not set on the agent server."})
        return
    state = sessions.get(session_id)
    ctx = state.context()
    ctx.from_ui = from_ui
    if not from_ui:
        yield _event({"type": "status", "text": "🛡️ Checking your request…"})
    try:
        async for ev in _stream_run(text, state, ctx):
            yield ev
    except InputGuardrailTripwireTriggered as exc:
        # The planner never ran. Answer with UI: the out-of-scope notice.
        verdict = exc.guardrail_result.output.output_info
        kind = verdict.category if isinstance(verdict, ScopeVerdict) else "off_topic"
        log.info("guardrail blocked a %s message", kind)
        render_notice(ctx, kind,  # type: ignore[arg-type]
                      getattr(verdict, "topic", ""), getattr(verdict, "suggestion", ""))
        for out in _a2ui_events(ctx):
            yield out
        yield _event({"type": "text", "delta": NOTICE_REPLY.get(kind, NOTICE_REPLY["off_topic"])})


async def _stream_run(text: str, state: SessionState, ctx: TurnContext) -> AsyncIterator[dict[str, str]]:
    result = Runner.run_streamed(build_agent(), text, session=state.history, context=ctx)
    said_something = new_paragraph = False
    async for ev in result.stream_events():
        if ev.type == "raw_response_event" and isinstance(ev.data, ResponseTextDeltaEvent):
            # Text from a later model response (after a tool call) starts a new line.
            delta = ("\n" if new_paragraph else "") + ev.data.delta
            said_something, new_paragraph = True, False
            yield _event({"type": "text", "delta": delta})
        elif ev.type == "run_item_stream_event" and ev.name == "tool_called":
            tool = getattr(ev.item.raw_item, "name", "")
            yield _event({"type": "status", "text": TOOL_STATUS.get(tool, f"Running {tool}…")})
        elif ev.type == "run_item_stream_event" and ev.name == "tool_output":
            new_paragraph = said_something
            # A UI tool just ran: send its A2UI messages now, before the model keeps talking.
            for out in _a2ui_events(ctx):
                yield out
    for out in _a2ui_events(ctx):  # anything left over
        yield out


async def handle_turn(req: TurnRequest) -> AsyncIterator[dict[str, str]]:
    try:
        match req.input:
            case StartInput():
                # Same path the agent's UI tools use, so surface tracking stays correct.
                ctx = sessions.get(req.sessionId).context()
                render_welcome(ctx)
                for out in _a2ui_events(ctx):
                    yield out
            case TextInput(text=text):
                async for ev in run_agent(text, req.sessionId):
                    yield ev
            case ActionInput(action=action):
                log.info("action %s from %s/%s", action.name, action.surfaceId, action.sourceComponentId)
                if action.name in LOCAL_ACTIONS:
                    ctx = sessions.get(req.sessionId).context()
                    handle_local_action(action, ctx)
                    for out in _a2ui_events(ctx):
                        yield out
                else:
                    async for ev in run_agent(action_to_prompt(action), req.sessionId, from_ui=True):
                        yield ev
    except Exception as exc:  # report to the client instead of silently dropping the stream
        log.exception("turn failed")
        yield _event({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
    yield _event({"type": "done"})


# --- app ------------------------------------------------------------------------------

app = FastAPI(title="Wanderly travel agent (A2UI v1.0)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "a2ui": A2UI_VERSION, "openaiKey": bool(os.getenv("OPENAI_API_KEY"))}


@app.post("/api/turn")
async def turn(req: TurnRequest) -> EventSourceResponse:
    return EventSourceResponse(handle_turn(req))


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run("travel_agent.server:app", host=settings.host, port=settings.port, reload=True)


if __name__ == "__main__":
    main()
