"""API endpoints for student progress analytics and submission history."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas.progress import (
    ProgressSummaryResponse,
    SubmissionHistoryItem,
    SubmissionHistoryResponse,
)
from app.services.progress.service import (
    get_progress_summary,
    get_submission_history,
    get_submission_snapshot,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get(
    "/summary",
    response_model=ProgressSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Student Progress Summary",
    description="Returns aggregate metrics calculated across all real persisted formal submissions for the authenticated user.",
)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ProgressSummaryResponse:
    """Calculate and return student progress summary statistics for current user."""
    try:
        return await get_progress_summary(db, user_id=current_user.id)
    except Exception as exc:
        logger.exception("Failed to calculate progress summary: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate student progress summary.",
        )


@router.get(
    "/history",
    response_model=SubmissionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Submission History",
    description="Returns paginated formal submission records for the authenticated user ordered by newest first.",
)
async def get_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Number of submissions per page"
    ),
    challenge_id: Optional[str] = Query(
        default=None, description="Optional challenge ID filter"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SubmissionHistoryResponse:
    """Retrieve paginated submission history for current user."""
    try:
        return await get_submission_history(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            challenge_id=challenge_id,
        )
    except Exception as exc:
        logger.exception("Failed to retrieve submission history: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submission history records.",
        )


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionHistoryItem,
    status_code=status.HTTP_200_OK,
    summary="Get Historical Submission Snapshot",
    description="Retrieves a specific historical submission record including code snapshot, verifying ownership.",
)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SubmissionHistoryItem:
    """Retrieve specific submission snapshot by ID, ensuring user owns the submission."""
    item = await get_submission_snapshot(db, submission_id, user_id=current_user.id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found.",
        )
    return item
