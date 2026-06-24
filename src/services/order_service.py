"""OrderService: order creation, totals, submission, cancellation.

Depends on: OrderRepository, InventoryService, Notifier, AuditLogger.
Note the cross-domain hop: create_order() calls InventoryService to
reserve stock before the order is persisted -- this is the real
"order creation touches inventory" relationship that the previous
synthetic repo only described in CLASS_CALL_MAP.md without making
visible in actual code.
"""

from src.repositories.order_repository import OrderRepository
from src.services.inventory_service import InventoryService
from src.utils.notifier import Notifier
from src.utils.audit_logger import AuditLogger


class OrderService:
    def __init__(self, order_repository: OrderRepository = None, inventory_service: InventoryService = None,
                 notifier: Notifier = None, audit_logger: AuditLogger = None):
        self.order_repository = order_repository or OrderRepository()
        self.inventory_service = inventory_service or InventoryService()
        self.notifier = notifier or Notifier()
        self.audit_logger = audit_logger or AuditLogger()

    def create_order(self, user_id: str, items: list) -> dict:
        """items: list of {"sku": str, "quantity": int, "price": float}."""
        for item in items:
            reserved = self.inventory_service.reserve_stock(item["sku"], item["quantity"])
            if not reserved:
                raise ValueError(f"Insufficient stock for SKU {item['sku']}")

        order = self.order_repository.save_order(user_id, items, status="created")
        self.audit_logger.record(actor=user_id, action="create_order", details={"order_id": order["id"]})
        return order

    def calculate_totals(self, order_id: str) -> float:
        order = self.order_repository.load_order(order_id)
        if not order:
            raise ValueError("Unknown order")
        return sum(item["price"] * item["quantity"] for item in order["items"])

    def submit_order(self, order_id: str) -> dict:
        order = self.order_repository.update_order(order_id, status="submitted")
        self.notifier.send(order["user_id"], channel="email", message=f"Order {order_id} confirmed.")
        self.audit_logger.record(actor=order["user_id"], action="submit_order", details={"order_id": order_id})
        return order

    def cancel_order(self, order_id: str) -> dict:
        order = self.order_repository.load_order(order_id)
        if not order:
            raise ValueError("Unknown order")
        for item in order["items"]:
            self.inventory_service.release_stock(item["sku"], item["quantity"])
        cancelled = self.order_repository.update_order(order_id, status="cancelled")
        self.audit_logger.record(actor=order["user_id"], action="cancel_order", details={"order_id": order_id})
        return cancelled
