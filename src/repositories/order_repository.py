"""OrderRepository: in-memory persistence for orders.

Used by: OrderService only.
"""


class OrderRepository:
    def __init__(self):
        self._orders = {}
        self._next_id = 1

    def save_order(self, user_id: str, items: list, status: str = "created") -> dict:
        order_id = str(self._next_id)
        self._next_id += 1
        order = {"id": order_id, "user_id": user_id, "items": items, "status": status}
        self._orders[order_id] = order
        return order

    def load_order(self, order_id: str) -> dict:
        return self._orders.get(order_id)

    def update_order(self, order_id: str, **fields) -> dict:
        if order_id not in self._orders:
            raise KeyError(f"No order with id {order_id}")
        self._orders[order_id].update(fields)
        return self._orders[order_id]

    def delete_order(self, order_id: str) -> bool:
        return self._orders.pop(order_id, None) is not None

    def list_orders_by_user(self, user_id: str) -> list:
        return [o for o in self._orders.values() if o["user_id"] == user_id]
