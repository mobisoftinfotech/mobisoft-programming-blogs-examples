"""Booking: a guest-details form, then a confirmation on the *same* surface.

A2UI ideas shown here:

* **Validation on the client.** ``required`` and ``email`` checks keep "Confirm" disabled
  until the form is valid, without a round-trip.
* **Two-way binding.** Inputs write to ``/booking/...``; the button's context reads them back.
* **Replacing a view in place.** The confirmation sends a new ``root`` component through
  ``updateComponents``. The surface stays; what it shows changes.
"""

from __future__ import annotations

from .. import messages as m
from ...tools import Hotel

SURFACE_ID = "booking"
CONFIRM_ACTION = "confirm_booking"
CANCEL_ACTION = "cancel_booking"


def build_booking_form(hotel: Hotel, travelers: int) -> list[m.Message]:
    P = "/booking"
    required = lambda path, msg: m.check(m.call("required", value=m.bind(path)), msg)  # noqa: E731
    components = [
        m.card("root", "b_col"),
        m.column("b_col", ["b_title", "b_hotel", "b_hotel_meta", "b_price", "b_divider", "b_name", "b_email",
                           "b_guests", "b_checkin", "b_breakfast", "b_actions"]),
        m.text("b_title", "🛎️ Complete your booking", variant="h3"),
        m.text("b_hotel", m.bind(f"{P}/hotelName"), variant="h4"),
        m.text("b_hotel_meta", m.bind(f"{P}/hotelMeta"), variant="caption"),
        m.row("b_price", ["b_price_label", "b_price_value"], align="center"),
        m.text("b_price_label", m.bind(f"{P}/priceLabel")),
        m.text("b_price_value", m.currency(m.bind(f"{P}/total"))),
        m.divider("b_divider"),
        m.text_field("b_name", "Guest name", m.bind(f"{P}/guestName"),
                     checks=[required(f"{P}/guestName", "Please enter the guest name.")]),
        m.text_field("b_email", "Email for the confirmation", m.bind(f"{P}/email"),
                     checks=[m.check(m.call("email", value=m.bind(f"{P}/email")), "Enter a valid email.")]),
        m.slider("b_guests", m.fmt(f"Guests: ${{{P}/guests}}"), m.bind(f"{P}/guests"), min_=1, max_=8),
        m.date_input("b_checkin", "Check-in date (optional, leave empty for flexible)", m.bind(f"{P}/checkIn")),
        m.checkbox("b_breakfast", "Add breakfast (+$15 per guest per night)", m.bind(f"{P}/breakfast")),
        m.row("b_actions", ["b_cancel", "b_confirm"], justify="end", align="center"),
        m.button("b_cancel", "b_cancel_label", CANCEL_ACTION, borderless=True),
        m.text("b_cancel_label", "Cancel"),
        m.button(
            "b_confirm",
            "b_confirm_label",
            CONFIRM_ACTION,
            {
                "hotelId": hotel.id,  # literal: fixed when the form was built
                "guestName": m.bind(f"{P}/guestName"),
                "email": m.bind(f"{P}/email"),
                "guests": m.bind(f"{P}/guests"),
                "checkIn": m.bind(f"{P}/checkIn"),
                "breakfast": m.bind(f"{P}/breakfast"),
            },
            primary=True,
            checks=[
                required(f"{P}/guestName", "Please enter the guest name."),
                m.check(m.call("email", value=m.bind(f"{P}/email")), "Enter a valid email."),
            ],
        ),
        m.text("b_confirm_label", "Confirm booking"),
    ]
    data = {
        "hotelName": hotel.name,
        "hotelMeta": f"{'★' * hotel.stars} · {hotel.neighborhood}, {hotel.city} · rated {hotel.rating}",
        "priceLabel": f"{hotel.nights} night{'s' * (hotel.nights != 1)} × ${hotel.price_per_night} =",
        "total": hotel.total_price,
        "guestName": "",
        "email": "",
        "guests": travelers,
        "checkIn": hotel.check_in,
        "breakfast": False,
    }
    return [
        m.create_surface(SURFACE_ID),
        m.update_components(SURFACE_ID, components),
        m.update_data_model(SURFACE_ID, data, P),
    ]


def build_confirmation(*, reference: str, hotel: Hotel, guest_name: str, email: str, guests: int,
                       check_in: str, breakfast: bool, total: int) -> list[m.Message]:
    P = "/confirmation"
    stay = f"Check-in {check_in}" if check_in else "Flexible dates: we'll email you to pick them"
    components = [
        # A new root replaces the form: same surface, new view.
        m.card("root", "c_col"),
        m.column("c_col", ["c_head", "c_ref", "c_divider", "c_hotel", "c_meta", "c_stay", "c_guest", "c_extras",
                           "c_total_row", "c_actions"]),
        m.row("c_head", ["c_icon", "c_title"], align="center"),
        m.icon("c_icon", "check"),
        m.text("c_title", "Booking confirmed", variant="h3"),
        m.text("c_ref", m.fmt(f"Reference: ${{{P}/reference}}"), variant="h5"),
        m.divider("c_divider"),
        m.text("c_hotel", m.bind(f"{P}/hotel"), variant="h4"),
        m.text("c_meta", m.bind(f"{P}/meta"), variant="caption"),
        m.text("c_stay", m.bind(f"{P}/stay")),
        m.text("c_guest", m.bind(f"{P}/guest")),
        m.text("c_extras", m.bind(f"{P}/extras"), variant="caption"),
        m.row("c_total_row", ["c_total_label", "c_total"], align="center"),
        m.text("c_total_label", "Total paid at the hotel:"),
        m.text("c_total", m.currency(m.bind(f"{P}/total"))),
        m.row("c_actions", ["c_new"], justify="end"),
        m.button("c_new", "c_new_label", "start_over"),
        m.text("c_new_label", "✨ Plan something else"),
    ]
    data = {
        "reference": reference,
        "hotel": hotel.name,
        "meta": f"{hotel.neighborhood}, {hotel.city} · {hotel.nights} night{'s' * (hotel.nights != 1)}",
        "stay": stay,
        "guest": f"👤 {guest_name} · {guests} guest{'s' * (guests != 1)} · confirmation sent to {email}",
        "extras": "🥐 Breakfast included" if breakfast else "Room only",
        "total": total,
    }
    return [
        m.create_surface(SURFACE_ID),
        m.update_components(SURFACE_ID, components),
        m.update_data_model(SURFACE_ID, data, P),
    ]
