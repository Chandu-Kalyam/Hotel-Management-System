"""Booking entity and lifecycle states for the hotel management system.

Booking stores one reservation and provides the small state changes that are
valid for that reservation. BookingManager owns collection-level rules such as
date conflicts and decides when these transitions may be called.
"""

from __future__ import annotations

# Used for calendar dates and for converting saved ISO date text.
from datetime import date

# Used for values loaded from JSON before booking fields are validated.
from typing import Any


class Booking:
    """Represent one guest reservation and its lifecycle state."""

    VALID_STATUSES = ("Confirmed", "Cancelled", "Checked-in", "Checked-out")

    def __init__(
        self,
        booking_id: str,
        guest_id: str,
        room_no: int,
        check_in: date,
        check_out: date,
        guests_count: int,
        status: str = "Confirmed",
    ) -> None:
        """Create a booking with validated identifiers, dates, and status.

        BookingManager validates the same dates before creating the object.
        The entity also checks the basic date order so objects loaded or
        created directly cannot contain a reversed stay.

        Raises:
            ValueError: If a field is invalid or checkout is not later than
                check-in.
        """
        self.booking_id = self._required_text("booking_id", booking_id)
        self.guest_id = self._required_text("guest_id", guest_id)
        self.room_no = self._positive_integer("room_no", room_no)
        self.check_in = self._date_value("check_in", check_in)
        self.check_out = self._date_value("check_out", check_out)
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be later than check_in.")
        self.guests_count = self._positive_integer("guests_count", guests_count)
        self.status = self._validate_status(status)

    def calculate_nights(self) -> int:
        """Return the number of nights between check-in and check-out."""
        return (self.check_out - self.check_in).days

    def confirm(self) -> None:
        """Confirm a new booking.

        Raises:
            ValueError: If the booking was already completed or cancelled.
        """
        if self.status != "Confirmed":
            raise ValueError(
                f"Booking '{self.booking_id}' cannot be confirmed from "
                f"status '{self.status}'."
            )

    def cancel(self) -> None:
        """Cancel a confirmed booking before the guest checks in.

        Raises:
            ValueError: If the booking is not currently confirmed.
        """
        if self.status != "Confirmed":
            raise ValueError(
                f"Booking '{self.booking_id}' cannot be cancelled from "
                f"status '{self.status}'."
            )
        self.status = "Cancelled"

    def check_in_guest(self) -> None:
        """Move a confirmed booking to the checked-in state.

        Raises:
            ValueError: If the booking is not confirmed.
        """
        if self.status != "Confirmed":
            raise ValueError(
                f"Booking '{self.booking_id}' cannot be checked in from "
                f"status '{self.status}'."
            )
        self.status = "Checked-in"

    def checkout(self) -> None:
        """Move a checked-in booking to the checked-out state.

        Raises:
            ValueError: If the booking was not checked in.
        """
        if self.status != "Checked-in":
            raise ValueError(
                f"Booking '{self.booking_id}' cannot be checked out from "
                f"status '{self.status}'."
            )
        self.status = "Checked-out"

    def to_dict(self) -> dict[str, Any]:
        """Convert the booking into JSON-compatible data."""
        return {
            "booking_id": self.booking_id,
            "guest_id": self.guest_id,
            "room_no": self.room_no,
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "guests_count": self.guests_count,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Booking:
        """Reconstruct a Booking from one saved JSON object.

        Dates are saved as ISO text so the file remains easy to read. They are
        converted back to date objects before the booking is used in Python.

        Raises:
            ValueError: If required fields are missing or values are invalid.
        """
        required_fields = (
            "booking_id",
            "guest_id",
            "room_no",
            "check_in",
            "check_out",
            "guests_count",
            "status",
        )
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(
                f"Booking data is missing required field(s): {fields}."
            )

        return cls(
            booking_id=data["booking_id"],
            guest_id=data["guest_id"],
            room_no=data["room_no"],
            check_in=cls._parse_saved_date("check_in", data["check_in"]),
            check_out=cls._parse_saved_date("check_out", data["check_out"]),
            guests_count=data["guests_count"],
            status=data["status"],
        )

    @classmethod
    def _validate_status(cls, status: str) -> str:
        """Return a supported lifecycle state or reject it."""
        if not isinstance(status, str) or status not in cls.VALID_STATUSES:
            valid_statuses = ", ".join(cls.VALID_STATUSES)
            raise ValueError(
                f"Unsupported booking status '{status}'. Use: {valid_statuses}."
            )
        return status

    @staticmethod
    def _required_text(field_name: str, value: Any) -> str:
        """Validate a required text identifier."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be non-empty text.")
        return value.strip()

    @staticmethod
    def _positive_integer(field_name: str, value: Any) -> int:
        """Validate a positive integer booking field."""
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value

    @staticmethod
    def _date_value(field_name: str, value: Any) -> date:
        """Validate a date object supplied by the manager or loader."""
        if not isinstance(value, date):
            raise ValueError(f"{field_name} must be a date.")
        return value

    @staticmethod
    def _parse_saved_date(field_name: str, value: Any) -> date:
        """Convert one ISO date string from JSON into a date object."""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be an ISO date string.")
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                f"{field_name} must use the YYYY-MM-DD format."
            ) from error
