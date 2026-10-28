"""Challenge definition for 'LRU Cache with TTL'.

A fundamental software engineering interview problem combining hash-map lookups,
recency ordering (LRU), and temporal expiration (TTL).
"""

from typing import Any, Dict, List

from app.schemas.review import KeyDecisionItem
from app.services.challenges.base import ChallengeDefinition

CHALLENGE_ID = "lru-cache-ttl"
CHALLENGE_TITLE = "LRU Cache with TTL"
CHALLENGE_DIFFICULTY = "Medium"
CATEGORY = "Data Structures"
TAGS = ["LRU Cache", "Hash Map", "Doubly Linked List", "TTL Eviction", "Memory Management"]
ESTIMATED_MINUTES = 30
SHORT_SUMMARY = "Build an in-memory key-value cache combining Least Recently Used eviction with time-to-live expiration."

CHALLENGE_DESCRIPTION = """### Problem Statement

In memory-constrained backend systems, caching hot data accelerates read throughput. However, caches must balance two distinct eviction pressures: **temporal freshness** (evicting stale items after a Time-To-Live duration) and **capacity constraints** (evicting the Least Recently Used item when memory is exhausted).

Your task is to implement the `LRUCacheTTL` class in Python.

#### Specification & Mechanics

1. **Initialization**:
   - `__init__(self, capacity: int, default_ttl_sec: float)`
   - `capacity` must be an integer strictly greater than zero (`> 0`). Otherwise, raise `ValueError`.
   - `default_ttl_sec` must be a float strictly greater than zero (`> 0`). Otherwise, raise `ValueError`.

2. **Reading Values**:
   - `get(self, key: str, current_time: Optional[float] = None) -> Optional[Any]`
   - If `current_time` is omitted or `None`, use `time.time()`.
   - If `key` is not present, return `None`.
   - If `key` is expired (`current_time >= entry_expiry`), remove it from the cache and return `None`.
   - If `key` is present and valid, mark it as **most recently used** and return its value.

3. **Writing Values**:
   - `set(self, key: str, value: Any, ttl_sec: Optional[float] = None, current_time: Optional[float] = None) -> None`
   - If `ttl_sec` is provided, it must be `> 0` (otherwise raise `ValueError`). If omitted, use `default_ttl_sec`.
   - If `key` already exists, update its value, recalculate its expiration, and mark it as most recently used.
   - If `key` is new:
     - First, purge any expired entries to free capacity.
     - If the cache is still at `capacity`, evict the **least recently used** item.
     - Insert the new key-value pair marked as most recently used.

4. **Active Size**:
   - `size(self, current_time: Optional[float] = None) -> int`
   - Returns the count of non-expired entries currently in the cache.

#### Expected Signature
```python
from typing import Any, Optional

class LRUCacheTTL:
    def __init__(self, capacity: int, default_ttl_sec: float):
        ...

    def get(self, key: str, current_time: Optional[float] = None) -> Optional[Any]:
        ...

    def set(self, key: str, value: Any, ttl_sec: Optional[float] = None, current_time: Optional[float] = None) -> None:
        ...

    def size(self, current_time: Optional[float] = None) -> int:
        ...
```
"""

STARTER_CODE = '''import time
from typing import Any, Optional
from collections import OrderedDict

class LRUCacheTTL:
    """Least Recently Used Cache with TTL expiration."""

    def __init__(self, capacity: int, default_ttl_sec: float):
        if capacity <= 0 or default_ttl_sec <= 0:
            # BUG: Returns None instead of raising ValueError
            return

        self.capacity = capacity
        self.default_ttl = float(default_ttl_sec)
        # Dictionary storing key -> (value, expire_at)
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str, current_time: Optional[float] = None) -> Optional[Any]:
        now = current_time if current_time is not None else time.time()
        if key not in self.cache:
            return None

        val, expire_at = self.cache[key]
        if now >= expire_at:
            del self.cache[key]
            return None

        # BUG: Forgets to move accessed key to end of OrderedDict (recency order broken)!
        return val

    def set(self, key: str, value: Any, ttl_sec: Optional[float] = None, current_time: Optional[float] = None) -> None:
        now = current_time if current_time is not None else time.time()
        ttl = float(ttl_sec) if ttl_sec is not None else self.default_ttl
        if ttl <= 0:
            return  # BUG: Should raise ValueError

        expire_at = now + ttl

        if key in self.cache:
            self.cache[key] = (value, expire_at)
            self.cache.move_to_end(key)
            return

        # BUG: Evicts immediately without checking if any existing items are already expired!
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)

        self.cache[key] = (value, expire_at)

    def size(self, current_time: Optional[float] = None) -> int:
        now = current_time if current_time is not None else time.time()
        # Returns raw dict length without filtering out expired items
        return len(self.cache)
'''

