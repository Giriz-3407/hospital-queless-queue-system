from typing import Optional, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.database.connection import mongo_manager, to_object_id


class DoctorRepository:
    """Data access repository for Doctors collection in MongoDB."""

    @property
    def collection(self):
        return mongo_manager.get_collection("doctors")

    def find_by_id(self, doctor_id: str | ObjectId) -> Optional[dict[str, Any]]:
        oid = to_object_id(doctor_id)
        return self.collection.find_one({"_id": oid})

    def find_by_user_id(self, user_id: str | ObjectId) -> Optional[dict[str, Any]]:
        oid = to_object_id(user_id)
        return self.collection.find_one({"user_id": oid})

    def find_by_department(
        self, dept_id: str | ObjectId, available_only: bool = False
    ) -> list[dict[str, Any]]:
        oid = to_object_id(dept_id)
        query: dict[str, Any] = {"department_id": oid}
        if available_only:
            query["is_available"] = True
        return list(self.collection.find(query).sort("display_name", 1))

    def list_all(self, dept_id: Optional[str | ObjectId] = None) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if dept_id:
            query["department_id"] = to_object_id(dept_id)
        return list(self.collection.find(query).sort("display_name", 1))

    def count_available(self, dept_id: str | ObjectId) -> int:
        oid = to_object_id(dept_id)
        return self.collection.count_documents({
            "department_id": oid,
            "is_available": True,
        })

    def create(self, doctor_dict: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        doctor_dict.setdefault("created_at", now)
        doctor_dict.setdefault("updated_at", now)
        doctor_dict.setdefault("is_available", True)
        doctor_dict["user_id"] = to_object_id(doctor_dict["user_id"])
        doctor_dict["department_id"] = to_object_id(doctor_dict["department_id"])

        result = self.collection.insert_one(doctor_dict)
        doctor_dict["_id"] = result.inserted_id
        return doctor_dict

    def update(self, doctor_id: str | ObjectId, update_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        oid = to_object_id(doctor_id)
        update_data["updated_at"] = datetime.now(timezone.utc)
        if "department_id" in update_data:
            update_data["department_id"] = to_object_id(update_data["department_id"])

        return self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_data},
            return_document=True,
        )

    def count_doctors(self) -> int:
        return self.collection.count_documents({})


doctor_repository = DoctorRepository()
