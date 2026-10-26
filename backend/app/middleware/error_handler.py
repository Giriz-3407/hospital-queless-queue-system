import logging
from flask import Flask
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from werkzeug.exceptions import HTTPException
from app.utils.response import api_error

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register custom JSON error handlers for common HTTP status codes and exceptions."""

    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(error: ValidationError):
        errors = error.errors()
        details = [
            {"loc": err["loc"], "msg": err["msg"], "type": err["type"]}
            for err in errors
        ]
        return api_error(
            message="Request validation failed. Please check your input fields.",
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )

    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError):
        return api_error(
            message=str(error),
            code="BAD_REQUEST",
            status_code=400,
        )

    @app.errorhandler(PermissionError)
    def handle_permission_error(error: PermissionError):
        return api_error(
            message=str(error),
            code="FORBIDDEN",
            status_code=403,
        )

    @app.errorhandler(PyMongoError)
    def handle_mongo_error(error: PyMongoError):
        logger.error("MongoDB Database Error: %s", error)
        return api_error(
            message="A database operation error occurred. Please try again later.",
            code="DATABASE_ERROR",
            status_code=500,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return api_error(
            message=error.description or "An HTTP error occurred.",
            code=error.name.upper().replace(" ", "_"),
            status_code=error.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception):
        logger.exception("Unhandled server exception: %s", error)
        return api_error(
            message="An unexpected internal server error occurred.",
            code="INTERNAL_SERVER_ERROR",
            status_code=500,
        )
