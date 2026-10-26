from functools import wraps
from typing import Callable, Any
from flask import request
import jwt
from app.utils.security import decode_access_token
from app.utils.response import api_error


def jwt_required(f: Callable) -> Callable:
    """Decorator to enforce and decode JWT access tokens from Authorization header."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return api_error(
                message="Authorization token is missing. Please provide 'Bearer <token>' in header.",
                code="UNAUTHORIZED",
                status_code=401,
            )

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return api_error(
                message="Invalid Authorization header format. Format must be 'Bearer <token>'.",
                code="INVALID_HEADER",
                status_code=401,
            )

        token = parts[1]
        try:
            payload = decode_access_token(token)
            # Attach current_user payload to request context
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return api_error(
                message="Your session has expired. Please log in again.",
                code="TOKEN_EXPIRED",
                status_code=401,
            )
        except (jwt.InvalidTokenError, Exception) as err:
            return api_error(
                message=f"Invalid or malformed authentication token: {str(err)}",
                code="INVALID_TOKEN",
                status_code=401,
            )

        return f(*args, **kwargs)

    return decorated_function


def roles_required(*allowed_roles: str) -> Callable:
    """
    Decorator to restrict access to specific roles (e.g., 'doctor', 'staff', 'admin').
    Must be placed after @jwt_required or will automatically require jwt.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            current_user = getattr(request, "current_user", None)
            if not current_user:
                return api_error(
                    message="Authentication required for this endpoint.",
                    code="UNAUTHORIZED",
                    status_code=401,
                )

            user_role = current_user.get("role")
            if user_role not in allowed_roles:
                return api_error(
                    message=f"Access denied. Required roles: {list(allowed_roles)}. Your role: '{user_role}'.",
                    code="FORBIDDEN",
                    status_code=403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
