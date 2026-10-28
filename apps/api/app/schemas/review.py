"""Pydantic schemas for post-submission solution review and learning experience."""

from typing import List, Optional
from pydantic import BaseModel, Field


class KeyDecisionItem(BaseModel):
    """A crucial design decision making the reference solution correct."""

    id: str = Field(..., description="Decision identifier")
    title: str = Field(..., description="Short title of the decision")
    explanation: str = Field(..., description="Explanation in context of the challenge")
    why_it_matters: str = Field(..., description="Why this decision matters in production systems")


class SemanticComparison(BaseModel):
    """Comparison analysis between student submitted code and reference solution."""

    is_exact_match: bool = Field(
        ..., description="Whether submitted code is an exact character/text match with reference"
    )
    is_functionally_equivalent: bool = Field(
        ...,
        description="Whether submitted code is functionally identical or passed all tests correctly",
    )
    difference_type: str = Field(
        ...,
        description="Categorization: 'identical', 'formatting_only', 'alternative_correct', 'functional_bug', or 'syntax_error'",
    )
    summary: str = Field(..., description="High-level summary of the comparison")
    meaningful_differences: List[str] = Field(
        default_factory=list,
        description="List of specific functional or architectural differences identified",
    )


class AiReviewSection(BaseModel):
    """Optional AI-generated review commentary from chosen provider."""

    available: bool = Field(..., description="Whether AI review is available")
    content: Optional[str] = Field(default=None, description="Markdown review commentary")
    model: Optional[str] = Field(default=None, description="Model identifier used")
    provider: Optional[str] = Field(default=None, description="Provider used (gemini, claude, openai)")
    error_message: Optional[str] = Field(
        default=None, description="Safe error message if AI review was unavailable"
    )


class SolutionReviewResponse(BaseModel):
    """Comprehensive post-submission review payload."""

    submission_id: str = Field(..., description="Submission identifier")
    challenge_id: str = Field(..., description="Challenge identifier")
    score: int = Field(..., description="Recorded deterministic correctness score (0-100)")
    status: str = Field(..., description="Recorded submission status")
    passed_count: int = Field(..., description="Number of passed tests")
    failed_count: int = Field(..., description="Number of failed tests")
    total_count: int = Field(..., description="Total evaluated tests")
    rubric_version: str = Field(..., description="Rubric version")
    submitted_code: str = Field(..., description="Exact code submitted for this submission ID")
    reference_code: str = Field(..., description="Authoritative reference solution")
    unified_diff: str = Field(..., description="Unified line diff between submitted and reference code")
    comparison: SemanticComparison = Field(..., description="Comparison analysis")
    key_decisions: List[KeyDecisionItem] = Field(..., description="Key implementation decisions")
    learning_takeaways: List[str] = Field(..., description="Core conceptual takeaways")
    ai_review: Optional[AiReviewSection] = Field(
        default=None, description="Optional Gemini-powered explanation of differences"
    )
    security_notice: str = Field(
        default=(
            "This solution review is provided in a local, unauthenticated development environment. "
            "A submission ID alone is not sufficient authorization for public multi-user production systems, "
            "which require user authentication, role-based authorization, and submission ownership checks."
        ),
        description="Notice regarding authentication and MVP scope limitations",
    )
