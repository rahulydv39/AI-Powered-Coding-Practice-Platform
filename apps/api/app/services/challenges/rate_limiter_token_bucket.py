"""Challenge definition for 'Rate Limiter (Token Bucket)'.

A classic system design and backend engineering interview problem testing
concurrency primitives, time-based token refill mechanics, and boundary validation.
"""

from typing import Any, Dict, List

from app.schemas.review import KeyDecisionItem
from app.services.challenges.base import ChallengeDefinition

CHALLENGE_ID = "rate-limiter-token-bucket"
CHALLENGE_TITLE = "Rate Limiter (Token Bucket)"
CHALLENGE_DIFFICULTY = "Medium"
CATEGORY = "Distributed Systems"
TAGS = ["Rate Limiting", "Token Bucket", "Traffic Shaping", "Time-Series"]
ESTIMATED_MINUTES = 25
SHORT_SUMMARY = "Implement a token bucket rate limiter to regulate burst traffic and defend APIs against abuse."

CHALLENGE_DESCRIPTION = """### Problem Statement

High-throughput API gateways and web services must protect downstream resources against request spikes, client loops, and distributed denial-of-service attempts. One of the most ubiquitous and mathematically sound rate-limiting algorithms is the **Token Bucket**.

Your task is to implement the `TokenBucketRateLimiter` class in Python.

#### Specification & Mechanics

1. **Initialization**:
   - `__init__(self, capacity: float, refill_rate_per_sec: float)`
   - The bucket begins completely full with `capacity` tokens.
   - Both `capacity` and `refill_rate_per_sec` must be strictly greater than zero (`> 0`). Otherwise, raise `ValueError`.

2. **Request Consumption**:
   - `allow_request(self, tokens_requested: float = 1.0, current_time: Optional[float] = None) -> bool`
   - If `current_time` is omitted or `None`, use `time.time()`.
   - If `tokens_requested <= 0`, raise `ValueError`.
   - Before evaluating availability, calculate elapsed time since the last refill and add `elapsed_seconds * refill_rate_per_sec` tokens to the bucket.
   - The token count must never exceed `capacity` (cap at `capacity`).
   - If the bucket has at least `tokens_requested` tokens:
     - Deduct `tokens_requested` from the bucket.
     - Record the updated timestamp.
     - Return `True` (request permitted).
   - If the bucket has fewer than `tokens_requested` tokens:
     - Do not deduct tokens.
     - Record the updated timestamp.
     - Return `False` (request throttled).

#### Expected Signature
```python
from typing import Optional

class TokenBucketRateLimiter:
    def __init__(self, capacity: float, refill_rate_per_sec: float):
        ...

    def allow_request(self, tokens_requested: float = 1.0, current_time: Optional[float] = None) -> bool:
        ...
```
"""

STARTER_CODE = '''import time
from typing import Optional

class TokenBucketRateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(self, capacity: float, refill_rate_per_sec: float):
        if capacity <= 0 or refill_rate_per_sec <= 0:
            # BUG: Returns None instead of raising ValueError
            return

        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.tokens = float(capacity)
        self.last_refill_timestamp = time.time()

    def allow_request(self, tokens_requested: float = 1.0, current_time: Optional[float] = None) -> bool:
        if tokens_requested <= 0:
            return False  # BUG: Should raise ValueError

        now = current_time if current_time is not None else time.time()
        elapsed = now - self.last_refill_timestamp

        # BUG: Uses integer division, discarding fractional elapsed seconds!
        tokens_to_add = int(elapsed) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)

        # BUG: Forgets to update self.last_refill_timestamp!
        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            return True

        return False
'''

REFERENCE_SOLUTION = '''import time
from typing import Optional

class TokenBucketRateLimiter:
    """Production reference implementation of Token Bucket Rate Limiter."""

    def __init__(self, capacity: float, refill_rate_per_sec: float):
        if capacity <= 0:
            raise ValueError("capacity must be strictly positive")
        if refill_rate_per_sec <= 0:
            raise ValueError("refill_rate_per_sec must be strictly positive")

        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.tokens = float(capacity)
        self.last_refill_timestamp = time.time()

    def allow_request(self, tokens_requested: float = 1.0, current_time: Optional[float] = None) -> bool:
        if tokens_requested <= 0:
            raise ValueError("tokens_requested must be strictly positive")

        now = current_time if current_time is not None else time.time()
        elapsed = max(0.0, now - self.last_refill_timestamp)

        # Continuous floating-point token refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill_timestamp = now

        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            return True

        return False
'''

