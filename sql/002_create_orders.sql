-- Backing store for OrderRepository (src/repositories/order_repository.py)
CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES users(id),
    status      VARCHAR(20)  NOT NULL DEFAULT 'created',  -- created | submitted | cancelled
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER       NOT NULL REFERENCES orders(id),
    sku         VARCHAR(50)   NOT NULL,
    quantity    INTEGER       NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
