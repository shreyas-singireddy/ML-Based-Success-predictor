"""
Pydantic V2 Schemas for Phase 5 Explainable AI API Responses.

Mirrors the ML-layer ExplanationOutput model but as validated, serializable
FastAPI response schemas.

All schemas use ConfigDict(protected_namespaces=()) to avoid Pydantic V2
warnings from model_* field names.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from backend.app.schemas.prediction import CGPAPredictionResponse
from backend.app.schemas.risk_prediction import RiskPredictionResponse


class FeatureContributionSchema(BaseModel):
    """API schema for a single feature's SHAP contribution."""
    model_config = ConfigDict(protected_namespaces=())

    feature_name: str = Field(..., description="Internal model feature name")
    display_name: str = Field(..., description="Human-readable feature label")
    original_value: Optional[float] = Field(
        None,
        description="Unscaled original value (None for binary-encoded categorical features)",
    )
    unit: str = Field(default="", description="Measurement unit (%, points, count, etc.)")
    shap_value: float = Field(..., description="Raw SHAP value for this feature")
    contribution_direction: str = Field(
        ...,
        description="'positive' = supports better student outcome, 'negative' = worsens outcome",
    )
    impact_level: str = Field(
        ..., description="Impact magnitude category: 'HIGH', 'MEDIUM', or 'LOW'"
    )
    is_demographic: bool = Field(
        default=False,
        description="True if this feature is demographic — fairness note applies",
    )
    student_explanation: str = Field(
        ...,
        description="Natural language explanation suitable for student-facing display",
    )


class ExplanationSchema(BaseModel):
    """
    Full SHAP explanation response for a single prediction.
    Includes local contributions, global importance, and fairness metadata.
    """
    model_config = ConfigDict(protected_namespaces=())

    # Metadata
    model_name: str = Field(..., description="Champion model name")
    model_version: str = Field(..., description="Champion model artifact version")
    model_type: str = Field(..., description="Internal model type string")
    explainer_type: str = Field(
        ..., description="SHAP explainer variant used (e.g., SHAP_LinearExplainer)"
    )
    explanation_available: bool = Field(
        ..., description="False if explanations could not be computed for this model type"
    )

    # Task context
    task_type: str = Field(
        ..., description="'cgpa_regression' or 'risk_classification'"
    )
    explained_class: Optional[str] = Field(
        None, description="For risk classification: the class being explained (e.g., 'HIGH')"
    )

    # Local contributions (top 5 by |SHAP|)
    top_factors: List[FeatureContributionSchema] = Field(
        default_factory=list,
        description="Top 5 most influential features ranked by |SHAP value|",
    )
    positive_factors: List[FeatureContributionSchema] = Field(
        default_factory=list,
        description="Features supporting a better student outcome (top 5)",
    )
    negative_factors: List[FeatureContributionSchema] = Field(
        default_factory=list,
        description="Features contributing to a worse student outcome (top 5)",
    )

    # SHAP additive components
    base_value: float = Field(
        default=0.0,
        description="Model expected value (mean prediction over training set)",
    )
    shap_sum: float = Field(
        default=0.0,
        description="Sum of all SHAP values — prediction ≈ base_value + shap_sum",
    )

    # Global feature importance (normalized to 100%)
    top_global_features: Dict[str, float] = Field(
        default_factory=dict,
        description="Top 10 globally important features (normalized to sum to 100%)",
    )

    # Fairness & limitations
    fairness_note: str = Field(
        ...,
        description="Required fairness and limitations disclosure for all predictions",
    )
    contains_demographic_factors: bool = Field(
        default=False,
        description="True if any demographic feature appears in top_factors",
    )


class CGPAExplainedResponse(CGPAPredictionResponse):
    """
    CGPA Prediction response augmented with SHAP-based local explanation.
    Extends CGPAPredictionResponse with the 'explanation' field.
    """
    model_config = ConfigDict(protected_namespaces=())

    explanation: ExplanationSchema = Field(
        ...,
        description="SHAP-based local explanation for this CGPA prediction",
    )


class RiskExplainedResponse(RiskPredictionResponse):
    """
    Risk Prediction response augmented with SHAP-based local explanation.
    Extends RiskPredictionResponse with the 'explanation' field.
    """
    model_config = ConfigDict(protected_namespaces=())

    explanation: ExplanationSchema = Field(
        ...,
        description="SHAP-based local explanation for this Risk prediction",
    )


class GlobalImportanceResponse(BaseModel):
    """Response for global feature importance endpoints (model-level, not instance-level)."""
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_version: str
    task_type: str
    explainer_type: str
    global_feature_importance: Dict[str, float] = Field(
        ...,
        description="All features with normalized importance percentages (sum to 100%)",
    )
    top_features: Dict[str, float] = Field(
        ...,
        description="Top 10 most important features",
    )
    fairness_note: str
