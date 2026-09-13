"""
Pydantic V2 Schemas for Phase 8 AI Personalized Recommendation Engine.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from ml.recommendations.recommendation_config import (
    RecommendationCategory,
    RecommendationPriority,
    RecommendationSource,
    ExpectedImpact,
    TimeHorizon,
)


class RecommendationEvidenceSchema(BaseModel):
    """Structured evidence item supporting a recommendation."""
    model_config = ConfigDict(protected_namespaces=())

    factor: str = Field(..., description="Machine-readable feature or factor key")
    display_name: str = Field(..., description="Human-readable factor title")
    current_value: Optional[Union[float, int, str]] = Field(None, description="Observed current student value")
    target_or_threshold: Optional[Union[float, int, str]] = Field(None, description="Policy threshold or target benchmark")
    unit: str = Field(default="", description="Measurement unit (%, marks, count, etc.)")
    source: str = Field(..., description="Evidence origin (ACADEMIC_DATA, RISK_POLICY, XAI, WHAT_IF_SIMULATION, COMBINED)")
    simulated_value: Optional[Union[float, int, str]] = Field(None, description="Hypothetical value tested in What-If simulator")
    shap_contribution: Optional[float] = Field(None, description="Local SHAP feature contribution if computed")
    impact_detail: Optional[str] = Field(None, description="Human-readable outcome or delta description")


class RecommendationItemSchema(BaseModel):
    """Single prioritized, evidence-backed academic recommendation."""
    model_config = ConfigDict(protected_namespaces=())

    id: str = Field(..., description="Unique recommendation identifier")
    title: str = Field(..., description="Concise action-oriented headline")
    priority: str = Field(..., description="CRITICAL, HIGH, MEDIUM, or LOW")
    category: str = Field(..., description="Taxonomy category (ATTENDANCE, BACKLOG_RECOVERY, etc.)")
    evidence: List[RecommendationEvidenceSchema] = Field(default_factory=list, description="Supporting evidence items")
    action: str = Field(..., description="Concrete, actionable academic guidance")
    expected_impact: str = Field(default="MEDIUM", description="Evidence-backed impact level: HIGH, MEDIUM, LOW, UNKNOWN")
    source: str = Field(..., description="Evidence origin: ACADEMIC_DATA, RISK_POLICY, XAI, WHAT_IF_SIMULATION, COMBINED")
    time_horizon: str = Field(default="THIS_WEEK", description="Planning horizon: THIS_WEEK, NEXT_30_DAYS, LONGER_TERM")
    risk_factor: Optional[str] = Field(None, description="Associated academic risk factor name")
    technical_details: Dict[str, Any] = Field(default_factory=dict, description="Model/SHAP parameters and metadata")


class ActionPlanSchema(BaseModel):
    """Organized temporal action plan grouping recommendations by time horizon."""
    model_config = ConfigDict(protected_namespaces=())

    this_week: List[RecommendationItemSchema] = Field(default_factory=list, description="Immediate priority actions")
    next_30_days: List[RecommendationItemSchema] = Field(default_factory=list, description="Medium-term milestone actions")
    longer_term: List[RecommendationItemSchema] = Field(default_factory=list, description="Strategic ongoing habits and goals")
    simulation_summary: Optional[Dict[str, Any]] = Field(None, description="What-If simulation highlights comparing baseline to target improvements")


class RecommendationRequest(BaseModel):
    """
    Request payload for generating personalized recommendations.
    Accepts either student_number (to resolve latest verified record from database)
    or explicit semester indicators.
    """
    model_config = ConfigDict(protected_namespaces=())

    student_number: Optional[str] = Field(None, description="Student identification number", json_schema_extra={"example": "STU-2023-001"})
    semester: Optional[int] = Field(None, ge=1, le=8, description="Target semester")
    gender: Optional[str] = Field(None, description="Student gender")
    age: Optional[int] = Field(None, ge=16, le=60, description="Student age")
    department_code: Optional[str] = Field(None, description="Department code")

    # Explicit indicators (optional if student_number provided, required otherwise)
    attendance_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Attendance percentage", json_schema_extra={"example": 68.0})
    previous_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0, description="Prior CGPA", json_schema_extra={"example": 6.2})
    mid_1: Optional[float] = Field(None, ge=0.0, le=100.0, description="Mid-Term 1 score", json_schema_extra={"example": 55.0})
    mid_2: Optional[float] = Field(None, ge=0.0, le=100.0, description="Mid-Term 2 score", json_schema_extra={"example": 58.0})
    internal_marks: Optional[float] = Field(None, ge=0.0, le=100.0, description="Internal marks", json_schema_extra={"example": 60.0})
    backlogs: Optional[int] = Field(None, ge=0, le=20, description="Active backlog count", json_schema_extra={"example": 1})


class RecommendationResponse(BaseModel):
    """Complete personalized recommendation payload with predictions and evidence."""
    model_config = ConfigDict(protected_namespaces=())

    student_number: Optional[str] = Field(None, description="Student identification number")
    student_name: Optional[str] = Field(None, description="Student full name")
    predicted_cgpa: float = Field(..., description="Projected semester CGPA from Phase 3 model")
    grade: str = Field(..., description="Institutional grade mapped from predicted CGPA")
    performance_category: str = Field(..., description="EXCELLENT, GOOD, AVERAGE, AT_RISK")
    risk_level: str = Field(..., description="Academic risk class: LOW, MEDIUM, HIGH, CRITICAL")
    risk_score: float = Field(..., description="Continuous normalized risk score (0-100)")
    recommendations: List[RecommendationItemSchema] = Field(default_factory=list, description="Ranked and deduplicated recommendations")
    action_plan: ActionPlanSchema = Field(..., description="Temporal action plan")
    evidence_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of evaluated indicators and simulation outcomes")
    model_version_info: Dict[str, str] = Field(default_factory=dict, description="Version metadata for all underlying models")
    policy_version: str = Field(default="1.0.0", description="Institutional recommendation policy version")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of recommendation generation")
    disclaimer: str = Field(
        default="Recommendations and simulations represent AI decision-support guidance based on historical statistical correlations, not institutional guarantees.",
        description="Fairness, transparency, and decision-support disclaimer"
    )
    status: str = Field(default="success")
