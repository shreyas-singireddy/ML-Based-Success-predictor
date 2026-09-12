"""
Local Explanation Engine for Student Success Predictor.

Converts raw SHAP values + feature values into:
1. Structured FeatureContribution objects (ranked by impact magnitude)
2. Separated positive / negative factor lists
3. Student-facing human narrative text (from feature_catalog templates)
4. A complete ExplanationOutput Pydantic model

Design constraints:
- Explanations describe model behavior, not causality.
- Templates use "associates" not "causes" / "proves".
- SHAP values for LinearRegression: positive = pushes CGPA up.
- SHAP values for Risk Classification: interpreted relative to predicted class.
  Positive SHAP for HIGH/CRITICAL risk class = negative student outcome.
  We reframe direction so "positive_contribution" always means better for the student.
- Fairness note is always included when any demographic feature appears.
- Explanation only uses data from the single prediction request; no cross-student info.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field, ConfigDict

from ml.explainability.feature_catalog import (
    FEATURE_DISPLAY_CATALOG,
    GLOBAL_FAIRNESS_NOTE,
    FeatureDisplayInfo,
    get_feature_info,
    get_demographic_features,
)

logger = logging.getLogger("student_predictor.explainability.local_explanation")

# ---------------------------------------------------------------------------
# Thresholds for impact level classification
# ---------------------------------------------------------------------------
IMPACT_THRESHOLDS = {
    "HIGH": 0.3,    # |SHAP| > 0.3 → HIGH impact
    "MEDIUM": 0.1,  # 0.1 < |SHAP| <= 0.3 → MEDIUM impact
    # else → LOW
}


def _get_impact_level(shap_magnitude: float) -> str:
    if shap_magnitude > IMPACT_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif shap_magnitude > IMPACT_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Pydantic output models (these are the ML-layer output models;
# the backend has a separate Pydantic V2 schema that mirrors them)
# ---------------------------------------------------------------------------

class FeatureContribution(BaseModel):
    """Structured representation of a single feature's SHAP contribution."""
    model_config = ConfigDict(protected_namespaces=())

    feature_name: str = Field(..., description="Internal model feature name")
    display_name: str = Field(..., description="Human-readable feature label")
    original_value: Optional[float] = Field(
        None,
        description="Unscaled original input value (None for OHE binary features)",
    )
    unit: str = Field(default="", description="Measurement unit (%, score, count, etc.)")
    shap_value: float = Field(..., description="Raw SHAP value for this feature")
    contribution_direction: str = Field(
        ...,
        description="'positive' = supports better student outcome, 'negative' = worsens outcome",
    )
    impact_level: str = Field(..., description="'HIGH', 'MEDIUM', or 'LOW'")
    is_demographic: bool = Field(
        default=False,
        description="True if feature is demographic (fairness disclosure required)",
    )
    student_explanation: str = Field(
        ...,
        description="Natural language explanation for student-facing display",
    )


class ExplanationOutput(BaseModel):
    """
    Complete explanation output for a single prediction.
    Returned by both CGPA and Risk explanation services.
    """
    model_config = ConfigDict(protected_namespaces=())

    # Metadata
    model_name: str
    model_version: str
    model_type: str
    explainer_type: str
    explanation_available: bool

    # Task type: 'cgpa_regression' or 'risk_classification'
    task_type: str

    # For risk: the class being explained (e.g., 'HIGH')
    explained_class: Optional[str] = None

    # Top N features ranked by |SHAP| (default top 5)
    top_factors: List[FeatureContribution] = Field(default_factory=list)

    # All features sorted by impact (useful for admin/faculty views)
    all_factors: List[FeatureContribution] = Field(default_factory=list)

    # Separated positive and negative factors
    positive_factors: List[FeatureContribution] = Field(default_factory=list)
    negative_factors: List[FeatureContribution] = Field(default_factory=list)

    # SHAP expected/base value (model intercept/mean prediction)
    base_value: float = Field(default=0.0)

    # Sum of SHAP values → prediction = base_value + shap_sum
    shap_sum: float = Field(default=0.0)

    # Global feature importance (precomputed, normalized to 100%)
    global_feature_importance: Dict[str, float] = Field(default_factory=dict)

    # Top 10 global features for UI display
    top_global_features: Dict[str, float] = Field(default_factory=dict)

    # Fairness and limitations note (always present)
    fairness_note: str = Field(default=GLOBAL_FAIRNESS_NOTE)

    # Whether any demographic features appear in top_factors
    contains_demographic_factors: bool = False


# ---------------------------------------------------------------------------
# Core explanation builder
# ---------------------------------------------------------------------------

