# Order Flow

1. **Create** — `OrderController.create_order()` calls
   `OrderService.create_order()`. For every line item it first calls
   `InventoryService.reserve_stock()` (which in turn calls
   `InventoryRepository.reserve_item()`); if any reservation fails the
   whole order is rejected with `ValueError` before anything is
   persisted. Only once every item is reserved does it persist the order
   via `OrderRepository.save_order()`.

2. **Totals** — `OrderService.calculate_totals()` reads the order via
   `OrderRepository.load_order()` and sums `price * quantity` across
   line items.

3. **Submit** — `OrderController.update_order()` with
   `{"action": "submit"}` calls `OrderService.submit_order()`, which
   marks the order `"submitted"` via `OrderRepository.update_order()`
   and sends a confirmation through `Notifier.send()`.

4. **Cancel** — `OrderController.cancel_order()` calls
   `OrderService.cancel_order()`, which releases every reserved line
   item back to inventory via `InventoryService.release_stock()` before
   marking the order `"cancelled"`.

Every step above also writes an `AuditLogger.record()` entry, which is
why `audit_logger.py` shows up as a dependency of nearly every flow in
this repo.
