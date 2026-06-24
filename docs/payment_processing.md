# Payment Flow

1. **Charge** — `PaymentController.process_payment()` calls
   `PaymentService.charge_card()`. It looks up the paying user via
   `UserRepository.find_by_id()`, validates the card number format
   (`validate_card()`, a 13–19 digit regex check), then delegates the
   actual charge to `PaymentGatewayClient.charge()` (a deterministic
   stub — no real network call). The result is recorded via
   `build_audit_record()` + `AuditLogger.record()`, and on approval a
   receipt is sent through `send_notification()` -> `Notifier.send()`.

2. **Refund** — `PaymentController.refund_payment()` calls
   `PaymentService.refund_payment()`, which delegates to
   `PaymentGatewayClient.refund()`, audits the result the same way as a
   charge, and sends a refund notice on success.

3. **Status** — `PaymentController.payment_status()` reads the audit
   trail directly via `PaymentService.audit_logger.search()`, filtered
   by the requesting user.

Note: `PaymentService` does not call `OrderService` or vice versa in
this slice — payments and orders are only connected through the
controller layer in a real request flow, not through direct
service-to-service calls. Don't expect `order_service.py` to show up as
a code-level dependency of `payment_service.py`.
