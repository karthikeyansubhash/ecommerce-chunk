"""PaymentGatewayClient: stand-in for an external payment processor.

Used by: PaymentService only. No network calls -- deterministic stub so
the repo has zero external dependencies.
"""

import random


class PaymentGatewayClient:
    def __init__(self, decline_rate: float = 0.0):
        # decline_rate lets tests force deterministic failures (set to 1.0)
        self.decline_rate = decline_rate

    def charge(self, card_number: str, amount: float) -> dict:
        if self.decline_rate and random.random() < self.decline_rate:
            return {"status": "declined", "reference": None}
        masked = f"****{card_number[-4:]}" if len(card_number) >= 4 else "****"
        return {"status": "approved", "reference": f"txn_{abs(hash((masked, amount)))}"}

    def refund(self, reference: str, amount: float) -> dict:
        if not reference:
            return {"status": "failed", "reason": "missing reference"}
        return {"status": "refunded", "reference": reference, "amount": amount}
