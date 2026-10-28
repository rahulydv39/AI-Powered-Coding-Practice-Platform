"""Pytest test configuration and fixtures."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.core.database import engine
from app.main import app
from app.models.user import User

TEST_USER = User(
    id="usr_default_test",
    email="test_student@example.com",
    full_name="Test Student",
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)


@pytest.fixture(autouse=True)
async def cleanup_database_connections() -> None:
    """Dispose pooled connections between tests so new event loops get fresh asyncpg handles."""
    yield
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_default_auth() -> None:
    """Set default authenticated user for existing challenge and scoring test suites."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncClient:
    """Asynchronous HTTPX test client executing inside the active asyncio loop."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
