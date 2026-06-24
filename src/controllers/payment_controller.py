"""PaymentController: thin request-handling layer in front of PaymentService."""

from src.services.payment_service import PaymentService


class PaymentController:
    def __init__(self, payment_service: PaymentService = None):
        self.payment_service = payment_service or PaymentService()

    def process_payment(self, payload: dict) -> dict:
        return self.payment_service.charge_card(payload["user_id"], payload["card_number"], payload["amount"])

    def refund_payment(self, payload: dict) -> dict:
        return self.payment_service.refund_payment(payload["user_id"], payload["reference"], payload["amount"])

    def payment_status(self, payload: dict) -> dict:
        records = self.payment_service.audit_logger.search(actor=payload["user_id"])
        return {"records": records}
