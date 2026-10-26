import pytest
from app.repositories.department_repository import department_repository
from app.repositories.user_repository import user_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.queue_repository import queue_repository
from app.utils.security import hash_password, create_access_token


@pytest.fixture
def doctor_setup(app):
    """Sets up a department and assigned doctor with authentication headers."""
    with app.app_context():
        # Create Cardiology department
        dept = department_repository.create({
            "name": "Cardiology Test",
            "code": "CARDT",
            "avg_consultation_time": 20,
            "is_active": True,
        })

        # Create Doctor User
        user = user_repository.create({
            "name": "Dr. Test Cardiologist",
            "email": "doc.cardio@hospital.org",
            "password_hash": hash_password("DoctorPass123!"),
            "role": "doctor",
            "is_active": True,
        })

        # Create Doctor Profile
        doc = doctor_repository.create({
            "user_id": user["_id"],
            "department_id": dept["_id"],
            "display_name": "Dr. Test Cardiologist",
            "specialty": "Cardiology",
            "is_available": True,
        })

        token = create_access_token(
            user_id=str(user["_id"]),
            email=user["email"],
            role="doctor",
            name=user["name"],
        )

        return {
            "dept": dept,
            "user": user,
            "doctor": doc,
            "headers": {"Authorization": f"Bearer {token}"},
        }


def test_doctor_queue_lifecycle(client, doctor_setup, auth_headers):
    """Test full doctor workflow: call next -> start consultation -> complete consultation."""
    dept_id = str(doctor_setup["dept"]["_id"])
    doc_headers = doctor_setup["headers"]

    # 1. Patient joins Cardiology queue
    join_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Heart palpitations"},
        headers=auth_headers,
    )
    assert join_res.status_code == 201
    ticket_id = join_res.get_json()["data"]["id"]

    # 2. Doctor views their queue
    q_res = client.get("/api/v1/doctor/queue", headers=doc_headers)
    assert q_res.status_code == 200
    q_data = q_res.get_json()["data"]
    assert len(q_data["waiting_queue"]) == 1
    assert q_data["waiting_queue"][0]["id"] == ticket_id
    assert q_data["stats"]["waiting"] == 1

    # 3. Doctor calls the next patient: WAITING -> CALLED
    next_res = client.post("/api/v1/doctor/queue/next", headers=doc_headers)
    assert next_res.status_code == 200
    called = next_res.get_json()["data"]
    assert called["id"] == ticket_id
    assert called["status"] == "CALLED"
    assert called["called_at"] is not None

    # Verify queue status updated
    q_res2 = client.get("/api/v1/doctor/queue", headers=doc_headers)
    q_data2 = q_res2.get_json()["data"]
    assert q_data2["currently_called"]["id"] == ticket_id
    assert len(q_data2["waiting_queue"]) == 0

    # 4. Doctor starts consultation: CALLED -> IN_CONSULTATION
    start_res = client.post(f"/api/v1/doctor/queue/{ticket_id}/start", headers=doc_headers)
    assert start_res.status_code == 200
    started = start_res.get_json()["data"]
    assert started["status"] == "IN_CONSULTATION"
    assert started["consultation_started_at"] is not None

    # 5. Doctor completes consultation: IN_CONSULTATION -> COMPLETED
    complete_res = client.post(
        f"/api/v1/doctor/queue/{ticket_id}/complete",
        json={"notes": "Normal sinus rhythm, advised hydration."},
        headers=doc_headers,
    )
    assert complete_res.status_code == 200
    completed = complete_res.get_json()["data"]
    assert completed["status"] == "COMPLETED"
    assert completed["completed_at"] is not None


def test_doctor_mark_no_show(client, doctor_setup, auth_headers):
    """Test doctor calling a patient and marking as NO_SHOW."""
    dept_id = str(doctor_setup["dept"]["_id"])
    doc_headers = doctor_setup["headers"]

    # Patient joins
    join_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Blood pressure check"},
        headers=auth_headers,
    )
    ticket_id = join_res.get_json()["data"]["id"]

    # Call patient
    client.post("/api/v1/doctor/queue/next", headers=doc_headers)

    # Mark as NO_SHOW
    no_show_res = client.post(
        f"/api/v1/doctor/queue/{ticket_id}/no-show",
        json={"notes": "Patient did not respond after 3 calls."},
        headers=doc_headers,
    )
    assert no_show_res.status_code == 200
    no_show_data = no_show_res.get_json()["data"]
    assert no_show_data["status"] == "NO_SHOW"


def test_invalid_state_transitions(client, doctor_setup, auth_headers):
    """Test that invalid status transitions (e.g., completing already completed) are rejected."""
    dept_id = str(doctor_setup["dept"]["_id"])
    doc_headers = doctor_setup["headers"]

    join_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Check"},
        headers=auth_headers,
    )
    ticket_id = join_res.get_json()["data"]["id"]

    # Directly completing without calling -> Rejected (400)
    complete_res = client.post(f"/api/v1/doctor/queue/{ticket_id}/complete", headers=doc_headers)
    assert complete_res.status_code == 400


def test_unauthorized_doctor_access_across_departments(app, client, doctor_setup, auth_headers):
    """Verify that a doctor cannot call or modify tickets from an unrelated department."""
    with app.app_context():
        # Create second department
        other_dept = department_repository.create({
            "name": "Orthopedics Unrelated",
            "code": "ORTHOU",
            "is_active": True,
        })
        other_dept_id = str(other_dept["_id"])

    # Patient joins Orthopedics
    join_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": other_dept_id, "reason": "Sprained ankle"},
        headers=auth_headers,
    )
    ortho_ticket_id = join_res.get_json()["data"]["id"]

    # Cardiologist doctor tries to operate on Orthopedics ticket -> 403 Forbidden
    doc_headers = doctor_setup["headers"]
    start_res = client.post(f"/api/v1/doctor/queue/{ortho_ticket_id}/start", headers=doc_headers)
    assert start_res.status_code == 403
    assert "Access denied" in start_res.get_json()["error"]["message"]
