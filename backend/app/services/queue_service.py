import logging
from typing import Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.repositories.queue_repository import queue_repository
from app.repositories.department_repository import department_repository
from app.database.connection import serialize_doc, serialize_docs, to_object_id

logger = logging.getLogger(__name__)


class QueueService:
    """Business logic for patient queues, live queue calculation, and staff operations."""

    def join_queue(
        self,
        patient_id: str,
        patient_name: str,
        department_id: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """Allows a patient to join a virtual queue for a specific hospital department."""
        dept = department_repository.find_by_id(department_id)
        if not dept or not dept.get("is_active", True):
            raise ValueError("The requested department does not exist or is currently inactive.")

        dept_oid = dept["_id"]
        patient_oid = to_object_id(patient_id)

        # Check for active existing ticket in this department
        existing_active = queue_repository.find_active_by_patient_and_dept(patient_oid, dept_oid)
        if existing_active:
            raise ValueError(
                f"You already hold an active queue ticket ({existing_active.get('ticket_number')}) "
                f"in {dept.get('name')}."
            )

        # Calculate current waiting position
        waiting_count = queue_repository.count_waiting(dept_oid)
        position = waiting_count + 1
        avg_time = dept.get("avg_consultation_time", 15)
        estimated_wait = position * avg_time

        # Generate unique ticket number for the department
        ticket_number = queue_repository.get_next_ticket_number(dept.get("code", "TKT"))

        ticket_doc = {
            "department_id": dept_oid,
            "department_name": dept.get("name"),
            "department_code": dept.get("code"),
            "patient_id": patient_oid,
            "patient_name": patient_name,
            "ticket_number": ticket_number,
            "position": position,
            "estimated_wait_minutes": estimated_wait,
            "status": "waiting",
            "reason": reason.strip() if reason else None,
            "called_at": None,
            "completed_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        created = queue_repository.create(ticket_doc)
        logger.info("Patient %s joined queue for %s with ticket %s", patient_id, dept.get("name"), ticket_number)
        return self._enrich_ticket(created, dept)

    def get_patient_queues(self, patient_id: str) -> list[dict[str, Any]]:
        """Retrieve all queue tickets belonging to the authenticated patient."""
        tickets = queue_repository.find_by_patient_id(patient_id)
        enriched = []
        for t in tickets:
            dept = department_repository.find_by_id(t["department_id"])
            enriched.append(self._enrich_ticket(t, dept))
        return enriched

    def get_queue_by_id(self, queue_id: str, current_user: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve queue ticket details with strict authorization check:
        Patients can ONLY view their own tickets; staff and doctors can view any ticket.
        """
        ticket = queue_repository.find_by_id(queue_id)
        if not ticket:
            raise ValueError(f"Queue ticket with ID '{queue_id}' was not found.")

        user_role = current_user.get("role")
        user_id = str(current_user.get("sub"))

        if user_role == "patient" and str(ticket["patient_id"]) != user_id:
            logger.warning("Unauthorized access attempt: user %s attempted to view ticket %s", user_id, queue_id)
            raise PermissionError("Access denied: You do not have permission to view another patient's queue ticket.")

        dept = department_repository.find_by_id(ticket["department_id"])
        return self._enrich_ticket(ticket, dept)

    def cancel_queue(self, queue_id: str, current_user: dict[str, Any]) -> dict[str, Any]:
        """
        Cancel a waiting ticket.
        Patients can only cancel their own tickets; staff can cancel on behalf of patients.
        """
        ticket = queue_repository.find_by_id(queue_id)
        if not ticket:
            raise ValueError(f"Queue ticket with ID '{queue_id}' was not found.")

        user_role = current_user.get("role")
        user_id = str(current_user.get("sub"))

        if user_role == "patient" and str(ticket["patient_id"]) != user_id:
            logger.warning("Unauthorized cancel attempt: user %s attempted to cancel ticket %s", user_id, queue_id)
            raise PermissionError("Access denied: You cannot cancel another patient's queue ticket.")

        if ticket.get("status") != "waiting":
            raise ValueError(f"Only tickets with 'waiting' status can be cancelled. Current status: '{ticket.get('status')}'.")

        updated = queue_repository.update_status(
            queue_id=queue_id,
            status="cancelled",
            notes="Cancelled by user" if user_role == "patient" else f"Cancelled by {user_role}",
        )
        logger.info("Ticket %s cancelled by user %s", ticket.get("ticket_number"), user_id)
        dept = department_repository.find_by_id(ticket["department_id"])
        return self._enrich_ticket(updated, dept)

    def list_queues_for_staff(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List queues for staff/doctor dashboard with filtering."""
        tickets = queue_repository.find_by_department(department_id, status)
        enriched = []
        for t in tickets:
            dept = department_repository.find_by_id(t["department_id"])
            enriched.append(self._enrich_ticket(t, dept))
        return enriched

    def update_queue_status_for_staff(
        self,
        queue_id: str,
        new_status: str,
        notes: Optional[str],
        staff_user: dict[str, Any],
    ) -> dict[str, Any]:
        """Update ticket status for doctor / staff workflow."""
        ticket = queue_repository.find_by_id(queue_id)
        if not ticket:
            raise ValueError(f"Queue ticket with ID '{queue_id}' was not found.")

        updated = queue_repository.update_status(
            queue_id=queue_id,
            status=new_status,
            notes=notes,
            staff_id=staff_user.get("sub"),
        )
        logger.info(
            "Ticket %s status updated to '%s' by staff %s",
            ticket.get("ticket_number"),
            new_status,
            staff_user.get("email"),
        )
        dept = department_repository.find_by_id(ticket["department_id"])
        return self._enrich_ticket(updated, dept)

    def _enrich_ticket(
        self, ticket: Optional[dict[str, Any]], dept: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """Helper to compute real-time queue position and currently serving ticket."""
        if not ticket:
            return {}

        serialized = serialize_doc(ticket) or {}
        dept_oid = ticket.get("department_id")
        status = ticket.get("status")

        if status == "waiting" and dept_oid:
            # Live recalculation of position and wait time
            waiting_before = queue_repository.count_waiting_before(dept_oid, ticket["created_at"])
            live_position = waiting_before + 1
            avg_time = dept.get("avg_consultation_time", 15) if dept else 15
            live_wait_minutes = live_position * avg_time

            serialized["live_position"] = live_position
            serialized["live_estimated_wait_minutes"] = live_wait_minutes
        else:
            serialized["live_position"] = 0
            serialized["live_estimated_wait_minutes"] = 0

        # Attach currently serving ticket
        if dept_oid:
            serving_ticket = queue_repository.get_currently_serving(dept_oid)
            serialized["currently_serving_ticket"] = (
                serving_ticket.get("ticket_number") if serving_ticket else "None"
            )

        return serialized


queue_service = QueueService()
