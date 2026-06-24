"""AuditLogger: append-only in-memory audit trail.

Used by: AuthService, InventoryService, OrderService, PaymentService.
This is the most widely shared dependency in the repo -- useful for
"where is X used across the codebase" retrieval tests.
"""

import time


class AuditLogger:
    def __init__(self):
        self._records = []

    def record(self, actor: str, action: str, details: dict = None) -> dict:
        """Append a new audit entry and return it."""
        entry = {
            "timestamp": time.time(),
            "actor": actor,
            "action": action,
            "details": details or {},
        }
        self._records.append(entry)
        return entry

    def search(self, actor: str = None, action: str = None) -> list:
        """Filter recorded entries by actor and/or action."""
        results = self._records
        if actor is not None:
            results = [r for r in results if r["actor"] == actor]
        if action is not None:
            results = [r for r in results if r["action"] == action]
        return results

    def export(self) -> list:
        """Return a copy of the full audit trail."""
        return list(self._records)
