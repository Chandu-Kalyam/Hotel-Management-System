"""Streamlit front end application for Hotel Management System.

This module connects the existing managers to a practical hotel workflow.
Business rules remain in the GuestManager, RoomManager, BookingManager, and
BillingManager classes; Streamlit is responsible only for input and display.
"""

from __future__ import annotations

# Used for reliable project-relative data paths and simple date controls.
from datetime import date, timedelta
from pathlib import Path

# Used for readable tabular data and safe display dictionaries.
from typing import Any

# Streamlit provides the web interface without adding another application layer.
import streamlit as st

# Existing domain managers perform validation and persistence.
from billing.billing_manager import BillingManager
from booking.booking_manager import BookingManager
from guest.guest import Guest
from guest.guest_manager import GuestManager
from room.room import DeluxeRoom, Room, StandardRoom, SuiteRoom
from room.room_manager import RoomManager
from storage.file_manager import FileManager, FileManagerError


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIRECTORY = PROJECT_ROOT / "data"
ROOM_STATUS_COLORS = {
    "Available": "#2f7d6d",
    "Reserved": "#b47b2c",
    "Occupied": "#9b4d5c",
    "Maintenance": "#687080",
}
BOOKING_STATUS_COLORS = {
    "Confirmed": "#b47b2c",
    "Checked-in": "#9b4d5c",
    "Checked-out": "#2f7d6d",
    "Cancelled": "#687080",
}
ROOM_PRICE_DEFAULTS = {"Standard": 2500.0, "Deluxe": 4000.0, "Suite": 6500.0}


def reset_widget_keys(keys: list[str]) -> None:
    """Remove successful-form values so the next render starts cleanly."""
    for key in keys:
        st.session_state.pop(key, None)


def reset_guest_delete_confirmation() -> None:
    """Clear deletion approval whenever the selected guest changes."""
    st.session_state["confirm_guest_delete"] = False


def reset_booking_cancel_confirmation() -> None:
    """Clear cancellation approval whenever the selected booking changes."""
    st.session_state["confirm_booking_cancel"] = False
    st.session_state.pop("cancel_booking_target", None)


def keep_checkout_after_check_in() -> None:
    """Move checkout to the next valid night when check-in moves forward."""
    check_in = st.session_state.get("new_check_in")
    check_out = st.session_state.get("new_check_out")
    if isinstance(check_in, date) and (
        not isinstance(check_out, date) or check_out <= check_in
    ):
        st.session_state["new_check_out"] = check_in + timedelta(days=1)


def refresh_after_success(message: str) -> None:
    """Show a success message after rerunning so the updated page is visible."""
    st.session_state["flash_success"] = message
    st.rerun()


def build_managers() -> tuple[
    FileManager,
    GuestManager,
    RoomManager,
    BookingManager,
    BillingManager,
]:
    """Construct all managers with one shared project-relative FileManager."""
    file_manager = FileManager(DATA_DIRECTORY)
    guest_manager = GuestManager(file_manager)
    room_manager = RoomManager(file_manager)
    booking_manager = BookingManager(guest_manager, room_manager, file_manager)
    billing_manager = BillingManager(booking_manager, room_manager, file_manager)
    return (
        file_manager,
        guest_manager,
        room_manager,
        booking_manager,
        billing_manager,
    )


