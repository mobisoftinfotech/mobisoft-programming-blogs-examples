"""UI as tools: the LLM drives the interface through typed tool calls.

The model never writes A2UI JSON. It calls a tool such as ``show_itinerary(...)``
whose arguments are enforced by OpenAI's strict JSON schema. The tool:

1. sanitises the arguments (the model can still pick a past date, etc.),
2. builds deterministic A2UI v1.0 messages with our surface builders,
3. puts them in the turn's *outbox*, which the server streams to the client,
4. returns a short result string, so the model knows what the user now sees.

Nothing here needs dates or a departure city: "7 nights in Thailand" and
"a hotel in Lisbon for 2 nights" are complete requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from agents import RunContextWrapper, function_tool

from . import tools
from .a2ui import Message
from .a2ui import messages as m
from .a2ui.surfaces import booking, hotels, itinerary, notice, trip_form, welcome
from .a2ui.surfaces.itinerary import Day, Itinerary, Stop
from .tools import Hotel
from .tools._data import seeded_rng

Interest = Literal["culture", "food", "outdoors", "landmarks", "nightlife"]


@dataclass
class TurnContext:
    """Per-turn state shared by the UI tools and the server.

    ``open_surfaces`` and ``memory`` live as long as the browser session. A surface may
    only be created once (re-creating it is an A2UI integrity error), so after the first
    time we send only ``updateComponents`` / ``updateDataModel``.
    """

    open_surfaces: set[str]
    memory: dict[str, Any] = field(default_factory=dict)
    outbox: list[Message] = field(default_factory=list)
    today: date = field(default_factory=date.today)
    # True when this turn comes from a click in our own UI (the guardrail skips those).
    from_ui: bool = False

    def emit(self, messages: list[Message]) -> None:
        for msg in messages:
            if "createSurface" in msg:
                surface_id = msg["createSurface"]["surfaceId"]
                if surface_id in self.open_surfaces:
                    continue  # already on screen: send only the updates that follow
                self.open_surfaces.add(surface_id)
            elif "deleteSurface" in msg:
                surface_id = msg["deleteSurface"]["surfaceId"]
                if surface_id not in self.open_surfaces:
                    continue  # nothing to delete
                self.open_surfaces.discard(surface_id)
            self.outbox.append(msg)

    def close(self, *surface_ids: str) -> None:
        self.emit([m.delete_surface(s) for s in surface_ids])

    def drain(self) -> list[Message]:
        out, self.outbox = self.outbox, []
        return out

    @property
    def hotels(self) -> dict[str, Hotel]:
        """Hotels shown to the user this session, by id (so actions can refer to them)."""
        return self.memory.setdefault("hotels", {})


# --- argument sanitising -------------------------------------------------------

def _future_iso(value: str | None, today: date) -> str:
    """Keep a valid ISO date on or after today; otherwise leave the field empty."""
    if not value:
        return ""
    try:
        d = date.fromisoformat(value)
    except ValueError:
        return ""
    return d.isoformat() if d >= today else ""


def _clamp(value: int | None, lo: int, hi: int, default: int) -> int:
    return default if value is None else max(lo, min(hi, value))


def _cut(text: str, n: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


# --- welcome ---------------------------------------------------------------------

def render_welcome(ctx: TurnContext) -> None:
    ctx.emit(welcome.build_welcome())


# --- trip form (optional: only when the user wants to fill details in) -------------

def render_trip_form(
    ctx: TurnContext,
    *,
    origin: str | None = None,
    destination: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    travelers: int | None = None,
    budget_usd: int | None = None,
    interests: list[str] | None = None,
) -> str:
    """Plain-Python core of the ``show_trip_form`` tool (easy to unit-test)."""
    start = _future_iso(start_date, ctx.today)
    end = _future_iso(end_date, ctx.today)
    if start and end and end <= start:
        end = ""
    defaults = trip_form.TripFormDefaults(
        origin=(origin or "").strip()[:80],
        destination=(destination or "").strip()[:80],
        start_date=start,
        end_date=end,
        travelers=_clamp(travelers, 1, 8, 2),
        budget=_clamp(budget_usd, 500, 15000, 3000),
        interests=list(interests) if interests else ["culture", "food"],
    )
    ctx.close(welcome.SURFACE_ID, notice.SURFACE_ID)
    ctx.emit(trip_form.build_trip_form(defaults, min_date=ctx.today.isoformat()))
    shown = defaults.model_dump()
    return (
        f"The trip form is now on screen, pre-filled with {shown}. "
        + ("Destination is still empty. " if not defaults.destination else "")
        + "Only the destination is required; the user clicks 'Plan my trip'."
    )


@function_tool
def show_trip_form(
    ctx: RunContextWrapper[TurnContext],
    origin: str | None,
    destination: str | None,
    start_date: str | None,
    end_date: str | None,
    travelers: int | None,
    budget_usd: int | None,
    interests: list[Interest] | None,
) -> str:
    """Show (or update) an optional trip-details form, pre-filled with what you know.

    Only use it when the user has NOT named a destination, or explicitly asks for a form.
    If they named a destination, call show_itinerary or show_hotels instead.

    Args:
        origin: City the user departs from (optional).
        destination: Place the user wants to visit.
        start_date: Departure date, ISO YYYY-MM-DD, or null.
        end_date: Return date, ISO YYYY-MM-DD, or null.
        travelers: Number of travelers (1-8).
        budget_usd: Total trip budget in US dollars.
        interests: What the user enjoys.
    """
    return render_trip_form(
        ctx.context, origin=origin, destination=destination, start_date=start_date, end_date=end_date,
        travelers=travelers, budget_usd=budget_usd, interests=interests,
    )


# --- itinerary ---------------------------------------------------------------------

def render_itinerary(ctx: TurnContext, it: Itinerary) -> str:
    """Sanitise the model's plan, then show it (create once, then data-only updates)."""
    nights = _clamp(it.nights, 1, 30, 3)
    days = [
        Day(
            day=i + 1,
            location=_cut(d.location, 60),
            title=_cut(d.title, 80),
            activities=[a.model_copy(update={"title": _cut(a.title, 80), "description": _cut(a.description, 220),
                                             "est_cost_usd": max(0, a.est_cost_usd)})
                        for a in d.activities[:5]],
        )
        for i, d in enumerate(it.days[:31])
    ]
    clean = it.model_copy(update={
        "destination": _cut(it.destination, 60),
        "title": _cut(it.title, 90),
        "summary": _cut(it.summary, 400),
        "nights": nights,
        "travelers": _clamp(it.travelers, 1, 12, 2),
        "stops": [Stop(city=_cut(s.city, 50), nights=_clamp(s.nights, 1, 30, 1)) for s in it.stops[:8]],
        "days": days,
        "tips": [_cut(t, 200) for t in it.tips[:6]],
        "est_budget_per_person_usd": max(0, it.est_budget_per_person_usd),
    })
    first_time = itinerary.SURFACE_ID not in ctx.open_surfaces
    ctx.close(welcome.SURFACE_ID, notice.SURFACE_ID, trip_form.SURFACE_ID)
    msgs = itinerary.build_itinerary(clean)
    if not first_time:
        # The layout is identical every time; a refinement only needs new data.
        msgs = [x for x in msgs if "updateDataModel" in x]
    ctx.emit(msgs)
    return (
        f"The itinerary '{clean.title}' ({clean.nights} nights, {len(days)} days, stops: "
        f"{', '.join(s.city for s in clean.stops)}) is now on screen"
        + (" (updated in place)" if not first_time else "")
        + ". Each stop has a 'Find hotels' button; the user can also ask for changes."
    )


