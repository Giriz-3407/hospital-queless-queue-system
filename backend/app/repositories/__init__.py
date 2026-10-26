from app.repositories.user_repository import user_repository, UserRepository
from app.repositories.department_repository import department_repository, DepartmentRepository
from app.repositories.queue_repository import queue_repository, QueueRepository

__all__ = [
    "user_repository",
    "UserRepository",
    "department_repository",
    "DepartmentRepository",
    "queue_repository",
    "QueueRepository",
]
