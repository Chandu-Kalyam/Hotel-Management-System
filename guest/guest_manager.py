"""Collection operations and persistence for hotel guests.

GuestManager owns the guest collection and coordinates Guest objects with the
existing FileManager. It does not know how bookings work, which keeps this
manager independent from BookingManager.
"""

from __future__ import annotations

# Callable describes the small optional check used before deleting a guest.
# Iterable lets the duplicate-ID helper work with any guest collection.
from collections.abc import Callable, Iterable

# Used for the path returned after guest records are saved.
from pathlib import Path

# The Guest entity validates and serializes one guest.
from guest.guest import Guest

# FileManager performs the JSON read/write work for the manager.
from storage.file_manager import FileManager


ActiveBookingChecker = Callable[[str], bool]
"""A callback that returns True when a guest currently has an active booking."""


class GuestManager:
    """Manage guest records while keeping JSON persistence in one place.

    The manager loads the existing collection once during construction and
    saves the full collection after each successful mutation.
    """

    GUESTS_FILE = "guests.json"

    def __init__(
        self,
        file_manager: FileManager | None = None,
        active_booking_checker: ActiveBookingChecker | None = None,
    ) -> None:
        """Create a manager and load the existing guest records.

        Parameters:
            file_manager: Optional persistence object, useful for supplying a
                different data directory during checks.
            active_booking_checker: Optional callback that accepts a guest ID
                and returns whether deletion should be blocked.
        """
        self.file_manager = file_manager or FileManager()
        self.active_booking_checker = active_booking_checker
        self.guests = self._load_guests()

    def add_guest(self, guest: Guest) -> Guest:
        """Add and persist a guest with a unique identifier.

        Raises:
            ValueError: If the value is not a Guest or its ID already exists.
        """
        if not isinstance(guest, Guest):
            raise ValueError("Only Guest objects can be added.")

        # Exact ID lookup is used here instead of a broad search. A search for
        # "G001" might match another field, while IDs must be unique by ID.
        if self.get_guest(guest.guest_id) is not None:
            raise ValueError(f"Guest ID '{guest.guest_id}' already exists.")

        self.guests.append(guest)
        self._save_guests()
        return guest

    def find_guest(self, search_text: str) -> list[Guest]:
        """Find guests by partial ID, name, phone, email, or ID proof text.

        An empty search returns a copy of the complete list. Returning a copy
        prevents callers from changing the manager's list without persistence.

        Raises:
            ValueError: If search_text is not text.
        """
        if not isinstance(search_text, str):
            raise ValueError("Search text must be text.")

        query = search_text.strip().casefold()
        if not query:
            return self.list_guests()

        # casefold makes searching case-insensitive; any matching field is
        # enough for the guest to appear in the result.
        searchable_fields = ("guest_id", "name", "phone", "email", "id_proof")
        return [
            guest
            for guest in self.guests
            if any(
                query in str(getattr(guest, field)).casefold()
                for field in searchable_fields
            )
        ]

    def get_guest(self, guest_id: str) -> Guest | None:
        """Return one guest by exact ID, or None when it is unknown.

        IDs are compared case-insensitively after surrounding spaces are
        removed, so ``g001`` and ``G001`` refer to the same guest.

        Raises:
            ValueError: If guest_id is not a non-empty string.
        """
        normalized_id = self._validate_guest_id(guest_id)
        for guest in self.guests:
            if guest.guest_id.casefold() == normalized_id.casefold():
                return guest
        return None

    def update_guest(
        self,
        guest_id: str,
        name: str,
        phone: str,
        email: str,
        address: str,
        id_proof: str,
    ) -> Guest:
        """Update and persist an existing guest.

        Raises:
            KeyError: If the guest ID is unknown.
            ValueError: If the ID or any replacement detail is invalid.
        """
        guest = self._require_guest(guest_id)
        guest.update_details(name, phone, email, address, id_proof)
        self._save_guests()
        return guest

    def delete_guest(self, guest_id: str) -> None:
        """Delete a guest unless an optional checker finds an active booking.

        The callback is the protection contract between managers without
        requiring GuestManager to import or depend directly on BookingManager.

        Raises:
            KeyError: If the guest ID is unknown.
            ValueError: If an active booking checker blocks deletion.
        """
        guest = self._require_guest(guest_id)

        # The ``and`` short-circuits safely when no callback was supplied.
        if self.active_booking_checker and self.active_booking_checker(
            guest.guest_id
        ):
            raise ValueError(
                f"Guest '{guest.guest_id}' cannot be deleted while an active "
                "booking exists."
            )

        self.guests.remove(guest)
        self._save_guests()

    def list_guests(self) -> list[Guest]:
        """Return a copy of guests in their stored order."""
        return list(self.guests)

    def _load_guests(self) -> list[Guest]:
        """Load guests, initializing ``guests.json`` only if it is missing.

        Existing records are never replaced during construction. Each JSON
        object is converted into a Guest so field validation is reused.

        Raises:
            ValueError: If the JSON shape, guest records, or IDs are invalid.
        """
        self.file_manager.initialize_json_file(self.GUESTS_FILE, [])
        raw_guests = self.file_manager.load_json(self.GUESTS_FILE)
        if not isinstance(raw_guests, list):
            raise ValueError("Guest data must be stored as a JSON list.")

        guests = []
        # Validate every saved record before the manager starts using it.
        for record in raw_guests:
            if not isinstance(record, dict):
                raise ValueError("Each guest record must be a JSON object.")
            guests.append(Guest.from_dict(record))
        self._ensure_unique_ids(guests)
        return guests

    def _save_guests(self) -> Path:
        """Persist all current guests without changing other data files."""
        return self.file_manager.save_json(
            self.GUESTS_FILE,
            [guest.to_dict() for guest in self.guests],
        )

    def _require_guest(self, guest_id: str) -> Guest:
        """Return a guest or raise the manager's consistent unknown-ID error."""
        guest = self.get_guest(guest_id)
        if guest is None:
            raise KeyError(f"Guest ID '{guest_id}' was not found.")
        return guest

    @staticmethod
    def _validate_guest_id(guest_id: str) -> str:
        """Validate and normalize an ID used in a lookup.

        Raises:
            ValueError: If the ID is not text or is empty after trimming.
        """
        if not isinstance(guest_id, str):
            raise ValueError("Guest ID must be text.")
        normalized_id = guest_id.strip()
        if not normalized_id:
            raise ValueError("Guest ID cannot be empty.")
        return normalized_id

    @staticmethod
    def _ensure_unique_ids(guests: Iterable[Guest]) -> None:
        """Reject duplicate IDs while loading saved guest records.

        ``seen_ids`` stores normalized IDs, so capitalization differences do
        not allow two records to represent the same guest.

        Raises:
            ValueError: If two guests use the same ID.
        """
        seen_ids: set[str] = set()
        for guest in guests:
            normalized_id = guest.guest_id.casefold()
            if normalized_id in seen_ids:
                raise ValueError(f"Guest ID '{guest.guest_id}' is duplicated.")
            seen_ids.add(normalized_id)
