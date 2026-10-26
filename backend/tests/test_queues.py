def test_join_and_manage_queue_flow(client, auth_headers):
    """Test full patient queue lifecycle: join, check my queues, and cancel."""
    # 1. Fetch departments to get a valid department_id
    dept_res = client.get("/api/v1/departments")
    depts = dept_res.get_json()["data"]
    dept_id = depts[0]["id"]

    # 2. Join queue
    join_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Persistent migraine"},
        headers=auth_headers,
    )
    assert join_res.status_code == 201
    join_data = join_res.get_json()
    assert join_data["success"] is True
    ticket = join_data["data"]
    ticket_id = ticket["id"]
    assert ticket["status"].upper() == "WAITING"
    assert ticket["position"] >= 1
    assert "ticket_number" in ticket

    # 3. Check /api/v1/queues/my
    my_res = client.get("/api/v1/queues/my", headers=auth_headers)
    assert my_res.status_code == 200
    my_tickets = my_res.get_json()["data"]
    assert len(my_tickets) >= 1
    assert my_tickets[0]["id"] == ticket_id

    # 4. Check specific queue ticket
    t_res = client.get(f"/api/v1/queues/{ticket_id}", headers=auth_headers)
    assert t_res.status_code == 200
    assert t_res.get_json()["data"]["id"] == ticket_id

    # 5. Cancel ticket
    cancel_res = client.post(f"/api/v1/queues/{ticket_id}/cancel", headers=auth_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["data"]["status"].upper() == "CANCELLED"


def test_duplicate_queue_join_prevention(client, auth_headers):
    """Test that a patient cannot join the same department queue multiple times actively."""
    dept_res = client.get("/api/v1/departments")
    dept_id = dept_res.get_json()["data"][0]["id"]

    # First join: success
    res1 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "First visit"},
        headers=auth_headers,
    )
    assert res1.status_code == 201

    # Second join in same department: rejected (400)
    res2 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Second visit duplicate"},
        headers=auth_headers,
    )
    assert res2.status_code == 400
    data = res2.get_json()
    assert data["success"] is False
    assert "already hold an active queue ticket" in data["error"]["message"]


def test_queue_position_and_ahead_calculation(client, auth_headers):
    """Test sequential token numbering and accurate queue positions for multiple patients."""
    dept_res = client.get("/api/v1/departments")
    dept_id = dept_res.get_json()["data"][0]["id"]

    # Register Patient 1 (via auth_headers)
    t1_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Patient 1"},
        headers=auth_headers,
    )
    t1 = t1_res.get_json()["data"]
    assert t1["live_position"] == 1
    assert t1["patients_ahead"] == 0

    # Register Patient 2
    reg2 = client.post(
        "/api/v1/auth/register",
        json={"name": "Patient 2", "email": "p2@example.com", "password": "Password123!"},
    )
    token2 = reg2.get_json()["data"]["token"]
    h2 = {"Authorization": f"Bearer {token2}"}

    t2_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Patient 2"},
        headers=h2,
    )
    t2 = t2_res.get_json()["data"]
    assert t2["live_position"] == 2
    assert t2["patients_ahead"] == 1
    # Check sequential tokens
    assert t1["token_number"] != t2["token_number"]


def test_queue_isolation_between_patients(client, auth_headers):
    """Verify that patient B cannot view or cancel patient A's queue ticket."""
    dept_res = client.get("/api/v1/departments")
    dept_id = dept_res.get_json()["data"][0]["id"]

    join_res = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_id, "reason": "Patient A Checkup"},
        headers=auth_headers,
    )
    ticket_a_id = join_res.get_json()["data"]["id"]

    # Register Patient B
    reg_b = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Patient B",
            "email": "patient.b@example.com",
            "password": "Password123!",
            "role": "patient",
        },
    )
    token_b = reg_b.get_json()["data"]["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Patient B attempts to view Patient A's ticket -> 403 Forbidden
    view_res = client.get(f"/api/v1/queues/{ticket_a_id}", headers=headers_b)
    assert view_res.status_code == 403
    assert "Access denied" in view_res.get_json()["error"]["message"]

    # Patient B attempts to cancel Patient A's ticket -> 403 Forbidden
    cancel_res = client.post(f"/api/v1/queues/{ticket_a_id}/cancel", headers=headers_b)
    assert cancel_res.status_code == 403
    assert "Access denied" in cancel_res.get_json()["error"]["message"]


def test_cross_department_duplicate_queue_join_prevention(client, auth_headers):
    """Enforce hospital-wide rule: a patient cannot join a second queue in ANY department."""
    dept_res = client.get("/api/v1/departments")
    depts = dept_res.get_json()["data"]
    assert len(depts) >= 2, "Test requires at least 2 clinical departments"
    dept_1_id = depts[0]["id"]
    dept_2_id = depts[1]["id"]

    # 1. Join Department 1 -> Success
    res1 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_1_id, "reason": "Dept 1 Consultation"},
        headers=auth_headers,
    )
    assert res1.status_code == 201

    # 2. Attempt to join Department 2 while Dept 1 ticket is active -> Rejected (400)
    res2 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_2_id, "reason": "Dept 2 Consultation"},
        headers=auth_headers,
    )
    assert res2.status_code == 400
    err = res2.get_json()
    assert err["success"] is False
    assert "already hold an active queue ticket" in err["error"]["message"]
    assert "at most one active queue ticket per patient" in err["error"]["message"]


