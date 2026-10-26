from flask import Blueprint, request
from app.services.auth_service import auth_service
from app.services.queue_service import queue_service
from app.models.queue import QueueStatus
from app.middleware.auth import jwt_required
from app.utils.response import api_response

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/patients/me", methods=["GET"])
@jwt_required
def get_patient_profile():
    """
    Get authenticated patient profile along with summary of active and recent queue visits.
    """
    current_user = request.current_user
    patient_id = current_user.get("sub")

    profile = auth_service.get_user_profile(patient_id)
    queues = queue_service.get_patient_queues(patient_id)

    active_queues = [
        q for q in queues
        if QueueStatus.normalize(q.get("status", "")) in QueueStatus.ACTIVE_STATUSES
    ]
    past_queues = [
        q for q in queues
        if QueueStatus.normalize(q.get("status", "")) in QueueStatus.TERMINAL_STATUSES
    ]

    response_data = {
        "profile": profile,
        "summary": {
            "active_tickets_count": len(active_queues),
            "past_visits_count": len(past_queues),
        },
        "active_queues": active_queues,
        "recent_queues": past_queues[:10],
    }

    return api_response(
        data=response_data,
        message="Patient information retrieved successfully.",
        status_code=200,
    )


@patients_bp.route("/patients/me/queues", methods=["GET"])
@jwt_required
def get_patient_queue_history():
    """Get all past and present queue entries for the authenticated patient."""
    current_user = request.current_user
    patient_id = current_user.get("sub")
    queues = queue_service.get_patient_queues(patient_id)
    return api_response(
        data=queues,
        message="Patient queue history retrieved successfully.",
        status_code=200,
    )