REFERENCE_SOLUTION = '''import time
from typing import Any, Optional
from collections import OrderedDict

class LRUCacheTTL:
    """Production reference implementation of LRU Cache with TTL."""

    def __init__(self, capacity: int, default_ttl_sec: float):
        if capacity <= 0:
            raise ValueError("capacity must be strictly positive")
        if default_ttl_sec <= 0:
            raise ValueError("default_ttl_sec must be strictly positive")

        self.capacity = int(capacity)
        self.default_ttl = float(default_ttl_sec)
        # key -> (value, expire_at) with OrderedDict preserving LRU order
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def _purge_expired(self, now: float) -> None:
        """Purge all expired entries."""
        expired_keys = [k for k, (_, exp) in self.cache.items() if now >= exp]
        for k in expired_keys:
            del self.cache[k]

    def get(self, key: str, current_time: Optional[float] = None) -> Optional[Any]:
        now = current_time if current_time is not None else time.time()
        if key not in self.cache:
            return None

        value, expire_at = self.cache[key]
        if now >= expire_at:
            del self.cache[key]
            return None

        # Mark key as most recently used
        self.cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl_sec: Optional[float] = None, current_time: Optional[float] = None) -> None:
        now = current_time if current_time is not None else time.time()
        ttl = float(ttl_sec) if ttl_sec is not None else self.default_ttl
        if ttl <= 0:
            raise ValueError("ttl_sec must be strictly positive")

        expire_at = now + ttl

        if key in self.cache:
            self.cache[key] = (value, expire_at)
            self.cache.move_to_end(key)
            return

        # Purge expired items first to reclaim capacity
        self._purge_expired(now)

        # Evict least recently used if still full
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)

        self.cache[key] = (value, expire_at)

    def size(self, current_time: Optional[float] = None) -> int:
        now = current_time if current_time is not None else time.time()
        return sum(1 for _, exp in self.cache.values() if now < exp)
'''

PUBLIC_TEST_SUMMARIES: List[Dict[str, str]] = [
    {
        "id": "basic_operations",
        "name": "Basic set and get retrieval",
        "description": "Stored keys can be retrieved accurately before expiration.",
    },
    {
        "id": "lru_eviction",
        "name": "Least recently used eviction",
        "description": "When capacity is exceeded, the least recently used key is evicted.",
    },
    {
        "id": "get_updates_recency",
        "name": "Reading a key refreshes recency",
        "description": "Calling get() marks an item as recently used and protects it from eviction.",
    },
    {
        "id": "ttl_expiration",
        "name": "Time-to-live lazy expiration",
        "description": "Expired keys return None and do not count toward active size.",
    },
    {
        "id": "boundary_validation",
        "name": "Capacity and TTL boundary validation",
        "description": "Raises ValueError for non-positive capacity or TTL values.",
    },
]

