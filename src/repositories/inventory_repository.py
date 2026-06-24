"""InventoryRepository: in-memory stock ledger.

Used by: InventoryService only.
"""


class InventoryRepository:
    def __init__(self):
        # sku -> {"available": int, "reserved": int}
        self._stock = {}

    def seed(self, sku: str, available: int) -> None:
        self._stock[sku] = {"available": available, "reserved": 0}

    def find_item(self, sku: str) -> dict:
        return self._stock.get(sku)

    def reserve_item(self, sku: str, quantity: int) -> bool:
        item = self._stock.get(sku)
        if not item or item["available"] < quantity:
            return False
        item["available"] -= quantity
        item["reserved"] += quantity
        return True

    def release_item(self, sku: str, quantity: int) -> bool:
        item = self._stock.get(sku)
        if not item or item["reserved"] < quantity:
            return False
        item["reserved"] -= quantity
        item["available"] += quantity
        return True

    def adjust_stock(self, sku: str, delta: int) -> dict:
        item = self._stock.setdefault(sku, {"available": 0, "reserved": 0})
        item["available"] = max(0, item["available"] + delta)
        return item
