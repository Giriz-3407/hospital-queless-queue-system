def test_get_departments_seeds_and_returns_list(client):
    """Test retrieving active hospital departments."""
    response = client.get("/api/v1/departments")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 5
    first_dept = data["data"][0]
    assert "name" in first_dept
    assert "code" in first_dept
    assert "current_waiting" in first_dept
    assert "estimated_wait_minutes" in first_dept


def test_create_department_unauthorized_for_anonymous(client):
    """Anonymous users cannot create departments."""
    response = client.post(
        "/api/v1/departments",
        json={"name": "Neurology", "code": "NEURO", "avg_consultation_time": 25},
    )
    assert response.status_code == 401


def test_create_department_authorized_for_staff(client, staff_auth_headers):
    """Staff/doctors can create departments."""
    response = client.post(
        "/api/v1/departments",
        json={"name": "Neurology", "code": "NEURO", "avg_consultation_time": 25},
        headers=staff_auth_headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["code"] == "NEURO"
