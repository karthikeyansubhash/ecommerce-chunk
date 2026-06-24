"""AuthController: thin request-handling layer in front of AuthService."""

from src.services.auth_service import AuthService


class AuthController:
    def __init__(self, auth_service: AuthService = None):
        self.auth_service = auth_service or AuthService()

    def register(self, payload: dict) -> dict:
        return self.auth_service.create_user(payload["email"], payload["password"])

    def login(self, payload: dict) -> dict:
        token = self.auth_service.authenticate_user(payload["email"], payload["password"])
        return {"token": token}

    def logout(self, payload: dict) -> dict:
        # Stateless tokens: logout is a client-side no-op, but we still audit it
        # via the service's audit logger for traceability.
        self.auth_service.audit_logger.record(actor=payload.get("user_id", "unknown"), action="logout")
        return {"status": "logged_out"}

    def refresh_token(self, payload: dict) -> dict:
        new_token = self.auth_service.refresh_jwt_token(payload["token"])
        return {"token": new_token}

    def get_profile(self, payload: dict) -> dict:
        return self.auth_service.load_profile(payload["user_id"])
