"""Shipping service for ecommerce-lite — NESTED FUNCTIONS variant.
 
Test fixture for chunk boundary behavior on nested (inner) functions.
Each method below contains one or more `def` statements declared
INSIDE the method body (true Python closures), not just calls to
other methods.
 
Question under test: does the chunker treat [outer method + all its
nested inner functions] as ONE chunk, or does it incorrectly split
an inner `def` into its own separate chunk / fail to capture it at all?
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
        if not recipient_id or not message:
            raise ShippingError("recipient_id and message are required")
        self.sent_log.append(f"{recipient_id}: {message}")
        return True
 
 
class ShippingService:
    """Coordinates shipment lifecycle. Methods below use nested
    (inner) functions instead of calling sibling methods, specifically
    to test how the chunker handles closures."""
 
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
 
    def mark_shipped(self, shipment_id: str, customer_id: str) -> Shipment:
        """Mark a shipment shipped and notify the customer.
 
        Contains TWO nested functions:
          1. _apply_status_update — closure that mutates shipment state
             and appends a history entry.
          2. _build_tracking_message — closure that formats the
             notification text.
 
        Both nested defs, plus the outer method body that calls them,
        must be captured as a single coherent chunk.
        """
        shipment = self._get_shipment(shipment_id)
        if shipment.status != ShipmentStatus.PACKED:
            raise ShippingError("Shipment must be packed before it can be marked shipped")
 
        def _apply_status_update() -> None:
            """Nested function #1: status transition + audit history."""
            shipment.status = ShipmentStatus.SHIPPED
            shipment.shipped_at = datetime.utcnow()
            shipment.history.append(
                f"status changed to shipped at {shipment.shipped_at.isoformat()}"
            )
 
        def _build_tracking_message() -> str:
            """Nested function #2: formats the customer-facing message."""
            return (
                f"Your order {shipment.order_id} has shipped via "
                f"{shipment.carrier}. Tracking number: {shipment.tracking_number}"
            )
 
        _apply_status_update()
        message = _build_tracking_message()
        self.notifier.send(customer_id, message)
 
        return shipment
 
    def mark_delivered(self, shipment_id: str, customer_id: str) -> Shipment:
        """Mirrors mark_shipped's nested-function pattern, with a third
        nested function added (validation), to test a method with
        THREE nested defs instead of two."""
        shipment = self._get_shipment(shipment_id)
 
        def _validate_can_deliver() -> None:
            """Nested function #1: precondition check."""
            if shipment.status not in (ShipmentStatus.SHIPPED, ShipmentStatus.OUT_FOR_DELIVERY):
                raise ShippingError("Shipment must be shipped before it can be marked delivered")
 
        def _apply_delivered_status() -> None:
            """Nested function #2: status transition + audit history."""
            shipment.status = ShipmentStatus.DELIVERED
            shipment.history.append(
                f"status changed to delivered at {datetime.utcnow().isoformat()}"
            )
 
        def _build_delivery_message() -> str:
            """Nested function #3: formats the customer-facing message."""
            return f"Your order {shipment.order_id} has been delivered."
 
        _validate_can_deliver()
        _apply_delivered_status()
        self.notifier.send(customer_id, _build_delivery_message())
 
        return shipment
 
    def initiate_return(self, shipment_id: str, customer_id: str, reason: str) -> Shipment:
        """Single nested function example — only one inner def, to give
        a contrast case against the two/three-nested-function methods
        above (tests whether chunk behavior differs by nesting count)."""
        shipment = self._get_shipment(shipment_id)
        if shipment.status != ShipmentStatus.DELIVERED:
            raise ShippingError("Only delivered shipments can be returned")
 
        def _record_return() -> str:
            """Nested function #1: applies status + builds notification text
            in one closure (combines two concerns into a single inner def,
            unlike mark_delivered which splits them into separate defs)."""
            shipment.status = ShipmentStatus.RETURNED
            shipment.history.append(f"return reason: {reason}")
            return f"Return initiated for order {shipment.order_id}: {reason}"
 
        notification_text = _record_return()
        self.notifier.send(customer_id, notification_text)
        return shipment
 
    def get_tracking_summary(self, shipment_id: str) -> str:
        """No nested functions — plain method, included as a control
        case alongside the nested-function methods above."""
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