PUBLIC_TEST_SUMMARIES: List[Dict[str, str]] = [
    {
        "id": "initial_burst",
        "name": "Initial burst capacity allowed",
        "description": "Bucket starts completely full and accepts requests up to capacity.",
    },
    {
        "id": "exhaustion_rejection",
        "name": "Depleted bucket throttles requests",
        "description": "Once tokens are exhausted, subsequent calls return False without deducting negative tokens.",
    },
    {
        "id": "time_based_refill",
        "name": "Continuous time-based token refill",
        "description": "Elapsed time correctly adds tokens according to the refill rate per second.",
    },
    {
        "id": "capacity_clamp",
        "name": "Capacity boundary clamping",
        "description": "Tokens never accumulate beyond the configured maximum capacity.",
    },
    {
        "id": "input_validation",
        "name": "Parameter boundary validation",
        "description": "Raises ValueError when capacity, rate, or tokens_requested is non-positive.",
    },
]

TEST_HARNESS_CODE = '''import json
import sys
import time

def run_tests():
    test_results = []

    try:
        from solution import TokenBucketRateLimiter
    except SyntaxError as e:
        output = {
            "status": "error",
            "error": f"SyntaxError in your code: {e.msg} (line {e.lineno})",
            "tests": [],
        }
        print(json.dumps(output))
        sys.exit(0)
    except Exception as e:
        output = {
            "status": "error",
            "error": f"Import/runtime error loading solution: {type(e).__name__}: {str(e)}",
            "tests": [],
        }
        print(json.dumps(output))
        sys.exit(0)

    # Test 1: Initial burst capacity allowed
    t0 = time.time()
    try:
        limiter = TokenBucketRateLimiter(capacity=3.0, refill_rate_per_sec=1.0)
        t_base = 1000.0
        r1 = limiter.allow_request(1.0, current_time=t_base)
        r2 = limiter.allow_request(1.0, current_time=t_base)
        r3 = limiter.allow_request(1.0, current_time=t_base)
        if not (r1 and r2 and r3):
            raise AssertionError(f"Expected 3 initial requests to succeed, got {[r1, r2, r3]}")
        test_results.append({
            "name": "Initial burst capacity allowed",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Initial burst capacity allowed",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 2: Depleted bucket throttles requests
    t0 = time.time()
    try:
        limiter = TokenBucketRateLimiter(capacity=2.0, refill_rate_per_sec=1.0)
        t_base = 2000.0
        limiter.allow_request(2.0, current_time=t_base)
        rejected = limiter.allow_request(1.0, current_time=t_base)
        if rejected is not False:
            raise AssertionError(f"Expected request to be rejected when bucket is empty, got {rejected}")
        test_results.append({
            "name": "Depleted bucket throttles requests",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Depleted bucket throttles requests",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 3: Continuous time-based token refill
    t0 = time.time()
    try:
        limiter = TokenBucketRateLimiter(capacity=2.0, refill_rate_per_sec=2.0)
        t_base = 3000.0
        limiter.allow_request(2.0, current_time=t_base) # Empty bucket
        # Advance time by 0.5 seconds -> refills 0.5 * 2 = 1.0 token
        r_after_half_sec = limiter.allow_request(1.0, current_time=t_base + 0.5)
        if r_after_half_sec is not True:
            raise AssertionError("Expected 1 token to refill after 0.5s at 2 tokens/sec")
        # Try immediately again -> should fail
        r_immediate = limiter.allow_request(1.0, current_time=t_base + 0.5)
        if r_immediate is not False:
            raise AssertionError("Expected second request at 0.5s to be rejected")
        test_results.append({
            "name": "Continuous time-based token refill",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Continuous time-based token refill",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 4: Capacity boundary clamping
    t0 = time.time()
    try:
        limiter = TokenBucketRateLimiter(capacity=5.0, refill_rate_per_sec=10.0)
        t_base = 4000.0
        # Wait 100 seconds (would generate 1000 tokens without clamping)
        # Should be clamped to 5.0
        # Consume 5 tokens -> succeed
        s1 = limiter.allow_request(5.0, current_time=t_base + 100.0)
        # 6th token -> fail
        s2 = limiter.allow_request(1.0, current_time=t_base + 100.0)
        if not s1 or s2:
            raise AssertionError(f"Expected tokens to clamp at capacity=5.0. Results: s1={s1}, s2={s2}")
        test_results.append({
            "name": "Capacity boundary clamping",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Capacity boundary clamping",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 5: Parameter boundary validation
    t0 = time.time()
    try:
        # Invalid capacity
        cap_val_err = False
        try:
            TokenBucketRateLimiter(capacity=0, refill_rate_per_sec=1.0)
        except ValueError:
            cap_val_err = True
        if not cap_val_err:
            raise AssertionError("Expected ValueError for capacity <= 0")

        # Invalid refill rate
        rate_val_err = False
        try:
            TokenBucketRateLimiter(capacity=5.0, refill_rate_per_sec=-1.0)
        except ValueError:
            rate_val_err = True
        if not rate_val_err:
            raise AssertionError("Expected ValueError for refill_rate <= 0")

        # Invalid tokens requested
        lim = TokenBucketRateLimiter(capacity=5.0, refill_rate_per_sec=1.0)
        req_val_err = False
        try:
            lim.allow_request(0.0)
        except ValueError:
            req_val_err = True
        if not req_val_err:
            raise AssertionError("Expected ValueError for tokens_requested <= 0")

        test_results.append({
            "name": "Parameter boundary validation",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Parameter boundary validation",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    passed_count = sum(1 for t in test_results if t["passed"])
    output = {
        "status": "passed" if passed_count == len(test_results) else "failed",
        "passed": passed_count,
        "failed": len(test_results) - passed_count,
        "total": len(test_results),
        "tests": test_results,
        "error": None,
    }
    print(json.dumps(output))

if __name__ == "__main__":
    run_tests()
'''

