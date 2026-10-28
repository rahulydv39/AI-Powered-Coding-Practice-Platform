"""Student progress calculation service and submission history queries.

Calculation semantics:
- All formal submissions (Submit Solution) recorded in the database are counted.
- Exploratory runs (Run Tests) are never persisted and therefore not counted.
- Unscorable attempts (status='runner_unavailable' or score is None) are:
    * Counted in total_submissions and per-challenge total_attempts.
    * Included in submission history with status and score=None.
    * Strictly EXCLUDED from best_score, most_recent_score, and average_score calculations.
    * An unscorable attempt is NEVER counted as a zero score.
- Empty database results are safely handled without ZeroDivisionError.
- Submissions are stably ordered by created_at DESC, id DESC.
"""

import math
from typing import Dict, List, Optional
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.schemas.progress import (
    PerChallengeProgress,
    ProgressSummaryResponse,
    RecentActivityItem,
    ScoreDataPoint,
    SubmissionHistoryItem,
    SubmissionHistoryResponse,
)

# Fallback registry of challenge titles preserved for backward compatibility
CHALLENGE_TITLES: Dict[str, str] = {
    "request-deduplication": "Request Deduplication",
}


def get_challenge_title(challenge_id: str) -> str:
    """Return authoritative title from ChallengeRegistry or human-readable fallback."""
    from app.services.challenges.registry import ChallengeRegistry

    challenge = ChallengeRegistry.get(challenge_id)
    if challenge:
        return challenge.title
    return CHALLENGE_TITLES.get(challenge_id, challenge_id.replace("-", " ").title())


async def get_progress_summary(db: AsyncSession, user_id: str) -> ProgressSummaryResponse:
    """Calculate aggregate student progress across formal submissions for an authenticated user."""
    # 1. Overall counts and score aggregates in a single consolidated query scoped to user
    overall_stmt = select(
        func.count(Submission.id).label("total"),
        func.count(distinct(Submission.challenge_id)).label("distinct_challenges"),
        func.sum(Submission.passed_count).label("total_passed"),
        func.sum(Submission.failed_count).label("total_failed"),
    ).where(Submission.user_id == user_id)
    overall_res = (await db.execute(overall_stmt)).one()

    total_submissions: int = overall_res.total or 0
    distinct_challenges: int = overall_res.distinct_challenges or 0
    total_passed: int = int(overall_res.total_passed or 0)
    total_failed: int = int(overall_res.total_failed or 0)

    # 2. Score-only aggregates (strictly where score IS NOT NULL and user matches)
    score_stmt = select(
        func.count(Submission.id).label("scorable_count"),
        func.max(Submission.score).label("best_score"),
        func.avg(Submission.score).label("avg_score"),
    ).where(Submission.user_id == user_id, Submission.score.is_not(None))
    score_res = (await db.execute(score_stmt)).one()

    scorable_submissions: int = score_res.scorable_count or 0
    best_score: Optional[int] = score_res.best_score if score_res.best_score is not None else None
    average_score: Optional[float] = (
        round(float(score_res.avg_score), 1) if score_res.avg_score is not None else None
    )

    # 3. Solved challenges and submission success rate
    # problems_solved: distinct challenges where user has at least one scorable submission with score == 100
    solved_stmt = select(
        func.count(distinct(Submission.challenge_id))
    ).where(
        Submission.user_id == user_id,
        Submission.score == 100,
    )
    problems_solved: int = (await db.scalar(solved_stmt)) or 0

    # perfect_submissions: scorable formal submissions with score == 100
    perfect_stmt = select(
        func.count(Submission.id)
    ).where(
        Submission.user_id == user_id,
        Submission.score == 100,
    )
    perfect_submissions: int = (await db.scalar(perfect_stmt)) or 0

    # submission_success_rate: percentage of scorable submissions with score == 100
    submission_success_rate: Optional[float] = (
        round((perfect_submissions / scorable_submissions) * 100.0, 1)
        if scorable_submissions > 0
        else None
    )

    # challenge_solve_rate: percentage of attempted challenges solved with score == 100
    challenge_solve_rate: Optional[float] = (
        round((problems_solved / distinct_challenges) * 100.0, 1)
        if distinct_challenges > 0
        else None
    )

    # 4. Most recent scorable score (newest submission where score IS NOT NULL for this user)
    latest_score_stmt = (
        select(Submission.score)
        .where(Submission.user_id == user_id, Submission.score.is_not(None))
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(1)
    )
    most_recent_score: Optional[int] = (await db.execute(latest_score_stmt)).scalar_one_or_none()

    # 5. Per-challenge aggregation scoped to this user
    per_challenge_list: List[PerChallengeProgress] = []

    challenges_stmt = select(Submission.challenge_id).distinct().where(Submission.user_id == user_id)
    challenge_ids = (await db.scalars(challenges_stmt)).all()

    for cid in sorted(challenge_ids):
        # Fetch attempt counts, best score, latest attempt for this challenge and user
        c_stats_stmt = select(
            func.count(Submission.id).label("total_attempts"),
            func.count(Submission.score).label("scorable_attempts"),
            func.max(Submission.score).label("best_score"),
        ).where(Submission.user_id == user_id, Submission.challenge_id == cid)
        c_stats = (await db.execute(c_stats_stmt)).one()

        # Latest attempt details
        c_latest_stmt = (
            select(Submission)
            .where(Submission.user_id == user_id, Submission.challenge_id == cid)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
            .limit(1)
        )
        c_latest = (await db.scalars(c_latest_stmt)).first()

        # Latest scorable score
        c_latest_scorable_stmt = (
            select(Submission.score)
            .where(
                Submission.user_id == user_id,
                Submission.challenge_id == cid,
                Submission.score.is_not(None),
            )
            .order_by(Submission.created_at.desc(), Submission.id.desc())
            .limit(1)
        )
        c_latest_score = (await db.execute(c_latest_scorable_stmt)).scalar_one_or_none()

        # Chronologically earliest scorable score
        c_first_scorable_stmt = (
            select(Submission.score)
            .where(
                Submission.user_id == user_id,
                Submission.challenge_id == cid,
                Submission.score.is_not(None),
            )
            .order_by(Submission.created_at.asc(), Submission.id.asc())
            .limit(1)
        )
        c_first_score = (await db.execute(c_first_scorable_stmt)).scalar_one_or_none()

        score_improvement_delta: Optional[int] = None
        if c_latest_score is not None and c_first_score is not None:
            score_improvement_delta = c_latest_score - c_first_score

        is_solved = bool(c_stats.best_score is not None and c_stats.best_score == 100)

        per_challenge_list.append(
            PerChallengeProgress(
                challenge_id=cid,
                challenge_title=get_challenge_title(cid),
                total_attempts=c_stats.total_attempts or 0,
                scorable_attempts=c_stats.scorable_attempts or 0,
                best_score=c_stats.best_score if c_stats.best_score is not None else None,
                latest_score=c_latest_score,
                first_scorable_score=c_first_score,
                score_improvement_delta=score_improvement_delta,
                is_solved=is_solved,
                latest_status=c_latest.status if c_latest else None,
                latest_submitted_at=c_latest.created_at if c_latest else None,
            )
        )

    # 6. Score progress history (chronological, scorable submissions for this user only, limit 50)
    history_stmt = (
        select(Submission.id, Submission.challenge_id, Submission.score, Submission.created_at)
        .where(Submission.user_id == user_id, Submission.score.is_not(None))
        .order_by(Submission.created_at.asc(), Submission.id.asc())
        .limit(50)
    )
    history_rows = (await db.execute(history_stmt)).all()
    score_history = [
        ScoreDataPoint(
            submission_id=r.id,
            challenge_id=r.challenge_id,
            score=r.score,
            created_at=r.created_at,
        )
        for r in history_rows
    ]

    # 7. Recent activity (chronological, newest first, limit 5, scoped to user)
    recent_stmt = (
        select(Submission)
        .where(Submission.user_id == user_id)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(5)
    )
    recent_rows = (await db.scalars(recent_stmt)).all()
    recent_activity = [
        RecentActivityItem(
            id=s.id,
            challenge_id=s.challenge_id,
            challenge_title=get_challenge_title(s.challenge_id),
            created_at=s.created_at,
            score=s.score,
            status=s.status,
            passed_count=s.passed_count,
            total_count=s.total_count,
        )
        for s in recent_rows
    ]

    return ProgressSummaryResponse(
        total_submissions=total_submissions,
        scorable_submissions=scorable_submissions,
        distinct_challenges_attempted=distinct_challenges,
        problems_solved=problems_solved,
        submission_success_rate=submission_success_rate,
        challenge_solve_rate=challenge_solve_rate,
        best_score=best_score,
        most_recent_score=most_recent_score,
        average_score=average_score,
        total_passed_tests=total_passed,
        total_failed_tests=total_failed,
        per_challenge=per_challenge_list,
        score_history=score_history,
        recent_activity=recent_activity,
    )


