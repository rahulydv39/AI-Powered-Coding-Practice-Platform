"""In-memory client rate limiter for AI Assistant endpoints.

LIMITATIONS:
- This is an in-memory sliding window rate limiter designed for local MVP development.
- In a multi-worker or multi-instance production environment, state is not shared;
  a shared cache (e.g., Redis) and centralized API gateway controls must be used.
"""

import time
from collections import defaultdict
from typing import Dict, List

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter tracking client IP addresses."""

    def __init__(self, requests_per_minute: int = 10):
        self.limit = requests_per_minute
        self.window_seconds = 60.0
        self._history: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request) -> None:
        """Check if request exceeds rate limit.

        SECURITY NOTE:
        Uses `request.client.host` (the direct socket IP) to prevent IP spoofing
        via arbitrary client-supplied `X-Forwarded-For` headers in local development.
        """
        settings = get_settings()
        limit = getattr(settings, "AI_RATE_LIMIT_PER_MINUTE", self.limit)

        client_ip = request.client.host if request.client else "unknown_client"
        now = time.time()
        window_start = now - self.window_seconds

        # Prune older entries
        timestamps = [ts for ts in self._history[client_ip] if ts > window_start]
        self._history[client_ip] = timestamps

        if len(timestamps) >= limit:
            retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please wait {retry_after}s before requesting AI assistance again.",
                headers={"Retry-After": str(retry_after)},
            )

        self._history[client_ip].append(now)


# Default singleton instance
rate_limiter = InMemoryRateLimiter()


def check_ai_rate_limit(request: Request) -> None:
    """Dependency callable for FastAPI routes."""
    rate_limiter.check(request)
