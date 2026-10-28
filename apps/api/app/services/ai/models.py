"""Data models for AI assistant requests and provider responses."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AiMode(str, Enum):
    """Supported AI assistance modes."""

    EXPLAIN = "explain"
    HINT = "hint"
    REVIEW = "review"


class AiRequest(BaseModel):
    """Normalized internal request payload passed to AI providers."""

    code: str = Field(..., description="Student Python code submission")
    question: Optional[str] = Field(default=None, description="Optional student inquiry")
    hint_level: int = Field(default=1, description="Progressive hint step (1, 2, or 3)")
    challenge_title: str = Field(default="Request Deduplication", description="Challenge name")
    challenge_description: str = Field(
        default="", description="Public problem description for context"
    )
    reference_code: Optional[str] = Field(
        default=None, description="Authoritative reference solution for review comparison"
    )
    score: Optional[int] = Field(
        default=None, description="Deterministic test score achieved"
    )
    test_summary: Optional[str] = Field(
        default=None, description="Public summary of test outcomes"
    )


class AiResponse(BaseModel):
    """Normalized response returned by AI provider adapters."""

    content: str = Field(..., description="Generated Markdown response from AI")
    mode: AiMode = Field(..., description="Mode executed")
    model: str = Field(..., description="Model identifier that produced the response")
    provider: str = Field(default="gemini", description="Provider identifier (gemini, claude, openai)")
    hint_level: Optional[int] = Field(
        default=None, description="Current progressive hint step if in hint mode"
    )
