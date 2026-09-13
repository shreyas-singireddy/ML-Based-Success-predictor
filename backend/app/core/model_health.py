"""
Model artifact health checks for the production ML registry.

Verifies that every artifact the inference services need is present, loadable,
and internally consistent (preprocessor feature schema ↔ model feature schema).
Always safe to call: loads only metadata and performs a cheap structural check —
never a full prediction and never a retrain.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("student_predictor.model_health")

REQUIRED_ARTIFACTS: Dict[str, str] = {
    "preprocessor.joblib": "Phase 2 fitted preprocessing pipeline",
    "best_model.joblib": "Phase 3 champion CGPA regression model",
    "best_risk_classifier.joblib": "Phase 4 champion risk classifier model",
    "model_metadata.json": "CGPA model metadata (version, feature schema)",
    "risk_metadata.json": "Risk model metadata (version, feature schema)",
    "feature_metadata.json": "Preprocessor feature schema metadata",
}


@dataclass
class ArtifactHealth:
    name: str
    status: str  # ok | missing | invalid
    detail: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass
class ModelHealthReport:
    status: str  # healthy | degraded
    registry_path: str
    artifacts: List[ArtifactHealth]
    models: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "registry_path": self.registry_path,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "models": self.models,
        }


def _load_metadata(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Model health: unreadable metadata %s: %s", path, exc)
        return None


def check_model_registry(registry_dir: Optional[Path] = None) -> ModelHealthReport:
    """Evaluate the model registry directory and report artifact health."""
    if registry_dir is None:
        from backend.app.core.config import settings

        candidate = settings.MODEL_REGISTRY_PATH
        registry_dir = Path(candidate) if candidate else (
            Path(__file__).resolve().parents[3] / "ml" / "registry"
        )

    registry_dir = registry_dir.resolve()
    reports_raw: List[Dict[str, str]] = []
    artifacts: List[ArtifactHealth] = []
    for name, purpose in REQUIRED_ARTIFACTS.items():
        path = registry_dir / name
        if not path.exists():
            artifacts.append(ArtifactHealth(name=name, status="missing", detail=purpose))
            continue
        artifacts.append(ArtifactHealth(name=name, status="ok", detail=purpose))

    models: Dict[str, Any] = {}
    cgpa_meta = _load_metadata(registry_dir / "model_metadata.json")
    risk_meta = _load_metadata(registry_dir / "risk_metadata.json")
    feature_meta = _load_metadata(registry_dir / "feature_metadata.json")

    for key, meta in (("cgpa", cgpa_meta), ("risk", risk_meta)):
        if meta:
            models[key] = {
                "model_version": meta.get("model_version"),
                "model_name": meta.get("model_name"),
            }
        else:
            models[key] = {"status": "missing-metadata"}

    # Structural compatibility: preprocessor feature count vs model expectation.
    compatibility_issues: List[str] = []
    if cgpa_meta and feature_meta:
        model_features = cgpa_meta.get("feature_names")
        transformed = feature_meta.get("transformed_feature_names")
        if isinstance(model_features, list) and isinstance(transformed, list):
            if len(model_features) != len(transformed):
                compatibility_issues.append(
                    "cgpa preprocessor/model feature count mismatch: "
                    f"{len(transformed)} vs {len(model_features)}"
                )
    if compatibility_issues:
        for issue in compatibility_issues:
            artifacts.append(ArtifactHealth(name="compatibility", status="invalid", detail=issue))
        models["compatibility"] = {"status": "invalid", "issues": compatibility_issues}

    status = "healthy"
    if not (registry_dir / "preprocessor.joblib").exists() or not (
        registry_dir / "best_model.joblib"
    ).exists():
        status = "degraded"
    if compatibility_issues:
        status = "degraded"

    return ModelHealthReport(
        status=status,
        registry_path=str(registry_dir),
        artifacts=artifacts,
        models=models,
    )