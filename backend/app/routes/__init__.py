from flask import Flask
from app.routes.health import health_bp
from app.routes.auth import auth_bp
from app.routes.departments import departments_bp
from app.routes.queues import queues_bp
from app.routes.patients import patients_bp
from app.routes.doctor import doctor_bp
from app.routes.admin import admin_bp


def register_blueprints(app: Flask, url_prefix: str = "/api/v1") -> None:
    """Register all modular route blueprints under the versioned API prefix and root health check."""
    # Register root health check for /health
    root_health_bp = Flask(__name__)  # or register health_bp at root as well:
    app.register_blueprint(health_bp, name="root_health", url_prefix="")
    # Register all versioned blueprints under /api/v1
    app.register_blueprint(health_bp, url_prefix=url_prefix)
    app.register_blueprint(auth_bp, url_prefix=url_prefix)
    app.register_blueprint(departments_bp, url_prefix=url_prefix)
    app.register_blueprint(queues_bp, url_prefix=url_prefix)
    app.register_blueprint(patients_bp, url_prefix=url_prefix)
    app.register_blueprint(doctor_bp, url_prefix=url_prefix)
    app.register_blueprint(admin_bp, url_prefix=url_prefix)
