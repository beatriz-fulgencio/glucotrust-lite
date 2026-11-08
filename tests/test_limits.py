from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from glucotrust.limits import InferenceLimiter, InferenceLimitExceeded


def test_rolling_limit_expires_without_waiting():
    now = [0.0]
    limiter = InferenceLimiter(max_requests=2, clock=lambda: now[0])
    with limiter.acquire():
        pass
    now[0] = 30
    with limiter.acquire():
        pass
    with pytest.raises(InferenceLimitExceeded, match="request limit"):
        with limiter.acquire():
            pytest.fail("Rate-limited work must not run")
    now[0] = 60
    with limiter.acquire():
        pass
    # Only the first request expired; the second remains in the rolling window.
    with pytest.raises(InferenceLimitExceeded):
        with limiter.acquire():
            pytest.fail("Rolling window was reset too early")


def test_concurrent_request_rejected_and_failure_releases_slot():
    limiter = InferenceLimiter(max_requests=3)
    with limiter.acquire():
        with ThreadPoolExecutor(max_workers=1) as executor:
            def competing_request():
                with limiter.acquire():
                    return "unexpected work"
            with pytest.raises(InferenceLimitExceeded, match="busy"):
                executor.submit(competing_request).result(timeout=5)
    with pytest.raises(RuntimeError, match="provider failure"):
        with limiter.acquire():
            raise RuntimeError("provider failure")
    # Failed work still consumes rate allowance, but must release concurrency.
    with limiter.acquire():
        pass
    with pytest.raises(InferenceLimitExceeded, match="request limit"):
        with limiter.acquire():
            pytest.fail("Failures must not bypass the rate limit")


def test_simultaneous_requests_cannot_overbook():
    limiter = InferenceLimiter(max_requests=20, max_concurrent=2)
    start = threading.Barrier(8)
    release = threading.Event()
    admitted = []
    rejected = []
    all_decided = threading.Event()
    lock = threading.Lock()

    def decide(destination):
        with lock:
            destination.append(True)
            if len(admitted) + len(rejected) == 8:
                all_decided.set()

    def request():
        start.wait(timeout=5)
        try:
            with limiter.acquire():
                decide(admitted)
                assert release.wait(timeout=5)
        except InferenceLimitExceeded:
            decide(rejected)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(request) for _ in range(8)]
        try:
            assert all_decided.wait(timeout=5)
            assert len(admitted) == 2 and len(rejected) == 6
        finally:
            release.set()
        for future in futures:
            future.result(timeout=5)


@pytest.mark.parametrize("kwargs", [{"max_requests": 0}, {"max_concurrent": 0}, {"window_seconds": 0}])
def test_invalid_limits_fail_closed(kwargs):
    with pytest.raises(ValueError):
        InferenceLimiter(**kwargs)