def configure_page() -> None:
    """Set the browser title and the shared boutique-hotel visual style."""
    st.set_page_config(
        page_title="Hotel Management System",
        page_icon="H",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
            --navy: #172a3a;
            --ink: #24313b;
            --ivory: #fbfaf6;
            --gold: #b28a4b;
            --teal: #2f7d6d;
            --line: #e5e0d6;
        }
        .stApp { background: var(--ivory); color: var(--ink); }
        label, .stMarkdown, .stCaption, [data-testid="stWidgetLabel"] {
            color: var(--ink) !important;
        }
        input, textarea, [data-baseweb="select"] > div,
        [data-testid="stNumberInput"] input {
            background: #ffffff !important; color: var(--ink) !important;
            border-color: #b7c0c5 !important;
        }
        input::placeholder, textarea::placeholder { color: #68737b !important; }
        [data-baseweb="popover"], [role="listbox"] {
            background: #ffffff !important; color: var(--ink) !important;
        }
        [role="option"] { color: var(--ink) !important; }
        button[kind="primary"],
        [data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: var(--navy) !important;
            color: #ffffff !important;
            border: 1px solid var(--navy) !important;
        }
        [data-testid="stAlert"] { border-left-color: var(--gold); }
        [data-testid="stSidebar"] {
            background: var(--navy);
            border-right: 1px solid #233e50;
        }
        [data-testid="stSidebar"] * { color: #f7f1e6; }
        [data-testid="stSidebar"] .stRadio label { padding: 0.35rem 0; }
        h1, h2, h3 { color: var(--navy); letter-spacing: -0.02em; }
        .hero {
            background: var(--navy); color: #f8f2e8; padding: 1.4rem 1.6rem;
            border-radius: 0.35rem; margin-bottom: 1.1rem;
            border-bottom: 4px solid var(--gold);
        }
        .hero h1 { color: #f8f2e8; margin: 0; font-size: 2rem; }
        .hero p { color: #d9e1e4; margin: 0.35rem 0 0; }
        .metric-card {
            background: #fff; border: 1px solid var(--line);
            border-top: 3px solid var(--gold); padding: 0.9rem 1rem;
            min-height: 6rem; box-shadow: 0 2px 10px rgba(23,42,58,.04);
        }
        .metric-label { color: #68737b; font-size: .82rem; }
        .metric-value { color: var(--navy); font-size: 1.7rem; font-weight: 700; }
        .status-pill {
            display: inline-block; padding: .18rem .55rem; border-radius: 1rem;
            color: var(--ink); font-size: .78rem; font-weight: 600;
        }
        div[data-testid="stForm"] {
            border: 1px solid var(--line); background: #fff; padding: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str) -> None:
    """Display a consistent page introduction."""
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def status_pill(status: str) -> str:
    """Return a colored HTML label for a stored operational or booking state."""
    color = {**ROOM_STATUS_COLORS, **BOOKING_STATUS_COLORS}.get(status, "#687080")
    text_color = "#24313b" if status in {"Reserved", "Confirmed"} else "#ffffff"
    return (
        f'<span class="status-pill" style="background:{color};color:{text_color}">'
        f"{status}</span>"
    )


def money(value: float) -> str:
    """Format a numeric value consistently as Indian rupees."""
    return f"INR {value:,.2f}"


def guests_table(guests: list[Guest]) -> list[dict[str, Any]]:
    """Convert guest objects into readable table rows."""
    return [
        {
            "Guest ID": guest.guest_id,
            "Name": guest.name,
            "Phone": guest.phone,
            "Email": guest.email,
        }
        for guest in guests
    ]


def rooms_table(rooms: list[Room]) -> list[dict[str, Any]]:
    """Convert rooms into rows without duplicating room logic."""
    return [
        {
            "Room": room.room_no,
            "Type": room.room_type,
            "Floor": room.floor,
            "Capacity": room.capacity,
            "Nightly price": money(room.calculate_nightly_price()),
            "Status": room.status,
        }
        for room in rooms
    ]


def booking_table(bookings: list[Any]) -> list[dict[str, Any]]:
    """Convert bookings into compact operational table rows."""
    return [
        {
            "Booking": booking.booking_id,
            "Guest": booking.guest_id,
            "Room": booking.room_no,
            "Check-in": booking.check_in.isoformat(),
            "Check-out": booking.check_out.isoformat(),
            "Guests": booking.guests_count,
            "Status": booking.status,
        }
        for booking in bookings
    ]


def render_dashboard(
    guest_manager: GuestManager,
    room_manager: RoomManager,
    booking_manager: BookingManager,
    billing_manager: BillingManager,
) -> None:
    """Render data-driven hotel operations overview."""
    page_header(
        "Hotel Management System",
        "Manage rooms, reservations, guests, and billing in one place.",
    )
    rooms = room_manager.list_rooms()
    bookings = booking_manager.list_bookings()
    today = date.today()
    active = [
        booking
        for booking in bookings
        if booking.status in booking_manager.ACTIVE_STATUSES
    ]
    metrics = [
        ("Total rooms", len(rooms)),
        ("Available", sum(room.status == "Available" for room in rooms)),
        ("Reserved", sum(room.status == "Reserved" for room in rooms)),
        ("Occupied", sum(room.status == "Occupied" for room in rooms)),
        ("Maintenance", sum(room.status == "Maintenance" for room in rooms)),
        ("Active bookings", len(active)),
    ]
    columns = st.columns(3)
    if len(metrics) > 3:
        columns = st.columns(3)
    for index, (label, value) in enumerate(metrics):
        column = columns[index % 3]
        with column:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{label}'
                f'</div><div class="metric-value">{value}</div></div>',
                unsafe_allow_html=True,
            )

    st.subheader("Today's movement")
    arrivals, departures = st.columns(2)
    with arrivals:
        arriving = [
            booking
            for booking in bookings
            if booking.check_in == today and booking.status == "Confirmed"
        ]
        st.write(f"Arrivals · {today.isoformat()}")
        if arriving:
            st.dataframe(booking_table(arriving), use_container_width=True, hide_index=True)
        else:
            st.caption("No confirmed arrivals today.")
    with departures:
        leaving = [
            booking
            for booking in bookings
            if booking.check_out == today and booking.status == "Checked-in"
        ]
        st.write(f"Departures · {today.isoformat()}")
        if leaving:
            st.dataframe(booking_table(leaving), use_container_width=True, hide_index=True)
        else:
            st.caption("No checked-in departures today.")

    left, right = st.columns(2)
    with left:
        st.subheader("Recent reservations")
        recent = list(reversed(bookings[-5:]))
        if recent:
            st.dataframe(booking_table(recent), use_container_width=True, hide_index=True)
        else:
            st.info("No reservations saved yet. Create the first booking from Booking Management.")
    with right:
        st.subheader("Billing summary")
        bills = billing_manager.list_bills()
        if bills:
            paid = [bill for bill in bills if bill.payment_status == "Paid"]
            st.metric("Recorded paid revenue", money(sum(bill.total for bill in paid)))
            st.caption(f"{len(paid)} completed bill(s) from saved records.")
        else:
            st.info("No completed bills yet. Revenue will appear after checkout.")
    st.caption(f"{len(guest_manager.list_guests())} guest record(s) saved.")


def render_guest_management(guest_manager: GuestManager) -> None:
    """Render guest registration, search, update, and protected deletion."""
    page_header("Guest management", "Keep front-desk guest records accurate and private.")
    with st.expander("Register a guest", expanded=not guest_manager.list_guests()):
        with st.form("add_guest"):
            left, right = st.columns(2)
            with left:
                guest_id = st.text_input("Guest ID", placeholder="G001", key="new_guest_id")
                name = st.text_input("Full name", key="new_guest_name")
                phone = st.text_input("Phone", key="new_guest_phone")
            with right:
                email = st.text_input("Email", key="new_guest_email")
                address = st.text_input("Address", key="new_guest_address")
                id_proof = st.text_input(
                    "ID proof reference",
                    help="Use fictional demonstration values only.",
                    key="new_guest_id_proof",
                )
            if st.form_submit_button("Register guest", type="primary"):
                try:
                    guest_manager.add_guest(Guest(guest_id, name, phone, email, address, id_proof))
                    st.success("Guest registered.")
                    reset_widget_keys(
                        [
                            "new_guest_id",
                            "new_guest_name",
                            "new_guest_phone",
                            "new_guest_email",
                            "new_guest_address",
                            "new_guest_id_proof",
                        ]
                    )
                    st.rerun()
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))

    guests = guest_manager.list_guests()
    search = st.text_input("Search guests", placeholder="ID, name, phone, or email")
    shown = guest_manager.find_guest(search) if search else guests
    st.subheader(f"Guest directory · {len(shown)} shown")
    if shown:
        st.dataframe(guests_table(shown), use_container_width=True, hide_index=True)
    else:
        st.info("No guest records match this search.")

    if guests:
        ids = [guest.guest_id for guest in guests]
        selected = st.selectbox(
            "Select a guest to update or delete",
            ids,
            key="selected_guest_id",
            on_change=reset_guest_delete_confirmation,
        )
        guest = guest_manager.get_guest(selected)
        if guest:
            st.caption(
                f"Selected guest: {guest.name} · {guest.phone} · {guest.email}"
            )
            with st.expander("Selected guest details"):
                st.write(f"Address: {guest.address}")
                st.write(f"ID proof reference: {guest.id_proof}")
            with st.expander("Update selected guest"):
                with st.form("update_guest"):
                    name = st.text_input("Name", guest.name, key=f"guest_name_{selected}")
                    phone = st.text_input("Phone", guest.phone, key=f"guest_phone_{selected}")
                    email = st.text_input("Email", guest.email, key=f"guest_email_{selected}")
                    address = st.text_input("Address", guest.address, key=f"guest_address_{selected}")
                    id_proof = st.text_input(
                        "ID proof reference",
                        guest.id_proof,
                        key=f"guest_id_proof_{selected}",
                    )
                    if st.form_submit_button("Save changes"):
                        try:
                            guest_manager.update_guest(selected, name, phone, email, address, id_proof)
                            refresh_after_success("Guest details updated.")
                        except (KeyError, ValueError, FileManagerError) as error:
                            st.error(str(error))
            confirm = st.checkbox(
                "I understand that this permanently deletes the selected guest.",
                key="confirm_guest_delete",
            )
            if st.button("Delete selected guest", disabled=not confirm):
                try:
                    guest_manager.delete_guest(selected)
                    st.success("Guest deleted.")
                    reset_widget_keys(["confirm_guest_delete", "selected_guest_id"])
                    st.rerun()
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))


def render_room_management(
    room_manager: RoomManager,
    booking_manager: BookingManager,
) -> None:
    """Render room inventory, filters, creation, and operational status edits."""
    page_header("Room management", "Maintain inventory and operational labels; dates belong to bookings.")
    rooms = room_manager.list_rooms()
    left, right = st.columns(2)
    with left:
        room_type = st.selectbox("Room type filter", ["All", "Standard", "Deluxe", "Suite"])
    with right:
        status = st.selectbox("Status filter", ["All", "Available", "Reserved", "Occupied", "Maintenance"])
    filtered = [
        room for room in rooms
        if (room_type == "All" or room.room_type == room_type)
        and (status == "All" or room.status == status)
    ]
    if filtered:
        st.dataframe(rooms_table(filtered), use_container_width=True, hide_index=True)
    else:
        st.info("No rooms match these filters.")

    with st.expander("Add a room"):
        new_type = st.selectbox(
            "Room type",
            ["Standard", "Deluxe", "Suite"],
            key="new_room_type",
        )
        with st.form("add_room"):
            room_no = st.number_input("Room number", min_value=1, step=1)
            floor = st.number_input("Floor", min_value=1, step=1)
            capacity = st.number_input("Capacity", min_value=1, step=1)
            base_price = st.number_input(
                "Nightly price (INR)",
                min_value=0.01,
                value=ROOM_PRICE_DEFAULTS[new_type],
                step=100.0,
                key=f"new_room_price_{new_type}",
            )
            if st.form_submit_button("Add room"):
                try:
                    room_class = {"Standard": StandardRoom, "Deluxe": DeluxeRoom, "Suite": SuiteRoom}[new_type]
                    room_manager.add_room(room_class(int(room_no), int(floor), int(capacity), base_price))
                    refresh_after_success("Room added.")
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))

    if rooms:
        selected = st.selectbox(
            "Select a room to update",
            [room.room_no for room in rooms],
            key="selected_room_no",
        )
        room = room_manager.get_room(selected)
        if room:
            active_booking = any(
                booking.room_no == room.room_no
                and booking.status in booking_manager.ACTIVE_STATUSES
                for booking in booking_manager.list_bookings()
            )
            if active_booking:
                st.info(
                    "Capacity and nightly price are locked while this room has "
                    "an active booking. Booking-derived status is protected."
                )
            with st.expander("Update room details and status"):
                with st.form("update_room"):
                    floor = st.number_input(
                        "Floor", min_value=1, value=room.floor, step=1
                    )
                    capacity = st.number_input(
                        "Capacity",
                        min_value=1,
                        value=room.capacity,
                        step=1,
                        disabled=active_booking,
                    )
                    price = st.number_input(
                        "Nightly price (INR)",
                        min_value=0.01,
                        value=float(room.base_price),
                        step=100.0,
                        disabled=active_booking,
                    )
                    new_status = st.selectbox(
                        "Operational status",
                        list(Room.VALID_STATUSES),
                        index=list(Room.VALID_STATUSES).index(room.status),
                        disabled=active_booking,
                    )
                    if st.form_submit_button("Save room changes"):
                        try:
                            room_manager.update_room(selected, int(floor), int(capacity), price)
                            room_manager.update_status(selected, new_status)
                            refresh_after_success("Room updated.")
                        except (KeyError, ValueError, FileManagerError) as error:
                            st.error(str(error))


