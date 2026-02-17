import asyncio
import time
from collections import defaultdict
from urllib.parse import urlparse


class PerDomainThrottle:
    """Enforces minimum delay between requests to the same domain."""

    HARD_FLOOR = 2.0  # Minimum 2s delay - prevents accidental DoS

    def __init__(self, delay: float = 2.0):
        self.delay = max(delay, self.HARD_FLOOR)
        self._last_request: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def wait(self, url: str) -> None:
        domain = urlparse(url).hostname or ""
        async with self._locks[domain]:
            now = time.monotonic()
            elapsed = now - self._last_request[domain]
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed)
            self._last_request[domain] = time.monotonic()


class CircuitBreaker:
    """Trips after consecutive failures; auto-resets after cooldown."""

    def __init__(self, threshold: int = 5, cooldown: float = 60.0):
        self.threshold = threshold
        self.cooldown = cooldown
        self._failures: dict[str, int] = defaultdict(int)
        self._tripped_at: dict[str, float] = {}

    def record_success(self, domain: str) -> None:
        self._failures[domain] = 0
        self._tripped_at.pop(domain, None)

    def record_failure(self, domain: str) -> None:
        self._failures[domain] += 1
        if self._failures[domain] >= self.threshold:
            self._tripped_at[domain] = time.monotonic()

    def is_open(self, domain: str) -> bool:
        if domain not in self._tripped_at:
            return False
        elapsed = time.monotonic() - self._tripped_at[domain]
        if elapsed >= self.cooldown:
            # Half-open: allow one attempt
            self._failures[domain] = 0
            del self._tripped_at[domain]
            return False
        return True
