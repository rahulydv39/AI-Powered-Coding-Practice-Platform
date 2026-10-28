"""Security and data isolation test suite proving multi-tenant student boundaries.

Proves:
1. User A cannot view User B's submission snapshot (404).
2. User A cannot access User B's solution review (404).
3. User A's progress summary ONLY counts User A's submissions.
4. User B with 0 submissions sees 0 counts and null score aggregates (empty state).
5. Unassigned historical submissions (user_id=None) are never leaked to User A or User B.
6. Unauthenticated requests cannot create formal submissions or view student progress.
"""

from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.submission import Submission
from app.services.challenges.request_deduplication import CHALLENGE_ID, REFERENCE_SOLUTION
from app.services.runner.docker_runner import DockerSandboxRunner
from app.services.runner.models import RunResult

settings = get_settings()


@pytest.fixture
async def clean_async_client() -> AsyncClient:
    """Async test client without default authentication overrides."""
    saved_override = app.dependency_overrides.pop(get_current_user, None)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client
    if saved_override:
        app.dependency_overrides[get_current_user] = saved_override


@pytest.mark.asyncio
async def test_two_user_data_isolation_and_ownership(clean_async_client: AsyncClient) -> None:
    """Prove that User A and User B cannot access each other's submissions, progress, or reviews."""
    ts = datetime.now().timestamp()
    email_a = f"usera_{ts}@example.com"
    email_b = f"userb_{ts}@example.com"
    password = "SecurePassword123!"
    headers = {"X-Gym-CSRF": "1"}

    # 1. Register User A and get session cookie
    resp_a = await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": password, "full_name": "User Alpha"},
        headers=headers,
    )
    assert resp_a.status_code == 201
    user_a_id = resp_a.json()["id"]
    cookie_a = resp_a.cookies.get(settings.SESSION_COOKIE_NAME)
    assert cookie_a is not None

    # 2. Register User B and get session cookie
    resp_b = await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": password, "full_name": "User Beta"},
        headers=headers,
    )
    assert resp_b.status_code == 201
    user_b_id = resp_b.json()["id"]
    cookie_b = resp_b.cookies.get(settings.SESSION_COOKIE_NAME)
    assert cookie_b is not None

    # 3. User B currently has 0 submissions -> verify pristine empty state
    clean_async_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie_b)
    b_summary = await clean_async_client.get("/api/v1/progress/summary")
    assert b_summary.status_code == 200
    b_data = b_summary.json()
    assert b_data["total_submissions"] == 0
    assert b_data["scorable_submissions"] == 0
    assert b_data["distinct_challenges_attempted"] == 0
    assert b_data["best_score"] is None
    assert b_data["average_score"] is None
    assert b_data["most_recent_score"] is None
    assert len(b_data["per_challenge"]) == 0
    assert len(b_data["score_history"]) == 0

    # 4. User A submits a solution (100% score)
    clean_async_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie_a)
    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=88.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        sub_resp = await clean_async_client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
            headers=headers,
        )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    submission_a_id = sub_data["submission_id"]
    assert submission_a_id is not None

    # 5. User A can view their own submission snapshot and history
    a_snap = await clean_async_client.get(f"/api/v1/progress/submissions/{submission_a_id}")
    assert a_snap.status_code == 200
    assert a_snap.json()["id"] == submission_a_id

    a_history = await clean_async_client.get("/api/v1/progress/history")
    assert a_history.status_code == 200
    assert a_history.json()["total"] == 1
    assert a_history.json()["items"][0]["id"] == submission_a_id

    # 5b. User A progress summary reflects 1 solved challenge and 100% success rate
    a_summary = await clean_async_client.get("/api/v1/progress/summary")
    assert a_summary.status_code == 200
    a_data = a_summary.json()
    assert a_data["problems_solved"] == 1
    assert a_data["submission_success_rate"] == 100.0
    assert a_data["challenge_solve_rate"] == 100.0
    assert len(a_data["recent_activity"]) == 1
    assert a_data["recent_activity"][0]["id"] == submission_a_id

    # 6. User A can view their own solution review
    a_review = await clean_async_client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{submission_a_id}/review"
    )
    assert a_review.status_code == 200
    assert a_review.json()["submission_id"] == submission_a_id

    # 7. CRITICAL SECURITY: User B attempts to access User A's submission snapshot -> MUST return 404
    clean_async_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie_b)
    b_access_snapshot = await clean_async_client.get(f"/api/v1/progress/submissions/{submission_a_id}")
    assert b_access_snapshot.status_code == 404

    # 8. CRITICAL SECURITY: User B attempts to review User A's submission -> MUST return 404
    b_access_review = await clean_async_client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{submission_a_id}/review"
    )
    assert b_access_review.status_code == 404

    # 9. User B's progress summary MUST STILL BE ZERO (User A's attempt is completely isolated)
    b_summary_after = await clean_async_client.get("/api/v1/progress/summary")
    assert b_summary_after.status_code == 200
    b_after_data = b_summary_after.json()
    assert b_after_data["total_submissions"] == 0
    assert b_after_data["best_score"] is None
    assert b_after_data["problems_solved"] == 0
    assert b_after_data["submission_success_rate"] is None
    assert b_after_data["challenge_solve_rate"] is None
    assert len(b_after_data["recent_activity"]) == 0

    # 10. User B's history MUST STILL BE EMPTY
    b_history = await clean_async_client.get("/api/v1/progress/history")
    assert b_history.status_code == 200
    assert b_history.json()["total"] == 0
    assert len(b_history.json()["items"]) == 0