def available_rooms(booking_manager: BookingManager, room_manager: RoomManager, check_in: date, check_out: date, guests_count: int) -> list[Room]:
    """Use existing manager APIs to find date-available rooms for the form."""
    candidates = room_manager.get_static_candidates(minimum_capacity=guests_count)
    return [
        room for room in candidates
        if booking_manager.is_room_available(room.room_no, check_in, check_out)
    ]


def render_booking_management(
    guest_manager: GuestManager,
    room_manager: RoomManager,
    booking_manager: BookingManager,
) -> None:
    """Render booking creation and valid lifecycle actions."""
    page_header("Booking management", "Reserve rooms by dates, not by global status labels.")
    guests = guest_manager.list_guests()
    today = date.today()
    if "new_check_in" not in st.session_state:
        st.session_state["new_check_in"] = today + timedelta(days=1)
    if "new_check_out" not in st.session_state:
        st.session_state["new_check_out"] = today + timedelta(days=2)

    st.subheader("Step A · Select stay dates")
    date_columns = st.columns(2)
    with date_columns[0]:
        check_in = st.date_input(
            "Check-in date",
            min_value=today,
            key="new_check_in",
            on_change=keep_checkout_after_check_in,
        )
    with date_columns[1]:
        check_out = st.date_input(
            "Check-out date",
            min_value=check_in + timedelta(days=1),
            key="new_check_out",
        )
    guests_count = st.number_input(
        "Number of guests",
        min_value=1,
        value=1,
        step=1,
        key="new_guests_count",
    )
    valid_range = check_out > check_in and check_in >= today
    nights = (check_out - check_in).days if valid_range else 0
    if valid_range:
        st.caption(
            f"Stay: {check_in.isoformat()} to {check_out.isoformat()} · "
            f"{nights} night(s). Room charges use occupied nights; checkout "
            "date is not counted as an occupied night."
        )
    else:
        st.error("Choose a checkout date later than the check-in date.")

    st.subheader("Step B · Show available rooms")
    room_options = (
        available_rooms(
            booking_manager,
            room_manager,
            check_in,
            check_out,
            int(guests_count),
        )
        if valid_range
        else []
    )
    room_labels = {
        room.room_no: (
            f"Room {room.room_no} · {room.room_type} · capacity {room.capacity} · "
            f"{money(room.calculate_nightly_price())} per night"
        )
        for room in room_options
    }
    if room_options:
        room_no = st.selectbox(
            "Available room",
            list(room_labels),
            format_func=lambda number: room_labels[number],
            key="new_room_no",
        )
        selected_room = room_manager.get_room(room_no)
        if selected_room is not None:
            estimate = selected_room.calculate_nightly_price() * nights
            st.caption(f"Indicative room charge estimate: {money(estimate)}")
    else:
        room_no = None
        st.info("No rooms are available for these dates and guest count.")

    st.subheader("Step C · Select guest and confirm")
    if not guests:
        st.warning("Register a guest before confirming a booking.")
        if st.button("Go to Guest Management"):
            st.session_state["front_desk_page"] = "Guest Management"
            st.rerun()
    else:
        guest_labels = {
            guest.guest_id: f"{guest.name} · Guest ID {guest.guest_id}"
            for guest in guests
        }
        guest_id = st.selectbox(
            "Guest",
            list(guest_labels),
            format_func=lambda value: guest_labels[value],
            key="new_booking_guest_id",
        )
        if room_no is not None and selected_room is not None and valid_range:
            st.caption(
                f"Booking summary · {guest_labels[guest_id]} · Room "
                f"{selected_room.room_no} ({selected_room.room_type}) · "
                f"{check_in.isoformat()} to {check_out.isoformat()} · "
                f"{nights} night(s) · Estimate {money(estimate)}"
            )
        with st.form("create_booking"):
            booking_id = st.text_input(
                "Booking ID", placeholder="B001", key="new_booking_id"
            )
            if st.form_submit_button(
                "Confirm booking",
                type="primary",
                disabled=room_no is None or not valid_range,
            ):
                try:
                    booking = booking_manager.create_booking(
                        booking_id,
                        guest_id,
                        int(room_no),
                        check_in,
                        check_out,
                        int(guests_count),
                    )
                    reset_widget_keys(
                        [
                            "new_booking_id",
                            "new_check_in",
                            "new_check_out",
                            "new_guests_count",
                            "new_room_no",
                            "new_booking_guest_id",
                        ]
                    )
                    refresh_after_success(
                        f"Booking {booking.booking_id} confirmed for room "
                        f"{booking.room_no}, {booking.check_in.isoformat()} to "
                        f"{booking.check_out.isoformat()} ({booking.calculate_nights()} night(s))."
                    )
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))

    bookings = booking_manager.list_bookings()
    search = st.text_input("Search bookings", placeholder="Booking ID, guest, room, or status")
    shown = booking_manager.find_booking(search) if search else bookings
    if shown:
        st.dataframe(booking_table(shown), use_container_width=True, hide_index=True)
    else:
        st.info("No bookings match this search.")
    eligible_check_ins = [
        booking
        for booking in bookings
        if booking.status == "Confirmed" and booking.check_in <= date.today()
    ]
    if eligible_check_ins:
        selected = st.selectbox(
            "Booking eligible for check-in",
            [booking.booking_id for booking in eligible_check_ins],
            key="selected_booking_id",
            on_change=reset_booking_cancel_confirmation,
        )
        booking = booking_manager.get_booking(selected)
        if booking:
            st.markdown(f"Current state: {status_pill(booking.status)}", unsafe_allow_html=True)
            if st.button("Check in guest"):
                try:
                    booking_manager.check_in_guest(selected)
                    refresh_after_success("Guest checked in.")
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))
    else:
        st.info("No confirmed bookings are eligible for check-in today.")

    confirmed_bookings = [
        booking for booking in bookings if booking.status == "Confirmed"
    ]
    if confirmed_bookings:
        cancel_target = st.selectbox(
            "Confirmed booking to cancel",
            [booking.booking_id for booking in confirmed_bookings],
            key="cancel_booking_id",
        )
        cancel_booking = booking_manager.get_booking(cancel_target)
        if cancel_booking and st.button("Cancel booking"):
            st.session_state["cancel_booking_target"] = cancel_target
        if (
            cancel_booking
            and st.session_state.get("cancel_booking_target") == cancel_target
        ):
            st.warning(
                f"Confirm cancellation of booking {cancel_target} for room "
                f"{cancel_booking.room_no}?"
            )
            confirm_cancel = st.checkbox(
                "I understand this cancellation cannot be undone.",
                key="confirm_booking_cancel",
            )
            if st.button(
                "Confirm booking cancellation",
                disabled=not confirm_cancel,
            ):
                try:
                    booking_manager.cancel_booking(cancel_target)
                    st.success("Booking cancelled.")
                    reset_widget_keys(
                        ["confirm_booking_cancel", "cancel_booking_target"]
                    )
                    st.rerun()
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))


