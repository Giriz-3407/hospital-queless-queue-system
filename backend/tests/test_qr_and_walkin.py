import pytest
from app.models.queue import QueueStatus
from app.repositories.department_repository import department_repository
from app.repositories.user_repository import user_repository
from app.repositories.doctor_repository import doctor_repository
from app.utils.security import hash_password, create_access_token


@pytest.fixture
def hospital_setup(app):
    """Seed departments and a doctor for QR and walk-in testing."""
    with app.app_context():
        card_dept = department_repository.create({
            "name": "Cardiology",
            "code": "CARD",
            "slug": "cardiology",
            "avg_consultation_time": 20,
            "is_active": True,
        })
        gen_dept = department_repository.create({
            "name": "General Medicine",
            "code": "GEN",
            "slug": "general-medicine",
            "avg_consultation_time": 10,
            "is_active": True,
        })
        ortho_dept = department_repository.create({
            "name": "Orthopedics",
            "code": "ORTHO",
            "slug": "orthopedics",
            "avg_consultation_time": 15,
            "is_active": True,
        })

        doc_user = user_repository.create({
            "name": "Dr. Marcus Vance",
            "email": "dr.vance@hospital.org",
            "password_hash": hash_password("DoctorPass123!"),
            "role": "doctor",
            "is_active": True,
        })

        doc_profile = doctor_repository.create({
            "user_id": doc_user["_id"],
            "department_id": card_dept["_id"],
            "display_name": "Dr. Marcus Vance",
            "specialty": "Cardiology",
            "is_available": True,
        })

        doc_token = create_access_token(
            user_id=str(doc_user["_id"]),
            email=doc_user["email"],
            role="doctor",
            name=doc_user["name"],
        )

        return {
            "card_dept": card_dept,
            "gen_dept": gen_dept,
            "ortho_dept": ortho_dept,
            "doc_headers": {"Authorization": f"Bearer {doc_token}"},
        }


def test_department_slug_and_qr_resolution(client, hospital_setup):
    """Verify department resolution by slug, code, and QR endpoint."""
    # 1. Resolve department by slug
    res = client.get("/api/v1/departments/cardiology")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["slug"] == "cardiology"
    assert data["code"] == "CARD"
    assert "qr_url" in data
    assert "/department/cardiology" in data["qr_url"]

    # 2. Resolve by code
    res_code = client.get("/api/v1/departments/GEN")
    assert res_code.status_code == 200
    data_gen = res_code.get_json()["data"]
    assert data_gen["slug"] == "general-medicine"
    assert "/department/general-medicine" in data_gen["qr_url"]

    # 3. Resolve by orthopedics & British alias orthopaedics
    res_ortho = client.get("/api/v1/departments/orthopaedics")
    assert res_ortho.status_code == 200
    data_ortho = res_ortho.get_json()["data"]
    assert data_ortho["code"] == "ORTHO"

    # 4. Graceful handling of invalid slug
    res_invalid = client.get("/api/v1/departments/non-existent-clinic")
    assert res_invalid.status_code in (400, 404)


def test_qr_config_endpoint(client, hospital_setup):
    """Verify centralized QR configuration endpoint."""
    res = client.get("/api/v1/departments/qr-config")
    assert res.status_code == 200
    json_data = res.get_json()["data"]
    assert "qr_public_base_url" in json_data
    assert "departments" in json_data
    assert len(json_data["departments"]) >= 3

    # Check that each department has a stable slug and encoded QR URL
    for d in json_data["departments"]:
        assert "slug" in d
        assert "qr_url" in d
        assert d["qr_url"].endswith(f"/department/{d['slug']}")
        assert not any(sensitive in d["qr_url"] for sensitive in ["token", "password", "patient", "secret"])

    # Test override parameter for testing/preview
    res_override = client.get("/api/v1/departments/qr-config?base_url=https://queueless.hospital.org")
    assert res_override.status_code == 200
    data_override = res_override.get_json()["data"]
    assert data_override["qr_public_base_url"] == "https://queueless.hospital.org"
    for d in data_override["departments"]:
        assert d["qr_url"].startswith("https://queueless.hospital.org/department/")


def test_assetlinks_endpoint(client):
    """Verify /.well-known/assetlinks.json for Android App Links."""
    res = client.get("/.well-known/assetlinks.json")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    target = data[0]["target"]
    assert target["namespace"] == "android_app"
    assert target["package_name"] == "com.queueless.hospital"
    assert "44:8F:05:BC:BE:F7:6B:9C:72:3C:65:FD:4E:A1:3D:3E:2E:17:38:0A:9C:3E:2A:99:CE:05:61:41:2A:48:94:E8" in target["sha256_cert_fingerprints"]


