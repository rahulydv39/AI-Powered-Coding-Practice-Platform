"""Post-submission solution review service.

Generates structured, deterministic review comparisons against the authoritative
reference solution for Request Deduplication, with optional Gemini AI commentary.
"""

import ast
import difflib
import logging
from typing import List, Tuple

from app.models.submission import Submission
from app.schemas.review import (
    AiReviewSection,
    KeyDecisionItem,
    SemanticComparison,
    SolutionReviewResponse,
)
from app.services.ai.base import BaseAiProvider
from app.services.ai.exceptions import AiError
from app.services.ai.models import AiMode, AiRequest
from app.services.challenges.request_deduplication import (
    CHALLENGE_DESCRIPTION,
    CHALLENGE_ID,
    CHALLENGE_TITLE,
    REFERENCE_SOLUTION,
)

logger = logging.getLogger(__name__)

KEY_DECISIONS: List[KeyDecisionItem] = [
    KeyDecisionItem(
        id="input_validation",
        title="Fail-Fast Input Validation (ValueError)",
        explanation=(
            "The reference solution verifies `if not isinstance(request_id, str) or not request_id.strip():` "
            "and immediately raises `ValueError('request_id must be a non-empty string')` before touching any state."
        ),
        why_it_matters=(
            "In production APIs, silent failures or returning boolean False for malformed/empty IDs causes "
            "invalid payloads to falsely appear as duplicate requests. Fail-fast validation enforces contract "
            "integrity at the service boundary."
        ),
    ),
    KeyDecisionItem(
        id="duplicate_check_ordering",
        title="Pre-Mutation Membership Check (`in seen_ids`)",
        explanation=(
            "The lookup `if request_id in seen_ids:` happens strictly before any mutation to `seen_ids`. "
            "If already present, it returns `False` immediately."
        ),
        why_it_matters=(
            "Order of operations is paramount: checking membership before inserting preserves the distinction "
            "between first-arrival and repeat occurrences. Adding before checking would erase that signal."
        ),
    ),
    KeyDecisionItem(
        id="state_registration",
        title="First-Occurrence State Mutation (`seen_ids.add`)",
        explanation=(
            "When an identifier is confirmed new, it is immediately registered: `seen_ids.add(request_id)`."
        ),
        why_it_matters=(
            "Without updating the tracking set, all future arrivals of this identifier would be treated as first "
            "occurrences, allowing duplicate operations and race conditions in downstream services."
        ),
    ),
    KeyDecisionItem(
        id="boolean_return_contract",
        title="Explicit Boolean Return Contract (`True` vs `False`)",
        explanation=(
            "Returns `True` exclusively for accepted first-time requests, and `False` for duplicate rejections."
        ),
        why_it_matters=(
            "Provides an unambiguous boolean gate for upstream dispatchers, middleware, and background workers "
            "to decide whether to process the payload or discard it."
        ),
    ),
]

LEARNING_TAKEAWAYS: List[str] = [
    (
        "Idempotency in Distributed Systems: Request deduplication ensures that network retries, client timeouts, "
        "and duplicate dispatches do not trigger duplicate database writes, double billing, or conflicting background jobs."
    ),
    (
        "Set Lookup Complexity: Python `set` uses hash tables offering average O(1) constant-time lookup and insertion, "
        "whereas an array/list requires O(N) linear scans that degrade under high request volume."
    ),
    (
        "Defensive Contract Boundaries: Differentiating client contract violations (raising ValueError) from valid duplicate "
        "domain events (returning False) prevents telemetry skew and avoids corrupting state."
    ),
    (
        "Horizontal State Architecture: In a single-process service, an in-memory set tracks session IDs. In distributed "
        "horizontal architectures, this pattern scales across nodes using shared stores like Redis sets with TTL expiration."
    ),
]


