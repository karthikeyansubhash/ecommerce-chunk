"""Payment processing for ecommerce-lite.

Handles payment intent creation, capture, refunds, and basic
gateway abstraction (mock gateway for tests / local dev).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentError(Exception):
    """Raised for any payment-related failure."""


@dataclass
class PaymentIntent:
    intent_id: str
    order_id: str
    amount_cents: int
    currency: str = "usd"
    status: PaymentStatus = PaymentStatus.PENDING
    refunded_cents: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    gateway_ref: Optional[str] = None

    @property
    def remaining_refundable_cents(self) -> int:
        return self.amount_cents - self.refunded_cents


class MockGateway:
    """Mock payment gateway used for local/test environments.

    Simulates network failures via `fail_rate` for resilience testing.
    """

    def __init__(self, fail_rate: float = 0.0):
        if not 0.0 <= fail_rate <= 1.0:
            raise ValueError("fail_rate must be between 0 and 1")
        self.fail_rate = fail_rate
        self._call_count = 0

    def charge(self, amount_cents: int, currency: str) -> str:
        self._call_count += 1
        if amount_cents <= 0:
            raise PaymentError("Charge amount must be positive")
        # Deterministic pseudo-failure based on call count, not random,
        # so tests stay reproducible.
        if self.fail_rate > 0 and self._call_count % int(1 / self.fail_rate) == 0:
            raise PaymentError("Gateway declined the charge")
        return f"gw_{uuid.uuid4().hex[:12]}"

    def refund(self, gateway_ref: str, amount_cents: int) -> str:
        if amount_cents <= 0:
            raise PaymentError("Refund amount must be positive")
        return f"rf_{uuid.uuid4().hex[:12]}"


class PaymentProcessor:
    """Coordinates payment intents against a gateway."""

    def __init__(self, gateway: Optional[MockGateway] = None):
        self.gateway = gateway or MockGateway()
        self._intents: dict[str, PaymentIntent] = {}

    def create_intent(self, order_id: str, amount_cents: int, currency: str = "usd") -> PaymentIntent:
        if amount_cents <= 0:
            raise PaymentError("amount_cents must be positive")
        intent = PaymentIntent(
            intent_id=f"pi_{uuid.uuid4().hex[:16]}",
            order_id=order_id,
            amount_cents=amount_cents,
            currency=currency,
        )
        self._intents[intent.intent_id] = intent
        return intent

    def capture(self, intent_id: str) -> PaymentIntent:
        intent = self._get_intent(intent_id)
        if intent.status != PaymentStatus.PENDING:
            raise PaymentError(f"Cannot capture intent in status {intent.status}")
        gateway_ref = self.gateway.charge(intent.amount_cents, intent.currency)
        intent.status = PaymentStatus.CAPTURED
        intent.gateway_ref = gateway_ref
        return intent

    def refund(self, intent_id: str, amount_cents: Optional[int] = None) -> PaymentIntent:
        intent = self._get_intent(intent_id)
        if intent.status not in (PaymentStatus.CAPTURED, PaymentStatus.PARTIALLY_REFUNDED):
            raise PaymentError(f"Cannot refund intent in status {intent.status}")

        refund_amount = amount_cents if amount_cents is not None else intent.remaining_refundable_cents
        if refund_amount > intent.remaining_refundable_cents:
            raise PaymentError("Refund amount exceeds remaining refundable balance")

        self.gateway.refund(intent.gateway_ref or "", refund_amount)
        intent.refunded_cents += refund_amount
        intent.status = (
            PaymentStatus.REFUNDED
            if intent.refunded_cents == intent.amount_cents
            else PaymentStatus.PARTIALLY_REFUNDED
        )
        return intent

    def _get_intent(self, intent_id: str) -> PaymentIntent:
        intent = self._intents.get(intent_id)
        if intent is None:
            raise PaymentError(f"No such payment intent: {intent_id}")
        return intent
