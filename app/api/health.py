"""Health check endpoint for Docker and orchestration systems."""

from nicegui import app
from pydantic import BaseModel
from typing import Literal


class HealthResponse(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "unhealthy"]


@app.get("/api/health")
def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns a simple health status for use by Docker HEALTHCHECK,
    load balancers, and orchestration systems like Kubernetes.

    Returns:
        HealthResponse with status "healthy"
    """
    return HealthResponse(status="healthy")
