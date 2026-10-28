"""Challenge definition for 'Circuit Breaker Pattern'.

A critical reliability engineering problem testing state-machine design,
resilient distributed systems thinking, and deterministic failure isolation.
"""

from typing import Any, Dict, List

from app.schemas.review import KeyDecisionItem
from app.services.challenges.base import ChallengeDefinition

CHALLENGE_ID = "circuit-breaker-pattern"
CHALLENGE_TITLE = "Circuit Breaker Pattern"
CHALLENGE_DIFFICULTY = "Hard"
CATEGORY = "Reliability Engineering"
TAGS = ["State Machine", "Fault Tolerance", "Circuit Breaker", "Resilience"]
ESTIMATED_MINUTES = 35
SHORT_SUMMARY = "Implement a state-machine circuit breaker to prevent cascading failures in distributed systems."

CHALLENGE_DESCRIPTION = """### Problem Statement

Distributed microservices and networked systems frequently experience transient outages, latency spikes, or complete downstream server failures. Without protection, upstream clients continue hammering the failing service, causing cascading thread exhaustion, resource depletion, and catastrophic outages.

The **Circuit Breaker** pattern acts as an automated safety switch that detects remote failures and prevents further calls to a struggling downstream dependency until it has recovered.

Your task is to implement the `CircuitBreaker` class in Python.

#### State Machine Mechanics

The circuit breaker operates across three distinct states:

```
        +-----------------------------------+
        |                                   |
        v                                   | (recovery_timeout elapsed)
   +----------+   failure_threshold    +----+-----+
   |  CLOSED  | ---------------------> |   OPEN   |
   +----------+      reached           +----------+
        ^                                   |
        |                                   | (trial call allowed)
        |                                   v
        |      success_threshold       +----+-----+
        +----------------------------- | HALF_OPEN|
               consecutive successes   +----------+
                                            |
                                            | (any failure)
                                            +-------------> trips back to OPEN
```

1. **`CLOSED` (Normal Operation)**:
   - Remote calls execute normally.
   - If a call succeeds, the consecutive failure counter resets to `0`.
   - If a call raises an exception, the failure counter increments.
   - When consecutive failures reach `failure_threshold`:
     - The circuit transitions to `OPEN`.
     - The transition timestamp is recorded.
   - The raised exception is re-raised to the caller.

2. **`OPEN` (Short-Circuit / Failing)**:
   - When a call is attempted, check if `recovery_timeout_sec` has elapsed since the transition to `OPEN`.
   - If time has **not** elapsed:
     - Do **not** execute the downstream function.
     - Immediately raise `CircuitBreakerOpenException("Circuit breaker is OPEN")`.
   - If `recovery_timeout_sec` **has** elapsed:
     - The circuit transitions to `HALF_OPEN`.
     - Proceed to evaluate the call under `HALF_OPEN` rules.

3. **`HALF_OPEN` (Canary / Trial)**:
   - The breaker allows trial requests to probe whether the remote dependency has recovered.
   - If a call **succeeds**:
     - Increment the consecutive success counter.
     - If consecutive successes reach `half_open_success_threshold`:
       - The circuit transitions back to `CLOSED`.
       - Failure and success counters reset to `0`.
     - Return the result to the caller.
   - If a call **fails** (raises any exception):
     - The circuit immediately transitions back to `OPEN`.
     - The transition timestamp updates to the current time.
     - The success counter resets to `0`.
     - The raised exception is re-raised to the caller.

#### Constructor & Method Specification

```python
class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 5.0,
        half_open_success_threshold: int = 2,
    ) -> None:
        ...

    @property
    def state(self) -> str:
        \"\"\"Returns 'CLOSED', 'OPEN', or 'HALF_OPEN'.\"\"\"
        ...

    def call(self, func: Callable[[], T], current_time: Optional[float] = None) -> T:
        \"\"\"Executes func() governed by the circuit breaker state machine.

        Args:
            func: A zero-argument callable to execute.
            current_time: Simulated epoch seconds for testing. Defaults to time.time().

        Raises:
            CircuitBreakerOpenException: If the circuit is OPEN and timeout has not elapsed.
            Exception: Whatever exception func() raises if the call fails.
        \"\"\"
        ...
```

#### Validation & Constraints
- `failure_threshold` must be an integer `>= 1`. Otherwise raise `ValueError`.
- `recovery_timeout_sec` must be a float/int `> 0`. Otherwise raise `ValueError`.
- `half_open_success_threshold` must be an integer `>= 1`. Otherwise raise `ValueError`.
- If `current_time` is omitted or `None`, default to `time.time()`.
"""

