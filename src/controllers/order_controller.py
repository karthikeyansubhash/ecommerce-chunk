"""OrderController: thin request-handling layer in front of OrderService."""

from src.services.order_service import OrderService


class OrderController:
    def __init__(self, order_service: OrderService = None):
        self.order_service = order_service or OrderService()

    def create_order(self, payload: dict) -> dict:
        return self.order_service.create_order(payload["user_id"], payload["items"])

    def cancel_order(self, payload: dict) -> dict:
        return self.order_service.cancel_order(payload["order_id"])

    def get_order(self, payload: dict) -> dict:
        order = self.order_service.order_repository.load_order(payload["order_id"])
        if not order:
            raise ValueError("Unknown order")
        return order

    def update_order(self, payload: dict) -> dict:
        if payload.get("action") == "submit":
            return self.order_service.submit_order(payload["order_id"])
        raise ValueError(f"Unsupported action: {payload.get('action')}")
