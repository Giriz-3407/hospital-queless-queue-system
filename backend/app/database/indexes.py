import logging
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import PyMongoError
from app.models.queue import QueueStatus

logger = logging.getLogger(__name__)


def ensure_indexes(db: Database) -> dict[str, list[str]]:
    """
    Ensure all necessary MongoDB indexes are created for performance and data integrity.
    Returns a dictionary of created index names by collection.
    """
    created_indexes: dict[str, list[str]] = {}

    try:
        # 1. Users collection indexes
        users_coll = db["users"]
        idx_users_email = users_coll.create_index(
            [("email", ASCENDING)],
            unique=True,
            name="idx_users_email_unique",
            background=True,
        )
        idx_users_role = users_coll.create_index(
            [("role", ASCENDING)],
            name="idx_users_role",
            background=True,
        )
        created_indexes["users"] = [idx_users_email, idx_users_role]

        # 2. Departments collection indexes
        departments_coll = db["departments"]
        idx_dept_code = departments_coll.create_index(
            [("code", ASCENDING)],
            unique=True,
            name="idx_departments_code_unique",
            background=True,
        )
        idx_dept_name = departments_coll.create_index(
            [("name", ASCENDING)],
            unique=True,
            name="idx_departments_name_unique",
            background=True,
        )
        idx_dept_active = departments_coll.create_index(
            [("is_active", ASCENDING)],
            name="idx_departments_is_active",
            background=True,
        )
        created_indexes["departments"] = [idx_dept_code, idx_dept_name, idx_dept_active]

        # 3. Doctors collection indexes
        doctors_coll = db["doctors"]
        idx_doc_user = doctors_coll.create_index(
            [("user_id", ASCENDING)],
            unique=True,
            name="idx_doctors_user_id_unique",
            background=True,
        )
        idx_doc_dept = doctors_coll.create_index(
            [("department_id", ASCENDING)],
            name="idx_doctors_department_id",
            background=True,
        )
        idx_doc_avail = doctors_coll.create_index(
            [("is_available", ASCENDING)],
            name="idx_doctors_is_available",
            background=True,
        )
        created_indexes["doctors"] = [idx_doc_user, idx_doc_dept, idx_doc_avail]

        # 4. Queues collection indexes
        queues_coll = db["queues"]
        idx_q_dept_date = queues_coll.create_index(
            [("department_id", ASCENDING), ("queue_date", ASCENDING)],
            name="idx_queues_department_date",
            background=True,
        )
        idx_q_dept_status_join = queues_coll.create_index(
            [("department_id", ASCENDING), ("status", ASCENDING), ("joined_at", ASCENDING)],
            name="idx_queues_dept_status_join",
            background=True,
        )
        idx_q_patient_status = queues_coll.create_index(
            [("patient_id", ASCENDING), ("status", ASCENDING)],
            name="idx_queues_patient_status",
            background=True,
        )
        idx_q_patient_created = queues_coll.create_index(
            [("patient_id", ASCENDING), ("created_at", DESCENDING)],
            name="idx_queues_patient_created",
            background=True,
        )
        idx_q_ticket = queues_coll.create_index(
            [("token_number", ASCENDING)],
            name="idx_queues_token_number",
            background=True,
        )
        idx_q_patient_active_unique = queues_coll.create_index(
            [("patient_id", ASCENDING)],
            unique=True,
            partialFilterExpression={
                "status": {
                    "$in": [
                        QueueStatus.WAITING,
                        QueueStatus.CALLED,
                        QueueStatus.IN_CONSULTATION,
                        "waiting",
                        "called",
                        "in_consultation",
                    ]
                }
            },
            name="idx_queues_patient_active_unique",
            background=True,
        )
        created_indexes["queues"] = [
            idx_q_dept_date,
            idx_q_dept_status_join,
            idx_q_patient_status,
            idx_q_patient_created,
            idx_q_ticket,
            idx_q_patient_active_unique,
        ]

        # 5. Audit logs collection indexes
        audit_coll = db["audit_logs"]
        idx_audit_timestamp = audit_coll.create_index(
            [("timestamp", DESCENDING)],
            name="idx_audit_timestamp",
            background=True,
        )
        idx_audit_action = audit_coll.create_index(
            [("action", ASCENDING)],
            name="idx_audit_action",
            background=True,
        )
        idx_audit_entity = audit_coll.create_index(
            [("entity_type", ASCENDING), ("entity_id", ASCENDING)],
            name="idx_audit_entity",
            background=True,
        )
        created_indexes["audit_logs"] = [idx_audit_timestamp, idx_audit_action, idx_audit_entity]

        logger.info("Successfully verified and configured MongoDB indexes: %s", created_indexes)
        return created_indexes

    except PyMongoError as err:
        logger.error("Failed to create MongoDB indexes: %s", err)
        return created_indexes
