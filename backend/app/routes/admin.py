from flask import Blueprint, request
from app.schemas.auth import DoctorCreateSchema, DoctorUpdateSchema
from app.schemas.department import DepartmentCreateSchema, DepartmentUpdateSchema
from app.schemas.queue import WalkInQueueCreateSchema
from app.services.auth_service import auth_service
from app.services.department_service import department_service
from app.services.queue_service import queue_service
from app.repositories.audit_repository import audit_repository
from app.database.connection import serialize_docs
from app.middleware.auth import jwt_required, roles_required
from app.utils.response import api_response

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_dashboard_stats():
    """System-wide summary metrics for Hospital Administrator dashboard."""
    stats = queue_service.get_admin_dashboard_stats()
    return api_response(
        data=stats,
        message="Admin dashboard statistics retrieved successfully.",
        status_code=200,
    )


@admin_bp.route("/admin/users", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_users():
    """List registered users with optional role filtering and pagination."""
    role = request.args.get("role")
    limit = int(request.args.get("limit", 50))
    skip = int(request.args.get("skip", 0))

    result = auth_service.list_users(role=role, limit=limit, skip=skip)
    return api_response(
        data=result,
        message="Users retrieved successfully.",
        status_code=200,
    )


@admin_bp.route("/admin/doctors", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_doctors():
    """List all doctors along with user credentials and assigned department."""
    dept_id = request.args.get("department_id")
    doctors = auth_service.list_doctors(dept_id=dept_id)
    return api_response(
        data=doctors,
        message="Doctors retrieved successfully.",
        status_code=200,
    )


@admin_bp.route("/admin/doctors", methods=["POST"])
@jwt_required
@roles_required("admin")
def create_doctor():
    """Admin provisions a new doctor account and assigns them to a department."""
    json_data = request.get_json(silent=True) or {}
    validated = DoctorCreateSchema(**json_data)
    doctor = auth_service.create_doctor_account(
        data=validated.model_dump(),
        admin_user=request.current_user,
    )
    return api_response(
        data=doctor,
        message="Doctor account created and assigned successfully.",
        status_code=201,
    )


@admin_bp.route("/admin/doctors/<doctor_id>", methods=["PATCH"])
@jwt_required
@roles_required("admin")
def update_doctor(doctor_id: str):
    """Admin updates doctor department assignment, specialty, or availability status."""
    json_data = request.get_json(silent=True) or {}
    validated = DoctorUpdateSchema(**json_data)
    updated = auth_service.update_doctor(
        doctor_id=doctor_id,
        update_data=validated.model_dump(exclude_unset=True),
        admin_user=request.current_user,
    )
    return api_response(
        data=updated,
        message="Doctor updated successfully.",
        status_code=200,
    )


@admin_bp.route("/admin/departments", methods=["POST"])
@jwt_required
@roles_required("admin")
def create_department():
    """Admin creates a new hospital department."""
    json_data = request.get_json(silent=True) or {}
    validated = DepartmentCreateSchema(**json_data)
    created = department_service.create_department(
        data=validated.model_dump(),
        admin_user=request.current_user,
    )
    return api_response(
        data=created,
        message="Department created successfully.",
        status_code=201,
    )


@admin_bp.route("/admin/departments/<department_id>", methods=["PATCH"])
@jwt_required
@roles_required("admin")
def update_department(department_id: str):
    """Admin updates department details or activates/deactivates department."""
    json_data = request.get_json(silent=True) or {}
    validated = DepartmentUpdateSchema(**json_data)
    updated = department_service.update_department(
        dept_id=department_id,
        data=validated.model_dump(exclude_unset=True),
        admin_user=request.current_user,
    )
    return api_response(
        data=updated,
        message="Department updated successfully.",
        status_code=200,
    )


@admin_bp.route("/admin/queues", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_all_queues():
    """Admin view of all queue entries across departments with filters and pagination."""
    department_id = request.args.get("department_id")
    status = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    skip = int(request.args.get("skip", 0))

    result = queue_service.list_queues_admin(
        department_id=department_id,
        status=status,
        limit=limit,
        skip=skip,
    )
    return api_response(
        data=result,
        message="Admin queue entries retrieved successfully.",
        status_code=200,
    )


@admin_bp.route("/admin/audit-logs", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_audit_logs():
    """Admin view of audit logs with pagination and filters."""
    entity_type = request.args.get("entity_type")
    action = request.args.get("action")
    limit = int(request.args.get("limit", 50))
    skip = int(request.args.get("skip", 0))

    logs = audit_repository.list_logs(
        entity_type=entity_type,
        action=action,
        limit=limit,
        skip=skip,
    )
    total = audit_repository.count_logs(entity_type=entity_type, action=action)
    serialized = serialize_docs(logs)

    return api_response(
        data={
            "logs": serialized,
            "total": total,
            "limit": limit,
            "skip": skip,
        },
        message="Audit logs retrieved successfully.",
        status_code=200,
    )


@admin_bp.route("/admin/walk-in", methods=["POST"])
@jwt_required
@roles_required("admin", "staff")
def register_walk_in():
    """Register a walk-in patient at the reception/admin console without requiring patient login."""
    json_data = request.get_json(silent=True) or {}
    validated = WalkInQueueCreateSchema(**json_data)
    ticket = queue_service.register_walk_in(
        receptionist_user=request.current_user,
        department_id=validated.department_id,
        patient_name=validated.patient_name,
        phone=validated.phone,
        age=validated.age,
        reason=validated.reason,
    )
    return api_response(
        data=ticket,
        message=f"Walk-in patient registered. Daily token: {ticket.get('token_number')}",
        status_code=201,
    )
