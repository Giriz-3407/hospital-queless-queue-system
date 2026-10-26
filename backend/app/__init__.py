import logging
import sys
from typing import Optional, Type
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

    # Configure CORS for restricted frontend origin
    frontend_origin = app.config.get("FRONTEND_ORIGIN", "http://localhost:5173")
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": [frontend_origin]}},
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

    logger.info("Application factory completed successfully.")
    return app
