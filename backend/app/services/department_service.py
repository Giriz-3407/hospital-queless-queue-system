import logging
from typing import Any
from app.repositories.department_repository import department_repository
from app.repositories.queue_repository import queue_repository
from app.database.connection import serialize_doc, serialize_docs

logger = logging.getLogger(__name__)


class DepartmentService:
    """Business logic for departments and queue capacity visibility."""

    def list_departments(self) -> list[dict[str, Any]]:
        # Auto-seed initial defaults if empty
        department_repository.seed_defaults_if_empty()

        departments = department_repository.find_all(active_only=True)
        results = []
        for dept in departments:
            dept_id = dept["_id"]
            waiting_count = queue_repository.count_waiting(dept_id)
            avg_time = dept.get("avg_consultation_time", 15)
            estimated_wait = waiting_count * avg_time

            serialized = serialize_doc(dept)
            if serialized:
                serialized["current_waiting"] = waiting_count
                serialized["estimated_wait_minutes"] = estimated_wait
                results.append(serialized)
        return results

    def get_department_by_id(self, dept_id: str) -> dict[str, Any]:
        dept = department_repository.find_by_id(dept_id)
        if not dept:
            raise ValueError(f"Department with ID '{dept_id}' not found.")
        serialized = serialize_doc(dept)
        if serialized:
            dept_id_oid = dept["_id"]
            serialized["current_waiting"] = queue_repository.count_waiting(dept_id_oid)
            serialized["stats"] = queue_repository.get_department_stats(dept_id_oid)
        return serialized or {}

    def create_department(self, data: dict[str, Any]) -> dict[str, Any]:
        code = data["code"].upper().strip()
        existing = department_repository.find_by_code(code)
        if existing:
            raise ValueError(f"Department with code '{code}' already exists.")

        created = department_repository.create(data)
        return serialize_doc(created) or {}


department_service = DepartmentService()
