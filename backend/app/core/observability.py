"""
Structured observability for the Student Success Predictor.

Provides:
1. A JSON-structured logging formatter controlled by LOG_LEVEL / LOG_FORMAT.
2. Request correlation IDs (X-Request-ID) and an access log that records
   request_id, method, path, status, latency, and error category — never
   passwords, tokens, bodies, or student records.
3. Security response headers (applied to every response) and a production-only
   Host (ALLOWED_HOSTS) allow-list check.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.app.core.config import settings

logger = logging.getLogger("student_predictor")

# Headers that are always safe to set and do not break the application.
SECURITY_HEADERS: dict = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# A conservative CSP that keeps the built SPA functional. Only applied outside
# local development to avoid breaking the Vite dev server (inline styles, ws).
PRODUCTION_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; connect-src 'self'; font-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


class JSONFormatter(logging.Formatter):
    """Compact JSON log formatter with selectable extra fields."""

    _EXTRA_FIELDS = (
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "error_category",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            try:
                payload["exc_info"] = self.formatException(record.exc_info)
            except Exception:  # pragma: no cover - defensive
                payload["exc_info"] = "unformattable"
        for key in self._EXTRA_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Idempotently configure the root logger from environment settings."""
    logger_obj = logging.getLogger("student_predictor")
    if getattr(logger_obj, "_observability_configured", False):
        return

    level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)
    formatter: logging.Formatter
    if str(settings.LOG_FORMAT).lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )

    # Route the "student_predictor.*" hierarchy through a single handler so
    # library loggers (uvicorn, sqlalchemy) keep their own defaults.
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger_obj.handlers = [handler]
    logger_obj.setLevel(level)
    logger_obj.propagate = False
    logger_obj._observability_configured = True  # type: ignore[attr-defined]


def _client_host(request: Request) -> str:
    # Respect the X-Forwarded-For header only in production (set by a trusted
    # reverse proxy). In development the direct peer address is used.
    if settings.ENVIRONMENT == "production":
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID, enforces Host allow-list, sets security headers,
    and emits one structured access-log line per handled request."""

    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id

        # Host header allow-list (production hardening; optional).
        allowed = settings.ALLOWED_HOSTS
        if settings.ENVIRONMENT == "production" and allowed:
            host = (request.headers.get("host") or "").split(":")[0]
            if host not in allowed:
                from starlette.responses import JSONResponse

                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "INVALID_HOST",
                            "message": "Unknown host.",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "path": request.url.path,
                        }
                    },
                    headers={"X-Request-ID": request_id},
                )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - handled by app handlers
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "request failed",
                exc_info=exc,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "error_category": "UNHANDLED_EXCEPTION",
                },
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if settings.ENVIRONMENT != "development":
            response.headers.setdefault("Content-Security-Policy", PRODUCTION_CSP)

        category = None
        if response.status_code >= 500:
            category = "SERVER_ERROR"
        elif response.status_code >= 400:
            category = "CLIENT_ERROR"

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "error_category": category,
            },
        )
        return response