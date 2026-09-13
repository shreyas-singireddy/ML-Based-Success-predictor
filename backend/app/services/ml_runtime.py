"""
ML runtime bootstrap.

Resolves the deployment-time model registry location (MODEL_REGISTRY_PATH)
once at application startup and points every inference/explanation singleton
at it. Keeps the ML layer free of backend imports while still honoring
production environment configuration.
"""

import logging
from pathlib import Path
from typing import Optional

from backend.app.core.config import _resolve_registry_path

logger = logging.getLogger("student_predictor.ml_runtime")


def configure_ml_runtime(registry_dir: Optional[Path] = None) -> Path:
    """Configure all inference services to use the resolved registry path."""
    from ml.explainability.explanation_service import explanation_service

    resolved = registry_dir or _resolve_registry_path()
    if explanation_service.registry_dir != resolved:
        explanation_service.configure_registry(registry_dir=resolved)
    logger.info("ML runtime registry: %s", resolved)
    return resolved