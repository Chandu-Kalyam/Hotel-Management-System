"""Guest entity used by the hotel management system.

The Guest class represents one guest and owns validation for that guest's
required details. Collection operations and JSON file persistence belong to
GuestManager instead.
"""

from __future__ import annotations

# Used to check the simple structure of an email address.
import re

# Used for JSON-loaded values whose exact type is checked by validation.
from typing import Any


class Guest:
    """Store and validate the details of one hotel guest.

    Each Guest object stores its own values on ``self``. The class also knows
    how to validate those values and convert itself to and from JSON-friendly
    dictionaries.
    """

    REQUIRED_FIELDS = ("guest_id", "name", "phone", "email", "address", "id_proof")

    def __init__(
        self,
        guest_id: str,
        name: str,
        phone: str,
        email: str,
        address: str,
        id_proof: str,
    ) -> None:
        """Create a guest after validating every required field.

        Raises:
            ValueError: If any field is not text or is empty after trimming.
        """
        self.guest_id = self._required_text("guest_id", guest_id)
        # Validate every replacement before changing the current object so a
        # failed edit cannot leave a partially updated guest in memory.
        new_name = self._required_text("name", name)
        new_phone = self._validate_phone(phone)
        new_email = self._validate_email(email)
        new_address = self._required_text("address", address)
        new_id_proof = self._required_text("id_proof", id_proof)

        self.name = new_name
        self.phone = new_phone
        self.email = new_email
        self.address = new_address
        self.id_proof = new_id_proof

    def update_details(
        self,
        name: str,
        phone: str,
        email: str,
        address: str,
        id_proof: str,
    ) -> None:
        """Replace editable guest details after validating every field.

        The guest ID is intentionally not changed here because it is the
        stable identifier used by managers and future bookings.

        Raises:
            ValueError: If any replacement value is invalid.
        """
        # Validate all replacements before changing the object.
        new_name = self._required_text("name", name)
        new_phone = self._validate_phone(phone)
        new_email = self._validate_email(email)
        new_address = self._required_text("address", address)
        new_id_proof = self._required_text("id_proof", id_proof)

        self.name = new_name
        self.phone = new_phone
        self.email = new_email
        self.address = new_address
        self.id_proof = new_id_proof

    def display_details(self) -> str:
        """Return a readable multi-line summary for a UI or console."""
        return (
            f"Guest ID: {self.guest_id}\n"
            f"Name: {self.name}\n"
            f"Phone: {self.phone}\n"
            f"Email: {self.email}\n"
            f"Address: {self.address}\n"
            f"ID Proof: {self.id_proof}"
        )

    def to_dict(self) -> dict[str, str]:
        """Convert this object into the dictionary saved in ``guests.json``."""
        return {
            "guest_id": self.guest_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "id_proof": self.id_proof,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Guest:
        """Build a Guest from one dictionary loaded from JSON.

        The list comprehension collects every required key that is absent.
        Reporting all missing keys at once makes malformed saved data easier
        for a student to correct.

        Raises:
            ValueError: If required keys are missing or their values are
                rejected by the constructor.
        """
        missing_fields = [
            field for field in cls.REQUIRED_FIELDS if field not in data
        ]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(f"Guest data is missing required field(s): {fields}.")

        # Keep older saved records loadable so one invalid legacy phone
        # number cannot prevent the application from starting. New records
        # and all edits still use strict phone validation.
        guest = cls.__new__(cls)
        guest.guest_id = cls._required_text("guest_id", data["guest_id"])
        guest.name = cls._required_text("name", data["name"])
        guest.phone = cls._required_text("phone", data["phone"])
        guest.email = cls._validate_email(data["email"])
        guest.address = cls._required_text("address", data["address"])
        guest.id_proof = cls._required_text("id_proof", data["id_proof"])
        return guest

    @staticmethod
    def _required_text(field_name: str, value: Any) -> str:
        """Return a trimmed non-empty string or reject invalid input.

        ``strip`` removes accidental surrounding spaces before the value is
        stored. This prevents a name or ID made only of spaces from passing
        validation.

        Raises:
            ValueError: If the value is not text or becomes empty after trim.
        """
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be text.")

        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError(f"{field_name} cannot be empty.")
        return cleaned_value

    @staticmethod
    def _validate_phone(value: Any) -> str:
        """Return exactly ten numeric digits or reject the phone number.

        Raises:
            ValueError: If the phone number is not exactly ten digits.
        """
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{10}", value):
            raise ValueError("Phone number must contain exactly 10 digits.")
        return value

    @staticmethod
    def _validate_email(value: Any) -> str:
        """Return a simple valid email address or reject the input.

        This intentionally checks only the basic format needed by the
        student project: one non-empty local part, an ``@`` symbol, and a
        non-empty domain containing a dot. Whitespace is not allowed.

        Raises:
            ValueError: If the email is empty or does not match the format.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "Please enter a valid email address, for example "
                "name@example.com."
            )

        email = value.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError(
                "Please enter a valid email address, for example "
                "name@example.com."
            )
        return email