def _strip_docstrings_and_comments(tree: ast.AST) -> None:
    """Recursively remove docstring Expr nodes for clean AST comparison."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body = node.body[1:]


def compare_code_with_reference(
    submitted_code: str,
    reference_code: str,
    score: int,
    passed_count: int,
    total_count: int,
    challenge_id: str = "request-deduplication",
) -> Tuple[str, SemanticComparison]:
    """Perform deterministic line-oriented diff and semantic difference analysis."""
    sub_lines = submitted_code.splitlines(keepends=True)
    ref_lines = reference_code.splitlines(keepends=True)

    diff = "".join(
        difflib.unified_diff(
            sub_lines,
            ref_lines,
            fromfile="submitted_code.py",
            tofile="reference_solution.py",
            lineterm="",
        )
    )

    # 1. Exact character match
    if submitted_code.strip() == reference_code.strip():
        return diff, SemanticComparison(
            is_exact_match=True,
            is_functionally_equivalent=True,
            difference_type="identical",
            summary="Your submitted code exactly matches the authoritative reference solution.",
            meaningful_differences=[],
        )

    # 2. Syntax validation
    try:
        sub_ast = ast.parse(submitted_code)
    except SyntaxError as exc:
        return diff, SemanticComparison(
            is_exact_match=False,
            is_functionally_equivalent=False,
            difference_type="syntax_error",
            summary=f"Submitted code contains a Python syntax error: {exc.msg} (line {exc.lineno}).",
            meaningful_differences=[f"Syntax error on line {exc.lineno}: {exc.msg}"],
        )

    # 3. Normalized AST comparison (ignoring comments/docstrings/whitespace)
    try:
        ref_ast = ast.parse(reference_code)
        sub_ast_copy = ast.parse(submitted_code)
        _strip_docstrings_and_comments(ref_ast)
        _strip_docstrings_and_comments(sub_ast_copy)

        if ast.dump(ref_ast) == ast.dump(sub_ast_copy):
            return diff, SemanticComparison(
                is_exact_match=False,
                is_functionally_equivalent=True,
                difference_type="formatting_only",
                summary=(
                    "Your submitted code is functionally identical to the reference solution "
                    "(differing only in comments, docstrings, or formatting)."
                ),
                meaningful_differences=[],
            )
    except Exception as exc:
        logger.debug("AST normalized comparison error: %s", exc)

    # 4. Solved all tests (score == 100) with alternative structural style
    if score == 100:
        return diff, SemanticComparison(
            is_exact_match=False,
            is_functionally_equivalent=True,
            difference_type="alternative_correct",
            summary=(
                f"Your submitted code passed all deterministic tests (100% score)! "
                f"It employs an alternative valid implementation structure compared to the reference solution."
            ),
            meaningful_differences=[],
        )

    # 5. Functional differences for failing or partial solutions
    meaningful_diffs: List[str] = []

    if challenge_id == "request-deduplication":
        has_seen_add = False
        has_value_error = False
        has_strip_check = False
        has_in_check = False

        for node in ast.walk(sub_ast):
            if isinstance(node, ast.Raise) and node.exc:
                if (isinstance(node.exc, ast.Name) and node.exc.id == "ValueError") or (
                    isinstance(node.exc, ast.Call)
                    and isinstance(node.exc.func, ast.Name)
                    and node.exc.func.id == "ValueError"
                ):
                    has_value_error = True
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add":
                    has_seen_add = True
                if isinstance(node.func, ast.Attribute) and node.func.attr == "strip":
                    has_strip_check = True
            elif isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, (ast.In, ast.NotIn)):
                        has_in_check = True

        if not has_value_error:
            meaningful_diffs.append(
                "Missing ValueError: Invalid, empty, or whitespace-only inputs must raise ValueError rather than returning False."
            )
        elif not has_strip_check:
            meaningful_diffs.append(
                "Whitespace validation: Empty or whitespace-only strings (e.g. '   ') should be validated with request_id.strip()."
            )

        if not has_seen_add:
            meaningful_diffs.append(
                "Missing state registration: Newly accepted identifiers are not added to seen_ids via seen_ids.add(request_id)."
            )

        if not has_in_check:
            meaningful_diffs.append(
                "Missing duplicate check: The code does not check if request_id is already in seen_ids before proceeding."
            )

    if not meaningful_diffs:
        meaningful_diffs.append(
            f"Code logic produced failing test outcomes ({passed_count}/{total_count} passed). Check branch conditions, state mutations, and edge case handling."
        )

    return diff, SemanticComparison(
        is_exact_match=False,
        is_functionally_equivalent=False,
        difference_type="functional_bug",
        summary=f"Submitted code differs functionally from the reference solution ({passed_count}/{total_count} tests passed).",
        meaningful_differences=meaningful_diffs,
    )


async def generate_solution_review(
    submission: Submission,
    include_ai: bool,
    ai_provider: BaseAiProvider,
    challenge_def: object = None,
) -> SolutionReviewResponse:
    """Assemble a post-submission solution review for a verified scorable submission."""
    if challenge_def is None:
        from app.services.challenges.registry import ChallengeRegistry

        challenge_def = ChallengeRegistry.get(submission.challenge_id)
        if challenge_def is None:
            from app.services.challenges.request_deduplication import REQUEST_DEDUPLICATION_CHALLENGE

            challenge_def = REQUEST_DEDUPLICATION_CHALLENGE

    ref_solution = getattr(challenge_def, "reference_solution", REFERENCE_SOLUTION)
    key_decisions = getattr(challenge_def, "key_decisions", KEY_DECISIONS)
    learning_takeaways = getattr(challenge_def, "learning_takeaways", LEARNING_TAKEAWAYS)
    c_title = getattr(challenge_def, "title", CHALLENGE_TITLE)
    c_desc = getattr(challenge_def, "description", CHALLENGE_DESCRIPTION)

    diff, comparison = compare_code_with_reference(
        submitted_code=submission.code,
        reference_code=ref_solution,
        score=submission.score or 0,
        passed_count=submission.passed_count,
        total_count=submission.total_count,
        challenge_id=submission.challenge_id,
    )

    ai_review: AiReviewSection | None = None

    if include_ai:
        ai_req = AiRequest(
            code=submission.code,
            reference_code=ref_solution,
            score=submission.score,
            test_summary=(
                f"{submission.passed_count}/{submission.total_count} tests passed "
                f"(status: {submission.status})"
            ),
            challenge_title=c_title,
            challenge_description=c_desc,
        )

        try:
            ai_resp = await ai_provider.generate_response(ai_req, mode=AiMode.REVIEW)
            ai_review = AiReviewSection(
                available=True,
                content=ai_resp.content,
                model=ai_resp.model,
                provider=ai_resp.provider,
                error_message=None,
            )
        except AiError as exc:
            logger.warning("AI review unavailable: %s", exc.message)
            ai_review = AiReviewSection(
                available=False,
                content=None,
                model=None,
                error_message=exc.message,
            )
        except Exception as exc:
            logger.exception("Unexpected error generating AI review: %s", exc)
            ai_review = AiReviewSection(
                available=False,
                content=None,
                model=None,
                error_message="AI assistant review could not be completed. Please try again.",
            )

    return SolutionReviewResponse(
        submission_id=submission.id,
        challenge_id=submission.challenge_id,
        score=submission.score or 0,
        status=submission.status,
        passed_count=submission.passed_count,
        failed_count=submission.failed_count,
        total_count=submission.total_count,
        rubric_version=submission.rubric_version,
        submitted_code=submission.code,
        reference_code=ref_solution,
        unified_diff=diff,
        comparison=comparison,
        key_decisions=key_decisions,
        learning_takeaways=learning_takeaways,
        ai_review=ai_review,
    )
