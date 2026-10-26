from flask import Blueprint, request
from app.schemas.auth import UserRegisterSchema, UserLoginSchema
from app.services.auth_service import auth_service
from app.middleware.auth import jwt_required
from app.utils.response import api_response, api_error

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new user (defaults to patient role)."""
    json_data = request.get_json(silent=True) or {}
    validated = UserRegisterSchema(**json_data)
    result = auth_service.register(validated.model_dump())
    return api_response(
        data=result,
        message="User registered successfully.",
        status_code=201,
    )


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Authenticate existing user and return a JWT access token."""
    json_data = request.get_json(silent=True) or {}
    validated = UserLoginSchema(**json_data)
    result = auth_service.login(validated.model_dump())
    return api_response(
        data=result,
        message="Authentication successful.",
        status_code=200,
    )


@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required
def get_me():
    """Return the profile of the currently authenticated user."""
    current_user = request.current_user
    user_id = current_user.get("sub")
    profile = auth_service.get_user_profile(user_id)
    return api_response(
        data=profile,
        message="Profile retrieved successfully.",
        status_code=200,
    )
