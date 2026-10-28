"""Data structures for isolated execution runner results."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TestItemResult(BaseModel):
    """Result of an individual test case execution."""

    __test__ = False  # Prevent pytest from treating this model as a test class

    name: str = Field(..., description="Human-readable test case name")
    passed: bool = Field(..., description="Whether this test passed")
    message: Optional[str] = Field(
        default=None, description="Assertion or failure message if the test failed"
    )
    duration_ms: Optional[float] = Field(
        default=None, description="Execution time in milliseconds for this test"
    )


class RunResult(BaseModel):
    """Aggregate result from the isolated runner."""

    status: str = Field(
        ...,
        description="Execution status ('passed', 'failed', 'error', 'timeout', 'runner_unavailable')",
    )
    passed: int = Field(default=0, description="Number of passed tests")
    failed: int = Field(default=0, description="Number of failed tests")
    total: int = Field(default=0, description="Total number of evaluated tests")
    tests: List[TestItemResult] = Field(
        default_factory=list, description="Per-test results breakdown"
    )
    execution_time_ms: float = Field(
        default=0.0, description="Total runner execution time in milliseconds"
    )
    stdout: str = Field(default="", description="Sanitized stdout captured from execution")
    stderr: str = Field(default="", description="Sanitized stderr captured from execution")
    error_message: Optional[str] = Field(
        default=None, description="High-level error or prerequisite notification"
    )
    docker_available: bool = Field(
        default=False, description="Whether Docker sandbox was available on the host"
    )
