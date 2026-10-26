from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
from bson import ObjectId


@dataclass
class AuditLog:
    action: str
    entity_type: str
    entity_id: str
    actor_user_id: Optional[ObjectId] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "actor_user_id": self.actor_user_id,
            "actor_name": self.actor_name,
            "actor_role": self.actor_role,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "metadata": self.metadata or {},
            "timestamp": self.timestamp,
        }
