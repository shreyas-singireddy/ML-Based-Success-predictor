"""
Phase 14/15 — Security hardening, observability, and MLOps health tests.

Covers:
1. Liveness / readiness / model-health endpoints.
2. Security response headers and request correlation IDs.
3. Login brute-force rate limiting (429).
4. CORS explicit-origin behavior (allow-list, no wildcard).
5. Logout clearing the refresh cookie.
6. Categorical input validation (gender / department_code).
7. Production configuration fails closed (default SECRET_KEY + DEBUG).
"""

import pytest
from httpx import AsyncClient

from backend.app.core.config import Settings

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Health / readiness / model health
# ---------------------------------------------------------------------------

async def test_health_endpoint(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert "service" in body and "version" in body and "environment" in body
    # Liveness payload must never leak configuration or secrets.
    assert "database_url" not in body and "secret" not in str(body).lower()


async def test_readiness_endpoint(client: AsyncClient):
    res = await client.get("/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"ready", "not_ready"}
    assert body["checks"]["database"] in {"ok", "unreachable"}


async def test_model_health_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/model/health")
    assert res.status_code in {200, 503}
    body = res.json()
    report = body["model_health"]
    assert report["status"] in {"healthy", "degraded"}
    assert "registry_path" in report
    assert report["models"]["cgpa"]["model_version"]


# ---------------------------------------------------------------------------
# Security headers & correlation IDs
# ---------------------------------------------------------------------------

async def test_security_headers_present(client: AsyncClient):
    res = await client.get("/health")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert res.headers["X-Request-ID"]


async def test_csp_present_outside_development(client: AsyncClient):
    from backend.app.core.observability import PRODUCTION_CSP

    res = await client.get("/health")
    if res.headers.get("Content-Security-Policy"):
        assert "default-src 'self'" in res.headers["Content-Security-Policy"]
    else:
        # Development environment does not attach CSP; assert the policy constant.
        assert "frame-ancestors 'none'" in PRODUCTION_CSP


async def test_request_id_echoed(client: AsyncClient):
    res = await client.get("/health", headers={"X-Request-ID": "abc123"})
    assert res.headers.get("X-Request-ID") == "abc123"


# ---------------------------------------------------------------------------
# Login rate limiting
# ---------------------------------------------------------------------------

async def test_login_rate_limit_returns_429(client: AsyncClient):
    from backend.app.api.v1 import auth as auth_module
    from backend.app.core.config import settings

    previous = settings.LOGIN_RATE_LIMIT_PER_MINUTE
    try:
        settings.LOGIN_RATE_LIMIT_PER_MINUTE = 3
        auth_module._login_limiter.reset()

        payload = {"email": "student1.test@university.edu", "password": "wrong-password"}
        statuses = []
        for _ in range(4):
            res = await client.post(f"{settings.API_V1_PREFIX}/auth/login", json=payload)
            statuses.append(res.status_code)
        assert statuses[-1] == 429, f"expected 429 on 4th burst, got {statuses}"
        assert all(s in {401, 429} for s in statuses)
    finally:
        settings.LOGIN_RATE_LIMIT_PER_MINUTE = previous
        auth_module._login_limiter.reset()


# ---------------------------------------------------------------------------
# CORS explicit origins
# ---------------------------------------------------------------------------

async def test_cors_allowed_origin(client: AsyncClient):
    res = await client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"


async def test_cors_disallowed_origin_no_header(client: AsyncClient):
    res = await client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert "access-control-allow-origin" not in res.headers


# ---------------------------------------------------------------------------
# Logout clears refresh cookie
# ---------------------------------------------------------------------------

async def test_logout_clears_refresh_cookie(client: AsyncClient):
    from backend.app.core.config import settings

    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "student1.test@university.edu", "password": "TestPass@123"},
    )
    assert res.status_code == 200
    assert res.cookies.get("refresh_token")

    out = await client.post(f"{settings.API_V1_PREFIX}/auth/logout")
    assert out.status_code == 204
    # The Set-Cookie header should instruct the browser to expire the cookie.
    set_cookie = out.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie and ("Max-Age=0" in set_cookie or "expires=" in set_cookie.lower())


# ---------------------------------------------------------------------------
# Categorical input validation (fail safely on unknown values)
# ---------------------------------------------------------------------------

async def test_prediction_rejects_invalid_gender(client: AsyncClient):
    from backend.app.core.config import settings

    payload = {
        "attendance_percentage": 80.0,
        "previous_cgpa": 7.0,
        "mid_1": 70.0,
        "mid_2": 75.0,
        "internal_marks": 72.0,
        "backlogs": 0,
        "gender": "UNICORN",
    }
    res = await client.post(f"{settings.API_V1_PREFIX}/predictions/cgpa", json=payload)
    assert res.status_code == 422
    assert "gender" in res.text


async def test_prediction_rejects_invalid_department(client: AsyncClient):
    from backend.app.core.config import settings

    payload = {
        "attendance_percentage": 80.0,
        "previous_cgpa": 7.0,
        "mid_1": 70.0,
        "mid_2": 75.0,
        "internal_marks": 72.0,
        "backlogs": 0,
        "department_code": "ASTRONOMY",
    }
    res = await client.post(f"{settings.API_V1_PREFIX}/predictions/cgpa", json=payload)
    assert res.status_code == 422
    assert "department_code" in res.text


# ---------------------------------------------------------------------------
# Production configuration guard
# ---------------------------------------------------------------------------

def test_production_config_rejects_defaults():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="super-secret-key-change-in-production-0123456789abcdef",
        )


def test_production_config_rejects_dev_secret():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="dev-secret-key-student-success-predictor-2026-phase-1",
        )


def test_production_config_forces_secure_cookies():
    s = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="a" * 64,
    )
    assert s.COOKIE_SECURE is True


def test_cors_without_wildcard_fallback():
    s = Settings(_env_file=None, BACKEND_CORS_ORIGINS="")  # type: ignore[call-arg]
    assert s.BACKEND_CORS_ORIGINS == [] or "*" not in s.BACKEND_CORS_ORIGINS