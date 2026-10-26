from app.schemas.auth import (
    UserRegisterSchema,
    UserLoginSchema,
    DoctorCreateSchema,
    DoctorUpdateSchema,
)
from app.schemas.department import DepartmentCreateSchema, DepartmentUpdateSchema
from app.schemas.queue import JoinQueueSchema, QueueStatusUpdateSchema

__all__ = [
    "UserRegisterSchema",
    "UserLoginSchema",
    "DoctorCreateSchema",
    "DoctorUpdateSchema",
    "DepartmentCreateSchema",
    "DepartmentUpdateSchema",
    "JoinQueueSchema",
    "QueueStatusUpdateSchema",
]
