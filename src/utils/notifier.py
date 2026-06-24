"""Notifier: sends order/payment notifications to the customer.

Used by: OrderService (order confirmation) and PaymentService (payment
receipt/refund notice). This is the real implementation of the
"Notifications" component referenced in ARCHITECTURE.md -- in the
previous synthetic repo this component was documented but never
actually existed in code, which is exactly the kind of doc/code mismatch
this repo is meant to let you test for.
"""


class Notifier:
    def __init__(self):
        self.sent = []  # in-memory outbox for test assertions

    def send(self, user_id: str, channel: str, message: str) -> dict:
        notification = {"user_id": user_id, "channel": channel, "message": message}
        self.sent.append(notification)
        return notification
