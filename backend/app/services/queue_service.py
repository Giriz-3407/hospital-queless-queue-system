import logging
import math
from typing import Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.repositories.queue_repository import queue_repository
from app.repositories.department_repository import department_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.user_repository import user_repository
from app.repositories.audit_repository import audit_repository
from app.models.queue import QueueStatus
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
        dept = department_repository.find_by_identifier(department_id)
        if not dept or not dept.get("is_active", True):
            raise ValueError("The requested department does not exist or is currently inactive.")

        dept_oid = dept["_id"]
        patient_oid = to_object_id(patient_id)

        # Check for active existing ticket across ANY department in the hospital
        existing_active = queue_repository.find_active_by_patient(patient_oid)
        if existing_active:
            active_dept = existing_active.get("department_name") or "another department"
            token = existing_active.get("token_number", "active ticket")
            status = existing_active.get("status", "ACTIVE")
            raise ValueError(
                f"You already hold an active queue ticket ({token}) in {active_dept} (status: {status}). "
                "Hospital policy permits at most one active queue ticket per patient across all departments."
            )

        now = datetime.now(timezone.utc)
        queue_date = now.strftime("%Y-%m-%d")

        # Atomic daily sequential token generation per department
        token_number, seq = queue_repository.get_next_ticket_number(
            dept_id=dept_oid,
            dept_code=dept.get("code", "TKT"),
            queue_date=queue_date,
        )

        # Calculate initial position and wait time
        waiting_count = queue_repository.count_waiting(dept_oid)
        position = waiting_count + 1
        patients_ahead = waiting_count
        avg_time = dept.get("avg_consultation_time", 15)
        avail_doctors = doctor_repository.count_available(dept_oid)

        if avail_doctors > 0:
            est_wait = math.ceil((patients_ahead * avg_time) / avail_doctors)
        else:
            assigned = doctor_repository.find_by_department(dept_oid, available_only=False)
            if len(assigned) > 0:
                est_wait = None  # Doctors assigned but currently none available
            else:
                est_wait = patients_ahead * avg_time

        ticket_doc = {
            "department_id": dept_oid,
            "department_name": dept.get("name"),
            "department_code": dept.get("code"),
            "patient_id": patient_oid,
            "patient_name": patient_name,
            "token_number": token_number,
            "queue_date": queue_date,
            "position": position,
            "estimated_wait_minutes": est_wait,
            "status": QueueStatus.WAITING,
            "doctor_id": None,
            "doctor_name": None,
            "reason": reason.strip() if reason else None,
            "notes": None,
            "joined_at": now,
            "called_at": None,
            "consultation_started_at": None,
            "completed_at": None,
            "cancelled_at": None,
            "created_at": now,
            "updated_at": now,
        }

        try:
            created = queue_repository.create(ticket_doc)
        except DuplicateKeyError:
            # Concurrency safeguard: a simultaneous request created an active ticket for this patient
            existing_active = queue_repository.find_active_by_patient(patient_oid)
            active_dept = existing_active.get("department_name") if existing_active else "another department"
            token = existing_active.get("token_number") if existing_active else "active ticket"
            raise ValueError(
                f"You already hold an active queue ticket ({token}) in {active_dept}. "
                "Hospital policy permits at most one active queue ticket per patient across all departments."
            )

        audit_repository.create_log(
            action="QUEUE_JOINED",
            entity_type="queue",
            entity_id=str(created["_id"]),
            actor_user_id=patient_oid,
            actor_name=patient_name,
            actor_role="patient",
            metadata={
                "department_name": dept.get("name"),
                "token_number": token_number,
                "position": position,
            },
        )

        logger.info("Patient %s joined queue for %s with token %s", patient_id, dept.get("name"), token_number)
        return self._enrich_ticket(created, dept)

    def register_walk_in(
        self,
        receptionist_user: dict[str, Any],
        department_id: str,
        patient_name: str,
        phone: Optional[str] = None,
        age: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Allows hospital receptionists and administrators to register a walk-in patient.
        Reuses the sequential counter and wait calculation engine without fabricating account credentials.
        """
        role = receptionist_user.get("role")
        if role not in ("admin", "staff"):
            raise PermissionError("Access denied: Only hospital staff and administrators can register walk-in patients.")

        dept = department_repository.find_by_identifier(department_id)
        if not dept or not dept.get("is_active", True):
            raise ValueError("The requested department does not exist or is currently inactive.")

        dept_oid = dept["_id"]
        cleaned_phone = phone.strip() if phone and phone.strip() else None

        # Enforce duplicate prevention when phone number can reliably identify the patient
        if cleaned_phone:
            active_phone_ticket = queue_repository.find_active_by_phone(cleaned_phone)
            if active_phone_ticket:
                active_dept = active_phone_ticket.get("department_name") or "another department"
                token = active_phone_ticket.get("token_number", "active ticket")
                raise ValueError(
                    f"A patient with phone number '{cleaned_phone}' already holds an active queue ticket ({token}) in {active_dept}. "
                    "Hospital policy permits at most one active queue ticket per patient."
                )

        now = datetime.now(timezone.utc)
        queue_date = now.strftime("%Y-%m-%d")

        # Atomic daily sequential token generation per department
        token_number, seq = queue_repository.get_next_ticket_number(
            dept_id=dept_oid,
            dept_code=dept.get("code", "TKT"),
            queue_date=queue_date,
        )

        # Calculate initial position and wait time
        waiting_count = queue_repository.count_waiting(dept_oid)
        position = waiting_count + 1
        patients_ahead = waiting_count
        avg_time = dept.get("avg_consultation_time", 15)
        avail_doctors = doctor_repository.count_available(dept_oid)

        if avail_doctors > 0:
            est_wait = math.ceil((patients_ahead * avg_time) / avail_doctors)
        else:
            assigned = doctor_repository.find_by_department(dept_oid, available_only=False)
            if len(assigned) > 0:
                est_wait = None  # Doctors assigned but currently none available
            else:
                est_wait = patients_ahead * avg_time

        # Unique ObjectId for walk-in patient identifier
        walk_in_patient_id = ObjectId()
        receptionist_oid = to_object_id(receptionist_user.get("sub"))

        ticket_doc = {
            "department_id": dept_oid,
            "department_name": dept.get("name"),
            "department_code": dept.get("code"),
            "patient_id": walk_in_patient_id,
            "patient_name": patient_name.strip(),
            "token_number": token_number,
            "queue_date": queue_date,
            "position": position,
            "estimated_wait_minutes": est_wait,
            "status": QueueStatus.WAITING,
            "doctor_id": None,
            "doctor_name": None,
            "reason": reason.strip() if reason else None,
            "notes": None,
            "is_walk_in": True,
            "patient_phone": cleaned_phone,
            "patient_age": age,
            "registered_by": receptionist_oid,
            "registered_by_name": receptionist_user.get("name"),
            "joined_at": now,
            "called_at": None,
            "consultation_started_at": None,
            "completed_at": None,
            "cancelled_at": None,
            "created_at": now,
            "updated_at": now,
        }

        created = queue_repository.create(ticket_doc)

        audit_repository.create_log(
            action="WALK_IN_REGISTERED",
            entity_type="queue",
            entity_id=str(created["_id"]),
            actor_user_id=receptionist_oid,
            actor_name=receptionist_user.get("name"),
            actor_role=role,
            metadata={
                "department_name": dept.get("name"),
                "token_number": token_number,
                "patient_name": patient_name.strip(),
                "patient_phone": cleaned_phone,
                "is_walk_in": True,
            },
        )

        logger.info(
            "Receptionist %s registered walk-in %s with token %s in %s",
            receptionist_user.get("name"),
            patient_name,
            token_number,
            dept.get("name"),
        )
        return self._enrich_ticket(created, dept)

    def get_patient_queues(self, patient_id: str) -> list[dict[str, Any]]:
        """Retrieve all queue tickets belonging to the authenticated patient with live positions."""
        tickets = queue_repository.find_by_patient_id(patient_id)
        enriched = []
        for t in tickets:
            dept = department_repository.find_by_id(t["department_id"])
            enriched.append(self._enrich_ticket(t, dept))
        return enriched

    def get_queue_by_id(self, queue_id: str, current_user: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve queue ticket details with strict authorization:
        Patients can ONLY view their own tickets; staff, doctors, and admins can view any.
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
        Patients can only cancel their own tickets; staff/admins can cancel any.
        """
        ticket = queue_repository.find_by_id(queue_id)
        if not ticket:
            raise ValueError(f"Queue ticket with ID '{queue_id}' was not found.")

        user_role = current_user.get("role")
        user_id = str(current_user.get("sub"))

        if user_role == "patient" and str(ticket["patient_id"]) != user_id:
            logger.warning("Unauthorized cancel attempt: user %s attempted to cancel ticket %s", user_id, queue_id)
            raise PermissionError("Access denied: You cannot cancel another patient's queue ticket.")

        status = QueueStatus.normalize(ticket.get("status", ""))
        if status != QueueStatus.WAITING:
            raise ValueError(f"Only tickets with 'WAITING' status can be cancelled. Current status: '{ticket.get('status')}'.")

        updated = queue_repository.atomic_cancel(
            queue_id=queue_id,
            patient_id=user_id if user_role == "patient" else None,
            notes=f"Cancelled by {user_role}: {current_user.get('name', 'User')}",
        )
        if not updated:
            raise ValueError("Ticket could not be cancelled. It may have already been called or modified.")

        audit_repository.create_log(
            action="QUEUE_CANCELLED",
            entity_type="queue",
            entity_id=queue_id,
            actor_user_id=user_id,
            actor_name=current_user.get("name"),
            actor_role=user_role,
            metadata={"token_number": ticket.get("token_number")},
        )

        logger.info("Ticket %s cancelled by user %s", ticket.get("token_number"), user_id)
        dept = department_repository.find_by_id(ticket["department_id"])
        return self._enrich_ticket(updated, dept)

    # -------------------------------------------------------------
    # DOCTOR WORKFLOW OPERATIONS
    # -------------------------------------------------------------

    def doctor_get_queue(self, doctor_user: dict[str, Any]) -> dict[str, Any]:
        """Fetch active queue, current called/serving patient, and department stats for doctor."""
        doc_profile = doctor_repository.find_by_user_id(doctor_user.get("sub"))
        if not doc_profile:
            raise PermissionError("No doctor profile is linked to your user account.")

        dept_id = doc_profile["department_id"]
        dept = department_repository.find_by_id(dept_id)
        if not dept:
            raise ValueError("Assigned department not found.")

        # Active called or in-consultation
        currently_called = queue_repository.get_currently_called(dept_id)
        currently_serving = queue_repository.get_currently_serving(dept_id)

        # Waiting tickets
        waiting_tickets = queue_repository.find_by_department(dept_id, status=QueueStatus.WAITING)
        enriched_waiting = [self._enrich_ticket(t, dept) for t in waiting_tickets]

        stats = queue_repository.get_department_stats(dept_id)

        return {
            "doctor": serialize_doc(doc_profile),
            "department": serialize_doc(dept),
            "currently_called": self._enrich_ticket(currently_called, dept) if currently_called else None,
            "currently_serving": self._enrich_ticket(currently_serving, dept) if currently_serving else None,
            "waiting_queue": enriched_waiting,
            "stats": stats,
        }

    def doctor_call_next(self, doctor_user: dict[str, Any]) -> dict[str, Any]:
        """Call next eligible waiting patient in doctor's assigned department."""
        doc_profile = doctor_repository.find_by_user_id(doctor_user.get("sub"))
        if not doc_profile:
            raise PermissionError("No doctor profile linked to your user account.")

        dept_id = doc_profile["department_id"]
        dept = department_repository.find_by_id(dept_id)

        # Find next eligible waiting ticket
        next_ticket = queue_repository.get_next_waiting_ticket(dept_id)
        if not next_ticket:
            raise ValueError("No patients currently waiting in your department queue.")

        called_ticket = queue_repository.atomic_call_next(
            queue_id=next_ticket["_id"],
            dept_id=dept_id,
            doctor_id=doc_profile["_id"],
            doctor_name=doc_profile.get("display_name"),
        )
        if not called_ticket:
            raise ValueError("The next patient was already called by another provider. Please try again.")

        audit_repository.create_log(
            action="QUEUE_CALLED",
            entity_type="queue",
            entity_id=str(called_ticket["_id"]),
            actor_user_id=doctor_user.get("sub"),
            actor_name=doctor_user.get("name"),
            actor_role="doctor",
            metadata={
                "token_number": called_ticket.get("token_number"),
                "patient_name": called_ticket.get("patient_name"),
            },
        )

        logger.info("Doctor %s called token %s", doctor_user.get("name"), called_ticket.get("token_number"))
        return self._enrich_ticket(called_ticket, dept)

    def doctor_start_consultation(self, queue_id: str, doctor_user: dict[str, Any]) -> dict[str, Any]:
        """Mark called patient as in consultation."""
        doc_profile = doctor_repository.find_by_user_id(doctor_user.get("sub"))
        if not doc_profile:
            raise PermissionError("No doctor profile linked to your user account.")

        dept_id = doc_profile["department_id"]
        dept = department_repository.find_by_id(dept_id)

        ticket = queue_repository.find_by_id(queue_id)
        if not ticket:
            raise ValueError(f"Queue ticket with ID '{queue_id}' not found.")

        # Ensure doctor cannot modify queue in unrelated department
        if str(ticket.get("department_id")) != str(dept_id):
            raise PermissionError("Access denied: You cannot operate on queues outside your assigned department.")

        updated = queue_repository.atomic_start_consultation(
            queue_id=queue_id,
            dept_id=dept_id,
            doctor_id=doc_profile["_id"],
            doctor_name=doc_profile.get("display_name"),
        )
        if not updated:
            raise ValueError("Cannot start consultation. Ticket must be in 'CALLED' or 'WAITING' status.")

        audit_repository.create_log(
            action="CONSULTATION_STARTED",
            entity_type="queue",
            entity_id=queue_id,
            actor_user_id=doctor_user.get("sub"),
            actor_name=doctor_user.get("name"),
            actor_role="doctor",
            metadata={"token_number": updated.get("token_number")},
        )

        return self._enrich_ticket(updated, dept)

    def doctor_complete_consultation(
        self, queue_id: str, doctor_user: dict[str, Any], notes: Optional[str] = None
    ) -> dict[str, Any]:
        """Mark consultation as completed."""
        doc_profile = doctor_repository.find_by_user_id(doctor_user.get("sub"))
        if not doc_profile:
            raise PermissionError("No doctor profile linked to your user account.")

        dept_id = doc_profile["department_id"]
        dept = department_repository.find_by_id(dept_id)

        ticket = queue_repository.find_by_id(queue_id)
        if not ticket:
            raise ValueError(f"Queue ticket with ID '{queue_id}' not found.")

        if str(ticket.get("department_id")) != str(dept_id):
            raise PermissionError("Access denied: You cannot operate on queues outside your assigned department.")

        updated = queue_repository.atomic_complete_consultation(
            queue_id=queue_id,
            dept_id=dept_id,
            doctor_id=doc_profile["_id"],
            notes=notes,
        )
        if not updated:
            raise ValueError("Cannot complete consultation. Ticket must be in 'IN_CONSULTATION' or 'CALLED' status.")

        audit_repository.create_log(
            action="CONSULTATION_COMPLETED",
            entity_type="queue",
            entity_id=queue_id,
            actor_user_id=doctor_user.get("sub"),
            actor_name=doctor_user.get("name"),
            actor_role="doctor",
            metadata={"token_number": updated.get("token_number")},
        )

        return self._enrich_ticket(updated, dept)

    def doctor_mark_no_show(
        self, queue_id: str, doctor_user: dict[str, Any], notes: Optional[str] = None
    ) -> dict[str, Any]:
        """Mark patient as NO_SHOW."""
        doc_profile = doctor_repository.find_by_user_id(doctor_user.get("sub"))
        if not doc_profile:
            raise PermissionError("No doctor profile linked to your user account.")

        dept_id = doc_profile["department_id"]
        dept = department_repository.find_by_id(dept_id)

        ticket = queue_repository.find_by_id(queue_id)
        if not ticket:
            raise ValueError(f"Queue ticket with ID '{queue_id}' not found.")

        if str(ticket.get("department_id")) != str(dept_id):
            raise PermissionError("Access denied: You cannot operate on queues outside your assigned department.")

        updated = queue_repository.atomic_mark_no_show(
            queue_id=queue_id,
            dept_id=dept_id,
            doctor_id=doc_profile["_id"],
            notes=notes,
        )
        if not updated:
            raise ValueError("Cannot mark NO_SHOW. Ticket must be in 'CALLED' or 'WAITING' status.")

        audit_repository.create_log(
            action="QUEUE_NO_SHOW",
            entity_type="queue",
            entity_id=queue_id,
            actor_user_id=doctor_user.get("sub"),
            actor_name=doctor_user.get("name"),
            actor_role="doctor",
            metadata={"token_number": updated.get("token_number")},
        )

        return self._enrich_ticket(updated, dept)

    # -------------------------------------------------------------
    # ADMIN OPERATIONS
    # -------------------------------------------------------------

    def list_queues_admin(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> dict[str, Any]:
        """Admin list all queues with pagination and filtering."""
        tickets = queue_repository.find_all(
            dept_id=department_id,
            status=status,
            limit=limit,
            skip=skip,
        )
        total = queue_repository.count_all(dept_id=department_id, status=status)

        enriched = []
        for t in tickets:
            dept = department_repository.find_by_id(t["department_id"])
            enriched.append(self._enrich_ticket(t, dept))

        return {
            "queues": enriched,
            "total": total,
            "limit": limit,
            "skip": skip,
        }

    def get_admin_dashboard_stats(self) -> dict[str, Any]:
        """System-wide summary metrics for Admin Dashboard."""
        total_users = user_repository.count_users()
        total_patients = user_repository.count_users(role="patient")
        total_doctors = doctor_repository.count_doctors()
        total_departments = department_repository.count_departments(active_only=False)
        active_departments = department_repository.count_departments(active_only=True)
        active_tickets = queue_repository.count_active_total()

        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        tickets_today = queue_repository.collection.count_documents({"queue_date": today_str})
        completed_today = queue_repository.collection.count_documents({
            "queue_date": today_str,
            "status": {"$in": [QueueStatus.COMPLETED, "completed"]},
        })

        return {
            "total_users": total_users,
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_departments": total_departments,
            "active_departments": active_departments,
            "active_tickets": active_tickets,
            "tickets_today": tickets_today,
            "completed_today": completed_today,
        }

    # -------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------

    def _enrich_ticket(
        self, ticket: Optional[dict[str, Any]], dept: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Enrich ticket with real-time dynamic queue calculations:
        - live_position (1 = next waiting)
        - live_patients_ahead (live_position - 1)
        - live_estimated_wait_minutes
        - currently_serving_ticket
        - currently_called_ticket
        """
        if not ticket:
            return {}

        serialized = serialize_doc(ticket) or {}
        dept_oid = ticket.get("department_id")
        status = QueueStatus.normalize(ticket.get("status", ""))
        queue_date = ticket.get("queue_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        joined_at = ticket.get("joined_at") or ticket.get("created_at")

        if status == QueueStatus.WAITING and dept_oid:
            # Deterministic count of patients ahead on same queue date
            waiting_before = queue_repository.count_waiting_before(dept_oid, queue_date, joined_at)
            live_position = waiting_before + 1
            patients_ahead = waiting_before

            avg_time = dept.get("avg_consultation_time", 15) if dept else 15
            avail_doctors = doctor_repository.count_available(dept_oid)

            if avail_doctors > 0:
                live_wait = math.ceil((patients_ahead * avg_time) / avail_doctors)
            else:
                assigned = doctor_repository.find_by_department(dept_oid, available_only=False)
                if len(assigned) > 0:
                    live_wait = None  # Doctors assigned but currently none available
                else:
                    live_wait = patients_ahead * avg_time

            serialized["live_position"] = live_position
            serialized["patients_ahead"] = patients_ahead
            serialized["live_estimated_wait_minutes"] = live_wait
        elif status in (QueueStatus.CALLED, QueueStatus.IN_CONSULTATION):
            serialized["live_position"] = 0
            serialized["patients_ahead"] = 0
            serialized["live_estimated_wait_minutes"] = 0
        else:
            serialized["live_position"] = 0
            serialized["patients_ahead"] = 0
            serialized["live_estimated_wait_minutes"] = 0

        # Include currently called and serving tokens
        if dept_oid:
            serving = queue_repository.get_currently_serving(dept_oid)
            called = queue_repository.get_currently_called(dept_oid)
            serialized["currently_serving_ticket"] = serving.get("token_number") if serving else None
            serialized["currently_called_ticket"] = called.get("token_number") if called else None

        # For backwards compatibility with any existing client looking for ticket_number or status
        serialized["ticket_number"] = serialized.get("token_number")
        serialized["position"] = serialized.get("live_position", serialized.get("position", 1))

        return serialized


queue_service = QueueService()
