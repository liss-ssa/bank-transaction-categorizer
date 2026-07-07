from __future__ import annotations

import asyncio
import time
from collections import deque


class AsyncRateLimiter:
    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.calls: deque[float] = deque()
        self.lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self.lock:
            now = time.monotonic()
            while self.calls and now - self.calls[0] > self.period_seconds:
                self.calls.popleft()
            if len(self.calls) >= self.max_calls:
                sleep_for = self.period_seconds - (now - self.calls[0])
                await asyncio.sleep(max(0.0, sleep_for))
            self.calls.append(time.monotonic())
