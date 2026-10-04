"""Health check endpoint for Docker and orchestration systems."""

from fastapi import Response
from nicegui import app
from pydantic import BaseModel
from sqlalchemy import text
from typing import Literal


class HealthResponse(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "unhealthy"]


@app.get("/api/health", responses={503: {"model": HealthResponse}})
def health_check(response: Response) -> HealthResponse:
    """Health check endpoint.

    Used by Docker HEALTHCHECK, load balancers and Kubernetes probes. Prüft mit
    ``SELECT 1``, dass die Datenbank erreichbar ist; vorher antwortete der
    Endpoint auch ohne Datenbank mit "healthy" (Issue #377).

    Returns:
        HealthResponse mit "healthy" (200) oder "unhealthy" (503)
    """
    from app.database import get_engine

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return HealthResponse(status="unhealthy")
    return HealthResponse(status="healthy")
