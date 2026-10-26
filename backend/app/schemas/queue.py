from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from app.models.queue import QueueStatus


class JoinQueueSchema(BaseModel):
    department_id: str = Field(..., min_length=1, max_length=100, description="Target department ObjectId, slug, or code")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for visit or symptoms")


class QueueStatusUpdateSchema(BaseModel):
    status: str = Field(..., description="Updated queue ticket status")
    notes: Optional[str] = Field(None, max_length=500, description="Staff consultation notes")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        norm = QueueStatus.normalize(v)
        if norm not in QueueStatus.ALL_STATUSES:
            raise ValueError(f"Invalid queue status '{v}'. Allowed statuses: {QueueStatus.ALL_STATUSES}")
        return norm


class WalkInQueueCreateSchema(BaseModel):
    department_id: str = Field(..., min_length=1, max_length=100, description="Target department ObjectId, slug, or code")
    patient_name: str = Field(..., min_length=2, max_length=100, description="Walk-in patient's full legal name")
    phone: Optional[str] = Field(None, max_length=25, description="Optional patient contact phone number")
    age: Optional[int] = Field(None, ge=0, le=130, description="Optional patient age in years")
    reason: Optional[str] = Field(None, max_length=500, description="Optional visit reason or chief complaint")

    @field_validator("patient_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Patient name must contain at least 2 characters")
        return stripped

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        return v.strip()
