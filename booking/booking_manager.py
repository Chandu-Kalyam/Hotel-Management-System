"""Booking collection, date availability, and lifecycle management.

BookingManager is the only owner of reservation date comparisons, overlap
detection, date-specific room availability, and booking-state transitions.
RoomManager supplies room lookups and operational status without importing this
module, so the dependency direction remains one-way.
"""

from __future__ import annotations

# Used to parse user-provided and saved calendar dates in one place.
from datetime import date

# Used for the path returned after bookings are saved.
from pathlib import Path

# GuestManager and RoomManager provide existence and capacity/status checks.
from guest.guest_manager import GuestManager
from room.room_manager import RoomManager

# Booking provides one reservation's data and valid state methods.
from booking.booking import Booking

# FileManager persists the booking collection as JSON.
from storage.file_manager import FileManager


class BookingManager:
    """Manage bookings while preserving guest, room, and JSON consistency."""

    BOOKINGS_FILE = "bookings.json"
    ACTIVE_STATUSES = ("Confirmed", "Checked-in")

    def __init__(
        self,
        guest_manager: GuestManager,
        room_manager: RoomManager,
        file_manager: FileManager | None = None,
    ) -> None:
        """Create a manager using existing guest and room managers.

        The managers are supplied by the caller rather than imported by room
        code. This keeps BookingManager's dependencies one-directional and
        lets tests provide temporary data directories.
        """
        self.guest_manager = guest_manager
        self.room_manager = room_manager
        self.file_manager = file_manager or FileManager()
        self.bookings = self._load_bookings()

        # Wire the existing callback contract after bookings are loaded so
        # GuestManager can prevent deletion of guests with active bookings.
        self.guest_manager.active_booking_checker = self.has_active_booking

    def create_booking(
        self,
        booking_id: str,
        guest_id: str,
        room_no: int,
        check_in: date | str,
        check_out: date | str,
        guests_count: int,
    ) -> Booking:
        """Validate, create, confirm, and persist a new booking.

        Raises:
            KeyError: If the guest or room does not exist.
            ValueError: If dates, guest count, room status, or booking ID is
                invalid, or if the requested dates conflict.
        """
        if self.get_booking(booking_id) is not None:
            raise ValueError(f"Booking ID '{booking_id}' already exists.")

        guest = self.guest_manager.get_guest(guest_id)
        if guest is None:
            raise KeyError(f"Guest ID '{guest_id}' was not found.")

        room = self.room_manager.get_room(room_no)
        if room is None:
            raise KeyError(f"Room number '{room_no}' was not found.")

        parsed_check_in = self._parse_date("check_in", check_in)
        parsed_check_out = self._parse_date("check_out", check_out)
        self._validate_date_range(parsed_check_in, parsed_check_out)
        self._validate_guest_count(guests_count, room.capacity)
        self._validate_guest_booking_overlap(
            guest.guest_id,
            parsed_check_in,
            parsed_check_out,
        )

        # Maintenance is a genuine operational restriction. Reserved and
        # Occupied labels are not rejected here because their date-specific
        # bookings are checked by the overlap method below.
        if room.status == "Maintenance":
            raise ValueError(f"Room '{room.room_no}' is under maintenance.")
        if not self.is_room_available(
            room.room_no, parsed_check_in, parsed_check_out
        ):
            raise ValueError(
                f"Room '{room.room_no}' is not available for the requested dates."
            )

        booking = Booking(
            booking_id=booking_id,
            guest_id=guest.guest_id,
            room_no=room.room_no,
            check_in=parsed_check_in,
            check_out=parsed_check_out,
            guests_count=guests_count,
        )
        booking.confirm()
        self.bookings.append(booking)
        self._save_bookings()
        self._recalculate_room_status(room.room_no)
        return booking

    def find_booking(self, search_text: str) -> list[Booking]:
        """Find bookings by ID, guest ID, room number, or status."""
        if not isinstance(search_text, str):
            raise ValueError("Booking search text must be text.")
        query = search_text.strip().casefold()
        if not query:
            return self.list_bookings()
        return [
            booking
            for booking in self.bookings
            if query in booking.booking_id.casefold()
            or query in booking.guest_id.casefold()
            or query in str(booking.room_no).casefold()
            or query in booking.status.casefold()
        ]

    def get_booking(self, booking_id: str) -> Booking | None:
        """Return a booking by exact ID, or None when it is unknown."""
        normalized_id = self._validate_booking_id(booking_id)
        for booking in self.bookings:
            if booking.booking_id.casefold() == normalized_id.casefold():
                return booking
        return None

    def list_bookings(self) -> list[Booking]:
        """Return a copy of bookings in their stored order."""
        return list(self.bookings)

    def cancel_booking(self, booking_id: str) -> Booking:
        """Cancel a confirmed booking and update its room label.

        Raises:
            KeyError: If the booking ID is unknown.
            ValueError: If the booking cannot be cancelled.
        """
        booking = self._require_booking(booking_id)
        booking.cancel()
        self._save_bookings()
        self._recalculate_room_status(booking.room_no)
        return booking

    def check_in_guest(self, booking_id: str) -> Booking:
        """Check in an eligible confirmed guest and mark the room occupied.

        Raises:
            KeyError: If the booking ID is unknown.
            ValueError: If the booking is not confirmed or its stay has not
                started yet.
        """
        booking = self._require_booking(booking_id)
        if booking.status != "Confirmed":
            raise ValueError(
                f"Booking '{booking.booking_id}' cannot be checked in from "
                f"status '{booking.status}'."
            )
        if booking.check_in > date.today():
            raise ValueError(
                f"Booking '{booking.booking_id}' cannot be checked in before "
                f"{booking.check_in.isoformat()}."
            )
        booking.check_in_guest()
        self._save_bookings()
        self._recalculate_room_status(booking.room_no)
        return booking

    def checkout_guest(self, booking_id: str) -> Booking:
        """Check out a checked-in guest and release the room label.

        Billing and stay-history persistence are intentionally not handled in
        Billing and stay-history persistence are coordinated by BillingManager
        after this manager completes the booking transition.

        Raises:
            KeyError: If the booking ID is unknown.
            ValueError: If checkout is attempted before check-in or repeated.
        """
        booking = self._require_booking(booking_id)
        booking.checkout()
        self._save_bookings()
        self._recalculate_room_status(booking.room_no)
        return booking

    def is_room_available(
        self,
        room_no: int,
        check_in: date | str,
        check_out: date | str,
    ) -> bool:
        """Return whether a room has no active overlapping reservation.

        The half-open interval rule allows a new stay to begin on the same
        date an existing stay ends:
        ``existing.check_in < requested.check_out`` and
        ``requested.check_in < existing.check_out``.

        Maintenance is rejected as an operational restriction. Reserved and
        Occupied labels alone do not reject non-overlapping requested dates.
        """
        room = self.room_manager.get_room(room_no)
        if room is None:
            raise KeyError(f"Room number '{room_no}' was not found.")
        parsed_check_in = self._parse_date("check_in", check_in)
        parsed_check_out = self._parse_date("check_out", check_out)
        self._validate_date_range(parsed_check_in, parsed_check_out)
        if room.status == "Maintenance":
            return False
        return not self.detect_conflict(
            room.room_no, parsed_check_in, parsed_check_out
        )

    def detect_conflict(
        self,
        room_no: int,
        check_in: date | str,
        check_out: date | str,
    ) -> bool:
        """Return whether active bookings overlap the requested room interval."""
        parsed_check_in = self._parse_date("check_in", check_in)
        parsed_check_out = self._parse_date("check_out", check_out)
        self._validate_date_range(parsed_check_in, parsed_check_out)

        for booking in self.bookings:
            if booking.room_no != room_no:
                continue
            if booking.status not in self.ACTIVE_STATUSES:
                continue

            # This condition is true only when both half-open intervals
            # actually overlap; touching endpoints are allowed.
            overlaps = (
                booking.check_in < parsed_check_out
                and parsed_check_in < booking.check_out
            )
            if overlaps:
                return True
        return False

    def has_active_booking(self, guest_id: str) -> bool:
        """Return whether a guest has a confirmed or checked-in booking."""
        normalized_guest_id = guest_id.strip().casefold()
        return any(
            booking.guest_id.casefold() == normalized_guest_id
            and booking.status in self.ACTIVE_STATUSES
            for booking in self.bookings
        )

    def _validate_guest_booking_overlap(
        self,
        guest_id: str,
        check_in: date,
        check_out: date,
    ) -> None:
        """Reject overlapping active stays for the same guest.

        Guest overlap is independent of room overlap: one guest cannot have
        two simultaneous active stays, even when the rooms are different.
        Cancelled and checked-out bookings are intentionally ignored.

        Raises:
            ValueError: If an active booking for the guest overlaps the
                requested half-open date interval.
        """
        for booking in self.bookings:
            if booking.guest_id.casefold() != guest_id.casefold():
                continue
            if booking.status not in self.ACTIVE_STATUSES:
                continue

            overlaps = (
                booking.check_in < check_out
                and check_in < booking.check_out
            )
            if overlaps:
                raise ValueError(
                    f"Guest '{guest_id}' already has an active booking "
                    f"({booking.booking_id}) for overlapping dates."
                )

    def _load_bookings(self) -> list[Booking]:
        """Load existing bookings without replacing the JSON file."""
        self.file_manager.initialize_json_file(self.BOOKINGS_FILE, [])
        raw_bookings = self.file_manager.load_json(self.BOOKINGS_FILE)
        if not isinstance(raw_bookings, list):
            raise ValueError("Booking data must be stored as a JSON list.")

        bookings = []
        for record in raw_bookings:
            if not isinstance(record, dict):
                raise ValueError("Each booking record must be a JSON object.")
            bookings.append(Booking.from_dict(record))
        self._ensure_unique_booking_ids(bookings)
        return bookings

    def _save_bookings(self) -> Path:
        """Persist all current bookings through FileManager."""
        return self.file_manager.save_json(
            self.BOOKINGS_FILE,
            [booking.to_dict() for booking in self.bookings],
        )

    def _require_booking(self, booking_id: str) -> Booking:
        """Return a booking or raise the consistent unknown-ID error."""
        booking = self.get_booking(booking_id)
        if booking is None:
            raise KeyError(f"Booking ID '{booking_id}' was not found.")
        return booking

    def _recalculate_room_status(self, room_no: int) -> None:
        """Derive one room's display status from its current booking states.

        Status is only a display and operational label. Date-specific
        availability remains controlled by ``is_room_available`` and
        ``detect_conflict``; this helper never changes booking dates or removes
        any booking.
        """
        room = self.room_manager.get_room(room_no)
        if room is None:
            raise KeyError(f"Room number '{room_no}' was not found.")
        if room.status == "Maintenance":
            return

        room_bookings = [
            booking for booking in self.bookings if booking.room_no == room_no
        ]
        if any(booking.status == "Checked-in" for booking in room_bookings):
            display_status = "Occupied"
        elif any(booking.status == "Confirmed" for booking in room_bookings):
            display_status = "Reserved"
        else:
            display_status = "Available"

        self.room_manager.update_status(room_no, display_status)

    @staticmethod
    def _parse_date(field_name: str, value: date | str) -> date:
        """Parse an ISO date string or accept an existing date object."""
        if isinstance(value, date):
            return value
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a date or YYYY-MM-DD text.")
        try:
            return date.fromisoformat(value.strip())
        except ValueError as error:
            raise ValueError(
                f"{field_name} must use the YYYY-MM-DD format."
            ) from error

    @staticmethod
    def _validate_date_range(check_in: date, check_out: date) -> None:
        """Reject past check-in dates and invalid stay ranges."""
        if check_in < date.today():
            raise ValueError("check_in cannot be in the past.")
        if check_out <= check_in:
            raise ValueError("check_out must be later than check_in.")

    @staticmethod
    def _validate_guest_count(guests_count: int, capacity: int) -> None:
        """Reject non-positive counts and counts above room capacity."""
        if (
            isinstance(guests_count, bool)
            or not isinstance(guests_count, int)
            or guests_count <= 0
        ):
            raise ValueError("guests_count must be a positive integer.")
        if guests_count > capacity:
            raise ValueError("guests_count cannot exceed room capacity.")

    @staticmethod
    def _validate_booking_id(booking_id: str) -> str:
        """Validate and normalize a booking ID used for lookup."""
        if not isinstance(booking_id, str) or not booking_id.strip():
            raise ValueError("booking_id must be non-empty text.")
        return booking_id.strip()

    @staticmethod
    def _ensure_unique_booking_ids(bookings: list[Booking]) -> None:
        """Reject duplicate booking IDs while loading saved data."""
        seen_ids: set[str] = set()
        for booking in bookings:
            normalized_id = booking.booking_id.casefold()
            if normalized_id in seen_ids:
                raise ValueError(
                    f"Booking ID '{booking.booking_id}' is duplicated."
                )
            seen_ids.add(normalized_id)
