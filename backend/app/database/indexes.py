import logging
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import PyMongoError

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
        idx_dept_active = departments_coll.create_index(
            [("is_active", ASCENDING)],
            name="idx_departments_is_active",
            background=True,
        )
        created_indexes["departments"] = [idx_dept_code, idx_dept_active]

        # 3. Queues collection indexes
        queues_coll = db["queues"]
        idx_q_dept_status = queues_coll.create_index(
            [("department_id", ASCENDING), ("status", ASCENDING)],
            name="idx_queues_department_status",
            background=True,
        )
        idx_q_patient_status = queues_coll.create_index(
            [("patient_id", ASCENDING), ("status", ASCENDING)],
            name="idx_queues_patient_status",
            background=True,
        )
        idx_q_ticket = queues_coll.create_index(
            [("ticket_number", ASCENDING)],
            name="idx_queues_ticket_number",
            background=True,
        )
        idx_q_created = queues_coll.create_index(
            [("created_at", DESCENDING)],
            name="idx_queues_created_at",
            background=True,
        )
        created_indexes["queues"] = [
            idx_q_dept_status,
            idx_q_patient_status,
            idx_q_ticket,
            idx_q_created,
        ]

        logger.info("Successfully verified and configured MongoDB indexes: %s", created_indexes)
        return created_indexes

    except PyMongoError as err:
        logger.error("Failed to create MongoDB indexes: %s", err)
        return created_indexes
