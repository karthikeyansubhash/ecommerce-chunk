"""JwtHelper: issues and verifies signed session tokens.

Real format (not the real JWT spec, kept simple on purpose):
    base64(payload_json) + "." + hmac_sha256(secret, payload_json)

Used by: AuthService only.

KNOWN SMELL (kept intentionally for QA/grounding test scenarios):
    SECRET_KEY is hardcoded below instead of pulled from environment/secret
    manager. A correct security review of auth_service.py / jwt_helper.py
    should flag this. Do not "fix" it silently when testing -- it exists so
    you can verify whether your indexing + LLM pipeline actually catches
    real issues instead of hallucinating fake ones.
"""

import base64
import hashlib
import hmac
import json
import time

SECRET_KEY = "super-secret-do-not-hardcode-in-real-systems"  # <- intentional smell
TOKEN_TTL_SECONDS = 3600


class JwtHelper:
    def __init__(self, secret: str = SECRET_KEY, ttl_seconds: int = TOKEN_TTL_SECONDS):
        self.secret = secret
        self.ttl_seconds = ttl_seconds

    def generate_token(self, user_id: str) -> str:
        """Create a signed token for the given user id."""
        payload = {"user_id": user_id, "issued_at": time.time()}
        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = self._sign(payload_bytes)
        encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8")
        return f"{encoded_payload}.{signature}"

    def validate_token(self, token: str) -> bool:
        """Return True if the token's signature is valid and it has not expired."""
        try:
            encoded_payload, signature = token.split(".")
            payload_bytes = base64.urlsafe_b64decode(encoded_payload)
        except (ValueError, base64.binascii.Error):
            return False

        expected_signature = self._sign(payload_bytes)
        if not hmac.compare_digest(expected_signature, signature):
            return False

        payload = json.loads(payload_bytes)
        age = time.time() - payload["issued_at"]
        return age <= self.ttl_seconds

    def decode_token(self, token: str) -> dict:
        """Decode and return the payload without checking expiry. Raises on bad signature."""
        encoded_payload, signature = token.split(".")
        payload_bytes = base64.urlsafe_b64decode(encoded_payload)
        if not hmac.compare_digest(self._sign(payload_bytes), signature):
            raise ValueError("Invalid token signature")
        return json.loads(payload_bytes)

    def _sign(self, payload_bytes: bytes) -> str:
        return hmac.new(self.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
