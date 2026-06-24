# ecommerce-lite

A small, fully working e-commerce backend used to test code indexing,
chunking, and semantic search. Unlike the previous test repo, every file
here has real, runnable logic — there is no filler text or repeated
boilerplate comments. All 8 unit tests pass (`pytest tests/`).

## Why this exists

To validate that an indexing/search pipeline can:
- Follow a real cross-file dependency chain (e.g. order creation actually
  calls into inventory reservation, not just a comment claiming it does).
- Distinguish a class's *definition* from its *usages* across layers.
- Retrieve the right chunk for symbol-, flow-, and file-type-specific
  queries (Python, Markdown, YAML, JSON, SQL).
- Catch real issues (two intentional, documented security smells) instead
  of hallucinating fake ones — see ARCHITECTURE.md.

## Layout

```
src/controllers/   request-handling layer (Auth, Order, Payment)
src/services/      business logic (Auth, Inventory, Order, Payment)
src/repositories/  in-memory persistence (User, Order, Inventory)
src/utils/         shared helpers (JwtHelper, AuditLogger, Notifier, PaymentGatewayClient)
tests/             pytest unit tests (test_auth_service.py, test_order_service.py)
sql/               schema definitions matching the repositories
config/            app + database config
docs/              architecture and per-flow documentation
```

## Running the tests

```
pip install pytest
pytest tests/ -v
```
