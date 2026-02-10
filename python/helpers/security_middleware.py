"""
Security Middleware for Agent Claw / SYNTHIA Dashboard

Implements:
- Rate limiting (per-IP)
- Anti-scraping headers
- Content Security Policy
- HSTS / X-Frame-Options / X-Content-Type-Options
- Bot detection (basic user-agent filtering)
- Request size limits
- IP-based brute force protection
"""

import time
import threading
from collections import defaultdict
from functools import wraps
from flask import Flask, request, Response


class SecurityMiddleware:
    """Production-grade security middleware for Flask."""

    def __init__(self, app: Flask, config: dict | None = None):
        self.app = app
        self.config = config or {}

        # Rate limiting state
        self._request_counts: dict[str, list[float]] = defaultdict(list)
        self._blocked_ips: dict[str, float] = {}
        self._lock = threading.Lock()

        # Configuration
        self.rate_limit = self.config.get("rate_limit", 120)  # requests per window
        self.rate_window = self.config.get("rate_window", 60)  # seconds
        self.block_duration = self.config.get("block_duration", 300)  # 5 min block
        self.max_content_length = self.config.get("max_content_length", 50 * 1024 * 1024)  # 50MB

        # Known bot user-agents to block (scrapers, not search engines)
        self.blocked_agents = [
            "scrapy", "httrack", "wget/1", "python-urllib",
            "go-http-client", "java/", "libwww-perl",
        ]

        # Whitelisted paths (no rate limiting)
        self.whitelist_paths = ["/health", "/favicon.svg", "/favicon.ico"]

        # Register middleware
        self._register()

    def _register(self):
        """Register before/after request hooks."""
        self.app.config["MAX_CONTENT_LENGTH"] = self.max_content_length

        @self.app.before_request
        def security_before():
            return self._before_request()

        @self.app.after_request
        def security_after(response):
            return self._after_response(response)

    def _before_request(self):
        """Pre-request security checks."""
        ip = request.remote_addr or "unknown"
        path = request.path

        # Skip security for whitelisted paths
        if path in self.whitelist_paths:
            return None

        # Check if IP is blocked
        with self._lock:
            if ip in self._blocked_ips:
                if time.time() < self._blocked_ips[ip]:
                    return Response("Too many requests. Try again later.", 429)
                else:
                    del self._blocked_ips[ip]

        # Basic bot detection
        ua = (request.headers.get("User-Agent") or "").lower()
        for bot in self.blocked_agents:
            if bot in ua:
                return Response("Forbidden", 403)

        # Rate limiting
        if not self._check_rate_limit(ip):
            with self._lock:
                self._blocked_ips[ip] = time.time() + self.block_duration
            return Response("Rate limit exceeded. Blocked temporarily.", 429)

        return None

    def _after_response(self, response: Response) -> Response:
        """Add security headers to all responses."""
        # Anti-clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (restrict browser APIs)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: https:; "
            "media-src 'self' blob:; "
            "frame-ancestors 'self';"
        )

        # HSTS (only if not localhost dev)
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Remove server header
        response.headers.pop("Server", None)

        # Cache control for API responses
        if request.path.startswith("/") and request.method == "POST":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response

    def _check_rate_limit(self, ip: str) -> bool:
        """Check if IP is within rate limits."""
        now = time.time()
        with self._lock:
            # Clean old entries
            self._request_counts[ip] = [
                t for t in self._request_counts[ip]
                if t > now - self.rate_window
            ]
            # Check limit
            if len(self._request_counts[ip]) >= self.rate_limit:
                return False
            # Record request
            self._request_counts[ip].append(now)
            return True

    def cleanup(self):
        """Periodic cleanup of stale rate limit data."""
        now = time.time()
        with self._lock:
            stale_ips = [
                ip for ip, times in self._request_counts.items()
                if not times or max(times) < now - self.rate_window * 2
            ]
            for ip in stale_ips:
                del self._request_counts[ip]

            expired_blocks = [
                ip for ip, expire in self._blocked_ips.items()
                if expire < now
            ]
            for ip in expired_blocks:
                del self._blocked_ips[ip]
