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
    assert ticket["status"] == "waiting"
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
    assert cancel_res.get_json()["data"]["status"] == "cancelled"


def test_queue_isolation_between_patients(client, auth_headers):
    """Verify that patient B cannot view or cancel patient A's queue ticket."""
    # Patient A creates a ticket
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
