"""Inventory operations and JSON persistence for hotel rooms.

RoomManager owns room records, room types, prices, capacity, and operational
status. It deliberately does not compare booking dates or import
BookingManager; BookingManager owns date-specific availability and conflicts.
"""

from __future__ import annotations

# Used for accepting room-type filters in a clear, reusable form.
from collections.abc import Iterable

# Used for the path returned after room records are saved.
from pathlib import Path

# Room classes provide validation, inheritance, and JSON reconstruction.
from room.room import Room

# FileManager handles JSON persistence without mixing storage with room rules.
from storage.file_manager import FileManager


class RoomManager:
    """Manage the room inventory while preserving JSON data."""

    ROOMS_FILE = "rooms.json"

    def __init__(self, file_manager: FileManager | None = None) -> None:
        """Create a manager and load rooms from the existing data file.

        A missing rooms file is initialized with an empty list. Existing
        records, including the fictional Phase 1 rooms, are never replaced.
        """
        self.file_manager = file_manager or FileManager()
        self.rooms = self._load_rooms()

    def add_room(self, room: Room) -> Room:
        """Add and persist a room with a unique room number.

        Raises:
            ValueError: If the value is not a Room or the number already exists.
        """
        if not isinstance(room, Room):
            raise ValueError("Only Room objects can be added.")
        if self.get_room(room.room_no) is not None:
            raise ValueError(f"Room number '{room.room_no}' already exists.")

        self.rooms.append(room)
        self._save_rooms()
        return room

    def find_room(self, search_text: str) -> list[Room]:
        """Find rooms by room number, type, or operational status.

        An empty search returns a copy of the complete inventory. This method
        is a broad inventory search; it does not decide date availability.

        Raises:
            ValueError: If search_text is not text.
        """
        if not isinstance(search_text, str):
            raise ValueError("Room search text must be text.")

        query = search_text.strip().casefold()
        if not query:
            return self.list_rooms()

        return [
            room
            for room in self.rooms
            if (
                query in str(room.room_no).casefold()
                or query in room.room_type.casefold()
                or query in room.status.casefold()
            )
        ]

    def get_room(self, room_no: int) -> Room | None:
        """Return one room by exact number, or None when it is unknown.

        Raises:
            ValueError: If room_no is not a positive integer.
        """
        normalized_room_no = self._validate_room_number(room_no)
        for room in self.rooms:
            if room.room_no == normalized_room_no:
                return room
        return None

    def list_rooms(self) -> list[Room]:
        """Return a copy of all rooms in their stored order."""
        return list(self.rooms)

    def update_room(
        self,
        room_no: int,
        floor: int,
        capacity: int,
        base_price: float,
    ) -> Room:
        """Update inventory details while preserving the room subclass.

        Room type is not changed by this method because changing a type should
        be an explicit domain decision rather than an accidental field edit.

        Raises:
            KeyError: If room_no is unknown.
            ValueError: If any new inventory value is invalid.
        """
        room = self._require_room(room_no)
        replacement = type(room)(
            room_no=room.room_no,
            floor=floor,
            capacity=capacity,
            base_price=base_price,
            status=room.status,
        )
        self.rooms[self.rooms.index(room)] = replacement
        self._save_rooms()
        return replacement

    def update_status(self, room_no: int, status: str) -> Room:
        """Update and persist a room's operational status.

        Reserved and Occupied remain display labels here. Date-specific
        booking checks are performed by BookingManager.

        Raises:
            KeyError: If room_no is unknown.
            ValueError: If room_no or status is invalid.
        """
        room = self._require_room(room_no)
        room.change_status(status)
        self._save_rooms()
        return room

    def get_static_candidates(
        self,
        room_type: str | None = None,
        minimum_capacity: int | None = None,
    ) -> list[Room]:
        """Return operational rooms matching static inventory requirements.

        Maintenance rooms are excluded because they are a genuine operational
        restriction. Reserved and Occupied labels are retained because they
        must not globally reject a future non-overlapping booking; BookingManager
        checks dates against active reservations.

        Raises:
            ValueError: If the room type or capacity filter is invalid.
        """
        normalized_type = self._validate_room_type(room_type)
        normalized_capacity = self._validate_minimum_capacity(minimum_capacity)

        return [
            room
            for room in self.rooms
            if room.status != "Maintenance"
            and (normalized_type is None or room.room_type == normalized_type)
            and (
                normalized_capacity is None
                or room.capacity >= normalized_capacity
            )
        ]

    def _load_rooms(self) -> list[Room]:
        """Load all rooms and reconstruct their saved subclasses."""
        self.file_manager.initialize_json_file(self.ROOMS_FILE, [])
        raw_rooms = self.file_manager.load_json(self.ROOMS_FILE)
        if not isinstance(raw_rooms, list):
            raise ValueError("Room data must be stored as a JSON list.")

        rooms = []
        for record in raw_rooms:
            if not isinstance(record, dict):
                raise ValueError("Each room record must be a JSON object.")
            rooms.append(Room.from_dict(record))
        self._ensure_unique_room_numbers(rooms)
        return rooms

    def _save_rooms(self) -> Path:
        """Persist all current rooms without changing other data files."""
        return self.file_manager.save_json(
            self.ROOMS_FILE,
            [room.to_dict() for room in self.rooms],
        )

    def _require_room(self, room_no: int) -> Room:
        """Return a room or raise the consistent unknown-number error."""
        room = self.get_room(room_no)
        if room is None:
            raise KeyError(f"Room number '{room_no}' was not found.")
        return room

    @staticmethod
    def _validate_room_number(room_no: int) -> int:
        """Validate the room number used for exact lookup."""
        if isinstance(room_no, bool) or not isinstance(room_no, int):
            raise ValueError("room_no must be a positive integer.")
        if room_no <= 0:
            raise ValueError("room_no must be a positive integer.")
        return room_no

    @staticmethod
    def _validate_room_type(room_type: str | None) -> str | None:
        """Validate an optional room-type filter."""
        if room_type is None:
            return None
        if not isinstance(room_type, str):
            raise ValueError("room_type must be text.")
        normalized_type = room_type.strip().title()
        valid_types = {"Room", "Standard", "Deluxe", "Suite"}
        if normalized_type not in valid_types:
            raise ValueError(
                "Unsupported room_type. Use Standard, Deluxe, or Suite."
            )
        return normalized_type

    @staticmethod
    def _validate_minimum_capacity(capacity: int | None) -> int | None:
        """Validate an optional minimum-capacity filter."""
        if capacity is None:
            return None
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise ValueError("minimum_capacity must be a positive integer.")
        if capacity <= 0:
            raise ValueError("minimum_capacity must be a positive integer.")
        return capacity

    @staticmethod
    def _ensure_unique_room_numbers(rooms: Iterable[Room]) -> None:
        """Reject duplicate room numbers while loading saved data."""
        seen_numbers: set[int] = set()
        for room in rooms:
            if room.room_no in seen_numbers:
                raise ValueError(f"Room number '{room.room_no}' is duplicated.")
            seen_numbers.add(room.room_no)