def test_called_and_in_consultation_states_prevent_joining_queue(client, auth_headers):
    """Verify that CALLED and IN_CONSULTATION tickets are considered active and prevent joining."""
    from app.repositories.queue_repository import queue_repository
    from app.models.queue import QueueStatus

    dept_res = client.get("/api/v1/departments")
    depts = dept_res.get_json()["data"]
    dept_1_id = depts[0]["id"]
    dept_2_id = depts[1]["id"]

    # Join queue -> WAITING
    res1 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_1_id},
        headers=auth_headers,
    )
    assert res1.status_code == 201
    ticket_id = res1.get_json()["data"]["id"]

    # Manually transition ticket to CALLED
    queue_repository.collection.update_one(
        {"_id": queue_repository.find_by_id(ticket_id)["_id"]},
        {"$set": {"status": QueueStatus.CALLED}},
    )

    # Attempt to join Dept 2 while CALLED -> Rejected
    res_called = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_2_id},
        headers=auth_headers,
    )
    assert res_called.status_code == 400
    assert "already hold an active queue ticket" in res_called.get_json()["error"]["message"]

    # Transition ticket to IN_CONSULTATION
    queue_repository.collection.update_one(
        {"_id": queue_repository.find_by_id(ticket_id)["_id"]},
        {"$set": {"status": QueueStatus.IN_CONSULTATION}},
    )

    # Attempt to join Dept 2 while IN_CONSULTATION -> Rejected
    res_consult = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_2_id},
        headers=auth_headers,
    )
    assert res_consult.status_code == 400
    assert "already hold an active queue ticket" in res_consult.get_json()["error"]["message"]


def test_queue_joining_permitted_after_terminal_states(client, auth_headers):
    """Verify that after an active ticket is CANCELLED or COMPLETED, patient can join a new queue."""
    from app.repositories.queue_repository import queue_repository
    from app.models.queue import QueueStatus

    dept_res = client.get("/api/v1/departments")
    depts = dept_res.get_json()["data"]
    dept_1_id = depts[0]["id"]
    dept_2_id = depts[1]["id"]

    # 1. Join Dept 1
    res1 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_1_id},
        headers=auth_headers,
    )
    assert res1.status_code == 201
    t1_id = res1.get_json()["data"]["id"]

    # Cancel ticket
    cancel_res = client.post(f"/api/v1/queues/{t1_id}/cancel", headers=auth_headers)
    assert cancel_res.status_code == 200

    # Join Dept 2 -> Success now that previous ticket is CANCELLED
    res2 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_2_id},
        headers=auth_headers,
    )
    assert res2.status_code == 201
    t2_id = res2.get_json()["data"]["id"]

    # Transition Dept 2 ticket to COMPLETED
    queue_repository.collection.update_one(
        {"_id": queue_repository.find_by_id(t2_id)["_id"]},
        {"$set": {"status": QueueStatus.COMPLETED}},
    )

    # Join Dept 1 again -> Success now that previous ticket is COMPLETED
    res3 = client.post(
        "/api/v1/queues/join",
        json={"department_id": dept_1_id},
        headers=auth_headers,
    )
    assert res3.status_code == 201


def test_concurrent_queue_joining_safety(app, client, auth_headers):
    """Test concurrent queue join requests from the same patient to ensure race conditions are safely blocked."""
    import threading
    from app.services.queue_service import queue_service

    dept_res = client.get("/api/v1/departments")
    depts = dept_res.get_json()["data"]
    dept_id = depts[0]["id"]

    # Get authenticated patient ID from token
    me_res = client.get("/api/v1/auth/me", headers=auth_headers)
    patient_id = me_res.get_json()["data"]["id"]
    patient_name = me_res.get_json()["data"]["name"]

    results = []
    barrier = threading.Barrier(4)

    def attempt_join(req_id):
        # Synchronize threads so they all hit join_queue simultaneously
        barrier.wait()
        with app.app_context():
            try:
                ticket = queue_service.join_queue(
                    patient_id=patient_id,
                    patient_name=patient_name,
                    department_id=dept_id,
                    reason=f"Concurrent #{req_id}",
                )
                results.append(("SUCCESS", ticket))
            except ValueError as e:
                results.append(("REJECTED", str(e)))

    threads = [threading.Thread(target=attempt_join, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = [r for r in results if r[0] == "SUCCESS"]
    rejections = [r for r in results if r[0] == "REJECTED"]

    # Exactly one request must succeed, and all 3 concurrent attempts must be rejected
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(rejections) == 3, f"Expected 3 rejections, got {len(rejections)}: {results}"
    for _, msg in rejections:
        assert "already hold an active queue ticket" in msg

