"""Authoritative challenge registry for AI Coding Gym.

Maintains in-memory registry of validated challenge definitions.
Guarantees:
- Server-side authoritative validation
- Zero hidden test or reference solution leakage in public catalog
- Fast O(1) lookup by URL-safe slug ID
"""

import re
from typing import Any, Dict, List, Optional
from app.services.challenges.base import ChallengeDefinition

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ChallengeRegistry:
    """Registry managing available coding challenges."""

    _challenges: Dict[str, ChallengeDefinition] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, challenge: ChallengeDefinition) -> None:
        """Register a new challenge definition."""
        if not SLUG_PATTERN.match(challenge.id):
            raise ValueError(
                f"Invalid challenge ID '{challenge.id}'. Must be lowercase alphanumeric with hyphens."
            )
        if challenge.id in cls._challenges:
            raise ValueError(f"Duplicate challenge ID registered: '{challenge.id}'.")
        cls._challenges[challenge.id] = challenge

    @classmethod
    def get(cls, challenge_id: str) -> Optional[ChallengeDefinition]:
        """Retrieve challenge definition by ID."""
        cls._ensure_initialized()
        return cls._challenges.get(challenge_id)

    @classmethod
    def exists(cls, challenge_id: str) -> bool:
        """Check whether challenge ID is registered."""
        cls._ensure_initialized()
        return challenge_id in cls._challenges

    @classmethod
    def list_all(cls) -> List[ChallengeDefinition]:
        """Return all registered challenge definitions (internal use only)."""
        cls._ensure_initialized()
        return list(cls._challenges.values())

    @classmethod
    def list_public(cls) -> List[Dict[str, Any]]:
        """Return public metadata for all challenges for catalog browsing.

        Never exposes reference_solution or test_harness_code.
        """
        cls._ensure_initialized()
        return [
            {
                "id": c.id,
                "title": c.title,
                "difficulty": c.difficulty,
                "category": c.category,
                "tags": c.tags,
                "estimated_minutes": c.estimated_minutes,
                "short_summary": c.short_summary,
            }
            for c in cls._challenges.values()
        ]

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazy load and register standard challenges if not yet initialized."""
        if cls._initialized:
            return
        cls._initialized = True
        # Import challenge modules to trigger self-registration
        # 1. Request Deduplication
        from app.services.challenges.request_deduplication import REQUEST_DEDUPLICATION_CHALLENGE
        cls.register(REQUEST_DEDUPLICATION_CHALLENGE)
        # 2. Rate Limiter (Token Bucket)
        from app.services.challenges.rate_limiter_token_bucket import RATE_LIMITER_CHALLENGE
        cls.register(RATE_LIMITER_CHALLENGE)
        # 3. LRU Cache with TTL
        from app.services.challenges.lru_cache_ttl import LRU_CACHE_CHALLENGE
        cls.register(LRU_CACHE_CHALLENGE)
        # 4. Circuit Breaker Pattern
        from app.services.challenges.circuit_breaker_pattern import CIRCUIT_BREAKER_CHALLENGE
        cls.register(CIRCUIT_BREAKER_CHALLENGE)

    @classmethod
    def reset_for_tests(cls) -> None:
        """Reset registry state for isolated unit testing."""
        cls._challenges.clear()
        cls._initialized = False
