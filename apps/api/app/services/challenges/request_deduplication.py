"""Challenge definition for 'Request Deduplication'.

Contains the public problem statement, starter code with intentional bug,
and server-side hidden test harness with reference verification.
"""

from typing import Any, Dict, List

from app.schemas.review import KeyDecisionItem
from app.services.challenges.base import ChallengeDefinition

CHALLENGE_ID = "request-deduplication"
CHALLENGE_TITLE = "Request Deduplication"
CHALLENGE_DIFFICULTY = "Easy"
CATEGORY = "Distributed Systems"
TAGS = ["Idempotency", "State Management", "In-Memory Caching"]
ESTIMATED_MINUTES = 15
SHORT_SUMMARY = "Filter duplicate HTTP request identifiers to prevent duplicate execution in distributed systems."

CHALLENGE_DESCRIPTION = """### Problem Statement

In distributed web services, duplicate HTTP requests can occur due to network retries, client timeouts, or user double-clicks. Your task is to write a function that inspects incoming request identifiers and filters out duplicates.

#### Requirements
1. **First Occurrence**: The first time an identifier is seen, it must be accepted (return `True`) and recorded in `seen_ids`.
2. **Subsequent Occurrences**: Any subsequent request with an already-seen identifier must be rejected (return `False`).
3. **Independent Identifiers**: Different identifiers must be evaluated independently without interfering with each other.
4. **Input Validation**: If `request_id` is empty, whitespace-only, or not a string, the function must raise a `ValueError`.

#### Function Signature
```python
def process_request(request_id: str, seen_ids: set[str]) -> bool:
    ...
```

#### Parameters
- `request_id`: The unique string identifier for the incoming request.
- `seen_ids`: A Python set tracking identifiers already seen in the current session.

#### Returns
- `bool`: `True` if the request is accepted (first occurrence), or `False` if rejected (duplicate).

#### Raises
- `ValueError`: If `request_id` is not a non-empty string.
"""

STARTER_CODE = '''def process_request(request_id: str, seen_ids: set[str]) -> bool:
    """Process an incoming request identifier and reject duplicates.

    Requirements:
      - The first occurrence of an identifier is accepted (returns True).
      - Subsequent occurrences of the same identifier are rejected (returns False).
      - Different identifiers are processed independently.
      - Empty or whitespace-only input must raise ValueError.

    Parameters:
      request_id: The unique string identifier for the incoming request.
      seen_ids: A set tracking identifiers seen during the current session.

    Returns:
      bool: True if accepted (first occurrence), False if rejected (duplicate).

    Raises:
      ValueError: If request_id is empty, whitespace-only, or not a string.
    """
    if not isinstance(request_id, str) or not request_id.strip():
        # BUG: Currently returns False instead of raising ValueError
        return False

    if request_id in seen_ids:
        return False

    # BUG: Forgot to register request_id in seen_ids!
    return True
'''

# Server-side reference solution (NEVER returned to client)
REFERENCE_SOLUTION = '''def process_request(request_id: str, seen_ids: set[str]) -> bool:
    """Correct reference implementation."""
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")

    if request_id in seen_ids:
        return False

    seen_ids.add(request_id)
    return True
'''

# Public test case summaries shown in the UI
PUBLIC_TEST_SUMMARIES: List[Dict[str, str]] = [
    {
        "id": "first_request",
        "name": "First request accepted",
        "description": "The first occurrence of an identifier returns True and is stored in seen_ids.",
    },
    {
        "id": "duplicate_request",
        "name": "Duplicate request rejected",
        "description": "Subsequent calls with the same identifier return False.",
    },
    {
        "id": "independent_ids",
        "name": "Independent identifiers",
        "description": "Different identifiers are accepted independently and do not collide.",
    },
    {
        "id": "sequence_processing",
        "name": "Repeated sequence processing",
        "description": "A sequence of interleaved new and duplicate identifiers is filtered accurately.",
    },
    {
        "id": "empty_input_validation",
        "name": "Empty and invalid input validation",
        "description": "Raises ValueError when request_id is empty, whitespace-only, or not a string.",
    },
]

# Hidden test harness executed inside the isolated container
# Imports solution.py, runs the 5 deterministic test cases, and outputs structured JSON
TEST_HARNESS_CODE = '''import json
import sys
import time

def run_tests():
    test_results = []

    # 1. Import student code with syntax error handling
    try:
        from solution import process_request
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

    # Test 1: First request accepted
    t0 = time.time()
    try:
        seen = set()
        res = process_request("req-100", seen)
        if res is not True:
            raise AssertionError(f"Expected process_request('req-100', seen) to return True, got {res}")
        if "req-100" not in seen:
            raise AssertionError("Expected 'req-100' to be added to seen_ids set")
        test_results.append({
            "name": "First request accepted",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "First request accepted",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 2: Duplicate request rejected
    t0 = time.time()
    try:
        seen = set()
        first_res = process_request("req-200", seen)
        second_res = process_request("req-200", seen)
        if first_res is not True:
            raise AssertionError(f"First request should return True, got {first_res}")
        if second_res is not False:
            raise AssertionError(f"Duplicate request should return False, got {second_res}")
        test_results.append({
            "name": "Duplicate request rejected",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Duplicate request rejected",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 3: Independent identifiers
    t0 = time.time()
    try:
        seen = set()
        res_a = process_request("id-alpha", seen)
        res_b = process_request("id-beta", seen)
        if res_a is not True or res_b is not True:
            raise AssertionError("Expected both unique identifiers 'id-alpha' and 'id-beta' to return True")
        if process_request("id-alpha", seen) is not False:
            raise AssertionError("Expected second call for 'id-alpha' to return False")
        if process_request("id-beta", seen) is not False:
            raise AssertionError("Expected second call for 'id-beta' to return False")
        test_results.append({
            "name": "Independent identifiers",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Independent identifiers",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 4: Repeated sequence processing
    t0 = time.time()
    try:
        seen = set()
        sequence = ["order-1", "order-2", "order-1", "order-3", "order-2", "order-1"]
        expected = [True, True, False, True, False, False]
        actual = [process_request(item, seen) for item in sequence]
        if actual != expected:
            raise AssertionError(f"Sequence processing mismatch. Expected {expected}, got {actual}")
        test_results.append({
            "name": "Repeated sequence processing",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Repeated sequence processing",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 5: Empty and invalid input validation
    t0 = time.time()
    try:
        seen = set()
        # Empty string
        empty_raised = False
        try:
            process_request("", seen)
        except ValueError:
            empty_raised = True
        if not empty_raised:
            raise AssertionError("Expected ValueError when request_id is empty string ''")

        # Whitespace-only string
        ws_raised = False
        try:
            process_request("   \\t\\n  ", seen)
        except ValueError:
            ws_raised = True
        if not ws_raised:
            raise AssertionError("Expected ValueError when request_id is whitespace-only string")

        test_results.append({
            "name": "Empty and invalid input validation",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Empty and invalid input validation",
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

REQUEST_DEDUPLICATION_CHALLENGE = ChallengeDefinition(
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
