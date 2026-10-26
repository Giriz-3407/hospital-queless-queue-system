from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import jwt
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Hash password using Werkzeug's secure hashing (scrypt/pbkdf2)."""
    return generate_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against its hash."""
    if not plain_password or not hashed_password:
        return False
    return check_password_hash(hashed_password, plain_password)


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    name: str,
    expires_minutes: Optional[int] = None,
) -> str:
    """
    Generate a signed JWT token containing user identity and role.
    """
    secret = current_app.config.get("JWT_SECRET_KEY")
    if not secret:
        raise ValueError("JWT_SECRET_KEY is not configured in the application.")

    if expires_minutes is None:
        expires_minutes = current_app.config.get("ACCESS_TOKEN_EXPIRES_MINUTES", 60)

    now = datetime.now(timezone.utc)
    expiration = now + timedelta(minutes=expires_minutes)

    payload = {
        "sub": str(user_id),
        "email": email.lower().strip(),
        "role": role,
        "name": name,
        "iat": now,
        "exp": expiration,
        "iss": "queueless-smart-hospital",
    }

    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    secret = current_app.config.get("JWT_SECRET_KEY")
    if not secret:
        raise ValueError("JWT_SECRET_KEY is not configured in the application.")

    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        options={"require": ["sub", "role", "exp"]},
    )
