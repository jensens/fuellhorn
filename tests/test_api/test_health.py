"""Tests for health check endpoint."""

from nicegui.testing import User
import pytest
from sqlalchemy import create_engine


async def test_health_check_endpoint(user: User) -> None:
    """Test that health check endpoint returns healthy status with correct schema."""
    response = await user.http_client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    # Verify response schema and value
    assert "status" in data
    assert data["status"] == "healthy"


async def test_health_check_reports_unreachable_database(user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ohne erreichbare Datenbank antwortet /api/health mit 503 und 'unhealthy' (Issue #377)."""
    broken_engine = create_engine("sqlite:////nonexistent-dir/for-health-check/fuellhorn.db")
    monkeypatch.setattr("app.database.get_engine", lambda: broken_engine)

    response = await user.http_client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"
