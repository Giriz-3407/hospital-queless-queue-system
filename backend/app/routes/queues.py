from flask import Blueprint, request
from app.schemas.queue import JoinQueueSchema, QueueStatusUpdateSchema
from app.services.queue_service import queue_service
from app.middleware.auth import jwt_required, roles_required
from app.utils.response import api_response

queues_bp = Blueprint("queues", __name__)


@queues_bp.route("/queues", methods=["GET"])
@jwt_required
@roles_required("doctor", "staff", "admin")
def list_queues():
    """
    List queue tickets for doctors and hospital staff.
    Supports query parameters: department_id and status.
    """
    department_id = request.args.get("department_id")
    status = request.args.get("status")
    tickets = queue_service.list_queues_for_staff(department_id=department_id, status=status)
    return api_response(
        data=tickets,
        message="Queues retrieved successfully.",
        status_code=200,
    )


@queues_bp.route("/queues/join", methods=["POST"])
@jwt_required
def join_queue():
    """
    Allow an authenticated patient to join a virtual queue.
    Automatically assigns next ticket number and calculates queue position and wait time.
    """
    json_data = request.get_json(silent=True) or {}
    validated = JoinQueueSchema(**json_data)

    current_user = request.current_user
    patient_id = current_user.get("sub")
    patient_name = current_user.get("name", "Patient")

    ticket = queue_service.join_queue(
        patient_id=patient_id,
        patient_name=patient_name,
        department_id=validated.department_id,
        reason=validated.reason,
    )
    return api_response(
        data=ticket,
        message="Joined virtual queue successfully.",
        status_code=201,
    )


@queues_bp.route("/queues/my", methods=["GET"])
@jwt_required
def get_my_queues():
    """Retrieve all tickets belonging to the authenticated patient with real-time positions."""
    current_user = request.current_user
    patient_id = current_user.get("sub")
    tickets = queue_service.get_patient_queues(patient_id=patient_id)
    return api_response(
        data=tickets,
        message="Your queue tickets retrieved successfully.",
        status_code=200,
    )


@queues_bp.route("/queues/<queue_id>", methods=["GET"])
@jwt_required
def get_queue_by_id(queue_id: str):
    """
    Retrieve specific queue details.
    Enforces authorization: Patients can only view their own ticket; staff can view any.
    """
    current_user = request.current_user
    ticket = queue_service.get_queue_by_id(queue_id=queue_id, current_user=current_user)
    return api_response(
        data=ticket,
        message="Queue ticket details retrieved.",
        status_code=200,
    )


@queues_bp.route("/queues/<queue_id>/cancel", methods=["POST"])
@jwt_required
def cancel_queue(queue_id: str):
    """
    Cancel a pending virtual queue ticket.
    Enforces authorization: Patients can only cancel their own ticket.
    """
    current_user = request.current_user
    cancelled = queue_service.cancel_queue(queue_id=queue_id, current_user=current_user)
    return api_response(
        data=cancelled,
        message="Queue ticket cancelled successfully.",
        status_code=200,
    )


@queues_bp.route("/queues/<queue_id>/status", methods=["PATCH"])
@jwt_required
@roles_required("doctor", "staff", "admin")
def update_queue_status(queue_id: str):
    """
    Update ticket status (in_consultation, completed, cancelled, no_show).
    Restricted to doctor, staff, and admin roles.
    """
    json_data = request.get_json(silent=True) or {}
    validated = QueueStatusUpdateSchema(**json_data)
    current_user = request.current_user

    updated = queue_service.update_queue_status_for_staff(
        queue_id=queue_id,
        new_status=validated.status,
        notes=validated.notes,
        staff_user=current_user,
    )
    return api_response(
        data=updated,
        message=f"Queue status updated to '{validated.status}'.",
        status_code=200,
    )
