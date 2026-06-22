"""Rate limiter using asyncio semaphore."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from ..logger import setup_logging

logger = setup_logging(__name__)

DEFAULT_CONCURRENCY = 3


class Throttle:
    """Async rate limiter based on semaphore.

    Limits concurrent AI requests to respect NaN Cloud rate limits
    (~100 RPM / 5 concurrent account-wide).

    Example:
        >>> throttle = Throttle(concurrency=3)
        >>> async with throttle.acquire():
        ...     await call_ai()
    """

    def __init__(
        self,
        concurrency: int | None = None,
        max_queue: int = 100,
    ) -> None:
        self._concurrency = concurrency or int(
            os.environ.get("AI_CONCURRENCY", str(DEFAULT_CONCURRENCY))
        )
        self._semaphore = asyncio.Semaphore(self._concurrency)
        self._max_queue = max_queue
        self._active = 0
        self._total_requests = 0

    @property
    def concurrency(self) -> int:
        """Current concurrency limit."""
        return self._concurrency

    @property
    def active_requests(self) -> int:
        """Number of currently active requests."""
        return self._active

    @property
    def total_requests(self) -> int:
        """Total requests processed."""
        return self._total_requests

    @asynccontextmanager
    async def acquire(self) -> Any:
        """Acquire a slot, blocking if at capacity.

        Yields a context that releases the slot on exit.
        """
        await self._semaphore.acquire()
        self._active += 1
        self._total_requests += 1
        logger.debug(
            "Throttle acquired (active=%d/%d)",
            self._active,
            self._concurrency,
        )
        try:
            yield None
        finally:
            self._active -= 1
            self._semaphore.release()
            logger.debug(
                "Throttle released (active=%d/%d)",
                self._active,
                self._concurrency,
            )

    async def try_acquire(self) -> bool:
        """Try to acquire a slot without blocking.

        Returns:
            True if acquired, False if at capacity.
        """
        # Access internal _value for non-blocking check
        value = self._semaphore._value
        acquired = value > 0
        if acquired:
            self._semaphore._value -= 1
            self._active += 1
            self._total_requests += 1
            logger.debug(
                "Throttle acquired (non-blocking, active=%d/%d)",
                self._active,
                self._concurrency,
            )
            return True
        return False
