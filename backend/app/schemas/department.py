from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DepartmentCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=10)
    description: Optional[str] = Field(None, max_length=500)
    avg_consultation_time: int = Field(15, ge=1, le=120, description="Average minutes per patient")
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class DepartmentUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=10)
    description: Optional[str] = Field(None, max_length=500)
    avg_consultation_time: Optional[int] = Field(None, ge=1, le=120)
    is_active: Optional[bool] = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.upper().strip()
        return v
