-- Backing store for UserRepository (src/repositories/user_repository.py)
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(64)  NOT NULL,  -- sha256 hex digest, see AuthService.validate_password
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
