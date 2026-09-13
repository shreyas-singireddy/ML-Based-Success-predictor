from typing import List, Optional, Union
from pathlib import Path

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ Runtime
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Student Success Predictor"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # Comma-separated hostnames (production reverse proxies should only forward
    # requests whose Host header is listed here). Empty => accept all (dev only).
    ALLOWED_HOSTS: Union[List[str], str] = []

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return v or []

    # --------------------------------------------------------- Security & Tokens
    # Generated with: openssl rand -hex 32  (NEVER use the default in production)
    SECRET_KEY: str = "super-secret-key-change-in-production-0123456789abcdef"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # HttpOnly refresh cookie Secure flag; force True when ENVIRONMENT=production
    COOKIE_SECURE: bool = False
    # Login brute-force guard (per IP per minute)
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10

    @model_validator(mode="after")
    def enforce_production_safety(self) -> "Settings":
        """Fail fast instead of silently running production with dev defaults."""
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be false when ENVIRONMENT=production.")
            if self.SECRET_KEY in (
                "super-secret-key-change-in-production-0123456789abcdef",
                "dev-secret-key-student-success-predictor-2026-phase-1",
                "change-this-to-a-super-secret-hex-key-in-production",
                "change-me-to-a-strong-random-hex-value",
            ) or self.SECRET_KEY.startswith("dev-"):
                raise ValueError(
                    "SECRET_KEY must be overridden with a strong random value "
                    "when ENVIRONMENT=production."
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters "
                    "when ENVIRONMENT=production."
                )
            if self.COOKIE_SECURE is False:
                self.COOKIE_SECURE = True
        return self

    # --------------------------------------------------------------------- CORS
    # Comma-separated list of explicit origins. NEVER "*" when credentials/private
    # data are involved. A missing/malformed value fails closed (empty list).
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return []

    # ------------------------------------------------- Database Configuration
    # Defaults to PostgreSQL with asyncpg for production; aiosqlite for tests/dev.
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "student_predictor_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/student_predictor_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/student_predictor_db"

    # CSV Upload limits
    MAX_CSV_UPLOAD_SIZE_MB: int = 10

    # --------------------------------------------- ML Registry & Inference
    # Optional override for the model artifact registry directory.
    #   e.g. /opt/success-predictor/models  (mounted volume / object store)
    # When empty, the in-repo default is used: <project_root>/ml/registry
    MODEL_REGISTRY_PATH: Optional[str] = None

    # -------------------------------------- GenAI Assistant (Phase 9)
    AI_PROVIDER: str = "gemini"  # gemini | openai | local | fallback
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_NAME: str = "gemini-1.5-flash"
    AI_MAX_OUTPUT_TOKENS: int = 1024
    AI_TEMPERATURE: float = 0.2
    AI_RATE_LIMIT_PER_MINUTE: int = 30

    # ------------------------------------------------- Logging & Observability
    LOG_LEVEL: str = "INFO"  # DEBUG | INFO | WARNING | ERROR | CRITICAL
    LOG_FORMAT: str = "json"  # json | text
    LOG_MAX_BODY_CHARS: int = 2000


settings = Settings()


def _resolve_registry_path() -> Path:
    """Resolve the model registry directory from config or the in-repo default."""
    if settings.MODEL_REGISTRY_PATH:
        return Path(settings.MODEL_REGISTRY_PATH).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "ml" / "registry"
