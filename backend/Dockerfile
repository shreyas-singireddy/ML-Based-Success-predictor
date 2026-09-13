# =============================================================================
# Student Success Predictor — Backend Production Image
# =============================================================================
# FastAPI + ML inference in a single modular-monolith container.
# The image includes the ML registry artifacts because inference loads them
# directly from disk (no external model server).
#
# Build:
#   docker build -f backend/Dockerfile -t student-predictor-backend .
#
# Run:
#   docker run --rm -p 8000:8000 --env-file .env \
#     -v "$(pwd)/ml/registry:/models" \
#     -e MODEL_REGISTRY_PATH=/models \
#     student-predictor-backend
# =============================================================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Install production dependencies first (better layer caching).
COPY backend/requirements-prod.txt ./backend/requirements-prod.txt
RUN pip install --no-cache-dir -r backend/requirements-prod.txt

# 2. Copy application code + ML layer + model artifacts.
COPY backend ./backend
COPY ml ./ml
COPY backend/alembic.ini ./backend/alembic.ini

# 3. Non-root runtime user for defense-in-depth.
RUN addgroup --system app && adduser --system --ingroup app --home /app app \
    && chown -R app:app /app
USER app

# 4. Production server: multiple workers, no reload, no debug.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=5).status==200 else 1)"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]