KEY_DECISIONS: List[KeyDecisionItem] = [
    KeyDecisionItem(
        id="continuous_refill",
        title="Lazy Fractional Time-Delta Refill",
        explanation=(
            "Rather than running a continuous background timer thread, the algorithm calculates tokens dynamically "
            "on arrival using `elapsed = now - last_refill_timestamp`."
        ),
        why_it_matters=(
            "Background threads consume CPU, introduce thread synchronization overhead, and do not scale to millions "
            "of buckets. Lazy evaluation computes exact token state in O(1) time only when a request actually arrives."
        ),
    ),
    KeyDecisionItem(
        id="capacity_capping",
        title="Upper-Bound Clamp (`min(capacity, tokens + refill)`)",
        explanation=(
            "Tokens accumulate up to `self.capacity` and no further, regardless of how long the bucket sat idle."
        ),
        why_it_matters=(
            "Without clamping, idle buckets would accumulate infinite tokens, permitting an unbounded burst that "
            "would overwhelm downstream services upon resumption."
        ),
    ),
    KeyDecisionItem(
        id="timestamp_update_on_check",
        title="Deterministic Timestamp Refresh on Every Evaluation",
        explanation=(
            "The `last_refill_timestamp` updates to `now` whenever requests are evaluated, keeping elapsed intervals accurate."
        ),
        why_it_matters=(
            "Failing to update timestamps when requests are rejected causes elapsed time to compound incorrectly, "
            "leading to premature bursts or starved clients."
        ),
    ),
]

LEARNING_TAKEAWAYS: List[str] = [
    "Token Bucket vs Leaky Bucket: Token bucket permits bursts up to capacity while enforcing an average rate; leaky bucket enforces a constant outflow rate without burst allowance.",
    "Distributed Rate Limiting: In production microservices, this algorithm is implemented with Redis Lua scripts to maintain atomicity across horizontally scaled API gateway instances.",
    "Graceful Degradation: When a rate limiter returns False, HTTP 429 Too Many Requests should be paired with a Retry-After header calculated from (tokens_needed - current_tokens) / refill_rate.",
]

RATE_LIMITER_CHALLENGE = ChallengeDefinition(
    id=CHALLENGE_ID,
    title=CHALLENGE_TITLE,
    difficulty=CHALLENGE_DIFFICULTY,
    category=CATEGORY,
    tags=TAGS,
    estimated_minutes=ESTIMATED_MINUTES,
    short_summary=SHORT_SUMMARY,
    description=CHALLENGE_DESCRIPTION,
    starter_code=STARTER_CODE,
    reference_solution=REFERENCE_SOLUTION,
    test_cases=PUBLIC_TEST_SUMMARIES,
    test_harness_code=TEST_HARNESS_CODE,
    key_decisions=KEY_DECISIONS,
    learning_takeaways=LEARNING_TAKEAWAYS,
)
