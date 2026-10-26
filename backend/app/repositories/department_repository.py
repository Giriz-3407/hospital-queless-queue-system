import logging
import re
from typing import Optional, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.database.connection import mongo_manager, to_object_id
from app.models.department import slugify_name

logger = logging.getLogger(__name__)

DEFAULT_DEPARTMENTS = [
    {
        "name": "General Medicine",
        "code": "GEN",
        "slug": "general-medicine",
        "description": "Routine check-ups, acute minor illnesses, and primary health consultations.",
        "avg_consultation_time": 10,
        "is_active": True,
    },
    {
        "name": "Cardiology",
        "code": "CARD",
        "slug": "cardiology",
        "description": "Specialized heart evaluations, ECG reviews, and cardiovascular consultations.",
        "avg_consultation_time": 20,
        "is_active": True,
    },
    {
        "name": "Pediatrics",
        "code": "PED",
        "slug": "pediatrics",
        "description": "Healthcare, developmental evaluations, and wellness care for infants and children.",
        "avg_consultation_time": 15,
        "is_active": True,
    },
    {
        "name": "Orthopedics",
        "code": "ORTHO",
        "slug": "orthopedics",
        "description": "Bone, joint, ligament, and spine diagnostic consultations.",
        "avg_consultation_time": 15,
        "is_active": True,
    },
    {
        "name": "Dermatology",
        "code": "DERM",
        "slug": "dermatology",
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

    def find_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return self.collection.find_one({"name": {"$regex": f"^{name.strip()}$", "$options": "i"}})

    def find_by_slug(self, slug: str) -> Optional[dict[str, Any]]:
        clean_slug = slug.lower().strip()
        doc = self.collection.find_one({"slug": clean_slug})
        if doc:
            return doc

        # British/American spelling alias handling
        if clean_slug == "orthopaedics":
            return self.collection.find_one({"$or": [{"slug": "orthopedics"}, {"code": "ORTHO"}]})
        elif clean_slug == "orthopedics":
            return self.collection.find_one({"$or": [{"slug": "orthopaedics"}, {"code": "ORTHO"}]})

        # Try slugified matching on name
        for candidate in self.find_all(active_only=False):
            candidate_slug = candidate.get("slug") or slugify_name(candidate.get("name", ""))
            if candidate_slug == clean_slug:
                return candidate
        return None

    def find_by_identifier(self, identifier: str) -> Optional[dict[str, Any]]:
        """
        Resolve department by slug, department code, MongoDB ObjectId, or name.
        Safe against malformed inputs and does not throw on invalid ObjectIds.
        """
        if not identifier:
            return None

        ident = identifier.strip()

        # 1. Try slug
        by_slug = self.find_by_slug(ident)
        if by_slug:
            return by_slug

        # 2. Try department code
        by_code = self.find_by_code(ident)
        if by_code:
            return by_code

        # 3. Try MongoDB ObjectId if 24-character hex
        if len(ident) == 24:
            try:
                oid = ObjectId(ident)
                by_id = self.collection.find_one({"_id": oid})
                if by_id:
                    return by_id
            except Exception:
                pass

        # 4. Try exact case-insensitive name match
        by_name = self.find_by_name(ident)
        if by_name:
            return by_name

        # 5. Try slugifying the identifier itself
        slugified = slugify_name(ident)
        if slugified != ident:
            return self.find_by_slug(slugified)

        return None

    def create(self, dept_dict: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        dept_dict.setdefault("created_at", now)
        dept_dict.setdefault("updated_at", now)
        dept_dict["code"] = dept_dict["code"].upper().strip()
        dept_dict["name"] = dept_dict["name"].strip()
        if not dept_dict.get("slug"):
            dept_dict["slug"] = slugify_name(dept_dict["name"])
        else:
            dept_dict["slug"] = slugify_name(dept_dict["slug"])
        dept_dict.setdefault("is_active", True)
        dept_dict.setdefault("avg_consultation_time", 15)

        result = self.collection.insert_one(dept_dict)
        dept_dict["_id"] = result.inserted_id
        return dept_dict

    def update(self, dept_id: str | ObjectId, update_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        oid = to_object_id(dept_id)
        update_data["updated_at"] = datetime.now(timezone.utc)
        if "code" in update_data:
            update_data["code"] = update_data["code"].upper().strip()
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()
            if "slug" not in update_data:
                update_data["slug"] = slugify_name(update_data["name"])
        if "slug" in update_data and update_data["slug"]:
            update_data["slug"] = slugify_name(update_data["slug"])

        return self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_data},
            return_document=True,
        )

    def count_departments(self, active_only: bool = False) -> int:
        query = {"is_active": True} if active_only else {}
        return self.collection.count_documents(query)

    def seed_defaults_if_empty(self) -> int:
        """Seed initial departments if none exist in the database, and backfill slugs."""
        try:
            count = self.collection.count_documents({})
            if count == 0:
                logger.info("Departments collection is empty. Seeding %d initial departments...", len(DEFAULT_DEPARTMENTS))
                now = datetime.now(timezone.utc)
                docs = [{**dept, "created_at": now, "updated_at": now} for dept in DEFAULT_DEPARTMENTS]
                res = self.collection.insert_many(docs)
                return len(res.inserted_ids)
            else:
                # Backfill slug for existing departments without slug
                cursor = self.collection.find({"slug": {"$exists": False}})
                for doc in cursor:
                    self.collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"slug": slugify_name(doc.get("name", "dept"))}}
                    )
            return 0
        except Exception as err:
            logger.warning("Could not auto-seed departments: %s", err)
            return 0


department_repository = DepartmentRepository()