def build_explanation(
    *,
    shap_values: np.ndarray,
    feature_names: List[str],
    feature_values_raw: Dict[str, float],
    base_value: float,
    global_importance: Dict[str, float],
    explainer_type: str,
    explanation_available: bool,
    model_name: str,
    model_version: str,
    model_type: str,
    task_type: str,  # 'cgpa_regression' or 'risk_classification'
    explained_class: Optional[str] = None,
    top_n: int = 5,
) -> ExplanationOutput:
    """
    Build a complete ExplanationOutput from raw SHAP values.

    Args:
        shap_values: Shape (n_features,) — raw SHAP values from explainer.
        feature_names: Ordered list of model feature names (length = n_features).
        feature_values_raw: Dict mapping raw feature names → unscaled original values.
                            Used for display. May be empty for OHE binary features.
        base_value: Model base value (expected prediction over training set).
        global_importance: Precomputed global importance dict from explainer.
        explainer_type: String identifying which SHAP explainer was used.
        explanation_available: False if the model type is unsupported.
        model_name: Champion model name (from metadata).
        model_version: Model artifact version string (from metadata).
        model_type: Internal model type string (e.g., 'baseline_linear').
        task_type: 'cgpa_regression' or 'risk_classification'.
        explained_class: For classifiers, the risk class being explained.
        top_n: Number of top factors to include.

    Returns:
        ExplanationOutput instance.
    """
    if len(shap_values) != len(feature_names):
        raise ValueError(
            f"shap_values length ({len(shap_values)}) != "
            f"feature_names length ({len(feature_names)})"
        )

    all_contributions: List[FeatureContribution] = []
    demographic_in_top = False

    for feat_name, shap_val in zip(feature_names, shap_values):
        info: FeatureDisplayInfo = get_feature_info(feat_name)

        # Determine contribution direction
        # For CGPA regression: positive SHAP → pushes CGPA up → good for student
        # For risk classification of HIGH/CRITICAL: positive SHAP pushes toward
        # that risk class → bad for student → invert direction
        if task_type == "cgpa_regression":
            is_positive_student_outcome = shap_val >= 0.0
        else:
            # Risk classification: explained_class is the predicted risk level
            # Positive SHAP for HIGH/CRITICAL = bad → invert
            high_risk_class = explained_class in ("HIGH", "CRITICAL")
            if high_risk_class:
                is_positive_student_outcome = shap_val <= 0.0
            else:
                # LOW / MEDIUM: positive SHAP for LOW class = good
                is_positive_student_outcome = shap_val >= 0.0

        direction = "positive" if is_positive_student_outcome else "negative"
        impact_level = _get_impact_level(abs(shap_val))

        # Get narrative template
        if is_positive_student_outcome:
            narrative = info.positive_template
        else:
            narrative = info.negative_template

        # Original unscaled value: look up by raw feature name
        # For OHE features, use parent group name as a fallback
        original_val = feature_values_raw.get(feat_name)
        if original_val is None and info.parent_group:
            original_val = feature_values_raw.get(info.parent_group)
        if original_val is None:
            # Try base feature name (strip 'enc_' prefix and OHE value suffix)
            raw_key = feat_name.replace("enc_", "").rsplit("_", 1)[0] if "_" in feat_name else feat_name
            original_val = feature_values_raw.get(raw_key)

        contrib = FeatureContribution(
            feature_name=feat_name,
            display_name=info.display_name,
            original_value=round(float(original_val), 4) if original_val is not None else None,
            unit=info.unit,
            shap_value=round(float(shap_val), 6),
            contribution_direction=direction,
            impact_level=impact_level,
            is_demographic=info.is_demographic,
            student_explanation=narrative,
        )
        all_contributions.append(contrib)

    # Sort all by |SHAP| descending
    all_contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)

    # Top N factors
    top_factors = all_contributions[:top_n]

    # Check demographic presence in top factors
    contains_demographic_factors = any(c.is_demographic for c in top_factors)

    # Positive / negative separation (from all contributions)
    positive_factors = [c for c in all_contributions if c.contribution_direction == "positive"]
    negative_factors = [c for c in all_contributions if c.contribution_direction == "negative"]

    # Top 10 global features for UI display (sorted by importance desc)
    top_global = dict(
        sorted(global_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    )

    shap_sum = float(np.sum(shap_values))

    return ExplanationOutput(
        model_name=model_name,
        model_version=model_version,
        model_type=model_type,
        explainer_type=explainer_type,
        explanation_available=explanation_available,
        task_type=task_type,
        explained_class=explained_class,
        top_factors=top_factors,
        all_factors=all_contributions,
        positive_factors=positive_factors[:5],
        negative_factors=negative_factors[:5],
        base_value=round(base_value, 6),
        shap_sum=round(shap_sum, 6),
        global_feature_importance=global_importance,
        top_global_features=top_global,
        fairness_note=GLOBAL_FAIRNESS_NOTE,
        contains_demographic_factors=contains_demographic_factors,
    )


def build_unavailable_explanation(
    *,
    model_name: str,
    model_version: str,
    model_type: str,
    explainer_type: str,
    feature_names: List[str],
    task_type: str,
) -> ExplanationOutput:
    """
    Returns an ExplanationOutput indicating explanations are unavailable.
    Used as a safe fallback when the SHAP computation fails or the model
    type is unsupported.
    """
    return ExplanationOutput(
        model_name=model_name,
        model_version=model_version,
        model_type=model_type,
        explainer_type=explainer_type,
        explanation_available=False,
        task_type=task_type,
        top_factors=[],
        all_factors=[],
        positive_factors=[],
        negative_factors=[],
        base_value=0.0,
        shap_sum=0.0,
        global_feature_importance={name: 0.0 for name in feature_names},
        top_global_features={},
        fairness_note=GLOBAL_FAIRNESS_NOTE,
        contains_demographic_factors=False,
    )
