"""
API Rate Limiting Middleware for Agent Claw endpoints.

Provides per-IP and per-endpoint rate limiting using a sliding window.
Applied automatically to Agent Claw API endpoints via the decorator.

Usage:
    from python.helpers.api_rate_limit import rate_limit, RateLimitConfig

    class MyHandler(ApiHandler):
        @classmethod
        def rate_limit_config(cls) -> RateLimitConfig:
            return RateLimitConfig(requests_per_minute=30)
"""

import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Global store for rate limit tracking
_rate_store: Dict[str, List[float]] = {}
_store_lock = threading.Lock()
_CLEANUP_INTERVAL = 300  # Cleanup stale entries every 5 minutes
_last_cleanup = 0.0


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting an endpoint."""
    requests_per_minute: int = 60
    requests_per_hour: int = 600
    burst_limit: int = 10  # Max requests in a 5-second burst window
    exempt_loopback: bool = True  # Skip rate limiting for localhost


def _cleanup_stale_entries():
    """Remove entries older than 1 hour to prevent memory growth."""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    cutoff = now - 3600
    stale_keys = []
    with _store_lock:
        for key, timestamps in _rate_store.items():
            _rate_store[key] = [t for t in timestamps if t > cutoff]
            if not _rate_store[key]:
                stale_keys.append(key)
        for key in stale_keys:
            del _rate_store[key]


def _get_client_ip(request: Any) -> str:
    """Extract client IP, respecting X-Forwarded-For behind proxies."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _is_loopback(ip: str) -> bool:
    """Check if IP is localhost/loopback."""
    return ip in ("127.0.0.1", "::1", "localhost", "0.0.0.0")


def check_rate_limit(
    request: Any,
    endpoint: str,
    config: Optional[RateLimitConfig] = None,
) -> Tuple[bool, Optional[Any]]:
    """
    Check if a request is within rate limits.

    Args:
        request: Flask request object
        endpoint: Endpoint name for namespacing
        config: Rate limit configuration (uses defaults if None)

    Returns:
        (allowed, response) — allowed=True means proceed; if False, response is a 429
    """
    if config is None:
        config = RateLimitConfig()

    client_ip = _get_client_ip(request)

    # Skip for loopback if configured
    if config.exempt_loopback and _is_loopback(client_ip):
        return True, None

    now = time.time()
    key = f"{client_ip}:{endpoint}"

    _cleanup_stale_entries()

    with _store_lock:
        if key not in _rate_store:
            _rate_store[key] = []

        timestamps = _rate_store[key]

        # Check burst limit (5-second window)
        burst_window = now - 5
        burst_count = sum(1 for t in timestamps if t > burst_window)
        if burst_count >= config.burst_limit:
            logger.warning(f"Rate limit burst exceeded: {client_ip} on {endpoint}")
            return False, _rate_limit_response(
                "Too many requests (burst)", retry_after=5
            )

        # Check per-minute limit
        minute_window = now - 60
        minute_count = sum(1 for t in timestamps if t > minute_window)
        if minute_count >= config.requests_per_minute:
            logger.warning(f"Rate limit/min exceeded: {client_ip} on {endpoint}")
            return False, _rate_limit_response(
                "Rate limit exceeded", retry_after=60
            )

        # Check per-hour limit
        hour_window = now - 3600
        hour_count = sum(1 for t in timestamps if t > hour_window)
        if hour_count >= config.requests_per_hour:
            logger.warning(f"Rate limit/hr exceeded: {client_ip} on {endpoint}")
            return False, _rate_limit_response(
                "Hourly rate limit exceeded", retry_after=300
            )

        # Record this request
        timestamps.append(now)

        # Prune old timestamps beyond 1 hour
        _rate_store[key] = [t for t in timestamps if t > now - 3600]

    return True, None


def _rate_limit_response(message: str, retry_after: int = 60) -> Any:
    """Build a 429 Too Many Requests response."""
    import json

    from flask import Response as FlaskResponse

    body = json.dumps({"error": message, "retry_after": retry_after})
    resp = FlaskResponse(response=body, status=429, mimetype="application/json")
    resp.headers["Retry-After"] = str(retry_after)
    return resp


# ── API Key Validation ──────────────────────────────────────

_API_KEYS: Optional[set] = None


def _load_api_keys() -> set:
    """Load API keys from environment."""
    global _API_KEYS
    if _API_KEYS is not None:
        return _API_KEYS

    import os
    keys_str = os.environ.get("AGENT_CLAW_API_KEYS", "")
    _API_KEYS = {k.strip() for k in keys_str.split(",") if k.strip()}
    if _API_KEYS:
        logger.info(f"Loaded {len(_API_KEYS)} Agent Claw API keys")
    return _API_KEYS


def validate_api_key(request: Any) -> Tuple[bool, Optional[Any]]:
    """
    Validate API key from request header or query param.
    If no API keys are configured, all requests are allowed.

    Returns:
        (valid, response) — valid=True means proceed; if False, response is a 401
    """
    import json

    from flask import Response as FlaskResponse

    keys = _load_api_keys()
    if not keys:
        # No API keys configured — allow all (dev mode)
        return True, None

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token in keys:
            return True, None

    # Check X-API-Key header
    api_key = request.headers.get("X-API-Key", "")
    if api_key and api_key in keys:
        return True, None

    # Check query parameter
    api_key = request.args.get("api_key", "")
    if api_key and api_key in keys:
        return True, None

    body = json.dumps({"error": "Invalid or missing API key"})
    return False, FlaskResponse(response=body, status=401, mimetype="application/json")


def rotate_api_keys(new_keys: List[str]) -> int:
    """
    Rotate API keys. Replaces the current key set.

    Args:
        new_keys: List of new API key strings

    Returns:
        Number of keys now active
    """
    global _API_KEYS
    _API_KEYS = {k.strip() for k in new_keys if k.strip()}
    logger.info(f"API keys rotated: {len(_API_KEYS)} keys active")
    return len(_API_KEYS)
