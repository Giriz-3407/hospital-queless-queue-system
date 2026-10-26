from typing import Optional, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.database.connection import mongo_manager, to_object_id


class UserRepository:
    """Data access repository for Users collection in MongoDB."""

    @property
    def collection(self):
        return mongo_manager.get_collection("users")

    def find_by_id(self, user_id: str | ObjectId) -> Optional[dict[str, Any]]:
        oid = to_object_id(user_id)
        return self.collection.find_one({"_id": oid})

    def find_by_email(self, email: str) -> Optional[dict[str, Any]]:
        return self.collection.find_one({"email": email.lower().strip()})

    def create(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        user_dict.setdefault("created_at", now)
        user_dict.setdefault("updated_at", now)
        user_dict["email"] = user_dict["email"].lower().strip()
        user_dict.setdefault("is_active", True)

        result = self.collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        return user_dict

    def update(self, user_id: str | ObjectId, update_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        oid = to_object_id(user_id)
        update_data["updated_at"] = datetime.now(timezone.utc)
        return self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_data},
            return_document=True,
        )

    def list_users(self, role: Optional[str] = None, limit: int = 50, skip: int = 0) -> list[dict[str, Any]]:
        query = {"role": role} if role else {}
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return list(cursor)

    def count_users(self, role: Optional[str] = None) -> int:
        query = {"role": role} if role else {}
        return self.collection.count_documents(query)


user_repository = UserRepository()
