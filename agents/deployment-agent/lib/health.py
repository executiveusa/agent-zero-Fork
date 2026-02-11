"""
Health Check — Multi-endpoint verification with retries
========================================================
Checks /, /health, /healthz, /api/health with configurable retry logic.
"""

import time
import urllib.error
import urllib.request
from typing import Any

HEALTH_ENDPOINTS = ["/health", "/healthz", "/api/health", "/"]


def health_check(
    base_url: str,
    retries: int = 5,
    delay: int = 15,
    endpoints: list[str] | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    """Run health checks against multiple endpoints.

    Args:
        base_url: App URL (e.g. http://myapp.31.220.58.212.sslip.io)
        retries: Number of attempts per endpoint
        delay: Seconds between retries
        endpoints: Custom endpoint list (default: /health, /healthz, /api/health, /)
        timeout: Request timeout in seconds

    Returns:
        {
            "healthy": True/False,
            "endpoint": "/health",
            "status_code": 200,
            "response_time_ms": 123,
            "attempts": 2,
            "errors": []
        }
    """
    if endpoints is None:
        endpoints = HEALTH_ENDPOINTS

    errors = []

    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}{endpoint}"

        for attempt in range(1, retries + 1):
            start = time.time()
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "AgentClaw/1.0"},
                )
                resp = urllib.request.urlopen(req, timeout=timeout)
                elapsed_ms = int((time.time() - start) * 1000)

                if resp.status == 200:
                    return {
                        "healthy": True,
                        "endpoint": endpoint,
                        "status_code": 200,
                        "response_time_ms": elapsed_ms,
                        "attempts": attempt,
                        "errors": errors,
                    }
            except urllib.error.HTTPError as e:
                errors.append(f"{url} → HTTP {e.code} (attempt {attempt})")
            except Exception as e:
                errors.append(f"{url} → {type(e).__name__}: {e} (attempt {attempt})")

            if attempt < retries:
                time.sleep(delay)

    return {
        "healthy": False,
        "endpoint": None,
        "status_code": None,
        "response_time_ms": None,
        "attempts": retries * len(endpoints),
        "errors": errors,
    }


def wait_for_healthy(
    base_url: str,
    max_wait: int = 180,
    poll_interval: int = 10,
) -> dict[str, Any]:
    """Wait for an app to become healthy after deployment.

    Polls /health every poll_interval seconds until healthy or timeout.
    """
    start = time.time()
    last_error = None

    while time.time() - start < max_wait:
        result = health_check(base_url, retries=1, delay=0, timeout=10)
        if result["healthy"]:
            return {
                "healthy": True,
                "waited_seconds": int(time.time() - start),
                **result,
            }
        last_error = result["errors"][-1] if result["errors"] else "No response"
        time.sleep(poll_interval)

    return {
        "healthy": False,
        "waited_seconds": int(time.time() - start),
        "last_error": last_error,
    }
