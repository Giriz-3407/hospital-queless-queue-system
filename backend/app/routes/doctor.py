from flask import Blueprint, request
from app.services.queue_service import queue_service
from app.middleware.auth import jwt_required, roles_required
from app.utils.response import api_response

doctor_bp = Blueprint("doctor", __name__)


@doctor_bp.route("/doctor/queue", methods=["GET"])
@jwt_required
@roles_required("doctor")
def get_doctor_queue():
    """
    Fetch active queue for the authenticated doctor's assigned department.
    Returns currently called patient, in consultation patient, waiting queue, and stats.
    """
    result = queue_service.doctor_get_queue(doctor_user=request.current_user)
    return api_response(
        data=result,
        message="Doctor queue retrieved successfully.",
        status_code=200,
    )


@doctor_bp.route("/doctor/queue/next", methods=["POST"])
@jwt_required
@roles_required("doctor")
def call_next_patient():
    """
    Call the next eligible waiting patient in doctor's assigned department.
    Transitions ticket from WAITING -> CALLED.
    """
    called_ticket = queue_service.doctor_call_next(doctor_user=request.current_user)
    return api_response(
        data=called_ticket,
        message=f"Patient with ticket {called_ticket.get('token_number')} called.",
        status_code=200,
    )


@doctor_bp.route("/doctor/queue/<queue_id>/start", methods=["POST"])
@jwt_required
@roles_required("doctor")
def start_consultation(queue_id: str):
    """
    Mark patient as in consultation.
    Transitions ticket from CALLED (or WAITING) -> IN_CONSULTATION.
    """
    started_ticket = queue_service.doctor_start_consultation(
        queue_id=queue_id,
        doctor_user=request.current_user,
    )
    return api_response(
        data=started_ticket,
        message=f"Consultation started for ticket {started_ticket.get('token_number')}.",
        status_code=200,
    )


@doctor_bp.route("/doctor/queue/<queue_id>/complete", methods=["POST"])
@jwt_required
@roles_required("doctor")
def complete_consultation(queue_id: str):
    """
    Mark patient consultation as completed.
    Transitions ticket from IN_CONSULTATION -> COMPLETED.
    """
    json_data = request.get_json(silent=True) or {}
    notes = json_data.get("notes")

    completed_ticket = queue_service.doctor_complete_consultation(
        queue_id=queue_id,
        doctor_user=request.current_user,
        notes=notes,
    )
    return api_response(
        data=completed_ticket,
        message=f"Consultation completed for ticket {completed_ticket.get('token_number')}.",
        status_code=200,
    )


@doctor_bp.route("/doctor/queue/<queue_id>/no-show", methods=["POST"])
@jwt_required
@roles_required("doctor")
def mark_no_show(queue_id: str):
    """
    Mark called patient as NO_SHOW.
    Transitions ticket from CALLED or WAITING -> NO_SHOW.
    """
    json_data = request.get_json(silent=True) or {}
    notes = json_data.get("notes")

    no_show_ticket = queue_service.doctor_mark_no_show(
        queue_id=queue_id,
        doctor_user=request.current_user,
        notes=notes,
    )
    return api_response(
        data=no_show_ticket,
        message=f"Ticket {no_show_ticket.get('token_number')} marked as No-Show.",
        status_code=200,
    )
