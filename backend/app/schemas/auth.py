from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from bson import ObjectId


class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: EmailStr = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password with minimum 8 characters")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    role: Optional[str] = Field("patient", description="Assigned role (public registration is restricted to patient)")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("role")
    @classmethod
    def enforce_patient_role(cls, v: Optional[str]) -> str:
        # Public registration must never grant doctor or admin privileges
        if v and v.lower() not in ("patient", ""):
            raise ValueError("Public registration is restricted to the 'patient' role. Staff/Doctor accounts must be created by an administrator.")
        return "patient"


class UserLoginSchema(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class DoctorCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Doctor full name")
    email: EmailStr = Field(..., description="Doctor login email")
    password: str = Field(..., min_length=8, max_length=128, description="Initial password")
    department_id: str = Field(..., description="Assigned department ObjectId")
    specialty: Optional[str] = Field(None, max_length=100, description="Doctor specialty")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("department_id")
    @classmethod
    def validate_dept_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise ValueError("department_id must be a valid 24-character hex MongoDB ObjectId")
        return v


class DoctorUpdateSchema(BaseModel):
    department_id: Optional[str] = Field(None, description="New assigned department ObjectId")
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    specialty: Optional[str] = Field(None, max_length=100)
    is_available: Optional[bool] = Field(None, description="Whether doctor is currently on duty/available")

    @field_validator("department_id")
    @classmethod
    def validate_dept_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not ObjectId.is_valid(v):
            raise ValueError("department_id must be a valid 24-character hex MongoDB ObjectId")
        return v
