import logging
import math
from typing import Any, Optional
from app.repositories.department_repository import department_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.queue_repository import queue_repository
from app.repositories.audit_repository import audit_repository
from app.database.connection import serialize_doc, serialize_docs, to_object_id

logger = logging.getLogger(__name__)


class DepartmentService:
    """Business logic service for hospital departments."""

    def list_departments(self, active_only: bool = True) -> list[dict[str, Any]]:
        """List departments enriched with real-time waiting metrics and doctor availability."""
        # Auto seed if empty
        department_repository.seed_defaults_if_empty()

        departments = department_repository.find_all(active_only=active_only)
        result = []

        for dept in departments:
            d_oid = dept["_id"]
            waiting_count = queue_repository.count_waiting(d_oid)
            stats = queue_repository.get_department_stats(d_oid)
            available_doctors = doctor_repository.count_available(d_oid)
            assigned_doctors = doctor_repository.find_by_department(d_oid, available_only=False)

            # Wait time estimation:
            # ceil(waiting_count * avg_consultation_time / effective_available_doctors)
            # If no available doctor, return None to represent unavailable wait estimate
            avg_time = dept.get("avg_consultation_time", 15)
            if available_doctors > 0:
                est_wait = math.ceil((waiting_count * avg_time) / available_doctors)
            elif len(assigned_doctors) > 0 and available_doctors == 0:
                # Doctors assigned but currently none available
                est_wait = None
            else:
                # Default baseline if no doctor profiles are configured yet
                est_wait = waiting_count * avg_time

            dept_data = serialize_doc(dept) or {}
            dept_data["current_waiting"] = waiting_count
            dept_data["estimated_wait_minutes"] = est_wait
            dept_data["available_doctors_count"] = available_doctors
            dept_data["total_doctors_count"] = len(assigned_doctors)
            dept_data["stats"] = stats
            dept_data["doctors"] = [
                {
                    "id": str(doc["_id"]),
                    "display_name": doc.get("display_name"),
                    "specialty": doc.get("specialty"),
                    "is_available": doc.get("is_available", True),
                }
                for doc in assigned_doctors
            ]
            result.append(dept_data)

        return result

    def get_department_by_id(self, dept_id: str) -> dict[str, Any]:
        """Get single department details with assigned doctors and active queue summary."""
        dept = department_repository.find_by_id(dept_id)
        if not dept:
            raise ValueError(f"Department with ID '{dept_id}' not found.")

        d_oid = dept["_id"]
        waiting_count = queue_repository.count_waiting(d_oid)
        stats = queue_repository.get_department_stats(d_oid)
        available_doctors = doctor_repository.count_available(d_oid)
        assigned_doctors = doctor_repository.find_by_department(d_oid, available_only=False)

        avg_time = dept.get("avg_consultation_time", 15)
        est_wait = math.ceil((waiting_count * avg_time) / max(available_doctors, 1)) if available_doctors > 0 else None

        dept_data = serialize_doc(dept) or {}
        dept_data["current_waiting"] = waiting_count
        dept_data["estimated_wait_minutes"] = est_wait
        dept_data["available_doctors_count"] = available_doctors
        dept_data["stats"] = stats
        dept_data["doctors"] = [
            {
                "id": str(doc["_id"]),
                "display_name": doc.get("display_name"),
                "specialty": doc.get("specialty"),
                "is_available": doc.get("is_available", True),
            }
            for doc in assigned_doctors
        ]
        return dept_data

    def create_department(self, data: dict[str, Any], admin_user: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Create a new hospital department."""
        code = data["code"].upper().strip()
        existing_code = department_repository.find_by_code(code)
        if existing_code:
            raise ValueError(f"A department with code '{code}' already exists.")

        name = data["name"].strip()
        existing_name = department_repository.find_by_name(name)
        if existing_name:
            raise ValueError(f"A department with name '{name}' already exists.")

        dept_doc = {
            "name": name,
            "code": code,
            "description": data.get("description"),
            "avg_consultation_time": data.get("avg_consultation_time", 15),
            "is_active": data.get("is_active", True),
        }
        created = department_repository.create(dept_doc)

        if admin_user:
            audit_repository.create_log(
                action="DEPARTMENT_CREATED",
                entity_type="department",
                entity_id=str(created["_id"]),
                actor_user_id=admin_user.get("sub"),
                actor_name=admin_user.get("name"),
                actor_role=admin_user.get("role"),
                metadata={"name": name, "code": code},
            )

        logger.info("Department created: %s (%s)", name, code)
        return serialize_doc(created) or {}

    def update_department(
        self, dept_id: str, data: dict[str, Any], admin_user: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Update department details or toggle active status."""
        dept = department_repository.find_by_id(dept_id)
        if not dept:
            raise ValueError(f"Department with ID '{dept_id}' not found.")

        patch: dict[str, Any] = {}
        if "name" in data and data["name"] is not None:
            new_name = data["name"].strip()
            existing = department_repository.find_by_name(new_name)
            if existing and str(existing["_id"]) != dept_id:
                raise ValueError(f"Another department with name '{new_name}' already exists.")
            patch["name"] = new_name

        if "code" in data and data["code"] is not None:
            new_code = data["code"].upper().strip()
            existing = department_repository.find_by_code(new_code)
            if existing and str(existing["_id"]) != dept_id:
                raise ValueError(f"Another department with code '{new_code}' already exists.")
            patch["code"] = new_code

        if "description" in data and data["description"] is not None:
            patch["description"] = data["description"]
        if "avg_consultation_time" in data and data["avg_consultation_time"] is not None:
            patch["avg_consultation_time"] = int(data["avg_consultation_time"])
        if "is_active" in data and data["is_active"] is not None:
            patch["is_active"] = bool(data["is_active"])

        updated = department_repository.update(dept_id, patch)

        if admin_user:
            audit_repository.create_log(
                action="DEPARTMENT_UPDATED",
                entity_type="department",
                entity_id=dept_id,
                actor_user_id=admin_user.get("sub"),
                actor_name=admin_user.get("name"),
                actor_role=admin_user.get("role"),
                metadata=patch,
            )

        logger.info("Department updated: %s", dept_id)
        return serialize_doc(updated) or {}


department_service = DepartmentService()
