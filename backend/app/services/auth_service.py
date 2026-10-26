import logging
from typing import Any, Optional
from datetime import datetime, timezone
from app.repositories.user_repository import user_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.department_repository import department_repository
from app.repositories.audit_repository import audit_repository
from app.utils.security import hash_password, verify_password, create_access_token
from app.database.connection import serialize_doc, serialize_docs, to_object_id

logger = logging.getLogger(__name__)


class AuthService:
    """Business logic service for user registration, authentication, and profiles."""

    def register(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Public patient registration.
        Strictly forces role='patient' to prevent privilege escalation.
        """
        email = data["email"].lower().strip()
        existing = user_repository.find_by_email(email)
        if existing:
            raise ValueError(f"User with email '{email}' already exists.")

        hashed = hash_password(data["password"])
        user_doc = {
            "name": data["name"].strip(),
            "email": email,
            "password_hash": hashed,
            "phone": data.get("phone"),
            "role": "patient",
            "is_active": True,
        }

        created = user_repository.create(user_doc)
        token = create_access_token(
            user_id=str(created["_id"]),
            email=created["email"],
            role="patient",
            name=created["name"],
        )

        user_data = serialize_doc(created)
        if user_data:
            user_data.pop("password_hash", None)

        audit_repository.create_log(
            action="PATIENT_REGISTERED",
            entity_type="user",
            entity_id=str(created["_id"]),
            actor_user_id=str(created["_id"]),
            actor_name=created["name"],
            actor_role="patient",
            metadata={"email": email},
        )

        logger.info("Patient registered successfully: %s", email)
        return {
            "user": user_data,
            "token": token,
        }

    def login(self, data: dict[str, Any]) -> dict[str, Any]:
        """Authenticate user and return JWT token."""
        email = data["email"].lower().strip()
        password = data["password"]

        user = user_repository.find_by_email(email)
        if not user or not verify_password(password, user.get("password_hash", "")):
            raise ValueError("Invalid email or password.")

        if not user.get("is_active", True):
            raise PermissionError("Your account has been deactivated. Please contact hospital administration.")

        user_role = user.get("role", "patient")
        token = create_access_token(
            user_id=str(user["_id"]),
            email=user["email"],
            role=user_role,
            name=user.get("name", "User"),
        )

        user_data = serialize_doc(user)
        if user_data:
            user_data.pop("password_hash", None)

        # If user is doctor, attach doctor profile info
        if user_role == "doctor":
            doc_profile = doctor_repository.find_by_user_id(user["_id"])
            if doc_profile:
                user_data["doctor_profile"] = serialize_doc(doc_profile)

        logger.info("User logged in successfully: %s (role: %s)", email, user_role)
        return {
            "user": user_data,
            "token": token,
        }

    def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Get profile for authenticated user."""
        user = user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user_data = serialize_doc(user)
        if user_data:
            user_data.pop("password_hash", None)

        if user.get("role") == "doctor":
            doc_profile = doctor_repository.find_by_user_id(user["_id"])
            if doc_profile:
                dept = department_repository.find_by_id(doc_profile.get("department_id"))
                doc_serialized = serialize_doc(doc_profile) or {}
                if dept:
                    doc_serialized["department_name"] = dept.get("name")
                    doc_serialized["department_code"] = dept.get("code")
                user_data["doctor_profile"] = doc_serialized

        return user_data or {}

    def create_doctor_account(self, data: dict[str, Any], admin_user: dict[str, Any]) -> dict[str, Any]:
        """Admin creates a doctor user account and associates with a department."""
        email = data["email"].lower().strip()
        existing = user_repository.find_by_email(email)
        if existing:
            raise ValueError(f"User with email '{email}' already exists.")

        dept_id = to_object_id(data["department_id"])
        dept = department_repository.find_by_id(dept_id)
        if not dept:
            raise ValueError("Department specified for doctor assignment does not exist.")

        hashed = hash_password(data["password"])
        user_doc = {
            "name": data["name"].strip(),
            "email": email,
            "password_hash": hashed,
            "phone": data.get("phone"),
            "role": "doctor",
            "is_active": True,
        }
        created_user = user_repository.create(user_doc)

        doctor_doc = {
            "user_id": created_user["_id"],
            "department_id": dept_id,
            "display_name": f"Dr. {data['name'].strip()}" if not data['name'].strip().lower().startswith("dr.") else data['name'].strip(),
            "specialty": data.get("specialty") or dept.get("name"),
            "is_available": True,
        }
        created_doctor = doctor_repository.create(doctor_doc)

        audit_repository.create_log(
            action="DOCTOR_CREATED",
            entity_type="doctor",
            entity_id=str(created_doctor["_id"]),
            actor_user_id=admin_user.get("sub"),
            actor_name=admin_user.get("name"),
            actor_role=admin_user.get("role"),
            metadata={
                "doctor_name": doctor_doc["display_name"],
                "doctor_email": email,
                "department_name": dept.get("name"),
            },
        )

        user_clean = serialize_doc(created_user) or {}
        user_clean.pop("password_hash", None)
        doc_clean = serialize_doc(created_doctor) or {}
        doc_clean["department_name"] = dept.get("name")
        doc_clean["user"] = user_clean

        logger.info("Doctor account created successfully: %s by admin %s", email, admin_user.get("sub"))
        return doc_clean

    def update_doctor(
        self, doctor_id: str, update_data: dict[str, Any], admin_user: dict[str, Any]
    ) -> dict[str, Any]:
        """Admin updates doctor assignment or availability."""
        doctor = doctor_repository.find_by_id(doctor_id)
        if not doctor:
            raise ValueError(f"Doctor with ID '{doctor_id}' not found.")

        patch: dict[str, Any] = {}
        if "department_id" in update_data and update_data["department_id"]:
            new_dept_id = to_object_id(update_data["department_id"])
            dept = department_repository.find_by_id(new_dept_id)
            if not dept:
                raise ValueError("Target department does not exist.")
            patch["department_id"] = new_dept_id
        if "display_name" in update_data and update_data["display_name"]:
            patch["display_name"] = update_data["display_name"].strip()
        if "specialty" in update_data and update_data["specialty"]:
            patch["specialty"] = update_data["specialty"].strip()
        if "is_available" in update_data and update_data["is_available"] is not None:
            patch["is_available"] = bool(update_data["is_available"])

        updated = doctor_repository.update(doctor_id, patch)

        audit_repository.create_log(
            action="DOCTOR_UPDATED",
            entity_type="doctor",
            entity_id=doctor_id,
            actor_user_id=admin_user.get("sub"),
            actor_name=admin_user.get("name"),
            actor_role=admin_user.get("role"),
            metadata=patch,
        )

        doc_clean = serialize_doc(updated) or {}
        dept = department_repository.find_by_id(updated["department_id"])
        if dept:
            doc_clean["department_name"] = dept.get("name")
        user = user_repository.find_by_id(updated["user_id"])
        if user:
            user_clean = serialize_doc(user) or {}
            user_clean.pop("password_hash", None)
            doc_clean["user"] = user_clean

        return doc_clean

    def list_doctors(self, dept_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List doctors with department and user profile details."""
        doctors = doctor_repository.list_all(dept_id=dept_id)
        result = []
        for d in doctors:
            item = serialize_doc(d) or {}
            dept = department_repository.find_by_id(d.get("department_id"))
            if dept:
                item["department_name"] = dept.get("name")
                item["department_code"] = dept.get("code")
            u = user_repository.find_by_id(d.get("user_id"))
            if u:
                u_clean = serialize_doc(u) or {}
                u_clean.pop("password_hash", None)
                item["user"] = u_clean
            result.append(item)
        return result

    def list_users(self, role: Optional[str] = None, limit: int = 50, skip: int = 0) -> dict[str, Any]:
        """Admin user listing with pagination."""
        users = user_repository.list_users(role=role, limit=limit, skip=skip)
        total = user_repository.count_users(role=role)
        clean_users = []
        for u in users:
            clean = serialize_doc(u) or {}
            clean.pop("password_hash", None)
            clean_users.append(clean)

        return {
            "users": clean_users,
            "total": total,
            "limit": limit,
            "skip": skip,
        }

    def seed_admin_user(self, email: str, password: str, name: str = "Hospital Administrator") -> dict[str, Any]:
        """CLI / Secure procedure for initial administrator provisioning."""
        clean_email = email.lower().strip()
        existing = user_repository.find_by_email(clean_email)
        hashed = hash_password(password)

        if existing:
            user_repository.update(existing["_id"], {
                "password_hash": hashed,
                "role": "admin",
                "name": name.strip(),
                "is_active": True,
            })
            logger.info("Existing user %s upgraded to administrator.", clean_email)
            return {"email": clean_email, "action": "updated"}
        else:
            user_doc = {
                "name": name.strip(),
                "email": clean_email,
                "password_hash": hashed,
                "role": "admin",
                "is_active": True,
            }
            user_repository.create(user_doc)
            logger.info("Administrator user created successfully: %s", clean_email)
            return {"email": clean_email, "action": "created"}


auth_service = AuthService()
