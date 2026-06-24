-- Backing store for InventoryRepository (src/repositories/inventory_repository.py)
CREATE TABLE inventory (
    sku         VARCHAR(50) PRIMARY KEY,
    available   INTEGER NOT NULL DEFAULT 0,
    reserved    INTEGER NOT NULL DEFAULT 0,
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
