import argparse
import getpass
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from app.config import get_config
from app.database.connection import mongo_manager
from app.database.indexes import ensure_indexes
from app.repositories.department_repository import department_repository, DEFAULT_DEPARTMENTS
from app.repositories.user_repository import user_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.queue_repository import queue_repository
from app.repositories.audit_repository import audit_repository
from app.services.auth_service import auth_service
from app.services.queue_service import queue_service
from app.utils.security import hash_password


def seed_admin(email: str = None, password: str = None, name: str = None):
    """Seed or update an administrator account securely."""
    if not email:
        email = os.getenv("ADMIN_EMAIL") or input("Enter administrator email [admin@hospital.org]: ").strip() or "admin@hospital.org"

    if not password:
        password = os.getenv("ADMIN_PASSWORD")
        if not password:
            password = getpass.getpass("Enter administrator password (min 8 chars): ")
            confirm = getpass.getpass("Confirm administrator password: ")
            if password != confirm:
                print("Error: Passwords do not match.")
                sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    if not name:
        name = os.getenv("ADMIN_NAME") or "Hospital Chief Administrator"

    res = auth_service.seed_admin_user(email=email, password=password, name=name)
    print(f"\nAdministrator account successfully {res['action']}: {email}")


def seed_demo_data():
    """Seed synthetic demonstration data: departments, doctors, patients, and active queue entries."""
    print("--- Seeding Demo Data ---")

    # 1. Departments
    department_repository.seed_defaults_if_empty()
    departments = department_repository.find_all(active_only=False)
    print(f"Verified {len(departments)} departments in database.")

    # 2. Demo Doctors (one per department)
    demo_doctors_data = [
        {"name": "Dr. Sarah Smith", "email": "dr.smith@hospital.org", "dept_code": "GEN", "spec": "Primary Care Physician"},
        {"name": "Dr. Marcus Vance", "email": "dr.vance@hospital.org", "dept_code": "CARD", "spec": "Senior Cardiologist"},
        {"name": "Dr. Emily Chen", "email": "dr.chen@hospital.org", "dept_code": "PED", "spec": "Pediatric Specialist"},
        {"name": "Dr. David Miller", "email": "dr.miller@hospital.org", "dept_code": "ORTHO", "spec": "Orthopedic Surgeon"},
        {"name": "Dr. Priya Patel", "email": "dr.patel@hospital.org", "dept_code": "DERM", "spec": "Consultant Dermatologist"},
    ]

    doctor_docs = []
    for d in demo_doctors_data:
        existing_user = user_repository.find_by_email(d["email"])
        dept = department_repository.find_by_code(d["dept_code"])
        if not dept:
            continue

        if not existing_user:
            user = user_repository.create({
                "name": d["name"],
                "email": d["email"],
                "password_hash": hash_password("DoctorPass123!"),
                "role": "doctor",
                "phone": "+1-555-0101",
                "is_active": True,
            })
            existing_user = user

        existing_doc = doctor_repository.find_by_user_id(existing_user["_id"])
        if not existing_doc:
            doc = doctor_repository.create({
                "user_id": existing_user["_id"],
                "department_id": dept["_id"],
                "display_name": d["name"],
                "specialty": d["spec"],
                "is_available": True,
            })
            doctor_docs.append(doc)
            print(f"Created Doctor: {d['name']} ({d['email']}) -> {dept['name']}")
        else:
            doctor_docs.append(existing_doc)

    # 3. Demo Patients
    demo_patients_data = [
        {"name": "Alice Johnson", "email": "alice@example.com"},
        {"name": "Bob Martinez", "email": "bob@example.com"},
        {"name": "Charlie Brown", "email": "charlie@example.com"},
        {"name": "Diana Prince", "email": "diana@example.com"},
        {"name": "Evan Wright", "email": "evan@example.com"},
    ]

    patient_users = []
    for p in demo_patients_data:
        user = user_repository.find_by_email(p["email"])
        if not user:
            user = user_repository.create({
                "name": p["name"],
                "email": p["email"],
                "password_hash": hash_password("PatientPass123!"),
                "role": "patient",
                "phone": "+1-555-0120",
                "is_active": True,
            })
            print(f"Created Patient: {p['name']} ({p['email']})")
        patient_users.append(user)

    # 4. Demo Queues
    gen_dept = department_repository.find_by_code("GEN")
    card_dept = department_repository.find_by_code("CARD")

    if gen_dept and len(patient_users) >= 3:
        # Check existing active tickets
        for idx, patient in enumerate(patient_users[:3]):
            existing = queue_repository.find_active_by_patient_and_dept(patient["_id"], gen_dept["_id"])
            if not existing:
                try:
                    ticket = queue_service.join_queue(
                        patient_id=str(patient["_id"]),
                        patient_name=patient["name"],
                        department_id=str(gen_dept["_id"]),
                        reason=f"Routine checkup & consultation #{idx + 1}",
                    )
                    print(f"Created Queue Ticket: {ticket['token_number']} for {patient['name']} in {gen_dept['name']}")
                except Exception as ex:
                    print(f"Queue note: {ex}")

    if card_dept and len(patient_users) >= 4:
        patient = patient_users[3]
        existing = queue_repository.find_active_by_patient_and_dept(patient["_id"], card_dept["_id"])
        if not existing:
            try:
                ticket = queue_service.join_queue(
                    patient_id=str(patient["_id"]),
                    patient_name=patient["name"],
                    department_id=str(card_dept["_id"]),
                    reason="ECG follow-up and blood pressure check",
                )
                print(f"Created Queue Ticket: {ticket['token_number']} for {patient['name']} in {card_dept['name']}")
            except Exception as ex:
                print(f"Queue note: {ex}")

    print("\n=======================================================")
    print(" DEMO DATA SEEDING COMPLETE")
    print(" Demo Doctor Login:  dr.smith@hospital.org / DoctorPass123!")
    print(" Demo Patient Login: alice@example.com / PatientPass123!")
    print("=======================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Queueless Hospital Database Seeder")
    parser.add_argument("--admin", action="store_true", help="Create or update an administrator account")
    parser.add_argument("--demo", action="store_true", help="Seed demonstration data (departments, doctors, patients, queues)")
    parser.add_argument("--email", type=str, help="Administrator email")
    parser.add_argument("--password", type=str, help="Administrator password")
    parser.add_argument("--name", type=str, help="Administrator full name")

    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if not mongo_manager.is_connected():
            print("Error: Could not connect to MongoDB. Please check your MONGODB_URI.")
            sys.exit(1)

        ensure_indexes(mongo_manager.db)

        if args.admin:
            seed_admin(email=args.email, password=args.password, name=args.name)
        elif args.demo:
            seed_demo_data()
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
