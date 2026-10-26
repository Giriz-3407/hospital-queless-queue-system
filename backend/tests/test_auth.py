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
    assert "password_hash" not in data["data"]["user"]


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
