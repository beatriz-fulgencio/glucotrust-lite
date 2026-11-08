"""Nonblocking admission limits shared by the app's browser sessions."""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
import os
import threading
import time


class InferenceLimitExceeded(RuntimeError):
    pass


class InferenceLimiter:
    def __init__(self, max_requests=6, max_concurrent=1, window_seconds=60, *, clock=time.monotonic):
        if max_requests < 1 or max_concurrent < 1 or window_seconds <= 0:
            raise ValueError("Inference limits must be positive")
        self.max_requests = max_requests
        self.max_concurrent = max_concurrent
        self.window_seconds = window_seconds
        self._clock = clock
        self._starts = deque()
        self._active = 0
        self._lock = threading.Lock()

    @contextmanager
    def acquire(self):
        with self._lock:
            now = self._clock()
            while self._starts and self._starts[0] <= now - self.window_seconds:
                self._starts.popleft()
            if self._active >= self.max_concurrent:
                raise InferenceLimitExceeded("The app is busy with another request. Please try again later.")
            if len(self._starts) >= self.max_requests:
                raise InferenceLimitExceeded("The app's request limit has been reached. Please try again in a minute.")
            self._starts.append(now)
            self._active += 1
        try:
            yield
        finally:
            with self._lock:
                self._active -= 1


_app_limiter = None
_app_limiter_lock = threading.Lock()


def get_inference_limiter():
    # Streamlit lets clients clear its caches. Keep admission state outside
    # those caches so clearing them or opening a new session cannot reset it.
    global _app_limiter
    with _app_limiter_lock:
        if _app_limiter is None:
            _app_limiter = InferenceLimiter(
                max_requests=int(os.getenv("GLUCOTRUST_REQUESTS_PER_MINUTE", "6")),
                max_concurrent=int(os.getenv("GLUCOTRUST_MAX_CONCURRENT_REQUESTS", "1")))
        return _app_limiter
