import logging
from typing import Any
from app.repositories.user_repository import user_repository
from app.utils.security import hash_password, verify_password, create_access_token
from app.database.connection import serialize_doc

logger = logging.getLogger(__name__)


class AuthService:
    """Business logic service for user registration, authentication, and profiles."""

    def register(self, data: dict[str, Any]) -> dict[str, Any]:
        email = data["email"].lower().strip()
        existing = user_repository.find_by_email(email)
        if existing:
            raise ValueError(f"User with email '{email}' already exists.")

        hashed = hash_password(data["password"])
        user_doc = {
            "name": data["name"].strip(),
            "email": email,
            "password_hash": hashed,
            "phone": data.get("phone"),
            "role": data.get("role", "patient"),
        }

        created = user_repository.create(user_doc)
        token = create_access_token(
            user_id=str(created["_id"]),
            email=created["email"],
            role=created["role"],
            name=created["name"],
        )

        user_data = serialize_doc(created)
        if user_data:
            user_data.pop("password_hash", None)

        logger.info("User registered successfully: %s (role: %s)", email, created["role"])
        return {
            "user": user_data,
            "token": token,
        }

    def login(self, data: dict[str, Any]) -> dict[str, Any]:
        email = data["email"].lower().strip()
        password = data["password"]

        user = user_repository.find_by_email(email)
        if not user or not verify_password(password, user.get("password_hash", "")):
            raise ValueError("Invalid email or password.")

        token = create_access_token(
            user_id=str(user["_id"]),
            email=user["email"],
            role=user.get("role", "patient"),
            name=user.get("name", "User"),
        )

        user_data = serialize_doc(user)
        if user_data:
            user_data.pop("password_hash", None)

        logger.info("User logged in successfully: %s", email)
        return {
            "user": user_data,
            "token": token,
        }

    def get_user_profile(self, user_id: str) -> dict[str, Any]:
        user = user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user_data = serialize_doc(user)
        if user_data:
            user_data.pop("password_hash", None)
        return user_data or {}


auth_service = AuthService()
