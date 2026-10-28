"""Automated tests for submission flow and deterministic correctness scoring."""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.services.challenges.request_deduplication import (
    CHALLENGE_ID,
    REFERENCE_SOLUTION,
    STARTER_CODE,
)
from app.services.runner.docker_runner import DockerSandboxRunner
from app.services.runner.models import RunResult, TestItemResult
from app.services.scoring.service import (
    RUBRIC_VERSION,
    SCORE_DISCLAIMER,
    calculate_correctness_score,
    evaluate_submission,
)


# ==============================================================================
# Unit Tests: Deterministic Scoring Formula & Rubric
# ==============================================================================

def test_calculate_correctness_score_formula() -> None:
    """Correctness score must strictly follow round(passed / total * 100)."""
    assert calculate_correctness_score(5, 5) == 100
    assert calculate_correctness_score(4, 5) == 80
    assert calculate_correctness_score(3, 5) == 60
    assert calculate_correctness_score(2, 5) == 40
    assert calculate_correctness_score(1, 5) == 20
    assert calculate_correctness_score(0, 5) == 0

    # Test standard rounding behavior
    assert calculate_correctness_score(1, 3) == 33  # 33.333... -> 33
    assert calculate_correctness_score(2, 3) == 67  # 66.666... -> 67

    # Edge cases
    assert calculate_correctness_score(0, 0) == 0
    assert calculate_correctness_score(-1, 5) == 0
    assert calculate_correctness_score(10, 5) == 100


def test_evaluate_submission_runner_unavailable_not_scorable() -> None:
    """Infrastructure errors must NOT yield scorable submissions or false 0 scores."""
    result = RunResult(
        status="runner_unavailable",
        passed=0,
        failed=0,
        total=0,
        docker_available=False,
        error_message="Docker not found",
    )
    outcome = evaluate_submission(result)

    assert outcome.is_scorable is False
    assert outcome.score is None
    assert outcome.status == "runner_unavailable"
    assert outcome.rubric_version == RUBRIC_VERSION
    assert outcome.score_disclaimer == SCORE_DISCLAIMER
    assert "unavailable" in outcome.feedback_summary.lower()


def test_evaluate_submission_code_error_is_scorable_zero() -> None:
    """Syntax or import errors are valid student attempts graded as 0."""
    result = RunResult(
        status="error",
        passed=0,
        failed=5,
        total=5,
        execution_time_ms=50.0,
        docker_available=True,
        error_message="SyntaxError: invalid syntax",
    )
    outcome = evaluate_submission(result)

    assert outcome.is_scorable is True
    assert outcome.score == 0
    assert outcome.status == "error"
    assert outcome.passed == 0
    assert outcome.failed == 5
    assert outcome.total == 5
    assert outcome.error_message == "SyntaxError: invalid syntax"


def test_evaluate_submission_timeout_is_scorable_zero() -> None:
    """Timeout runs (e.g. infinite loops) are graded as 0."""
    result = RunResult(
        status="timeout",
        passed=0,
        failed=5,
        total=5,
        execution_time_ms=5000.0,
        docker_available=True,
        error_message="Execution timed out",
    )
    outcome = evaluate_submission(result)

    assert outcome.is_scorable is True
    assert outcome.score == 0
    assert outcome.status == "timeout"


def test_evaluate_submission_full_and_partial_pass() -> None:
    """Scoring correctly categorizes full and partial passes."""
    # Full pass
    pass_result = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=120.0,
        docker_available=True,
    )
    pass_outcome = evaluate_submission(pass_result)
    assert pass_outcome.is_scorable is True
    assert pass_outcome.score == 100
    assert pass_outcome.status == "passed"
    assert "100/100" in pass_outcome.feedback_summary

    # Partial pass (3 of 5)
    partial_result = RunResult(
        status="failed",
        passed=3,
        failed=2,
        total=5,
        execution_time_ms=110.0,
        docker_available=True,
    )
    partial_outcome = evaluate_submission(partial_result)
    assert partial_outcome.is_scorable is True
    assert partial_outcome.score == 60
    assert partial_outcome.status == "failed"
    assert "60/100" in partial_outcome.feedback_summary


# ==============================================================================
# Integration Tests: POST /api/v1/challenges/{challenge_id}/submit
# ==============================================================================

def test_submit_rejects_unknown_challenge(client: TestClient) -> None:
    """Submitting to a non-existent challenge ID must return 404."""
    response = client.post(
        "/api/v1/challenges/unknown-challenge-xyz/submit",
        json={"code": "def foo(): pass"},
    )
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"]["message"].lower()


def test_submit_rejects_empty_code(client: TestClient) -> None:
    """Submitting empty or whitespace code must return 422."""
    response = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/submit",
        json={"code": "   "},
    )
    assert response.status_code == 422


def test_submit_rejects_oversized_code(client: TestClient) -> None:
    """Submitting code exceeding 20,000 characters must return 422."""
    giant_code = "x = 1\n" * 4000
    response = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/submit",
        json={"code": giant_code},
    )
    assert response.status_code == 422


def test_submit_runner_unavailable_returns_safe_error(client: TestClient) -> None:
    """When Docker is missing, submission must return 200 with scorable=False and score=None."""
    with patch.object(DockerSandboxRunner, "is_docker_available", return_value=False):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": STARTER_CODE},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "runner_unavailable"
        assert data["score"] is None
        assert data["submission_id"] is None
        assert data["docker_available"] is False
        assert "docker sandbox is unavailable" in data["error_message"].lower()


def test_submit_with_mocked_full_pass(client: TestClient) -> None:
    """Mocked full pass must persist to database, return submission_id, and 100 score."""
    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=135.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["challenge_id"] == CHALLENGE_ID
        assert data["status"] == "passed"
        assert data["score"] == 100
        assert data["passed"] == 5
        assert data["failed"] == 0
        assert data["total"] == 5
        assert data["rubric_version"] == RUBRIC_VERSION
        assert data["score_disclaimer"] == SCORE_DISCLAIMER
        assert data["submission_id"] is not None
        assert data["submission_id"].startswith("sub_")
        assert data["created_at"] is not None


def test_submit_with_mocked_partial_pass(client: TestClient) -> None:
    """Mocked partial pass returns proportional score and records attempt in database."""
    mock_run = RunResult(
        status="failed",
        passed=2,
        failed=3,
        total=5,
        execution_time_ms=115.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": STARTER_CODE},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "failed"
        assert data["score"] == 40  # round(2/5 * 100) = 40
        assert data["passed"] == 2
        assert data["failed"] == 3
        assert data["total"] == 5
        assert data["submission_id"] is not None


def test_submit_response_does_not_leak_hidden_test_harness(client: TestClient) -> None:
    """Authoritative test harness and reference solutions must never leak in submission responses."""
    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=120.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
        )
        assert response.status_code == 200
        body = response.text

        assert "test_results.append" not in body
        assert "t0 = time.time()" not in body
        assert "process_request(request_id: str" not in body


def test_real_docker_sandbox_submission(client: TestClient) -> None:
    """End-to-end submission test running inside real Docker sandbox if available."""
    runner = DockerSandboxRunner()
    if not runner.is_docker_available():
        pytest.skip("Docker is not available on this host.")

    response = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/submit",
        json={"code": REFERENCE_SOLUTION},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["challenge_id"] == CHALLENGE_ID
    assert data["status"] == "passed"
    assert data["score"] == 100
    assert data["passed"] == 5
    assert data["failed"] == 0
    assert data["total"] == 5
    assert data["docker_available"] is True
    assert data["submission_id"] is not None
    assert data["submission_id"].startswith("sub_")