def render_billing(
    booking_manager: BookingManager,
    billing_manager: BillingManager,
) -> None:
    """Render checked-in billing, services, discount, and checkout."""
    page_header("Billing and checkout", "Build an itemized bill, then complete the stay cleanly.")
    checked_in = [booking for booking in booking_manager.list_bookings() if booking.status == "Checked-in"]
    if not checked_in:
        st.info("Only checked-in guests can receive a bill. Check in a confirmed booking first.")
        return
    options = {
        booking.booking_id: (
            f"{booking.booking_id} · Room {booking.room_no} · Guest {booking.guest_id}"
        )
        for booking in checked_in
    }
    booking_id = st.selectbox(
        "Checked-in booking",
        list(options),
        format_func=lambda value: options[value],
        key="billing_booking_id",
    )
    existing = next((bill for bill in billing_manager.list_bills() if bill.booking_id == booking_id), None)
    if existing is None:
        with st.form("create_bill"):
            bill_id = st.text_input(
                "Bill ID",
                value=f"BILL-{booking_id}",
                key=f"bill_id_{booking_id}",
            )
            if st.form_submit_button("Generate itemized bill", type="primary"):
                try:
                    billing_manager.create_bill(bill_id, booking_id)
                    refresh_after_success("Bill generated.")
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))
        return

    bill = existing
    services = billing_manager.list_services()
    if services:
        with st.form("add_service"):
            service_options = {
                service.service_id: f"{service.name} · {money(service.price)}"
                for service in services
            }
            service_id = st.selectbox(
                "Hotel service",
                list(service_options),
                format_func=lambda value: service_options[value],
            )
            quantity = st.number_input(
                "Quantity",
                min_value=0,
                value=1,
                step=1,
                key=f"service_quantity_{bill.bill_id}",
                help="Enter at least 1 unit.",
            )
            if st.form_submit_button("Add service"):
                quantity_value = int(quantity)
                if quantity_value < 1:
                    st.error("Service quantity must be at least 1.")
                else:
                    try:
                        billing_manager.add_service_to_bill(
                            bill.bill_id, service_id, quantity_value
                        )
                        st.success("Service added to bill.")
                        st.rerun()
                    except (KeyError, ValueError, FileManagerError) as error:
                        st.error(str(error))
    else:
        st.info("No hotel services are configured yet.")
    with st.form("apply_discount"):
        discount = st.number_input(
            "Discount (INR)",
            min_value=0.0,
            value=float(bill.discount),
            step=50.0,
            key=f"discount_{bill.bill_id}",
        )
        if st.form_submit_button("Apply discount"):
            try:
                billing_manager.apply_discount_to_bill(bill.bill_id, discount)
                st.success("Discount applied.")
            except (KeyError, ValueError, FileManagerError) as error:
                st.error(str(error))

    st.subheader(f"Bill {bill.bill_id}")
    st.code(bill.generate_itemized_bill(), language=None)
    if st.button("Complete checkout", type="primary"):
        try:
            billing_manager.checkout(bill.bill_id)
            refresh_after_success(
                "Checkout completed. The bill is marked Paid and stay history was saved."
            )
        except (KeyError, ValueError, FileManagerError) as error:
            st.error(str(error))


