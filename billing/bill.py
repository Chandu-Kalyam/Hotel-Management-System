"""Bill entity and centralized hotel billing calculations."""

from __future__ import annotations

# Used to reject NaN and infinity before currency conversion.
import math

# Decimal keeps currency calculations predictable before JSON conversion.
from decimal import Decimal, ROUND_HALF_UP

# Used for values loaded from bills.json and service item dictionaries.
from typing import Any

# Bill calculations use existing booking nights and room pricing behavior.
from booking.booking import Booking
from room.room import Room
from billing.service import Service


class Bill:
    """Represent an itemized bill for one booking.

    The tax rate is a simple project demonstration rate. It is not intended
    to represent legally applicable tax rules.
    """

    DEMONSTRATION_TAX_RATE = Decimal("0.05")
    PAYMENT_STATUSES = ("Pending", "Paid")

    def __init__(
        self,
        bill_id: str,
        booking_id: str,
        room_charge: float = 0.0,
        service_charges: float = 0.0,
        tax: float = 0.0,
        discount: float = 0.0,
        total: float = 0.0,
        payment_status: str = "Pending",
        services: list[dict[str, Any]] | None = None,
    ) -> None:
        """Create a bill with validated saved amounts and service items."""
        self.bill_id = self._required_text("bill_id", bill_id)
        self.booking_id = self._required_text("booking_id", booking_id)
        self.room_charge = self._money(room_charge, "room_charge")
        self.service_charges = self._money(
            service_charges, "service_charges"
        )
        self.tax = self._money(tax, "tax")
        self.discount = self._money(discount, "discount")
        self.total = self._money(total, "total")
        if payment_status not in self.PAYMENT_STATUSES:
            raise ValueError(
                "payment_status must be Pending or Paid."
            )
        self.payment_status = payment_status
        self.services = self._validate_service_items(services or [])

    def add_service(self, service: Service, quantity: int) -> dict[str, Any]:
        """Add a positive quantity using a snapshot of the current service.

        Repeated additions of the same service are combined into one item,
        keeping the final bill easy to read.

        Raises:
            ValueError: If the service type or quantity is invalid.
        """
        if not isinstance(service, Service):
            raise ValueError("Only Service objects can be added to a bill.")
        self._validate_quantity(quantity)

        for item in self.services:
            if item["service_id"] == service.service_id:
                item["quantity"] += quantity
                item["line_total"] = self._rounded(
                    Decimal(str(item["unit_price"])) * item["quantity"]
                )
                self.calculate_service_charges()
                return item

        item = {
            "service_id": service.service_id,
            "name": service.name,
            "category": service.category,
            "unit_price": service.price,
            "quantity": quantity,
            "line_total": self._rounded(
                Decimal(str(service.price)) * quantity
            ),
        }
        self.services.append(item)
        self.calculate_service_charges()
        return item

    def calculate_room_charge(self, booking: Booking, room: Room) -> float:
        """Calculate nights multiplied by the room's polymorphic nightly price."""
        if not isinstance(booking, Booking) or not isinstance(room, Room):
            raise ValueError("calculate_room_charge needs Booking and Room objects.")
        self.room_charge = self._rounded(
            Decimal(str(booking.calculate_nights()))
            * Decimal(str(room.calculate_nightly_price()))
        )
        self.calculate_total()
        return self.room_charge

    def calculate_service_charges(self) -> float:
        """Calculate the sum of every itemized service line."""
        self.service_charges = self._rounded(
            sum(
                (
                    Decimal(str(item["line_total"]))
                    for item in self.services
                ),
                Decimal("0"),
            )
        )
        self.calculate_total()
        return self.service_charges

    def calculate_tax(self) -> float:
        """Calculate demonstration tax from room and service subtotal."""
        subtotal = Decimal(str(self.room_charge)) + Decimal(
            str(self.service_charges)
        )
        self.tax = self._rounded(subtotal * self.DEMONSTRATION_TAX_RATE)
        self.calculate_total()
        return self.tax

    def apply_discount(self, discount: float) -> float:
        """Apply a non-negative discount that cannot exceed the subtotal."""
        discount_amount = self._money(discount, "discount")
        subtotal = self._money(
            self.room_charge + self.service_charges,
            "subtotal",
        )
        if discount_amount > subtotal:
            raise ValueError("discount cannot exceed the subtotal.")
        self.discount = discount_amount
        self.calculate_total()
        return self.discount

    def calculate_total(self) -> float:
        """Calculate the non-negative final total from the bill components."""
        subtotal = Decimal(str(self.room_charge)) + Decimal(
            str(self.service_charges)
        )
        tax_amount = Decimal(str(self.tax))
        discount_amount = Decimal(str(self.discount))
        final_total = subtotal + tax_amount - discount_amount
        if final_total < 0:
            raise ValueError("The final bill total cannot be negative.")
        self.total = self._rounded(final_total)
        return self.total

    def generate_itemized_bill(self) -> str:
        """Return a readable itemized bill summary."""
        lines = [
            f"Bill: {self.bill_id}",
            f"Booking: {self.booking_id}",
            f"Room charge: INR {self.room_charge:.2f}",
        ]
        for item in self.services:
            lines.append(
                f"{item['name']} x {item['quantity']}: "
                f"INR {item['line_total']:.2f}"
            )
        lines.extend(
            [
                f"Service charges: INR {self.service_charges:.2f}",
                f"Tax (5% demonstration rate): INR {self.tax:.2f}",
                f"Discount: INR {self.discount:.2f}",
                f"Total: INR {self.total:.2f}",
                f"Payment status: {self.payment_status}",
            ]
        )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert this bill and its service items to JSON-compatible data."""
        return {
            "bill_id": self.bill_id,
            "booking_id": self.booking_id,
            "room_charge": self.room_charge,
            "service_charges": self.service_charges,
            "tax": self.tax,
            "discount": self.discount,
            "total": self.total,
            "payment_status": self.payment_status,
            "services": self.services,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Bill:
        """Reconstruct a Bill from one saved JSON object."""
        required_fields = (
            "bill_id",
            "booking_id",
            "room_charge",
            "service_charges",
            "tax",
            "discount",
            "total",
            "payment_status",
            "services",
        )
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(f"Bill data is missing required field(s): {fields}.")
        return cls(
            bill_id=data["bill_id"],
            booking_id=data["booking_id"],
            room_charge=data["room_charge"],
            service_charges=data["service_charges"],
            tax=data["tax"],
            discount=data["discount"],
            total=data["total"],
            payment_status=data["payment_status"],
            services=data["services"],
        )

    @classmethod
    def _validate_service_items(
        cls,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Validate saved service snapshots without sharing mutable input."""
        validated = []
        for item in items:
            required_fields = (
                "service_id",
                "name",
                "category",
                "unit_price",
                "quantity",
                "line_total",
            )
            if not isinstance(item, dict) or any(
                field not in item for field in required_fields
            ):
                raise ValueError("Each bill service item is incomplete.")
            cls._validate_quantity(item["quantity"])
            unit_price = cls._money(item["unit_price"], "unit_price")
            line_total = cls._money(item["line_total"], "line_total")
            expected_total = cls._rounded(
                Decimal(str(unit_price)) * item["quantity"]
            )
            if line_total != expected_total:
                raise ValueError("A service line total is incorrect.")
            validated.append(dict(item))
        return validated

    @staticmethod
    def _required_text(field_name: str, value: Any) -> str:
        """Validate one required bill identifier."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be non-empty text.")
        return value.strip()

    @staticmethod
    def _validate_quantity(quantity: Any) -> None:
        """Reject zero, negative, boolean, and non-integer quantities."""
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity <= 0
        ):
            raise ValueError("Service quantity must be at least 1.")

    @staticmethod
    def _money(value: Any, field_name: str) -> float:
        """Validate a non-negative amount and round it to two decimals."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a non-negative number.")
        if not math.isfinite(float(value)) or value < 0:
            raise ValueError(f"{field_name} must be a non-negative number.")
        return Bill._rounded(Decimal(str(value)))

    @staticmethod
    def _rounded(value: Decimal) -> float:
        """Round an amount using ordinary currency half-up rounding."""
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
