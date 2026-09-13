"""
Pydantic V2 Schemas for AI Academic Risk Prediction API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ml.classification.risk_policy import RiskLevel, PerformanceCategory
from ml.config.pipeline_config import ALLOWED_GENDERS, ALLOWED_DEPARTMENTS


class RiskPredictionRequest(BaseModel):
    """Payload for student academic risk evaluation."""

    student_number: Optional[str] = Field(
        default=None,
        description="Optional unique student roll/matriculation number for historical context retrieval.",
        json_schema_extra={"example": "2023cs002"},
    )
    gender: Optional[str] = Field(
        default="MALE",
        description="Student biological/administrative gender (MALE, FEMALE, OTHER).",
        json_schema_extra={"example": "MALE"},
    )
    age: Optional[int] = Field(
        default=20,
        ge=16,
        le=40,
        description="Student age in completed years.",
        json_schema_extra={"example": 20},
    )
    department_code: Optional[str] = Field(
        default="CS",
        description="Academic department code (e.g. CS, IT, ECE, EEE, MECH, CIVIL, AI, DS).",
        json_schema_extra={"example": "CS"},
    )
    semester: Optional[int] = Field(
        default=4,
        ge=1,
        le=8,
        description="Target academic semester for prediction.",
        json_schema_extra={"example": 4},
    )
    attendance_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current semester pre-final examination class attendance rate.",
        json_schema_extra={"example": 68.0},
    )
    previous_cgpa: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Cumulative Grade Point Average (CGPA) preceding the current semester.",
        json_schema_extra={"example": 6.2},
    )
    mid_1: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="First Mid-Term examination performance score.",
        json_schema_extra={"example": 62.0},
    )
    mid_2: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Second Mid-Term examination performance score.",
        json_schema_extra={"example": 65.0},
    )
    internal_marks: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Continuous internal assessment aggregate marks.",
        json_schema_extra={"example": 64.0},
    )
    backlogs: int = Field(
        ...,
        ge=0,
        le=20,
        description="Count of currently active/un-cleared backlogs.",
        json_schema_extra={"example": 1},
    )

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v is None:
            return v
        if v.upper() not in ALLOWED_GENDERS:
            raise ValueError(f"gender must be one of {ALLOWED_GENDERS}; got '{v}'")
        return v.upper()

    @field_validator("department_code")
    @classmethod
    def validate_department_code(cls, v):
        if v is None:
            return v
        if v.upper() not in ALLOWED_DEPARTMENTS:
            raise ValueError(
                f"department_code must be one of {ALLOWED_DEPARTMENTS}; got '{v}'"
            )
        return v.upper()

    model_config = ConfigDict(extra="ignore")


class RiskFactorDetail(BaseModel):
    """Transparent deterministic policy factor breakdown."""

    factor: str = Field(..., description="Academic indicator name (e.g. Attendance, Backlogs, Mid-Term Performance).")
    level: str = Field(..., description="Indicator severity classification (LOW, MEDIUM, HIGH, CRITICAL).")
    value: Any = Field(..., description="Observed input value for the indicator.")
    detail: str = Field(..., description="Explanatory detail based on institutional threshold policy.")


class RiskPredictionResponse(BaseModel):
    """Structured response payload for AI Academic Risk Prediction."""

    predicted_cgpa: float = Field(..., description="Projected semester CGPA from Phase 3 regression engine.")
    grade: str = Field(..., description="Institutional grade mapped from predicted CGPA (O, A+, A, B, C).")
    performance_category: str = Field(..., description="Institutional performance category (EXCELLENT, GOOD, AVERAGE, AT_RISK).")
    risk_level: str = Field(..., description="Classified academic risk level from Phase 4 classifier (LOW, MEDIUM, HIGH, CRITICAL).")
    risk_score: float = Field(..., description="Normalized continuous risk severity score in range [0.0, 100.0].")
    risk_probabilities: Dict[str, float] = Field(..., description="Multiclass prediction probabilities for LOW, MEDIUM, HIGH, CRITICAL.")
    risk_factors: List[RiskFactorDetail] = Field(..., description="Transparent 5-factor deterministic policy breakdown.")
    model_name: str = Field(..., description="Champion classifier model identifier.")
    model_version: str = Field(..., description="Version of the risk classification model artifact.")
    prediction_context: str = Field(..., description="Prediction context (e.g. adhoc_student, historical_student).")
    status: str = Field(default="success", description="Prediction operation execution status.")

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
