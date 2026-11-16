from collections import defaultdict, deque
from time import monotonic
from typing import Protocol

_SWEEP_EVERY = 500


class RateLimiter(Protocol):
    def allow(self, key: str, limit: int, window_seconds: int = 900) -> tuple[bool, int]: ...


class InMemoryRateLimiter:
    """Single-process limiter for local use. Swap for a Redis-backed one in Phase 8."""

    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._calls = 0

    def _sweep(self, now: float, window_seconds: int) -> None:
        stale = [k for k, v in self._attempts.items() if not v or v[-1] <= now - window_seconds]
        for key in stale:
            del self._attempts[key]

    def allow(self, key: str, limit: int, window_seconds: int = 900) -> tuple[bool, int]:
        now = monotonic()
        self._calls += 1
        if self._calls % _SWEEP_EVERY == 0:
            self._sweep(now, window_seconds)
        entries = self._attempts[key]
        while entries and entries[0] <= now - window_seconds:
            entries.popleft()
        if len(entries) >= limit:
            retry_after = max(1, int(window_seconds - (now - entries[0])))
            return False, retry_after
        entries.append(now)
        return True, 0