@pytest.mark.asyncio
async def test_unauthenticated_requests_blocked(clean_async_client: AsyncClient) -> None:
    """Unauthenticated requests must be rejected from creating submissions or viewing progress."""
    headers = {"X-Gym-CSRF": "1"}

    # Submit without cookie
    sub_resp = await clean_async_client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/submit",
        json={"code": REFERENCE_SOLUTION},
        headers=headers,
    )
    assert sub_resp.status_code == 401

    # Progress summary without cookie
    sum_resp = await clean_async_client.get("/api/v1/progress/summary")
    assert sum_resp.status_code == 401

    # History without cookie
    hist_resp = await clean_async_client.get("/api/v1/progress/history")
    assert hist_resp.status_code == 401

    # Review without cookie
    rev_resp = await clean_async_client.get(f"/api/v1/challenges/{CHALLENGE_ID}/submissions/sub_123/review")
    assert rev_resp.status_code == 401


@pytest.mark.asyncio
async def test_historical_unassigned_submissions_inaccessible(clean_async_client: AsyncClient) -> None:
    """Historical pre-authentication records (user_id=None) are not accessible to ordinary student accounts."""
    ts = datetime.now().timestamp()
    email = f"student_new_{ts}@example.com"
    headers = {"X-Gym-CSRF": "1"}

    # 1. Register student
    reg_resp = await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!"},
        headers=headers,
    )
    cookie = reg_resp.cookies.get(settings.SESSION_COOKIE_NAME)
    clean_async_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)

    # 2. Insert pre-auth submission with user_id = NULL
    unassigned_id = f"sub_unassigned_{int(ts)}"
    async with AsyncSessionLocal() as session:
        unassigned_sub = Submission(
            id=unassigned_id,
            user_id=None,  # Pre-auth record!
            challenge_id=CHALLENGE_ID,
            code="def process_request(): pass",
            score=75,
            passed_count=3,
            failed_count=1,
            total_count=4,
            status="failed",
            created_at=datetime.now(timezone.utc),
        )
        session.add(unassigned_sub)
        await session.commit()

    # 3. New student tries to fetch snapshot of unassigned submission -> 404
    snap_resp = await clean_async_client.get(f"/api/v1/progress/submissions/{unassigned_id}")
    assert snap_resp.status_code == 404

    # 4. New student tries to review unassigned submission -> 404
    review_resp = await clean_async_client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{unassigned_id}/review"
    )
    assert review_resp.status_code == 404

    # 5. New student's summary does not count unassigned submission
    sum_resp = await clean_async_client.get("/api/v1/progress/summary")
    assert sum_resp.json()["total_submissions"] == 0
