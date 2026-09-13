"""
Pydantic schemas for Phase 10 Faculty Intelligence & Intervention Dashboard.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.academic_record import AcademicRecordResponse
from backend.app.schemas.explanation import ExplanationSchema
from backend.app.schemas.recommendation import RecommendationItemSchema, ActionPlanSchema
from backend.app.schemas.risk_prediction import RiskFactorDetail


class FacultyTopRiskFactor(BaseModel):
    factor_name: str
    feature_code: str
    affected_students_count: int
    severity: str = Field("MEDIUM", description="LOW | MEDIUM | HIGH | CRITICAL")
    description: str


class FacultyAcademicAlert(BaseModel):
    id: str
    alert_type: str = Field(..., description="ATTENDANCE_CRITICAL | HIGH_BACKLOGS | RISK_ELEVATED | CGPA_DROP | MULTI_RISK")
    severity: str = Field("HIGH", description="INFO | MEDIUM | HIGH | CRITICAL")
    title: str
    description: str
    affected_count: int
    student_ids: List[str] = Field(default_factory=list)
    recommended_action: str


class FacultyOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    students_monitored: int
    average_current_cgpa: Optional[float] = None
    average_predicted_cgpa: Optional[float] = None
    risk_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    )
    attendance_overview: Dict[str, Any] = Field(
        default_factory=lambda: {
            "average_attendance": None,
            "below_75_count": 0,
            "below_65_count": 0,
        }
    )
    backlog_overview: Dict[str, Any] = Field(
        default_factory=lambda: {
            "total_backlogs": 0,
            "students_with_backlogs": 0,
            "students_with_backlogs_pct": 0.0,
        }
    )
    performance_categories: Dict[str, int] = Field(
        default_factory=lambda: {
            "EXCELLENT": 0,
            "GOOD": 0,
            "AVERAGE": 0,
            "AT_RISK": 0,
        }
    )
    top_risk_factors: List[FacultyTopRiskFactor] = Field(default_factory=list)
    recent_alerts: List[FacultyAcademicAlert] = Field(default_factory=list)
    department_scope: Optional[str] = None
    department_name: Optional[str] = None
    last_analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class FacultyStudentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_number: str
    name: str
    department_id: uuid.UUID
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    current_semester: int
    gender: str
    current_cgpa: Optional[float] = None
    predicted_cgpa: Optional[float] = None
    risk_level: str = Field("LOW", description="LOW | MEDIUM | HIGH | CRITICAL")
    risk_score: float = Field(0.0, description="Normalized continuous risk score 0.0-100.0")
    priority_score: float = Field(0.0, description="Composite intervention priority score 0.0-100.0")
    priority_tier: str = Field("LOW", description="LOW | MEDIUM | HIGH | CRITICAL")
    attendance_percentage: Optional[float] = None
    backlogs: int = 0
    cgpa_trend: str = Field("INSUFFICIENT_DATA", description="IMPROVING | STABLE | DECLINING | INSUFFICIENT_DATA")
    top_risk_factors: List[str] = Field(default_factory=list)
    prediction_confidence: Optional[float] = None
    confidence_category: str = "MODERATE"
    last_evaluated_at: Optional[datetime] = None


class FacultyStudentListResponse(BaseModel):
    items: List[FacultyStudentSummary]
    total: int
    page: int
    limit: int
    pages: int
    risk_counts: Dict[str, int] = Field(
        default_factory=lambda: {"ALL": 0, "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    )


class GroupedFacultyRecommendations(BaseModel):
    immediate_attention: List[RecommendationItemSchema] = Field(default_factory=list)
    short_term: List[RecommendationItemSchema] = Field(default_factory=list)
    monitor: List[RecommendationItemSchema] = Field(default_factory=list)


class HistoricalVsPredictedTrend(BaseModel):
    semester_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_cgpa: Optional[float] = None
    predicted_cgpa: Optional[float] = None
    trend_direction: str = Field("STABLE", description="IMPROVING | STABLE | DECLINING | INSUFFICIENT_DATA")
    delta_cgpa: Optional[float] = None
    trend_description: str


class FacultyStudentDossier(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


    # Student info
    student: FacultyStudentSummary
    academic_history: List[AcademicRecordResponse] = Field(default_factory=list)
    trend_analysis: HistoricalVsPredictedTrend

    # Phase 3 Prediction details
    predicted_cgpa: Optional[float] = None
    prediction_confidence: Optional[float] = None
    prediction_interval: Optional[Dict[str, float]] = None
    feature_summary: Optional[Dict[str, Any]] = None

    # Phase 4 Risk details
    risk_level: str
    risk_score: float
    risk_factors_breakdown: Optional[List[RiskFactorDetail]] = None

    # Phase 5 Explainability details
    explanation: Optional[ExplanationSchema] = None
    faculty_explanation_summary: str

    # Phase 8 Recommendations grouped for faculty action
    grouped_recommendations: GroupedFacultyRecommendations
    action_plan: Optional[ActionPlanSchema] = None


    # Model provenance
    model_version: str = "cgpa_v1.0.0"
    risk_model_version: str = "risk_v1.0.0"
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = (
        "Predictions and risk classifications are decision-support signals, "
        "not deterministic outcomes. Faculty judgment, contextual student circumstances, "
        "and direct mentorship remain essential."
    )


class FacultyAnalyticsResponse(BaseModel):
    department_scope: Optional[str] = None
    total_students: int
    risk_distribution: Dict[str, int]
    performance_distribution: Dict[str, int]
    cgpa_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"<6.0": 0, "6.0-7.0": 0, "7.0-8.0": 0, "8.0-9.0": 0, ">=9.0": 0}
    )
    attendance_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"<65%": 0, "65%-75%": 0, "75%-85%": 0, ">=85%": 0}
    )
    backlog_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"0": 0, "1-2": 0, "3-4": 0, ">=5": 0}
    )
    top_model_risk_factors: List[FacultyTopRiskFactor] = Field(default_factory=list)
    semester_risk_hotspots: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class FacultyAssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    student_id: Optional[uuid.UUID] = None


class FacultyAssistantChatResponse(BaseModel):
    reply: str
    intent: str
    scope: str
    evidence_references: List[Dict[str, Any]] = Field(default_factory=list)
    data_summary: Optional[Dict[str, Any]] = None
    disclaimer: str = (
        "AI Insights are generated strictly from verified academic records and ML models. "
        "Always exercise professional faculty discretion."
    )


class FacultySuggestionsResponse(BaseModel):
    suggestions: List[str]
