from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


@dataclass
class Doctor:
    user_id: ObjectId
    department_id: ObjectId
    display_name: str
    specialty: Optional[str] = None
    is_available: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "department_id": self.department_id,
            "display_name": self.display_name.strip(),
            "specialty": self.specialty,
            "is_available": self.is_available,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
