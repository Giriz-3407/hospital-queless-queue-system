def test_admin_dashboard_stats(client, admin_auth_headers):
    """Test administrator dashboard statistics endpoint."""
    res = client.get("/api/v1/admin/dashboard", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "total_users" in data
    assert "total_patients" in data
    assert "total_doctors" in data
    assert "total_departments" in data
    assert "active_tickets" in data


def test_admin_create_and_manage_doctor(client, admin_auth_headers):
    """Test admin creates a doctor user, assigns department, and updates availability."""
    # 1. Fetch departments
    dept_res = client.get("/api/v1/departments")
    dept_id = dept_res.get_json()["data"][0]["id"]

    # 2. Admin creates doctor
    doc_payload = {
        "name": "Dr. Newly Created",
        "email": "new.doctor@hospital.org",
        "password": "SecurePassword123!",
        "department_id": dept_id,
        "specialty": "General Consultation",
    }
    create_res = client.post("/api/v1/admin/doctors", json=doc_payload, headers=admin_auth_headers)
    assert create_res.status_code == 201
    created_doc = create_res.get_json()["data"]
    assert created_doc["display_name"] == "Dr. Newly Created"
    assert created_doc["is_available"] is True
    doc_id = created_doc["id"]

    # 3. Admin toggles doctor availability to False
    patch_res = client.patch(
        f"/api/v1/admin/doctors/{doc_id}",
        json={"is_available": False},
        headers=admin_auth_headers,
    )
    assert patch_res.status_code == 200
    patched_doc = patch_res.get_json()["data"]
    assert patched_doc["is_available"] is False


def test_admin_create_and_update_department(client, admin_auth_headers):
    """Test admin creates and deactivates a department."""
    create_res = client.post(
        "/api/v1/admin/departments",
        json={
            "name": "Oncology Care",
            "code": "ONCO",
            "description": "Cancer screening and chemotherapy consultation",
            "avg_consultation_time": 30,
            "is_active": True,
        },
        headers=admin_auth_headers,
    )
    assert create_res.status_code == 201
    dept_id = create_res.get_json()["data"]["id"]

    # Deactivate department
    patch_res = client.patch(
        f"/api/v1/admin/departments/{dept_id}",
        json={"is_active": False},
        headers=admin_auth_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.get_json()["data"]["is_active"] is False


def test_admin_audit_logs(client, admin_auth_headers):
    """Test admin can view audit logs created by system events."""
    res = client.get("/api/v1/admin/audit-logs", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "logs" in data
    assert "total" in data
    assert isinstance(data["logs"], list)


def test_admin_queues_overview(client, admin_auth_headers):
    """Test admin queues listing with pagination."""
    res = client.get("/api/v1/admin/queues", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "queues" in data
    assert "total" in data
