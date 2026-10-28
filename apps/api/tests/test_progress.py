"""Comprehensive test suite for student progress analytics and submission history."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db_session
from app.main import app
from app.models.submission import Submission
from app.services.challenges.request_deduplication import CHALLENGE_ID, STARTER_CODE
from app.services.progress.service import (
    get_progress_summary,
    get_submission_history,
    get_submission_snapshot,
)
from app.services.runner.docker_runner import DockerSandboxRunner
from app.services.runner.models import RunResult


@pytest.fixture
async def in_memory_db() -> AsyncSession:
    """Create a completely clean, isolated in-memory database for progress tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


USER_ID = "usr_test_student"


# ==============================================================================
# Unit Tests: Progress Calculation Semantics
# ==============================================================================

async def test_progress_empty_database(in_memory_db: AsyncSession) -> None:
    """Empty database must safely yield nulls/zeros without ZeroDivisionError."""
    summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert summary.total_submissions == 0
    assert summary.scorable_submissions == 0
    assert summary.distinct_challenges_attempted == 0
    assert summary.best_score is None
    assert summary.most_recent_score is None
    assert summary.average_score is None
    assert summary.total_passed_tests == 0
    assert summary.total_failed_tests == 0
    assert len(summary.per_challenge) == 0
    assert len(summary.score_history) == 0

    history = await get_submission_history(in_memory_db, user_id=USER_ID)
    assert history.total == 0
    assert len(history.items) == 0
    assert history.total_pages == 1
    assert history.has_next is False
    assert history.has_prev is False


async def test_progress_single_submission(in_memory_db: AsyncSession) -> None:
    """Single submission correctly populates all summary statistics."""
    sub = Submission(
        id="sub_test1",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="def process_request(): pass",
        score=80,
        passed_count=4,
        failed_count=1,
        total_count=5,
        execution_time_ms=105.0,
        status="failed",
        created_at=datetime.now(timezone.utc),
    )
    in_memory_db.add(sub)
    await in_memory_db.commit()

    summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert summary.total_submissions == 1
    assert summary.scorable_submissions == 1
    assert summary.distinct_challenges_attempted == 1
    assert summary.best_score == 80
    assert summary.most_recent_score == 80
    assert summary.average_score == 80.0
    assert summary.total_passed_tests == 4
    assert summary.total_failed_tests == 1
    assert len(summary.per_challenge) == 1
    assert summary.per_challenge[0].best_score == 80
    assert summary.per_challenge[0].total_attempts == 1


async def test_progress_multiple_attempts_same_challenge(in_memory_db: AsyncSession) -> None:
    """Multiple attempts on same challenge correctly reflect best, latest, and average scores."""
    now = datetime.now(timezone.utc)

    # Attempt 1 (older, score 20)
    sub1 = Submission(
        id="sub_attempt1",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="code1",
        score=20,
        passed_count=1,
        failed_count=4,
        total_count=5,
        status="failed",
        created_at=now - timedelta(minutes=10),
    )
    # Attempt 2 (middle, best score 100)
    sub2 = Submission(
        id="sub_attempt2",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="code2",
        score=100,
        passed_count=5,
        failed_count=0,
        total_count=5,
        status="passed",
        created_at=now - timedelta(minutes=5),
    )
    # Attempt 3 (latest, score 60)
    sub3 = Submission(
        id="sub_attempt3",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="code3",
        score=60,
        passed_count=3,
        failed_count=2,
        total_count=5,
        status="failed",
        created_at=now,
    )
    in_memory_db.add_all([sub1, sub2, sub3])
    await in_memory_db.commit()

    summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert summary.total_submissions == 3
    assert summary.scorable_submissions == 3
    assert summary.distinct_challenges_attempted == 1
    assert summary.best_score == 100
    assert summary.most_recent_score == 60  # newest attempt
    # Average: (20 + 100 + 60) / 3 = 180 / 3 = 60.0
    assert summary.average_score == 60.0
    assert summary.total_passed_tests == 9
    assert summary.total_failed_tests == 6

    per_c = summary.per_challenge[0]
    assert per_c.total_attempts == 3
    assert per_c.best_score == 100
    assert per_c.latest_score == 60


