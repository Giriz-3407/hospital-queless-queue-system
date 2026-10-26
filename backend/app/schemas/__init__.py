from app.schemas.auth import UserRegisterSchema, UserLoginSchema
from app.schemas.department import DepartmentCreateSchema, DepartmentUpdateSchema
from app.schemas.queue import JoinQueueSchema, QueueStatusUpdateSchema

__all__ = [
    "UserRegisterSchema",
    "UserLoginSchema",
    "DepartmentCreateSchema",
    "DepartmentUpdateSchema",
    "JoinQueueSchema",
    "QueueStatusUpdateSchema",
]
