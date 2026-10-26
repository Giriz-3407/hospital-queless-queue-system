from app.utils.security import verify_password, hash_password
from app.repositories.user_repository import user_repository


def test_register_success(client):
    """Test successful user registration."""
    payload = {
        "name": "Alice Patient",
        "email": "alice@example.com",
        "password": "SecurePassword123!",
        "role": "patient",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert data["data"]["user"]["email"] == "alice@example.com"
    assert data["data"]["user"]["role"] == "patient"
    assert "password_hash" not in data["data"]["user"]


def test_register_rejects_admin_role_escalation(client):
    """Test public registration prevents assigning admin role."""
    payload = {
        "name": "Malicious User",
        "email": "hacker@example.com",
        "password": "Password123!",
        "role": "admin",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.get_json()
    assert data["success"] is False
    assert "Public registration is restricted to the 'patient' role" in str(data)


def test_register_rejects_doctor_role_escalation(client):
    """Test public registration prevents assigning doctor role."""
    payload = {
        "name": "Fake Doctor",
        "email": "fake.doctor@example.com",
        "password": "Password123!",
        "role": "doctor",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_password_hashing(client):
    """Verify password is saved only as secure hash and not plaintext."""
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Hashing Test",
            "email": "hashing@example.com",
            "password": "PlaintextPassword123!",
        },
    )
    user = user_repository.find_by_email("hashing@example.com")
    assert user is not None
    assert user["password_hash"] != "PlaintextPassword123!"
    assert verify_password("PlaintextPassword123!", user["password_hash"]) is True
    assert verify_password("WrongPassword!", user["password_hash"]) is False


def test_register_duplicate_email(client):
    """Test registration rejects duplicate email."""
    payload = {
        "name": "Alice Duplicate",
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "already exists" in data["error"]["message"].lower()


def test_login_success(client):
    """Test valid credentials login."""
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob Patient",
            "email": "bob@example.com",
            "password": "Password123!",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert data["data"]["user"]["name"] == "Bob Patient"


def test_login_invalid_password(client):
    """Test login with wrong password."""
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob Wrong",
            "email": "bob.wrong@example.com",
            "password": "Password123!",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bob.wrong@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_get_me_unauthorized(client):
    """Test GET /api/v1/auth/me rejects requests without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_authorized(client, auth_headers):
    """Test GET /api/v1/auth/me returns profile when token is provided."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "jane.doe@example.com"


def test_rbac_patient_forbidden_from_admin_route(client, auth_headers):
    """Test that a patient token is rejected with 403 on admin routes."""
    res = client.get("/api/v1/admin/dashboard", headers=auth_headers)
    assert res.status_code == 403
    data = res.get_json()
    assert data["success"] is False
    assert "Access denied" in data["error"]["message"]
