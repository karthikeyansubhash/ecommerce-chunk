"""Inventory and stock management for ecommerce-lite."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class StockMovementType(Enum):
    RESTOCK = "restock"
    SALE = "sale"
    RESERVATION = "reservation"
    RESERVATION_RELEASE = "reservation_release"
    ADJUSTMENT = "adjustment"


class InventoryError(Exception):
    """Raised for invalid inventory operations."""


@dataclass
class StockMovement:
    sku: str
    movement_type: StockMovementType
    quantity: int
    reference_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StockLevel:
    sku: str
    on_hand: int = 0
    reserved: int = 0
    reorder_threshold: int = 10

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved

    @property
    def needs_reorder(self) -> bool:
        return self.available <= self.reorder_threshold


class InventoryManager:
    """Tracks stock levels and reservations across SKUs."""

    def __init__(self):
        self._stock: dict[str, StockLevel] = {}
        self._movements: list[StockMovement] = []

    def register_sku(self, sku: str, initial_quantity: int = 0, reorder_threshold: int = 10) -> StockLevel:
        if sku in self._stock:
            raise InventoryError(f"SKU already registered: {sku}")
        level = StockLevel(sku=sku, on_hand=initial_quantity, reorder_threshold=reorder_threshold)
        self._stock[sku] = level
        if initial_quantity > 0:
            self._record(sku, StockMovementType.RESTOCK, initial_quantity)
        return level

    def restock(self, sku: str, quantity: int, reference_id: Optional[str] = None) -> StockLevel:
        if quantity <= 0:
            raise InventoryError("Restock quantity must be positive")
        level = self._get(sku)
        level.on_hand += quantity
        self._record(sku, StockMovementType.RESTOCK, quantity, reference_id)
        return level

    def reserve(self, sku: str, quantity: int, reference_id: Optional[str] = None) -> StockLevel:
        if quantity <= 0:
            raise InventoryError("Reserve quantity must be positive")
        level = self._get(sku)
        if level.available < quantity:
            raise InventoryError(f"Insufficient available stock for {sku}: have {level.available}, need {quantity}")
        level.reserved += quantity
        self._record(sku, StockMovementType.RESERVATION, quantity, reference_id)
        return level

    def release_reservation(self, sku: str, quantity: int, reference_id: Optional[str] = None) -> StockLevel:
        level = self._get(sku)
        if quantity > level.reserved:
            raise InventoryError("Cannot release more than currently reserved")
        level.reserved -= quantity
        self._record(sku, StockMovementType.RESERVATION_RELEASE, quantity, reference_id)
        return level

    def fulfill_sale(self, sku: str, quantity: int, reference_id: Optional[str] = None) -> StockLevel:
        """Convert a reservation into a completed sale, decrementing on_hand."""
        level = self._get(sku)
        if quantity > level.reserved:
            raise InventoryError("Cannot fulfill more than currently reserved")
        if quantity > level.on_hand:
            raise InventoryError("Cannot fulfill more than on-hand stock")
        level.reserved -= quantity
        level.on_hand -= quantity
        self._record(sku, StockMovementType.SALE, quantity, reference_id)
        return level

    def adjust(self, sku: str, delta: int, reference_id: Optional[str] = None) -> StockLevel:
        """Manual stock correction, e.g. after a physical count or damage write-off."""
        level = self._get(sku)
        new_on_hand = level.on_hand + delta
        if new_on_hand < 0:
            raise InventoryError("Adjustment would result in negative stock")
        level.on_hand = new_on_hand
        self._record(sku, StockMovementType.ADJUSTMENT, delta, reference_id)
        return level

    def skus_needing_reorder(self) -> list[StockLevel]:
        return [level for level in self._stock.values() if level.needs_reorder]

    def movement_history(self, sku: str) -> list[StockMovement]:
        return [m for m in self._movements if m.sku == sku]

    def _record(
        self,
        sku: str,
        movement_type: StockMovementType,
        quantity: int,
        reference_id: Optional[str] = None,
    ) -> None:
        self._movements.append(
            StockMovement(sku=sku, movement_type=movement_type, quantity=quantity, reference_id=reference_id)
        )

    def _get(self, sku: str) -> StockLevel:
        level = self._stock.get(sku)
        if level is None:
            raise InventoryError(f"Unknown SKU: {sku}")
        return level