STARTER_CODE = '''import time
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class CircuitBreakerOpenException(Exception):
    """Raised when an execution is attempted while the circuit breaker is OPEN."""
    pass


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 5.0,
        half_open_success_threshold: int = 2,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout_sec <= 0:
            raise ValueError("recovery_timeout_sec must be > 0")
        if half_open_success_threshold < 1:
            raise ValueError("half_open_success_threshold must be >= 1")

        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = float(recovery_timeout_sec)
        self.half_open_success_threshold = half_open_success_threshold

        self._state = "CLOSED"
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_state_change: float = 0.0

    @property
    def state(self) -> str:
        return self._state

    def call(self, func: Callable[[], T], current_time: Optional[float] = None) -> T:
        now = time.time() if current_time is None else float(current_time)

        # BUG: Starter implementation does not evaluate state transitions properly
        # and resets state prematurely on any success.
        try:
            result = func()
            self._consecutive_failures = 0
            self._state = "CLOSED"
            return result
        except Exception as exc:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._state = "OPEN"
                self._last_state_change = now
            raise exc
'''

REFERENCE_SOLUTION = '''import time
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class CircuitBreakerOpenException(Exception):
    """Raised when an execution is attempted while the circuit breaker is OPEN."""
    pass


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 5.0,
        half_open_success_threshold: int = 2,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout_sec <= 0:
            raise ValueError("recovery_timeout_sec must be > 0")
        if half_open_success_threshold < 1:
            raise ValueError("half_open_success_threshold must be >= 1")

        self.failure_threshold = int(failure_threshold)
        self.recovery_timeout_sec = float(recovery_timeout_sec)
        self.half_open_success_threshold = int(half_open_success_threshold)

        self._state = "CLOSED"
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_state_change: float = 0.0

    @property
    def state(self) -> str:
        return self._state

    def call(self, func: Callable[[], T], current_time: Optional[float] = None) -> T:
        now = time.time() if current_time is None else float(current_time)

        # 1. State transition from OPEN -> HALF_OPEN on timeout
        if self._state == "OPEN":
            if (now - self._last_state_change) >= self.recovery_timeout_sec:
                self._state = "HALF_OPEN"
                self._consecutive_successes = 0
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")

        # 2. Execution under HALF_OPEN
        if self._state == "HALF_OPEN":
            try:
                result = func()
            except Exception as exc:
                self._state = "OPEN"
                self._last_state_change = now
                self._consecutive_successes = 0
                raise exc

            self._consecutive_successes += 1
            if self._consecutive_successes >= self.half_open_success_threshold:
                self._state = "CLOSED"
                self._consecutive_failures = 0
                self._consecutive_successes = 0
            return result

        # 3. Execution under CLOSED
        try:
            result = func()
        except Exception as exc:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._state = "OPEN"
                self._last_state_change = now
            raise exc

        self._consecutive_failures = 0
        return result
'''

PUBLIC_TEST_SUMMARIES: List[Dict[str, Any]] = [
    {
        "id": "test_closed_state_successful_execution",
        "name": "Closed State Normal Operation",
        "description": "Executes call successfully in CLOSED state, maintaining healthy status without tripping.",
    },
    {
        "id": "test_closed_to_open_transition_on_failure_threshold",
        "name": "Trip to OPEN on Consecutive Failures",
        "description": "Trips circuit to OPEN when failure threshold is reached and immediately blocks subsequent calls.",
    },
    {
        "id": "test_open_to_half_open_transition_after_timeout",
        "name": "Transition to HALF_OPEN after Timeout",
        "description": "Allows trial requests after recovery timeout elapses without permitting full traffic.",
    },
    {
        "id": "test_half_open_recovery_requires_success_threshold",
        "name": "Full Recovery Requires Success Threshold",
        "description": "Requires half_open_success_threshold consecutive successful calls before restoring CLOSED state.",
    },
    {
        "id": "test_half_open_immediate_reopen_on_failure",
        "name": "Immediate Re-Trip to OPEN on Trial Failure",
        "description": "Immediately aborts recovery and trips back to OPEN upon any failure in HALF_OPEN state.",
    },
]

