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
