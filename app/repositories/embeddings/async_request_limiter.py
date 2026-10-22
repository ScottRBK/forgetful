"""Admission control for one adapter's logical asynchronous SDK requests."""
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class AsyncRequestLimiter:
    """Hold a slot until an awaited request completes, fails, or is cancelled."""

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("Embedding concurrency must be at least 1")
        self._slots = asyncio.Semaphore(capacity)
        self._active = 0
        self._closed = False
        self._drained = asyncio.Event()
        self._drained.set()
        self._close_task: asyncio.Task | None = None

    @asynccontextmanager
    async def request(self) -> AsyncIterator[None]:
        if self._closed:
            raise RuntimeError("Embedding adapter is closed")
        async with self._slots:
            if self._closed:
                raise RuntimeError("Embedding adapter is closed")
            self._active += 1
            self._drained.clear()
            try:
                yield
            finally:
                self._active -= 1
                if self._active == 0:
                    self._drained.set()

    def close_admission(self) -> None:
        """Prevent new SDK requests before scheduling asynchronous shutdown."""
        self._closed = True

    async def aclose(self) -> None:
        self.close_admission()
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._drained.wait())
        await asyncio.shield(self._close_task)
