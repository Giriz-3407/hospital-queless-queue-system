import pytest
from app import create_app
from app.config import TestingConfig
from app.database.connection import mongo_manager
from app.repositories.user_repository import user_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.department_repository import department_repository
from app.utils.security import hash_password, create_access_token


@pytest.fixture(scope="session")
def app():
    """Create test application configured for testing."""
    test_app = create_app(TestingConfig)
    return test_app


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean test collections before each test run if database is connected."""
    if mongo_manager.is_connected():
        try:
            db = mongo_manager.db
            db["users"].delete_many({})
            db["queues"].delete_many({})
            db["departments"].delete_many({})
            db["doctors"].delete_many({})
            db["counters"].delete_many({})
            db["audit_logs"].delete_many({})
        except Exception:
            pass
    yield


@pytest.fixture
def client(app):
    """Flask test client."""
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Helper fixture providing an authenticated patient token."""
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "Password123!",
            "phone": "+1-555-0199",
            "role": "patient",
        },
    )
    data = res.get_json()
    token = data["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_auth_headers(app):
    """Helper fixture providing an authenticated doctor token."""
    with app.app_context():
        user = user_repository.create({
            "name": "Dr. Sarah Smith",
            "email": "dr.smith@hospital.org",
            "password_hash": hash_password("Password123!"),
            "role": "doctor",
            "is_active": True,
        })
        token = create_access_token(
            user_id=str(user["_id"]),
            email=user["email"],
            role="doctor",
            name=user["name"],
        )
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(app):
    """Helper fixture providing an authenticated administrator token."""
    with app.app_context():
        user = user_repository.create({
            "name": "Hospital Admin",
            "email": "admin@hospital.org",
            "password_hash": hash_password("AdminSecurePassword123!"),
            "role": "admin",
            "is_active": True,
        })
        token = create_access_token(
            user_id=str(user["_id"]),
            email=user["email"],
            role="admin",
            name=user["name"],
        )
        return {"Authorization": f"Bearer {token}"}
