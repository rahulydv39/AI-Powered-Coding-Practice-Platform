"""Pydantic schemas for student progress analytics and submission history."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SubmissionHistoryItem(BaseModel):
    """Historical submission entry."""

    id: str = Field(..., description="Unique submission identifier")
    challenge_id: str = Field(..., description="Challenge identifier")
    challenge_title: str = Field(..., description="Human-readable challenge title")
    created_at: datetime = Field(..., description="Timestamp of submission evaluation (UTC)")
    score: Optional[int] = Field(
        default=None,
        description="Deterministic correctness score (0-100), or None if unscorable",
    )
    passed_count: int = Field(default=0, description="Passed test cases count")
    failed_count: int = Field(default=0, description="Failed test cases count")
    total_count: int = Field(default=0, description="Total evaluated test cases count")
    status: str = Field(..., description="Status: passed, failed, error, timeout, runner_unavailable")
    execution_time_ms: Optional[float] = Field(
        default=None, description="Execution duration in milliseconds"
    )
    rubric_version: str = Field(..., description="Rubric evaluation version")
    is_review_available: bool = Field(
        ..., description="Whether post-submission solution review can be viewed"
    )
    code: Optional[str] = Field(
        default=None, description="Snapshot of Python source code evaluated"
    )


class SubmissionHistoryResponse(BaseModel):
    """Paginated collection of student submission history."""

    items: List[SubmissionHistoryItem] = Field(..., description="List of submission records")
    total: int = Field(..., description="Total count of formal submissions matching filters")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of available pages")
    has_next: bool = Field(..., description="Whether a next page exists")
    has_prev: bool = Field(..., description="Whether a previous page exists")


class ScoreDataPoint(BaseModel):
    """Point on the score progress timeline."""

    submission_id: str = Field(..., description="Submission ID")
    challenge_id: str = Field(..., description="Challenge ID")
    score: int = Field(..., description="Score achieved (0-100)")
    created_at: datetime = Field(..., description="Submission timestamp")


class PerChallengeProgress(BaseModel):
    """Progress metrics aggregated per specific challenge."""

    challenge_id: str = Field(..., description="Challenge identifier")
    challenge_title: str = Field(..., description="Human-readable challenge title")
    total_attempts: int = Field(..., description="Total formal attempts submitted")
    scorable_attempts: int = Field(..., description="Attempts with scorable test execution")
    best_score: Optional[int] = Field(
        default=None, description="Highest score achieved (None if no scorable attempts)"
    )
    latest_score: Optional[int] = Field(
        default=None, description="Score of most recent scorable attempt"
    )
    first_scorable_score: Optional[int] = Field(
        default=None, description="Score of the first scorable attempt"
    )
    score_improvement_delta: Optional[int] = Field(
        default=None,
        description="Latest scorable score minus first scorable score in percentage points",
    )
    is_solved: bool = Field(
        default=False, description="Whether the challenge has at least one 100% scorable submission"
    )
    latest_status: Optional[str] = Field(
        default=None, description="Status of the most recent attempt"
    )
    latest_submitted_at: Optional[datetime] = Field(
        default=None, description="Timestamp of most recent attempt"
    )


class RecentActivityItem(BaseModel):
    """Recent formal submission activity entry."""

    id: str = Field(..., description="Unique submission identifier")
    challenge_id: str = Field(..., description="Challenge identifier")
    challenge_title: str = Field(..., description="Human-readable challenge title")
    created_at: datetime = Field(..., description="Timestamp of submission evaluation (UTC)")
    score: Optional[int] = Field(
        default=None, description="Score achieved (0-100), or None if unscorable"
    )
    status: str = Field(..., description="Execution status")
    passed_count: int = Field(default=0, description="Passed tests")
    total_count: int = Field(default=0, description="Total tests")


class ProgressSummaryResponse(BaseModel):
    """Comprehensive student progress analytics aggregated from real submissions."""

    total_submissions: int = Field(..., description="Total formal submissions recorded")
    scorable_submissions: int = Field(..., description="Number of submissions that were scorable")
    distinct_challenges_attempted: int = Field(
        ..., description="Number of unique challenges attempted"
    )
    problems_solved: int = Field(
        default=0,
        description="Number of distinct challenges with at least one 100% score",
    )
    submission_success_rate: Optional[float] = Field(
        default=None,
        description="Percentage of scorable formal submissions with score == 100",
    )
    challenge_solve_rate: Optional[float] = Field(
        default=None,
        description="Percentage of attempted challenges solved with score == 100",
    )
    best_score: Optional[int] = Field(
        default=None, description="Best deterministic score across all scorable attempts"
    )
    most_recent_score: Optional[int] = Field(
        default=None, description="Score achieved in the most recent scorable attempt"
    )
    average_score: Optional[float] = Field(
        default=None, description="Average correctness score across all scorable attempts"
    )
    total_passed_tests: int = Field(..., description="Cumulative passed test assertions")
    total_failed_tests: int = Field(..., description="Cumulative failed test assertions")
    per_challenge: List[PerChallengeProgress] = Field(
        ..., description="Per-challenge breakdown of attempts and high scores"
    )
    score_history: List[ScoreDataPoint] = Field(
        ..., description="Chronological scored attempts for progress-over-time charting"
    )
    recent_activity: List[RecentActivityItem] = Field(
        default_factory=list, description="Recent formal submission events (newest first, limit 5)"
    )
    data_isolation_notice: str = Field(
        default="All progress analytics, scores, and historical records are strictly isolated to your authenticated account.",
        description="Data isolation guarantee notice",
    )