async def test_progress_multiple_challenges(in_memory_db: AsyncSession) -> None:
    """Multiple challenges correctly track distinct challenges and per-challenge metrics."""
    now = datetime.now(timezone.utc)
    sub_c1 = Submission(
        id="sub_c1",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="code_a",
        score=100,
        passed_count=5,
        failed_count=0,
        total_count=5,
        status="passed",
        created_at=now - timedelta(minutes=5),
    )
    sub_c2 = Submission(
        id="sub_c2",
        user_id=USER_ID,
        challenge_id="rate-limiter-token-bucket",
        code="code_b",
        score=50,
        passed_count=3,
        failed_count=3,
        total_count=6,
        status="failed",
        created_at=now,
    )
    in_memory_db.add_all([sub_c1, sub_c2])
    await in_memory_db.commit()

    summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert summary.total_submissions == 2
    assert summary.distinct_challenges_attempted == 2
    assert summary.best_score == 100
    assert summary.most_recent_score == 50
    assert summary.average_score == 75.0
    assert len(summary.per_challenge) == 2

    c_ids = [c.challenge_id for c in summary.per_challenge]
    assert "rate-limiter-token-bucket" in c_ids
    assert "request-deduplication" in c_ids


async def test_unscorable_submissions_excluded_from_score_aggregates(
    in_memory_db: AsyncSession,
) -> None:
    """Unscorable attempts (score is None / runner unavailable) MUST NOT skew averages or be treated as zero."""
    now = datetime.now(timezone.utc)

    # Scorable submission: 100%
    sub_scorable = Submission(
        id="sub_valid",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="def process_request(): return True",
        score=100,
        passed_count=5,
        failed_count=0,
        total_count=5,
        status="passed",
        created_at=now - timedelta(minutes=10),
    )
    # Unscorable submission (runner unavailable, score=None)
    sub_unscorable = Submission(
        id="sub_unscorable",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="def process_request(): return True",
        score=None,  # Missing score!
        passed_count=0,
        failed_count=0,
        total_count=0,
        status="runner_unavailable",
        created_at=now,  # newest!
    )
    in_memory_db.add_all([sub_scorable, sub_unscorable])
    await in_memory_db.commit()

    summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    # Total submissions includes unscorable attempt
    assert summary.total_submissions == 2
    assert summary.scorable_submissions == 1

    # Score aggregates MUST exclude the unscorable attempt
    assert summary.best_score == 100
    # Latest scorable score remains 100, NOT None and NOT 0!
    assert summary.most_recent_score == 100
    # Average is 100.0, NOT 50.0!
    assert summary.average_score == 100.0

    # Submission history shows both attempts
    history = await get_submission_history(in_memory_db, user_id=USER_ID)
    assert history.total == 2
    assert history.items[0].id == "sub_unscorable"
    assert history.items[0].score is None
    assert history.items[0].status == "runner_unavailable"
    assert history.items[0].is_review_available is False

    assert history.items[1].id == "sub_valid"
    assert history.items[1].score == 100
    assert history.items[1].is_review_available is True


async def test_pagination_and_stable_ordering(in_memory_db: AsyncSession) -> None:
    """History pagination orders newest first with deterministic tie-breaking by ID."""
    now = datetime.now(timezone.utc)
    submissions = []
    # Create 25 submissions, some with exact same timestamp
    for i in range(25):
        submissions.append(
            Submission(
                id=f"sub_{i:03d}",
                user_id=USER_ID,
                challenge_id="request-deduplication",
                code=f"code_{i}",
                score=i * 4,
                passed_count=1,
                failed_count=1,
                total_count=2,
                status="failed",
                # Even i get same timestamp, odd i get distinct timestamp
                created_at=now if i % 2 == 0 else now - timedelta(seconds=i),
            )
        )
    in_memory_db.add_all(submissions)
    await in_memory_db.commit()

    # Page 1 (size 10)
    page1 = await get_submission_history(in_memory_db, user_id=USER_ID, page=1, page_size=10)
    assert page1.total == 25
    assert len(page1.items) == 10
    assert page1.page == 1
    assert page1.total_pages == 3
    assert page1.has_next is True
    assert page1.has_prev is False

    # Page 2 (size 10)
    page2 = await get_submission_history(in_memory_db, user_id=USER_ID, page=2, page_size=10)
    assert len(page2.items) == 10
    assert page2.page == 2
    assert page2.has_next is True
    assert page2.has_prev is True

    # Page 3 (size 10, remaining 5)
    page3 = await get_submission_history(in_memory_db, user_id=USER_ID, page=3, page_size=10)
    assert len(page3.items) == 5
    assert page3.page == 3
    assert page3.has_next is False
    assert page3.has_prev is True

    # Verify no duplicate IDs across pages
    all_ids = [item.id for item in page1.items + page2.items + page3.items]
    assert len(all_ids) == len(set(all_ids)) == 25


