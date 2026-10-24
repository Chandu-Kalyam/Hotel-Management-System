"""Hotel service entity used by the billing part of the application."""

from __future__ import annotations

# Used to reject NaN and infinity in service prices.
import math

# Used for values loaded from JSON before service fields are validated.
from typing import Any


class Service:
    """Represent one optional hotel service and its INR unit price."""

    def __init__(
        self,
        service_id: str,
        name: str,
        category: str,
        price: float,
    ) -> None:
        """Create a service after validating its required fields.

        Raises:
            ValueError: If text is empty or the price is not positive.
        """
        self.service_id = self._required_text("service_id", service_id)
        self.name = self._required_text("name", name)
        self.category = self._required_text("category", category)
        self.price = self._positive_price(price)

    def display_details(self) -> str:
        """Return readable service information for a future UI."""
        return (
            f"{self.name} ({self.category}) - "
            f"INR {self.price:.2f} per unit"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert this service to the structure used in services.json."""
        return {
            "service_id": self.service_id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Service:
        """Reconstruct a Service from one saved JSON object."""
        required_fields = ("service_id", "name", "category", "price")
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(f"Service data is missing required field(s): {fields}.")
        return cls(
            service_id=data["service_id"],
            name=data["name"],
            category=data["category"],
            price=data["price"],
        )

    @staticmethod
    def _required_text(field_name: str, value: Any) -> str:
        """Validate one required text field."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be non-empty text.")
        return value.strip()

    @staticmethod
    def _positive_price(value: Any) -> float:
        """Validate a positive numeric INR price."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("price must be a positive number.")
        if not math.isfinite(float(value)) or value <= 0:
            raise ValueError("price must be a positive number.")
        return round(float(value), 2)
