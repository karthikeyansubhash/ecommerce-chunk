"""Inventory service for ecommerce-lite (post-change).

UC02 modified file — low-stock alert story implemented inside
reserve_stock only. No new methods added.

Expected chunking after re-index: STILL 5 chunks —
__init__, check_stock, reserve_stock, release_stock, update_inventory.
reserve_stock's line range grows, but chunk count must stay the same
(no split, no merge, no new chunk).
"""

from __future__ import annotations


class InventoryServiceError(Exception):
    """Raised for invalid inventory operations."""


class InventoryService:
    def __init__(self, low_stock_threshold: int = 10):
        self.stock: dict[str, int] = {}
        self.reserved: dict[str, int] = {}
        self.low_stock_threshold = low_stock_threshold
        self.low_stock_alerts: list[str] = []

    def check_stock(self, sku: str) -> int:
        """Return current on-hand stock for a SKU, defaulting to 0 if unknown."""
        return self.stock.get(sku, 0)

    def reserve_stock(self, sku: str, quantity: int) -> bool:
        """Reserve units of a SKU for an order.

        Returns True if reservation succeeded, False if insufficient stock.

        Low-stock alert story: after a successful reservation, if the
        remaining available stock for this SKU drops to or below the
        configured low_stock_threshold, an alert is recorded so
        downstream notification/restocking workflows can pick it up.
        """
        if quantity <= 0:
            raise InventoryServiceError("quantity must be positive")

        available = self.check_stock(sku) - self.reserved.get(sku, 0)
        if available < quantity:
            return False

        self.reserved[sku] = self.reserved.get(sku, 0) + quantity

        remaining_available = self.check_stock(sku) - self.reserved.get(sku, 0)
        if remaining_available <= self.low_stock_threshold:
            alert_message = (
                f"Low stock alert: SKU '{sku}' has {remaining_available} units testing"
                f"remaining (threshold: {self.low_stock_threshold})"
            )
            if alert_message not in self.low_stock_alerts:
                self.low_stock_alerts.append(alert_message)

        return True

    def release_stock(self, sku: str, quantity: int) -> None:
        """Release a previously made reservation, e.g. on order cancellation."""
        if quantity <= 0:
            raise InventoryServiceError("quantity must be positive")

        current_reserved = self.reserved.get(sku, 0)
        if quantity > current_reserved:
            raise InventoryServiceError("Cannot release more than currently reserved")

        self.reserved[sku] = current_reserved - quantity

    def update_inventory(self, sku: str, delta: int) -> int:
        """Adjust on-hand inventory by delta (positive for restock, negative for write-off)."""
        new_quantity = self.stock.get(sku, 0) + delta
        if new_quantity < 0:
            raise InventoryServiceError("Inventory cannot go negative")

        self.stock[sku] = new_quantity
        return new_quantity
