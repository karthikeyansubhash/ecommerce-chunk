"""InventoryService: stock checks, reservation, release.

Depends on: InventoryRepository, AuditLogger.
"""

from src.repositories.inventory_repository import InventoryRepository
from src.utils.audit_logger import AuditLogger


class InventoryService:
    def __init__(self, inventory_repository: InventoryRepository = None, audit_logger: AuditLogger = None):
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.audit_logger = audit_logger or AuditLogger()

    def check_stock(self, sku: str) -> dict:
        item = self.inventory_repository.find_item(sku)
        if item is None:
            raise ValueError(f"Unknown SKU: {sku}")
        return item

    def reserve_stock(self, sku: str, quantity: int) -> bool:
        ok = self.inventory_repository.reserve_item(sku, quantity)
        self.audit_logger.record(actor="system", action="reserve_stock",
                                  details={"sku": sku, "quantity": quantity, "success": ok})
        return ok

    def release_stock(self, sku: str, quantity: int) -> bool:
        ok = self.inventory_repository.release_item(sku, quantity)
        self.audit_logger.record(actor="system", action="release_stock",
                                  details={"sku": sku, "quantity": quantity, "success": ok})
        return ok

    def update_inventory(self, sku: str, delta: int) -> dict:
        item = self.inventory_repository.adjust_stock(sku, delta)
        self.audit_logger.record(actor="system", action="update_inventory",
                                  details={"sku": sku, "delta": delta})
        return item
