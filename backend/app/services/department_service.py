import logging
import math
from typing import Any, Optional
from flask import current_app
from app.config import Config
from app.models.department import slugify_name
from app.repositories.department_repository import department_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.queue_repository import queue_repository
from app.repositories.audit_repository import audit_repository
from app.database.connection import serialize_doc, serialize_docs, to_object_id

logger = logging.getLogger(__name__)


def _get_base_qr_url() -> str:
    """Retrieve configured QR public base URL with fallback."""
    try:
        return current_app.config.get("QR_PUBLIC_BASE_URL", Config.QR_PUBLIC_BASE_URL)
    except Exception:
        return Config.QR_PUBLIC_BASE_URL


class DepartmentService:
    """Business logic service for hospital departments."""

    def list_departments(self, active_only: bool = True) -> list[dict[str, Any]]:
        """List departments enriched with real-time waiting metrics, doctor availability, slugs, and QR URLs."""
        # Auto seed if empty
        department_repository.seed_defaults_if_empty()

        departments = department_repository.find_all(active_only=active_only)
        if not departments:
            return []

        dept_oids = [d["_id"] for d in departments]
        base_qr_url = _get_base_qr_url().rstrip("/")

        # 1. Batch load all assigned doctors for these departments in a single query
        all_assigned = list(doctor_repository.collection.find({"department_id": {"$in": dept_oids}}))
        doctors_by_dept: dict[Any, list[dict[str, Any]]] = {}
        avail_count_by_dept: dict[Any, int] = {}
        for doc in all_assigned:
            d_id = doc["department_id"]
            doctors_by_dept.setdefault(d_id, []).append(doc)
            if doc.get("is_available", True):
                avail_count_by_dept[d_id] = avail_count_by_dept.get(d_id, 0) + 1

        # 2. Batch load queue stats using a single aggregation pipeline to eliminate N+1 latency
        pipeline = [
            {"$match": {"department_id": {"$in": dept_oids}}},
            {"$group": {
                "_id": {
                    "dept": "$department_id",
                    "status": {"$toLower": "$status"}
                },
                "count": {"$sum": 1}
            }}
        ]
        agg_results = list(queue_repository.collection.aggregate(pipeline))
        stats_by_dept: dict[Any, dict[str, int]] = {}
        for row in agg_results:
            d_id = row["_id"]["dept"]
            st = row["_id"]["status"]
            cnt = row["count"]
            if d_id not in stats_by_dept:
                stats_by_dept[d_id] = {"waiting": 0, "called": 0, "in_consultation": 0, "completed": 0, "cancelled": 0}
            if st in stats_by_dept[d_id]:
                stats_by_dept[d_id][st] += cnt

        result = []
        for dept in departments:
            d_oid = dept["_id"]
            dept_stats = stats_by_dept.get(d_oid, {"waiting": 0, "called": 0, "in_consultation": 0, "completed": 0, "cancelled": 0})
            waiting_count = dept_stats.get("waiting", 0)
            available_doctors = avail_count_by_dept.get(d_oid, 0)
            assigned_doctors = doctors_by_dept.get(d_oid, [])

            # Wait time estimation:
            # ceil(waiting_count * avg_consultation_time / effective_available_doctors)
            avg_time = dept.get("avg_consultation_time", 15)
            if available_doctors > 0:
                est_wait = math.ceil((waiting_count * avg_time) / available_doctors)
            elif len(assigned_doctors) > 0 and available_doctors == 0:
                est_wait = None
            else:
                est_wait = waiting_count * avg_time

            slug = dept.get("slug") or slugify_name(dept.get("name", "dept"))
            dept_data = serialize_doc(dept) or {}
            dept_data["slug"] = slug
            dept_data["qr_url"] = f"{base_qr_url}/department/{slug}"
            dept_data["current_waiting"] = waiting_count
            dept_data["estimated_wait_minutes"] = est_wait
            dept_data["available_doctors_count"] = available_doctors
            dept_data["total_doctors_count"] = len(assigned_doctors)
            dept_data["stats"] = dept_stats
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
        """
        Get single department details by MongoDB ObjectId, slug, or department code.
        Returns assigned doctors, active queue summary, slug, and QR destination URL.
        """
        dept = department_repository.find_by_identifier(dept_id)
        if not dept:
            raise ValueError(f"Department with ID or slug '{dept_id}' not found.")

        d_oid = dept["_id"]
        waiting_count = queue_repository.count_waiting(d_oid)
        stats = queue_repository.get_department_stats(d_oid)
        available_doctors = doctor_repository.count_available(d_oid)
        assigned_doctors = doctor_repository.find_by_department(d_oid, available_only=False)

        avg_time = dept.get("avg_consultation_time", 15)
        est_wait = math.ceil((waiting_count * avg_time) / max(available_doctors, 1)) if available_doctors > 0 else None

        base_qr_url = _get_base_qr_url().rstrip("/")
        slug = dept.get("slug") or slugify_name(dept.get("name", "dept"))

        dept_data = serialize_doc(dept) or {}
        dept_data["slug"] = slug
        dept_data["qr_url"] = f"{base_qr_url}/department/{slug}"
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

    def get_qr_config(self, base_url_override: Optional[str] = None) -> dict[str, Any]:
        """Retrieve centralized QR code configuration and department URLs."""
        base_url = (base_url_override.strip() if base_url_override else None) or _get_base_qr_url()
        base_url = base_url.rstrip("/")

        depts = self.list_departments(active_only=False)
        return {
            "qr_public_base_url": base_url,
            "departments": [
                {
                    "id": d["id"],
                    "name": d["name"],
                    "code": d["code"],
                    "slug": d["slug"],
                    "qr_url": f"{base_url}/department/{d['slug']}",
                    "is_active": d.get("is_active", True),
                    "avg_consultation_time": d.get("avg_consultation_time", 15),
                    "current_waiting": d.get("current_waiting", 0),
                }
                for d in depts
            ],
        }

    def create_department(self, data: dict[str, Any], admin_user: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Create a new hospital department with unique code and slug."""
        code = data["code"].upper().strip()
        existing_code = department_repository.find_by_code(code)
        if existing_code:
            raise ValueError(f"A department with code '{code}' already exists.")

        name = data["name"].strip()
        existing_name = department_repository.find_by_name(name)
        if existing_name:
            raise ValueError(f"A department with name '{name}' already exists.")

        slug = slugify_name(data.get("slug") or name)
        existing_slug = department_repository.find_by_slug(slug)
        if existing_slug:
            raise ValueError(f"A department with slug '{slug}' already exists.")

        dept_doc = {
            "name": name,
            "code": code,
            "slug": slug,
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
                metadata={"name": name, "code": code, "slug": slug},
            )

        logger.info("Department created: %s (%s, slug=%s)", name, code, slug)
        return serialize_doc(created) or {}

    def update_department(
        self, dept_id: str, data: dict[str, Any], admin_user: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Update department details or toggle active status."""
        dept = department_repository.find_by_identifier(dept_id)
        if not dept:
            raise ValueError(f"Department with ID or slug '{dept_id}' not found.")

        actual_id = str(dept["_id"])
        patch: dict[str, Any] = {}
        if "name" in data and data["name"] is not None:
            new_name = data["name"].strip()
            existing = department_repository.find_by_name(new_name)
            if existing and str(existing["_id"]) != actual_id:
                raise ValueError(f"Another department with name '{new_name}' already exists.")
            patch["name"] = new_name
            if "slug" not in data or not data["slug"]:
                patch["slug"] = slugify_name(new_name)

        if "code" in data and data["code"] is not None:
            new_code = data["code"].upper().strip()
            existing = department_repository.find_by_code(new_code)
            if existing and str(existing["_id"]) != actual_id:
                raise ValueError(f"Another department with code '{new_code}' already exists.")
            patch["code"] = new_code

        if "slug" in data and data["slug"] is not None:
            new_slug = slugify_name(data["slug"])
            existing_slug = department_repository.find_by_slug(new_slug)
            if existing_slug and str(existing_slug["_id"]) != actual_id:
                raise ValueError(f"Another department with slug '{new_slug}' already exists.")
            patch["slug"] = new_slug

        if "description" in data and data["description"] is not None:
            patch["description"] = data["description"]
        if "avg_consultation_time" in data and data["avg_consultation_time"] is not None:
            patch["avg_consultation_time"] = int(data["avg_consultation_time"])
        if "is_active" in data and data["is_active"] is not None:
            patch["is_active"] = bool(data["is_active"])

        updated = department_repository.update(actual_id, patch)

        if admin_user:
            audit_repository.create_log(
                action="DEPARTMENT_UPDATED",
                entity_type="department",
                entity_id=actual_id,
                actor_user_id=admin_user.get("sub"),
                actor_name=admin_user.get("name"),
                actor_role=admin_user.get("role"),
                metadata=patch,
            )

        logger.info("Department updated: %s", actual_id)
        return serialize_doc(updated) or {}


department_service = DepartmentService()
