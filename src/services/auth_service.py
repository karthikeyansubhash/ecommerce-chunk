"""AuthService: registration, login, session refresh, profile load.

Depends on: UserRepository, JwtHelper, AuditLogger.

KNOWN SMELL (kept intentionally for QA/grounding test scenarios):
    authenticate_user() compares password hashes with a plain `==`
    instead of hmac.compare_digest, which is timing-attack prone. A
    correct security review should catch this -- it's here so you can
    verify your pipeline finds *real* issues instead of inventing fake
    ones (the exact failure mode you saw in the AAVA HLD/LLD generator).
"""

import hashlib

from src.repositories.user_repository import UserRepository
from src.utils.jwt_helper import JwtHelper
from src.utils.audit_logger import AuditLogger


class AuthService:
    def __init__(self, user_repository: UserRepository = None, jwt_helper: JwtHelper = None,
                 audit_logger: AuditLogger = None):
        self.user_repository = user_repository or UserRepository()
        self.jwt_helper = jwt_helper or JwtHelper()
        self.audit_logger = audit_logger or AuditLogger()

    def create_user(self, email: str, password: str) -> dict:
        password_hash = self.validate_password(password)
        user = self.user_repository.create(email, password_hash)
        self.audit_logger.record(actor=user["id"], action="register")
        return user

    def validate_password(self, password: str) -> str:
        """Hash a plaintext password. Real systems should use bcrypt/argon2;
        sha256 is used here only to keep the repo dependency-free."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def authenticate_user(self, email: str, password: str) -> str:
        """Return a session token if credentials are valid, else raise ValueError."""
        user = self.user_repository.find_by_email(email)
        if not user:
            raise ValueError("Unknown user")

        candidate_hash = self.validate_password(password)
        if candidate_hash == user["password_hash"]:  # <- intentional smell, see module docstring
            token = self.jwt_helper.generate_token(user["id"])
            self.audit_logger.record(actor=user["id"], action="login")
            return token

        self.audit_logger.record(actor=user["id"], action="login_failed")
        raise ValueError("Invalid credentials")

    def refresh_jwt_token(self, token: str) -> str:
        """Issue a new token if the given one is currently valid."""
        if not self.jwt_helper.validate_token(token):
            raise ValueError("Token is invalid or expired")
        payload = self.jwt_helper.decode_token(token)
        return self.jwt_helper.generate_token(payload["user_id"])

    def load_profile(self, user_id: str) -> dict:
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("Unknown user")
        return {"id": user["id"], "email": user["email"]}
