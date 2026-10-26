from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class QueueStatus:
    WAITING = "WAITING"
    CALLED = "CALLED"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

    ALL_STATUSES = [WAITING, CALLED, IN_CONSULTATION, COMPLETED, CANCELLED, NO_SHOW]
    ACTIVE_STATUSES = [WAITING, CALLED, IN_CONSULTATION]
    TERMINAL_STATUSES = [COMPLETED, CANCELLED, NO_SHOW]

    @classmethod
    def normalize(cls, status: str) -> str:
        s = status.upper().strip()
        if s in cls.ALL_STATUSES:
            return s
        # handle lowercase variants like "waiting", "in_consultation"
        for st in cls.ALL_STATUSES:
            if s == st.replace("_", "") or s == st:
                return st
        return s


@dataclass
class QueueTicket:
    department_id: ObjectId
    department_name: str
    department_code: str
    patient_id: ObjectId
    patient_name: str
    token_number: str
    queue_date: str  # YYYY-MM-DD
    position: int = 1
    estimated_wait_minutes: Optional[int] = 0
    status: str = QueueStatus.WAITING
    doctor_id: Optional[ObjectId] = None
    doctor_name: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    called_at: Optional[datetime] = None
    consultation_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "department_id": self.department_id,
            "department_name": self.department_name,
            "department_code": self.department_code,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "token_number": self.token_number,
            "queue_date": self.queue_date,
            "position": self.position,
            "estimated_wait_minutes": self.estimated_wait_minutes,
            "status": self.status,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "reason": self.reason,
            "notes": self.notes,
            "joined_at": self.joined_at,
            "called_at": self.called_at,
            "consultation_started_at": self.consultation_started_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
