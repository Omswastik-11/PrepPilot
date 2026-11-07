"""
Unit Tests for Sliding Window Rate Limiter.

Pure synchronous unit tests:
  1. Rate limiter permits requests up to the threshold.
  2. Rate limiter blocks requests once quota is exhausted.
  3. Sliding window properly restores capacity over time.
  4. Proxy-aware IP extraction from X-Forwarded-For headers.
  5. JWT bearer token extraction for user-based tiers.
"""

import pytest
from unittest.mock import MagicMock

from app.middleware.rate_limit import (
    SlidingWindowRateLimiter,
    get_client_ip,
    get_authenticated_user_id,
)
from app.utils.security import create_access_token


@pytest.fixture
def limiter():
    lim = SlidingWindowRateLimiter()
    lim.reset()
    return lim


def test_sliding_window_permits_up_to_max(limiter):
    """Requests within limit are allowed and headers reflect remaining capacity."""
    key = "test_user_1"
    max_requests = 3
    window = 60.0

    # 1st request
    allowed, remaining, reset_sec, retry_after = limiter.check_rate_limit(
        key, max_requests=max_requests, window_seconds=window
    )
    assert allowed is True
    assert remaining == 2
    assert retry_after == 0

    # 2nd request
    allowed, remaining, reset_sec, retry_after = limiter.check_rate_limit(
        key, max_requests=max_requests, window_seconds=window
    )
    assert allowed is True
    assert remaining == 1

    # 3rd request (exhausts quota)
    allowed, remaining, reset_sec, retry_after = limiter.check_rate_limit(
        key, max_requests=max_requests, window_seconds=window
    )
    assert allowed is True
    assert remaining == 0


def test_sliding_window_blocks_over_limit(limiter):
    """Requests exceeding limit return allowed=False and positive retry_after."""
    key = "test_user_blocked"
    max_requests = 2
    window = 10.0

    # Exhaust limit
    limiter.check_rate_limit(key, max_requests=max_requests, window_seconds=window)
    limiter.check_rate_limit(key, max_requests=max_requests, window_seconds=window)

    # 3rd request must be blocked
    allowed, remaining, reset_sec, retry_after = limiter.check_rate_limit(
        key, max_requests=max_requests, window_seconds=window
    )
    assert allowed is False
    assert remaining == 0
    assert 1 <= retry_after <= 10


def test_sliding_window_slides_and_restores_capacity(limiter):
    """Expired timestamps roll off the window, restoring capacity."""
    key = "test_user_sliding"
    max_requests = 1
    window = 0.5  # 500ms window

    # 1st request succeeds
    allowed, _, _, _ = limiter.check_rate_limit(
        key, max_requests=max_requests, window_seconds=window
    )
    assert allowed is True

    # Immediate 2nd request blocked
    allowed, _, _, _ = limiter.check_rate_limit(
        key, max_requests=max_requests, window_seconds=window
    )
    assert allowed is False

    # Simulate passing of time by shifting timestamps back
    queue = limiter._requests[key]
    queue[0] -= 1.0  # 1 second ago (outside 0.5s window)

    # Now request should succeed again
    allowed, remaining, _, _ = limiter.check_rate_limit(
        key, max_requests=max_requests, window_seconds=window
    )
    assert allowed is True
    assert remaining == 0


def test_get_client_ip_with_forwarded_for():
    """Extracts the first (client) IP from X-Forwarded-For header chain."""
    request = MagicMock()
    request.headers = {"x-forwarded-for": "203.0.113.195, 70.41.3.18, 150.172.238.178"}
    ip = get_client_ip(request)
    assert ip == "203.0.113.195"


def test_get_client_ip_fallback():
    """Falls back to client.host when no proxy header is present."""
    request = MagicMock()
    request.headers = {}
    request.client.host = "192.168.1.50"
    ip = get_client_ip(request)
    assert ip == "192.168.1.50"


def test_get_authenticated_user_id_valid_jwt():
    """Decodes user_id subject from valid Bearer token."""
    user_id = "d8e3b7b2-4d2b-4b2a-8c2b-4d2b4b2a8c2b"
    token = create_access_token(subject=user_id)

    request = MagicMock()
    request.headers = {"authorization": f"Bearer {token}"}
    extracted = get_authenticated_user_id(request)
    assert extracted == user_id


def test_get_authenticated_user_id_invalid_or_missing():
    """Returns None for missing or malformed token."""
    request = MagicMock()
    request.headers = {}
    assert get_authenticated_user_id(request) is None

    request.headers = {"authorization": "Bearer invalid.token.structure"}
    assert get_authenticated_user_id(request) is None
