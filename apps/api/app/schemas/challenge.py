"""Pydantic schemas for challenge endpoints and test execution."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TestCaseSummary(BaseModel):
    """Public summary of a test case visible to students."""

    __test__ = False

    id: str = Field(..., description="Unique test case identifier")
    name: str = Field(..., description="Human-readable test case name")
    description: str = Field(..., description="Description of the requirement under test")


class SandboxStatus(BaseModel):
    """Information regarding host sandbox execution readiness."""

    docker_available: bool = Field(..., description="Whether Docker is detected and operational")
    message: str = Field(..., description="Guidance or operational status message")


class ChallengeCatalogItem(BaseModel):
    """Summary metadata of a challenge for catalog listings."""

    id: str = Field(..., description="Challenge slug identifier")
    title: str = Field(..., description="Challenge title")
    difficulty: str = Field(..., description="Difficulty rating (Easy, Medium, Hard)")
    category: str = Field(..., description="Engineering domain category")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    estimated_minutes: int = Field(..., description="Estimated minutes to complete")
    short_summary: str = Field(..., description="One-sentence problem summary")


class ChallengeDetailResponse(BaseModel):
    """Response containing challenge statement and starter code (without reference solutions)."""

    id: str = Field(..., description="Challenge identifier")
    title: str = Field(..., description="Challenge title")
    difficulty: str = Field(..., description="Difficulty rating")
    category: Optional[str] = Field(default=None, description="Engineering domain category")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    estimated_minutes: int = Field(..., description="Estimated time to complete in minutes")
    short_summary: Optional[str] = Field(default=None, description="One-sentence problem summary")
    description: str = Field(..., description="Problem description and rules")
    starter_code: str = Field(..., description="Python starter code with bug")
    test_cases: List[TestCaseSummary] = Field(..., description="Public test case summaries")
    sandbox_status: SandboxStatus = Field(..., description="Sandbox environment availability")


class CodeRunRequest(BaseModel):
    """Request payload submitting code for test execution."""

    code: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="Python code submission for evaluation",
    )


class TestItemResultSchema(BaseModel):
    """Outcome of an individual test case."""

    __test__ = False

    name: str = Field(..., description="Test name")
    passed: bool = Field(..., description="Pass/fail status")
    message: Optional[str] = Field(default=None, description="Failure details or assertion diff")
    duration_ms: Optional[float] = Field(default=None, description="Execution time in ms")


class CodeRunResponse(BaseModel):
    """Structured results from isolated runner execution."""

    status: str = Field(
        ...,
        description="Status: 'passed', 'failed', 'error', 'timeout', or 'runner_unavailable'",
    )
    passed: int = Field(default=0, description="Total passed tests")
    failed: int = Field(default=0, description="Total failed tests")
    total: int = Field(default=0, description="Total evaluated tests")
    tests: List[TestItemResultSchema] = Field(
        default_factory=list, description="Detailed test case outcomes"
    )
    execution_time_ms: float = Field(
        default=0.0, description="Total execution time in milliseconds"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error or setup prerequisite details"
    )
    stdout: Optional[str] = Field(default=None, description="Standard output from execution")
    docker_available: bool = Field(
        default=False, description="Whether Docker was available for isolated execution"
    )
