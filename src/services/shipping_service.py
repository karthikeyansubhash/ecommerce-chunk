"""Shipping service for ecommerce-lite.

UC-07 test fixture — chunk boundary & content integrity.

This file is deliberately built with cascading function calls
(a method calling 2-3 other methods/functions within its own body)
to verify the chunker captures each function as ONE coherent chunk,
not split mid-function across the call sequence.

Key method under test: ShippingService.mark_shipped
  - performs two distinct operations in one body:
      1. status update (self.update_status)
      2. notification dispatch (Notifier.send)
  - the chunk for mark_shipped must span both calls, start to finish.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ShippingError(Exception):
    """Raised for invalid shipping operations."""


class ShipmentStatus(Enum):
    PENDING = "pending"
    PACKED = "packed"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    RETURNED = "returned"


@dataclass
class Shipment:
    shipment_id: str
    order_id: str
    status: ShipmentStatus = ShipmentStatus.PENDING
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    history: list[str] = field(default_factory=list)


class Notifier:
    """Lightweight notification dispatcher (email/SMS stub)."""

    def __init__(self):
        self.sent_log: list[str] = []

    def send(self, recipient_id: str, message: str) -> bool:
        """Dispatch a notification. Returns True on simulated success."""
        if not recipient_id or not message:
            raise ShippingError("recipient_id and message are required")
        self.sent_log.append(f"{recipient_id}: {message}")
        return True


class ShippingService:
    """Coordinates shipment lifecycle: packing, dispatch, tracking, delivery."""

    def __init__(self, notifier: Optional[Notifier] = None):
        self.shipments: dict[str, Shipment] = {}
        self.notifier = notifier or Notifier()

    def create_shipment(self, shipment_id: str, order_id: str) -> Shipment:
        if shipment_id in self.shipments:
            raise ShippingError(f"Shipment already exists: {shipment_id}")
        shipment = Shipment(shipment_id=shipment_id, order_id=order_id)
        shipment.history.append(f"created at {datetime.utcnow().isoformat()}")
        self.shipments[shipment_id] = shipment
        return shipment

    def update_status(self, shipment_id: str, new_status: ShipmentStatus) -> Shipment:
        """Update shipment status and append an audit entry to its history."""
        shipment = self._get_shipment(shipment_id)
        shipment.status = new_status
        shipment.history.append(
            f"status changed to {new_status.value} at {datetime.utcnow().isoformat()}"
        )
        return shipment

    def assign_carrier(self, shipment_id: str, carrier: str, tracking_number: str) -> Shipment:
        shipment = self._get_shipment(shipment_id)
        if shipment.status != ShipmentStatus.PENDING:
            raise ShippingError("Carrier can only be assigned while shipment is pending")
        shipment.carrier = carrier
        shipment.tracking_number = tracking_number
        self.update_status(shipment_id, ShipmentStatus.PACKED)
        return shipment

    def mark_shipped(self, shipment_id: str, customer_id: str) -> Shipment:
        """Mark a shipment as shipped and notify the customer.

        Performs two distinct operations in sequence:
          1. Status update — transitions the shipment to SHIPPED and
             records the shipped_at timestamp via self.update_status.
          2. Notification dispatch — sends a tracking notification to
             the customer via Notifier.send.

        Both operations must be captured within this single method's
        chunk; this is the core boundary the chunker is being tested
        against.
        """
        shipment = self._get_shipment(shipment_id)
        if shipment.status != ShipmentStatus.PACKED:
            raise ShippingError("Shipment must be packed before it can be marked shipped")

        # Operation 1: status update (cascades into update_status, which
        # itself appends to history).
        self.update_status(shipment_id, ShipmentStatus.SHIPPED)
        shipment.shipped_at = datetime.utcnow()

        # Operation 2: notification dispatch (cascades into Notifier.send).
        tracking_msg = (
            f"Your order {shipment.order_id} has shipped via {shipment.carrier}. "
            f"Tracking number: {shipment.tracking_number}"
        )
        self.notifier.send(customer_id, tracking_msg)

        return shipment

    def mark_delivered(self, shipment_id: str, customer_id: str) -> Shipment:
        """Mark a shipment delivered and notify the customer — mirrors
        mark_shipped's two-operation pattern for consistency testing."""
        shipment = self._get_shipment(shipment_id)
        if shipment.status not in (ShipmentStatus.SHIPPED, ShipmentStatus.OUT_FOR_DELIVERY):
            raise ShippingError("Shipment must be shipped before it can be marked delivered")

        self.update_status(shipment_id, ShipmentStatus.DELIVERED)
        self.notifier.send(customer_id, f"Your order {shipment.order_id} has been delivered.")
        return shipment

    def initiate_return(self, shipment_id: str, customer_id: str, reason: str) -> Shipment:
        """Cascading example: validates, updates status, logs reason, notifies —
        four steps chained in one method body."""
        shipment = self._get_shipment(shipment_id)
        if shipment.status != ShipmentStatus.DELIVERED:
            raise ShippingError("Only delivered shipments can be returned")

        self.update_status(shipment_id, ShipmentStatus.RETURNED)
        shipment.history.append(f"return reason: {reason}")
        self.notifier.send(
            customer_id, f"Return initiated for order {shipment.order_id}: {reason}"
        )
        return shipment

    def get_tracking_summary(self, shipment_id: str) -> str:
        """Cascades into _get_shipment and reads multiple fields to build
        a human-readable summary line."""
        shipment = self._get_shipment(shipment_id)
        return (
            f"Order {shipment.order_id} | Status: {shipment.status.value} | "
            f"Carrier: {shipment.carrier or 'N/A'} | "
            f"Tracking: {shipment.tracking_number or 'N/A'}"
        )

    def _get_shipment(self, shipment_id: str) -> Shipment:
        shipment = self.shipments.get(shipment_id)
        if shipment is None:
            raise ShippingError(f"No such shipment: {shipment_id}")
        return shipment
