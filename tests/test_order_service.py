"""Unit tests for OrderService, including the inventory cross-dependency."""

import pytest

from src.services.order_service import OrderService
from src.services.inventory_service import InventoryService
from src.repositories.inventory_repository import InventoryRepository


@pytest.fixture
def inventory_service():
    repo = InventoryRepository()
    repo.seed("SKU-1", available=10)
    return InventoryService(inventory_repository=repo)


@pytest.fixture
def order_service(inventory_service):
    return OrderService(inventory_service=inventory_service)


def test_create_order_reserves_stock(order_service, inventory_service):
    order = order_service.create_order("user-1", [{"sku": "SKU-1", "quantity": 3, "price": 9.99}])
    assert order["status"] == "created"
    item = inventory_service.check_stock("SKU-1")
    assert item["available"] == 7
    assert item["reserved"] == 3


def test_create_order_fails_when_stock_insufficient(order_service):
    with pytest.raises(ValueError):
        order_service.create_order("user-1", [{"sku": "SKU-1", "quantity": 999, "price": 9.99}])


def test_cancel_order_releases_stock(order_service, inventory_service):
    order = order_service.create_order("user-1", [{"sku": "SKU-1", "quantity": 4, "price": 5.0}])
    order_service.cancel_order(order["id"])
    item = inventory_service.check_stock("SKU-1")
    assert item["available"] == 10
    assert item["reserved"] == 0


def test_submit_order_sends_notification(order_service):
    order = order_service.create_order("user-1", [{"sku": "SKU-1", "quantity": 1, "price": 2.0}])
    order_service.submit_order(order["id"])
    assert len(order_service.notifier.sent) == 1
    assert order_service.notifier.sent[0]["user_id"] == "user-1"
