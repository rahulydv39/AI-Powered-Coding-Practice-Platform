"""Deterministic scoring service for coding challenge submissions.

RUBRIC SPECIFICATION (correctness-v1):
- Measures test correctness only (passed_tests / total_tests * 100).
- Does NOT measure code quality, algorithmic complexity, reasoning, or AI usage.
- Scores are integers from 0 to 100.
- Infrastructure errors (e.g. runner unavailable) are NOT scorable and must not
  be recorded as valid 0-score submissions.
- Code errors (syntax errors, crashes) are scorable with score = 0.
"""

from typing import Optional
from pydantic import BaseModel, Field

from app.services.runner.models import RunResult

RUBRIC_VERSION = "correctness-v1"
SCORE_DISCLAIMER = (
    "Correctness score measures test performance; it does not yet measure reasoning or code quality."
)


def calculate_correctness_score(passed: int, total: int) -> int:
    """Calculate an integer percentage score from 0 to 100.

    Formula: round(passed_tests / total_tests * 100)
    """
    if total <= 0:
        return 0
    calculated = round((passed / total) * 100)
    return max(0, min(100, calculated))


class ScoringOutcome(BaseModel):
    """Result of evaluating a test runner execution for submission scoring."""

    is_scorable: bool = Field(
        ...,
        description="Whether this result represents a valid evaluated attempt vs. infrastructure failure",
    )
    score: Optional[int] = Field(
        default=None,
        description="Integer correctness score from 0 to 100 (None if not scorable)",
    )
    status: str = Field(..., description="Submission status (passed, failed, error, timeout, runner_unavailable)")
    passed: int = Field(default=0, description="Number of passed tests")
    failed: int = Field(default=0, description="Number of failed tests")
    total: int = Field(default=0, description="Total number of evaluated tests")
    execution_time_ms: Optional[float] = Field(
        default=None, description="Execution time in milliseconds"
    )
    rubric_version: str = Field(default=RUBRIC_VERSION, description="Rubric identifier")
    feedback_summary: str = Field(..., description="Human-readable scoring explanation")
    score_disclaimer: str = Field(default=SCORE_DISCLAIMER, description="Scope limitation notice")
    error_message: Optional[str] = Field(default=None, description="Error message if applicable")


def evaluate_submission(run_result: RunResult) -> ScoringOutcome:
    """Evaluate a RunResult and determine scorable status, percentage score, and feedback."""
    # 1. Infrastructure failures: NOT scorable as valid student attempts
    if run_result.status == "runner_unavailable" or not run_result.docker_available:
        return ScoringOutcome(
            is_scorable=False,
            score=None,
            status="runner_unavailable",
            passed=0,
            failed=0,
            total=0,
            execution_time_ms=None,
            rubric_version=RUBRIC_VERSION,
            feedback_summary="Execution sandbox is unavailable. Test evaluation could not be performed.",
            error_message=run_result.error_message or "Docker sandbox is required to evaluate submissions.",
        )

    # 2. Syntax errors or runtime crash during solution loading
    if run_result.status == "error":
        return ScoringOutcome(
            is_scorable=True,
            score=0,
            status="error",
            passed=0,
            failed=run_result.total if run_result.total > 0 else 5,
            total=run_result.total if run_result.total > 0 else 5,
            execution_time_ms=run_result.execution_time_ms,
            rubric_version=RUBRIC_VERSION,
            feedback_summary="Code failed to execute due to a syntax or runtime error. Correctness: 0/100.",
            error_message=run_result.error_message,
        )

    # 3. Timeout failures
    if run_result.status == "timeout":
        return ScoringOutcome(
            is_scorable=True,
            score=0,
            status="timeout",
            passed=0,
            failed=run_result.total if run_result.total > 0 else 5,
            total=run_result.total if run_result.total > 0 else 5,
            execution_time_ms=run_result.execution_time_ms,
            rubric_version=RUBRIC_VERSION,
            feedback_summary="Execution exceeded the time limit (5.0s). Check for infinite loops. Correctness: 0/100.",
            error_message=run_result.error_message,
        )

    # 4. Standard test outcomes (passed or failed)
    total = run_result.total
    passed = run_result.passed
    failed = run_result.failed
    score = calculate_correctness_score(passed, total)

    if score == 100:
        feedback = f"All {total} tests passed! Perfect correctness score (100/100)."
        status_str = "passed"
    elif score == 0:
        feedback = f"0 of {total} tests passed. Correctness score: 0/100."
        status_str = "failed"
    else:
        feedback = f"{passed} of {total} tests passed ({score}%). Correctness score: {score}/100."
        status_str = "failed"

    return ScoringOutcome(
        is_scorable=True,
        score=score,
        status=status_str,
        passed=passed,
        failed=failed,
        total=total,
        execution_time_ms=run_result.execution_time_ms,
        rubric_version=RUBRIC_VERSION,
        feedback_summary=feedback,
        error_message=None,
    )