def test_reception_walk_in_registration_and_doctor_lifecycle(client, admin_auth_headers, hospital_setup):
    """
    Test reception-assisted walk-in patient registration:
    1. Admin/staff registers a walk-in patient with no app account.
    2. Validates atomic sequential token generation.
    3. Verifies entry appears in doctor's waiting queue.
    4. Doctor calls the walk-in patient and starts/completes consultation.
    """
    card_dept_id = str(hospital_setup["card_dept"]["_id"])

    # 1. Register walk-in
    payload = {
        "department_id": card_dept_id,
        "patient_name": "Eleanor Vance (Walk-in)",
        "phone": "+1-555-9876",
        "age": 68,
        "reason": "Chest tightness and palpitations",
    }
    res = client.post(
        "/api/v1/admin/walk-in",
        headers=admin_auth_headers,
        json=payload,
    )
    assert res.status_code == 201
    ticket = res.get_json()["data"]
    assert ticket["token_number"].startswith("CARD-")
    assert ticket["patient_name"] == "Eleanor Vance (Walk-in)"
    assert ticket["status"] == QueueStatus.WAITING
    assert ticket["is_walk_in"] is True
    assert ticket["patient_phone"] == "+1-555-9876"
    assert ticket["patient_age"] == 68

    # 2. Check doctor's queue - walk-in patient MUST appear in doctor's queue
    doc_headers = hospital_setup["doc_headers"]
    res_doc = client.get(
        "/api/v1/doctor/queue",
        headers=doc_headers,
    )
    assert res_doc.status_code == 200
    doc_data = res_doc.get_json()["data"]
    waiting_tokens = [t["token_number"] for t in doc_data["waiting_queue"]]
    assert ticket["token_number"] in waiting_tokens

    # 3. Doctor calls next patient
    res_call = client.post(
        "/api/v1/doctor/queue/next",
        headers=doc_headers,
    )
    assert res_call.status_code == 200
    called = res_call.get_json()["data"]
    assert called["status"] == QueueStatus.CALLED
    assert called["token_number"] == ticket["token_number"]

    # 4. Doctor starts consultation
    res_start = client.post(
        f"/api/v1/doctor/queue/{called['id']}/start",
        headers=doc_headers,
    )
    assert res_start.status_code == 200
    assert res_start.get_json()["data"]["status"] == QueueStatus.IN_CONSULTATION

    # 5. Doctor completes consultation
    res_complete = client.post(
        f"/api/v1/doctor/queue/{called['id']}/complete",
        headers=doc_headers,
        json={"notes": "ECG completed. Normal sinus rhythm. Prescribed medication."},
    )
    assert res_complete.status_code == 200
    assert res_complete.get_json()["data"]["status"] == QueueStatus.COMPLETED


def test_walk_in_duplicate_phone_prevention(client, admin_auth_headers, hospital_setup):
    """Verify that a walk-in cannot be registered with an already active phone number."""
    card_dept_id = str(hospital_setup["card_dept"]["_id"])
    phone = "+1-555-4321"

    # Register first walk-in
    res1 = client.post(
        "/api/v1/admin/walk-in",
        headers=admin_auth_headers,
        json={
            "department_id": card_dept_id,
            "patient_name": "Baby Tommy",
            "phone": phone,
            "age": 2,
        },
    )
    assert res1.status_code == 201

    # Attempt to register second walk-in with same active phone number
    res2 = client.post(
        "/api/v1/admin/walk-in",
        headers=admin_auth_headers,
        json={
            "department_id": card_dept_id,
            "patient_name": "Baby Tommy",
            "phone": phone,
            "age": 2,
        },
    )
    assert res2.status_code in (400, 422)
    err = res2.get_json()["error"]["message"]
    assert "already holds an active queue ticket" in err


def test_walk_in_without_phone_creates_distinct_tickets(client, admin_auth_headers, hospital_setup):
    """Walk-ins without phone number cannot be linked and should not block one another."""
    gen_dept_id = str(hospital_setup["gen_dept"]["_id"])

    res1 = client.post(
        "/api/v1/admin/walk-in",
        headers=admin_auth_headers,
        json={
            "department_id": gen_dept_id,
            "patient_name": "Anonymous John",
        },
    )
    assert res1.status_code == 201

    res2 = client.post(
        "/api/v1/admin/walk-in",
        headers=admin_auth_headers,
        json={
            "department_id": gen_dept_id,
            "patient_name": "Anonymous John",
        },
    )
    assert res2.status_code == 201
    assert res1.get_json()["data"]["token_number"] != res2.get_json()["data"]["token_number"]


def test_walk_in_rbac_permissions(client, auth_headers, hospital_setup):
    """Verify that patients and unauthenticated users cannot register walk-in entries."""
    dept_id = str(hospital_setup["gen_dept"]["_id"])
    payload = {
        "department_id": dept_id,
        "patient_name": "Unauthorized Attempt",
    }

    # 1. Unauthenticated request rejected
    res_anon = client.post("/api/v1/admin/walk-in", json=payload)
    assert res_anon.status_code == 401

    # 2. Patient role rejected
    res_patient = client.post(
        "/api/v1/admin/walk-in",
        headers=auth_headers,
        json=payload,
    )
    assert res_patient.status_code == 403


def test_walk_in_rejects_inactive_department(client, admin_auth_headers, hospital_setup):
    """Verify that walk-ins cannot be registered into inactive departments."""
    dept_id = str(hospital_setup["ortho_dept"]["_id"])

    # Deactivate Orthopedics
    client.patch(
        f"/api/v1/admin/departments/{dept_id}",
        headers=admin_auth_headers,
        json={"is_active": False},
    )

    # Attempt walk-in registration
    res = client.post(
        "/api/v1/admin/walk-in",
        headers=admin_auth_headers,
        json={
            "department_id": dept_id,
            "patient_name": "Skin Check Walk-in",
        },
    )
    assert res.status_code in (400, 422)
    err = res.get_json()["error"]["message"]
    assert "inactive" in err.lower()
