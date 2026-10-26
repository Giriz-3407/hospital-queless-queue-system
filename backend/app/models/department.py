from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Department:
    name: str
    code: str
    description: Optional[str] = None
    avg_consultation_time: int = 15
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code.upper(),
            "description": self.description,
            "avg_consultation_time": self.avg_consultation_time,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }
