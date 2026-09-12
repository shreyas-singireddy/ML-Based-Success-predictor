"""
Pydantic Schemas for AI CGPA Prediction API.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class CGPAPredictionRequest(BaseModel):
    """Input payload for semester CGPA prediction."""
    attendance_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Attendance percentage in the current semester (0-100)",
        json_schema_extra={"example": 82.0},
    )
    previous_cgpa: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Cumulative CGPA prior to current semester (0-10)",
        json_schema_extra={"example": 7.40},
    )
    mid_1: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Mid-Term 1 examination score (0-100)",
        json_schema_extra={"example": 72.0},
    )
    mid_2: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Mid-Term 2 examination score (0-100)",
        json_schema_extra={"example": 76.0},
    )
    internal_marks: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Continuous internal assessment marks (0-100)",
        json_schema_extra={"example": 78.0},
    )
    backlogs: int = Field(
        default=0,
        ge=0,
        le=50,
        description="Number of active academic backlogs",
        json_schema_extra={"example": 0},
    )
    department_code: Optional[str] = Field(
        default="CS",
        description="Academic department code (e.g. CS, IT, ECE)",
        json_schema_extra={"example": "CS"},
    )
    semester: Optional[int] = Field(
        default=4,
        ge=1,
        le=12,
        description="Current semester number (1-12)",
        json_schema_extra={"example": 4},
    )
    gender: Optional[str] = Field(
        default="MALE",
        description="Student gender (MALE, FEMALE, OTHER)",
        json_schema_extra={"example": "MALE"},
    )
    age: Optional[int] = Field(
        default=20,
        ge=15,
        le=100,
        description="Student age in years",
        json_schema_extra={"example": 20},
    )
    student_number: Optional[str] = Field(
        default=None,
        description="Optional student number to query authorized historical records from DB for longitudinal trend calculation",
        json_schema_extra={"example": "2023cs001"},
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "attendance_percentage": 82.0,
                "previous_cgpa": 7.40,
                "mid_1": 72.0,
                "mid_2": 76.0,
                "internal_marks": 78.0,
                "backlogs": 0,
                "department_code": "CS",
                "semester": 4,
                "gender": "MALE",
                "age": 20,
            }
        },
    )


class FeatureSummary(BaseModel):
    """Summary of raw and engineered features used for inference."""
    academic_average: float
    attendance_risk_score: float
    attendance_risk_category: str
    internal_average: float
    mid_term_average: float
    previous_cgpa_trend: float
    backlog_severity_score: float
    backlog_severity_category: str
    academic_stability: float


class CGPAPredictionResponse(BaseModel):
    """Prediction response containing predicted CGPA and dynamic model metadata."""
    predicted_cgpa: float = Field(..., description="Predicted Semester CGPA (0.0 - 10.0)")
    model_name: str = Field(..., description="Name of the champion model used for inference")
    model_version: str = Field(..., description="Version of the model artifact loaded from metadata")
    prediction_context: str = Field(..., description="Context of prediction: 'adhoc_student' or 'historical_student'")
    feature_summary: FeatureSummary = Field(..., description="Summary of engineered pre-exam features")
    top_feature_contributions: Optional[Dict[str, float]] = Field(
        default=None,
        description="Global model feature importances / linear beta weights",
    )
    status: str = Field(default="success", description="Prediction status")

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "predicted_cgpa": 7.82,
                "model_name": "LinearRegression",
                "model_version": "cgpa_v1.0.0",
                "prediction_context": "adhoc_student",
                "feature_summary": {
                    "academic_average": 75.33,
                    "attendance_risk_score": 0.0,
                    "attendance_risk_category": "NORMAL",
                    "internal_average": 0.78,
                    "mid_term_average": 74.0,
                    "previous_cgpa_trend": 0.0,
                    "backlog_severity_score": 0.0,
                    "backlog_severity_category": "NONE",
                    "academic_stability": 0.0,
                },
                "status": "success",
            }
        },
    )
