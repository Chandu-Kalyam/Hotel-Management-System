"""Room entities for the hotel management system.

The room hierarchy demonstrates shared behavior through inheritance while
allowing each room type to provide its own pricing method. Date-specific
reservation availability is intentionally not handled here; BookingManager
owns that date-specific responsibility.
"""

from __future__ import annotations

# Used to reject NaN and infinity in prices loaded from files or user input.
import math

# Used for values loaded from JSON before the room fields validate them.
from typing import Any


class Room:
    """Represent one room and its operational status.

    Room stores inventory facts such as capacity and base price. The ``status``
    describes the room's current operational label, while date-specific
    booking conflicts are checked by BookingManager.
    """

    VALID_STATUSES = ("Available", "Reserved", "Occupied", "Maintenance")
    ROOM_TYPE = "Room"

    def __init__(
        self,
        room_no: int,
        floor: int,
        capacity: int,
        base_price: float,
        status: str = "Available",
    ) -> None:
        """Create a room after validating its inventory values.

        Raises:
            ValueError: If a number is invalid or the status is unsupported.
        """
        # using protected methods encapsulates validation logic and avoids code duplication in subclasses
        self.room_no = self._positive_integer("room_no", room_no)
        self.floor = self._positive_integer("floor", floor)
        self.capacity = self._positive_integer("capacity", capacity)
        self.base_price = self._positive_price(base_price)
        self.status = self._validate_status(status)

    # Here we want to provide a read-only attribute that can be accessed like a regular attribute, but is actually computed by a method. This allows us to encapsulate the logic for determining the room type and ensures that it cannot be modified directly.
    @property
    def room_type(self) -> str:
        """Return the JSON-compatible name of this room type."""
        return self.ROOM_TYPE

    def calculate_nightly_price(self) -> float:
        """Return this room's nightly price without hidden adjustments.

        Subclasses override this method so the same manager can calculate a
        price polymorphically for any Room object. The agreed sample prices
        remain unchanged, so every type returns its stored base price.
        """
        return self.base_price

    def change_status(self, status: str) -> None:
        """Change the operational status after validating the new label.

        ``Reserved`` and ``Occupied`` are useful status labels, but they are
        not date-global booking restrictions. Only genuine operational
        restrictions such as ``Maintenance`` are handled as static exclusions.

        Raises:
            ValueError: If status is not one of the supported labels.
        """
        self.status = self._validate_status(status)

    def display_details(self) -> str:
        """Return readable details for display in the Streamlit interface."""
        return (
            f"Room {self.room_no} | {self.room_type} | Floor {self.floor} | "
            f"Capacity {self.capacity} | INR {self.calculate_nightly_price():.2f} "
            f"per night | Status: {self.status}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert this room into the structure used by ``rooms.json``."""
        return {
            "room_no": self.room_no,
            "floor": self.floor,
            "room_type": self.room_type,
            "capacity": self.capacity,
            "base_price": self.base_price,
            "status": self.status,
        }

    # @classmethod is used here to allow subclasses to call this method and get the correct class type without needing to know the specific subclass. This is useful for deserialization, where we want to create an instance of the correct subclass based on the data provided.
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Room:
        """Reconstruct the correct Room subclass from saved JSON data.

        The ``room_type`` field acts as a simple discriminator. This keeps the
        JSON beginner-friendly while preserving the correct OOP type after a
        manager reload.

        Raises:
            ValueError: If the room type is missing or unsupported, or if any
                room field fails validation.
        """
        room_type = data.get("room_type")
        room_classes = {
            "Room": Room,
            "Standard": StandardRoom,
            "Deluxe": DeluxeRoom,
            "Suite": SuiteRoom,
        }
        room_class = room_classes.get(room_type)
        if room_class is None:
            raise ValueError(f"Unsupported room type: {room_type!r}.")

        required_fields = ("room_no", "floor", "capacity", "base_price", "status")
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(f"Room data is missing required field(s): {fields}.")

        return room_class(
            room_no=data["room_no"],
            floor=data["floor"],
            capacity=data["capacity"],
            base_price=data["base_price"],
            status=data["status"],
        )

    @classmethod
    def _validate_status(cls, status: str) -> str:
        """Return a supported status label or reject it."""
        if not isinstance(status, str):
            raise ValueError("Room status must be text.")
        cleaned_status = status.strip().title()
        if cleaned_status not in cls.VALID_STATUSES:
            valid_statuses = ", ".join(cls.VALID_STATUSES)
            raise ValueError(
                f"Unsupported room status '{status}'. Use: {valid_statuses}."
            )
        return cleaned_status

    @staticmethod
    def _positive_integer(field_name: str, value: Any) -> int:
        """Validate a positive integer room field."""
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value
    # @staticmethod is used here to indicate that this method does not depend on any instance-specific data. It can be called on the class itself or on an instance, and it only uses the parameters passed to it. This is appropriate for utility functions like this one that perform validation without needing access to the instance's state.
    @staticmethod
    def _positive_price(value: Any) -> float:
        """Validate a positive numeric price and store it as a float."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("base_price must be a positive number.")
        if not math.isfinite(float(value)) or value <= 0:
            raise ValueError("base_price must be a positive number.")
        return float(value)


class StandardRoom(Room):
    """Represent a Standard room using its stored INR base price."""

    ROOM_TYPE = "Standard"

    def calculate_nightly_price(self) -> float:
        """Return the Standard room's stored base price unchanged."""
        return self.base_price


class DeluxeRoom(Room):
    """Represent a Deluxe room using its stored INR base price."""

    ROOM_TYPE = "Deluxe"

    def calculate_nightly_price(self) -> float:
        """Return the Deluxe room's stored base price unchanged."""
        return self.base_price


class SuiteRoom(Room):
    """Represent a Suite room using its stored INR base price."""

    ROOM_TYPE = "Suite"

    def calculate_nightly_price(self) -> float:
        """Return the Suite room's stored base price unchanged."""
        return self.base_price
