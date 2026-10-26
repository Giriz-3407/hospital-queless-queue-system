import logging
from typing import Optional, Any
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import ReturnDocument
from app.database.connection import mongo_manager, to_object_id
from app.models.queue import QueueStatus

logger = logging.getLogger(__name__)


class QueueRepository:
    """Data access repository for Queues and Counters collections in MongoDB."""

    @property
    def collection(self):
        return mongo_manager.get_collection("queues")

    @property
    def counters_collection(self):
        return mongo_manager.get_collection("counters")

    def find_by_id(self, queue_id: str | ObjectId) -> Optional[dict[str, Any]]:
        oid = to_object_id(queue_id)
        return self.collection.find_one({"_id": oid})

    def find_active_by_patient(
        self, patient_id: str | ObjectId
    ) -> Optional[dict[str, Any]]:
        """Find an active queue ticket (WAITING, CALLED, IN_CONSULTATION) for a patient across all hospital departments."""
        p_oid = to_object_id(patient_id)
        return self.collection.find_one({
            "patient_id": p_oid,
            "status": {"$in": [
                QueueStatus.WAITING,
                QueueStatus.CALLED,
                QueueStatus.IN_CONSULTATION,
                "waiting",
                "called",
                "in_consultation",
            ]},
        })

    def find_active_by_patient_and_dept(
        self, patient_id: str | ObjectId, dept_id: str | ObjectId
    ) -> Optional[dict[str, Any]]:
        """Find an active queue ticket (WAITING, CALLED, IN_CONSULTATION) for a patient in department."""
        p_oid = to_object_id(patient_id)
        d_oid = to_object_id(dept_id)
        return self.collection.find_one({
            "patient_id": p_oid,
            "department_id": d_oid,
            "status": {"$in": [
                QueueStatus.WAITING,
                QueueStatus.CALLED,
                QueueStatus.IN_CONSULTATION,
                # also match lowercase in case legacy data exists
                "waiting",
                "called",
                "in_consultation",
            ]},
        })

    def find_by_patient_id(
        self, patient_id: str | ObjectId, active_only: bool = False
    ) -> list[dict[str, Any]]:
        """Find tickets for a patient, ordered by creation date."""
        p_oid = to_object_id(patient_id)
        query: dict[str, Any] = {"patient_id": p_oid}
        if active_only:
            query["status"] = {"$in": [
                QueueStatus.WAITING,
                QueueStatus.CALLED,
                QueueStatus.IN_CONSULTATION,
                "waiting",
                "called",
                "in_consultation",
            ]}
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
            norm_status = QueueStatus.normalize(status)
            query["status"] = {"$in": [norm_status, norm_status.lower()]}
        cursor = self.collection.find(query).sort([("joined_at", 1)])
        return list(cursor)

    def find_all(
        self,
        dept_id: Optional[str | ObjectId] = None,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """Find queue tickets for admin monitoring with pagination."""
        query: dict[str, Any] = {}
        if dept_id:
            query["department_id"] = to_object_id(dept_id)
        if status:
            norm_status = QueueStatus.normalize(status)
            query["status"] = {"$in": [norm_status, norm_status.lower()]}
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return list(cursor)

    def count_all(
        self,
        dept_id: Optional[str | ObjectId] = None,
        status: Optional[str] = None,
    ) -> int:
        query: dict[str, Any] = {}
        if dept_id:
            query["department_id"] = to_object_id(dept_id)
        if status:
            norm_status = QueueStatus.normalize(status)
            query["status"] = {"$in": [norm_status, norm_status.lower()]}
        return self.collection.count_documents(query)

    def count_waiting_before(self, dept_id: ObjectId, queue_date: str, joined_at: datetime) -> int:
        """Count patients waiting before a given ticket's joined_at timestamp on the same date."""
        return self.collection.count_documents({
            "department_id": dept_id,
            "queue_date": queue_date,
            "status": {"$in": [QueueStatus.WAITING, "waiting"]},
            "joined_at": {"$lt": joined_at},
        })

    def count_waiting(self, dept_id: ObjectId) -> int:
        """Count total patients currently waiting in this department."""
        return self.collection.count_documents({
            "department_id": dept_id,
            "status": {"$in": [QueueStatus.WAITING, "waiting"]},
        })

    def count_active_total(self) -> int:
        """Total active tickets in hospital (WAITING, CALLED, IN_CONSULTATION)."""
        return self.collection.count_documents({
            "status": {"$in": [
                QueueStatus.WAITING,
                QueueStatus.CALLED,
                QueueStatus.IN_CONSULTATION,
                "waiting",
                "called",
                "in_consultation",
            ]}
        })

    def get_next_ticket_number(self, dept_id: ObjectId | str, dept_code: str, queue_date: str) -> tuple[str, int]:
        """
        Concurrency-safe atomic daily ticket number generator.
        Uses find_one_and_update with $inc on counters collection.
        Returns (token_string, sequence_number), e.g. ("GEN-001", 1).
        """
        counter_key = f"{str(dept_id)}_{queue_date}"
        counter_doc = self.counters_collection.find_one_and_update(
            {"_id": counter_key},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        seq = counter_doc.get("seq", 1)
        token_number = f"{dept_code.upper()}-{seq:03d}"
        return token_number, seq

    def create(self, ticket_dict: dict[str, Any]) -> dict[str, Any]:
        """Insert a new queue ticket."""
        now = datetime.now(timezone.utc)
        ticket_dict.setdefault("created_at", now)
        ticket_dict.setdefault("updated_at", now)
        ticket_dict.setdefault("joined_at", now)
        ticket_dict["status"] = QueueStatus.normalize(ticket_dict.get("status", QueueStatus.WAITING))

        result = self.collection.insert_one(ticket_dict)
        ticket_dict["_id"] = result.inserted_id
        return ticket_dict

    def get_next_waiting_ticket(self, dept_id: ObjectId | str) -> Optional[dict[str, Any]]:
        """Find the next eligible waiting ticket by deterministic FIFO order (joined_at, token_number)."""
        d_oid = to_object_id(dept_id)
        return self.collection.find_one(
            {
                "department_id": d_oid,
                "status": {"$in": [QueueStatus.WAITING, "waiting"]},
            },
            sort=[("joined_at", 1), ("token_number", 1)],
        )

    def atomic_call_next(
        self,
        queue_id: ObjectId | str,
        dept_id: ObjectId | str,
        doctor_id: Optional[ObjectId | str] = None,
        doctor_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Atomically transition ticket from WAITING -> CALLED.
        Guarantees concurrency safety: only succeeds if current status is WAITING.
        """
        q_oid = to_object_id(queue_id)
        d_oid = to_object_id(dept_id)
        now = datetime.now(timezone.utc)

        update_doc: dict[str, Any] = {
            "status": QueueStatus.CALLED,
            "called_at": now,
            "updated_at": now,
        }
        if doctor_id:
            update_doc["doctor_id"] = to_object_id(doctor_id)
        if doctor_name:
            update_doc["doctor_name"] = doctor_name

        return self.collection.find_one_and_update(
            {
                "_id": q_oid,
                "department_id": d_oid,
                "status": {"$in": [QueueStatus.WAITING, "waiting"]},
            },
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
        )

    def atomic_start_consultation(
        self,
        queue_id: ObjectId | str,
        dept_id: ObjectId | str,
        doctor_id: Optional[ObjectId | str] = None,
        doctor_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Atomically transition ticket from CALLED (or WAITING) -> IN_CONSULTATION.
        """
        q_oid = to_object_id(queue_id)
        d_oid = to_object_id(dept_id)
        now = datetime.now(timezone.utc)

        update_doc: dict[str, Any] = {
            "status": QueueStatus.IN_CONSULTATION,
            "consultation_started_at": now,
            "updated_at": now,
        }
        if doctor_id:
            update_doc["doctor_id"] = to_object_id(doctor_id)
        if doctor_name:
            update_doc["doctor_name"] = doctor_name

        return self.collection.find_one_and_update(
            {
                "_id": q_oid,
                "department_id": d_oid,
                "status": {"$in": [QueueStatus.CALLED, "called", QueueStatus.WAITING, "waiting"]},
            },
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
        )

    def atomic_complete_consultation(
        self,
        queue_id: ObjectId | str,
        dept_id: ObjectId | str,
        doctor_id: Optional[ObjectId | str] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Atomically transition ticket from IN_CONSULTATION (or CALLED) -> COMPLETED.
        """
        q_oid = to_object_id(queue_id)
        d_oid = to_object_id(dept_id)
        now = datetime.now(timezone.utc)

        update_doc: dict[str, Any] = {
            "status": QueueStatus.COMPLETED,
            "completed_at": now,
            "updated_at": now,
        }
        if notes is not None:
            update_doc["notes"] = notes
        if doctor_id:
            update_doc["doctor_id"] = to_object_id(doctor_id)

        return self.collection.find_one_and_update(
            {
                "_id": q_oid,
                "department_id": d_oid,
                "status": {"$in": [
                    QueueStatus.IN_CONSULTATION,
                    "in_consultation",
                    QueueStatus.CALLED,
                    "called",
                ]},
            },
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
        )

    def atomic_mark_no_show(
        self,
        queue_id: ObjectId | str,
        dept_id: ObjectId | str,
        doctor_id: Optional[ObjectId | str] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Atomically transition ticket from CALLED or WAITING -> NO_SHOW.
        """
        q_oid = to_object_id(queue_id)
        d_oid = to_object_id(dept_id)
        now = datetime.now(timezone.utc)

        update_doc: dict[str, Any] = {
            "status": QueueStatus.NO_SHOW,
            "completed_at": now,
            "updated_at": now,
        }
        if notes is not None:
            update_doc["notes"] = notes
        if doctor_id:
            update_doc["doctor_id"] = to_object_id(doctor_id)

        return self.collection.find_one_and_update(
            {
                "_id": q_oid,
                "department_id": d_oid,
                "status": {"$in": [
                    QueueStatus.CALLED,
                    "called",
                    QueueStatus.WAITING,
                    "waiting",
                ]},
            },
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
        )

    def atomic_cancel(
        self,
        queue_id: ObjectId | str,
        patient_id: Optional[ObjectId | str] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Atomically transition ticket from WAITING -> CANCELLED.
        """
        q_oid = to_object_id(queue_id)
        now = datetime.now(timezone.utc)

        query: dict[str, Any] = {
            "_id": q_oid,
            "status": {"$in": [QueueStatus.WAITING, "waiting"]},
        }
        if patient_id:
            query["patient_id"] = to_object_id(patient_id)

        update_doc: dict[str, Any] = {
            "status": QueueStatus.CANCELLED,
            "cancelled_at": now,
            "updated_at": now,
        }
        if notes:
            update_doc["notes"] = notes

        return self.collection.find_one_and_update(
            query,
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
        )

    def get_currently_serving(self, dept_id: ObjectId) -> Optional[dict[str, Any]]:
        """Return the ticket currently in consultation for a department."""
        return self.collection.find_one({
            "department_id": dept_id,
            "status": {"$in": [QueueStatus.IN_CONSULTATION, "in_consultation"]},
        })

    def get_currently_called(self, dept_id: ObjectId) -> Optional[dict[str, Any]]:
        """Return the ticket currently called for a department."""
        return self.collection.find_one(
            {
                "department_id": dept_id,
                "status": {"$in": [QueueStatus.CALLED, "called"]},
            },
            sort=[("called_at", -1)],
        )

    def get_department_stats(self, dept_id: ObjectId) -> dict[str, Any]:
        """Get aggregate counts for department dashboard."""
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        waiting = self.collection.count_documents({
            "department_id": dept_id,
            "status": {"$in": [QueueStatus.WAITING, "waiting"]},
        })
        called = self.collection.count_documents({
            "department_id": dept_id,
            "status": {"$in": [QueueStatus.CALLED, "called"]},
        })
        serving = self.collection.count_documents({
            "department_id": dept_id,
            "status": {"$in": [QueueStatus.IN_CONSULTATION, "in_consultation"]},
        })
        completed_today = self.collection.count_documents({
            "department_id": dept_id,
            "queue_date": today_str,
            "status": {"$in": [QueueStatus.COMPLETED, "completed"]},
        })
        no_show_today = self.collection.count_documents({
            "department_id": dept_id,
            "queue_date": today_str,
            "status": {"$in": [QueueStatus.NO_SHOW, "no_show"]},
        })

        return {
            "waiting": waiting,
            "called": called,
            "in_consultation": serving,
            "completed_today": completed_today,
            "no_show_today": no_show_today,
        }


queue_repository = QueueRepository()
