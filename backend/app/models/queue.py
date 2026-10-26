from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


@dataclass
class QueueTicket:
    department_id: ObjectId
    department_name: str
    department_code: str
    patient_id: ObjectId
    patient_name: str
    ticket_number: str
    position: int
    estimated_wait_minutes: int
    status: str = "waiting"  # waiting, in_consultation, completed, cancelled, no_show
    reason: Optional[str] = None
    called_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "department_id": self.department_id,
            "department_name": self.department_name,
            "department_code": self.department_code,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "ticket_number": self.ticket_number,
            "position": self.position,
            "estimated_wait_minutes": self.estimated_wait_minutes,
            "status": self.status,
            "reason": self.reason,
            "called_at": self.called_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