TEST_HARNESS_CODE = '''import json
import time
import sys

def run_tests():
    from solution import CircuitBreaker, CircuitBreakerOpenException

    results = []

    # Test 1: Closed State Normal Operation
    t0 = time.perf_counter()
    try:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_sec=5.0)
        assert cb.state == "CLOSED", f"Expected CLOSED, got {cb.state}"
        res1 = cb.call(lambda: "hello", current_time=100.0)
        assert res1 == "hello", f"Expected 'hello', got {res1}"
        assert cb.state == "CLOSED"
        # Intermittent failure followed by success resets failure count
        try:
            cb.call(lambda: 1 / 0, current_time=101.0)
        except ZeroDivisionError:
            pass
        assert cb.state == "CLOSED"
        cb.call(lambda: "recovered", current_time=102.0)
        assert cb.state == "CLOSED"
        assert cb._consecutive_failures == 0
        d1 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Closed State Normal Operation", "passed": True, "message": None, "duration_ms": round(d1, 2)})
    except Exception as e:
        d1 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Closed State Normal Operation", "passed": False, "message": str(e), "duration_ms": round(d1, 2)})

    # Test 2: Trip to OPEN on Consecutive Failures
    t0 = time.perf_counter()
    try:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_sec=5.0)
        for i in range(2):
            try:
                cb.call(lambda: 1 / 0, current_time=100.0 + i)
            except ZeroDivisionError:
                pass
            assert cb.state == "CLOSED", f"Expected CLOSED after {i+1} failures, got {cb.state}"

        # 3rd failure trips the breaker
        try:
            cb.call(lambda: 1 / 0, current_time=103.0)
        except ZeroDivisionError:
            pass
        assert cb.state == "OPEN", f"Expected OPEN after 3 failures, got {cb.state}"

        # Subsequent call before timeout must raise CircuitBreakerOpenException without running func
        func_called = False
        def bad():
            nonlocal func_called
            func_called = True
            return "should not run"

        raised_open = False
        try:
            cb.call(bad, current_time=104.0)
        except CircuitBreakerOpenException:
            raised_open = True
        assert raised_open, "Expected CircuitBreakerOpenException while OPEN"
        assert not func_called, "Function was executed despite circuit being OPEN"
        d2 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Trip to OPEN on Consecutive Failures", "passed": True, "message": None, "duration_ms": round(d2, 2)})
    except Exception as e:
        d2 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Trip to OPEN on Consecutive Failures", "passed": False, "message": str(e), "duration_ms": round(d2, 2)})

    # Test 3: Transition to HALF_OPEN after Timeout
    t0 = time.perf_counter()
    try:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=5.0, half_open_success_threshold=2)
        # Trip it
        for _ in range(2):
            try:
                cb.call(lambda: 1 / 0, current_time=10.0)
            except ZeroDivisionError:
                pass
        assert cb.state == "OPEN"

        # At t=14.9 (4.9s elapsed < 5.0s), still OPEN
        try:
            cb.call(lambda: "ok", current_time=14.9)
            assert False, "Should have raised CircuitBreakerOpenException"
        except CircuitBreakerOpenException:
            pass

        # At t=15.0 (5.0s elapsed >= 5.0s), transitions to HALF_OPEN and allows call
        res = cb.call(lambda: "trial-1", current_time=15.0)
        assert res == "trial-1"
        assert cb.state == "HALF_OPEN", f"Expected HALF_OPEN after first success, got {cb.state}"
        d3 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Transition to HALF_OPEN after Timeout", "passed": True, "message": None, "duration_ms": round(d3, 2)})
    except Exception as e:
        d3 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Transition to HALF_OPEN after Timeout", "passed": False, "message": str(e), "duration_ms": round(d3, 2)})

    # Test 4: Full Recovery Requires Success Threshold
    t0 = time.perf_counter()
    try:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=5.0, half_open_success_threshold=3)
        # Trip to OPEN at t=10.0
        for _ in range(2):
            try:
                cb.call(lambda: 1 / 0, current_time=10.0)
            except ZeroDivisionError:
                pass
        assert cb.state == "OPEN"

        # Trial 1 at t=16.0 -> HALF_OPEN (1/3)
        cb.call(lambda: "t1", current_time=16.0)
        assert cb.state == "HALF_OPEN"

        # Trial 2 at t=16.5 -> HALF_OPEN (2/3)
        cb.call(lambda: "t2", current_time=16.5)
        assert cb.state == "HALF_OPEN"

        # Trial 3 at t=17.0 -> CLOSED (3/3 threshold reached)
        cb.call(lambda: "t3", current_time=17.0)
        assert cb.state == "CLOSED", f"Expected CLOSED after 3 successes, got {cb.state}"
        d4 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Full Recovery Requires Success Threshold", "passed": True, "message": None, "duration_ms": round(d4, 2)})
    except Exception as e:
        d4 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Full Recovery Requires Success Threshold", "passed": False, "message": str(e), "duration_ms": round(d4, 2)})

    # Test 5: Immediate Re-Trip to OPEN on Trial Failure
    t0 = time.perf_counter()
    try:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=5.0, half_open_success_threshold=3)
        # Trip to OPEN at t=10.0
        for _ in range(2):
            try:
                cb.call(lambda: 1 / 0, current_time=10.0)
            except ZeroDivisionError:
                pass
        assert cb.state == "OPEN"

        # Enter HALF_OPEN at t=15.5 with one success
        cb.call(lambda: "t1", current_time=15.5)
        assert cb.state == "HALF_OPEN"

        # Next call fails at t=16.0 -> immediately trips back to OPEN
        try:
            cb.call(lambda: 1 / 0, current_time=16.0)
        except ZeroDivisionError:
            pass
        assert cb.state == "OPEN", f"Expected OPEN after trial failure, got {cb.state}"

        # Must enforce a fresh 5-second recovery window from t=16.0
        # At t=19.0 (only 3.0s elapsed), must still be OPEN
        try:
            cb.call(lambda: "fast", current_time=19.0)
            assert False, "Should have raised CircuitBreakerOpenException"
        except CircuitBreakerOpenException:
            pass

        # At t=21.0 (5.0s elapsed from t=16.0), allowed again
        res = cb.call(lambda: "trial-again", current_time=21.0)
        assert res == "trial-again"
        assert cb.state == "HALF_OPEN"
        d5 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Immediate Re-Trip to OPEN on Trial Failure", "passed": True, "message": None, "duration_ms": round(d5, 2)})
    except Exception as e:
        d5 = (time.perf_counter() - t0) * 1000
        results.append({"name": "Immediate Re-Trip to OPEN on Trial Failure", "passed": False, "message": str(e), "duration_ms": round(d5, 2)})

    passed_count = sum(1 for r in results if r["passed"])
    failed_count = sum(1 for r in results if not r["passed"])
    status = "passed" if failed_count == 0 else "failed"

    output = {
        "status": status,
        "passed": passed_count,
        "failed": failed_count,
        "total": len(results),
        "tests": results,
        "error": None
    }
    print(json.dumps(output))

if __name__ == "__main__":
    run_tests()
'''

