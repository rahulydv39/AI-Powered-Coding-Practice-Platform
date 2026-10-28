"""API endpoints for interactive coding challenges."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.rate_limit import check_ai_rate_limit
from app.models.submission import Submission
from app.models.user import User
from app.schemas.ai import (
    AiExplainRequest,
    AiHintRequest,
    AiResponseSchema,
    ProviderInfoSchema,
    ProvidersListResponse,
)
from app.schemas.challenge import (
    ChallengeCatalogItem,
    ChallengeDetailResponse,
    CodeRunRequest,
    CodeRunResponse,
    SandboxStatus,
    TestCaseSummary,
    TestItemResultSchema,
)
from app.schemas.review import SolutionReviewResponse
from app.schemas.submission import SubmissionRequest, SubmissionResponse
from app.services.ai.base import BaseAiProvider
from app.services.ai.exceptions import AiError
from app.services.ai.factory import (
    SUPPORTED_PROVIDERS,
    get_ai_provider as get_dynamic_ai_provider,
    get_available_providers,
)
from app.services.ai.gemini_provider import get_ai_provider
from app.services.ai.models import AiMode, AiRequest
from app.services.challenges.registry import ChallengeRegistry
from app.services.challenges.request_deduplication import CHALLENGE_ID
from app.services.challenges.solution_review import generate_solution_review
from app.services.runner.docker_runner import DockerSandboxRunner, get_sandbox_runner
from app.services.scoring.service import evaluate_submission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get(
    "",
    response_model=List[ChallengeCatalogItem],
    status_code=status.HTTP_200_OK,
    summary="List Available Coding Challenges",
    description="Returns public catalog metadata for all registered interview practice challenges.",
)
async def list_challenges() -> List[ChallengeCatalogItem]:
    """Retrieve public challenge catalog.

    Server-side reference solutions and hidden test harnesses are NEVER exposed.
    """
    return [ChallengeCatalogItem(**c) for c in ChallengeRegistry.list_public()]


@router.get(
    "/ai/providers",
    response_model=ProvidersListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Supported AI Providers",
    description="Returns supported AI providers and configured model IDs without exposing secrets.",
)
async def list_ai_providers() -> ProvidersListResponse:
    """Retrieve supported AI providers and active defaults."""
    settings = get_settings()
    return ProvidersListResponse(
        default_provider=settings.AI_DEFAULT_PROVIDER or "gemini",
        providers=[ProviderInfoSchema(**p) for p in get_available_providers()],
    )


@router.get(
    "/{challenge_id}",
    response_model=ChallengeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Challenge Metadata",
    description="Returns public problem statement, starter code, and test case summaries.",
)
async def get_challenge(
    challenge_id: str,
    runner: DockerSandboxRunner = Depends(get_sandbox_runner),
) -> ChallengeDetailResponse:
    """Retrieve challenge details by ID.

    Note: Server-side reference solutions and hidden test harnesses are NEVER exposed.
    Public access permitted for browsing problem descriptions.
    """
    challenge = ChallengeRegistry.get(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    docker_active = runner.is_docker_available()
    sandbox_msg = (
        "Docker sandbox is available and ready for isolated execution."
        if docker_active
        else "Docker is not detected on the host. Please install and start Docker Desktop or OrbStack to execute tests safely."
    )

    test_summaries = [
        TestCaseSummary(
            id=t["id"],
            name=t["name"],
            description=t["description"],
        )
        for t in challenge.test_cases
    ]

    return ChallengeDetailResponse(
        id=challenge.id,
        title=challenge.title,
        difficulty=challenge.difficulty,
        category=challenge.category,
        tags=challenge.tags,
        estimated_minutes=challenge.estimated_minutes,
        short_summary=challenge.short_summary,
        description=challenge.description,
        starter_code=challenge.starter_code,
        test_cases=test_summaries,
        sandbox_status=SandboxStatus(
            docker_available=docker_active,
            message=sandbox_msg,
        ),
    )


@router.post(
    "/{challenge_id}/run",
    response_model=CodeRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Code in Isolated Sandbox",
    description="Submits Python code for isolated containerized evaluation against deterministic tests.",
)
async def run_challenge_code(
    challenge_id: str,
    payload: CodeRunRequest,
    current_user: User = Depends(get_current_user),
    runner: DockerSandboxRunner = Depends(get_sandbox_runner),
) -> CodeRunResponse:
    """Execute submitted code in an isolated container.

    SECURITY RULE:
    - Requires authenticated student account.
    - The server supplies the authoritative test harness. The client cannot modify
      test assertions or bypass isolation.
    """
    challenge = ChallengeRegistry.get(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    if not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Submitted code cannot be empty.",
        )

    # Dispatch to isolated runner with server-side test harness
    result = runner.run_submission(
        student_code=payload.code,
        test_harness_code=challenge.test_harness_code,
    )

    return CodeRunResponse(
        status=result.status,
        passed=result.passed,
        failed=result.failed,
        total=result.total,
        tests=[
            TestItemResultSchema(
                name=t.name,
                passed=t.passed,
                message=t.message,
                duration_ms=t.duration_ms,
            )
            for t in result.tests
        ],
        execution_time_ms=result.execution_time_ms,
        error_message=result.error_message,
        stdout=result.stdout if result.stdout else None,
        docker_available=result.docker_available,
    )


@router.post(
    "/{challenge_id}/ai/explain",
    response_model=AiResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Explain Student Code (AI Assistant)",
    description="Analyzes the submitted code and returns a clear, structured explanation using the selected provider.",
    dependencies=[Depends(check_ai_rate_limit)],
)
async def explain_code(
    challenge_id: str,
    payload: AiExplainRequest,
    current_user: User = Depends(get_current_user),
    ai_provider: BaseAiProvider = Depends(get_ai_provider),
) -> AiResponseSchema:
    """Explain what the student's code does, its control flow, and potential edge cases."""
    challenge = ChallengeRegistry.get(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    if not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source code cannot be empty.",
        )

    # Resolve target provider
    from app.main import app

    target_provider = ai_provider
    if payload.provider:
        p_key = payload.provider.lower().strip()
        if p_key not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider '{payload.provider}'. Supported providers: {', '.join(SUPPORTED_PROVIDERS)}.",
            )
        if get_ai_provider not in app.dependency_overrides:
            try:
                target_provider = get_dynamic_ai_provider(p_key)
            except AiError as exc:
                raise HTTPException(
                    status_code=exc.status_code,
                    detail=exc.message,
                )

    ai_req = AiRequest(
        code=payload.code,
        question=payload.question,
        challenge_title=challenge.title,
        challenge_description=challenge.description,
    )

    try:
        response = await target_provider.generate_response(ai_req, mode=AiMode.EXPLAIN)
        return AiResponseSchema(
            success=True,
            mode="explain",
            content=response.content,
            model=response.model,
            provider=response.provider,
        )
    except AiError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.post(
    "/{challenge_id}/ai/hint",
    response_model=AiResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Progressive Debugging Hint (AI Assistant)",
    description="Returns a progressive hint based on student code and requested hint level using selected provider.",
    dependencies=[Depends(check_ai_rate_limit)],
)
async def get_hint(
    challenge_id: str,
    payload: AiHintRequest,
    current_user: User = Depends(get_current_user),
    ai_provider: BaseAiProvider = Depends(get_ai_provider),
) -> AiResponseSchema:
    """Generate a progressive debugging hint guiding the student toward the solution."""
    challenge = ChallengeRegistry.get(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    if not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source code cannot be empty.",
        )

    # Resolve target provider
    from app.main import app

    target_provider = ai_provider
    if payload.provider:
        p_key = payload.provider.lower().strip()
        if p_key not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider '{payload.provider}'. Supported providers: {', '.join(SUPPORTED_PROVIDERS)}.",
            )
        if get_ai_provider not in app.dependency_overrides:
            try:
                target_provider = get_dynamic_ai_provider(p_key)
            except AiError as exc:
                raise HTTPException(
                    status_code=exc.status_code,
                    detail=exc.message,
                )

    ai_req = AiRequest(
        code=payload.code,
        question=payload.question,
        hint_level=payload.hint_level,
        challenge_title=challenge.title,
        challenge_description=challenge.description,
    )

    try:
        response = await target_provider.generate_response(ai_req, mode=AiMode.HINT)
        return AiResponseSchema(
            success=True,
            mode="hint",
            content=response.content,
            model=response.model,
            provider=response.provider,
            hint_level=response.hint_level,
        )
    except AiError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.post(
    "/{challenge_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Challenge Solution for Scoring",
    description="Evaluates student submission against authoritative test suite and calculates deterministic correctness score.",
)
async def submit_challenge_solution(
    challenge_id: str,
    payload: SubmissionRequest,
    current_user: User = Depends(get_current_user),
    runner: DockerSandboxRunner = Depends(get_sandbox_runner),
    db: AsyncSession = Depends(get_db_session),
) -> SubmissionResponse:
    """Submit code for formal grading and score recording.

    SECURITY & INTEGRITY:
    - Requires authenticated student account; associates submission with current user.
    - Code is executed in an isolated Docker sandbox against hidden server-side test harness.
    - Code is NEVER executed directly on the host API process.
    - Deterministic scoring: round(passed_tests / total_tests * 100).
    - AI is NOT used for correctness evaluation.
    - Test harness, hidden inputs, and reference solutions are NEVER leaked.
    - Infrastructure failures (Docker unavailable) do not yield scorable submissions.
    """
    challenge = ChallengeRegistry.get(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    if not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Submitted code cannot be empty.",
        )

    # 1. Execute in Docker sandbox using authoritative test harness
    run_result = runner.run_submission(
        student_code=payload.code,
        test_harness_code=challenge.test_harness_code,
    )

    # 2. Compute deterministic score and evaluation outcome
    outcome = evaluate_submission(run_result)

    submission_id = None
    created_at = None

    # 3. Persist scorable attempts in PostgreSQL database associated with current student
    if outcome.is_scorable:
        submission = Submission(
            user_id=current_user.id,
            challenge_id=challenge_id,
            code=payload.code,
            score=outcome.score,
            passed_count=outcome.passed,
            failed_count=outcome.failed,
            total_count=outcome.total,
            execution_time_ms=outcome.execution_time_ms,
            status=outcome.status,
            rubric_version=outcome.rubric_version,
        )
        try:
            db.add(submission)
            await db.commit()
            await db.refresh(submission)
            submission_id = submission.id
            created_at = submission.created_at
        except Exception as exc:
            logger.error("Failed to persist submission to database: %s", exc)
            await db.rollback()
            created_at = datetime.now(timezone.utc)

    return SubmissionResponse(
        submission_id=submission_id,
        challenge_id=challenge_id,
        status=outcome.status,
        score=outcome.score,
        passed=outcome.passed,
        failed=outcome.failed,
        total=outcome.total,
        execution_time_ms=outcome.execution_time_ms,
        rubric_version=outcome.rubric_version,
        feedback_summary=outcome.feedback_summary,
        score_disclaimer=outcome.score_disclaimer,
        docker_available=run_result.docker_available,
        error_message=outcome.error_message,
        created_at=created_at,
    )


