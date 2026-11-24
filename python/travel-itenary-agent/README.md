# Wanderly: AI Travel Itinerary Planner with A2UI

Tutorial code for **"Generative UI Tutorial: Build an AI Travel Itinerary Planner Agent with A2UI"**.
An OpenAI agent plans trips and replies with **interactive UI** (A2UI v1.0) that a React app renders.

| Part | Stack |
|---|---|
| `agent/` | Python 3.12+, OpenAI Agents SDK, FastAPI, Server-Sent Events |
| `client/` | React 19, Vite, `@a2ui/web_core` 0.15 (protocol v1.0), `@a2ui/react` 0.15, `@a2ui/markdown-it` |

## Quick start

Prerequisites: [uv](https://docs.astral.sh/uv/), Node 24.15+ (or 22.22+), and an OpenAI API key.

```bash
# 1. Agent
cd agent
cp .env.example .env          # add OPENAI_API_KEY
uv sync
uv run travel-server          # http://127.0.0.1:8000

# 2. Client (new terminal)
cd client
npm install
npm run dev                   # http://localhost:5173
```

Open http://localhost:5173. The left panel shows UI the agent sends as A2UI messages; the right panel is the chat.

No dates, departure city or budget are needed. Type (or tap on the welcome screen):

| You say | The agent shows (all A2UI) |
|---|---|
| **"Prepare me an itinerary for 7 nights and 8 days for Thailand"** | A day-by-day itinerary: route, stops, 8 day cards, tips, estimated budget |
| **"Book a hotel for me in Lisbon for 2 days"** | Hotel cards with **Select** buttons → booking form → confirmation |
| *Clicks "🏨 Find hotels" on a stop* | Hotels for that stop's city and nights |
| *Clicks "💸 Cheaper" or types a change* | The same itinerary, updated in place (data only) |

What each surface demonstrates:

| Surface | A2UI features |
|---|---|
| `welcome` | Template list of buttons; each action context reads its own item |
| `itinerary` | Nested templates (days → activities), relative bindings, `formatCurrency`, data-only refinement, actions from inside templates, two-way bound text field |
| `hotels` | Templated cards, a per-card **Select** button whose context binds the card's `id` |
| `booking` | Inputs with `required` / `email` checks, slider, optional date, checkbox; then a new `root` replaces the form with a confirmation on the **same** surface |
| (all) | `deleteSurface` for screens that are no longer relevant; Cancel / Start over handled by the server without calling the model |

### A2UI v1.0

The agent speaks protocol **v1.0**. The client processes messages with `@a2ui/web_core/v1_0`.
`@a2ui/react` 0.15 has no v1.0 entry point yet, so surfaces are drawn with its v0.9 `<A2uiSurface>`.
Both catalogs share the same components, and the client tests run every surface through the v1.0
processor and renderer. Switch to `@a2ui/react/v1_0` once it ships.

What changed from v0.9 (all handled in `agent/travel_agent/a2ui/messages.py`):

| v0.9 | v1.0 |
|---|---|
| `"version": "v0.9"` | `"version": "1.0"` |
| `{"path": "/x"}`, `{"call": "fn"}` | `{"@path": "/x"}`, `{"@call": "fn"}` (template `children` keep `path`) |
| `theme` on `createSurface` | removed; the brand colour is `--a2ui-color-primary` in `client/src/styles.css` |
| ids like `it-day-title` | identifiers only: `it_day_title` (the builder rejects anything else) |
| `Text` variants `h1`–`h5` | `body` / `caption` only; headings are Markdown, rendered by `@a2ui/markdown-it` |

`client/package.json` uses `overrides` for two things: `@a2ui/markdown-it` 0.2.2 declares
`@a2ui/web_core ^0.14` (it works with 0.15), and its pinned `dompurify` 3.4.11 has known XSS
advisories, so it's raised to 3.4.17.

### Guardrails: out-of-scope questions get UI too

Every typed message first goes through an **input guardrail** (`agent/travel_agent/guardrails.py`,
OpenAI Agents SDK `@input_guardrail`, blocking). A small classifier labels it `travel`, `small_talk`,
`off_topic`, `unsafe` or `prompt_injection`. The last three trip the wire: the planner never runs,
and the agent shows the **`notice`** A2UI surface instead. It's one layout whose data and icon depend
on the case (ℹ️ off-topic, ⚠️ unsafe, 🔒 injection). It shows what you asked about, what Wanderly can do,
and one-tap travel requests, one tailored to your question ("Who won the 2022 World Cup?" →
"Plan a trip to Argentina…"). Follow-ups like "make it cheaper" use recent history and are not blocked.
Clicks in the UI skip the check. As a second layer, the planner's instructions tell it to call
`show_out_of_scope` if anything slips through. Set `GUARDRAIL_MODEL` to a small model to make the check faster.

The trip form (`show_trip_form`) is still there for users who name no destination or ask for a form.
Only the destination is required on it.

Chapter 2 only (terminal chat, no UI):

```bash
cd agent && uv run travel-cli
```

## Tests

```bash
cd agent && uv run pytest     # tools, A2UI builders, UI tools, golden file, API
cd agent && uv run pytest -m live   # real OpenAI call (needs OPENAI_API_KEY)
cd client && npm test         # golden files checked by the real A2UI v1.0 MessageProcessor
```

`agent/tests/golden/*.json` (one per surface) is the contract between the two halves. Python generates
the files and the client checks them with the official renderer: they must be valid, nested templates
must render, and templated buttons must send the right context. Regenerate them with
`UPDATE_GOLDEN=1 uv run pytest`.

## Progress

- [x] Ch 1: Setup
- [x] Ch 2: Plain-text agent with mock tools
- [x] Ch 3: First A2UI surface (trip form) over SSE + action round-trip
- [x] Ch 4: The agent drives the UI (`show_trip_form` tool, strict schema)
- [x] Ch 5–8 (most of them): itinerary, hotels, booking and confirmation as A2UI, no dates needed,
      templates + data binding, data-only refinement, `deleteSurface`
