"""Automated tests for challenge endpoints, request validation, and isolated runner."""

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


def test_get_challenge_metadata(client: TestClient) -> None:
    """GET /api/v1/challenges/request-deduplication must return metadata and starter code."""
    response = client.get(f"/api/v1/challenges/{CHALLENGE_ID}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == CHALLENGE_ID
    assert data["title"] == "Request Deduplication"
    assert data["difficulty"] == "Easy"
    assert data["estimated_minutes"] == 15
    assert "process_request" in data["starter_code"]
    assert len(data["test_cases"]) == 5
    assert "sandbox_status" in data
    assert "docker_available" in data["sandbox_status"]


def test_starter_code_does_not_expose_reference_solution(client: TestClient) -> None:
    """The API response must never leak the reference solution or hidden assertions."""
    response = client.get(f"/api/v1/challenges/{CHALLENGE_ID}")
    assert response.status_code == 200
    body_str = response.text

    # Verify reference solution text is not exposed
    assert "Correct reference implementation" not in body_str
    # Verify hidden test runner implementation is not exposed
    assert "test_results.append" not in body_str
    assert "t0 = time.time()" not in body_str


def test_run_rejects_empty_code(client: TestClient) -> None:
    """POST /run with empty code must return 422 Unprocessable Entity."""
    response = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/run",
        json={"code": "   "},
    )
    assert response.status_code == 422


def test_run_rejects_oversized_code(client: TestClient) -> None:
    """POST /run with code exceeding 20,000 characters must return 422."""
    giant_code = "x = 1\n" * 4000  # > 24,000 chars
    response = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/run",
        json={"code": giant_code},
    )
    assert response.status_code == 422


def test_runner_unavailable_when_docker_missing(client: TestClient) -> None:
    """When Docker is unavailable, the runner must refuse host execution and return clear guidance."""
    with patch.object(DockerSandboxRunner, "is_docker_available", return_value=False):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/run",
            json={"code": STARTER_CODE},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "runner_unavailable"
        assert data["docker_available"] is False
        assert "Docker sandbox is unavailable" in data["error_message"]
        assert data["total"] == 0


def test_run_with_mocked_passing_results(client: TestClient) -> None:
    """Endpoint must accurately structure results when all tests pass."""
    mock_run_result = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        tests=[
            TestItemResult(name="First request accepted", passed=True, duration_ms=1.2),
            TestItemResult(name="Duplicate request rejected", passed=True, duration_ms=0.8),
            TestItemResult(name="Independent identifiers", passed=True, duration_ms=0.9),
            TestItemResult(name="Repeated sequence processing", passed=True, duration_ms=1.1),
            TestItemResult(name="Empty and invalid input validation", passed=True, duration_ms=0.7),
        ],
        execution_time_ms=120.5,
        docker_available=True,
    )

    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run_result):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/run",
            json={"code": REFERENCE_SOLUTION},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "passed"
        assert data["passed"] == 5
        assert data["failed"] == 0
        assert data["total"] == 5
        assert len(data["tests"]) == 5
        assert all(t["passed"] for t in data["tests"])


def test_run_with_mocked_failing_results(client: TestClient) -> None:
    """Endpoint must accurately structure results when tests fail with assertion diffs."""
    mock_run_result = RunResult(
        status="failed",
        passed=1,
        failed=4,
        total=5,
        tests=[
            TestItemResult(name="First request accepted", passed=True, duration_ms=1.0),
            TestItemResult(
                name="Duplicate request rejected",
                passed=False,
                message="AssertionError: Duplicate request should return False, got True",
                duration_ms=0.9,
            ),
            TestItemResult(
                name="Independent identifiers",
                passed=False,
                message="AssertionError: Expected second call for 'id-alpha' to return False",
                duration_ms=0.8,
            ),
            TestItemResult(
                name="Repeated sequence processing",
                passed=False,
                message="AssertionError: Sequence processing mismatch",
                duration_ms=1.0,
            ),
            TestItemResult(
                name="Empty and invalid input validation",
                passed=False,
                message="AssertionError: Expected ValueError when request_id is empty string ''",
                duration_ms=0.7,
            ),
        ],
        execution_time_ms=115.0,
        docker_available=True,
    )

    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run_result):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/run",
            json={"code": STARTER_CODE},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "failed"
        assert data["passed"] == 1
        assert data["failed"] == 4
        assert data["total"] == 5
        assert data["tests"][1]["passed"] is False
        assert "AssertionError" in data["tests"][1]["message"]


