"""Tests for AI throttle/rate limiter."""

from __future__ import annotations

import asyncio

import pytest

from pdf_modifier.ai.throttle import Throttle


class TestThrottle:
    """Throttle concurrency tests."""

    @pytest.mark.asyncio
    async def test_allows_concurrent_requests(self) -> None:
        throttle = Throttle(concurrency=3)
        active_count = 0
        max_active = 0

        async def track() -> None:
            nonlocal active_count, max_active
            async with throttle.acquire():
                active_count += 1
                max_active = max(max_active, active_count)
                await asyncio.sleep(0.01)
                active_count -= 1

        await asyncio.gather(*[track() for _ in range(6)])
        assert max_active <= 3

    @pytest.mark.asyncio
    async def test_limits_concurrency(self) -> None:
        throttle = Throttle(concurrency=2)
        active_count = 0
        max_active = 0

        async def track() -> None:
            nonlocal active_count, max_active
            async with throttle.acquire():
                active_count += 1
                max_active = max(max_active, active_count)
                await asyncio.sleep(0.02)
                active_count -= 1

        await asyncio.gather(*[track() for _ in range(10)])
        assert max_active <= 2
        assert throttle.total_requests == 10

    def test_default_concurrency(self) -> None:
        throttle = Throttle()
        assert throttle.concurrency == 3

    def test_custom_concurrency(self) -> None:
        throttle = Throttle(concurrency=5)
        assert throttle.concurrency == 5

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_CONCURRENCY", "7")
        throttle = Throttle()
        assert throttle.concurrency == 7

    @pytest.mark.asyncio
    async def test_try_acquire_success(self) -> None:
        throttle = Throttle(concurrency=2)
        result = await throttle.try_acquire()
        assert result is True
        assert throttle.active_requests == 1

    @pytest.mark.asyncio
    async def test_try_acquire_full(self) -> None:
        throttle = Throttle(concurrency=1)
        await throttle.try_acquire()
        result = await throttle.try_acquire()
        assert result is False

    def test_initial_state(self) -> None:
        throttle = Throttle()
        assert throttle.active_requests == 0
        assert throttle.total_requests == 0