@function_tool
def show_itinerary(
    ctx: RunContextWrapper[TurnContext],
    destination: str,
    title: str,
    summary: str,
    nights: int,
    travelers: int,
    stops: list[Stop],
    days: list[Day],
    tips: list[str],
    est_budget_per_person_usd: int,
) -> str:
    """Show a complete day-by-day itinerary in the UI panel (replaces any previous one).

    Dates and departure city are NOT needed. Build the plan from your own travel knowledge.

    Args:
        destination: Country, region or city, e.g. "Thailand".
        title: Catchy title, e.g. "Thailand: Temples, Mountains & Islands".
        summary: Two sentences on the shape of the trip.
        nights: Number of nights. "N nights and N+1 days" means nights=N.
        travelers: Number of travelers (assume 2 if not said).
        stops: Base cities in order, with nights in each (nights add up to the total).
        days: One entry per day (nights + 1 days), each with 2-4 activities (Morning/Afternoon/Evening).
            Put travel between stops in the plan (kind "travel").
        tips: 3-5 short practical tips (transport, money, etiquette, weather, what to pack).
        est_budget_per_person_usd: Rough per-person cost excluding international flights.
    """
    it = Itinerary(destination=destination, title=title, summary=summary, nights=nights, travelers=travelers,
                   stops=stops, days=days, tips=tips, est_budget_per_person_usd=est_budget_per_person_usd)
    return render_itinerary(ctx.context, it)


# --- hotels ------------------------------------------------------------------------

def render_hotels(ctx: TurnContext, *, city: str, nights: int | None, travelers: int | None,
                  check_in: str | None = None) -> str:
    city = _cut(city, 60) or "Lisbon"
    nights = _clamp(nights, 1, 30, 2)
    travelers = _clamp(travelers, 1, 8, 2)
    start = _future_iso(check_in, ctx.today) or None
    found = tools.search_hotels(city, check_in=start, travelers=travelers, nights=nights)
    for h in found:
        ctx.hotels[h.id] = h
    ctx.close(welcome.SURFACE_ID, notice.SURFACE_ID, trip_form.SURFACE_ID)
    ctx.emit(hotels.build_hotels(found[0].city, found, travelers))
    listing = "; ".join(f"{h.id}: {h.name}, {h.stars}★, ${h.price_per_night}/night" for h in found)
    return f"{len(found)} hotels in {found[0].city} for {nights} nights are on screen ({listing}). " \
           "The user picks one with its Select button."


