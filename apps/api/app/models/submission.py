"""SQLAlchemy database model for challenge submissions."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def generate_submission_id() -> str:
    """Generate a prefixed unique submission identifier."""
    return f"sub_{uuid.uuid4().hex[:16]}"


class Submission(Base):
    """Stores candidate challenge submission records and deterministic scores."""

    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_submission_id,
        index=True,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    challenge_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    passed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    execution_time_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )
    rubric_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="correctness-v1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="submissions",
    )
