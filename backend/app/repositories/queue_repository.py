from typing import Optional, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.database.connection import mongo_manager, to_object_id


class QueueRepository:
    """Data access repository for Queues collection in MongoDB."""

    @property
    def collection(self):
        return mongo_manager.get_collection("queues")

    def find_by_id(self, queue_id: str | ObjectId) -> Optional[dict[str, Any]]:
        oid = to_object_id(queue_id)
        return self.collection.find_one({"_id": oid})

    def find_active_by_patient_and_dept(
        self, patient_id: str | ObjectId, dept_id: str | ObjectId
    ) -> Optional[dict[str, Any]]:
        """Find an active queue ticket for a given patient in a specific department."""
        p_oid = to_object_id(patient_id)
        d_oid = to_object_id(dept_id)
        return self.collection.find_one({
            "patient_id": p_oid,
            "department_id": d_oid,
            "status": {"$in": ["waiting", "in_consultation"]},
        })

    def find_by_patient_id(
        self, patient_id: str | ObjectId, active_only: bool = False
    ) -> list[dict[str, Any]]:
        """Find tickets for a patient, ordered by creation date."""
        p_oid = to_object_id(patient_id)
        query: dict[str, Any] = {"patient_id": p_oid}
        if active_only:
            query["status"] = {"$in": ["waiting", "in_consultation"]}
        cursor = self.collection.find(query).sort("created_at", -1)
        return list(cursor)

    def find_by_department(
        self, dept_id: Optional[str | ObjectId] = None, status: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Find queue tickets by department and optional status."""
        query: dict[str, Any] = {}
        if dept_id:
            query["department_id"] = to_object_id(dept_id)
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort([
            ("created_at", 1)  # FIFO order for queues
        ])
        return list(cursor)

    def count_waiting_before(self, dept_id: ObjectId, created_at: datetime) -> int:
        """Count how many patients are waiting before a given ticket creation timestamp."""
        return self.collection.count_documents({
            "department_id": dept_id,
            "status": "waiting",
            "created_at": {"$lt": created_at},
        })

    def count_waiting(self, dept_id: ObjectId) -> int:
        """Count total patients currently waiting in this department."""
        return self.collection.count_documents({
            "department_id": dept_id,
            "status": "waiting",
        })

    def get_next_ticket_number(self, dept_code: str) -> str:
        """Generate a sequential ticket number for the current calendar day."""
        now = datetime.now(timezone.utc)
        start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
        count_today = self.collection.count_documents({
            "department_code": dept_code.upper(),
            "created_at": {"$gte": start_of_day},
        })
        sequence = count_today + 1
        return f"{dept_code.upper()}-{sequence:03d}"

    def create(self, ticket_dict: dict[str, Any]) -> dict[str, Any]:
        """Insert a new queue ticket."""
        now = datetime.now(timezone.utc)
        ticket_dict.setdefault("created_at", now)
        ticket_dict.setdefault("updated_at", now)
        ticket_dict.setdefault("status", "waiting")

        result = self.collection.insert_one(ticket_dict)
        ticket_dict["_id"] = result.inserted_id
        return ticket_dict

    def update_status(
        self,
        queue_id: str | ObjectId,
        status: str,
        notes: Optional[str] = None,
        staff_id: Optional[str | ObjectId] = None,
    ) -> Optional[dict[str, Any]]:
        """Update ticket status (waiting, in_consultation, completed, cancelled, no_show)."""
        oid = to_object_id(queue_id)
        now = datetime.now(timezone.utc)

        update_fields: dict[str, Any] = {
            "status": status,
            "updated_at": now,
        }
        if notes is not None:
            update_fields["notes"] = notes
        if staff_id:
            update_fields["updated_by_staff_id"] = to_object_id(staff_id)

        if status == "in_consultation":
            update_fields["called_at"] = now
        elif status in ("completed", "cancelled", "no_show"):
            update_fields["completed_at"] = now

        return self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_fields},
            return_document=True,
        )

    def get_currently_serving(self, dept_id: ObjectId) -> Optional[dict[str, Any]]:
        """Return the ticket currently in consultation for a department."""
        return self.collection.find_one({
            "department_id": dept_id,
            "status": "in_consultation",
        })

    def get_department_stats(self, dept_id: ObjectId) -> dict[str, Any]:
        """Get aggregate counts for department dashboard."""
        now = datetime.now(timezone.utc)
        start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

        waiting = self.collection.count_documents({
            "department_id": dept_id,
            "status": "waiting",
        })
        serving = self.collection.count_documents({
            "department_id": dept_id,
            "status": "in_consultation",
        })
        completed_today = self.collection.count_documents({
            "department_id": dept_id,
            "status": "completed",
            "completed_at": {"$gte": start_of_day},
        })

        return {
            "waiting": waiting,
            "in_consultation": serving,
            "completed_today": completed_today,
        }


queue_repository = QueueRepository()
