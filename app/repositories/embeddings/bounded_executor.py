"""Adapter-layer admission control for blocking inference on dedicated workers."""
import asyncio
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from typing import TypeVar

T = TypeVar("T")


class BoundedExecutor:
    """Count submitted work until its worker finishes, even if its caller cancels."""

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("Embedding concurrency must be at least 1")
        self._capacity = capacity
        self._executor = ThreadPoolExecutor(max_workers=capacity, thread_name_prefix="embedding")
        self._condition = asyncio.Condition()
        self._active = 0
        self._closed = False
        self._close_task: asyncio.Task | None = None

    async def run(self, function: Callable[..., T], *args) -> T:
        loop = asyncio.get_running_loop()
        async with self._condition:
            await self._condition.wait_for(lambda: self._closed or self._active < self._capacity)
            if self._closed:
                raise RuntimeError("Embedding adapter is closed")
            self._active += 1
            try:
                future = self._executor.submit(partial(function, *args))
            except BaseException:
                self._active -= 1
                self._condition.notify_all()
                raise
            future.add_done_callback(lambda completed: self._worker_done(loop, completed))
        wrapped = asyncio.wrap_future(future, loop=loop)
        # A cancelled caller no longer awaits this future; still retrieve worker failures.
        wrapped.add_done_callback(lambda completed: completed.exception() if not completed.cancelled() else None)
        return await asyncio.shield(wrapped)

    def _worker_done(self, loop: asyncio.AbstractEventLoop, future: Future) -> None:
        try:
            loop.call_soon_threadsafe(self._schedule_release)
        except RuntimeError:
            # Normal shutdown drains before loop closure. A prematurely closed loop
            # cannot have live waiters, but must not break the worker's completion.
            future.exception()

    def _schedule_release(self) -> None:
        asyncio.create_task(self._release())

    async def _release(self) -> None:
        async with self._condition:
            self._active -= 1
            self._condition.notify_all()

    async def _close(self) -> None:
        async with self._condition:
            self._closed = True
            self._condition.notify_all()
            await self._condition.wait_for(lambda: self._active == 0)
        await asyncio.to_thread(self._executor.shutdown, wait=True)

    async def aclose(self) -> None:
        """Reject and wake waiters, drain workers, and join them without blocking the loop."""
        if self._close_task is None:
            self._closed = True
            self._close_task = asyncio.create_task(self._close())
        await asyncio.shield(self._close_task)