KEY_DECISIONS: List[KeyDecisionItem] = [
    KeyDecisionItem(
        id="explicit_three_state_machine",
        title="Explicit CLOSED / OPEN / HALF_OPEN State Machine",
        explanation=(
            "The circuit breaker is modeled as an explicit finite state machine with deterministic transitions "
            "between healthy execution (CLOSED), fail-fast isolation (OPEN), and canary probing (HALF_OPEN)."
        ),
        why_it_matters=(
            "Ad-hoc flags or naive counters fail to handle edge cases like failed recovery trials or partial recoveries, "
            "risking thrashing or continuous load against degraded downstream services."
        ),
    ),
    KeyDecisionItem(
        id="fail_fast_without_execution",
        title="Fail-Fast Short-Circuiting in OPEN State",
        explanation=(
            "When the circuit is OPEN and recovery timeout has not expired, calls are immediately aborted by raising "
            "`CircuitBreakerOpenException` without ever invoking the remote dependency callable."
        ),
        why_it_matters=(
            "This relieves struggling downstream dependencies from incoming request pressure, giving them time to recover, "
            "and eliminates thread blocking in the calling application."
        ),
    ),
    KeyDecisionItem(
        id="consecutive_trial_verification",
        title="Multi-Trial Canary Verification in HALF_OPEN",
        explanation=(
            "A single successful response during HALF_OPEN is insufficient to declare a service fully recovered; "
            "`half_open_success_threshold` consecutive successes must be observed before closing the circuit."
        ),
        why_it_matters=(
            "Fluctuating or flapping services often succeed intermittently before failing again under load. Requiring "
            "consecutive successful probes prevents premature circuit closure."
        ),
    ),
]

LEARNING_TAKEAWAYS: List[str] = [
    "Preventing Cascading Outages: In distributed architectures (e.g. Netflix Hystrix, Resilience4j, Envoy), circuit breakers isolate failures so an auxiliary service outage doesn't bring down user-facing flows.",
    "Fail-Fast vs Fallbacks: Circuit breakers pair naturally with fallback strategies (e.g. serving stale cache data, default recommendations, or cached customer profiles) when CircuitBreakerOpenException is caught.",
    "Deterministic Testing with Virtual Time: Injecting simulated timestamps (current_time) enables rigorous, zero-wait unit testing of complex time-dependent state machines without brittle sleep() calls.",
]

CIRCUIT_BREAKER_CHALLENGE = ChallengeDefinition(
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
