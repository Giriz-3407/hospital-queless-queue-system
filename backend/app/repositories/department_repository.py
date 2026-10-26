import logging
from typing import Optional, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.database.connection import mongo_manager, to_object_id

logger = logging.getLogger(__name__)

DEFAULT_DEPARTMENTS = [
    {
        "name": "General Medicine",
        "code": "GEN",
        "description": "Routine check-ups, acute minor illnesses, and primary health consultations.",
        "avg_consultation_time": 10,
        "is_active": True,
    },
    {
        "name": "Cardiology",
        "code": "CARD",
        "description": "Specialized heart evaluations, ECG reviews, and cardiovascular consultations.",
        "avg_consultation_time": 20,
        "is_active": True,
    },
    {
        "name": "Pediatrics",
        "code": "PED",
        "description": "Healthcare, developmental evaluations, and wellness care for infants and children.",
        "avg_consultation_time": 15,
        "is_active": True,
    },
    {
        "name": "Orthopedics",
        "code": "ORTHO",
        "description": "Bone, joint, ligament, and spine diagnostic consultations.",
        "avg_consultation_time": 15,
        "is_active": True,
    },
    {
        "name": "Dermatology",
        "code": "DERM",
        "description": "Skin conditions, allergies, rashes, and hair/nail specialist care.",
        "avg_consultation_time": 12,
        "is_active": True,
    },
]


class DepartmentRepository:
    """Data access repository for Departments collection in MongoDB."""

    @property
    def collection(self):
        return mongo_manager.get_collection("departments")

    def find_all(self, active_only: bool = True) -> list[dict[str, Any]]:
        query = {"is_active": True} if active_only else {}
        cursor = self.collection.find(query).sort("name", 1)
        return list(cursor)

    def find_by_id(self, dept_id: str | ObjectId) -> Optional[dict[str, Any]]:
        oid = to_object_id(dept_id)
        return self.collection.find_one({"_id": oid})

    def find_by_code(self, code: str) -> Optional[dict[str, Any]]:
        return self.collection.find_one({"code": code.upper().strip()})

    def create(self, dept_dict: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        dept_dict.setdefault("created_at", now)
        dept_dict["code"] = dept_dict["code"].upper().strip()
        dept_dict.setdefault("is_active", True)

        result = self.collection.insert_one(dept_dict)
        dept_dict["_id"] = result.inserted_id
        return dept_dict

    def seed_defaults_if_empty(self) -> int:
        """Seed initial departments if none exist in the database."""
        try:
            count = self.collection.count_documents({})
            if count == 0:
                logger.info("Departments collection is empty. Seeding %d initial departments...", len(DEFAULT_DEPARTMENTS))
                now = datetime.now(timezone.utc)
                docs = [{**dept, "created_at": now} for dept in DEFAULT_DEPARTMENTS]
                res = self.collection.insert_many(docs)
                return len(res.inserted_ids)
            return 0
        except Exception as err:
            logger.warning("Could not auto-seed departments: %s", err)
            return 0


department_repository = DepartmentRepository()