@function_tool
def show_hotels(
    ctx: RunContextWrapper[TurnContext],
    city: str,
    nights: int,
    travelers: int | None,
    check_in: str | None,
) -> str:
    """Search hotels and show them as cards the user can select. No dates needed.

    Args:
        city: City to stay in.
        nights: Number of nights. "for 2 days" means 2 nights.
        travelers: Number of guests, or null if unknown.
        check_in: ISO date YYYY-MM-DD only if the user gave one, otherwise null (flexible dates).
    """
    return render_hotels(ctx.context, city=city, nights=nights, travelers=travelers, check_in=check_in)


# --- booking -----------------------------------------------------------------------

def render_booking_form(ctx: TurnContext, hotel_id: str, travelers: int | None = None) -> str:
    hotel = ctx.hotels.get(hotel_id)
    if hotel is None:
        return f"Unknown hotel id {hotel_id!r}. Call show_hotels first."
    ctx.close(notice.SURFACE_ID)
    ctx.emit(booking.build_booking_form(hotel, _clamp(travelers, 1, 8, 2)))
    return f"The booking form for {hotel.name} is on screen. The user enters their name and email and confirms."


@function_tool
def show_booking_form(ctx: RunContextWrapper[TurnContext], hotel_id: str) -> str:
    """Show the guest-details form to book a hotel the user selected.

    Args:
        hotel_id: The id of a hotel from show_hotels, e.g. "HT-LIS-2".
    """
    return render_booking_form(ctx.context, hotel_id)


def render_confirmation(ctx: TurnContext, *, hotel_id: str, guest_name: str, email: str, guests: int,
                        check_in: str | None, breakfast: bool) -> str:
    hotel = ctx.hotels.get(hotel_id)
    if hotel is None:
        return f"Unknown hotel id {hotel_id!r}. Call show_hotels first."
    guests = _clamp(guests, 1, 8, 2)
    start = _future_iso(check_in, ctx.today)
    total = hotel.total_price + (15 * guests * hotel.nights if breakfast else 0)
    rng = seeded_rng("booking", hotel_id, guest_name, email)
    reference = "WND-" + "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    ctx.emit(booking.build_confirmation(
        reference=reference, hotel=hotel, guest_name=_cut(guest_name, 80), email=_cut(email, 120),
        guests=guests, check_in=start, breakfast=breakfast, total=total,
    ))
    ctx.close(hotels.SURFACE_ID)
    return f"Booked (demo, nothing was charged). Reference {reference}, {hotel.name}, total ${total}. " \
           "The confirmation is on screen."


@function_tool
def confirm_booking(
    ctx: RunContextWrapper[TurnContext],
    hotel_id: str,
    guest_name: str,
    email: str,
    guests: int,
    check_in: str | None,
    breakfast: bool,
) -> str:
    """Confirm a hotel booking (demo, no payment) and show the confirmation.

    Args:
        hotel_id: The hotel id from the booking form.
        guest_name: Guest name from the form.
        email: Email from the form.
        guests: Number of guests.
        check_in: ISO date, or null for flexible dates.
        breakfast: Whether breakfast was added.
    """
    return render_confirmation(ctx.context, hotel_id=hotel_id, guest_name=guest_name, email=email,
                               guests=guests, check_in=check_in, breakfast=breakfast)


# --- out of scope ---------------------------------------------------------------------

def render_notice(ctx: TurnContext, kind: notice.Kind, topic: str = "", suggestion: str = "") -> str:
    """Show the out-of-scope card (used by the guardrail and by the tool below)."""
    ctx.close(welcome.SURFACE_ID)
    ctx.emit(notice.build_notice(kind, _cut(topic, 60), _cut(suggestion, 120)))
    return "A notice explaining that this is outside travel planning, with travel suggestions, is on screen."


@function_tool
def show_out_of_scope(ctx: RunContextWrapper[TurnContext], topic: str, suggestion: str) -> str:
    """Politely decline a request that is not about travel, with a card of things you CAN do.

    Use it for anything unrelated to trips, destinations, hotels or bookings. Do not answer
    the unrelated question itself.

    Args:
        topic: What the user asked about, in 2-6 words.
        suggestion: A related travel request they might enjoy, written as the user would type it.
    """
    return render_notice(ctx.context, "off_topic", topic, suggestion)


UI_TOOLS = [show_itinerary, show_hotels, show_booking_form, confirm_booking, show_trip_form, show_out_of_scope]