@router.get(
    "/{challenge_id}/submissions/{submission_id}/review",
    response_model=SolutionReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Post-Submission Solution Review",
    description="Returns reference solution, key implementation decisions, diff analysis, and optional AI comparison after a completed scorable submission.",
)
async def get_submission_solution_review(
    challenge_id: str,
    submission_id: str,
    include_ai: bool = Query(
        default=False, description="Whether to include AI review commentary"
    ),
    provider: Optional[str] = Query(
        default=None, description="Requested AI provider (gemini, claude, openai)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    ai_provider: BaseAiProvider = Depends(get_ai_provider),
) -> SolutionReviewResponse:
    """Retrieve structured solution review and learning insights for an evaluated submission.

    ACCESS RULES & INTEGRITY:
    - Available ONLY after an eligible submission has been completed and stored.
    - Reference solution is kept strictly server-side until this review endpoint is requested.
    - Verified against database: submission must exist, match challenge_id, belong to current user, and have a scorable outcome.
    - Non-scorable submissions (runner unavailable) cannot access solution review.
    - Stored submission code is used for the comparison, NOT arbitrary client parameters.
    - Scoped strictly to current user; other users or unauthenticated requests cannot access this review.
    """
    challenge = ChallengeRegistry.get(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    stmt = select(Submission).where(
        Submission.id == submission_id,
        Submission.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found.",
        )

    if submission.challenge_id != challenge_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' does not belong to challenge '{challenge_id}'.",
        )

    if submission.score is None or submission.status == "runner_unavailable":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solution review is only available for completed, scorable submissions. "
                "This submission was not scorable due to an infrastructure error."
            ),
        )

    # Resolve target provider
    from app.main import app

    target_provider = ai_provider
    if provider:
        p_key = provider.lower().strip()
        if p_key not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider '{provider}'. Supported providers: {', '.join(SUPPORTED_PROVIDERS)}.",
            )
        if get_ai_provider not in app.dependency_overrides:
            try:
                target_provider = get_dynamic_ai_provider(p_key)
            except AiError as exc:
                raise HTTPException(
                    status_code=exc.status_code,
                    detail=exc.message,
                )

    return await generate_solution_review(
        submission=submission,
        include_ai=include_ai,
        ai_provider=target_provider,
        challenge_def=challenge,
    )
