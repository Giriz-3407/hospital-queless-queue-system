import pytest
from app import create_app
from app.config import TestingConfig
from app.database.connection import mongo_manager


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
            # Reset departments to allow fresh seed or test
            db["departments"].delete_many({})
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
def staff_auth_headers(client):
    """Helper fixture providing an authenticated staff token."""
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Dr. Sarah Smith",
            "email": "dr.smith@hospital.org",
            "password": "Password123!",
            "phone": "+1-555-0100",
            "role": "doctor",
        },
    )
    data = res.get_json()
    token = data["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