async def get_submission_history(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    challenge_id: Optional[str] = None,
) -> SubmissionHistoryResponse:
    """Retrieve paginated formal submission records for a specific authenticated user."""
    base_filter = [Submission.user_id == user_id]
    if challenge_id:
        base_filter.append(Submission.challenge_id == challenge_id)

    # Count total matching rows
    count_stmt = select(func.count(Submission.id)).where(*base_filter)
    total = (await db.scalar(count_stmt)) or 0

    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    safe_page = max(1, min(page, total_pages)) if total > 0 else 1
    offset = (safe_page - 1) * page_size

    # Fetch ordered page of items with stable ordering
    items_stmt = (
        select(Submission)
        .where(*base_filter)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(page_size)
        .offset(offset)
    )

    submissions = (await db.scalars(items_stmt)).all()

    items = [
        SubmissionHistoryItem(
            id=s.id,
            challenge_id=s.challenge_id,
            challenge_title=get_challenge_title(s.challenge_id),
            created_at=s.created_at,
            score=s.score,
            passed_count=s.passed_count,
            failed_count=s.failed_count,
            total_count=s.total_count,
            status=s.status,
            execution_time_ms=s.execution_time_ms,
            rubric_version=s.rubric_version,
            is_review_available=(s.score is not None and s.status != "runner_unavailable"),
            code=s.code,
        )
        for s in submissions
    ]

    return SubmissionHistoryResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=safe_page < total_pages,
        has_prev=safe_page > 1,
    )


async def get_submission_snapshot(
    db: AsyncSession,
    submission_id: str,
    user_id: str,
) -> Optional[SubmissionHistoryItem]:
    """Retrieve full submission record including code snapshot, verifying user ownership."""
    stmt = select(Submission).where(
        Submission.id == submission_id,
        Submission.user_id == user_id,
    )
    submission = (await db.scalars(stmt)).first()
    if not submission:
        return None

    return SubmissionHistoryItem(
        id=submission.id,
        challenge_id=submission.challenge_id,
        challenge_title=get_challenge_title(submission.challenge_id),
        created_at=submission.created_at,
        score=submission.score,
        passed_count=submission.passed_count,
        failed_count=submission.failed_count,
        total_count=submission.total_count,
        status=submission.status,
        execution_time_ms=submission.execution_time_ms,
        rubric_version=submission.rubric_version,
        is_review_available=(submission.score is not None and submission.status != "runner_unavailable"),
        code=submission.code,
    )
