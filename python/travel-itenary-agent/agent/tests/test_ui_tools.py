"""UI tools. No LLM needed: we test the plain-Python cores and the schemas."""

from datetime import date

from travel_agent.ui_tools import (
    TurnContext,
    render_booking_form,
    render_confirmation,
    render_hotels,
    render_itinerary,
    render_trip_form,
    render_welcome,
    show_hotels,
    show_itinerary,
    show_trip_form,
)

from .samples import thailand

TODAY = date(2027, 3, 1)


def _ctx():
    return TurnContext(open_surfaces=set(), today=TODAY)


def _data(msgs, surface=None):
    return next(m for m in msgs if "updateDataModel" in m
                and (surface is None or m["updateDataModel"]["surfaceId"] == surface))["updateDataModel"]["value"]


def _kinds(msgs):
    return [next(k for k in m if k != "version") for m in msgs]


# --- trip form (optional now) ---

def test_trip_form_prefills_and_only_destination_matters():
    ctx = _ctx()
    result = render_trip_form(ctx, destination="Lisbon", travelers=3, interests=["food"])
    trip = _data(ctx.outbox)["trip"]
    assert trip["destination"] == "Lisbon" and trip["travelers"] == 3 and trip["interests"] == ["food"]
    assert "Only the destination is required" in result


def test_trip_form_sanitises_bad_model_output():
    ctx = _ctx()
    render_trip_form(ctx, start_date="2027-02-01", end_date="next friday", travelers=40, budget_usd=10)
    trip = _data(ctx.outbox)["trip"]
    assert trip["startDate"] == "" and trip["endDate"] == ""
    assert trip["travelers"] == 8 and trip["budget"] == 500


def test_surface_created_once_then_only_updated():
    ctx = _ctx()
    render_trip_form(ctx, destination="Paris")
    first = ctx.drain()
    render_trip_form(ctx, destination="Tokyo")
    second = ctx.drain()
    assert "createSurface" in _kinds(first) and "createSurface" not in _kinds(second)
    assert _data(second)["trip"]["destination"] == "Tokyo"


# --- itinerary: no dates, no origin ---

def test_itinerary_without_dates_replaces_welcome():
    ctx = _ctx()
    render_welcome(ctx)
    ctx.drain()
    result = render_itinerary(ctx, thailand())
    msgs = ctx.drain()
    assert msgs[0] == {"version": "1.0", "deleteSurface": {"surfaceId": "welcome"}}
    assert _kinds(msgs)[1:] == ["createSurface", "updateComponents", "updateDataModel", "updateDataModel"]
    assert ctx.open_surfaces == {"itinerary"}
    assert "Bangkok, Chiang Mai, Phuket" in result


def test_itinerary_refinement_is_data_only():
    ctx = _ctx()
    render_itinerary(ctx, thailand())
    ctx.drain()
    changed = thailand().model_copy(update={"title": "Thailand, slowly"})
    result = render_itinerary(ctx, changed)
    msgs = ctx.drain()
    assert set(_kinds(msgs)) == {"updateDataModel"}, "no components re-sent"
    assert _data(msgs)["title"] == "Thailand, slowly"
    assert "updated in place" in result


def test_itinerary_sanitises_numbers_and_renumbers_days():
    bad = thailand().model_copy(update={"nights": 500, "travelers": 0, "est_budget_per_person_usd": -5})
    bad.days[2].day = 9
    ctx = _ctx()
    render_itinerary(ctx, bad)
    data = _data(ctx.outbox)
    assert data["nights"] == 30 and data["budget"] == 0
    assert [d["label"] for d in data["days"]] == ["Day 1", "Day 2", "Day 3"]


# --- hotels → booking → confirmation ---

def test_hotels_need_only_city_and_nights():
    ctx = _ctx()
    result = render_hotels(ctx, city="Lisbon", nights=2, travelers=None)
    data = _data(ctx.outbox, "hotels")
    assert "flexible dates" in data["subtitle"] and "2 nights" in data["subtitle"]
    assert len(ctx.hotels) == 4 and "HT-LIS-" in result


def test_full_booking_flow():
    ctx = _ctx()
    render_hotels(ctx, city="Lisbon", nights=2, travelers=2)
    hotel = next(iter(ctx.hotels.values()))
    ctx.drain()

    render_booking_form(ctx, hotel.id)
    form = ctx.drain()
    assert _data(form)["total"] == hotel.total_price

    result = render_confirmation(ctx, hotel_id=hotel.id, guest_name="Ana", email="ana@example.com",
                                 guests=2, check_in=None, breakfast=True)
    done = ctx.drain()
    assert "createSurface" not in _kinds(done), "same booking surface, new root"
    assert _data(done)["total"] == hotel.total_price + 15 * 2 * 2
    assert _data(done)["reference"].startswith("WND-")
    assert ctx.open_surfaces == {"booking"}, "hotel list closed after booking"
    assert "WND-" in result


def test_unknown_hotel_is_reported_to_the_model():
    ctx = _ctx()
    assert "Unknown hotel" in render_booking_form(ctx, "HT-NOPE-1")
    assert ctx.outbox == []


# --- schemas ---

def test_tool_schemas_are_strict():
    for tool in (show_itinerary, show_hotels, show_trip_form):
        schema = tool.params_json_schema
        assert tool.strict_json_schema
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
    activity = show_itinerary.params_json_schema["$defs"]["Activity"]
    assert activity["properties"]["slot"]["enum"] == ["Morning", "Afternoon", "Evening"]
