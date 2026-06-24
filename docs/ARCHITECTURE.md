# Architecture

Four domains, each following Controller -> Service -> Repository, plus a
small set of shared utilities.

## Domains

**Authentication** — register, login, refresh session, load profile.
Controller: `AuthController`. Service: `AuthService`. Repository:
`UserRepository`. Utility: `JwtHelper`.

**Orders** — create, submit, cancel, total an order. Controller:
`OrderController`. Service: `OrderService`. Repository: `OrderRepository`.
`OrderService` also calls `InventoryService` directly (a service-to-service
call, not just a repository call) to reserve/release stock as part of
order creation/cancellation.

**Inventory** — stock check, reservation, release, adjustment. Service:
`InventoryService`. Repository: `InventoryRepository`. Has no controller
of its own in this slice — it's only reached through `OrderService`.

**Payments** — card validation, charge, refund, receipt. Controller:
`PaymentController`. Service: `PaymentService`. Talks to `UserRepository`
directly (to look up the paying user) and to the external-gateway stub
`PaymentGatewayClient`.

## Shared utilities

- `AuditLogger` — used by all four services (`AuthService`,
  `InventoryService`, `OrderService`, `PaymentService`). The most
  fan-in dependency in the repo; good for "where is X used across the
  whole codebase" queries.
- `Notifier` — used by both `OrderService` (order confirmation) and
  `PaymentService` (payment/refund receipt). Two distinct call sites,
  good for testing multi-file usage retrieval on a single class.
- `JwtHelper` — used only by `AuthService`.
- `PaymentGatewayClient` — used only by `PaymentService`.

## Known, intentional issues (for security/QA test scenarios)

These are real, present in the code, and meant to be found by a
correct review — not fixed silently:

1. `src/utils/jwt_helper.py` — `SECRET_KEY` is hardcoded in source
   instead of loaded from an environment variable or secret manager.
2. `src/services/auth_service.py` — `authenticate_user()` compares
   password hashes with plain `==` rather than a constant-time
   comparison (`hmac.compare_digest`), which is timing-attack prone.

A grounded indexing/search pipeline asked "find security issues in the
auth flow" should surface both of these from `jwt_helper.py` and
`auth_service.py` — and should NOT invent unrelated claims (e.g. TLS
version, path sanitization) that aren't present in this code.