def test_run_with_mocked_syntax_error(client: TestClient) -> None:
    """Endpoint must return status='error' when student code contains a syntax error."""
    mock_run_result = RunResult(
        status="error",
        passed=0,
        failed=0,
        total=0,
        tests=[],
        execution_time_ms=50.0,
        error_message="SyntaxError in your code: invalid syntax (line 3)",
        docker_available=True,
    )

    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run_result):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/run",
            json={"code": "def broken_syntax(:\n  pass"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "error"
        assert "SyntaxError" in data["error_message"]


def test_run_with_mocked_timeout(client: TestClient) -> None:
    """Endpoint must return status='timeout' when execution exceeds limit."""
    mock_run_result = RunResult(
        status="timeout",
        passed=0,
        failed=0,
        total=0,
        tests=[],
        execution_time_ms=5002.0,
        error_message="Execution timed out (5.0s limit exceeded). Check for infinite loops.",
        docker_available=True,
    )

    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run_result):
        response = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/run",
            json={"code": "while True: pass"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "timeout"
        assert "timed out" in data["error_message"]


@pytest.mark.skipif(
    not DockerSandboxRunner.is_docker_available(),
    reason="Docker daemon is not available on this host. Skipping real container integration test.",
)
def test_real_docker_sandbox_execution() -> None:
    """Real container integration test: runs only when Docker is installed and running."""
    from app.services.challenges.request_deduplication import TEST_HARNESS_CODE

    runner = DockerSandboxRunner()
    result = runner.run_submission(
        student_code=REFERENCE_SOLUTION,
        test_harness_code=TEST_HARNESS_CODE,
    )
    assert result.status == "passed"
    assert result.passed == 5
    assert result.failed == 0


@pytest.mark.skipif(
    not DockerSandboxRunner.is_docker_available(),
    reason="Docker daemon is not available on this host. Skipping real container integration test.",
)
def test_corrected_implementation_passes_all_tests() -> None:
    """Verifies that the user's exact corrected implementation passes all 5 tests."""
    from app.services.challenges.request_deduplication import TEST_HARNESS_CODE

    corrected_code = '''def process_request(request_id: str, seen_ids: set[str]) -> bool:
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")

    if request_id in seen_ids:
        return False

    seen_ids.add(request_id)
    return True
'''
    runner = DockerSandboxRunner()
    result = runner.run_submission(
        student_code=corrected_code,
        test_harness_code=TEST_HARNESS_CODE,
    )
    assert result.status == "passed"
    assert result.passed == 5
    assert result.failed == 0
    assert result.total == 5
    for t in result.tests:
        assert t.passed is True


def test_list_challenges_catalog(client: TestClient) -> None:
    """GET /api/v1/challenges returns public catalog for all registered problems."""
    response = client.get("/api/v1/challenges")
    assert response.status_code == 200
    catalog = response.json()
    assert isinstance(catalog, list)
    assert len(catalog) >= 4

    slugs = [c["id"] for c in catalog]
    assert "request-deduplication" in slugs
    assert "rate-limiter-token-bucket" in slugs
    assert "lru-cache-ttl" in slugs
    assert "circuit-breaker-pattern" in slugs

    for item in catalog:
        assert "id" in item
        assert "title" in item
        assert "difficulty" in item
        assert "category" in item
        assert "tags" in item
        assert "estimated_minutes" in item
        assert "short_summary" in item
        # Security invariant: reference solutions and harnesses must never be in catalog
        assert "reference_solution" not in item
        assert "test_harness_code" not in item


def test_get_all_registered_challenges_metadata(client: TestClient) -> None:
    """GET /api/v1/challenges/{id} returns metadata and test summaries for every problem."""
    expected_challenges = [
        ("request-deduplication", "Easy"),
        ("rate-limiter-token-bucket", "Medium"),
        ("lru-cache-ttl", "Medium"),
        ("circuit-breaker-pattern", "Hard"),
    ]

    for c_id, expected_diff in expected_challenges:
        resp = client.get(f"/api/v1/challenges/{c_id}")
        assert resp.status_code == 200, f"Failed for challenge {c_id}"
        data = resp.json()
        assert data["id"] == c_id
        assert data["difficulty"] == expected_diff
        assert len(data["test_cases"]) == 5
        assert len(data["starter_code"]) > 20
        # Security invariant: never expose reference code or hidden assertions
        assert "reference_solution" not in data
        assert "test_harness_code" not in data


def test_get_unknown_challenge_returns_404(client: TestClient) -> None:
    """GET /api/v1/challenges/{id} with unknown slug returns 404."""
    resp = client.get("/api/v1/challenges/non-existent-challenge-999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["error"]["message"].lower()


def test_practice_endpoints_require_authentication(client: TestClient) -> None:
    """Practice endpoints require an authenticated session and reject anonymous callers with 401."""
    from app.api.deps import get_current_user
    from app.main import app

    # Remove default test authentication override
    saved_override = app.dependency_overrides.pop(get_current_user, None)
    try:
        # Public metadata is accessible without auth
        meta_resp = client.get(f"/api/v1/challenges/{CHALLENGE_ID}")
        assert meta_resp.status_code == 200

        # Exploratory test run requires authentication
        run_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/run",
            json={"code": "def process_request(): pass"},
        )
        assert run_resp.status_code == 401

        # Formal submit requires authentication
        submit_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": "def process_request(): pass"},
        )
        assert submit_resp.status_code == 401

        # AI explain requires authentication
        explain_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/ai/explain",
            json={"code": "def process_request(): pass"},
        )
        assert explain_resp.status_code == 401

        # AI hint requires authentication
        hint_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/ai/hint",
            json={"code": "def process_request(): pass"},
        )
        assert hint_resp.status_code == 401
    finally:
        # Restore auth override for other tests
        if saved_override:
            app.dependency_overrides[get_current_user] = saved_override


@pytest.mark.skipif(
    not DockerSandboxRunner.is_docker_available(),
    reason="Docker daemon is not available on this host. Skipping real container integration test.",
)
def test_all_new_challenges_reference_solutions_pass_tests() -> None:
    """Verifies that the reference solutions for all new challenges pass 100% of their test suites."""
    from app.services.challenges.registry import ChallengeRegistry

    runner = DockerSandboxRunner()
    for challenge_id in ["rate-limiter-token-bucket", "lru-cache-ttl", "circuit-breaker-pattern"]:
        challenge = ChallengeRegistry.get(challenge_id)
        assert challenge is not None

        result = runner.run_submission(
            student_code=challenge.reference_solution,
            test_harness_code=challenge.test_harness_code,
        )
        assert result.status == "passed", f"Challenge {challenge_id} failed: {result.error_message}"
        assert result.passed == 5, f"Challenge {challenge_id} expected 5 passed, got {result.passed}"
        assert result.failed == 0, f"Challenge {challenge_id} had failed tests: {result.tests}"

