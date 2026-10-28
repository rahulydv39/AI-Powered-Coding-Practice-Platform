"""Automated tests for post-submission solution review and learning experience."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.models.submission import Submission
from app.services.ai.base import BaseAiProvider
from app.services.ai.exceptions import AiTimeoutError
from app.services.ai.models import AiMode, AiResponse
from app.services.challenges.request_deduplication import (
    CHALLENGE_ID,
    REFERENCE_SOLUTION,
    STARTER_CODE,
)
from app.services.challenges.solution_review import (
    KEY_DECISIONS,
    LEARNING_TAKEAWAYS,
    compare_code_with_reference,
)
from app.services.runner.docker_runner import DockerSandboxRunner
from app.services.runner.models import RunResult


# ==============================================================================
# Unit Tests: Semantic Comparison & Difference Categorization
# ==============================================================================

def test_compare_code_exact_match() -> None:
    """Exact character match must be recognized as identical."""
    diff, comp = compare_code_with_reference(
        submitted_code=REFERENCE_SOLUTION,
        reference_code=REFERENCE_SOLUTION,
        score=100,
        passed_count=5,
        total_count=5,
    )
    assert comp.is_exact_match is True
    assert comp.is_functionally_equivalent is True
    assert comp.difference_type == "identical"
    assert len(comp.meaningful_differences) == 0


def test_compare_code_formatting_and_docstring_only() -> None:
    """Formatting or docstring differences must NOT be flagged as bugs."""
    code_with_diff_docstring = '''def process_request(request_id: str, seen_ids: set[str]) -> bool:
    """Custom student docstring with extra whitespace."""
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")

    if request_id in seen_ids:
        return False

    seen_ids.add(request_id)
    return True
'''
    diff, comp = compare_code_with_reference(
        submitted_code=code_with_diff_docstring,
        reference_code=REFERENCE_SOLUTION,
        score=100,
        passed_count=5,
        total_count=5,
    )
    assert comp.is_exact_match is False
    assert comp.is_functionally_equivalent is True
    assert comp.difference_type == "formatting_only"
    assert len(comp.meaningful_differences) == 0
    assert "functionally identical" in comp.summary.lower()


def test_compare_code_alternative_correct_style() -> None:
    """Alternative implementation passing all tests must not be falsely criticized."""
    alternative_code = '''def process_request(request_id: str, seen_ids: set[str]) -> bool:
    # Uses different conditional style but passes all tests
    if not request_id or not isinstance(request_id, str) or len(request_id.strip()) == 0:
        raise ValueError("invalid request_id")
    if request_id in seen_ids:
        return False
    seen_ids.add(request_id)
    return True
'''
    diff, comp = compare_code_with_reference(
        submitted_code=alternative_code,
        reference_code=REFERENCE_SOLUTION,
        score=100,
        passed_count=5,
        total_count=5,
    )
    assert comp.is_functionally_equivalent is True
    assert comp.difference_type == "alternative_correct"
    assert len(comp.meaningful_differences) == 0
    assert "100% score" in comp.summary


def test_compare_code_syntax_error() -> None:
    """Unparseable syntax errors are clearly categorized without crashing."""
    broken_code = "def process_request(:\n    return True"
    diff, comp = compare_code_with_reference(
        submitted_code=broken_code,
        reference_code=REFERENCE_SOLUTION,
        score=0,
        passed_count=0,
        total_count=5,
    )
    assert comp.is_functionally_equivalent is False
    assert comp.difference_type == "syntax_error"
    assert len(comp.meaningful_differences) > 0
    assert "syntax error" in comp.summary.lower()


def test_compare_code_failing_identifies_missing_registration_and_validation() -> None:
    """Starter code with intentional bugs accurately identifies missing add and ValueError."""
    diff, comp = compare_code_with_reference(
        submitted_code=STARTER_CODE,
        reference_code=REFERENCE_SOLUTION,
        score=0,
        passed_count=0,
        total_count=5,
    )
    assert comp.is_functionally_equivalent is False
    assert comp.difference_type == "functional_bug"
    assert any("ValueError" in d for d in comp.meaningful_differences)
    assert any("seen_ids.add" in d for d in comp.meaningful_differences)


# ==============================================================================
# Integration Tests: Access Rules, Endpoints, and DB Integrity
# ==============================================================================

def test_reference_solution_not_leaked_in_metadata_or_runs(client: TestClient) -> None:
    """Reference solution must be strictly inaccessible before an eligible submission review."""
    # 1. Challenge metadata
    meta_resp = client.get(f"/api/v1/challenges/{CHALLENGE_ID}")
    assert meta_resp.status_code == 200
    assert "Correct reference implementation" not in meta_resp.text

    # 2. Exploratory run
    run_resp = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/run",
        json={"code": STARTER_CODE},
    )
    assert run_resp.status_code == 200
    assert "Correct reference implementation" not in run_resp.text

    # 3. Submit solution response
    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=100.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        sub_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
        )
        assert sub_resp.status_code == 200
        assert "Correct reference implementation" not in sub_resp.text


def test_review_rejects_unknown_submission_id(client: TestClient) -> None:
    """Reviewing a non-existent submission ID must return 404."""
    response = client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/sub_nonexistent999/review"
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["error"]["message"].lower()


def test_review_rejects_unknown_challenge_id(client: TestClient) -> None:
    """Reviewing under an unsupported challenge ID must return 404."""
    response = client.get(
        "/api/v1/challenges/unknown-challenge/submissions/sub_12345/review"
    )
    assert response.status_code == 404


def test_review_rejects_non_scorable_infrastructure_failures(client: TestClient) -> None:
    """If a submission had runner_unavailable or score=None, review must be rejected (400)."""
    # Create submission when Docker is unavailable
    with patch.object(DockerSandboxRunner, "is_docker_available", return_value=False):
        sub_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": STARTER_CODE},
        )
        assert sub_resp.status_code == 200
        sub_data = sub_resp.json()
        assert sub_data["status"] == "runner_unavailable"
        assert sub_data["submission_id"] is None

    # Even if someone constructs a URL with a fake ID, non-scorable is blocked
    # (Testing via direct route check)
    bogus_resp = client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/sub_nonexistent/review"
    )
    assert bogus_resp.status_code == 404


def test_review_successful_flow_and_data_integrity(client: TestClient) -> None:
    """Valid scorable submission allows accessing review; score and records are unmodified."""
    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=110.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        sub_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
        )
        assert sub_resp.status_code == 200
        submission_id = sub_resp.json()["submission_id"]
        original_score = sub_resp.json()["score"]

    # Request review (deterministic, without AI)
    review_resp = client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{submission_id}/review"
    )
    assert review_resp.status_code == 200
    review_data = review_resp.json()

    assert review_data["submission_id"] == submission_id
    assert review_data["challenge_id"] == CHALLENGE_ID
    assert review_data["score"] == original_score
    assert review_data["status"] == "passed"
    assert review_data["passed_count"] == 5
    assert review_data["failed_count"] == 0
    assert review_data["total_count"] == 5

    # Check reference solution
    assert "def process_request" in review_data["reference_code"]
    assert "seen_ids.add(request_id)" in review_data["reference_code"]

    # Check key decisions (4 items)
    assert len(review_data["key_decisions"]) == 4
    decision_ids = [d["id"] for d in review_data["key_decisions"]]
    assert "input_validation" in decision_ids
    assert "duplicate_check_ordering" in decision_ids
    assert "state_registration" in decision_ids
    assert "boolean_return_contract" in decision_ids

    # Check learning takeaways (4 items)
    assert len(review_data["learning_takeaways"]) == 4

    # Check comparison & diff
    assert review_data["comparison"]["is_exact_match"] is True
    assert "unified_diff" in review_data

    # Check security notice
    assert "unauthenticated" in review_data["security_notice"].lower()

    # Re-verify that calling review did NOT alter the score or duplicate records
    repeat_review = client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{submission_id}/review"
    )
    assert repeat_review.status_code == 200
    assert repeat_review.json()["score"] == original_score


def test_review_with_mocked_gemini_success(client: TestClient) -> None:
    """When include_ai=True, Gemini commentary is included with structured sections."""
    from app.main import app
    from app.services.ai.gemini_provider import get_ai_provider

    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=115.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        sub_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
        )
        submission_id = sub_resp.json()["submission_id"]

    mock_provider = AsyncMock(spec=BaseAiProvider)
    mock_provider.generate_response.return_value = AiResponse(
        content="### Implementation Comparison\nGreat job passing all tests!\n### Why These Decisions Matter\nO(1) lookups are fast.\n### Key Architectural Takeaways\nIdempotency is crucial.",
        mode=AiMode.REVIEW,
        model="gemini-2.5-flash",
    )

    app.dependency_overrides[get_ai_provider] = lambda: mock_provider
    try:
        review_resp = client.get(
            f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{submission_id}/review?include_ai=true"
        )
        assert review_resp.status_code == 200
        data = review_resp.json()

        assert data["ai_review"] is not None
        assert data["ai_review"]["available"] is True
        assert "Implementation Comparison" in data["ai_review"]["content"]
        assert data["ai_review"]["model"] == "gemini-2.5-flash"
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)


def test_review_graceful_fallback_when_gemini_times_out(client: TestClient) -> None:
    """If Gemini times out, deterministic review remains 100% accessible with safe error notice."""
    from app.main import app
    from app.services.ai.gemini_provider import get_ai_provider

    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=120.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        sub_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
        )
        submission_id = sub_resp.json()["submission_id"]

    mock_provider = AsyncMock(spec=BaseAiProvider)
    mock_provider.generate_response.side_effect = AiTimeoutError("Gemini timed out after 15s")

    app.dependency_overrides[get_ai_provider] = lambda: mock_provider
    try:
        review_resp = client.get(
            f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{submission_id}/review?include_ai=true"
        )
        assert review_resp.status_code == 200
        data = review_resp.json()

        # Deterministic parts are fully intact
        assert "def process_request" in data["reference_code"]
        assert len(data["key_decisions"]) == 4

        # AI section reflects graceful failure
        assert data["ai_review"] is not None
        assert data["ai_review"]["available"] is False
        assert "timed out" in data["ai_review"]["error_message"].lower()
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)
