import time
from datetime import datetime, timezone
from flask import Blueprint, current_app
from app.database.connection import mongo_manager
from app.utils.response import api_response

health_bp = Blueprint("health", __name__)
START_TIME = time.time()


@health_bp.route("/health", methods=["GET"])
def check_health():
    """
    Health check endpoint reporting service availability and database connectivity.
    Does not expose sensitive credentials, connection strings, or system paths.
    """
    db_status = mongo_manager.ping()
    is_db_connected = db_status.get("connected", False)

    uptime_seconds = int(time.time() - START_TIME)

    status_str = "healthy" if is_db_connected else "degraded"
    status_code = 200 if is_db_connected else 503

    payload = {
        "status": status_str,
        "service": current_app.config.get("APP_NAME", "Queueless Smart Hospital API"),
        "version": current_app.config.get("APP_VERSION", "1.0.0"),
        "uptime_seconds": uptime_seconds,
        "database": {
            "status": "connected" if is_db_connected else "disconnected",
            "name": db_status.get("database", "unknown") if is_db_connected else None,
        },
        "server_time": datetime.now(timezone.utc).isoformat(),
    }

    return api_response(
        data=payload,
        message=f"Service is {status_str}",
        status_code=status_code,
    )
