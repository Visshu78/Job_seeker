"""
Rate limiter — per-tool throttling to avoid API bans.
"""
import time
import threading
from collections import defaultdict
from utils.logger import get_logger

logger = get_logger("rate-limiter")


class RateLimiter:
    """
    Per-tool rate limiter using a token bucket approach.
    Tracks requests per tool and enforces delays.
    """

    def __init__(self):
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._last_call: dict[str, float] = defaultdict(float)
        self._call_counts: dict[str, int] = defaultdict(int)

        # Default delays per tool (seconds between requests)
        self._delays: dict[str, float] = {
            "apollo_io":    1.5,
            "hunter_io":    1.0,
            "signalhire":   2.0,
            "snov_io":      1.0,
            "rocketreach":  1.5,
            "contactout":   1.5,
            "free_tools":   0.5,
            "linkedin":     3.0,
            "duckduckgo":   1.0,
            "default":      1.0,
        }

    def wait(self, tool: str) -> None:
        """Block until the rate limit delay has passed for the given tool."""
        delay = self._delays.get(tool, self._delays["default"])
        with self._locks[tool]:
            elapsed = time.time() - self._last_call[tool]
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(f"[dim]Rate limiting {tool}: waiting {wait_time:.2f}s[/dim]")
                time.sleep(wait_time)
            self._last_call[tool] = time.time()
            self._call_counts[tool] += 1

    def set_delay(self, tool: str, seconds: float) -> None:
        """Override delay for a specific tool."""
        self._delays[tool] = seconds

    def get_call_count(self, tool: str) -> int:
        return self._call_counts[tool]

    def reset_counts(self) -> None:
        self._call_counts.clear()


# Global singleton
rate_limiter = RateLimiter()