async def test_snapshot_retrieval(in_memory_db: AsyncSession) -> None:
    """Code snapshot is accurately preserved for historical inspection."""
    test_code = "def process_request(request_id, seen_ids):\n    return True"
    sub = Submission(
        id="sub_snap_123",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code=test_code,
        score=100,
        passed_count=5,
        failed_count=0,
        total_count=5,
        status="passed",
        created_at=datetime.now(timezone.utc),
    )
    in_memory_db.add(sub)
    await in_memory_db.commit()

    snapshot = await get_submission_snapshot(in_memory_db, "sub_snap_123", user_id=USER_ID)
    assert snapshot is not None
    assert snapshot.code == test_code
    assert snapshot.score == 100

    non_existent = await get_submission_snapshot(in_memory_db, "sub_nonexistent", user_id=USER_ID)
    assert non_existent is None


# ==============================================================================
# Integration Tests: HTTP Endpoints & Exploratory Separation
# ==============================================================================

def test_exploratory_runs_do_not_create_submission_history(client: TestClient) -> None:
    """Exploratory test runs ('Run Tests') must NEVER be persisted in submission history."""
    # 1. Get initial total submissions from progress API
    resp_before = client.get("/api/v1/progress/summary")
    assert resp_before.status_code == 200
    initial_total = resp_before.json()["total_submissions"]

    # 2. Perform exploratory test run
    run_resp = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/run",
        json={"code": STARTER_CODE},
    )
    assert run_resp.status_code == 200

    # 3. Verify total submissions did NOT increase
    resp_after = client.get("/api/v1/progress/summary")
    assert resp_after.status_code == 200
    assert resp_after.json()["total_submissions"] == initial_total


def test_api_progress_summary_endpoint(client: TestClient) -> None:
    """GET /api/v1/progress/summary returns properly typed analytics."""
    response = client.get("/api/v1/progress/summary")
    assert response.status_code == 200
    data = response.json()

    assert "total_submissions" in data
    assert "scorable_submissions" in data
    assert "distinct_challenges_attempted" in data
    assert "best_score" in data
    assert "most_recent_score" in data
    assert "average_score" in data
    assert "per_challenge" in data
    assert "score_history" in data
    assert "data_isolation_notice" in data
    assert "isolated" in data["data_isolation_notice"].lower()


