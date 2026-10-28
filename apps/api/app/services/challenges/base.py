"""Base dataclass definition for interactive coding challenges."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.schemas.review import KeyDecisionItem


@dataclass(frozen=True)
class ChallengeDefinition:
    """Immutable authoritative definition of a coding challenge."""

    id: str  # URL-safe slug, e.g. "request-deduplication"
    title: str  # Display title, e.g. "Request Deduplication"
    difficulty: str  # "Easy" | "Medium" | "Hard"
    category: str  # Primary technical domain, e.g. "Distributed Systems"
    tags: List[str]  # Sub-topics, e.g. ["Idempotency", "State Management"]
    estimated_minutes: int  # Estimated completion duration
    short_summary: str  # Concise 1-sentence catalog summary
    description: str  # Full GitHub-flavored Markdown problem statement & specification
    starter_code: str  # Initial starter template with intentional bug
    reference_solution: str  # Authoritative hidden reference implementation
    test_cases: List[Dict[str, str]]  # Public test summaries: [{"id", "name", "description"}]
    test_harness_code: str  # Complete Python test harness executed inside isolated Docker container
    key_decisions: List[KeyDecisionItem] = field(default_factory=list)  # Authoritative engineering tradeoffs
    learning_takeaways: List[str] = field(default_factory=list)  # Core concepts and production context
