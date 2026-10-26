import logging
from typing import Any, Optional
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoManager:
    """Manages the MongoDB client connection, database handle, and connectivity lifecycle."""

    def __init__(self, uri: Optional[str] = None, database_name: Optional[str] = None):
        self.uri: Optional[str] = uri
        self.database_name: Optional[str] = database_name
        self.timeout_ms: int = 3000
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def init_app(self, app) -> None:
        """Initialize MongoDB from Flask application config."""
        self.uri = app.config.get("MONGODB_URI", "mongodb://127.0.0.1:27017/")
        self.database_name = app.config.get("MONGODB_DATABASE", "queueless_hospital")
        self.timeout_ms = app.config.get("MONGODB_TIMEOUT_MS", 3000)

        # Attempt initial connection
        self.connect()

    def connect(self) -> bool:
        """Establish connection to MongoDB instance or Atlas cluster."""
        try:
            if self._client is not None:
                self._client.close()

            logger.info("Connecting to MongoDB at %s (database: %s)", self._mask_uri(self.uri or ""), self.database_name)
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=self.timeout_ms,
                connectTimeoutMS=self.timeout_ms,
                retryWrites=True,
            )
            # Verify connectivity with a quick admin ping
            self._client.admin.command("ping")
            self._db = self._client[self.database_name]
            logger.info("Successfully connected to MongoDB database '%s'", self.database_name)
            return True
        except (ServerSelectionTimeoutError, PyMongoError) as err:
            logger.warning("MongoDB connection could not be established immediately: %s", err)
            self._db = None
            return False

    def is_connected(self) -> bool:
        """Check whether MongoDB connection is currently active."""
        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    def ping(self) -> dict[str, Any]:
        """Perform a ping and return status details."""
        try:
            if self._client is None:
                connected = self.connect()
                if not connected:
                    return {"connected": False, "error": "Client not initialized"}
            self._client.admin.command("ping")
            return {"connected": True, "database": self.database_name}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    @property
    def db(self) -> Database:
        """Return database instance. Raises RuntimeError if unavailable."""
        if self._db is None or not self.is_connected():
            reconnected = self.connect()
            if not reconnected or self._db is None:
                raise RuntimeError("Database connection is currently unavailable.")
        return self._db

    def get_collection(self, collection_name: str) -> Collection:
        """Return a specific collection from the active database."""
        return self.db[collection_name]

    def close(self) -> None:
        """Close MongoClient connection."""
        if self._client is not None:
            logger.info("Closing MongoDB connection")
            self._client.close()
            self._client = None
            self._db = None

    @staticmethod
    def _mask_uri(uri: str) -> str:
        """Mask credentials from connection URI for safe logging."""
        if not uri:
            return ""
        if "@" in uri and "://" in uri:
            protocol_part, rest = uri.split("://", 1)
            credentials, host_part = rest.split("@", 1)
            return f"{protocol_part}://***:***@{host_part}"
        return uri


# Global manager instance
mongo_manager = MongoManager()


def to_object_id(id_val: Any) -> ObjectId:
    """
    Safely convert string or ObjectId into ObjectId.
    Raises ValueError with a user-friendly message if invalid.
    """
    if isinstance(id_val, ObjectId):
        return id_val
    if not id_val or not isinstance(id_val, str) or not ObjectId.is_valid(id_val):
        raise ValueError(f"Invalid ObjectId format: {id_val}")
    return ObjectId(id_val)


def serialize_doc(doc: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """
    Recursively serialize MongoDB document for JSON responses:
    - Converts '_id' ObjectId to string 'id'
    - Converts datetime to ISO-formatted strings
    - Converts nested ObjectIds to strings
    """
    if doc is None:
        return None

    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(item) if isinstance(item, dict)
                else str(item) if isinstance(item, ObjectId)
                else item.isoformat() if isinstance(item, datetime)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def serialize_docs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialize a list of MongoDB documents."""
    return [serialize_doc(doc) for doc in docs if doc is not None]
