def test_health_endpoint_structure(client):
    """Test that health check endpoint returns 200 or 503 with standardized envelope."""
    response = client.get("/api/v1/health")
    data = response.get_json()

    assert response.status_code in (200, 503)
    assert "success" in data
    assert "data" in data
    assert "status" in data["data"]
    assert "database" in data["data"]
    assert "uptime_seconds" in data["data"]
    assert "version" in data["data"]
    # Ensure sensitive fields are never exposed
    assert "uri" not in str(data).lower()
    assert "secret" not in str(data).lower()
