from datetime import datetime, timezone
from typing import Any, Optional
from flask import jsonify, Response


def api_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    status_code: int = 200,
) -> tuple[Response, int]:
    """
    Standardized success API response envelope.
    """
    payload = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload), status_code


def api_error(
    message: str = "An error occurred",
    code: str = "BAD_REQUEST",
    status_code: int = 400,
    details: Optional[Any] = None,
) -> tuple[Response, int]:
    """
    Standardized error API response envelope.
    """
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload), status_code
