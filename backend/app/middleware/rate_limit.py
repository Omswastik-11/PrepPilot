"""
Sliding Window Rate Limiter Middleware.

DESIGN DECISIONS:
  1. Sliding Window Algorithm:
     - Unlike fixed-window counters (which suffer from double-bursts at boundary edges),
       a sliding window tracks exact timestamps within the window.
     - Smoothly distributes request capacity and prevents boundary edge attacks.

  2. Tiered Rate Limiting:
     - Auth endpoints (/api/auth/*): 5 req/min per IP (mitigates brute-force & guest spam).
     - AI endpoints (/api/interviews/*):
         * Guest / Unauthenticated: 5 req/min per IP.
         * Authenticated user: 20 req/min per user ID.
     - General endpoints (/api/*): 60 req/min.

  3. Reverse-Proxy Awareness:
     - Correctly extracts the true client IP from the leftmost entry in X-Forwarded-For,
       falling back to request.client.host if not behind a proxy.

  4. RFC Standard Headers:
     - X-RateLimit-Limit: Total allowed requests in current window.
     - X-RateLimit-Remaining: Available requests remaining in current window.
     - X-RateLimit-Reset: Seconds until oldest request rolls off the window.
     - Retry-After: Seconds to wait when HTTP 429 is returned.
"""

import time
import threading
import logging
from collections import defaultdict, deque
from typing import Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.config import get_settings
from app.utils.security import decode_token

logger = logging.getLogger(__name__)

EXEMPT_PATHS = {
    "/",
    "/health",
    "/healthz",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class SlidingWindowRateLimiter:
    """In-memory sliding window counter with thread-safe atomic window tracking."""

    def __init__(self, cleanup_interval_seconds: float = 300.0):
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = cleanup_interval_seconds

    def _cleanup_stale_keys(self, now: float, window_seconds: float = 60.0) -> None:
        """Purge keys that have had no activity within the sliding window."""
        cutoff = now - window_seconds
        stale_keys = []
        for key, queue in self._requests.items():
            while queue and queue[0] <= cutoff:
                queue.popleft()
            if not queue:
                stale_keys.append(key)
        for key in stale_keys:
            del self._requests[key]

    def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: float = 60.0
    ) -> Tuple[bool, int, int, int]:
        """
        Check and record an access attempt. Thread-safe and non-blocking.

        Returns:
            Tuple[is_allowed, remaining_requests, reset_seconds, retry_after]
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Periodic cleanup
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup_stale_keys(now, window_seconds)
                self._last_cleanup = now

            queue = self._requests[key]

            # Drop timestamps older than window cutoff
            while queue and queue[0] <= cutoff:
                queue.popleft()

            current_count = len(queue)
            if current_count >= max_requests:
                # Throttled: calculate when the oldest recorded request rolls off
                oldest_timestamp = queue[0]
                retry_after = max(1, int(oldest_timestamp + window_seconds - now))
                reset_seconds = retry_after
                return False, 0, reset_seconds, retry_after

            # Allowed: record timestamp
            queue.append(now)
            remaining = max_requests - len(queue)
            oldest_timestamp = queue[0]
            reset_seconds = max(1, int(oldest_timestamp + window_seconds - now))
            return True, remaining, reset_seconds, 0

    def reset(self) -> None:
        """Clear all recorded requests (primarily for unit tests)."""
        with self._lock:
            self._requests.clear()
            self._last_cleanup = time.time()


# Global in-memory limiter instance
limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract true client IP from X-Forwarded-For or socket host."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_authenticated_user_id(request: Request) -> Optional[str]:
    """Extract user ID subject from Authorization header if a valid JWT is present."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    try:
        payload = decode_token(token, expected_type="access")
        return payload.get("sub")
    except Exception:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces tiered, proxy-aware sliding window rate limits.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_settings()

        # 1. Skip if rate limiting is globally disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # 2. Skip preflight CORS and health check endpoints
        path = request.url.path
        if request.method == "OPTIONS" or path in EXEMPT_PATHS:
            return await call_next(request)

        # 3. Determine client key and rate limit policy based on route and auth status
        client_ip = get_client_ip(request)
        user_id = get_authenticated_user_id(request)

        # Route matching
        if path.startswith("/api/auth/"):
            # Auth endpoints (login, register, guest creation): strictly throttled per IP
            key = f"auth:{client_ip}"
            max_requests = settings.RATE_LIMIT_AUTH_PER_MINUTE
        elif path.startswith("/api/interviews"):
            # AI-intensive endpoints (question generation & answer evaluation)
            if user_id:
                key = f"ai_user:{user_id}"
                max_requests = settings.RATE_LIMIT_AI_USER_PER_MINUTE
            else:
                key = f"ai_guest:{client_ip}"
                max_requests = settings.RATE_LIMIT_AI_GUEST_PER_MINUTE
        elif path.startswith("/api/"):
            # General application API endpoints
            if user_id:
                key = f"api_user:{user_id}"
            else:
                key = f"api_ip:{client_ip}"
            max_requests = settings.RATE_LIMIT_DEFAULT_PER_MINUTE
        else:
            # Static files, root, favicon, etc.
            return await call_next(request)

        # 4. Check limit with sliding window
        is_allowed, remaining, reset_sec, retry_after = limiter.check_rate_limit(
            key=key, max_requests=max_requests, window_seconds=60.0
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for key '{key}' on {request.method} {path}. Retry after {retry_after}s"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests. Please wait {retry_after} second{'s' if retry_after != 1 else ''} before trying again.",
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_sec),
                },
            )

        # 5. Execute route handler and inject rate limit headers into successful response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_sec)

        return response