TEST_HARNESS_CODE = '''import json
import sys
import time

def run_tests():
    test_results = []

    try:
        from solution import LRUCacheTTL
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

    # Test 1: Basic set and get retrieval
    t0 = time.time()
    try:
        cache = LRUCacheTTL(capacity=3, default_ttl_sec=10.0)
        t_base = 100.0
        cache.set("a", 1, current_time=t_base)
        cache.set("b", 2, current_time=t_base)
        val_a = cache.get("a", current_time=t_base)
        val_b = cache.get("b", current_time=t_base)
        val_c = cache.get("c", current_time=t_base)
        if val_a != 1 or val_b != 2 or val_c is not None:
            raise AssertionError(f"Expected a=1, b=2, c=None. Got a={val_a}, b={val_b}, c={val_c}")
        test_results.append({
            "name": "Basic set and get retrieval",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Basic set and get retrieval",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 2: Least recently used eviction
    t0 = time.time()
    try:
        cache = LRUCacheTTL(capacity=2, default_ttl_sec=100.0)
        t_base = 200.0
        cache.set("x", 10, current_time=t_base)
        cache.set("y", 20, current_time=t_base)
        # Insert 3rd item "z" -> should evict "x" (the oldest/least recently used)
        cache.set("z", 30, current_time=t_base)
        if cache.get("x", current_time=t_base) is not None:
            raise AssertionError("Expected key 'x' to be evicted when capacity=2 was exceeded")
        if cache.get("y", current_time=t_base) != 20 or cache.get("z", current_time=t_base) != 30:
            raise AssertionError("Expected keys 'y' and 'z' to remain in cache")
        test_results.append({
            "name": "Least recently used eviction",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Least recently used eviction",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 3: Reading a key refreshes recency
    t0 = time.time()
    try:
        cache = LRUCacheTTL(capacity=2, default_ttl_sec=100.0)
        t_base = 300.0
        cache.set("k1", 100, current_time=t_base)
        cache.set("k2", 200, current_time=t_base)
        # Access k1 -> now k2 is the least recently used!
        cache.get("k1", current_time=t_base)
        # Set k3 -> should evict k2, NOT k1!
        cache.set("k3", 300, current_time=t_base)
        if cache.get("k1", current_time=t_base) != 100:
            raise AssertionError("Expected 'k1' to remain because get() marked it as recently used")
        if cache.get("k2", current_time=t_base) is not None:
            raise AssertionError("Expected 'k2' to be evicted as least recently used")
        test_results.append({
            "name": "Reading a key refreshes recency",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Reading a key refreshes recency",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 4: Time-to-live lazy expiration
    t0 = time.time()
    try:
        cache = LRUCacheTTL(capacity=5, default_ttl_sec=5.0)
        t_base = 400.0
        cache.set("short_lived", "alpha", ttl_sec=2.0, current_time=t_base)
        cache.set("long_lived", "beta", ttl_sec=10.0, current_time=t_base)

        # At t_base + 3.0s: short_lived is expired, long_lived is valid
        if cache.get("short_lived", current_time=t_base + 3.0) is not None:
            raise AssertionError("Expected 'short_lived' to return None after its 2s TTL expired")
        if cache.get("long_lived", current_time=t_base + 3.0) != "beta":
            raise AssertionError("Expected 'long_lived' to remain valid before its 10s TTL")
        if cache.size(current_time=t_base + 3.0) != 1:
            raise AssertionError(f"Expected active size=1 at t+3s, got {cache.size(t_base + 3.0)}")
        test_results.append({
            "name": "Time-to-live lazy expiration",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Time-to-live lazy expiration",
            "passed": False,
            "message": f"{type(e).__name__}: {str(e)}",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    # Test 5: Capacity and TTL boundary validation
    t0 = time.time()
    try:
        # Invalid capacity
        cap_err = False
        try:
            LRUCacheTTL(capacity=0, default_ttl_sec=5.0)
        except ValueError:
            cap_err = True
        if not cap_err:
            raise AssertionError("Expected ValueError for capacity <= 0")

        # Invalid default TTL
        ttl_err = False
        try:
            LRUCacheTTL(capacity=5, default_ttl_sec=0.0)
        except ValueError:
            ttl_err = True
        if not ttl_err:
            raise AssertionError("Expected ValueError for default_ttl <= 0")

        # Invalid item TTL
        c = LRUCacheTTL(capacity=5, default_ttl_sec=5.0)
        set_err = False
        try:
            c.set("key", "val", ttl_sec=-2.0)
        except ValueError:
            set_err = True
        if not set_err:
            raise AssertionError("Expected ValueError for set(..., ttl_sec <= 0)")

        test_results.append({
            "name": "Capacity and TTL boundary validation",
            "passed": True,
            "message": None,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        test_results.append({
            "name": "Capacity and TTL boundary validation",
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
        id="ordered_dict_recency",
        title="O(1) Recency Tracking via `OrderedDict.move_to_end`",
        explanation=(
            "Using `collections.OrderedDict` provides average O(1) hash lookups and O(1) linked-list pointer updates "
            "to reposition keys to the end whenever read or written."
        ),
        why_it_matters=(
            "A standard array or list requires O(N) linear scans to update positions, causing cache latency to grow "
            "linearly with capacity."
        ),
    ),
    KeyDecisionItem(
        id="lazy_ttl_eviction",
        title="Lazy Expiration on Access with Reclaim on Capacity",
        explanation=(
            "Expired keys are invalidated upon `get()` access and purged prior to new insertions before evicting unexpired items."
        ),
        why_it_matters=(
            "Prevents premature eviction of live data when space is occupied by dead entries whose TTL has passed."
        ),
    ),
    KeyDecisionItem(
        id="recency_on_read",
        title="Move to MRU on Successful Read (`get`)",
        explanation=(
            "`get()` must mark the key as most recently used via `move_to_end()` to preserve hot keys from being dropped."
        ),
        why_it_matters=(
            "If only `set()` updates recency, a frequently read item will stay at the front of the queue and be wrongfully "
            "evicted as least recently used."
        ),
    ),
]

LEARNING_TAKEAWAYS: List[str] = [
    "Dual Eviction Policies: Production caching tiers (like Redis or Memcached) combine LRU/LFU memory policies with TTL expiration to prevent stale data from lingering.",
    "Lazy vs Active Expiration: High-performance caches avoid full background sweeps on every clock tick, favoring lazy eviction on read and batch eviction when capacity thresholds are reached.",
    "Thread Safety Considerations: In concurrent server environments, in-memory caches must guard operations with read-write locks or use lock-free sharded partitions.",
]

LRU_CACHE_CHALLENGE = ChallengeDefinition(
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
