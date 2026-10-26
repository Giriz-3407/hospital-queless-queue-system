from flask import Blueprint, request
from app.schemas.department import DepartmentCreateSchema
from app.services.department_service import department_service
from app.middleware.auth import jwt_required, roles_required
from app.utils.response import api_response

departments_bp = Blueprint("departments", __name__)


@departments_bp.route("/departments", methods=["GET"])
def get_departments():
    """List all active hospital departments along with queue status and wait estimates."""
    departments = department_service.list_departments()
    return api_response(
        data=departments,
        message="Departments retrieved successfully.",
        status_code=200,
    )


@departments_bp.route("/departments", methods=["POST"])
@jwt_required
@roles_required("admin", "staff", "doctor")
def create_department():
    """Create a new department (Admin, Staff, and Doctors)."""
    json_data = request.get_json(silent=True) or {}
    validated = DepartmentCreateSchema(**json_data)
    created = department_service.create_department(validated.model_dump())
    return api_response(
        data=created,
        message="Department created successfully.",
        status_code=201,
    )
