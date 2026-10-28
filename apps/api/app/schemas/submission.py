"""Pydantic schemas for challenge submissions and deterministic scoring."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.services.scoring.service import RUBRIC_VERSION, SCORE_DISCLAIMER


class SubmissionRequest(BaseModel):
    """Payload for submitting code for final challenge evaluation."""

    code: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="Source code submitted for evaluation",
    )


class SubmissionResponse(BaseModel):
    """Response returned upon evaluating a submission."""

    submission_id: Optional[str] = Field(
        default=None, description="Unique database submission ID if persisted"
    )
    challenge_id: str = Field(..., description="Challenge identifier")
    status: str = Field(
        ...,
        description="Submission status: 'passed', 'failed', 'error', 'timeout', or 'runner_unavailable'",
    )
    score: Optional[int] = Field(
        default=None,
        description="Integer correctness score from 0 to 100 (None if runner unavailable)",
    )
    passed: int = Field(default=0, description="Number of passed tests")
    failed: int = Field(default=0, description="Number of failed tests")
    total: int = Field(default=0, description="Total number of evaluated tests")
    execution_time_ms: Optional[float] = Field(
        default=None, description="Execution time in milliseconds"
    )
    rubric_version: str = Field(
        default=RUBRIC_VERSION, description="Evaluation rubric version identifier"
    )
    feedback_summary: str = Field(
        ..., description="Deterministic scoring feedback summary"
    )
    score_disclaimer: str = Field(
        default=SCORE_DISCLAIMER, description="Scope limitation disclaimer"
    )
    docker_available: bool = Field(
        ..., description="Whether Docker sandbox was available"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if execution or evaluation failed"
    )
    created_at: Optional[datetime] = Field(
        default=None, description="Timestamp when submission was evaluated"
    )
