"""Pydantic schemas for health and system status endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Minimal health check response model."""

    status: str = Field(default="ok", description="Current service health state")


class ApiV1HealthResponse(BaseModel):
    """Detailed API v1 health and metadata response model."""

    status: str = Field(..., description="Overall service status (healthy or degraded)")
    version: str = Field(..., description="Semantic version of the API service")
    environment: str = Field(..., description="Application execution environment")
    database: Optional[str] = Field(
        default=None,
        description="Database connection status ('connected' or 'disconnected')",
    )