def render_history(file_manager: FileManager, billing_manager: BillingManager) -> None:
    """Display saved completed-stay text and completed bill summaries."""
    page_header("Stay history", "Review completed stays saved by the checkout workflow.")
    try:
        history = file_manager.read_text("history.txt")
    except FileManagerError as error:
        st.error(f"History could not be loaded: {error}")
        return
    if history.strip():
        search = st.text_input(
            "Search history",
            placeholder="Booking ID, guest ID/name, bill ID, room, or dates",
        )
        lines = history.splitlines()
        filtered = [
            line for line in lines
            if not search.strip() or search.strip().lower() in line.lower()
        ]
        if filtered:
            st.code("\n".join(filtered), language=None)
        else:
            st.info("No history entries match this search.")
    else:
        st.info("No completed stays yet. History will appear after a successful checkout.")
    paid_bills = [bill for bill in billing_manager.list_bills() if bill.payment_status == "Paid"]
    if paid_bills:
        st.subheader("Completed bill records")
        st.dataframe(
            [{"Bill": bill.bill_id, "Booking": bill.booking_id, "Total": money(bill.total)} for bill in paid_bills],
            use_container_width=True,
            hide_index=True,
        )
        pending_history = [
            bill for bill in paid_bills
            if f"Bill: {bill.bill_id}" not in history
        ]
        if pending_history:
            st.warning(
                "Some completed bills are missing their stay-history line because "
                "a previous history write failed."
            )
            repair_id = st.selectbox(
                "Completed bill to repair",
                [bill.bill_id for bill in pending_history],
                key="history_repair_bill_id",
            )
            if st.button("Repair missing history record"):
                try:
                    billing_manager.repair_history(repair_id)
                    refresh_after_success("The missing history record was restored.")
                except (KeyError, ValueError, FileManagerError) as error:
                    st.error(str(error))