def test_api_submission_history_pagination(client: TestClient) -> None:
    """GET /api/v1/progress/history supports pagination and returns structured records."""
    response = client.get("/api/v1/progress/history?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert "has_next" in data
    assert "has_prev" in data

    if data["items"]:
        first = data["items"][0]
        assert "id" in first
        assert "challenge_id" in first
        assert "challenge_title" in first
        assert "created_at" in first
        assert "score" in first
        assert "status" in first
        assert "is_review_available" in first


# ==============================================================================
# Unit Tests: Phase 6.2 Refinements (Solved, Rates, Deltas, Activity)
# ==============================================================================

async def test_progress_metrics_solved_and_rates(in_memory_db: AsyncSession) -> None:
    """Validate problems_solved, success rates, score deltas, and zero denominators."""
    now = datetime.now(timezone.utc)

    # 1. Empty state: rates must be None, solved must be 0
    empty_summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert empty_summary.problems_solved == 0
    assert empty_summary.submission_success_rate is None
    assert empty_summary.challenge_solve_rate is None
    assert len(empty_summary.recent_activity) == 0

    # 2. First attempt: score 40% (failed, not solved)
    sub1 = Submission(
        id="sub_p1",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="attempt1",
        score=40,
        passed_count=2,
        failed_count=3,
        total_count=5,
        status="failed",
        created_at=now - timedelta(minutes=20),
    )
    in_memory_db.add(sub1)
    await in_memory_db.commit()

    s1 = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert s1.problems_solved == 0
    assert s1.submission_success_rate == 0.0
    assert s1.challenge_solve_rate == 0.0
    assert len(s1.per_challenge) == 1
    assert s1.per_challenge[0].is_solved is False
    assert s1.per_challenge[0].first_scorable_score == 40
    assert s1.per_challenge[0].latest_score == 40
    assert s1.per_challenge[0].score_improvement_delta == 0

    # 3. Second attempt: score 100% (solved)
    sub2 = Submission(
        id="sub_p2",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="attempt2",
        score=100,
        passed_count=5,
        failed_count=0,
        total_count=5,
        status="passed",
        created_at=now - timedelta(minutes=10),
    )
    in_memory_db.add(sub2)
    await in_memory_db.commit()

    s2 = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert s2.problems_solved == 1
    # 1 perfect out of 2 scorable = 50.0%
    assert s2.submission_success_rate == 50.0
    # 1 solved out of 1 distinct attempted = 100.0%
    assert s2.challenge_solve_rate == 100.0
    assert s2.per_challenge[0].is_solved is True
    assert s2.per_challenge[0].first_scorable_score == 40
    assert s2.per_challenge[0].latest_score == 100
    # 100 - 40 = 60 percentage points improvement
    assert s2.per_challenge[0].score_improvement_delta == 60

    # 4. Third attempt: unscorable infrastructure failure (runner_unavailable, score=None)
    sub3 = Submission(
        id="sub_p3",
        user_id=USER_ID,
        challenge_id="request-deduplication",
        code="attempt3",
        score=None,
        passed_count=0,
        failed_count=0,
        total_count=0,
        status="runner_unavailable",
        created_at=now,
    )
    in_memory_db.add(sub3)
    await in_memory_db.commit()

    s3 = await get_progress_summary(in_memory_db, user_id=USER_ID)
    # Total submissions is 3, but scorable is still 2
    assert s3.total_submissions == 3
    assert s3.scorable_submissions == 2
    # Unscorable attempt MUST NOT reduce submission_success_rate!
    assert s3.submission_success_rate == 50.0
    assert s3.challenge_solve_rate == 100.0
    # Latest scorable score remains 100
    assert s3.most_recent_score == 100
    assert s3.per_challenge[0].latest_score == 100
    assert s3.per_challenge[0].score_improvement_delta == 60


async def test_recent_activity_ordering_and_content(in_memory_db: AsyncSession) -> None:
    """Recent activity lists newest 5 formal attempts with accurate metadata."""
    now = datetime.now(timezone.utc)
    for i in range(7):
        in_memory_db.add(
            Submission(
                id=f"sub_rec_{i}",
                user_id=USER_ID,
                challenge_id="request-deduplication",
                code=f"code_{i}",
                score=i * 10,
                passed_count=i,
                failed_count=5 - i if i <= 5 else 0,
                total_count=5,
                status="passed" if i * 10 == 100 else "failed",
                created_at=now + timedelta(minutes=i),
            )
        )
    await in_memory_db.commit()

    summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    assert len(summary.recent_activity) == 5
    # Newest item must be sub_rec_6
    assert summary.recent_activity[0].id == "sub_rec_6"
    assert summary.recent_activity[0].score == 60
    assert summary.recent_activity[4].id == "sub_rec_2"
    assert summary.recent_activity[4].score == 20


async def test_submission_history_filter_by_challenge_id(in_memory_db: AsyncSession) -> None:
    """History query filters by challenge_id accurately without cross-contamination."""
    now = datetime.now(timezone.utc)
    in_memory_db.add_all([
        Submission(
            id="sub_h1",
            user_id=USER_ID,
            challenge_id="request-deduplication",
            code="code1",
            score=100,
            status="passed",
            created_at=now - timedelta(minutes=2),
        ),
        Submission(
            id="sub_h2",
            user_id=USER_ID,
            challenge_id="other-challenge",
            code="code2",
            score=50,
            status="failed",
            created_at=now - timedelta(minutes=1),
        ),
    ])
    await in_memory_db.commit()

    res_all = await get_submission_history(in_memory_db, user_id=USER_ID)
    assert res_all.total == 2

    res_filtered = await get_submission_history(
        in_memory_db, user_id=USER_ID, challenge_id="request-deduplication"
    )
    assert res_filtered.total == 1
    assert res_filtered.items[0].id == "sub_h1"
    assert res_filtered.items[0].challenge_id == "request-deduplication"


def test_get_challenge_title_uses_authoritative_registry() -> None:
    """get_challenge_title resolves authoritative titles from ChallengeRegistry with clean fallback."""
    from app.services.progress.service import get_challenge_title

    assert get_challenge_title("request-deduplication") == "Request Deduplication"
    assert get_challenge_title("rate-limiter-token-bucket") == "Rate Limiter (Token Bucket)"
    assert get_challenge_title("lru-cache-ttl") == "LRU Cache with TTL"
    assert get_challenge_title("circuit-breaker-pattern") == "Circuit Breaker Pattern"
    assert get_challenge_title("unknown-custom-slug") == "Unknown Custom Slug"


async def test_progress_summary_authoritative_titles_and_no_legacy_notice(in_memory_db: AsyncSession) -> None:
    """Progress summary and history use authoritative titles and do not include stale local_mvp_notice."""
    now = datetime.now(timezone.utc)
    in_memory_db.add_all([
        Submission(
            id="sub_t1",
            user_id=USER_ID,
            challenge_id="rate-limiter-token-bucket",
            code="code1",
            score=100,
            status="passed",
            created_at=now - timedelta(minutes=3),
        ),
        Submission(
            id="sub_t2",
            user_id=USER_ID,
            challenge_id="lru-cache-ttl",
            code="code2",
            score=80,
            status="passed",
            created_at=now - timedelta(minutes=2),
        ),
        Submission(
            id="sub_t3",
            user_id=USER_ID,
            challenge_id="circuit-breaker-pattern",
            code="code3",
            score=100,
            status="passed",
            created_at=now - timedelta(minutes=1),
        ),
    ])
    await in_memory_db.commit()

    summary = await get_progress_summary(in_memory_db, user_id=USER_ID)
    summary_dict = summary.model_dump()

    # Verify stale notice is absent and data isolation notice is present
    assert "local_mvp_notice" not in summary_dict
    assert "data_isolation_notice" in summary_dict
    assert "strictly isolated" in summary.data_isolation_notice.lower()

    # Verify per-challenge titles match registry exactly
    per_ch_titles = {pc.challenge_id: pc.challenge_title for pc in summary.per_challenge}
    assert per_ch_titles["rate-limiter-token-bucket"] == "Rate Limiter (Token Bucket)"
    assert per_ch_titles["lru-cache-ttl"] == "LRU Cache with TTL"
    assert per_ch_titles["circuit-breaker-pattern"] == "Circuit Breaker Pattern"

    # Verify recent activity titles match registry exactly
    recent_titles = {ra.challenge_id: ra.challenge_title for ra in summary.recent_activity}
    assert recent_titles["rate-limiter-token-bucket"] == "Rate Limiter (Token Bucket)"
    assert recent_titles["lru-cache-ttl"] == "LRU Cache with TTL"
    assert recent_titles["circuit-breaker-pattern"] == "Circuit Breaker Pattern"

    # Verify history items titles match registry exactly
    hist = await get_submission_history(in_memory_db, user_id=USER_ID)
    hist_titles = {item.challenge_id: item.challenge_title for item in hist.items}
    assert hist_titles["rate-limiter-token-bucket"] == "Rate Limiter (Token Bucket)"
    assert hist_titles["lru-cache-ttl"] == "LRU Cache with TTL"
    assert hist_titles["circuit-breaker-pattern"] == "Circuit Breaker Pattern"

