from app.repositories.user_repository import user_repository, UserRepository
from app.repositories.department_repository import department_repository, DepartmentRepository
from app.repositories.doctor_repository import doctor_repository, DoctorRepository
from app.repositories.queue_repository import queue_repository, QueueRepository
from app.repositories.audit_repository import audit_repository, AuditRepository

__all__ = [
    "user_repository",
    "UserRepository",
    "department_repository",
    "DepartmentRepository",
    "doctor_repository",
    "DoctorRepository",
    "queue_repository",
    "QueueRepository",
    "audit_repository",
    "AuditRepository",
]
