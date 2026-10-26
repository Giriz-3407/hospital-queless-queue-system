from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class JoinQueueSchema(BaseModel):
    department_id: str = Field(..., description="Target department ObjectId")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for visit or symptoms")

    @field_validator("department_id")
    @classmethod
    def validate_dept_object_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise ValueError("department_id must be a valid 24-character hex MongoDB ObjectId")
        return v


class QueueStatusUpdateSchema(BaseModel):
    status: Literal["waiting", "in_consultation", "completed", "cancelled", "no_show"] = Field(
        ..., description="Updated queue ticket status"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Staff consultation notes")
