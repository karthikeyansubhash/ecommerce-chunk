"""PaymentService: card validation, charging, refunds, receipts.

Depends on: UserRepository, PaymentGatewayClient, Notifier, AuditLogger.
"""

import re

from src.repositories.user_repository import UserRepository
from src.utils.payment_gateway import PaymentGatewayClient
from src.utils.notifier import Notifier
from src.utils.audit_logger import AuditLogger

CARD_PATTERN = re.compile(r"^\d{13,19}$")


class PaymentService:
    def __init__(self, user_repository: UserRepository = None, gateway: PaymentGatewayClient = None,
                 notifier: Notifier = None, audit_logger: AuditLogger = None):
        self.user_repository = user_repository or UserRepository()
        self.gateway = gateway or PaymentGatewayClient()
        self.notifier = notifier or Notifier()
        self.audit_logger = audit_logger or AuditLogger()

    def validate_card(self, card_number: str) -> bool:
        return bool(CARD_PATTERN.match(card_number))

    def charge_card(self, user_id: str, card_number: str, amount: float) -> dict:
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("Unknown user")
        if not self.validate_card(card_number):
            raise ValueError("Invalid card number")

        result = self.gateway.charge(card_number, amount)
        record = self.build_audit_record(user_id, "charge", amount, result)
        self.audit_logger.record(**record)
        if result["status"] == "approved":
            self.send_notification(user_id, f"Payment of {amount} approved.")
        return result

    def refund_payment(self, user_id: str, reference: str, amount: float) -> dict:
        result = self.gateway.refund(reference, amount)
        record = self.build_audit_record(user_id, "refund", amount, result)
        self.audit_logger.record(**record)
        if result["status"] == "refunded":
            self.send_notification(user_id, f"Refund of {amount} processed.")
        return result

    def build_audit_record(self, user_id: str, action: str, amount: float, result: dict) -> dict:
        return {
            "actor": user_id,
            "action": f"payment_{action}",
            "details": {"amount": amount, "gateway_status": result["status"]},
        }

    def send_notification(self, user_id: str, message: str) -> dict:
        return self.notifier.send(user_id, channel="email", message=message)
