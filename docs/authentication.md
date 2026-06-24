# Authentication Flow

1. **Register** — `AuthController.register()` calls
   `AuthService.create_user()`, which hashes the password
   (`validate_password()`, sha256) and persists the user via
   `UserRepository.create()`. An `AuditLogger.record()` entry is written
   with action `"register"`.

2. **Login** — `AuthController.login()` calls
   `AuthService.authenticate_user()`. It looks the user up by email
   (`UserRepository.find_by_email()`), re-hashes the supplied password,
   and compares it to the stored hash. On success it issues a session
   token via `JwtHelper.generate_token()` and logs action `"login"`; on
   failure it logs `"login_failed"` and raises `ValueError`.

3. **Refresh** — `AuthController.refresh_token()` calls
   `AuthService.refresh_jwt_token()`, which validates the existing token
   (`JwtHelper.validate_token()`), decodes it (`JwtHelper.decode_token()`),
   and issues a new one for the same user id.

4. **Profile** — `AuthController.get_profile()` calls
   `AuthService.load_profile()`, which reads the user via
   `UserRepository.find_by_id()`.

5. **Logout** — `AuthController.logout()` is a stateless no-op (tokens
   aren't server-tracked) that still writes an audit entry directly via
   `auth_service.audit_logger.record()`.

See `docs/ARCHITECTURE.md` for the two intentional security smells in
this flow (hardcoded JWT secret, non-constant-time hash comparison).
