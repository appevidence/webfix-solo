# Ported from appevidence/evidence-capture-app at commit 24e849a8c4253daf3c12dac1be8bad11c45819ae
from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_fixed

RETRY_DEFAULTS: dict = {
    "stop": stop_after_attempt(3),
    "wait": wait_fixed(1.0),
    "reraise": True,
}


async def retry_async(coro_fn, *args, max_attempts: int = 3, wait_seconds: float = 1.0, **kwargs):
    """Retry an async coroutine function with tenacity."""
    decorated = retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_fixed(wait_seconds),
        reraise=True,
    )(coro_fn)
    return await decorated(*args, **kwargs)


def retry_sync(fn, *args, max_attempts: int = 3, wait_seconds: float = 1.0, **kwargs):
    """Retry a sync function with tenacity."""
    decorated = retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_fixed(wait_seconds),
        reraise=True,
    )(fn)
    return decorated(*args, **kwargs)
