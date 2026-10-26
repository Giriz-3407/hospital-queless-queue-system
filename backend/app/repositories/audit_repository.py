from typing import Optional, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.database.connection import mongo_manager, to_object_id


class AuditRepository:
    """Data access repository for Audit Logs in MongoDB."""

    @property
    def collection(self):
        return mongo_manager.get_collection("audit_logs")

    def create_log(
        self,
        action: str,
        entity_type: str,
        entity_id: str | ObjectId,
        actor_user_id: Optional[str | ObjectId] = None,
        actor_name: Optional[str] = None,
        actor_role: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Record an audit log entry. Strip any sensitive fields before persisting."""
        now = datetime.now(timezone.utc)
        clean_metadata = {k: v for k, v in (metadata or {}).items() if "password" not in k and "token" not in k}

        log_doc = {
            "actor_user_id": to_object_id(actor_user_id) if actor_user_id else None,
            "actor_name": actor_name,
            "actor_role": actor_role,
            "action": action.upper().strip(),
            "entity_type": entity_type.lower().strip(),
            "entity_id": str(entity_id),
            "metadata": clean_metadata,
            "timestamp": now,
        }
        res = self.collection.insert_one(log_doc)
        log_doc["_id"] = res.inserted_id
        return log_doc

    def list_logs(
        self,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if entity_type:
            query["entity_type"] = entity_type.lower().strip()
        if action:
            query["action"] = action.upper().strip()

        cursor = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        return list(cursor)

    def count_logs(
        self,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> int:
        query: dict[str, Any] = {}
        if entity_type:
            query["entity_type"] = entity_type.lower().strip()
        if action:
            query["action"] = action.upper().strip()
        return self.collection.count_documents(query)


audit_repository = AuditRepository()
