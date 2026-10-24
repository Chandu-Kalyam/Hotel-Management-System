"""Service loading, bill persistence, checkout, and stay-history coordination."""

from __future__ import annotations

# Used for the path returned after billing JSON is saved.
from pathlib import Path

# Bill uses Booking and Room objects for centralized calculations.
from billing.bill import Bill
from billing.service import Service

# BookingManager owns booking state transitions and checked-in validation.
from booking.booking import Booking
from booking.booking_manager import BookingManager

# RoomManager supplies the correct room object and room-specific price.
from room.room import Room
from room.room_manager import RoomManager

# FileManager handles JSON and TXT persistence in the configured data folder.
from storage.file_manager import FileManager, FileManagerError


class BillingManager:
    """Manage services and bills without duplicating booking rules."""

    SERVICES_FILE = "services.json"
    BILLS_FILE = "bills.json"
    HISTORY_FILE = "history.txt"

    def __init__(
        self,
        booking_manager: BookingManager,
        room_manager: RoomManager,
        file_manager: FileManager | None = None,
    ) -> None:
        """Load services and bills using the supplied public managers."""
        self.booking_manager = booking_manager
        self.room_manager = room_manager
        self.file_manager = file_manager or FileManager()
        self.services = self._load_services()
        self.bills = self._load_bills()
        self.file_manager.initialize_text_file(self.HISTORY_FILE)

    def list_services(self) -> list[Service]:
        """Return all available hotel services."""
        return list(self.services)

    def find_service(self, service_id: str) -> Service | None:
        """Return one service by exact ID, or None when unknown."""
        normalized_id = self._required_text("service_id", service_id).casefold()
        return next(
            (
                service
                for service in self.services
                if service.service_id.casefold() == normalized_id
            ),
            None,
        )

    def list_bills(self) -> list[Bill]:
        """Return all saved bills in their stored order."""
        return list(self.bills)

    def find_bill(self, bill_id: str) -> Bill | None:
        """Return one bill by exact ID, or None when unknown."""
        normalized_id = self._required_text("bill_id", bill_id).casefold()
        return next(
            (
                bill
                for bill in self.bills
                if bill.bill_id.casefold() == normalized_id
            ),
            None,
        )

    def create_bill(self, bill_id: str, booking_id: str) -> Bill:
        """Create and save an itemized bill for a checked-in booking.

        Raises:
            KeyError: If the booking or room is unknown.
            ValueError: If the booking is not checked in or a bill exists.
        """
        if self.find_bill(bill_id) is not None:
            raise ValueError(f"Bill ID '{bill_id}' already exists.")
        booking = self.booking_manager.get_booking(booking_id)
        if booking is None:
            raise KeyError(f"Booking ID '{booking_id}' was not found.")
        if booking.status != "Checked-in":
            raise ValueError(
                "A bill can only be generated for a checked-in booking."
            )
        room = self.room_manager.get_room(booking.room_no)
        if room is None:
            raise KeyError(f"Room number '{booking.room_no}' was not found.")

        bill = Bill(bill_id=bill_id, booking_id=booking.booking_id)
        bill.calculate_room_charge(booking, room)
        bill.calculate_service_charges()
        bill.calculate_tax()
        bill.calculate_total()
        self.bills.append(bill)
        self._save_bills()
        return bill

    def add_service_to_bill(
        self,
        bill_id: str,
        service_id: str,
        quantity: int,
    ) -> Bill:
        """Add a service to a bill for a still checked-in booking."""
        bill = self._require_bill(bill_id)
        booking = self._require_booking_for_bill(bill)
        if booking.status != "Checked-in":
            raise ValueError("Services can only be added before checkout.")
        service = self.find_service(service_id)
        if service is None:
            raise KeyError(f"Service ID '{service_id}' was not found.")
        bill.add_service(service, quantity)
        self._recalculate_bill(bill, booking)
        self._save_bills()
        return bill

    def apply_discount_to_bill(self, bill_id: str, discount: float) -> Bill:
        """Apply and persist a valid discount before checkout."""
        bill = self._require_bill(bill_id)
        booking = self._require_booking_for_bill(bill)
        if booking.status != "Checked-in":
            raise ValueError("Discounts can only be applied before checkout.")
        bill.apply_discount(discount)
        self._recalculate_bill(bill, booking)
        self._save_bills()
        return bill

    def checkout(self, bill_id: str) -> Bill:
        """Complete checkout through BookingManager and append stay history.

        The bill is recalculated before checkout. BookingManager performs the
        state transition and room-status recalculation; this class does not
        duplicate either rule.
        """
        bill = self._require_bill(bill_id)
        booking = self._require_booking_for_bill(bill)
        room = self.room_manager.get_room(booking.room_no)
        if room is None:
            raise KeyError(f"Room number '{booking.room_no}' was not found.")
        if booking.status == "Checked-out" and bill.payment_status == "Paid":
            # A completed checkout can be retried only to repair a history
            # append that failed after the booking and bill were saved.
            self._append_history_once(bill, booking, room)
            return bill
        if booking.status != "Checked-in":
            raise ValueError(
                "Checkout requires a checked-in booking and cannot be repeated."
            )
        self._recalculate_bill(bill, booking)
        self._save_bills()
        self.booking_manager.checkout_guest(booking.booking_id)
        bill.payment_status = "Paid"
        self._save_bills()
        self._append_history_once(bill, booking, room)
        return bill

    def repair_history(self, bill_id: str) -> Bill:
        """Retry the history append for a completed, paid checkout.

        This recovery is idempotent: an existing matching history marker is
        detected before another line is appended.

        Raises:
            KeyError: If the bill, booking, or room is unknown.
            ValueError: If the bill is not a completed paid checkout.
            FileManagerError: If the history file cannot be read or appended.
        """
        bill = self._require_bill(bill_id)
        booking = self._require_booking_for_bill(bill)
        if booking.status != "Checked-out" or bill.payment_status != "Paid":
            raise ValueError("Only a completed paid checkout can repair history.")
        room = self.room_manager.get_room(booking.room_no)
        if room is None:
            raise KeyError(f"Room number '{booking.room_no}' was not found.")
        self._append_history_once(bill, booking, room)
        return bill

    def _load_services(self) -> list[Service]:
        """Load existing service definitions without replacing them."""
        self.file_manager.initialize_json_file(self.SERVICES_FILE, [])
        raw_services = self.file_manager.load_json(self.SERVICES_FILE)
        if not isinstance(raw_services, list):
            raise ValueError("Service data must be stored as a JSON list.")
        services = []
        for record in raw_services:
            if not isinstance(record, dict):
                raise ValueError("Each service record must be a JSON object.")
            services.append(Service.from_dict(record))
        self._ensure_unique_ids(services)
        return services

    def _load_bills(self) -> list[Bill]:
        """Load saved bills and initialize bills.json only if missing."""
        self.file_manager.initialize_json_file(self.BILLS_FILE, [])
        raw_bills = self.file_manager.load_json(self.BILLS_FILE)
        if not isinstance(raw_bills, list):
            raise ValueError("Bill data must be stored as a JSON list.")
        bills = []
        for record in raw_bills:
            if not isinstance(record, dict):
                raise ValueError("Each bill record must be a JSON object.")
            bills.append(Bill.from_dict(record))
        self._ensure_unique_ids(bills)
        return bills

    def _save_bills(self) -> Path:
        """Persist every current bill through FileManager."""
        return self.file_manager.save_json(
            self.BILLS_FILE,
            [bill.to_dict() for bill in self.bills],
        )

    def _recalculate_bill(self, bill: Bill, booking: Booking) -> None:
        """Refresh all bill totals from the booking, room, and service lines."""
        room = self.room_manager.get_room(booking.room_no)
        if room is None:
            raise KeyError(f"Room number '{booking.room_no}' was not found.")
        bill.calculate_room_charge(booking, room)
        bill.calculate_service_charges()
        bill.calculate_tax()
        bill.calculate_total()

    def _append_history_once(
        self,
        bill: Bill,
        booking: Booking,
        room: Room,
    ) -> None:
        """Append one completed-stay line without duplicating a prior entry."""
        history = self.file_manager.read_text(self.HISTORY_FILE)
        marker = f"Booking: {booking.booking_id} | Bill: {bill.bill_id}"
        if marker in history:
            return
        guest = self.booking_manager.guest_manager.get_guest(booking.guest_id)
        guest_reference = booking.guest_id
        if guest is not None:
            guest_reference = f"{guest.guest_id} ({guest.name})"
        record = (
            f"{marker} | Guest: {guest_reference} | Room: {room.room_no} | "
            f"Check-in: {booking.check_in.isoformat()} | "
            f"Check-out: {booking.check_out.isoformat()} | "
            f"Total: INR {bill.total:.2f}\n"
        )
        self.file_manager.append_text(self.HISTORY_FILE, record)

    def _require_bill(self, bill_id: str) -> Bill:
        """Return a bill or raise a consistent unknown-ID error."""
        bill = self.find_bill(bill_id)
        if bill is None:
            raise KeyError(f"Bill ID '{bill_id}' was not found.")
        return bill

    def _require_booking_for_bill(self, bill: Bill) -> Booking:
        """Return the booking referenced by a bill."""
        booking = self.booking_manager.get_booking(bill.booking_id)
        if booking is None:
            raise KeyError(f"Booking ID '{bill.booking_id}' was not found.")
        return booking

    @staticmethod
    def _required_text(field_name: str, value: str) -> str:
        """Validate text used for service and bill lookup."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be non-empty text.")
        return value.strip()

    @staticmethod
    def _ensure_unique_ids(records: list[object]) -> None:
        """Reject duplicate service or bill identifiers while loading."""
        seen_ids: set[str] = set()
        for record in records:
            normalized_id = record.service_id.casefold() if isinstance(
                record, Service
            ) else record.bill_id.casefold()
            if normalized_id in seen_ids:
                raise ValueError("Duplicate service or bill ID found.")
            seen_ids.add(normalized_id)
