"""Tests for health check endpoint."""

from nicegui.testing import User


async def test_health_check_endpoint(user: User) -> None:
    """Test that health check endpoint returns healthy status with correct schema."""
    response = await user.http_client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    # Verify response schema and value
    assert "status" in data
    assert data["status"] == "healthy"
