"""Database engine, session management, and base models for SQLAlchemy 2.x."""

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# SQLAlchemy 2.x Declarative Base for future schema models
class Base(DeclarativeBase):
    """Base class for all future database entity models."""
    pass


# Lazy initialization of async engine to allow the app to boot cleanly without DB
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for FastAPI route handlers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Safe ping to verify database connectivity without throwing unhandled errors."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            return True
    except Exception as exc:
        logger.warning("Database connectivity check failed (PostgreSQL may be offline): %s", exc)
        return False