def render_services(billing_manager: BillingManager) -> None:
    """Display the configured hotel service catalog without mutating it."""
    page_header("Hotel services", "Browse the services available for checked-in stays.")
    services = billing_manager.list_services()
    if not services:
        st.info("No hotel services are configured yet.")
        return
    st.dataframe(
        [
            {
                "Service ID": service.service_id,
                "Service": service.name,
                "Category": service.category,
                "Price": money(service.price),
            }
            for service in services
        ],
        use_container_width=True,
        hide_index=True,
    )


def main() -> None:
    """Start the Streamlit application and route the selected page."""
    configure_page()
    try:
        file_manager, guest_manager, room_manager, booking_manager, billing_manager = build_managers()
    except (FileManagerError, KeyError, ValueError) as error:
        st.error(
            "The saved application data could not be loaded. "
            f"Please correct the data file and try again: {error}"
        )
        st.stop()
    if message := st.session_state.pop("flash_success", None):
        st.success(message)
    with st.sidebar:
        st.markdown("## Hotel Management System")
        page = st.radio(
            "Front desk",
            [
                "Dashboard",
                "Guest Management",
                "Room Management",
                "Booking Management",
                "Services",
                "Billing & Checkout",
                "Stay History",
            ],
            key="front_desk_page",
        )
        st.divider()

    if page == "Dashboard":
        render_dashboard(guest_manager, room_manager, booking_manager, billing_manager)
    elif page == "Guest Management":
        render_guest_management(guest_manager)
    elif page == "Room Management":
        render_room_management(room_manager, booking_manager)
    elif page == "Booking Management":
        render_booking_management(guest_manager, room_manager, booking_manager)
    elif page == "Billing & Checkout":
        render_billing(booking_manager, billing_manager)
    elif page == "Services":
        render_services(billing_manager)
    else:
        render_history(file_manager, billing_manager)


if __name__ == "__main__":
    main()
