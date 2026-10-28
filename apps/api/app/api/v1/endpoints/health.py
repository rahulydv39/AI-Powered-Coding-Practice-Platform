"""Health check endpoint for API v1."""

from fastapi import APIRouter, status

from app.core.config import get_settings
from app.core.database import check_database_connection
from app.schemas.health import ApiV1HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get(
    "/health",
    response_model=ApiV1HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="API v1 Health Check",
    description="Returns API status, version, environment, and database availability.",
)
async def get_api_v1_health() -> ApiV1HealthResponse:
    """Return API version, environment, and connectivity status."""
    db_connected = await check_database_connection()
    db_status = "connected" if db_connected else "disconnected"

    return ApiV1HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
    )
