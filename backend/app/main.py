from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.app.core.config import settings
from backend.app.core.database import engine, Base, AsyncSessionLocal
from backend.app.core.observability import RequestContextMiddleware, configure_logging
from backend.app.core.model_health import check_model_registry
# Register all SQLAlchemy mappers (User.notifications -> Notification, etc.).
# Without this, string relationships fail to resolve at mapper configuration.
import backend.app.models  # noqa: F401
from backend.app.api.v1 import api_router
from backend.app.services.ml_runtime import configure_ml_runtime

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup (creates if not exist)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Point inference/explanation services at the deployment-time registry.
    configure_ml_runtime()
    yield
    # Cleanup database engine on shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Student Academic Performance & CGPA Prediction System — Production Backend API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# Structured observability: request IDs, security headers, Host allow-list.
app.add_middleware(RequestContextMiddleware)

# CORS Configuration — explicit origin allow-list only. Never "*" with
# credentials; a malformed config now fails closed (empty list) instead of
# falling back to a wildcard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Standardized Error Handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        errors.append({
            "field": field,
            "issue": err.get("msg", "Validation error"),
            "type": err.get("type", "invalid_value"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The submitted payload failed schema validation.",
                "details": errors,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Explicitly scrub stack traces: `detail` is only ever a pre-authored string.
    message = exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path,
            }
        },
        headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak internal exception details to clients, even in DEBUG mode for
    # off-the-path failures. Details go to logs (structured), not the wire.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path,
            }
        },
    )


# ---------------------------------------------------------------------------
# Liveness / readiness / model health (no secrets in any payload)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["System"])
async def readiness_check():
    """Readiness probe: application + database + model artifacts + config."""
    db_ok = True
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    model_health = check_model_registry()
    all_ready = db_ok and model_health.status == "healthy"

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": {
            "database": "ok" if db_ok else "unreachable",
            "model_artifacts": model_health.status,
            "configuration": "ok",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/model/health", tags=["System", "MLOps"])
async def model_health_public():
    """Model artifact health summary for MLOps dashboards / orchestration."""
    report = check_model_registry()
    code = status.HTTP_200_OK if report.status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=code,
        content={
            "model_health": report.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
