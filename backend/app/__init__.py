import logging
import sys
from typing import Any, Optional, Type
from flask import Flask
from app.config import Config, get_config
from app.extensions import cors, mongo_manager
from app.database.indexes import ensure_indexes
from app.middleware.error_handler import register_error_handlers
from app.routes import register_blueprints


def configure_logging(app: Flask) -> None:
    """Configure secure, clean application logging."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def create_app(config_class: Optional[Type[Config]] = None) -> Flask:
    """
    Application factory for Queueless Smart Hospital Flask Backend.
    Initializes configuration, database connection, extensions, error handlers, and blueprints.
    """
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Setup logging
    configure_logging(app)
    logger = logging.getLogger(__name__)
    logger.info("Initializing %s in %s mode", app.config.get("APP_NAME"), config_class.__name__)

    # Configure CORS for frontend origin(s)
    frontend_origin_raw = app.config.get("FRONTEND_ORIGIN", "*")
    if not frontend_origin_raw or frontend_origin_raw.strip() == "*":
        allowed_origins: Any = "*"
    elif "," in frontend_origin_raw:
        allowed_origins = [o.strip() for o in frontend_origin_raw.split(",") if o.strip()]
    else:
        allowed_origins = [frontend_origin_raw.strip()]

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # Initialize MongoDB connection manager
    mongo_manager.init_app(app)

    # Initialize database indexes if connected
    if mongo_manager.is_connected():
        try:
            ensure_indexes(mongo_manager.db)
        except Exception as err:
            logger.warning("Could not automatically verify database indexes on startup: %s", err)

    # Register custom error handlers
    register_error_handlers(app)

    # Register modular blueprints with versioned API prefix (/api/v1)
    api_prefix = app.config.get("API_PREFIX", "/api/v1")
    register_blueprints(app, url_prefix=api_prefix)

    # Domain verification assetlinks.json for Android App Links
    @app.route("/.well-known/assetlinks.json", methods=["GET"])
    def assetlinks():
        import json
        from flask import Response
        content = [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": "com.queueless.hospital",
                    "sha256_cert_fingerprints": [
                        "44:8F:05:BC:BE:F7:6B:9C:72:3C:65:FD:4E:A1:3D:3E:2E:17:38:0A:9C:3E:2A:99:CE:05:61:41:2A:48:94:E8"
                    ]
                }
            }
        ]
        return Response(json.dumps(content, indent=2), mimetype="application/json")

    logger.info("Application factory completed successfully.")
    return app
