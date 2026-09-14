"""Drain admitted synchronous source writes before cancellation/reset completes."""
import asyncio
from starlette.concurrency import run_in_threadpool


async def settled_thread(function, *args):
    task = asyncio.create_task(run_in_threadpool(function, *args))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        # A Python thread cannot be killed. Await it before releasing ownership.
        await task
        raise
