from flask import Blueprint, request
from app.schemas.department import DepartmentCreateSchema, DepartmentUpdateSchema
from app.services.department_service import department_service
from app.repositories.queue_repository import queue_repository
from app.services.queue_service import queue_service
from app.middleware.auth import jwt_required, roles_required
from app.utils.response import api_response

departments_bp = Blueprint("departments", __name__)


@departments_bp.route("/departments", methods=["GET"])
def get_departments():
    """List all active hospital departments along with queue status and wait estimates."""
    active_only = request.args.get("all", "").lower() not in ("true", "1")
    departments = department_service.list_departments(active_only=active_only)
    return api_response(
        data=departments,
        message="Departments retrieved successfully.",
        status_code=200,
    )


@departments_bp.route("/departments/<department_id>", methods=["GET"])
def get_department(department_id: str):
    """Retrieve details for a single department including assigned doctors."""
    dept = department_service.get_department_by_id(department_id)
    return api_response(
        data=dept,
        message="Department retrieved successfully.",
        status_code=200,
    )


@departments_bp.route("/departments", methods=["POST"])
@jwt_required
@roles_required("admin", "doctor")
def create_department():
    """Create a new department (Admin and Doctors)."""
    json_data = request.get_json(silent=True) or {}
    validated = DepartmentCreateSchema(**json_data)
    created = department_service.create_department(validated.model_dump(), admin_user=request.current_user)
    return api_response(
        data=created,
        message="Department created successfully.",
        status_code=201,
    )


@departments_bp.route("/departments/<department_id>", methods=["PATCH"])
@jwt_required
@roles_required("admin")
def update_department(department_id: str):
    """Update department information or toggle active status (Admin only)."""
    json_data = request.get_json(silent=True) or {}
    validated = DepartmentUpdateSchema(**json_data)
    updated = department_service.update_department(
        department_id=department_id,
        data=validated.model_dump(exclude_unset=True),
        admin_user=request.current_user,
    )
    return api_response(
        data=updated,
        message="Department updated successfully.",
        status_code=200,
    )


@departments_bp.route("/departments/<department_id>/queue", methods=["GET"])
def get_department_queue(department_id: str):
    """View active queue for a specific department."""
    status = request.args.get("status")
    tickets = queue_repository.find_by_department(dept_id=department_id, status=status)
    dept = department_service.get_department_by_id(department_id)
    enriched = [queue_service._enrich_ticket(t, dept) for t in tickets]
    return api_response(
        data=enriched,
        message="Department queue retrieved successfully.",
        status_code=200,
    )
